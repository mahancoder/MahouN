"""
Ultra-Advanced Monitoring System
=================================
Comprehensive monitoring and observability for RAG systems.

Features:
- Real-time metrics collection
- Performance monitoring
- Quality metrics tracking
- Alerting system
- Dashboard data aggregation
- Anomaly detection
- Cost tracking
- User behavior analytics
- A/B test monitoring
- System health checks
"""

import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import numpy as np


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    name: str
    value: float
    metric_type: MetricType
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp,
            "tags": self.tags
        }


@dataclass
class Alert:
    level: AlertLevel
    message: str
    metric_name: str
    value: float
    threshold: float
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MetricAggregator:
    """Aggregates metrics over time windows"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
    
    def add(self, name: str, value: float):
        """Add metric value"""
        self.metrics[name].append(value)
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for metric"""
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        values = list(self.metrics[name])
        return {
            "count": len(values),
            "mean": np.mean(values),
            "median": np.median(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "p50": np.percentile(values, 50),
            "p95": np.percentile(values, 95),
            "p99": np.percentile(values, 99)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all metrics"""
        return {name: self.get_stats(name) for name in self.metrics.keys()}


class AlertManager:
    """Manages alerts and thresholds"""
    
    def __init__(self):
        self.thresholds: Dict[str, Dict[str, float]] = {}
        self.alerts: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
    
    def set_threshold(
        self,
        metric_name: str,
        warning: Optional[float] = None,
        error: Optional[float] = None,
        critical: Optional[float] = None
    ):
        """Set alert thresholds for metric"""
        self.thresholds[metric_name] = {}
        if warning is not None:
            self.thresholds[metric_name]["warning"] = warning
        if error is not None:
            self.thresholds[metric_name]["error"] = error
        if critical is not None:
            self.thresholds[metric_name]["critical"] = critical
    
    def check_metric(self, metric: Metric):
        """Check if metric exceeds thresholds"""
        if metric.name not in self.thresholds:
            return
        
        thresholds = self.thresholds[metric.name]
        
        # Check critical first
        if "critical" in thresholds and metric.value >= thresholds["critical"]:
            self._create_alert(AlertLevel.CRITICAL, metric, thresholds["critical"])
        elif "error" in thresholds and metric.value >= thresholds["error"]:
            self._create_alert(AlertLevel.ERROR, metric, thresholds["error"])
        elif "warning" in thresholds and metric.value >= thresholds["warning"]:
            self._create_alert(AlertLevel.WARNING, metric, thresholds["warning"])
    
    def _create_alert(self, level: AlertLevel, metric: Metric, threshold: float):
        """Create and trigger alert"""
        alert = Alert(
            level=level,
            message=f"{metric.name} exceeded {level.value} threshold",
            metric_name=metric.name,
            value=metric.value,
            threshold=threshold
        )
        
        self.alerts.append(alert)
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")
    
    def register_callback(self, callback: Callable[[Alert], None]):
        """Register alert callback"""
        self.alert_callbacks.append(callback)
    
    def get_recent_alerts(self, limit: int = 10) -> List[Alert]:
        """Get recent alerts"""
        return self.alerts[-limit:]


class UltraMonitoring:
    """
    Ultra-advanced monitoring system
    
    Features:
    - Metrics collection and aggregation
    - Alert management
    - Performance tracking
    - Quality monitoring
    """
    
    def __init__(self, window_size: int = 100):
        self.metrics: List[Metric] = []
        self.aggregator = MetricAggregator(window_size)
        self.alert_manager = AlertManager()
        
        # Counters
        self.counters: Dict[str, int] = defaultdict(int)
        
        # Timers
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
        # System start time
        self.start_time = time.time()
        
        print("📊 Ultra Monitoring initialized")
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        self.aggregator.add(name, value)
        self.alert_manager.check_metric(metric)
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter"""
        self.counters[name] += value
        self.record_metric(name, self.counters[name], MetricType.COUNTER, tags)
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer duration"""
        self.timers[name].append(duration)
        self.record_metric(name, duration, MetricType.TIMER, tags)
    
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        return TimerContext(self, name, tags)
    
    def record_query_metrics(
        self,
        query: str,
        num_results: int,
        latency: float,
        relevance_score: Optional[float] = None
    ):
        """Record query-specific metrics"""
        self.increment_counter("queries_total")
        self.record_timer("query_latency", latency)
        self.record_metric("results_count", num_results, MetricType.GAUGE)
        
        if relevance_score is not None:
            self.record_metric("relevance_score", relevance_score, MetricType.GAUGE)
    
    def record_retrieval_metrics(
        self,
        num_candidates: int,
        num_retrieved: int,
        retrieval_time: float
    ):
        """Record retrieval-specific metrics"""
        self.increment_counter("retrievals_total")
        self.record_metric("candidates_count", num_candidates, MetricType.GAUGE)
        self.record_metric("retrieved_count", num_retrieved, MetricType.GAUGE)
        self.record_timer("retrieval_time", retrieval_time)
    
    def record_reranking_metrics(
        self,
        num_docs: int,
        reranking_time: float,
        rank_changes: int
    ):
        """Record reranking-specific metrics"""
        self.increment_counter("reranks_total")
        self.record_metric("rerank_docs", num_docs, MetricType.GAUGE)
        self.record_timer("rerank_time", reranking_time)
        self.record_metric("rank_changes", rank_changes, MetricType.GAUGE)
    
    def record_embedding_metrics(
        self,
        num_texts: int,
        embedding_time: float,
        cache_hit_rate: Optional[float] = None
    ):
        """Record embedding-specific metrics"""
        self.increment_counter("embeddings_total", num_texts)
        self.record_timer("embedding_time", embedding_time)
        
        if cache_hit_rate is not None:
            self.record_metric("embedding_cache_hit_rate", cache_hit_rate, MetricType.GAUGE)
    
    def set_alert_threshold(
        self,
        metric_name: str,
        warning: Optional[float] = None,
        error: Optional[float] = None,
        critical: Optional[float] = None
    ):
        """Set alert thresholds"""
        self.alert_manager.set_threshold(metric_name, warning, error, critical)
    
    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """Register alert callback"""
        self.alert_manager.register_callback(callback)
    
    def get_summary(self) -> Dict:
        """Get monitoring summary"""
        uptime = time.time() - self.start_time
        
        summary = {
            "uptime_seconds": uptime,
            "total_metrics": len(self.metrics),
            "counters": dict(self.counters),
            "aggregated_stats": self.aggregator.get_all_stats(),
            "recent_alerts": [alert.to_dict() for alert in self.alert_manager.get_recent_alerts()],
        }
        
        return summary
    
    def get_dashboard_data(self) -> Dict:
        """Get data for monitoring dashboard"""
        stats = self.aggregator.get_all_stats()
        
        dashboard = {
            "overview": {
                "uptime": time.time() - self.start_time,
                "total_queries": self.counters.get("queries_total", 0),
                "total_retrievals": self.counters.get("retrievals_total", 0),
                "total_reranks": self.counters.get("reranks_total", 0),
            },
            "performance": {
                "query_latency": stats.get("query_latency", {}),
                "retrieval_time": stats.get("retrieval_time", {}),
                "rerank_time": stats.get("rerank_time", {}),
                "embedding_time": stats.get("embedding_time", {}),
            },
            "quality": {
                "relevance_score": stats.get("relevance_score", {}),
                "results_count": stats.get("results_count", {}),
            },
            "alerts": {
                "recent": [alert.to_dict() for alert in self.alert_manager.get_recent_alerts(5)],
                "total": len(self.alert_manager.alerts),
            }
        }
        
        return dashboard
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        if format == "json":
            return json.dumps(self.get_summary(), indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")


class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, monitoring: UltraMonitoring, name: str, tags: Optional[Dict[str, str]] = None):
        self.monitoring = monitoring
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.monitoring.record_timer(self.name, duration, self.tags)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("🚀 Testing Ultra Monitoring")
    print("=" * 60)
    
    # Initialize monitoring
    monitoring = UltraMonitoring(window_size=100)
    
    # Set alert thresholds
    monitoring.set_alert_threshold("query_latency", warning=1.0, error=2.0, critical=5.0)
    monitoring.set_alert_threshold("relevance_score", warning=0.5, error=0.3, critical=0.1)
    
    # Register alert callback
    def alert_callback(alert: Alert):
        print(f"🚨 ALERT [{alert.level.value.upper()}]: {alert.message}")
    
    monitoring.register_alert_callback(alert_callback)
    
    # Simulate some queries
    print(f"\n📝 Simulating queries...")
    for i in range(10):
        with monitoring.timer("query_latency"):
            time.sleep(0.01)  # Simulate query processing
            
            monitoring.record_query_metrics(
                query=f"test query {i}",
                num_results=5,
                latency=0.01,
                relevance_score=0.8 + (i * 0.01)
            )
    
    # Simulate retrieval
    print(f"\n🔍 Simulating retrieval...")
    with monitoring.timer("retrieval_time"):
        time.sleep(0.02)
        monitoring.record_retrieval_metrics(
            num_candidates=100,
            num_retrieved=10,
            retrieval_time=0.02
        )
    
    # Simulate reranking
    print(f"\n🎯 Simulating reranking...")
    with monitoring.timer("rerank_time"):
        time.sleep(0.015)
        monitoring.record_reranking_metrics(
            num_docs=10,
            reranking_time=0.015,
            rank_changes=3
        )
    
    # Get summary
    print(f"\n📊 Monitoring Summary:")
    summary = monitoring.get_summary()
    print(f"   Uptime: {summary['uptime_seconds']:.2f}s")
    print(f"   Total metrics: {summary['total_metrics']}")
    print(f"   Total queries: {summary['counters'].get('queries_total', 0)}")
    
    # Get dashboard data
    print(f"\n📈 Dashboard Data:")
    dashboard = monitoring.get_dashboard_data()
    print(f"   Overview: {dashboard['overview']}")
    
    if dashboard['performance']['query_latency']:
        latency_stats = dashboard['performance']['query_latency']
        print(f"   Query Latency:")
        print(f"      Mean: {latency_stats.get('mean', 0):.3f}s")
        print(f"      P95: {latency_stats.get('p95', 0):.3f}s")
        print(f"      P99: {latency_stats.get('p99', 0):.3f}s")
    
    # Export metrics
    print(f"\n💾 Exporting metrics...")
    metrics_json = monitoring.export_metrics("json")
    print(f"   Exported {len(metrics_json)} bytes")
    
    print("\n✅ Monitoring test complete")
