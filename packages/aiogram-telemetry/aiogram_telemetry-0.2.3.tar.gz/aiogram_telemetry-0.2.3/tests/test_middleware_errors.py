from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from prometheus_client import REGISTRY

from aiogram_telemetry.config import TelemetryConfig
from aiogram_telemetry.core.middleware import HandlerTelemetryMiddleware, UpdateTelemetryMiddleware
from aiogram_telemetry.core.tracker import track
from aiogram_telemetry.storage.redis_store import RedisStore
from aiogram_telemetry.utils.labels import sanitize_label
from tests.conftest import FakeRedis


@pytest.mark.asyncio
async def test_handler_exception_records_errors(redis_client, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = TelemetryConfig(
        redis_dsn="redis://localhost:6379/15",
        enable_detailed=True,
        sampling_rate=1.0,
    )
    store = RedisStore(cfg, client=redis_client)
    update_middleware = UpdateTelemetryMiddleware(cfg, store, None)
    handler_middleware = HandlerTelemetryMiddleware(cfg)

    async def failing_handler(event, data):
        raise ValueError("boom")

    async def wrapped_handler(event, data):
        return await handler_middleware(failing_handler, event, data)

    event = SimpleNamespace(event_type="message")
    data: dict[str, object] = {}

    error_labels = {
        "service": cfg.service_name,
        "env": cfg.environment,
        "update_type": "message",
        "error_type": "ValueError",
    }
    before_errors = REGISTRY.get_sample_value("aiogram_errors_total_total", error_labels) or 0.0

    fixed_now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("aiogram_telemetry.core.middleware.utc_now", lambda: fixed_now)
    monkeypatch.setattr("aiogram_telemetry.core.middleware.random.random", lambda: 0.0)

    with pytest.raises(ValueError):
        await update_middleware(wrapped_handler, event, data)

    after_errors = REGISTRY.get_sample_value("aiogram_errors_total_total", error_labels) or 0.0
    assert after_errors == pytest.approx(before_errors + 1.0)

    hour_key = "metr:v1:agg:hour:2024010112"
    day_key = "metr:v1:agg:day:20240101"
    assert await redis_client.hget(hour_key, "errors_total::ValueError::message") == "1"
    assert await redis_client.hget(day_key, "errors_total::ValueError::message") == "1"
    handler_label = sanitize_label(failing_handler.__qualname__)
    assert await redis_client.hget(hour_key, f"handlers_total::{handler_label}") == "1"

    await store.close()


@pytest.mark.asyncio
async def test_redis_pipeline_failure_logging(redis_client, caplog, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = TelemetryConfig(redis_dsn="redis://localhost:6379/15", raise_on_errors=False)
    store = RedisStore(cfg, client=redis_client)
    update_middleware = UpdateTelemetryMiddleware(cfg, store, None)

    class FailingPipeline:
        def hincrby(self, *args, **kwargs) -> "FailingPipeline":
            return self

        def expire(self, *args, **kwargs) -> "FailingPipeline":
            return self

        async def execute(self) -> None:
            raise ConnectionError("redis down")

    monkeypatch.setattr(redis_client, "pipeline", lambda: FailingPipeline())

    async def final_handler(event, data):
        return "ok"

    event = SimpleNamespace(event_type="message")
    data: dict[str, object] = {}

    caplog.set_level("WARNING")
    result = await update_middleware(final_handler, event, data)
    assert result == "ok"
    assert any("Redis pipeline execution failed" in record.message for record in caplog.records)

    await store.close()


@pytest.mark.asyncio
async def test_redis_pipeline_failure_raises_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = TelemetryConfig(redis_dsn="redis://localhost:6379/15", raise_on_errors=True)
    fake_client = FakeRedis(decode_responses=True)
    store = RedisStore(cfg, client=fake_client)
    update_middleware = UpdateTelemetryMiddleware(cfg, store, None)

    class FailingPipeline:
        def hincrby(self, *args, **kwargs) -> "FailingPipeline":
            return self

        def expire(self, *args, **kwargs) -> "FailingPipeline":
            return self

        async def execute(self) -> None:
            raise ConnectionError("redis down")

    monkeypatch.setattr(fake_client, "pipeline", lambda: FailingPipeline())

    async def final_handler(event, data):
        return "ok"

    event = SimpleNamespace(event_type="message")
    data: dict[str, object] = {}

    with pytest.raises(ConnectionError):
        await update_middleware(final_handler, event, data)

    await store.close()


@pytest.mark.asyncio
async def test_handler_name_propagation(redis_client, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = TelemetryConfig(
        redis_dsn="redis://localhost:6379/15",
        enable_detailed=True,
    )
    store = RedisStore(cfg, client=redis_client)
    update_middleware = UpdateTelemetryMiddleware(cfg, store, None)
    handler_middleware = HandlerTelemetryMiddleware(cfg)

    @track("tracked_handler")
    async def tracked_handler(event, data):
        return "ok"

    async def wrapped_handler(event, data):
        return await handler_middleware(tracked_handler, event, data)

    event = SimpleNamespace(event_type="message")
    data: dict[str, object] = {}

    fixed_now = datetime(2024, 1, 2, 9, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("aiogram_telemetry.core.middleware.utc_now", lambda: fixed_now)

    await update_middleware(wrapped_handler, event, data)

    hour_key = "metr:v1:agg:hour:2024010209"
    assert await redis_client.hget(hour_key, "handlers_total::tracked_handler") == "1"

    await store.close()


@pytest.mark.asyncio
async def test_handler_counts_disabled(redis_client, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = TelemetryConfig(redis_dsn="redis://localhost:6379/15", enable_detailed=False)
    store = RedisStore(cfg, client=redis_client)
    update_middleware = UpdateTelemetryMiddleware(cfg, store, None)

    async def final_handler(event, data):
        return "ok"

    event = SimpleNamespace(event_type="message")
    data: dict[str, object] = {}

    fixed_now = datetime(2024, 1, 3, 9, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("aiogram_telemetry.core.middleware.utc_now", lambda: fixed_now)

    await update_middleware(final_handler, event, data)

    hour_key = "metr:v1:agg:hour:2024010309"
    handler_label = sanitize_label(final_handler.__qualname__)
    assert await redis_client.hget(hour_key, f"handlers_total::{handler_label}") is None

    await store.close()
