"""Month-to-date spend, derived from usage_snapshots.

Single source of truth for "how much has a team spent". Budgets deliberately
do NOT store a spend column: a cached total has to be invalidated by every
writer (the API, seed.py, fetch_usage.py, a future Cost Explorer sync), and
the one that forgets silently under-reports spend — which in an alerting tool
means alerts quietly stop firing. Summing the snapshots is cheap given the
(team_id, snapshot_date) index and cannot go stale.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.entities import UsageSnapshot


def month_bounds(month: str) -> tuple[date, date]:
    """Return [start, end) dates for a "YYYY-MM" string."""
    year, mon = (int(part) for part in month.split("-"))
    start = date(year, mon, 1)
    end = date(year + (mon == 12), (mon % 12) + 1, 1)
    return start, end


def month_to_date_spend(db: Session, team_id: int, month: str) -> float:
    """Sum recorded usage for a team within the given "YYYY-MM" month."""
    start, end = month_bounds(month)
    total = db.execute(
        select(func.coalesce(func.sum(UsageSnapshot.cost_usd), 0)).where(
            UsageSnapshot.team_id == team_id,
            UsageSnapshot.snapshot_date >= start,
            UsageSnapshot.snapshot_date < end,
        )
    ).scalar_one()
    return round(float(total), 2)
