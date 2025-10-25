"""Telemetry configuration using pydantic-settings."""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings


class TelemetryConfig(BaseSettings):
    """Configuration options for aiogram telemetry."""

    service_name: str = "bot"
    environment: str = "dev"

    # Redis
    redis_dsn: str = "redis://localhost:6379/0"
    retention_hours: int = 24 * 30
    retention_days: int = 365

    # Behavior
    sampling_rate: float = 1.0
    anonymize: bool = False
    enable_detailed: bool = False
    raise_on_errors: bool = False

    # Prometheus
    enable_prometheus: bool = True
    prometheus_host: str = "0.0.0.0"
    prometheus_port: int = 9102
    prometheus_path: str = "/metrics"

    # Postgres (optional)
    enable_postgres: bool = False
    postgres_dsn: str | None = None
    postgres_schema: str = "public"
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 10
    postgres_echo: bool = False
    postgres_auto_create: bool = False

    model_config = {
        "env_prefix": "TELEM_",
        "extra": "ignore",
    }

    @field_validator("sampling_rate")
    @classmethod
    def _validate_sampling(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("sampling_rate must be between 0 and 1")
        return value

    @field_validator("prometheus_port")
    @classmethod
    def _validate_port(cls, value: int) -> int:
        if not 0 < value < 65536:
            raise ValueError("prometheus_port must be between 1 and 65535")
        return value

    @field_validator("prometheus_path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("prometheus_path must start with '/'")
        return value
