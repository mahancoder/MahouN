"""
MAHOUN Core Module
==================

Core components for the MAHOUN Enterprise system.
"""
from typing import Any, Optional

from .runtime_config import (
    get_runtime_settings,
    is_desktop_minimal,
    should_skip_graph,
    should_skip_lora_training,
    is_enterprise_graph_mode,
    get_graph_config,
    MahounRuntimeSettings,
)

from .models import (
    LegalDocType,
    LegalDocument,
    LegalEntity,
    ReasoningStep,
    CausalRelation,
    ReasoningResult,
    UncertaintyEstimate,
)

# RAG Pipeline alias for backward compatibility
# Removed to fix architecture boundary violation
RAGPipeline: Optional[Any] = None
__all__ = [
    # Runtime Config
    "get_runtime_settings",
    "is_desktop_minimal",
    "should_skip_graph",
    "should_skip_lora_training",
    "is_enterprise_graph_mode",
    "get_graph_config",
    "MahounRuntimeSettings",
    # Models
    "LegalDocType",
    "LegalDocument",
    "LegalEntity",
    "ReasoningStep",
    "CausalRelation",
    "ReasoningResult",
    "UncertaintyEstimate",
    # RAG Pipeline
    "RAGPipeline",
]

