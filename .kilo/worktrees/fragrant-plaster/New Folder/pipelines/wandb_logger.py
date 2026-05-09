# pipelines/wandb_logger.py
"""
Centralized W&B Logging System
- Unified logging interface
- Automatic metric tracking
- Custom charts and tables
- Artifact management
"""

import os
import json
from pathlib import Path
import numpy as np

try:
    import wandb

    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

from pipelines._logging import setup_logger

log = setup_logger("wandb_logger")


class WandBLogger:
    """Centralized W&B logging"""

    def __init__(
        self,
        project: str = None,
        name: str = None,
        config: Dict = None,
        tags: List[str] = None,
        enabled: bool = True,
    ):
        self.enabled = enabled and WANDB_AVAILABLE
        self.run = None

        if not self.enabled:
            if not WANDB_AVAILABLE:
                log.warning("W&B not available. Install with: pip install wandb")
            return

        # Initialize run
        self.run = wandb.init(
            project=project or os.getenv("WANDB_PROJECT", "mahoun"),
            name=name or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            config=config or {},
            tags=tags or [],
            reinit=True,
        )

        log.info(f"W&B run initialized: {self.run.name}")

    def log_metrics(self, metrics: Dict[str, Any], step: int = None):
        """Log metrics"""
        if not self.enabled:
            return

        wandb.log(metrics, step=step)

    def log_table(self, name: str, columns: List[str], data: List[List[Any]]):
        """Log table"""
        if not self.enabled:
            return

        table = wandb.Table(columns=columns, data=data)
        wandb.log({name: table})

    def log_histogram(self, name: str, values: List[float]):
        """Log histogram"""
        if not self.enabled:
            return

        wandb.log({name: wandb.Histogram(values)})

    def log_chart(self, name: str, table: wandb.Table, x: str, y: str, title: str = None):
        """Log chart"""
        if not self.enabled:
            return

        wandb.log({name: wandb.plot.scatter(table, x, y, title=title or name)})

    def log_confusion_matrix(self, y_true: List, y_pred: List, class_names: List[str]):
        """Log confusion matrix"""
        if not self.enabled:
            return

        wandb.log(
            {
                "confusion_matrix": wandb.plot.confusion_matrix(
                    probs=None, y_true=y_true, preds=y_pred, class_names=class_names
                )
            }
        )

    def log_artifact(self, name: str, artifact_type: str, file_path: str, metadata: Dict = None):
        """Log artifact"""
        if not self.enabled:
            return

        artifact = wandb.Artifact(name=name, type=artifact_type, metadata=metadata or {})
        artifact.add_file(file_path)
        wandb.log_artifact(artifact)

    def log_model(self, model_path: str, name: str = "model", metadata: Dict = None):
        """Log model artifact"""
        self.log_artifact(name=name, artifact_type="model", file_path=model_path, metadata=metadata)

    def finish(self):
        """Finish run"""
        if not self.enabled:
            return

        wandb.finish()
        log.info("W&B run finished")


class PipelineLogger:
    """Logger for pipeline stages"""

    def __init__(self, stage_name: str, wandb_logger: WandBLogger = None):
        self.stage_name = stage_name
        self.wandb = wandb_logger
        self.start_time = datetime.now()
        self.metrics = {}

    def log_start(self, config: Dict = None):
        """Log stage start"""
        log.info(f"Starting stage: {self.stage_name}")

        if self.wandb:
            self.wandb.log_metrics(
                {
                    f"{self.stage_name}/status": 0,  # 0=started
                    f"{self.stage_name}/start_time": self.start_time.timestamp(),
                }
            )

            if config:
                self.wandb.log_metrics(
                    {f"{self.stage_name}/config/{k}": v for k, v in config.items()}
                )

    def log_progress(self, current: int, total: int, metrics: Dict = None):
        """Log progress"""
        progress = current / total if total > 0 else 0

        log.info(f"{self.stage_name}: {current}/{total} ({progress:.1%})")

        if self.wandb:
            log_dict = {
                f"{self.stage_name}/progress": progress,
                f"{self.stage_name}/current": current,
                f"{self.stage_name}/total": total,
            }

            if metrics:
                log_dict.update({f"{self.stage_name}/{k}": v for k, v in metrics.items()})

            self.wandb.log_metrics(log_dict)

    def log_metrics(self, metrics: Dict):
        """Log metrics"""
        self.metrics.update(metrics)

        if self.wandb:
            self.wandb.log_metrics({f"{self.stage_name}/{k}": v for k, v in metrics.items()})

    def log_complete(self, success: bool = True, error: str = None):
        """Log stage completion"""
        duration = (datetime.now() - self.start_time).total_seconds()

        status_msg = "completed" if success else "failed"
        log.info(f"{self.stage_name} {status_msg} in {duration:.1f}s")

        if self.wandb:
            log_dict = {
                f"{self.stage_name}/status": 1 if success else -1,  # 1=success, -1=failed
                f"{self.stage_name}/duration": duration,
                f"{self.stage_name}/end_time": datetime.now().timestamp(),
            }

            if error:
                log_dict[f"{self.stage_name}/error"] = error

            self.wandb.log_metrics(log_dict)


