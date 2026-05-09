"""
Anomaly Detection System
========================

Enterprise-grade anomaly detection for monitoring system health.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import logging

log = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """System alert"""
    id: str
    metric_name: str
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnomalyDetectionSystem:
    """
    Anomaly detection for system monitoring.
    
    Features:
    - Threshold-based alerting
    - Statistical anomaly detection
    - Alert management
    """
    
    def __init__(self):
        """Initialize anomaly detection system"""
        self.alerts: List[Alert] = []
        self.thresholds: Dict[str, Dict[str, float]] = {
            "latency_ms": {"warning": 500, "error": 1000, "critical": 2000},
            "error_rate": {"warning": 0.01, "error": 0.05, "critical": 0.1},
            "memory_usage": {"warning": 0.7, "error": 0.85, "critical": 0.95},
            "cpu_usage": {"warning": 0.7, "error": 0.85, "critical": 0.95},
        }
        self._alert_counter = 0
        log.info("AnomalyDetectionSystem initialized")
    
    def check_metric(
        self,
        metric_name: str,
        value: float,
        custom_thresholds: Optional[Dict[str, float]] = None
    ) -> Optional[Alert]:
        """
        Check if a metric value triggers an alert.
        
        Args:
            metric_name: Name of the metric
            value: Current metric value
            custom_thresholds: Optional custom thresholds
            
        Returns:
            Alert if triggered, None otherwise
        """
        thresholds = custom_thresholds or self.thresholds.get(metric_name, {})
        
        if not thresholds:
            return None
        
        # Check thresholds in order of severity
        severity: Optional[Any] = None
        threshold: Optional[Any] = None
        if value >= thresholds.get("critical", float("inf")):
            severity = AlertSeverity.CRITICAL
            threshold = thresholds["critical"]
        elif value >= thresholds.get("error", float("inf")):
            severity = AlertSeverity.ERROR
            threshold = thresholds["error"]
        elif value >= thresholds.get("warning", float("inf")):
            severity = AlertSeverity.WARNING
            threshold = thresholds["warning"]
        
        if severity:
            self._alert_counter += 1
            alert = Alert(
                id=f"alert_{self._alert_counter}",
                metric_name=metric_name,
                severity=severity,
                message=f"{metric_name} is {severity.value}: {value} >= {threshold}",
                value=value,
                threshold=threshold,
            )
            self.alerts.append(alert)
            log.warning(f"Alert triggered: {alert.message}")
            return alert
        
        return None
    
    def get_all_alerts(
        self,
        severity: Optional[str] = None,
        limit: int = 100,
        include_resolved: bool = False
    ) -> List[Alert]:
        """
        Get all alerts, optionally filtered.
        
        Args:
            severity: Filter by severity
            limit: Maximum number of alerts
            include_resolved: Include resolved alerts
            
        Returns:
            List of alerts
        """
        alerts = self.alerts
        
        if not include_resolved:
            alerts = [a for a in alerts if not a.resolved]
        
        if severity:
            alerts = [a for a in alerts if a.severity.value == severity]
        
        # Sort by timestamp descending
        alerts = sorted(alerts, key=lambda a: a.timestamp, reverse=True)
        
        return alerts[:limit]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        Mark an alert as resolved.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if alert was found and resolved
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                log.info(f"Alert {alert_id} resolved")
                return True
        return False
    
    def clear_alerts(self) -> int:
        """
        Clear all alerts.
        
        Returns:
            Number of alerts cleared
        """
        count = len(self.alerts)
        self.alerts.clear()
        log.info(f"Cleared {count} alerts")
        return count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        active_alerts = [a for a in self.alerts if not a.resolved]
        
        by_severity: Dict[str, Any] = {}
        for alert in active_alerts:
            severity = alert.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(active_alerts),
            "resolved_alerts": len(self.alerts) - len(active_alerts),
            "by_severity": by_severity,
        }

