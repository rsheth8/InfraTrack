"""Database engine + session factory.

Defaults to a local SQLite file so the project runs with no external services.
Set DATABASE_URL to a Postgres URL (the docker-compose file boots one) to use
Postgres instead. SQLAlchemy 2.x ORM.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent.parent / "infratrack.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_SQLITE_PATH}")

_engine_kwargs: dict = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    pass


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
