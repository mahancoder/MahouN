"""Refactored Metrics Collector - Enterprise Orchestrator"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List

from ..config import ObservabilityConfig, get_observability_config
from .store import MetricsStore
from .system_provider import SystemMetricsProvider
from .snapshot import MetricsSnapshot
from .metrics import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Enterprise-grade metrics collector with explicit lifecycle management."""
    
    def __init__(
        self,
        config: Optional[ObservabilityConfig] = None,
        store: Optional[MetricsStore] = None,
        system_provider: Optional[SystemMetricsProvider] = None
    ) -> None:
        self._config = config or get_observability_config()
        self._store = store or MetricsStore()
        
        if system_provider is None:
            self._system_provider = SystemMetricsProvider(start_time=time.time())
        else:
            self._system_provider = system_provider
        
        logger.info("MetricsCollector initialized")
    
    def collect_system_metrics(self) -> None:
        """EXPLICIT system metrics collection."""
        if not self._config.metrics_enabled:
            return
        
        if self._system_provider is None:
            return
        
        try:
            system_metrics = self._system_provider.collect()
            
            if not system_metrics:
                return
            
            for name, value in system_metrics.items():
                gauge = self._store.register_gauge(name)
                gauge.set(value)
            
            logger.debug(f"Collected {len(system_metrics)} system metrics")
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def snapshot(self) -> Dict[str, Any]:
        """PURE snapshot of current metrics state."""
        if not self._config.metrics_enabled:
            return {"counters": {}, "gauges": {}, "histograms": {}}
        
        return self._store.snapshot()
    
    def create_immutable_snapshot(self) -> MetricsSnapshot:
        """Create immutable snapshot with audit metadata."""
        return MetricsSnapshot.create(self._store)
    
    def reset(self) -> None:
        """Deterministic reset of all metrics."""
        self._store.reset()
        logger.info("All metrics reset")
    
    def to_prometheus(self) -> str:
        """PURE Prometheus export without state mutation."""
        if not self._config.metrics_enabled:
            return "# Metrics disabled"
        
        snapshot_data = self._store.snapshot()
        return self._format_prometheus(snapshot_data)
    
    def _format_prometheus(self, snapshot_data: Dict[str, Any]) -> str:
        """Format snapshot data as Prometheus metrics with HELP and TYPE."""
        lines = []
        
        try:
            # Group metrics by base name for HELP/TYPE headers
            counter_names = set()
            gauge_names = set()
            histogram_names = set()
            
            # Extract base names from keys (remove label part)
            for key in snapshot_data.get("counters", {}).keys():
                # Extract name before '{' if labels exist
                base_name = key.split('{')[0] if '{' in key else key
                counter_names.add(base_name)
            
            for key in snapshot_data.get("gauges", {}).keys():
                base_name = key.split('{')[0] if '{' in key else key
                gauge_names.add(base_name)
            
            for key in snapshot_data.get("histograms", {}).keys():
                base_name = key.split('{')[0] if '{' in key else key
                histogram_names.add(base_name)
            
            # Counters with HELP and TYPE
            for name in sorted(counter_names):
                lines.append(f'# HELP {name} Counter metric')
                lines.append(f'# TYPE {name} counter')
                
                # Add all variants (with and without labels)
                for key, counter_data in snapshot_data.get("counters", {}).items():
                    base_name = key.split('{')[0] if '{' in key else key
                    if base_name == name:
                        value = counter_data["value"]
                        labels = counter_data.get("labels", {})
                        
                        if labels:
                            label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                            lines.append(f'{name}{{{label_str}}} {value}')
                        else:
                            lines.append(f'{name} {value}')
            
            # Gauges with HELP and TYPE
            for name in sorted(gauge_names):
                lines.append(f'# HELP {name} Gauge metric')
                lines.append(f'# TYPE {name} gauge')
                
                for key, gauge_data in snapshot_data.get("gauges", {}).items():
                    base_name = key.split('{')[0] if '{' in key else key
                    if base_name == name:
                        value = gauge_data["value"]
                        labels = gauge_data.get("labels", {})
                        
                        if labels:
                            label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                            lines.append(f'{name}{{{label_str}}} {value}')
                        else:
                            lines.append(f'{name} {value}')
            
            # Histograms with HELP and TYPE
            for name in sorted(histogram_names):
                lines.append(f'# HELP {name} Histogram metric')
                lines.append(f'# TYPE {name} histogram')
                
                for key, histogram_data in snapshot_data.get("histograms", {}).items():
                    base_name = key.split('{')[0] if '{' in key else key
                    if base_name == name:
                        count = histogram_data["count"]
                        labels = histogram_data.get("labels", {})
                        
                        label_part = ""
                        if labels:
                            label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                            label_part = f'{{{label_str}}}'
                        
                        lines.append(f'{name}_count{label_part} {count}')
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Failed to format Prometheus metrics: {e}")
            return f"# Error formatting metrics: {e}"
    
    def register_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> Counter:
        """Register counter metric."""
        return self._store.register_counter(name, labels)
    
    def register_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Gauge:
        """Register gauge metric."""
        return self._store.register_gauge(name, labels)
    
    def register_histogram(
        self, 
        name: str, 
        buckets: Optional[List[float]] = None, 
        labels: Optional[Dict[str, str]] = None
    ) -> Histogram:
        """Register histogram metric."""
        return self._store.register_histogram(name, buckets, labels)
    
    def get_counter(self, name: str) -> Optional[Counter]:
        """Get counter by name."""
        return self._store.get_counter(name)
    
    def get_gauge(self, name: str) -> Optional[Gauge]:
        """Get gauge by name."""
        return self._store.get_gauge(name)
    
    def get_histogram(self, name: str) -> Optional[Histogram]:
        """Get histogram by name."""
        return self._store.get_histogram(name)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics (backward compatible)."""
        return self.snapshot()
    
    def update_system_metrics(self) -> None:
        """Update system metrics (DEPRECATED)."""
        logger.warning("update_system_metrics() is deprecated. Use collect_system_metrics().")
        self.collect_system_metrics()
    
    def get_collector_info(self) -> Dict[str, Any]:
        """Get information about the collector state."""
        return {
            "metrics_enabled": self._config.metrics_enabled,
            "system_provider_available": (
                self._system_provider.is_available() 
                if self._system_provider else False
            ),
            "metric_counts": self._store._get_metric_counts(),
            "architecture": "refactored"
        }
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        info = self.get_collector_info()
        return (f"MetricsCollector(enabled={info['metrics_enabled']}, "
                f"system_available={info['system_provider_available']}, "
                f"metrics={info['metric_counts']})")


# Global singleton
_metrics_instance: Optional[MetricsCollector] = None
_metrics_lock = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance (singleton)."""
    global _metrics_instance
    
    if _metrics_instance is None:
        with _metrics_lock:
            if _metrics_instance is None:
                _metrics_instance = MetricsCollector()
                logger.info("Global MetricsCollector instance created")
    
    return _metrics_instance


def reset_global_collector() -> None:
    """Reset the global collector instance."""
    global _metrics_instance
    
    with _metrics_lock:
        _metrics_instance = None
        logger.info("Global MetricsCollector instance reset")


def register_counter(name: str, labels: Optional[Dict[str, str]] = None) -> Counter:
    """Register a counter metric (convenience function)."""
    return get_metrics_collector().register_counter(name, labels)


def register_gauge(name: str, labels: Optional[Dict[str, str]] = None) -> Gauge:
    """Register a gauge metric (convenience function)."""
    return get_metrics_collector().register_gauge(name, labels)


def register_histogram(
    name: str, 
    buckets: Optional[List[float]] = None, 
    labels: Optional[Dict[str, str]] = None
) -> Histogram:
    """Register a histogram metric (convenience function)."""
    return get_metrics_collector().register_histogram(name, buckets, labels)
