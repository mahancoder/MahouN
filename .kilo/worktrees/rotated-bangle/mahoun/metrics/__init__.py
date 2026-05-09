# MAHOUN Metrics & Health System
"""
Prometheus-compatible metrics and health system with enterprise-grade architecture.

Architecture:
    - MetricsStore: Pure state container
    - SystemMetricsProvider: Isolated system metrics collector
    - MetricsSnapshot: Immutable audit-grade snapshots
    - MetricsCollector: Orchestrator with explicit lifecycle

Backward Compatibility:
    All existing imports continue to work. The refactored architecture
    is used internally while preserving the public API.
"""

# Metric types (from original implementation) - import first to avoid circular deps
from .metrics import Counter, Histogram, Gauge

# New architecture components
from .store import MetricsStore
from .system_provider import SystemMetricsProvider
from .snapshot import MetricsSnapshot, METRICS_SCHEMA_VERSION

# Refactored collector (uses new architecture internally)
from .collector import (
    MetricsCollector,
    get_metrics_collector,
    reset_global_collector,
    register_counter,
    register_histogram,
    register_gauge
)

# Health system
from .health import HealthSystem, get_health_system

__all__ = [
    # New architecture components
    "MetricsStore",
    "SystemMetricsProvider",
    "MetricsSnapshot",
    "METRICS_SCHEMA_VERSION",
    
    # Main collector (refactored)
    "MetricsCollector",
    "get_metrics_collector",
    "reset_global_collector",
    
    # Metric types
    "Counter",
    "Histogram",
    "Gauge",
    
    # Convenience functions
    "register_counter",
    "register_histogram",
    "register_gauge",
    
    # Health system
    "HealthSystem",
    "get_health_system",
]

