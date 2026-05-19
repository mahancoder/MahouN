"""
MAHOUN Metrics Module
=====================

Prometheus metrics for monitoring and observability.
"""

from mahoun.metrics.mode_enforcement import (
    verdict_generation_blocked_total,
    config_validation_failures_total,
    mode_check_total,
    current_mode,
    graph_enabled,
    verdict_engine_initialized,
    verdict_generation_duration_seconds,
    config_validation_duration_seconds,
    record_blocked_attempt,
    record_mode_check,
    record_config_validation_failure,
    set_current_mode,
    set_graph_enabled,
    set_verdict_engine_initialized,
    record_verdict_generation_duration,
    record_config_validation_duration,
)

from mahoun.metrics.collector import (
    get_metrics_collector,
    MetricsCollector,
    reset_global_collector,
    register_counter,
    register_gauge,
    register_histogram
)
from mahoun.metrics.metrics import Counter, Gauge, Histogram
from mahoun.metrics.store import MetricsStore
from mahoun.metrics.system_provider import SystemMetricsProvider
from mahoun.metrics.snapshot import MetricsSnapshot

__all__ = [
    # Counters
    "verdict_generation_blocked_total",
    "config_validation_failures_total",
    "mode_check_total",
    # Gauges
    "current_mode",
    "graph_enabled",
    "verdict_engine_initialized",
    # Histograms
    "verdict_generation_duration_seconds",
    "config_validation_duration_seconds",
    # Helper functions
    "record_blocked_attempt",
    "record_mode_check",
    "record_config_validation_failure",
    "set_current_mode",
    "set_graph_enabled",
    "set_verdict_engine_initialized",
    "record_verdict_generation_duration",
    "record_config_validation_duration",
    # Metrics Collector
    "get_metrics_collector",
    "MetricsCollector",
    "reset_global_collector",
    "register_counter",
    "register_gauge",
    "register_histogram",
    "Counter",
    "Gauge",
    "Histogram",
    "MetricsStore",
    "SystemMetricsProvider",
    "MetricsSnapshot",
]
