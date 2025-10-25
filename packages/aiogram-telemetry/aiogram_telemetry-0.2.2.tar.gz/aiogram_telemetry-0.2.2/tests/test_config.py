from __future__ import annotations

import pytest

from aiogram_telemetry.config import TelemetryConfig


def test_config_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEM_SERVICE_NAME", "demo-bot")
    monkeypatch.setenv("TELEM_PROMETHEUS_PORT", "9200")
    cfg = TelemetryConfig()
    assert cfg.service_name == "demo-bot"
    assert cfg.prometheus_port == 9200


def test_config_invalid_port() -> None:
    with pytest.raises(ValueError):
        TelemetryConfig(prometheus_port=0)


def test_config_invalid_path() -> None:
    with pytest.raises(ValueError):
        TelemetryConfig(prometheus_path="metrics")


def test_config_invalid_sampling() -> None:
    with pytest.raises(ValueError):
        TelemetryConfig(sampling_rate=1.5)
