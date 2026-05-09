"""
Embedding Service - Re-export from embed_index
===============================================

This module re-exports embedding functionality from
pipelines.embed_index for backward compatibility.

For new code, prefer importing directly from:
    from pipelines.embed_index import AdvancedEmbedder
"""

# Re-export all public APIs from the actual implementation
from pipelines.embed_index import (
    AdvancedEmbedder,
    EmbeddingConfig,
)

__all__ = [
    'AdvancedEmbedder',
    'EmbeddingConfig',
]
