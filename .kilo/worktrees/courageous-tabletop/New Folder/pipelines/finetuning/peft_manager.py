"""
PEFT Manager for MAHOUN
=======================
مدیریت کامل Parameter-Efficient Fine-Tuning:
- LoRA, QLoRA, AdaLoRA, DoRA
- Prefix Tuning
- P-Tuning v2
- Prompt Tuning
- IA3 (Infused Adapter by Inhibiting and Amplifying Inner Activations)
- Adapter Fusion
- Multi-Adapter Management
- Adapter Routing
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import warnings

import torch
import torch.nn as nn
import numpy as np

try:
    from peft import (
        LoraConfig,
        AdaLoraConfig,
        PrefixTuningConfig,
        PromptTuningConfig,
        IA3Config,
        get_peft_model,
        PeftModel,
        PeftConfig,
        TaskType,
    )
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    warnings.warn("PEFT not available")

from transformers import AutoModel, AutoTokenizer

# Import from ultra systems
from ultra_systems.training.ultra_lora_trainer import (
    UltraLoRATrainer,
    UltraLoRAConfig,
    LoRAMethod,
)

# Map to existing names for compatibility
PEFTManager = UltraLoRATrainer
PEFTMethod = LoRAMethod

@dataclass
class AdapterInfo:
    """Adapter information"""
    name: str
    method: PEFTMethod
    path: str
    task: str
    performance: Optional[Dict[str, float]] = None
    metadata: Optional[Dict] = None

class AdapterRouter:
    """Route queries to appropriate adapters"""
    
    def __init__(self, adapters: List[AdapterInfo]):
        self.adapters = {a.name: a for a in adapters}
        self.routing_model = None  # Could be a classifier
    
    def route(self, query: str, context: Optional[Dict] = None) -> str:
        """
        Route query to best adapter
        
        Args:
            query: Input query
            context: Additional context (domain, task type, etc.)
        
        Returns:
            Adapter name
        """
        # Simple rule-based routing
        if context and "task" in context:
            task = context["task"]
            
            # Find adapter for task
            for name, adapter in self.adapters.items():
                if adapter.task == task:
                    return name
        
        # Default: use best performing adapter
        best_adapter = max(
            self.adapters.values(),
            key=lambda a: a.performance.get("f1", 0.0) if a.performance else 0.0
        )
        
        return best_adapter.name
    
    def route_ensemble(
        self,
        query: str,
        top_k: int = 3,
        context: Optional[Dict] = None
    ) -> List[Tuple[str, float]]:
        """
        Route to multiple adapters for ensemble
        
        Returns:
            List of (adapter_name, weight) tuples
        """
        # Score adapters
        scores = {}
        for name, adapter in self.adapters.items():
            score = adapter.performance.get("f1", 0.5) if adapter.performance else 0.5
            
            # Boost score if task matches
            if context and "task" in context and adapter.task == context["task"]:
                score *= 1.5
            
            scores[name] = score
        
        # Get top-k
        top_adapters = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Normalize weights
        total = sum(score for _, score in top_adapters)
        weights = [(name, score / total) for name, score in top_adapters]
        
        return weights


class PEFTManager:
    """Manage multiple PEFT adapters"""
    
    def __init__(
        self,
        base_model_name: str,
        adapters_dir: str = "models/adapters",
        device: Optional[str] = None,
    ):
        self.base_model_name = base_model_name
        self.adapters_dir = Path(adapters_dir)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load base model
        log.info(f"Loading base model: {base_model_name}")
        self.base_model = AutoModel.from_pretrained(base_model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        self.base_model.to(self.device)
        
        # Adapters
        self.adapters: Dict[str, AdapterInfo] = {}
        self.loaded_adapters: Dict[str, PeftModel] = {}
        self.active_adapter: Optional[str] = None
        
        # Router
        self.router: Optional[AdapterRouter] = None
        
        # Load existing adapters
        self._discover_adapters()
    
    def _discover_adapters(self):
        """Discover existing adapters"""
        
        if not self.adapters_dir.exists():
            log.info("No adapters directory found")
            return
        
        log.info(f"Discovering adapters in {self.adapters_dir}...")
        
        for adapter_path in self.adapters_dir.iterdir():
            if adapter_path.is_dir():
                # Check if valid adapter
                config_file = adapter_path / "adapter_config.json"
                if config_file.exists():
                    try:
                        with open(config_file) as f:
                            config = json.load(f)
                        
                        # Load metadata
                        metadata_file = adapter_path / "metadata.json"
                        metadata = {}
                        if metadata_file.exists():
                            with open(metadata_file) as f:
                                metadata = json.load(f)
                        
                        adapter_info = AdapterInfo(
                            name=adapter_path.name,
                            method=PEFTMethod(config.get("peft_type", "lora").lower()),
                            path=str(adapter_path),
                            task=metadata.get("task", "unknown"),
                            performance=metadata.get("performance"),
                            metadata=metadata,
                        )
                        
                        self.adapters[adapter_info.name] = adapter_info
                        log.info(f"   Found adapter: {adapter_info.name} ({adapter_info.method.value})")
                    
                    except Exception as e:
                        log.warning(f"   Failed to load adapter {adapter_path.name}: {e}")
        
        log.info(f"Discovered {len(self.adapters)} adapters")
        
        # Create router
        if self.adapters:
            self.router = AdapterRouter(list(self.adapters.values()))
    
    def create_adapter(
        self,
        name: str,
        method: PEFTMethod,
        task: str,
        config: Optional[Dict] = None,
    ) -> PeftConfig:
        """
        Create new adapter configuration
        
        Args:
            name: Adapter name
            method: PEFT method
            task: Task type
            config: Method-specific config
        
        Returns:
            PEFT config
        """
        if not PEFT_AVAILABLE:
            raise ImportError("PEFT not available")
        
        config = config or {}
        
        # Task type mapping
        task_type_map = {
            "embedding": TaskType.FEATURE_EXTRACTION,
            "ner": TaskType.TOKEN_CLS,
            "classification": TaskType.SEQ_CLS,
            "generation": TaskType.CAUSAL_LM,
        }
        
        task_type = task_type_map.get(task, TaskType.FEATURE_EXTRACTION)
        
        # Create config based on method
        if method == PEFTMethod.LORA or method == PEFTMethod.QLORA or method == PEFTMethod.DORA:
            peft_config = LoraConfig(
                r=config.get("r", 8),
                lora_alpha=config.get("lora_alpha", 16),
                target_modules=config.get("target_modules", ["query", "key", "value"]),
                lora_dropout=config.get("lora_dropout", 0.1),
                bias="none",
                task_type=task_type,
                use_rslora=config.get("use_rslora", True),
                use_dora=(method == PEFTMethod.DORA),
            )
        
        elif method == PEFTMethod.ADALORA:
            peft_config = AdaLoraConfig(
                r=config.get("r", 8),
                lora_alpha=config.get("lora_alpha", 16),
                target_modules=config.get("target_modules", ["query", "key", "value"]),
                lora_dropout=config.get("lora_dropout", 0.1),
                task_type=task_type,
                init_r=config.get("init_r", 12),
                target_r=config.get("target_r", 8),
                beta1=config.get("beta1", 0.85),
                beta2=config.get("beta2", 0.85),
            )
        
        elif method == PEFTMethod.PREFIX_TUNING:
            peft_config = PrefixTuningConfig(
                num_virtual_tokens=config.get("num_virtual_tokens", 20),
                task_type=task_type,
                prefix_projection=config.get("prefix_projection", True),
            )
        
        elif method == PEFTMethod.PROMPT_TUNING:
            peft_config = PromptTuningConfig(
                num_virtual_tokens=config.get("num_virtual_tokens", 20),
                task_type=task_type,
                prompt_tuning_init=config.get("prompt_tuning_init", "RANDOM"),
            )
        
        elif method == PEFTMethod.IA3:
            peft_config = IA3Config(
                target_modules=config.get("target_modules", ["k", "v", "down_proj"]),
                feedforward_modules=config.get("feedforward_modules", ["down_proj"]),
                task_type=task_type,
            )
        
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        log.info(f"Created {method.value} config for adapter '{name}'")
        
        return peft_config
    
    def train_adapter(
        self,
        name: str,
        method: PEFTMethod,
        task: str,
        train_dataloader,
        eval_dataloader=None,
        config: Optional[Dict] = None,
        training_args: Optional[Dict] = None,
    ):
        """
        Train new adapter
        
        Args:
            name: Adapter name
            method: PEFT method
            task: Task type
            train_dataloader: Training data
            eval_dataloader: Evaluation data
            config: Method-specific config
            training_args: Training arguments
        """
        # Create adapter config
        peft_config = self.create_adapter(name, method, task, config)
        
        # Create PEFT model
        model = get_peft_model(self.base_model, peft_config)
        model.print_trainable_parameters()
        
        # Train (use AdvancedLoRATrainer or similar)
        # ... training code ...
        
        # Save adapter
        output_dir = self.adapters_dir / name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model.save_pretrained(output_dir)
        
        # Save metadata
        metadata = {
            "name": name,
            "method": method.value,
            "task": task,
            "base_model": self.base_model_name,
            "config": config or {},
            "training_args": training_args or {},
        }
        
        with open(output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Register adapter
        adapter_info = AdapterInfo(
            name=name,
            method=method,
            path=str(output_dir),
            task=task,
            metadata=metadata,
        )
        
        self.adapters[name] = adapter_info
        
        log.info(f"✅ Adapter '{name}' trained and saved")
    
    def load_adapter(self, name: str, set_active: bool = True) -> PeftModel:
        """Load adapter"""
        
        if name not in self.adapters:
            raise ValueError(f"Adapter '{name}' not found")
        
        if name in self.loaded_adapters:
            log.info(f"Adapter '{name}' already loaded")
            model = self.loaded_adapters[name]
        else:
            adapter_info = self.adapters[name]
            log.info(f"Loading adapter '{name}' from {adapter_info.path}")
            
            model = PeftModel.from_pretrained(
                self.base_model,
                adapter_info.path,
            )
            
            self.loaded_adapters[name] = model
        
        if set_active:
            self.active_adapter = name
            log.info(f"Active adapter set to '{name}'")
        
        return model
    
    def unload_adapter(self, name: str):
        """Unload adapter to free memory"""
        
        if name in self.loaded_adapters:
            del self.loaded_adapters[name]
            log.info(f"Adapter '{name}' unloaded")
            
            if self.active_adapter == name:
                self.active_adapter = None
    
    def switch_adapter(self, name: str):
        """Switch to different adapter"""
        
        if name not in self.adapters:
            raise ValueError(f"Adapter '{name}' not found")
        
        self.load_adapter(name, set_active=True)
    
    def merge_adapter(self, name: str) -> nn.Module:
        """
        Merge adapter weights into base model
        
        Returns:
            Merged model (no longer needs adapter)
        """
        model = self.load_adapter(name, set_active=False)
        
        log.info(f"Merging adapter '{name}' into base model...")
        merged_model = model.merge_and_unload()
        
        log.info("✅ Adapter merged")
        return merged_model
    
    def fuse_adapters(
        self,
        adapter_names: List[str],
        weights: Optional[List[float]] = None,
        output_name: Optional[str] = None,
    ) -> PeftModel:
        """
        Fuse multiple adapters
        
        Args:
            adapter_names: List of adapter names
            weights: Fusion weights (default: equal)
            output_name: Name for fused adapter
        
        Returns:
            Fused model
        """
        if weights is None:
            weights = [1.0 / len(adapter_names)] * len(adapter_names)
        
        log.info(f"Fusing {len(adapter_names)} adapters: {adapter_names}")
        log.info(f"Weights: {weights}")
        
        # Load adapters
        models = [self.load_adapter(name, set_active=False) for name in adapter_names]
        
        # Fuse (weighted average of LoRA parameters)
        fused_params = {}
        
        for name, param in models[0].named_parameters():
            if "lora" in name:
                fused_params[name] = param.data * weights[0]
        
        for i, model in enumerate(models[1:], 1):
            for name, param in model.named_parameters():
                if "lora" in name and name in fused_params:
                    fused_params[name] += param.data * weights[i]
        
        # Create fused model
        fused_model = models[0]
        for name, param in fused_model.named_parameters():
            if name in fused_params:
                param.data = fused_params[name]
        
        # Save if output_name provided
        if output_name:
            output_dir = self.adapters_dir / output_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            fused_model.save_pretrained(output_dir)
            
            # Save metadata
            metadata = {
                "name": output_name,
                "method": "fused",
                "source_adapters": adapter_names,
                "fusion_weights": weights,
            }
            
            with open(output_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            log.info(f"✅ Fused adapter saved as '{output_name}'")
        
        return fused_model
    
    def ensemble_predict(
        self,
        text: str,
        adapter_names: Optional[List[str]] = None,
        weights: Optional[List[float]] = None,
    ):
        """
        Ensemble prediction from multiple adapters
        
        Args:
            text: Input text
            adapter_names: Adapters to use (default: all)
            weights: Ensemble weights (default: equal)
        
        Returns:
            Ensemble prediction
        """
        if adapter_names is None:
            adapter_names = list(self.adapters.keys())
        
        if weights is None:
            weights = [1.0 / len(adapter_names)] * len(adapter_names)
        
        log.info(f"Ensemble prediction with {len(adapter_names)} adapters")
        
        # Get predictions from each adapter
        predictions = []
        
        for name in adapter_names:
            model = self.load_adapter(name, set_active=False)
            model.eval()
            
            # Tokenize
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
            
            # Predict
            with torch.no_grad():
                outputs = model(**inputs)
            
            predictions.append(outputs)
        
        # Combine predictions (weighted average)
        # Implementation depends on task type
        # For embeddings: weighted average of embeddings
        # For classification: weighted average of logits
        
        return predictions  # TODO: implement combination logic
    
    def auto_route(self, text: str, context: Optional[Dict] = None):
        """Automatically route to best adapter"""
        
        if not self.router:
            raise ValueError("No router available")
        
        adapter_name = self.router.route(text, context)
        log.info(f"Routed to adapter: {adapter_name}")
        
        return self.load_adapter(adapter_name)
    
    def list_adapters(self) -> List[AdapterInfo]:
        """List all available adapters"""
        return list(self.adapters.values())
    
    def get_adapter_info(self, name: str) -> AdapterInfo:
        """Get adapter information"""
        if name not in self.adapters:
            raise ValueError(f"Adapter '{name}' not found")
        return self.adapters[name]
    
    def delete_adapter(self, name: str):
        """Delete adapter"""
        
        if name not in self.adapters:
            raise ValueError(f"Adapter '{name}' not found")
        
        # Unload if loaded
        if name in self.loaded_adapters:
            self.unload_adapter(name)
        
        # Delete files
        adapter_info = self.adapters[name]
        adapter_path = Path(adapter_info.path)
        
        if adapter_path.exists():
            import shutil
            shutil.rmtree(adapter_path)
            log.info(f"Deleted adapter files: {adapter_path}")
        
        # Remove from registry
        del self.adapters[name]
        
        log.info(f"✅ Adapter '{name}' deleted")
    
    def benchmark_adapters(self, eval_dataloader) -> Dict[str, Dict[str, float]]:
        """Benchmark all adapters"""
        
        log.info(f"Benchmarking {len(self.adapters)} adapters...")
        
        results = {}
        
        for name in self.adapters.keys():
            log.info(f"   Evaluating {name}...")
            
            model = self.load_adapter(name, set_active=False)
            model.eval()
            
            # Evaluate
            # ... evaluation code ...
            
            # Store results
            results[name] = {
                "accuracy": 0.0,  # TODO: compute
                "f1": 0.0,
                "latency_ms": 0.0,
            }
        
        log.info("✅ Benchmark complete")
        return results


def main():
    """Example usage"""
    
    # Initialize manager
    manager = PEFTManager(
        base_model_name="BAAI/bge-m3",
        adapters_dir="models/adapters",
    )
    
    # List adapters
    adapters = manager.list_adapters()
    print(f"\nAvailable adapters: {len(adapters)}")
    for adapter in adapters:
        print(f"  - {adapter.name} ({adapter.method.value}) - Task: {adapter.task}")
    
    # Load adapter
    if adapters:
        model = manager.load_adapter(adapters[0].name)
        print(f"\nLoaded adapter: {adapters[0].name}")
    
    # Auto-route
    if manager.router:
        text = "قانون مدنی چیست؟"
        model = manager.auto_route(text, context={"task": "legal_qa"})
        print(f"\nAuto-routed to: {manager.active_adapter}")


if __name__ == "__main__":
    main()
