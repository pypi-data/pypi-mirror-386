"""Convenience entry point for installing telemetry onto an aiogram dispatcher."""

from __future__ import annotations

import asyncio
from typing import Optional

from aiogram import Dispatcher

from .config import TelemetryConfig
from .core.middleware import HandlerTelemetryMiddleware, UpdateTelemetryMiddleware
from .exporter.prometheus import start_prometheus_server
from .storage.redis_store import RedisStore
from .utils.logging import logger

try:
    from .storage.postgres import PostgresBackend
except ImportError:  # pragma: no cover - optional dependency
    PostgresBackend = None  # type: ignore[assignment]


class TelemetryRuntime:
    """Runtime resources created during telemetry setup."""

    def __init__(self) -> None:
        self.prometheus_task: Optional[asyncio.Task[None]] = None
        self.redis_store: Optional[RedisStore] = None
        self.postgres_backend: Optional["PostgresBackend"] = None


_runtime = TelemetryRuntime()


async def setup_telemetry(dispatcher: Dispatcher, cfg: TelemetryConfig) -> None:
    """Attach telemetry middlewares and supporting services to a dispatcher."""

    redis_store = RedisStore(cfg)
    _runtime.redis_store = redis_store
    try:
        await redis_store.ping()
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("Redis ping failed: %s", exc)
        if cfg.raise_on_errors:
            raise

    if cfg.enable_prometheus:
        _runtime.prometheus_task = start_prometheus_server(cfg)

    postgres_backend: Optional["PostgresBackend"] = None
    if cfg.enable_postgres:
        if PostgresBackend is None:
            message = (
                "Postgres extras not installed. Use pip install aiogram-telemetry[postgres]."
            )
            logger.warning(message)
            if cfg.raise_on_errors:
                raise RuntimeError(message)
        else:
            try:
                postgres_backend = PostgresBackend(cfg)
                _runtime.postgres_backend = postgres_backend
                if cfg.postgres_auto_create:
                    await postgres_backend.create_all()
            except Exception as exc:  # pragma: no cover - network/driver dependent
                logger.warning("Postgres initialization failed: %s", exc)
                if cfg.raise_on_errors:
                    raise

    update_middleware = UpdateTelemetryMiddleware(cfg, redis_store, postgres_backend)
    dispatcher.update.middleware(update_middleware)

    if cfg.enable_detailed:
        dispatcher.message.middleware(HandlerTelemetryMiddleware(cfg))
        dispatcher.callback_query.middleware(HandlerTelemetryMiddleware(cfg))
        dispatcher.inline_query.middleware(HandlerTelemetryMiddleware(cfg))


async def shutdown_telemetry() -> None:
    """Attempt to gracefully shutdown telemetry services."""

    if _runtime.prometheus_task:
        _runtime.prometheus_task.cancel()
        try:
            await _runtime.prometheus_task
        except asyncio.CancelledError:  # pragma: no cover - event loop behavior
            pass
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Error while awaiting prometheus task: %s", exc)

    if _runtime.redis_store is not None:
        await _runtime.redis_store.close()

    if _runtime.postgres_backend is not None:
        await _runtime.postgres_backend.dispose()
