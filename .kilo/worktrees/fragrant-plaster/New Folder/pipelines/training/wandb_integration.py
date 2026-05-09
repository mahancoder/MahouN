"""
Weights & Biases Integration
=============================

Complete W&B integration for training monitoring and logging.
"""

from typing import Dict, List, Optional, Any
import torch
import numpy as np
from pathlib import Path

# Optional WandB
try:
    import wandb
    HAS_WANDB = True
except ImportError:
    HAS_WANDB = False
    wandb = None

from pipelines._logging import setup_logger

logger = setup_logger("wandb_integration")


class WandBTracker:
    """
    Weights & Biases experiment tracker
    
    Features:
    - Automatic experiment logging
    - Model checkpointing
    - Hyperparameter tracking
    - Metric visualization
    - Artifact management
    """
    
    def __init__(
        self,
        project: str = "mahoun-legal-ai",
        entity: Optional[str] = None,
        name: Optional[str] = None,
        config: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        enabled: bool = True,
    ):
        """
        Initialize W&B tracker
        
        Args:
            project: W&B project name
            entity: W&B entity (team/user)
            name: Run name
            config: Configuration dictionary
            tags: List of tags
            notes: Run notes
            enabled: Enable/disable W&B logging
        """
        self.enabled = enabled
        self.project = project
        self.entity = entity
        
        if self.enabled:
            try:
                self.run = wandb.init(
                    project=project,
                    entity=entity,
                    name=name,
                    config=config,
                    tags=tags,
                    notes=notes,
                    reinit=True
                )
                
                logger.info(f"W&B initialized: {self.run.name} ({self.run.id})")
                
            except Exception as e:
                logger.warning(f"W&B initialization failed: {e}")
                self.enabled = False
                self.run = None
        else:
            self.run = None
            logger.info("W&B tracking disabled")
    
    def log(self, metrics: Dict[str, Any], step: Optional[int] = None):
        """Log metrics to W&B"""
        if not self.enabled or not self.run:
            return
        
        try:
            wandb.log(metrics, step=step)
        except Exception as e:
            logger.error(f"W&B logging failed: {e}")
    
    def log_model(
        self,
        model: torch.nn.Module,
        name: str,
        metadata: Optional[Dict] = None
    ):
        """Log model to W&B"""
        if not self.enabled or not self.run:
            return
        
        try:
            # Save model
            model_path = Path(f"models/{name}.pt")
            model_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), model_path)
            
            # Log as artifact
            artifact = wandb.Artifact(
                name=name,
                type="model",
                metadata=metadata or {}
            )
            artifact.add_file(str(model_path))
            self.run.log_artifact(artifact)
            
            logger.info(f"Model logged to W&B: {name}")
            
        except Exception as e:
            logger.error(f"Model logging failed: {e}")
    
    def log_table(
        self,
        name: str,
        data: List[List[Any]],
        columns: List[str]
    ):
        """Log table to W&B"""
        if not self.enabled or not self.run:
            return
        
        try:
            table = wandb.Table(data=data, columns=columns)
            wandb.log({name: table})
        except Exception as e:
            logger.error(f"Table logging failed: {e}")
    
    def log_image(
        self,
        name: str,
        image: Any,
        caption: Optional[str] = None
    ):
        """Log image to W&B"""
        if not self.enabled or not self.run:
            return
        
        try:
            wandb.log({name: wandb.Image(image, caption=caption)})
        except Exception as e:
            logger.error(f"Image logging failed: {e}")
    
    def log_histogram(
        self,
        name: str,
        values: np.ndarray
    ):
        """Log histogram to W&B"""
        if not self.enabled or not self.run:
            return
        
        try:
            wandb.log({name: wandb.Histogram(values)})
        except Exception as e:
            logger.error(f"Histogram logging failed: {e}")
    
    def watch(
        self,
        model: torch.nn.Module,
        log_freq: int = 100,
        log_graph: bool = True
    ):
        """Watch model gradients"""
        if not self.enabled or not self.run:
            return
        
        try:
            wandb.watch(model, log_freq=log_freq, log_graph=log_graph)
            logger.info("Model watching enabled")
        except Exception as e:
            logger.error(f"Model watching failed: {e}")
    
    def finish(self):
        """Finish W&B run"""
        if self.enabled and self.run:
            try:
                wandb.finish()
                logger.info("W&B run finished")
            except Exception as e:
                logger.error(f"W&B finish failed: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.finish()


def log_training_metrics(
    tracker: WandBTracker,
    epoch: int,
    train_loss: float,
    val_loss: Optional[float] = None,
    train_acc: Optional[float] = None,
    val_acc: Optional[float] = None,
    learning_rate: Optional[float] = None,
    **kwargs
):
    """
    Log training metrics
    
    Args:
        tracker: W&B tracker
        epoch: Current epoch
        train_loss: Training loss
        val_loss: Validation loss
        train_acc: Training accuracy
        val_acc: Validation accuracy
        learning_rate: Current learning rate
        **kwargs: Additional metrics
    """
    metrics = {
        "epoch": epoch,
        "train/loss": train_loss,
    }
    
    if val_loss is not None:
        metrics["val/loss"] = val_loss
    
    if train_acc is not None:
        metrics["train/accuracy"] = train_acc
    
    if val_acc is not None:
        metrics["val/accuracy"] = val_acc
    
    if learning_rate is not None:
        metrics["train/learning_rate"] = learning_rate
    
    # Add additional metrics
    metrics.update(kwargs)
    
    tracker.log(metrics, step=epoch)


def log_gat_training(
    tracker: WandBTracker,
    epoch: int,
    train_metrics: Dict[str, float],
    val_metrics: Optional[Dict[str, float]] = None
):
    """
    Log GAT training metrics
    
    Args:
        tracker: W&B tracker
        epoch: Current epoch
        train_metrics: Training metrics
        val_metrics: Validation metrics
    """
    metrics = {"epoch": epoch}
    
    # Add training metrics
    for key, value in train_metrics.items():
        metrics[f"train/{key}"] = value
    
    # Add validation metrics
    if val_metrics:
        for key, value in val_metrics.items():
            metrics[f"val/{key}"] = value
    
    tracker.log(metrics, step=epoch)


def log_embedding_training(
    tracker: WandBTracker,
    step: int,
    loss: float,
    similarity_score: Optional[float] = None,
    batch_size: Optional[int] = None
):
    """
    Log embedding training metrics
    
    Args:
        tracker: W&B tracker
        step: Current step
        loss: Training loss
        similarity_score: Similarity score
        batch_size: Batch size
    """
    metrics = {
        "step": step,
        "train/loss": loss,
    }
    
    if similarity_score is not None:
        metrics["train/similarity"] = similarity_score
    
    if batch_size is not None:
        metrics["train/batch_size"] = batch_size
    
    tracker.log(metrics, step=step)
