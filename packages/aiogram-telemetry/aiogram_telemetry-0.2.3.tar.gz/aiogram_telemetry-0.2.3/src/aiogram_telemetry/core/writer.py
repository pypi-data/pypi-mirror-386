"""Optional Postgres writers."""

from __future__ import annotations

from typing import Any, Mapping

from ..config import TelemetryConfig
from ..utils.privacy import scrub_payload

try:  # Optional dependency
    from ..storage.postgres import PostgresBackend
    from ..storage.models import TelemetryEvent
except ImportError:  # pragma: no cover - optional dependency
    PostgresBackend = None  # type: ignore[assignment]
    TelemetryEvent = None  # type: ignore[assignment]


async def maybe_write_event_to_pg(
    backend: "PostgresBackend | None",
    cfg: TelemetryConfig,
    ev: Mapping[str, Any],
) -> None:
    """Persist sampled events to Postgres if enabled."""

    if not cfg.enable_postgres or backend is None:
        return
    if TelemetryEvent is None:
        return

    payload = dict(ev)
    payload["attrs"] = scrub_payload(ev.get("attrs", {}))

    async with backend.get_session() as session:
        event = TelemetryEvent(  # type: ignore[call-arg]
            ts=payload["ts"],
            service=payload["service"],
            env=payload["env"],
            update_type=payload["update_type"],
            handler=payload.get("handler"),
            error_type=payload.get("error_type"),
            latency_ms=int(payload["latency_ms"]),
            attrs=payload.get("attrs", {}),
        )
        session.add(event)
        await session.commit()
