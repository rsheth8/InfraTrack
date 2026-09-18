"""Evaluate every enabled alert and print which ones would trigger.

For each enabled `Alert`, compare the team's current-month spend to the
threshold (percent of budget). In production, route triggered alerts to SES
or a webhook; this version just logs them.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal  # noqa: E402
from app.entities import Alert, Budget  # noqa: E402
from app.spend import month_to_date_spend  # noqa: E402


def main() -> None:
    current_month = date.today().strftime("%Y-%m")
    triggered = 0

    with SessionLocal() as db:
        for alert in db.query(Alert).filter(Alert.enabled.is_(True)).all():
            budget = (
                db.query(Budget)
                .filter(Budget.team_id == alert.team_id, Budget.month == current_month)
                .first()
            )
            if budget is None or float(budget.budget_usd) <= 0:
                continue

            spend = month_to_date_spend(db, alert.team_id, current_month)
            percent = (spend / float(budget.budget_usd)) * 100
            if percent >= float(alert.threshold):
                triggered += 1
                print(
                    f"[ALERT] team={alert.team_id} email={alert.email} "
                    f"spend={percent:.1f}% threshold={float(alert.threshold):.1f}%"
                )

    print(f"Evaluated alerts. Triggered: {triggered}")


if __name__ == "__main__":
    main()
