"""Pydantic models.

Field names intentionally mirror the TypeScript types in
frontend/app/page.tsx (snake_case) so the JSON returned by this API
can be consumed by the frontend without any key transformation.
"""
from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class CaseInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    victim_reference: str = Field(min_length=1, max_length=200)
    blockchain: str
    wallet_address: str
    token: str
    reported_amount: float
    max_hops: int


class Transaction(BaseModel):
    tx_hash: str
    chain: str
    from_address: str
    to_address: str
    asset: str
    amount: float
    timestamp: str
    block_number: int


class Entity(BaseModel):
    address: str
    entity_name: str
    entity_type: str
    confidence: int
    source: str
    confirmed: bool


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    risk: int


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    amount: float
    asset: str
    tx_hash: str
    timestamp: str


class RiskFactor(BaseModel):
    name: str
    points: int
    evidence: str


class RiskAssessment(BaseModel):
    score: int
    level: str
    factors: List[RiskFactor]


class Alert(BaseModel):
    id: str
    severity: str
    amount: float
    asset: str
    reason: str


class CaseRecord(BaseModel):
    id: str
    input: CaseInput
    valid_wallet: bool
    transactions: List[Transaction]
    entities: List[Entity]
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    risk: RiskAssessment
    traced_amount: float
    max_hop_depth: int
    monitoring: bool
    alerts: List[Alert]
