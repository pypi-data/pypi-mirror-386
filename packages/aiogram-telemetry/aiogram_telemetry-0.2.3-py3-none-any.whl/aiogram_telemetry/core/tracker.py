"""Decorator utilities for custom telemetry spans."""

from __future__ import annotations

import asyncio
from contextvars import ContextVar, Token
from dataclasses import dataclass
from functools import wraps
from time import perf_counter
from typing import Any, Awaitable, Callable, Dict, Mapping, MutableMapping, TypeVar

from ..utils.labels import sanitize_label
from ..utils.logging import logger
from .metrics import CUSTOM_DURATION

R = TypeVar("R")

_ALLOWED_ATTRS = {"feature", "phase", "route"}
TRACK_ATTR_KEY = "telem_attrs"


@dataclass
class TelemetryContext:
    """Context object shared between middlewares and trackers."""

    service: str
    env: str
    attrs: MutableMapping[str, str]


_context: ContextVar[TelemetryContext | None] = ContextVar("telemetry_context", default=None)
_span_attrs: ContextVar[dict[str, str]] = ContextVar("telemetry_span_attrs", default={})


def enter_context(service: str, env: str, attrs: MutableMapping[str, str]) -> Token[TelemetryContext | None]:
    """Push telemetry context for the current task."""

    return _context.set(TelemetryContext(service=service, env=env, attrs=attrs))


def reset_context(token: Token[TelemetryContext | None]) -> None:
    """Reset telemetry context to a previous state."""

    _context.reset(token)


def get_context() -> TelemetryContext | None:
    """Return the current telemetry context if any."""

    return _context.get()


def _normalize_attrs(attrs: Mapping[str, str] | None) -> Dict[str, str]:
    cleaned: Dict[str, str] = {}
    if not attrs:
        return cleaned
    for key, value in attrs.items():
        if key in _ALLOWED_ATTRS:
            cleaned[key] = sanitize_label(value)
    return cleaned


def track(name: str, attrs: Mapping[str, str] | None = None) -> Callable[[Callable[..., Awaitable[R]]], Callable[..., Awaitable[R]]]:
    """Decorator that records a histogram observation for the wrapped coroutine."""

    def decorator(func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("@track can only decorate async functions")

        metric_name = sanitize_label(name)
        static_attrs = _normalize_attrs(attrs)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> R:
            ctx = get_context()
            if ctx is None:
                return await func(*args, **kwargs)

            parent_attrs = _span_attrs.get()
            base_attrs = dict(parent_attrs) if parent_attrs else {}
            merged_attrs = {**base_attrs, **static_attrs}

            token = _span_attrs.set(merged_attrs)
            start = perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = perf_counter() - start
                feature = merged_attrs.get("feature", "unknown")
                phase = merged_attrs.get("phase", "unknown")
                route = merged_attrs.get("route", "unknown")
                try:
                    CUSTOM_DURATION.labels(
                        service=ctx.service,
                        env=ctx.env,
                        name=metric_name,
                        feature=feature,
                        phase=phase,
                        route=route,
                    ).observe(elapsed)
                except Exception as exc:  # pragma: no cover - prometheus errors
                    logger.warning("Failed to record custom duration: %s", exc)
                finally:
                    _span_attrs.reset(token)

                ctx.attrs.clear()
                if merged_attrs:
                    ctx.attrs.update(merged_attrs)

        setattr(wrapper, "__telem_name__", metric_name)

        return wrapper

    return decorator
