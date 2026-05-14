"""Pydantic response/request schemas (API contract)."""
from __future__ import annotations

from datetime import date
from typing import List

from pydantic import BaseModel


class TeamSummary(BaseModel):
    id: int
    name: str


class UsagePoint(BaseModel):
    timestamp: date
    service: str
    cost_usd: float


class UsageResponse(BaseModel):
    team_id: int
    period: str
    total_usd: float
    points: List[UsagePoint]
    by_service: dict[str, float]


class AlertCreate(BaseModel):
    team_id: int
    threshold: float
    email: str


class AlertResponse(BaseModel):
    id: int
    team_id: int
    threshold: float
    email: str
    enabled: bool

    class Config:
        from_attributes = True


class BudgetResponse(BaseModel):
    team_id: int
    month: str
    budget_usd: float
    spend_usd: float
    percent_used: float