class ExperimentTracker:
    """Track experiments and comparisons"""

    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.runs = []

    def add_run(self, run_name: str, metrics: Dict, config: Dict = None):
        """Add run to experiment"""
        self.runs.append(
            {
                "name": run_name,
                "metrics": metrics,
                "config": config or {},
                "timestamp": datetime.now().isoformat(),
            }
        )

    def compare_runs(self) -> Dict:
        """Compare runs"""
        if not self.runs:
            return {}

        # Get all metric keys
        all_metrics = set()
        for run in self.runs:
            all_metrics.update(run["metrics"].keys())

        # Compare
        comparison = {}
        for metric in all_metrics:
            values = [run["metrics"].get(metric, None) for run in self.runs]

            # Filter None values
            valid_values = [v for v in values if v is not None]

            if valid_values:
                comparison[metric] = {
                    "mean": np.mean(valid_values),
                    "std": np.std(valid_values),
                    "min": np.min(valid_values),
                    "max": np.max(valid_values),
                    "values": values,
                }

        return comparison

    def save_comparison(self, output_file: str):
        """Save comparison to file"""
        comparison = self.compare_runs()

        output = {
            "experiment": self.experiment_name,
            "num_runs": len(self.runs),
            "runs": self.runs,
            "comparison": comparison,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        log.info(f"Experiment comparison saved to {output_file}")


# Convenience functions
def init_wandb(
    project: str = None, name: str = None, config: Dict = None, tags: List[str] = None
) -> WandBLogger:
    """Initialize W&B logger"""
    return WandBLogger(project=project, name=name, config=config, tags=tags, enabled=True)


def log_pipeline_run(pipeline_name: str, stages: List[str], config: Dict = None) -> WandBLogger:
    """Log full pipeline run"""

    wandb_logger = init_wandb(
        name=f"{pipeline_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        config=config,
        tags=["pipeline", pipeline_name],
    )

    # Log pipeline structure
    wandb_logger.log_metrics(
        {
            "pipeline/name": pipeline_name,
            "pipeline/num_stages": len(stages),
            "pipeline/stages": ",".join(stages),
        }
    )

    return wandb_logger


def main():
    """Test W&B logging"""

    # Initialize
    logger = init_wandb(
        project="mahoun-test", name="test_run", config={"test": True}, tags=["test"]
    )

    # Log metrics
    logger.log_metrics({"accuracy": 0.95, "loss": 0.05})

    # Log table
    logger.log_table("results", columns=["query", "score"], data=[["query1", 0.9], ["query2", 0.8]])

    # Log histogram
    logger.log_histogram("scores", [0.9, 0.8, 0.85, 0.92])

    # Pipeline logger
    pipeline_logger = PipelineLogger("test_stage", logger)
    pipeline_logger.log_start({"param": "value"})
    pipeline_logger.log_progress(50, 100, {"metric": 0.5})
    pipeline_logger.log_complete(success=True)

    # Finish
    logger.finish()

    print("✅ W&B logging test complete")


if __name__ == "__main__":
    main()
