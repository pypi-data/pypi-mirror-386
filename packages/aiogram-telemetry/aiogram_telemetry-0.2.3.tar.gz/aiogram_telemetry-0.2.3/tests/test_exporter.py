from __future__ import annotations

import asyncio

import pytest
from aiohttp import ClientSession
from aiohttp.test_utils import unused_port

from aiogram_telemetry.config import TelemetryConfig
from aiogram_telemetry.exporter.prometheus import start_prometheus_server


@pytest.mark.asyncio
async def test_prometheus_exporter_lifecycle() -> None:
    cfg = TelemetryConfig(
        enable_prometheus=True,
        prometheus_host="127.0.0.1",
        prometheus_port=unused_port(),
        prometheus_path="/metrics-test",
    )

    task = start_prometheus_server(cfg)
    await asyncio.sleep(0.05)
    try:
        async with ClientSession() as session:
            url = f"http://{cfg.prometheus_host}:{cfg.prometheus_port}{cfg.prometheus_path}"
            async with session.get(url) as response:
                assert response.status == 200
                body = await response.text()
                assert "aiogram_updates_total" in body
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
