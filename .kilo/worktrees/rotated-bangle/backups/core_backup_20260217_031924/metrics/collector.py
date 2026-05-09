"""
Metrics Collection System
==========================
Centralized metrics collection for all components.

این سیستم metrics را برای monitoring و optimization جمع‌آوری می‌کند:
- Counters: تعداد رویدادها
- Gauges: مقادیر لحظه‌ای
- Timings: مدت زمان اجرا
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Single metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags
        }


class MetricsCollector:
    """
    Thread-safe metrics collector
    
    Usage:
        collector = MetricsCollector()
        collector.record_counter("requests", 1)
        collector.record_gauge("memory_mb", 512.5)
        collector.record_timing("api.latency", 150.5)
    """
    
    def __init__(self, max_history: int = 10000):
        """
        Initialize metrics collector
        
        Args:
            max_history: Maximum number of historical data points per metric
        """
        self.max_history = max_history
        self._metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_history)
        )
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        
        logger.info(f"MetricsCollector initialized (max_history={max_history})")
    
    def record_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """
        Record a counter metric
        
        Counters are cumulative and only increase.
        
        Args:
            name: Metric name
            value: Value to add (default: 1)
            tags: Optional tags for categorization
        """
        with self._lock:
            self._counters[name] += value
            self._metrics[name].append(Metric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {}
            ))
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a gauge metric
        
        Gauges represent current values that can go up or down.
        
        Args:
            name: Metric name
            value: Current value
            tags: Optional tags for categorization
        """
        with self._lock:
            self._gauges[name] = value
            self._metrics[name].append(Metric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {}
            ))
    
    def record_timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a timing metric
        
        Args:
            name: Metric name
            duration_ms: Duration in milliseconds
            tags: Optional tags for categorization
        """
        self.record_gauge(f"{name}.duration_ms", duration_ms, tags)
    
    def get_metrics(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get collected metrics
        
        Args:
            name: Optional metric name to filter by
        
        Returns:
            Dictionary with metrics data
        """
        with self._lock:
            if name:
                # Get specific metric
                return {
                    "name": name,
                    "counter": self._counters.get(name, 0),
                    "gauge": self._gauges.get(name, 0.0),
                    "history": [m.to_dict() for m in self._metrics.get(name, [])],
                    "history_count": len(self._metrics.get(name, []))
                }
            else:
                # Get all metrics
                return {
                    "counters": dict(self._counters),
                    "gauges": dict(self._gauges),
                    "total_metrics": sum(len(h) for h in self._metrics.values()),
                    "unique_metrics": len(self._metrics)
                }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics
        
        Returns:
            Dictionary with summary stats
        """
        with self._lock:
            return {
                "total_counters": len(self._counters),
                "total_gauges": len(self._gauges),
                "total_data_points": sum(len(h) for h in self._metrics.values()),
                "unique_metrics": len(self._metrics),
                "top_counters": sorted(
                    self._counters.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                "timestamp": datetime.now().isoformat()
            }
    
    def reset(self, name: Optional[str] = None):
        """
        Reset metrics
        
        Args:
            name: Optional metric name to reset (resets all if None)
        """
        with self._lock:
            if name:
                if name in self._counters:
                    del self._counters[name]
                if name in self._gauges:
                    del self._gauges[name]
                if name in self._metrics:
                    del self._metrics[name]
                logger.info(f"Reset metric: {name}")
            else:
                self._counters.clear()
                self._gauges.clear()
                self._metrics.clear()
                logger.info("Reset all metrics")


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None
_collector_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """
    Get global metrics collector (singleton)
    
    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    
    if _metrics_collector is None:
        with _collector_lock:
            # Double-check locking
            if _metrics_collector is None:
                _metrics_collector = MetricsCollector()
    
    return _metrics_collector
