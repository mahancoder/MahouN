"""
Ultra Systems Package
====================
Enterprise-grade ultra-advanced systems for AI/ML applications.

Modules:
- self_improve: Self-improvement and reinforcement learning systems
- rag: Retrieval-Augmented Generation systems
- graph: Graph processing and knowledge graph systems
- pipelines: Data processing pipelines
- core: Core orchestration and utilities
- nlp: Natural Language Processing systems
- guardrails: NLI verification and citation auditing
- training: Advanced training systems (LoRA/PEFT)
- data: Data augmentation and processing
- vector_store: Vector store backends
"""

__version__ = "2.0.0"
__author__ = "Ultra Systems Team"

# Import main components
from ultra_systems.self_improve import (
    UltraSelfImprovementSystem,
    UltraRLAgent,
    UltraActiveLearner,
    UltraBanditSystem,
)

from ultra_systems.rag import (
    UltraGraphRAG,
    UltraEvaluationSystem,
    UltraIndexingSystem,
)

from ultra_systems.graph import (
    UltraGraphBuilder,
    UltraRelationExtractor,
    UltraGraphQueryService,
)

from ultra_systems.pipelines import (
    UltraDataIngestion,
    UltraLegalDataPipeline,
)

from ultra_systems.nlp import (
    UltraEntityExtractor,
)

from ultra_systems.guardrails import (
    UltraNLIVerifier,
    UltraCitationAuditor,
)

from ultra_systems.training import (
    UltraLoRATrainer,
)

from ultra_systems.data import (
    UltraDataAugmenter,
)

from ultra_systems.vector_store import (
    UltraChromaDBBackend,
)

__all__ = [
    # Self-Improve
    "UltraSelfImprovementSystem",
    "UltraRLAgent",
    "UltraActiveLearner",
    "UltraBanditSystem",
    
    # RAG
    "UltraGraphRAG",
    "UltraEvaluationSystem",
    "UltraIndexingSystem",
    
    # Graph
    "UltraGraphBuilder",
    "UltraRelationExtractor",
    "UltraGraphQueryService",
    
    # Pipelines
    "UltraDataIngestion",
    "UltraLegalDataPipeline",
    
    # NLP
    "UltraEntityExtractor",
    
    # Guardrails
    "UltraNLIVerifier",
    "UltraCitationAuditor",
    
    # Training
    "UltraLoRATrainer",
    
    # Data
    "UltraDataAugmenter",
    
    # Vector Store
    "UltraChromaDBBackend",
]
