"""
Embedding Module
================
Enterprise-grade text embedding with multi-model support and advanced features
"""

from .service import (
    EmbeddingService,
    ModelManager,
    BatchEmbedder,
    EmbeddingResult,
    ModelInfo
)

__all__ = [
    "EmbeddingService",
    "ModelManager",
    "BatchEmbedder",
    "EmbeddingResult",
    "ModelInfo",
]
