"""Prometheus metric definitions."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

HISTOGRAM_BUCKETS = [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]

UPDATES_TOTAL = Counter(
    "aiogram_updates_total",
    "Total number of aiogram updates processed.",
    labelnames=("service", "env", "update_type"),
)

ERRORS_TOTAL = Counter(
    "aiogram_errors_total",
    "Total number of aiogram handler errors.",
    labelnames=("service", "env", "update_type", "error_type"),
)

UPDATE_LATENCY = Histogram(
    "aiogram_update_latency_seconds",
    "Latency of aiogram update processing in seconds.",
    labelnames=("service", "env", "update_type"),
    buckets=HISTOGRAM_BUCKETS,
)

HANDLER_DURATION = Histogram(
    "aiogram_handler_duration_seconds",
    "Duration of aiogram handler execution in seconds.",
    labelnames=("service", "env", "update_type", "handler"),
    buckets=HISTOGRAM_BUCKETS,
)

CUSTOM_DURATION = Histogram(
    "aiogram_custom_duration_seconds",
    "Custom duration measurements captured via @track.",
    labelnames=("service", "env", "name", "feature", "phase", "route"),
    buckets=HISTOGRAM_BUCKETS,
)
