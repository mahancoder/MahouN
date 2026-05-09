# MAHOUN Health System
"""
Enhanced health system with metrics integration.
"""

import asyncio
import logging
import threading
import time

try:
    import psutil
except ImportError:
    psutil: Optional[Any] = None
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .metrics import get_metrics_collector
from ..config import get_observability_config

logger = logging.getLogger(__name__)


@dataclass
class ComponentStatus:
    """Status of a system component."""
    name: str
    healthy: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    last_check: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class HealthReport:
    """Complete health report."""
    overall_healthy: bool
    uptime_seconds: float
    cpu_percent: float
    memory_bytes: int
    components: Dict[str, ComponentStatus] = field(default_factory=dict)
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class HealthSystem:
    """
    Enhanced health system with metrics integration.
    
    Provides comprehensive health reporting.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize health system.
        
        Args:
            config: ObservabilityConfig (default: from get_observability_config)
        """
        from ..config import ObservabilityConfig, get_observability_config
        
        self.config = config or get_observability_config()
        self.metrics = get_metrics_collector()
        self._start_time = time.time()
        self._last_agent_failures: List[Dict[str, Any]] = []
        self._pending_tasks_count: int = 0
    
    async def check_health(self) -> HealthReport:
        """
        Perform comprehensive health check.
        
        Returns:
            HealthReport with all health information
        """
        # System metrics
        if psutil is not None:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
        else:
            cpu_percent = 0.0
            memory = type('obj', (object,), {'used': 0})()
        
        uptime = time.time() - self._start_time
        
        # Component checks
        components: Dict[str, Any] = {}
        # Check vector store
        try:
            from mahoun.pipelines.vector_store.manager import VectorStoreManager
            manager = VectorStoreManager()
            stats = manager.get_stats()
            components["vector_store"] = ComponentStatus(
                name="vector_store",
                healthy=True,
                message="VectorStore is operational",
                details={"stats": stats}
            )
        except Exception as e:
            components["vector_store"] = ComponentStatus(
                name="vector_store",
                healthy=False,
                message=f"VectorStore check failed: {str(e)}",
                details={"error": str(e)}
            )
        
        # Check graph (if enabled)
        try:
            from mahoun.core.runtime_config import should_skip_graph
            if not should_skip_graph():
                from mahoun.graph.ultra_graph_builder import UltraGraphBuilder
                components["graph"] = ComponentStatus(
                    name="graph",
                    healthy=True,
                    message="Graph system is enabled"
                )
            else:
                components["graph"] = ComponentStatus(
                    name="graph",
                    healthy=True,
                    message="Graph system is disabled (expected)"
                )
        except Exception as e:
            components["graph"] = ComponentStatus(
                name="graph",
                healthy=False,
                message=f"Graph check failed: {str(e)}"
            )
        
        # Check agents
        try:
            from mahoun.agents.orchestrator import UltraOrchestrator
            orchestrator = UltraOrchestrator()
            agent_count = len(orchestrator.agents)
            components["agents"] = ComponentStatus(
                name="agents",
                healthy=True,
                message=f"{agent_count} agents registered",
                details={"agent_count": agent_count}
            )
        except Exception as e:
            components["agents"] = ComponentStatus(
                name="agents",
                healthy=False,
                message=f"Agents check failed: {str(e)}"
            )
        
        # Overall health
        overall_healthy = all(c.healthy for c in components.values())
        
        # Metrics summary
        all_metrics = self.metrics.get_all_metrics()
        metrics_summary = {
            "request_count": all_metrics.get("counters", {}).get("mahoun_requests_total", {}).get("value", 0),
            "error_count": all_metrics.get("counters", {}).get("mahoun_errors_total", {}).get("value", 0),
            "avg_latency_ms": all_metrics.get("histograms", {}).get("mahoun_request_latency_ms", {}).get("percentiles", {}).get("p50", 0.0)
        }
        
        return HealthReport(
            overall_healthy=overall_healthy,
            uptime_seconds=uptime,
            cpu_percent=cpu_percent,
            memory_bytes=memory.used,
            components=components,
            metrics_summary=metrics_summary
        )
    
    def record_agent_failure(self, agent_name: str, error: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record an agent failure.
        
        Args:
            agent_name: Name of the agent
            error: Error message
            metadata: Additional metadata
        """
        failure_record = {
            "agent": agent_name,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self._last_agent_failures.append(failure_record)
        
        # Keep only last 10 failures
        if len(self._last_agent_failures) > 10:
            self._last_agent_failures = self._last_agent_failures[-10:]
    
    def get_last_failures(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get last agent failures.
        
        Args:
            limit: Number of failures to return
            
        Returns:
            List of failure records
        """
        return self._last_agent_failures[-limit:]
    
    def set_pending_tasks_count(self, count: int) -> None:
        """Set pending tasks count."""
        self._pending_tasks_count = count
    
    def get_pending_tasks_count(self) -> int:
        """Get pending tasks count."""
        return self._pending_tasks_count


# Global health system instance
_health_instance: Optional[HealthSystem] = None
_health_lock = threading.Lock()


def get_health_system() -> HealthSystem:
    """Get global health system instance (singleton)."""
    global _health_instance
    
    if _health_instance is None:
        with _health_lock:
            if _health_instance is None:
                _health_instance = HealthSystem()
    
    return _health_instance

