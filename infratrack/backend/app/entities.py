"""SQLAlchemy ORM entities. Mirrors db/schema.sql but works on SQLite too."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow() -> datetime:
    """Timezone-aware UTC now (datetime.utcnow is deprecated on 3.12+)."""
    return datetime.now(UTC)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    budgets: Mapped[list[Budget]] = relationship(back_populates="team")
    alerts: Mapped[list[Alert]] = relationship(back_populates="team")
    snapshots: Mapped[list[UsageSnapshot]] = relationship(back_populates="team")


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    month: Mapped[str] = mapped_column(String, nullable=False)  # "YYYY-MM"
    budget_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    team: Mapped[Team] = relationship(back_populates="budgets")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    threshold: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    team: Mapped[Team] = relationship(back_populates="alerts")


class UsageSnapshot(Base):
    __tablename__ = "usage_snapshots"
    # One row per team/service/day. The constraint does double duty: it makes
    # fetch_usage re-runs safe, and its (team_id, snapshot_date) prefix is the
    # index every dashboard read needs for its date-range filter.
    __table_args__ = (
        UniqueConstraint("team_id", "snapshot_date", "service", name="uq_usage_team_date_service"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    service: Mapped[str] = mapped_column(String, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    team: Mapped[Team] = relationship(back_populates="snapshots")
