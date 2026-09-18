"""Usage endpoint — window boundaries, aggregation, and input validation."""

from datetime import date, timedelta

import pytest

from tests.conftest import add_usage


def test_day_window_is_today_only(client, db, team):
    """Regression: the window used `today - days`, so "day" returned two days."""
    add_usage(db, team.id, date.today(), "EC2", 10.0)
    add_usage(db, team.id, date.today() - timedelta(days=1), "EC2", 99.0)

    body = client.get(f"/api/usage?team_id={team.id}&period=day").json()
    assert body["total_usd"] == 10.0
    assert {p["timestamp"] for p in body["points"]} == {date.today().isoformat()}


def test_week_window_is_seven_days_inclusive(client, db, team):
    for offset in range(10):
        add_usage(db, team.id, date.today() - timedelta(days=offset), "EC2", 1.0)

    body = client.get(f"/api/usage?team_id={team.id}&period=week").json()
    assert body["total_usd"] == 7.0


@pytest.mark.parametrize("period,days", [("day", 1), ("week", 7), ("month", 30), ("quarter", 90)])
def test_each_period_covers_its_documented_window(client, db, team, period, days):
    for offset in range(100):
        add_usage(db, team.id, date.today() - timedelta(days=offset), "EC2", 1.0)

    body = client.get(f"/api/usage?team_id={team.id}&period={period}").json()
    assert body["total_usd"] == float(days)


def test_unknown_period_is_rejected(client, team):
    """Regression: an unknown period silently fell back to a 7-day window."""
    res = client.get(f"/api/usage?team_id={team.id}&period=fortnight")
    assert res.status_code == 422


def test_by_service_totals_and_grand_total(client, db, team):
    add_usage(db, team.id, date.today(), "EC2", 10.0)
    add_usage(db, team.id, date.today() - timedelta(days=1), "EC2", 5.0)
    add_usage(db, team.id, date.today(), "S3", 2.5)

    body = client.get(f"/api/usage?team_id={team.id}&period=week").json()
    assert body["by_service"] == {"EC2": 15.0, "S3": 2.5}
    assert body["total_usd"] == 17.5


def test_excludes_other_teams(client, db, team):
    from app.entities import Team

    other = Team(name="data")
    db.add(other)
    db.commit()
    db.refresh(other)
    add_usage(db, other.id, date.today(), "EC2", 500.0)
    add_usage(db, team.id, date.today(), "EC2", 1.0)

    body = client.get(f"/api/usage?team_id={team.id}&period=week").json()
    assert body["total_usd"] == 1.0


def test_empty_team_returns_zeroed_payload(client, team):
    body = client.get(f"/api/usage?team_id={team.id}&period=week").json()
    assert body["total_usd"] == 0.0
    assert body["points"] == []
    assert body["by_service"] == {}


def test_points_are_ordered_by_date(client, db, team):
    for offset in (2, 0, 1):
        add_usage(db, team.id, date.today() - timedelta(days=offset), "EC2", 1.0)

    body = client.get(f"/api/usage?team_id={team.id}&period=week").json()
    stamps = [p["timestamp"] for p in body["points"]]
    assert stamps == sorted(stamps)
