"""Storage backends for aiogram telemetry."""

from .redis_store import RedisStore

__all__ = ["RedisStore"]
