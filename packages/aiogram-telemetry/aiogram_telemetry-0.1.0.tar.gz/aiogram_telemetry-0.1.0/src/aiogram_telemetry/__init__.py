"""Top-level package for aiogram-telemetry."""

from .config import TelemetryConfig
from .core.tracker import track
from .setup import setup_telemetry

__all__ = ["TelemetryConfig", "setup_telemetry", "track"]
