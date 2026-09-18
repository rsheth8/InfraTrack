"""Test fixtures.

Points DATABASE_URL at a throwaway SQLite file *before* app.db is imported, so
tests exercise the real engine, the real session factory and the real scripts
rather than a mocked stand-in. Each test gets a freshly created schema.
"""

from __future__ import annotations

import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="infratrack-tests-"))
# Defaults to throwaway SQLite. Set TEST_DATABASE_URL to run the same suite
# against Postgres -- CI does, so the documented Postgres support is proven
# rather than assumed (SQLite is lenient about types and constraints).
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_TMP / 'test.db'}")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.entities import Alert, Budget, Team, UsageSnapshot  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session
        # A test that asserts on IntegrityError leaves the transaction in a
        # failed state; Postgres blocks the teardown DROP until it is cleared.
        session.rollback()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def team(db) -> Team:
    row = Team(name="platform")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def add_usage(db, team_id: int, day: date, service: str, cost: float) -> None:
    db.add(UsageSnapshot(team_id=team_id, service=service, cost_usd=cost, snapshot_date=day))
    db.commit()


def add_budget(db, team_id: int, amount: float, month: str | None = None) -> Budget:
    row = Budget(
        team_id=team_id,
        month=month or date.today().strftime("%Y-%m"),
        budget_usd=amount,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


__all__ = ["add_usage", "add_budget", "Alert", "Budget", "Team", "UsageSnapshot", "timedelta"]
