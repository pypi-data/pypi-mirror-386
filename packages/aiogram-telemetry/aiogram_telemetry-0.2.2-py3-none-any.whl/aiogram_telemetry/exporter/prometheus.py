"""Prometheus exporter for aiogram telemetry."""

from __future__ import annotations

import asyncio

from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from ..config import TelemetryConfig
from ..utils.logging import logger


async def _serve_prometheus(cfg: TelemetryConfig) -> None:
    app = web.Application()

    async def handle_metrics(_: web.Request) -> web.Response:
        data = generate_latest()
        return web.Response(body=data, content_type=CONTENT_TYPE_LATEST)

    app.router.add_get(cfg.prometheus_path, handle_metrics)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=cfg.prometheus_host, port=cfg.prometheus_port)
    try:
        await site.start()
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:  # pragma: no cover - expected during shutdown
        raise
    except Exception as exc:  # pragma: no cover - server lifecycle errors
        logger.warning("Prometheus server error: %s", exc)
    finally:
        await runner.cleanup()


def start_prometheus_server(cfg: TelemetryConfig) -> asyncio.Task[None]:
    """Start the Prometheus exporter in the background."""

    loop = asyncio.get_running_loop()
    return loop.create_task(_serve_prometheus(cfg))
