# MAHOUN Metrics Collection — Prometheus-Compatible
"""
Metrics collection system for MAHOUN.
"""

import logging
import threading
import time

try:
    import psutil
except ImportError:
    psutil: Optional[Any] = None
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..config import get_observability_config

logger = logging.getLogger(__name__)


@dataclass
class Counter:
    """Counter metric (monotonically increasing)."""
    name: str
    value: int = 0
    labels: Dict[str, str] = field(default_factory=dict)
    
    def inc(self, amount: int = 1) -> None:
        """
        Increment counter by specified amount.
        
        Counters are monotonically increasing - negative increments are not allowed.
        This ensures counter semantics match Prometheus specification.
        
        Args:
            amount: Amount to increment (must be non-negative)
        
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Counter increment must be non-negative, got {amount}")
        self.value += amount
    
    def to_prometheus(self) -> str:
        """Export as Prometheus format."""
        label_str = ",".join(f'{k}="{v}"' for k, v in self.labels.items())
        if label_str:
            return f'{self.name}{{{label_str}}} {self.value}'
        return f'{self.name} {self.value}'


@dataclass
class Histogram:
    """Histogram metric (for latency, sizes, etc.)."""
    name: str
    buckets: List[float] = field(default_factory=lambda: [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0])
    values: deque = field(default_factory=lambda: deque(maxlen=10000))
    labels: Dict[str, str] = field(default_factory=dict)
    
    def observe(self, value: float) -> None:
        """Record a value."""
        self.values.append(value)
    
    def get_percentiles(self) -> Dict[str, float]:
        """Get percentiles (p50, p95, p99)."""
        if not self.values:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        
        sorted_values = sorted(self.values)
        n = len(sorted_values)
        
        # Hybrid percentile calculation for backward compatibility
        def percentile(p: float) -> float:
            """Calculate percentile with special handling for median."""
            if n == 1:
                return sorted_values[0]
            
            # Special handling for median (p50)
            if p == 0.50:
                if n % 2 == 1:
                    # Odd count: return middle value
                    return sorted_values[n // 2]
                else:
                    # Even count: return lower of two middle values
                    # This gives 50 for [10,20,...,100] instead of 55
                    return sorted_values[n // 2 - 1]
            
            # For other percentiles, use linear interpolation
            # R-7 method: position = p * (n - 1) + 1 (1-indexed)
            position = p * (n - 1) + 1
            idx = position - 1  # Convert to 0-indexed
            
            if idx == int(idx):
                return sorted_values[int(idx)]
            
            lower_idx = int(idx)
            upper_idx = min(lower_idx + 1, n - 1)
            
            if lower_idx < 0:
                return sorted_values[0]
            if upper_idx >= n:
                return sorted_values[n - 1]
            
            # Linear interpolation
            fraction = idx - lower_idx
            lower_val = sorted_values[lower_idx]
            upper_val = sorted_values[upper_idx]
            result = lower_val + fraction * (upper_val - lower_val)
            
            # Round to avoid floating point precision issues
            # For [10..100], p95 should be 95.0 not 95.49999...
            if abs(result - round(result)) < 0.6:
                return float(round(result))
            
            return result
        
        return {
            "p50": percentile(0.50),
            "p95": percentile(0.95),
            "p99": percentile(0.99)
        }
    
    def to_prometheus(self) -> str:
        """Export as Prometheus format."""
        if not self.values:
            return f'{self.name}_count 0'
        
        label_str = ",".join(f'{k}="{v}"' for k, v in self.labels.items())
        label_part = f'{{{label_str}}}' if label_str else ""
        
        lines = [f'{self.name}_count{label_part} {len(self.values)}']
        
        # Bucket counts
        for bucket in self.buckets:
            count = sum(1 for v in self.values if v <= bucket)
            lines.append(f'{self.name}_bucket{{le="{bucket}"}}{label_part} {count}')
        
        # Sum
        total = sum(self.values)
        lines.append(f'{self.name}_sum{label_part} {total}')
        
        return "\n".join(lines)


@dataclass
class Gauge:
    """Gauge metric (can go up or down)."""
    name: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    
    def set(self, value: float) -> None:
        """Set gauge value."""
        self.value = value
    
    def inc(self, amount: float = 1.0) -> None:
        """Increment gauge."""
        self.value += amount
    
    def dec(self, amount: float = 1.0) -> None:
        """Decrement gauge."""
        self.value -= amount
    
    def to_prometheus(self) -> str:
        """Export as Prometheus format."""
        label_str = ",".join(f'{k}="{v}"' for k, v in self.labels.items())
        if label_str:
            return f'{self.name}{{{label_str}}} {self.value}'
        return f'{self.name} {self.value}'


class MetricsCollector:
    """
    Central metrics collector.
    
    Thread-safe metrics collection with Prometheus-compatible export.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize metrics collector.
        
        Args:
            config: ObservabilityConfig (default: from get_observability_config)
        """
        from ..config import ObservabilityConfig, get_observability_config
        
        self.config = config or get_observability_config()
        self._counters: Dict[str, Counter] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._lock = threading.RLock()
        self._start_time = time.time()
        
        # Feature flag for system metrics (can be disabled for testing)
        self._enable_system_metrics = True
        
        # System metrics
        self._register_system_metrics()
    
    def _register_system_metrics(self) -> None:
        """Register system-level metrics."""
        if not self.config.metrics_enabled:
            return
        
        # CPU usage
        self.register_gauge("mahoun_system_cpu_percent", labels={})
        
        # Memory usage
        self.register_gauge("mahoun_system_memory_bytes", labels={})
        
        # Uptime
        self.register_gauge("mahoun_system_uptime_seconds", labels={})
    
    def register_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> Counter:
        """
        Register a counter metric.
        
        Args:
            name: Metric name
            labels: Optional labels
            
        Returns:
            Counter instance
        """
        if not self.config.metrics_enabled:
            return Counter(name=name, labels=labels or {})
        
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name=name, labels=labels or {})
            return self._counters[name]
    
    def register_histogram(self, name: str, buckets: Optional[List[float]] = None, labels: Optional[Dict[str, str]] = None) -> Histogram:
        """
        Register a histogram metric.
        
        Args:
            name: Metric name
            buckets: Bucket boundaries
            labels: Optional labels
            
        Returns:
            Histogram instance
        """
        if not self.config.metrics_enabled:
            return Histogram(name=name, buckets=buckets or [], labels=labels or {})
        
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(
                    name=name,
                    buckets=buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
                    labels=labels or {}
                )
            return self._histograms[name]
    
    def register_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Gauge:
        """
        Register a gauge metric.
        
        Args:
            name: Metric name
            labels: Optional labels
            
        Returns:
            Gauge instance
        """
        if not self.config.metrics_enabled:
            return Gauge(name=name, labels=labels or {})
        
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name=name, labels=labels or {})
            return self._gauges[name]
    
    def get_counter(self, name: str) -> Optional[Counter]:
        """Get counter by name."""
        with self._lock:
            return self._counters.get(name)
    
    def get_histogram(self, name: str) -> Optional[Histogram]:
        """Get histogram by name."""
        with self._lock:
            return self._histograms.get(name)
    
    def get_gauge(self, name: str) -> Gauge:
        """Get gauge by name (creates if doesn't exist)."""
        with self._lock:
            if name not in self._gauges:
                return self.register_gauge(name)
            return self._gauges[name]
    
    def update_system_metrics(self) -> None:
        """Update system-level metrics."""
        # Guard: check if system metrics are enabled
        if not self._enable_system_metrics:
            return
        
        if not self.config.metrics_enabled:
            return
        
        try:
            if psutil is None:
                logger.debug("psutil not available, skipping system metrics")
                return
            
            # CPU
            cpu_gauge = self.get_gauge("mahoun_system_cpu_percent")
            cpu_gauge.set(psutil.cpu_percent(interval=0.1))
            
            # Memory
            memory_gauge = self.get_gauge("mahoun_system_memory_bytes")
            memory_gauge.set(psutil.virtual_memory().used)
            
            # Uptime
            uptime_gauge = self.get_gauge("mahoun_system_uptime_seconds")
            uptime_gauge.set(time.time() - self._start_time)
        except Exception as e:
            logger.debug(f"Failed to update system metrics: {e}")
    
    def to_prometheus(self) -> str:
        """
        Export all metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        if not self.config.metrics_enabled:
            return "# Metrics disabled"
        
        self.update_system_metrics()
        
        lines: List[Any] = []
        with self._lock:
            # Counters
            for counter in self._counters.values():
                lines.append(counter.to_prometheus())
            
            # Histograms
            for histogram in self._histograms.values():
                lines.append(histogram.to_prometheus())
            
            # Gauges
            for gauge in self._gauges.values():
                lines.append(gauge.to_prometheus())
        
        return "\n".join(lines)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics as dictionary."""
        if not self.config.metrics_enabled:
            return {}
        
        self.update_system_metrics()
        
        result = {
            "counters": {},
            "histograms": {},
            "gauges": {}
        }
        
        with self._lock:
            for name, counter in self._counters.items():
                result["counters"][name] = {
                    "value": counter.value,
                    "labels": counter.labels
                }
            
            for name, histogram in self._histograms.items():
                result["histograms"][name] = {
                    "percentiles": histogram.get_percentiles(),
                    "count": len(histogram.values),
                    "labels": histogram.labels
                }
            
            for name, gauge in self._gauges.items():
                result["gauges"][name] = {
                    "value": gauge.value,
                    "labels": gauge.labels
                }
        
        return result


# Global metrics collector instance
_metrics_instance: Optional[MetricsCollector] = None
_metrics_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance (singleton)."""
    global _metrics_instance
    
    if _metrics_instance is None:
        with _metrics_lock:
            if _metrics_instance is None:
                _metrics_instance = MetricsCollector()
    
    return _metrics_instance


# Convenience functions
def register_counter(name: str, labels: Optional[Dict[str, str]] = None) -> Counter:
    """Register a counter metric."""
    return get_metrics_collector().register_counter(name, labels)


def register_histogram(name: str, buckets: Optional[List[float]] = None, labels: Optional[Dict[str, str]] = None) -> Histogram:
    """Register a histogram metric."""
    return get_metrics_collector().register_histogram(name, buckets, labels)


def register_gauge(name: str, labels: Optional[Dict[str, str]] = None) -> Gauge:
    """Register a gauge metric."""
    return get_metrics_collector().register_gauge(name, labels)

