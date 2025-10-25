from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from prometheus_client import REGISTRY

from aiogram_telemetry.config import TelemetryConfig
from aiogram_telemetry.core.middleware import HandlerTelemetryMiddleware, UpdateTelemetryMiddleware
from aiogram_telemetry.storage.redis_store import RedisStore
from aiogram_telemetry.utils.labels import sanitize_label


@pytest.mark.asyncio
async def test_middleware_basic(redis_client) -> None:
    cfg = TelemetryConfig(redis_dsn="redis://localhost:6379/15", enable_detailed=True)
    store = RedisStore(cfg, client=redis_client)
    update_middleware = UpdateTelemetryMiddleware(cfg, store, None)
    handler_middleware = HandlerTelemetryMiddleware(cfg)

    async def final_handler(event, data):
        await asyncio.sleep(0.01)
        return "ok"

    async def wrapped_handler(event, data):
        return await handler_middleware(final_handler, event, data)

    event = SimpleNamespace(event_type="message")
    data: dict[str, object] = {}

    labels = {
        "service": cfg.service_name,
        "env": cfg.environment,
        "update_type": "message",
    }
    before_updates = REGISTRY.get_sample_value("aiogram_updates_total_total", labels) or 0.0
    before_latency = (
        REGISTRY.get_sample_value("aiogram_update_latency_seconds_count", labels) or 0.0
    )
    handler_label = sanitize_label(final_handler.__qualname__)
    handler_labels = {
        "service": cfg.service_name,
        "env": cfg.environment,
        "update_type": "message",
        "handler": handler_label,
    }
    before_handler = (
        REGISTRY.get_sample_value("aiogram_handler_duration_seconds_count", handler_labels)
        or 0.0
    )

    result = await update_middleware(wrapped_handler, event, data)
    assert result == "ok"

    assert REGISTRY.get_sample_value("aiogram_updates_total_total", labels) == pytest.approx(
        before_updates + 1.0
    )
    assert REGISTRY.get_sample_value("aiogram_update_latency_seconds_count", labels) == pytest.approx(
        before_latency + 1.0
    )
    assert REGISTRY.get_sample_value("aiogram_handler_duration_seconds_count", handler_labels) == pytest.approx(
        before_handler + 1.0
    )

    await store.close()
