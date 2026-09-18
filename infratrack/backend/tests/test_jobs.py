"""Offline jobs: the daily usage fetch and the alert evaluator."""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.entities import Alert, Team, UsageSnapshot
from scripts import fetch_usage, send_alerts
from tests.conftest import add_budget, add_usage


def test_fetch_usage_is_idempotent(db, team):
    """Regression: a retried cron run used to append a second set of rows for
    the same day, double-counting that day's spend."""
    fetch_usage.main()
    first = db.query(UsageSnapshot).filter(UsageSnapshot.snapshot_date == date.today()).count()
    assert first > 0

    fetch_usage.main()
    second = db.query(UsageSnapshot).filter(UsageSnapshot.snapshot_date == date.today()).count()
    assert second == first


def test_fetch_usage_without_teams_is_a_noop(db, capsys):
    fetch_usage.main()
    assert db.query(UsageSnapshot).count() == 0
    assert "Run scripts/seed.py first" in capsys.readouterr().out


def test_duplicate_snapshot_is_rejected_by_the_database(db, team):
    add_usage(db, team.id, date.today(), "EC2", 1.0)
    with pytest.raises(IntegrityError):
        add_usage(db, team.id, date.today(), "EC2", 2.0)
    db.rollback()


def test_send_alerts_fires_on_usage_written_after_the_budget(db, team, capsys):
    """Regression: the evaluator compared against the stale stored spend column,
    so alerts never fired once the cron took over from the seed."""
    add_budget(db, team.id, 100.0)
    db.add(Alert(team_id=team.id, threshold=80.0, email="ops@example.com", enabled=True))
    db.commit()

    send_alerts.main()
    assert "Triggered: 0" in capsys.readouterr().out

    add_usage(db, team.id, date.today(), "EC2", 85.0)

    send_alerts.main()
    out = capsys.readouterr().out
    assert "[ALERT]" in out
    assert "Triggered: 1" in out


def test_send_alerts_skips_disabled_alerts(db, team, capsys):
    add_budget(db, team.id, 100.0)
    add_usage(db, team.id, date.today(), "EC2", 999.0)
    db.add(Alert(team_id=team.id, threshold=80.0, email="ops@example.com", enabled=False))
    db.commit()

    send_alerts.main()
    assert "Triggered: 0" in capsys.readouterr().out


def test_health_and_teams(client, db):
    assert client.get("/health").json() == {"status": "ok"}

    db.add_all([Team(name="zeta"), Team(name="alpha")])
    db.commit()
    assert [t["name"] for t in client.get("/api/teams").json()] == ["alpha", "zeta"]
