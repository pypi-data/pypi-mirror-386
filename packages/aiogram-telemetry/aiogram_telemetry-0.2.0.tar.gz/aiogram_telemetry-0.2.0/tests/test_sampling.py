from __future__ import annotations

from types import SimpleNamespace

import pytest
from prometheus_client import REGISTRY

from aiogram_telemetry.config import TelemetryConfig
from aiogram_telemetry.core.middleware import HandlerTelemetryMiddleware, UpdateTelemetryMiddleware
from aiogram_telemetry.storage.redis_store import RedisStore


@pytest.mark.asyncio
async def test_sampling_drops_all(redis_client, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = TelemetryConfig(
        redis_dsn="redis://localhost:6379/15",
        sampling_rate=0.0,
        enable_detailed=True,
    )
    store = RedisStore(cfg, client=redis_client)
    update_middleware = UpdateTelemetryMiddleware(cfg, store, None)
    handler_middleware = HandlerTelemetryMiddleware(cfg)

    async def final_handler(event, data):
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

    monkeypatch.setattr("aiogram_telemetry.core.middleware.random.random", lambda: 0.5)
    result = await update_middleware(wrapped_handler, event, data)
    assert result == "ok"

    assert (
        REGISTRY.get_sample_value("aiogram_updates_total_total", labels) or 0.0
    ) == pytest.approx(before_updates)
    assert await redis_client.keys("*") == []

    await store.close()


@pytest.mark.asyncio
async def test_sampling_accept_and_drop(redis_client, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = TelemetryConfig(
        redis_dsn="redis://localhost:6379/15",
        sampling_rate=0.5,
        enable_detailed=False,
    )
    store = RedisStore(cfg, client=redis_client)
    update_middleware = UpdateTelemetryMiddleware(cfg, store, None)

    async def final_handler(event, data):
        return "ok"

    event = SimpleNamespace(event_type="message")
    data: dict[str, object] = {}
    labels = {
        "service": cfg.service_name,
        "env": cfg.environment,
        "update_type": "message",
    }

    monkeypatch.setattr("aiogram_telemetry.core.middleware.random.random", lambda: 0.25)
    before = REGISTRY.get_sample_value("aiogram_updates_total_total", labels) or 0.0
    result = await update_middleware(final_handler, event, data)
    assert result == "ok"
    after = REGISTRY.get_sample_value("aiogram_updates_total_total", labels) or 0.0
    assert after == pytest.approx(before + 1.0)

    monkeypatch.setattr("aiogram_telemetry.core.middleware.random.random", lambda: 0.75)
    result = await update_middleware(final_handler, event, data)
    assert result == "ok"
    assert (
        REGISTRY.get_sample_value("aiogram_updates_total_total", labels) or 0.0
    ) == pytest.approx(after)

    await store.close()
