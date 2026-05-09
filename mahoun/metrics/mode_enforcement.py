"""
Mode Enforcement Metrics
=========================

Prometheus metrics for dual-mode enforcement monitoring.

Tracks:
- Blocked verdict generation attempts
- Mode distribution
- Configuration validation failures

Note: Gracefully degrades if prometheus_client is not installed.
"""

from typing import Optional

# Try to import prometheus_client, gracefully degrade if not available
try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create no-op classes
    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            pass
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def set(self, *args, **kwargs):
            pass
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def observe(self, *args, **kwargs):
            pass

# ============================================================================
# Counters
# ============================================================================

verdict_generation_blocked_total = Counter(
    "mahoun_verdict_generation_blocked_total",
    "Total number of verdict generation attempts blocked due to mode constraints",
    labelnames=["mode", "reason", "entry_point"],
)

config_validation_failures_total = Counter(
    "mahoun_config_validation_failures_total",
    "Total number of configuration validation failures at startup",
    labelnames=["validation_rule", "mode"],
)

mode_check_total = Counter(
    "mahoun_mode_check_total",
    "Total number of mode checks performed",
    labelnames=["mode", "graph_enabled", "result"],
)

# ============================================================================
# Gauges
# ============================================================================

current_mode = Gauge(
    "mahoun_current_mode",
    "Current runtime mode (0=desktop_minimal, 1=server_full)",
    labelnames=["mode"],
)

graph_enabled = Gauge(
    "mahoun_graph_enabled",
    "Whether graph operations are enabled (0=disabled, 1=enabled)",
)

verdict_engine_initialized = Gauge(
    "mahoun_verdict_engine_initialized",
    "Whether verdict engine is initialized (0=no, 1=yes)",
)

# ============================================================================
# Histograms
# ============================================================================

verdict_generation_duration_seconds = Histogram(
    "mahoun_verdict_generation_duration_seconds",
    "Time spent generating verdicts",
    labelnames=["mode", "success"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, float("inf")),
)

config_validation_duration_seconds = Histogram(
    "mahoun_config_validation_duration_seconds",
    "Time spent validating configuration at startup",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, float("inf")),
)


# ============================================================================
# Helper Functions
# ============================================================================


def record_blocked_attempt(
    mode: str, reason: str, entry_point: str = "unknown"
) -> None:
    """
    Record a blocked verdict generation attempt.
    
    Args:
        mode: Runtime mode (desktop_minimal, server_full)
        reason: Reason for blocking (graph_disabled, resource_constraint, etc.)
        entry_point: Where the block occurred (api, engine, mcp, etc.)
    """
    verdict_generation_blocked_total.labels(
        mode=mode, reason=reason, entry_point=entry_point
    ).inc()


def record_mode_check(mode: str, graph_enabled: bool, passed: bool) -> None:
    """
    Record a mode check.
    
    Args:
        mode: Runtime mode
        graph_enabled: Whether graph is enabled
        passed: Whether check passed (True) or blocked (False)
    """
    result = "passed" if passed else "blocked"
    mode_check_total.labels(
        mode=mode, graph_enabled=str(graph_enabled).lower(), result=result
    ).inc()


def record_config_validation_failure(validation_rule: str, mode: str) -> None:
    """
    Record a configuration validation failure.
    
    Args:
        validation_rule: Which validation rule failed
        mode: Runtime mode
    """
    config_validation_failures_total.labels(
        validation_rule=validation_rule, mode=mode
    ).inc()


def set_current_mode(mode: str) -> None:
    """
    Set current runtime mode gauge.
    
    Args:
        mode: Runtime mode (desktop_minimal, server_full)
    """
    # Clear all mode labels first
    current_mode.labels(mode="desktop_minimal").set(0)
    current_mode.labels(mode="server_full").set(0)
    
    # Set current mode
    if mode == "desktop_minimal":
        current_mode.labels(mode="desktop_minimal").set(1)
    elif mode == "server_full":
        current_mode.labels(mode="server_full").set(1)


def set_graph_enabled(enabled: bool) -> None:
    """
    Set graph enabled gauge.
    
    Args:
        enabled: Whether graph is enabled
    """
    graph_enabled.set(1 if enabled else 0)


def set_verdict_engine_initialized(initialized: bool) -> None:
    """
    Set verdict engine initialized gauge.
    
    Args:
        initialized: Whether engine is initialized
    """
    verdict_engine_initialized.set(1 if initialized else 0)


def record_verdict_generation_duration(
    duration_seconds: float, mode: str, success: bool
) -> None:
    """
    Record verdict generation duration.
    
    Args:
        duration_seconds: Duration in seconds
        mode: Runtime mode
        success: Whether generation succeeded
    """
    verdict_generation_duration_seconds.labels(
        mode=mode, success=str(success).lower()
    ).observe(duration_seconds)


def record_config_validation_duration(duration_seconds: float) -> None:
    """
    Record configuration validation duration.
    
    Args:
        duration_seconds: Duration in seconds
    """
    config_validation_duration_seconds.observe(duration_seconds)
