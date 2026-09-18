"""Generate a fresh daily usage snapshot for every team.

In production this would hit AWS Cost Explorer + CloudWatch via boto3 and
write the result to `usage_snapshots`. The demo version here samples from the
same synthetic-cost model used by `scripts/seed.py` so the dashboard keeps
moving on a cron.

Schedule example (cron): ``5 0 * * *  python -m scripts.fetch_usage``
"""

from __future__ import annotations

import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal  # noqa: E402
from app.entities import Team, UsageSnapshot  # noqa: E402
from scripts.seed import SERVICE_DAILY_MEANS  # noqa: E402


def main() -> None:
    today = date.today()
    rng = random.Random()

    with SessionLocal() as db:
        teams = db.query(Team).all()
        if not teams:
            print("No teams configured. Run scripts/seed.py first.")
            return

        # Idempotent: clear today's rows before rewriting them, so a retried or
        # double-scheduled cron run replaces the day instead of doubling it.
        db.query(UsageSnapshot).filter(UsageSnapshot.snapshot_date == today).delete(
            synchronize_session=False
        )

        for team in teams:
            multiplier = rng.uniform(0.6, 1.8)
            for service, mean in SERVICE_DAILY_MEANS.items():
                jitter = rng.gauss(1.0, 0.12)
                cost = max(0.1, mean * multiplier * jitter)
                db.add(
                    UsageSnapshot(
                        team_id=team.id,
                        service=service,
                        cost_usd=round(cost, 2),
                        snapshot_date=today,
                    )
                )
        db.commit()
        print(f"Wrote daily snapshots for {len(teams)} teams.")


if __name__ == "__main__":
    main()
