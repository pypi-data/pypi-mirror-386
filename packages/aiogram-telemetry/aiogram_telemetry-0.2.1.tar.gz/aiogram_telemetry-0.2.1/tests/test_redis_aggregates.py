from __future__ import annotations

from datetime import datetime, timezone

import pytest

from aiogram_telemetry.config import TelemetryConfig
from aiogram_telemetry.storage.redis_store import RedisStore


@pytest.mark.asyncio
async def test_redis_aggregates(redis_client) -> None:
    cfg = TelemetryConfig(redis_dsn="redis://localhost:6379/15")
    store = RedisStore(cfg, client=redis_client)

    now = datetime(2024, 1, 1, 12, 30, tzinfo=timezone.utc)

    await store.incr_aggregates(
        update_type="message",
        error_type=None,
        handler="greet",
        now_utc=now,
        enable_handler=True,
    )
    await store.incr_aggregates(
        update_type="message",
        error_type="ValueError",
        handler="greet",
        now_utc=now,
        enable_handler=True,
    )

    hour_key = "metr:v1:agg:hour:2024010112"
    day_key = "metr:v1:agg:day:20240101"

    hour_fields = await redis_client.hgetall(hour_key)
    day_fields = await redis_client.hgetall(day_key)

    assert hour_fields["updates_total::message"] == "2"
    assert day_fields["updates_total::message"] == "2"
    assert hour_fields["errors_total::ValueError::message"] == "1"
    assert day_fields["errors_total::ValueError::message"] == "1"
    assert hour_fields["handlers_total::greet"] == "2"

    hour_ttl = await redis_client.ttl(hour_key)
    day_ttl = await redis_client.ttl(day_key)
    assert hour_ttl <= cfg.retention_hours * 3600
    assert day_ttl <= cfg.retention_days * 86400

    await store.close()
