"""Async Postgres helpers for telemetry persistence."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ..config import TelemetryConfig
from ..utils.logging import logger
from .models import TelemetryBase


class PostgresBackend:
    """Manage the SQLAlchemy engine and session factory."""

    def __init__(self, cfg: TelemetryConfig) -> None:
        if not cfg.postgres_dsn:
            raise ValueError("postgres_dsn must be provided when enable_postgres=True")
        self.cfg = cfg
        self.engine: AsyncEngine = create_async_engine(
            cfg.postgres_dsn,
            echo=cfg.postgres_echo,
            pool_size=cfg.postgres_pool_size,
            max_overflow=cfg.postgres_max_overflow,
        )
        TelemetryBase.metadata.schema = cfg.postgres_schema
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """Yield an AsyncSession."""

        session: AsyncSession = self.session_factory()
        try:
            yield session
        finally:
            await session.close()

    async def create_all(self) -> None:
        """Create tables defined in TelemetryBase metadata."""

        logger.warning("postgres_auto_create is enabled; prefer Alembic migrations in production.")
        async with self.engine.begin() as conn:
            await conn.run_sync(TelemetryBase.metadata.create_all)

    async def dispose(self) -> None:
        """Dispose of the engine."""

        await self.engine.dispose()
