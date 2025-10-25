"""Redis-backed aggregates for aiogram telemetry."""

from __future__ import annotations

import inspect
from datetime import datetime
from typing import Optional

import redis.asyncio as redis

from ..config import TelemetryConfig
from ..utils.labels import sanitize_label
from ..utils.logging import logger


class RedisStore:
    """Thin wrapper around a Redis client for telemetry aggregates."""

    def __init__(self, cfg: TelemetryConfig, client: redis.Redis | None = None) -> None:
        self.cfg = cfg
        self._client: redis.Redis
        if client is None:
            self._client = redis.from_url(
                cfg.redis_dsn,
                encoding="utf-8",
                decode_responses=True,
            )
        else:
            self._client = client

    @property
    def client(self) -> redis.Redis:
        """Expose the underlying Redis client (useful for tests)."""

        return self._client

    async def ping(self) -> None:
        """Ping Redis to ensure connectivity."""

        await self._client.ping()

    async def close(self) -> None:
        """Close the Redis client."""

        close = getattr(self._client, "close", None)
        if callable(close):
            result = close()
            if inspect.isawaitable(result):
                await result
        wait_closed = getattr(self._client, "wait_closed", None)
        if callable(wait_closed):
            result = wait_closed()
            if inspect.isawaitable(result):
                await result

    async def incr_aggregates(
        self,
        *,
        update_type: str,
        error_type: Optional[str],
        handler: Optional[str],
        now_utc: datetime,
        enable_handler: bool,
    ) -> None:
        """Increment hourly/daily aggregates for the given event."""

        hour_key = now_utc.strftime("metr:v1:agg:hour:%Y%m%d%H")
        day_key = now_utc.strftime("metr:v1:agg:day:%Y%m%d")
        update_field = f"updates_total::{sanitize_label(update_type)}"
        pipe = self._client.pipeline()
        pipe.hincrby(hour_key, update_field, 1)
        pipe.expire(hour_key, self.cfg.retention_hours * 3600)
        pipe.hincrby(day_key, update_field, 1)
        pipe.expire(day_key, self.cfg.retention_days * 86400)

        if error_type:
            error_field = f"errors_total::{sanitize_label(error_type)}::{sanitize_label(update_type)}"
            pipe.hincrby(hour_key, error_field, 1)
            pipe.hincrby(day_key, error_field, 1)

        if enable_handler and handler:
            handler_field = f"handlers_total::{sanitize_label(handler)}"
            pipe.hincrby(hour_key, handler_field, 1)
            pipe.hincrby(day_key, handler_field, 1)

        try:
            await pipe.execute()
        except Exception as exc:
            logger.warning("Redis pipeline execution failed: %s", exc)
            if self.cfg.raise_on_errors:
                raise
