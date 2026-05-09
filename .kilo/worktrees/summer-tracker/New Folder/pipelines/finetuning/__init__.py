"""
Fine-tuning Module for MAHOUN
==============================
Advanced Parameter-Efficient Fine-Tuning (PEFT) implementations:
- LoRA, QLoRA, AdaLoRA, DoRA
- Prefix Tuning, Prompt Tuning, IA3
- Multi-Adapter Management
- Adapter Fusion & Routing
"""

# Import from ultra systems
from ultra_systems.training import (
    UltraLoRATrainer,
    UltraLoRAConfig,
    LoRAMethod,
    TaskType,
    LoRAFusion,
)

# Map to existing names for compatibility
AdvancedLoRATrainer = UltraLoRATrainer
AdvancedLoRAConfig = UltraLoRAConfig

# PEFT Manager (using ultra systems)
from ultra_systems.training.ultra_lora_trainer import UltraLoRATrainer as PEFTManager
PEFTMethod = LoRAMethod
AdapterInfo = None
AdapterRouter = None

__all__ = [
    # Advanced LoRA
    "AdvancedLoRATrainer",
    "AdvancedLoRAConfig",
    "LoRAMethod",
    "TaskType",
    "LoRAFusion",
    
    # PEFT Manager
    "PEFTManager",
    "PEFTMethod",
    "AdapterInfo",
    "AdapterRouter",
]

__version__ = "2.0.0"
__author__ = "MAHOUN Team"
__description__ = "Advanced PEFT for Legal AI"
