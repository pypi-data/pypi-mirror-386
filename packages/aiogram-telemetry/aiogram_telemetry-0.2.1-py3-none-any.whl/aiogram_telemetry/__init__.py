"""Top-level package for aiogram-telemetry."""

from .config import TelemetryConfig
from .core.tracker import track
from .setup import setup_telemetry

__all__ = ["TelemetryConfig", "setup_telemetry", "track"]

try:
    __version__ = version("aiogram-telemetry")
except PackageNotFoundError:
    __version__ = "0.0.0"