"""Privacy helpers for telemetry events."""

from __future__ import annotations

from typing import Mapping


def scrub_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    """Return a sanitized copy of the payload.

    Currently this is a passthrough; hooks are provided for future anonymization.
    """

    return payload
