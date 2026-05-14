from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_session
from app.entities import UsageSnapshot
from app.models import UsagePoint, UsageResponse

router = APIRouter()

_PERIOD_TO_DAYS = {"day": 1, "week": 7, "month": 30, "quarter": 90}


@router.get("/usage", response_model=UsageResponse)
def get_usage(
    team_id: int = Query(..., ge=1),
    period: str = Query("week"),
    db: Session = Depends(get_session),
) -> UsageResponse:
    days = _PERIOD_TO_DAYS.get(period, 7)
    cutoff = date.today() - timedelta(days=days)

    rows = (
        db.query(UsageSnapshot)
        .filter(UsageSnapshot.team_id == team_id)
        .filter(UsageSnapshot.snapshot_date >= cutoff)
        .order_by(UsageSnapshot.snapshot_date)
        .all()
    )

    points = [
        UsagePoint(timestamp=r.snapshot_date, service=r.service, cost_usd=float(r.cost_usd))
        for r in rows
    ]

    by_service: dict[str, float] = {}
    for r in rows:
        by_service[r.service] = by_service.get(r.service, 0.0) + float(r.cost_usd)

    total = sum(by_service.values())

    return UsageResponse(
        team_id=team_id,
        period=period,
        total_usd=round(total, 2),
        points=points,
        by_service={k: round(v, 2) for k, v in by_service.items()},
    )
