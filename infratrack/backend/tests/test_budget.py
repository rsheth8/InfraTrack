"""Budget endpoint — spend must always reflect recorded usage."""

from datetime import date, timedelta

import pytest

from app.spend import month_bounds, month_to_date_spend
from tests.conftest import add_budget, add_usage


def test_spend_tracks_usage_recorded_after_the_budget_was_created(client, db, team):
    """Regression: spend used to be a stored column written once at seed time.

    Every later usage write -- the daily fetch_usage cron -- left it untouched,
    so the dashboard under-reported spend and threshold alerts silently stopped
    firing. Spend is now summed from usage_snapshots on read.
    """
    add_budget(db, team.id, 1000.0)

    assert client.get(f"/api/budget?team_id={team.id}").json()["spend_usd"] == 0.0

    add_usage(db, team.id, date.today(), "EC2", 300.0)
    add_usage(db, team.id, date.today(), "S3", 150.0)

    body = client.get(f"/api/budget?team_id={team.id}").json()
    assert body["spend_usd"] == 450.0
    assert body["percent_used"] == 45.0


def test_percent_used_can_exceed_100(client, db, team):
    add_budget(db, team.id, 100.0)
    add_usage(db, team.id, date.today(), "EC2", 250.0)

    assert client.get(f"/api/budget?team_id={team.id}").json()["percent_used"] == 250.0


def test_zero_budget_does_not_divide_by_zero(client, db, team):
    add_budget(db, team.id, 0.0)
    add_usage(db, team.id, date.today(), "EC2", 10.0)

    body = client.get(f"/api/budget?team_id={team.id}").json()
    assert body["percent_used"] == 0.0


def test_spend_excludes_other_months(client, db, team):
    add_budget(db, team.id, 1000.0)
    first_of_month = date.today().replace(day=1)
    add_usage(db, team.id, first_of_month - timedelta(days=1), "EC2", 999.0)
    add_usage(db, team.id, first_of_month, "EC2", 25.0)

    assert client.get(f"/api/budget?team_id={team.id}").json()["spend_usd"] == 25.0


def test_spend_excludes_other_teams(client, db, team):
    from app.entities import Team

    other = Team(name="data")
    db.add(other)
    db.commit()
    db.refresh(other)

    add_budget(db, team.id, 1000.0)
    add_usage(db, other.id, date.today(), "EC2", 500.0)

    assert client.get(f"/api/budget?team_id={team.id}").json()["spend_usd"] == 0.0


def test_missing_budget_is_404(client, team):
    assert client.get(f"/api/budget?team_id={team.id}").status_code == 404


def test_team_id_must_be_positive(client):
    assert client.get("/api/budget?team_id=0").status_code == 422


@pytest.mark.parametrize(
    "month,expected",
    [
        ("2026-01", (date(2026, 1, 1), date(2026, 2, 1))),
        ("2026-09", (date(2026, 9, 1), date(2026, 10, 1))),
        ("2026-12", (date(2026, 12, 1), date(2027, 1, 1))),
    ],
)
def test_month_bounds_handles_year_rollover(month, expected):
    assert month_bounds(month) == expected


def test_month_to_date_spend_on_empty_table_is_zero(db, team):
    assert month_to_date_spend(db, team.id, "2026-09") == 0.0
