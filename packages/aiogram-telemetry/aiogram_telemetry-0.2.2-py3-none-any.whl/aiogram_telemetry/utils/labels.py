"""Label sanitization helpers."""

from __future__ import annotations

import re

_MAX_LABEL_LENGTH = 80
_ALLOWED_RE = re.compile(r"[^a-zA-Z0-9_:]+")


def sanitize_label(value: str | None) -> str:
    """Normalize a label value by stripping illegal characters and length."""

    if not value:
        return "unknown"
    cleaned = _ALLOWED_RE.sub("_", value)
    if len(cleaned) > _MAX_LABEL_LENGTH:
        cleaned = cleaned[:_MAX_LABEL_LENGTH]
    return cleaned


def handler_label(handler_name: str | None) -> str:
    """Return a sanitized handler label."""

    return sanitize_label(handler_name)
