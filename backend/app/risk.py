"""Rule-based (non-ML) risk scoring.

Every rule here is explainable: each factor that fires reports the
evidence that triggered it, which is what the frontend's "Evidence
review" panel displays. This is a heuristic prioritisation aid for a
human investigator, not an automated determination of wrongdoing.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from .models import Entity, RiskAssessment, RiskFactor, Transaction

RAPID_WINDOW_SECONDS = 60
FRAGMENTATION_MIN_DESTINATIONS = 2
HIGH_VALUE_THRESHOLD = 100_000


def _has_rapid_movement(transactions: List[Transaction]) -> bool:
    timestamps = sorted(datetime.fromisoformat(tx.timestamp) for tx in transactions)
    for earlier, later in zip(timestamps, timestamps[1:]):
        if (later - earlier).total_seconds() <= RAPID_WINDOW_SECONDS:
            return True
    return False


def _has_fragmentation(transactions: List[Transaction]) -> bool:
    destinations_by_source: dict[str, set[str]] = {}
    for tx in transactions:
        destinations_by_source.setdefault(tx.from_address, set()).add(tx.to_address)
    return any(len(dests) >= FRAGMENTATION_MIN_DESTINATIONS for dests in destinations_by_source.values())


def _has_known_entity(entities: List[Entity]) -> bool:
    return any(entity.confirmed for entity in entities)


def assess(transactions: List[Transaction], entities: List[Entity], reported_amount: float) -> RiskAssessment:
    factors: List[RiskFactor] = []

    if _has_rapid_movement(transactions):
        factors.append(
            RiskFactor(
                name="Rapid fund movement",
                points=30,
                evidence="Sequential transfers occurred within 60 seconds.",
            )
        )

    if _has_fragmentation(transactions):
        factors.append(
            RiskFactor(
                name="Fund fragmentation",
                points=25,
                evidence="One wallet sent funds to multiple destinations.",
            )
        )

    if _has_known_entity(entities):
        factors.append(
            RiskFactor(
                name="Known entity connection",
                points=25,
                evidence="A labeled entity appears in the trace.",
            )
        )

    if reported_amount >= HIGH_VALUE_THRESHOLD:
        factors.append(
            RiskFactor(
                name="High-value report",
                points=20,
                evidence="Reported loss meets or exceeds the high-value review threshold.",
            )
        )

    score = min(sum(factor.points for factor in factors), 100)

    if score >= 80:
        level = "critical"
    elif score >= 55:
        level = "high"
    elif score >= 30:
        level = "medium"
    else:
        level = "low"

    return RiskAssessment(score=score, level=level, factors=factors)
