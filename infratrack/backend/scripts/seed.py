"""Populate the database with realistic synthetic teams, budgets, and 90 days
of daily usage snapshots across common AWS services.

Run from the backend directory: `python -m scripts.seed`
"""
from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

# Allow running as a script from the backend/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.entities import Alert, Budget, Team, UsageSnapshot  # noqa: E402

# Daily mean cost per service, modeled loosely on a small startup's AWS bill.
SERVICE_DAILY_MEANS = {
    "EC2": 38.0,
    "S3": 7.5,
    "RDS": 22.0,
    "CloudFront": 4.2,
    "Lambda": 1.1,
    "DynamoDB": 6.8,
    "CloudWatch": 2.6,
}

TEAMS = ["platform", "data", "growth", "ml-research"]


def reset_schema() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed() -> None:
    reset_schema()
    rng = random.Random(42)

    with SessionLocal() as db:
        teams = [Team(name=name) for name in TEAMS]
        db.add_all(teams)
        db.flush()

        today = date.today()
        for team in teams:
            # Team-specific cost multiplier so totals vary
            multiplier = rng.uniform(0.6, 1.8)

            # 90 days of daily snapshots per service
            for day_offset in range(90):
                d = today - timedelta(days=89 - day_offset)
                # Weekly seasonality: cheaper on weekends
                weekend = 0.78 if d.weekday() >= 5 else 1.0
                # Mild upward drift
                drift = 1.0 + (day_offset / 90) * 0.15

                for service, mean in SERVICE_DAILY_MEANS.items():
                    jitter = rng.gauss(1.0, 0.12)
                    cost = max(0.1, mean * multiplier * weekend * drift * jitter)
                    db.add(
                        UsageSnapshot(
                            team_id=team.id,
                            service=service,
                            cost_usd=round(cost, 2),
                            snapshot_date=d,
                        )
                    )

            # Flush pending snapshots before summing month-to-date spend
            db.flush()

            current_month = today.strftime("%Y-%m")
            mtd = sum(
                float(s.cost_usd)
                for s in db.query(UsageSnapshot)
                .filter(
                    UsageSnapshot.team_id == team.id,
                    UsageSnapshot.snapshot_date
                    >= today.replace(day=1),
                )
                .all()
            )
            db.add(
                Budget(
                    team_id=team.id,
                    month=current_month,
                    budget_usd=round(mtd * rng.uniform(1.2, 2.0) + 500, 2),
                    spend_usd=round(mtd, 2),
                )
            )

            # One default alert per team at 80% threshold
            db.add(
                Alert(
                    team_id=team.id,
                    threshold=80.0,
                    email=f"{team.name}-oncall@example.com",
                    enabled=True,
                )
            )

        db.commit()
        print(f"Seeded {len(teams)} teams, 90 days of usage, budgets, and alerts.")


if __name__ == "__main__":
    seed()
