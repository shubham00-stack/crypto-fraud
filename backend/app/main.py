"""Crypto Fraud Attribution MVP — backend.

Implements the endpoints the frontend calls:
  POST /api/cases                       create a case + run the demo trace
  POST /api/cases/{case_id}/monitor/start start monitoring, emit one demo alert
  GET  /api/cases/{case_id}              fetch a stored case
  GET  /api/cases/{case_id}/report       export the case as a PDF

The blockchain data is always synthetic and deterministic — see
app/blockchain.py. No live chain data, API keys, or paid services are
used anywhere in this demo.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .blockchain import DemoBlockchainProvider
from .models import Alert, CaseInput, CaseRecord
from .risk import assess

WALLET_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")
ALLOWED_HOPS = {3, 4, 5}

app = FastAPI(title="Crypto Fraud Attribution MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

CASES: Dict[str, CaseRecord] = {}
provider = DemoBlockchainProvider()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/cases", response_model=CaseRecord)
def create_case(payload: CaseInput) -> CaseRecord:
    wallet = payload.wallet_address.strip()
    if not WALLET_PATTERN.match(wallet):
        raise HTTPException(
            status_code=400,
            detail="Invalid Ethereum wallet address. Enter a valid 0x-prefixed 42-character address.",
        )
    if payload.reported_amount <= 0:
        raise HTTPException(status_code=400, detail="Reported amount must be greater than zero.")
    if payload.max_hops not in ALLOWED_HOPS:
        raise HTTPException(
            status_code=400,
            detail="Trace depth must be between 3 and 5 hops for this demo provider.",
        )

    transactions, entities, nodes, edges, traced_amount = provider.trace(
        wallet_address=wallet,
        blockchain=payload.blockchain,
        token=payload.token,
        reported_amount=payload.reported_amount,
        max_hops=payload.max_hops,
    )

    risk = assess(transactions, entities, payload.reported_amount)

    case = CaseRecord(
        id=uuid.uuid4().hex[:10],
        input=payload,
        valid_wallet=True,
        transactions=transactions,
        entities=entities,
        nodes=nodes,
        edges=edges,
        risk=risk,
        traced_amount=traced_amount,
        max_hop_depth=payload.max_hops,
        monitoring=False,
        alerts=[],
    )
    CASES[case.id] = case
    return case


@app.get("/api/cases/{case_id}", response_model=CaseRecord)
def get_case(case_id: str) -> CaseRecord:
    case = CASES.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


@app.post("/api/cases/{case_id}/monitor/start", response_model=CaseRecord)
def start_monitoring(case_id: str) -> CaseRecord:
    case = CASES.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    case.monitoring = True
    if not case.alerts:
        # Deterministic per-case demo alert: a small new transfer out of the
        # last hop of the trace, sized as a fraction of the traced amount.
        demo_amount = round(max(case.traced_amount, 1) * 0.08, 2)
        case.alerts.append(
            Alert(
                id=uuid.uuid4().hex[:8],
                severity="HIGH",
                amount=demo_amount,
                asset=case.input.token,
                reason=(
                    "New outbound transfer detected from a monitored wallet in this trace "
                    f"at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')} (synthetic demo event)."
                ),
            )
        )
    CASES[case_id] = case
    return case


@app.get("/api/cases/{case_id}/report")
def export_report(case_id: str) -> Response:
    case = CASES.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Imported lazily so a missing reportlab install only breaks PDF export,
    # not the whole API.
    from .pdf import build_report_pdf

    pdf_bytes = build_report_pdf(case)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="case-{case_id}-report.pdf"'},
    )
