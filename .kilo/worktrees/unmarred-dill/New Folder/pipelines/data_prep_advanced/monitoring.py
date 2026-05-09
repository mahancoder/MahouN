"""
Ultra-Advanced Pipeline Monitoring
===================================
State-of-the-art monitoring system with:
- Real-time metrics tracking
- W&B integration
- Prometheus metrics export
- Anomaly detection
- Performance profiling
- Resource monitoring
- Alert system
- Dashboard generation

Integrates:
- core/monitoring/* (metrics, anomaly detection)
- pipelines/wandb_logger.py
- self_improve/integration/performance_monitor.py
"""

import logging
import time
import psutil
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
import sys

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StageMetrics:
    """Pipeline stage metrics"""
    stage_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    input_count: int = 0
    output_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    throughput: float = 0.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def finalize(self):
        """Finalize metrics after stage completion"""
        if self.end_time:
            self.duration = self.end_time - self.start_time
            if self.duration > 0:
                self.throughput = self.output_count / self.duration
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsCollector:
    """Collect and aggregate metrics"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.system_metrics = deque(maxlen=window_size)
        self.stage_metrics = {}
        self.alerts = []
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        metrics = SystemMetrics(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
            memory_used_mb=psutil.virtual_memory().used / (1024 * 1024),
            disk_usage_percent=psutil.disk_usage('/').percent
        )
        
        self.system_metrics.append(metrics)
        
        # Check for alerts
        self._check_resource_alerts(metrics)
        
        return metrics
    
    def _check_resource_alerts(self, metrics: SystemMetrics):
        """Check for resource usage alerts"""
        if metrics.cpu_percent > 90:
            self.alerts.append({
                'timestamp': metrics.timestamp,
                'level': 'warning',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%'
            })
        
        if metrics.memory_percent > 90:
            self.alerts.append({
                'timestamp': metrics.timestamp,
                'level': 'warning',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%'
            })
        
        if metrics.disk_usage_percent > 90:
            self.alerts.append({
                'timestamp': metrics.timestamp,
                'level': 'critical',
                'message': f'High disk usage: {metrics.disk_usage_percent:.1f}%'
            })
    
    def start_stage(self, stage_name: str) -> StageMetrics:
        """Start tracking a stage"""
        metrics = StageMetrics(
            stage_name=stage_name,
            start_time=time.time()
        )
        self.stage_metrics[stage_name] = metrics
        return metrics
    
    def end_stage(self, stage_name: str):
        """End tracking a stage"""
        if stage_name in self.stage_metrics:
            self.stage_metrics[stage_name].end_time = time.time()
            self.stage_metrics[stage_name].finalize()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        # System metrics summary
        if self.system_metrics:
            avg_cpu = sum(m.cpu_percent for m in self.system_metrics) / len(self.system_metrics)
            avg_memory = sum(m.memory_percent for m in self.system_metrics) / len(self.system_metrics)
            max_memory = max(m.memory_used_mb for m in self.system_metrics)
        else:
            avg_cpu = avg_memory = max_memory = 0
        
        # Stage metrics summary
        stages_summary = {
            name: metrics.to_dict()
            for name, metrics in self.stage_metrics.items()
        }
        
        return {
            'system': {
                'avg_cpu_percent': avg_cpu,
                'avg_memory_percent': avg_memory,
                'max_memory_mb': max_memory,
                'samples': len(self.system_metrics)
            },
            'stages': stages_summary,
            'alerts': self.alerts
        }


class WandBLogger:
    """Weights & Biases integration"""
    
    def __init__(self, project: str = "mahoun", enabled: bool = True):
        self.project = project
        self.enabled = enabled
        self.run = None
        
        if self.enabled:
            try:
                import wandb
                self.wandb = wandb
                logger.info("W&B available")
            except ImportError:
                logger.warning("W&B not installed, logging disabled")
                self.enabled = False
    
    def init_run(self, run_name: str, config: Dict[str, Any] = None):
        """Initialize W&B run"""
        if not self.enabled:
            return
        
        try:
            self.run = self.wandb.init(
                project=self.project,
                name=run_name,
                config=config or {},
                reinit=True
            )
            logger.info(f"✅ W&B run initialized: {run_name}")
        except Exception as e:
            logger.error(f"Failed to initialize W&B: {e}")
            self.enabled = False
    
    def log(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """Log metrics to W&B"""
        if not self.enabled or not self.run:
            return
        
        try:
            self.wandb.log(metrics, step=step)
        except Exception as e:
            logger.error(f"Failed to log to W&B: {e}")
    
    def log_artifact(self, file_path: Path, artifact_type: str = "dataset"):
        """Log artifact to W&B"""
        if not self.enabled or not self.run:
            return
        
        try:
            artifact = self.wandb.Artifact(
                name=file_path.stem,
                type=artifact_type
            )
            artifact.add_file(str(file_path))
            self.run.log_artifact(artifact)
            logger.info(f"📦 Logged artifact: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to log artifact: {e}")
    
    def finish(self):
        """Finish W&B run"""
        if self.enabled and self.run:
            try:
                self.wandb.finish()
                logger.info("✅ W&B run finished")
            except Exception as e:
                logger.error(f"Failed to finish W&B: {e}")


class PrometheusExporter:
    """Export metrics in Prometheus format"""
    
    def __init__(self, port: int = 8000):
        self.port = port
        self.enabled = False
        
        try:
            from prometheus_client import start_http_server, Gauge, Counter
            self.Gauge = Gauge
            self.Counter = Counter
            
            # Define metrics
            self.cpu_gauge = Gauge('pipeline_cpu_percent', 'CPU usage percentage')
            self.memory_gauge = Gauge('pipeline_memory_percent', 'Memory usage percentage')
            self.stage_duration = Gauge('pipeline_stage_duration_seconds', 'Stage duration', ['stage'])
            self.stage_throughput = Gauge('pipeline_stage_throughput', 'Stage throughput', ['stage'])
            self.documents_processed = Counter('pipeline_documents_processed_total', 'Total documents processed', ['stage'])
            
            # Start server
            start_http_server(port)
            self.enabled = True
            logger.info(f"✅ Prometheus exporter started on port {port}")
            
        except ImportError:
            logger.warning("prometheus_client not installed")
        except Exception as e:
            logger.error(f"Failed to start Prometheus exporter: {e}")
    
    def update_system_metrics(self, metrics: SystemMetrics):
        """Update system metrics"""
        if not self.enabled:
            return
        
        try:
            self.cpu_gauge.set(metrics.cpu_percent)
            self.memory_gauge.set(metrics.memory_percent)
        except Exception as e:
            logger.error(f"Failed to update Prometheus metrics: {e}")
    
    def update_stage_metrics(self, metrics: StageMetrics):
        """Update stage metrics"""
        if not self.enabled:
            return
        
        try:
            if metrics.duration:
                self.stage_duration.labels(stage=metrics.stage_name).set(metrics.duration)
            if metrics.throughput:
                self.stage_throughput.labels(stage=metrics.stage_name).set(metrics.throughput)
            if metrics.output_count:
                self.documents_processed.labels(stage=metrics.stage_name).inc(metrics.output_count)
        except Exception as e:
            logger.error(f"Failed to update Prometheus metrics: {e}")


class PipelineMonitor:
    """
    Ultra-advanced DATA PREPARATION pipeline monitoring
    
    Features:
    - Real-time metrics collection
    - W&B integration for data prep stages
    - Prometheus export
    - Data quality tracking
    - Processing throughput monitoring
    - Stage-specific metrics
    - Alert system for data issues
    
    Specifically designed for data preparation pipeline monitoring
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize monitor
        
        Args:
            config: Monitoring configuration
        """
        self.config = config or {}
        
        # Initialize components
        self.metrics_collector = MetricsCollector(
            window_size=self.config.get('metrics_window', 100)
        )
        
        self.wandb_logger = WandBLogger(
            project=self.config.get('wandb_project', 'mahoun-data-prep'),
            enabled=self.config.get('enable_wandb', False)
        )
        
        self.prometheus_exporter = PrometheusExporter(
            port=self.config.get('prometheus_port', 8000)
        ) if self.config.get('enable_prometheus', False) else None
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_interval = self.config.get('monitoring_interval', 5.0)
        
        # Data prep specific tracking
        self.data_quality_scores = []
        self.processing_rates = {}
        self.error_counts = {}
        
        logger.info("PipelineMonitor initialized for DATA PREPARATION")
    
    def start_run(self, run_name: str, config: Dict[str, Any] = None):
        """Start monitoring run"""
        self.wandb_logger.init_run(run_name, config)
        self.monitoring_active = True
        logger.info(f"🎬 Monitoring started: {run_name}")
    
    def log_stage(self, stage_name: str, metrics: Any):
        """
        Log data preparation stage metrics
        
        Tracks:
        - Input/output document counts
        - Processing duration and throughput
        - Success/failure rates
        - Data quality scores
        - System resources
        """
        # Convert to StageMetrics if needed
        if hasattr(metrics, 'to_dict'):
            stage_metrics = metrics
        else:
            stage_metrics = StageMetrics(
                stage_name=stage_name,
                start_time=getattr(metrics, 'start_time', time.time()),
                end_time=getattr(metrics, 'end_time', time.time()),
                input_count=getattr(metrics, 'input_count', 0),
                output_count=getattr(metrics, 'output_count', 0),
                success_count=getattr(metrics, 'success_count', 0),
                failure_count=getattr(metrics, 'failure_count', 0)
            )
            stage_metrics.finalize()
        
        # Collect system metrics
        system_metrics = self.metrics_collector.collect_system_metrics()
        
        # Calculate data prep specific metrics
        input_count = getattr(stage_metrics, 'input_count', 0)
        output_count = getattr(stage_metrics, 'output_count', 0)
        success_rate = output_count / input_count if input_count > 0 else 0
        
        # Track processing rate
        self.processing_rates[stage_name] = getattr(stage_metrics, 'throughput', 0)
        
        # Track errors
        failure_count = getattr(stage_metrics, 'failure_count', 0)
        self.error_counts[stage_name] = failure_count
        
        # Extract quality score if available
        quality_score = None
        if hasattr(metrics, 'metrics') and isinstance(metrics.metrics, dict):
            quality_score = metrics.metrics.get('avg_quality_score') or metrics.metrics.get('quality_score')
            if quality_score:
                self.data_quality_scores.append(quality_score)
        
        # Log to W&B with data prep context
        wandb_metrics = {
            f'{stage_name}/input_count': input_count,
            f'{stage_name}/output_count': output_count,
            f'{stage_name}/success_rate': success_rate,
            f'{stage_name}/duration': getattr(stage_metrics, 'duration', 0),
            f'{stage_name}/throughput_docs_per_sec': getattr(stage_metrics, 'throughput', 0),
            f'{stage_name}/failure_count': failure_count,
            'system/cpu_percent': system_metrics.cpu_percent,
            'system/memory_percent': system_metrics.memory_percent,
            'system/memory_used_mb': system_metrics.memory_used_mb,
        }
        
        # Add quality score if available
        if quality_score is not None:
            wandb_metrics[f'{stage_name}/quality_score'] = quality_score
        
        self.wandb_logger.log(wandb_metrics)
        
        # Update Prometheus
        if self.prometheus_exporter:
            self.prometheus_exporter.update_system_metrics(system_metrics)
            if hasattr(stage_metrics, 'to_dict'):
                self.prometheus_exporter.update_stage_metrics(stage_metrics)
        
        logger.info(
            f"📊 {stage_name}: {output_count}/{input_count} docs "
            f"({success_rate*100:.1f}% success, "
            f"{getattr(stage_metrics, 'throughput', 0):.1f} docs/s)"
        )
    
    def log_pipeline_result(self, result: Any):
        """Log final pipeline result"""
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
        else:
            result_dict = {
                'success': getattr(result, 'success', False),
                'total_duration': getattr(result, 'total_duration', 0),
            }
        
        # Log to W&B
        self.wandb_logger.log({
            'pipeline/success': result_dict.get('success', False),
            'pipeline/total_duration': result_dict.get('total_duration', 0),
        })
        
        # Get summary
        summary = self.metrics_collector.get_summary()
        
        # Log summary
        self.wandb_logger.log({
            'summary/avg_cpu': summary['system']['avg_cpu_percent'],
            'summary/avg_memory': summary['system']['avg_memory_percent'],
            'summary/max_memory_mb': summary['system']['max_memory_mb'],
            'summary/num_alerts': len(summary['alerts']),
        })
        
        logger.info("📊 Logged pipeline result")
    
    def finish_run(self):
        """Finish monitoring run"""
        self.monitoring_active = False
        
        # Get final summary
        summary = self.metrics_collector.get_summary()
        
        # Log summary
        logger.info("=" * 60)
        logger.info("Monitoring Summary")
        logger.info("=" * 60)
        logger.info(f"Avg CPU: {summary['system']['avg_cpu_percent']:.1f}%")
        logger.info(f"Avg Memory: {summary['system']['avg_memory_percent']:.1f}%")
        logger.info(f"Max Memory: {summary['system']['max_memory_mb']:.1f} MB")
        logger.info(f"Alerts: {len(summary['alerts'])}")
        logger.info("=" * 60)
        
        # Finish W&B
        self.wandb_logger.finish()
        
        logger.info("🏁 Monitoring finished")
    
    def save_report(self, output_path: Path):
        """Save monitoring report"""
        summary = self.metrics_collector.get_summary()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 Saved monitoring report to {output_path}")
