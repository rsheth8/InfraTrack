"""Pydantic response/request schemas (API contract)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Accepted /usage windows. Anything else is rejected with a 422 by FastAPI
# rather than silently falling back to a default window.
Period = Literal["day", "week", "month", "quarter"]


class TeamSummary(BaseModel):
    id: int
    name: str


class UsagePoint(BaseModel):
    timestamp: date
    service: str
    cost_usd: float


class UsageResponse(BaseModel):
    team_id: int
    period: Period
    total_usd: float
    points: list[UsagePoint]
    by_service: dict[str, float]


class AlertCreate(BaseModel):
    team_id: int = Field(..., ge=1)
    # Percent of budget. Over 100 is legitimate ("tell me at 150%"); zero or
    # negative would fire on every evaluation forever.
    threshold: float = Field(..., gt=0, le=1000)
    email: EmailStr


class AlertResponse(BaseModel):
    id: int
    team_id: int
    threshold: float
    email: str
    enabled: bool

    model_config = ConfigDict(from_attributes=True)


class BudgetResponse(BaseModel):
    team_id: int
    month: str
    budget_usd: float
    spend_usd: float
    percent_used: float
