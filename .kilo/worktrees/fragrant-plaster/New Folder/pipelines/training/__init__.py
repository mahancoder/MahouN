"""
MAHOUN Training Pipeline Module
================================

Training utilities and integrations for model fine-tuning.

Components:
- Wandb Integration: Weights & Biases experiment tracking
- Training Utilities: Helper functions for training
- Model Checkpointing: Save and load model checkpoints

Features:
- Experiment tracking with W&B
- Hyperparameter logging
- Metric visualization
- Model versioning
- Distributed training support
"""

__version__ = "1.0.0"

from pipelines.training.wandb_integration import (
    WandbIntegration,
    init_wandb,
    log_metrics,
    log_model,
    finish_wandb,
)

__all__ = [
    "WandbIntegration",
    "init_wandb",
    "log_metrics",
    "log_model",
    "finish_wandb",
]
