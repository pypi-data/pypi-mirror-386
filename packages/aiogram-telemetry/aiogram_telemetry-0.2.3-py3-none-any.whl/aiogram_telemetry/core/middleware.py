"""Aiogram middlewares that emit telemetry."""

from __future__ import annotations

import random
from contextvars import ContextVar, Token
from time import perf_counter
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware

from ..config import TelemetryConfig
from ..utils.clocks import utc_now
from ..utils.labels import handler_label, sanitize_label
from ..utils.logging import logger
from .metrics import ERRORS_TOTAL, HANDLER_DURATION, UPDATE_LATENCY, UPDATES_TOTAL
from ..storage.redis_store import RedisStore
from ..core.tracker import TRACK_ATTR_KEY, enter_context, reset_context

try:  # Optional Postgres
    from ..storage.postgres import PostgresBackend
except ImportError:  # pragma: no cover - optional dependency
    PostgresBackend = None  # type: ignore[assignment]

HandlerType = Callable[[Any, Dict[str, Any]], Awaitable[Any]]

_CURRENT_HANDLER: ContextVar[str | None] = ContextVar(
    "aiogram_telemetry_current_handler", default=None
)
_HANDLER_TOKEN_KEY = "_telem_handler_token"
_SAMPLED_FLAG: ContextVar[bool] = ContextVar(
    "aiogram_telemetry_sampled", default=True
)


def resolve_update_type(event: Any) -> str:
    """Best-effort resolution of the update type."""

    if hasattr(event, "event_type"):
        update_type = getattr(event, "event_type")
        if isinstance(update_type, str):
            return sanitize_label(update_type)
    if hasattr(event, "update_type"):
        update_type = getattr(event, "update_type")
        if isinstance(update_type, str):
            return sanitize_label(update_type)
    if hasattr(event, "message"):
        return "message"
    if hasattr(event, "callback_query"):
        return "callback_query"
    name = event.__class__.__name__ if hasattr(event, "__class__") else "update"
    return sanitize_label(name.lower())


def resolve_handler_name(handler: HandlerType) -> str:
    """Derive a stable handler name for metrics."""

    telem_name = getattr(handler, "__telem_name__", None)
    if telem_name:
        return handler_label(telem_name)
    qualname = getattr(handler, "__qualname__", None)
    if isinstance(qualname, str):
        return handler_label(qualname)
    name = getattr(handler, "__name__", None)
    if isinstance(name, str):
        return handler_label(name)
    return "unknown"


class UpdateTelemetryMiddleware(BaseMiddleware):
    """Middleware attached to updates, responsible for coarse telemetry."""

    def __init__(
        self,
        cfg: TelemetryConfig,
        store: RedisStore,
        postgres_backend: Optional["PostgresBackend"],
    ) -> None:
        self.cfg = cfg
        self.store = store
        self.postgres_backend = postgres_backend

    async def __call__(
        self,
        handler: HandlerType,
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        sampled = True
        sample_token: Token[bool] | None = None
        if self.cfg.sampling_rate < 1.0:
            sampled = random.random() <= self.cfg.sampling_rate
        if not sampled:
            sample_token = _SAMPLED_FLAG.set(False)
            try:
                return await handler(event, data)
            finally:
                if sample_token is not None:
                    _SAMPLED_FLAG.reset(sample_token)

        sample_token = _SAMPLED_FLAG.set(True)

        update_type = resolve_update_type(event)
        data["telem_update_type"] = update_type

        start = perf_counter()
        now = utc_now()
        error_type: str | None = None

        context_store: Dict[str, str] = data.setdefault(TRACK_ATTR_KEY, {})
        token = enter_context(self.cfg.service_name, self.cfg.environment, context_store)
        try:
            result = await handler(event, data)
            return result
        except Exception as exc:
            error_type = sanitize_label(exc.__class__.__name__)
            try:
                ERRORS_TOTAL.labels(
                    service=self.cfg.service_name,
                    env=self.cfg.environment,
                    update_type=update_type,
                    error_type=error_type,
                ).inc()
            except Exception as metric_exc:  # pragma: no cover - prometheus errors
                logger.warning("Failed to record error counter: %s", metric_exc)
            raise
        finally:
            reset_context(token)
            handler_token = data.pop(_HANDLER_TOKEN_KEY, None)
            handler_name: str | None = None
            if self.cfg.enable_detailed:
                handler_name = _CURRENT_HANDLER.get()
            elapsed = perf_counter() - start
            try:
                UPDATES_TOTAL.labels(
                    service=self.cfg.service_name,
                    env=self.cfg.environment,
                    update_type=update_type,
                ).inc()
                UPDATE_LATENCY.labels(
                    service=self.cfg.service_name,
                    env=self.cfg.environment,
                    update_type=update_type,
                ).observe(elapsed)
            except Exception as metric_exc:  # pragma: no cover - prometheus errors
                logger.warning("Failed to record update metrics: %s", metric_exc)

            enable_handler = self.cfg.enable_detailed and handler_name is not None
            try:
                await self.store.incr_aggregates(
                    update_type=update_type,
                    error_type=error_type,
                    handler=handler_name,
                    now_utc=now,
                    enable_handler=enable_handler,
                )
            except Exception as store_exc:
                logger.warning("Redis aggregate increment failed: %s", store_exc)
                if self.cfg.raise_on_errors:
                    if handler_token is not None:
                        _CURRENT_HANDLER.reset(handler_token)
                    if sample_token is not None:
                        _SAMPLED_FLAG.reset(sample_token)
                    raise

            if self.postgres_backend is not None:
                from .writer import maybe_write_event_to_pg

                event_payload = {
                    "ts": now,
                    "service": self.cfg.service_name,
                    "env": self.cfg.environment,
                    "update_type": update_type,
                    "handler": handler_name if enable_handler else None,
                    "error_type": error_type,
                    "latency_ms": elapsed * 1000.0,
                    "attrs": data.get(TRACK_ATTR_KEY, {}),
                }
                try:
                    await maybe_write_event_to_pg(self.postgres_backend, self.cfg, event_payload)
                except Exception as exc:
                    logger.warning("Postgres write failed: %s", exc)
                    if self.cfg.raise_on_errors:
                        if handler_token is not None:
                            _CURRENT_HANDLER.reset(handler_token)
                        if sample_token is not None:
                            _SAMPLED_FLAG.reset(sample_token)
                        raise

            if handler_token is not None:
                try:
                    _CURRENT_HANDLER.reset(handler_token)
                except LookupError:
                    logger.debug("Handler context already reset")
            if sample_token is not None:
                _SAMPLED_FLAG.reset(sample_token)


class HandlerTelemetryMiddleware(BaseMiddleware):
    """Middleware measuring handler execution when detailed telemetry is enabled."""

    def __init__(self, cfg: TelemetryConfig) -> None:
        self.cfg = cfg

    async def __call__(
        self,
        handler: HandlerType,
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        if not _SAMPLED_FLAG.get():
            return await handler(event, data)
        update_type = data.get("telem_update_type", resolve_update_type(event))
        handler_name = resolve_handler_name(handler)
        token = _CURRENT_HANDLER.set(handler_name)
        data[_HANDLER_TOKEN_KEY] = token
        start = perf_counter()
        try:
            return await handler(event, data)
        finally:
            elapsed = perf_counter() - start
            try:
                HANDLER_DURATION.labels(
                    service=self.cfg.service_name,
                    env=self.cfg.environment,
                    update_type=update_type,
                    handler=handler_name,
                ).observe(elapsed)
            except Exception as exc:  # pragma: no cover - prometheus errors
                logger.warning("Failed to record handler duration: %s", exc)
