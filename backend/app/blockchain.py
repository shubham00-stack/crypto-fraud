"""Demo blockchain provider.

This module is intentionally isolated so it can be swapped for a real
EVM indexer / RPC / block-explorer client in production. It never makes
network calls: every value is derived deterministically from the wallet
address that was entered, so the same address always reproduces the
same trace, transactions, entity labels and risk indicators.

No production API keys or live chain data are used or required.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from .models import Entity, GraphEdge, GraphNode, Transaction

EXCHANGE_NAME = "Nexus Digital Exchange (Demo)"
EXCHANGE_SOURCE = "Demo VASP deposit-address list"


def _seed_int(value: str) -> int:
    digest = hashlib.sha256(value.lower().encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _derive_address(seed: str, index: int) -> str:
    digest = hashlib.sha256(f"{seed}:{index}".encode("utf-8")).hexdigest()
    return "0x" + digest[:40]


def _derive_tx_hash(seed: str, index: int) -> str:
    digest = hashlib.sha256(f"{seed}:tx:{index}".encode("utf-8")).hexdigest()
    return "0x" + digest


class DemoBlockchainProvider:
    """Generates a deterministic synthetic multi-hop trace for a wallet."""

    def trace(
        self,
        wallet_address: str,
        blockchain: str,
        token: str,
        reported_amount: float,
        max_hops: int,
    ) -> Tuple[List[Transaction], List[Entity], List[GraphNode], List[GraphEdge], float]:
        wallet = wallet_address.lower()
        seed = f"{wallet}:{blockchain}:{max_hops}"
        rng_seed = _seed_int(seed)

        # Hop 1 always fragments into two branches: this both demonstrates
        # "fund fragmentation" and gives the trace two independent paths to
        # follow, one of which terminates at a known exchange address.
        branch_count = 2
        hops_per_branch = max(max_hops - 1, 2)

        base_time = datetime.now(timezone.utc) - timedelta(minutes=7 * (max_hops + 1))

        transactions: List[Transaction] = []
        nodes: List[GraphNode] = [
            GraphNode(id=wallet, label=f"{wallet[:8]}...{wallet[-4:]}", node_type="reported", risk=0)
        ]
        edges: List[GraphEdge] = []
        entities: List[Entity] = []

        block_number = 18_000_000 + (rng_seed % 500_000)
        tx_index = 0
        current_time = base_time

        # Hop 1: reported wallet fans out to `branch_count` intermediary wallets
        # within a short window, both branches leaving from the same source.
        first_hop_addresses = [_derive_address(seed, b) for b in range(branch_count)]
        first_hop_amount = reported_amount / branch_count
        traced_terminal_amount = 0.0
        exchange_wallet = None

        for b, addr in enumerate(first_hop_addresses):
            # Keep the two fan-out transfers close together (well under a
            # minute apart) so the "rapid fund movement" indicator fires.
            current_time = base_time + timedelta(seconds=25 * (b + 1))
            tx_index += 1
            transactions.append(
                Transaction(
                    tx_hash=_derive_tx_hash(seed, tx_index),
                    chain=blockchain,
                    from_address=wallet,
                    to_address=addr,
                    asset=token,
                    amount=round(first_hop_amount, 2),
                    timestamp=current_time.isoformat(timespec="milliseconds"),
                    block_number=block_number + tx_index,
                )
            )
            nodes.append(GraphNode(id=addr, label=f"{addr[:8]}...{addr[-4:]}", node_type="wallet", risk=35))
            edges.append(
                GraphEdge(
                    id=f"e{tx_index}",
                    source=wallet,
                    target=addr,
                    amount=round(first_hop_amount, 2),
                    asset=token,
                    tx_hash=transactions[-1].tx_hash,
                    timestamp=current_time.isoformat(timespec="milliseconds"),
                )
            )

        # Extend each branch for the remaining hops, decaying the amount at
        # each step to simulate fees / partial cash-outs along the way.
        for b, start_addr in enumerate(first_hop_addresses):
            prev_addr = start_addr
            amount = first_hop_amount
            branch_seed = f"{seed}:branch:{b}"
            for hop in range(1, hops_per_branch):
                is_last_hop = hop == hops_per_branch - 1
                # The first branch's final hop lands on a known exchange
                # deposit address; the second branch terminates at an
                # unlabeled wallet, which is a realistic mixed outcome.
                if is_last_hop and b == 0:
                    next_addr = _derive_address(branch_seed, 900)
                    exchange_wallet = next_addr
                    node_type = "exchange"
                else:
                    next_addr = _derive_address(branch_seed, hop)
                    node_type = "wallet"

                amount = amount * (0.88 - 0.02 * hop)
                current_time = current_time + timedelta(minutes=3 + (hop * 2))
                tx_index += 1
                tx_hash = _derive_tx_hash(seed, tx_index)
                transactions.append(
                    Transaction(
                        tx_hash=tx_hash,
                        chain=blockchain,
                        from_address=prev_addr,
                        to_address=next_addr,
                        asset=token,
                        amount=round(amount, 2),
                        timestamp=current_time.isoformat(timespec="milliseconds"),
                        block_number=block_number + tx_index,
                    )
                )
                nodes.append(
                    GraphNode(
                        id=next_addr,
                        label=f"{next_addr[:8]}...{next_addr[-4:]}",
                        node_type=node_type,
                        risk=85 if node_type == "exchange" else 35,
                    )
                )
                edges.append(
                    GraphEdge(
                        id=f"e{tx_index}",
                        source=prev_addr,
                        target=next_addr,
                        amount=round(amount, 2),
                        asset=token,
                        tx_hash=tx_hash,
                        timestamp=current_time.isoformat(timespec="milliseconds"),
                    )
                )
                prev_addr = next_addr

                if is_last_hop:
                    traced_terminal_amount += amount

        if exchange_wallet:
            confidence = 80 + (rng_seed % 18)
            entities.append(
                Entity(
                    address=exchange_wallet,
                    entity_name=EXCHANGE_NAME,
                    entity_type="exchange",
                    confidence=confidence,
                    source=EXCHANGE_SOURCE,
                    confirmed=True,
                )
            )

        return transactions, entities, nodes, edges, round(traced_terminal_amount, 2)
