"""
Advanced LoRA/PEFT Trainer for MAHOUN
=====================================
Enterprise-grade LoRA training with all advanced features.

Features:
- Multi-task Learning (Embedding + NER + Classification)
- QLoRA (4-bit/8-bit quantization)
- AdaLoRA (Adaptive rank allocation)
- DoRA (Weight-Decomposed LoRA)
- LoRA Fusion (merge multiple adapters)
- Dynamic Rank Allocation
- Gradient Checkpointing
- Mixed Precision Training
- Distributed Training Support
"""

import os
import json
import warnings
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.cuda.amp import autocast, GradScaler
from tqdm import tqdm
import numpy as np

try:
    from peft import (
        LoraConfig,
        AdaLoraConfig,
        get_peft_model,
        PeftModel,
        prepare_model_for_kbit_training,
    )
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    warnings.warn("PEFT not installed")

try:
    import bitsandbytes as bnb
    BITSANDBYTES_AVAILABLE = True
except ImportError:
    BITSANDBYTES_AVAILABLE = False

from transformers import (
    AutoTokenizer,
    AutoModel,
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification,
    get_cosine_schedule_with_warmup,
)

# Import from ultra systems
from ultra_systems.training.ultra_lora_trainer import (
    UltraLoRATrainer,
    UltraLoRAConfig,
    LoRAMethod,
    TaskType,
    LoRAFusion,
)

# Map to existing names for compatibility
AdvancedLoRATrainer = UltraLoRATrainer
AdvancedLoRAConfig = UltraLoRAConfig

# Export all
__all__ = [
    "AdvancedLoRATrainer",
    "AdvancedLoRAConfig",
    "LoRAMethod",
    "TaskType",
    "LoRAFusion",
]
