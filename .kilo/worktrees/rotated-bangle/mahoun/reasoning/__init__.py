"""
Reasoning Module
================

Multi-stage reasoning and knowledge graph integration for MAHOUN.
"""
from typing import Any, List, Optional

__version__ = "2.0.0"

# Conditional imports to avoid dependency issues
try:
    from .reasoning_engine import ReasoningEngine, ReasoningResult
except ImportError:
    ReasoningEngine: Optional[Any] = None
    ReasoningResult: Optional[Any] = None
try:
    from .policies import PolicyEngine, PolicyDecision
except ImportError:
    PolicyEngine: Optional[Any] = None
    PolicyDecision: Optional[Any] = None
try:
    from .chain_of_thought import ChainOfThoughtReasoner
except ImportError:
    ChainOfThoughtReasoner: Optional[Any] = None
try:
    from .causal_inference import CausalInferenceEngine
except ImportError:
    CausalInferenceEngine: Optional[Any] = None
try:
    from .knowledge_graph import LegalKnowledgeGraph
except ImportError:
    LegalKnowledgeGraph: Optional[Any] = None
try:
    from .ultra_reasoning_service import UltraReasoningService
except ImportError:
    UltraReasoningService: Optional[Any] = None
# Always safe imports
try:
    from .reasoning_chain import ReasoningChain, ReasoningConfig, ReasoningMode, ReasoningResult
    __all__ = ["ReasoningChain", "ReasoningConfig", "ReasoningMode", "ReasoningResult"]
except ImportError:
    __all__: List[Any] = []
# Add optional exports
if ReasoningEngine:
    __all__.extend(["ReasoningEngine"])
if PolicyEngine:
    __all__.extend(["PolicyEngine", "PolicyDecision"])
if ChainOfThoughtReasoner:
    __all__.append("ChainOfThoughtReasoner")
if CausalInferenceEngine:
    __all__.append("CausalInferenceEngine")
if LegalKnowledgeGraph:
    __all__.append("LegalKnowledgeGraph")
if UltraReasoningService:
    __all__.append("UltraReasoningService")
