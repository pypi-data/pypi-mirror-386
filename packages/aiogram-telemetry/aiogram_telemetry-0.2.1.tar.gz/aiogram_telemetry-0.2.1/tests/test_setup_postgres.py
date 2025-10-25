from __future__ import annotations

import pytest

from aiogram_telemetry.config import TelemetryConfig
from aiogram_telemetry import setup as telem_setup


class DummyManager:
    def __init__(self) -> None:
        self.middlewares: list[object] = []

    def middleware(self, middleware: object) -> None:
        self.middlewares.append(middleware)


class DummyDispatcher:
    def __init__(self) -> None:
        self.update = DummyManager()
        self.message = DummyManager()
        self.callback_query = DummyManager()
        self.inline_query = DummyManager()


class DummyStore:
    def __init__(self, cfg: TelemetryConfig) -> None:
        self.cfg = cfg

    async def ping(self) -> None:  # pragma: no cover - trivial
        return None

    async def close(self) -> None:  # pragma: no cover - trivial
        return None

    async def incr_aggregates(self, **_: object) -> None:  # pragma: no cover - unused
        return None


@pytest.mark.asyncio
async def test_postgres_missing_extras(monkeypatch: pytest.MonkeyPatch, caplog) -> None:
    monkeypatch.setattr(telem_setup, "RedisStore", DummyStore)
    monkeypatch.setattr(telem_setup, "PostgresBackend", None)

    cfg = TelemetryConfig(enable_postgres=True, enable_prometheus=False)
    dispatcher = DummyDispatcher()

    caplog.set_level("WARNING")
    await telem_setup.setup_telemetry(dispatcher, cfg)
    assert any("Postgres extras not installed" in record.message for record in caplog.records)

    await telem_setup.shutdown_telemetry()


@pytest.mark.asyncio
async def test_postgres_init_failure(monkeypatch: pytest.MonkeyPatch, caplog) -> None:
    monkeypatch.setattr(telem_setup, "RedisStore", DummyStore)

    class FailingBackend:
        def __init__(self, cfg: TelemetryConfig) -> None:
            raise ConnectionError("pg unavailable")

    monkeypatch.setattr(telem_setup, "PostgresBackend", FailingBackend)

    cfg = TelemetryConfig(enable_postgres=True, enable_prometheus=False, raise_on_errors=False)
    dispatcher = DummyDispatcher()

    caplog.set_level("WARNING")
    await telem_setup.setup_telemetry(dispatcher, cfg)
    assert any("Postgres initialization failed" in record.message for record in caplog.records)

    await telem_setup.shutdown_telemetry()


@pytest.mark.asyncio
async def test_postgres_init_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(telem_setup, "RedisStore", DummyStore)

    class FailingBackend:
        def __init__(self, cfg: TelemetryConfig) -> None:
            raise ConnectionError("pg unavailable")

    monkeypatch.setattr(telem_setup, "PostgresBackend", FailingBackend)

    cfg = TelemetryConfig(enable_postgres=True, enable_prometheus=False, raise_on_errors=True)
    dispatcher = DummyDispatcher()

    with pytest.raises(ConnectionError):
        await telem_setup.setup_telemetry(dispatcher, cfg)

    # cleanup runtime to avoid leakage
    await telem_setup.shutdown_telemetry()
