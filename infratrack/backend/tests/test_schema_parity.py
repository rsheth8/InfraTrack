"""db/schema.sql must stay in step with the ORM models.

The Postgres DDL is hand-maintained alongside entities.py. Nothing stops the
two drifting apart, and the failure mode is nasty: everything works on the
SQLite default and breaks only for whoever deploys on Postgres. This applies
the real DDL and compares it to the ORM's own idea of the schema.

Postgres-only -- schema.sql uses SERIAL and NOW(), which SQLite has no notion of.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import inspect

import app.entities  # noqa: F401  (registers the tables on Base.metadata)
from app.db import Base, engine

_SCHEMA_SQL = Path(__file__).resolve().parent.parent.parent / "db" / "schema.sql"

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="db/schema.sql is Postgres DDL; set TEST_DATABASE_URL to a Postgres URL",
)


@pytest.fixture
def schema_from_sql():
    """Replace the ORM-created schema with one built from db/schema.sql."""
    Base.metadata.drop_all(bind=engine)
    with engine.begin() as conn:
        conn.exec_driver_sql(_SCHEMA_SQL.read_text())
    yield inspect(engine)
    Base.metadata.drop_all(bind=engine)


@pytest.mark.parametrize("table", sorted(Base.metadata.tables))
def test_columns_match_the_orm(schema_from_sql, table):
    from_sql = {c["name"] for c in schema_from_sql.get_columns(table)}
    from_orm = {c.name for c in Base.metadata.tables[table].columns}
    assert from_sql == from_orm, (
        f"{table}: only in ORM={from_orm - from_sql}, only in schema.sql={from_sql - from_orm}"
    )


def test_usage_snapshots_uniqueness_is_enforced(schema_from_sql):
    """The (team_id, snapshot_date, service) guard is what makes the daily
    fetch job safe to retry, so it has to exist in the deployed DDL too."""
    indexes = schema_from_sql.get_indexes("usage_snapshots")
    unique = [i for i in indexes if i["unique"]]
    assert any(i["column_names"] == ["team_id", "snapshot_date", "service"] for i in unique), (
        f"missing unique index on (team_id, snapshot_date, service); found {unique}"
    )
