"""SQLAlchemy models for optional Postgres persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, MetaData, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, declared_attr

class TelemetryBase(DeclarativeBase):
    """Declarative base with configurable schema support."""

    metadata = MetaData()

    @declared_attr.directive
    def __tablename__(cls) -> str:  # type: ignore[override]
        return cls.__name__.lower()


class TelemetryEvent(TelemetryBase):
    """Individual telemetry event rows."""

    __tablename__ = "telemetry_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts = Column(DateTime(timezone=True), nullable=False, index=True)
    service = Column(String(64), nullable=False)
    env = Column(String(32), nullable=False)
    update_type = Column(String(64), nullable=False)
    handler = Column(String(128), nullable=True)
    error_type = Column(String(128), nullable=True)
    latency_ms = Column(BigInteger, nullable=False)
    attrs = Column(JSONB, nullable=False, default=dict)


class TelemetryAggregateHourly(TelemetryBase):
    """Aggregated hourly payloads."""

    __tablename__ = "telemetry_aggregate_hourly"
    __table_args__ = (UniqueConstraint("period_start", "service", "env", name="uq_telem_hour"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    service = Column(String(64), nullable=False)
    env = Column(String(32), nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)


__all__ = ["TelemetryBase", "TelemetryEvent", "TelemetryAggregateHourly"]
