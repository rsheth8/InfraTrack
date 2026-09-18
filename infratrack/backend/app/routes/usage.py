from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.entities import UsageSnapshot
from app.models import Period, UsagePoint, UsageResponse

router = APIRouter()

_PERIOD_TO_DAYS: dict[str, int] = {"day": 1, "week": 7, "month": 30, "quarter": 90}


@router.get("/usage", response_model=UsageResponse)
def get_usage(
    team_id: int = Query(..., ge=1),
    period: Period = Query("week"),
    db: Session = Depends(get_session),
) -> UsageResponse:
    # Windows are inclusive of today: "day" is today alone, "week" is 7 days.
    days = _PERIOD_TO_DAYS[period]
    cutoff = date.today() - timedelta(days=days - 1)

    # Aggregate in the database rather than pulling every snapshot row and
    # summing in Python -- the row count grows with teams x services x days.
    rows = db.execute(
        select(
            UsageSnapshot.snapshot_date,
            UsageSnapshot.service,
            func.sum(UsageSnapshot.cost_usd),
        )
        .where(
            UsageSnapshot.team_id == team_id,
            UsageSnapshot.snapshot_date >= cutoff,
        )
        .group_by(UsageSnapshot.snapshot_date, UsageSnapshot.service)
        .order_by(UsageSnapshot.snapshot_date)
    ).all()

    points = [
        UsagePoint(timestamp=day, service=service, cost_usd=round(float(cost), 2))
        for day, service, cost in rows
    ]

    by_service: dict[str, float] = {}
    for point in points:
        by_service[point.service] = by_service.get(point.service, 0.0) + point.cost_usd

    return UsageResponse(
        team_id=team_id,
        period=period,
        total_usd=round(sum(by_service.values()), 2),
        points=points,
        by_service={k: round(v, 2) for k, v in by_service.items()},
    )
