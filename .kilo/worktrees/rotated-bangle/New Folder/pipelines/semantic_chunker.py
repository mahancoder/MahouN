"""
Semantic Chunker - Re-export from gnn
======================================

This module re-exports the SemanticChunker implementation from
pipelines.gnn.semantic_chunker for backward compatibility.

For new code, prefer importing directly from:
    from pipelines.gnn.semantic_chunker import SemanticChunker
"""

# Re-export all public APIs from the actual implementation
from pipelines.gnn.semantic_chunker import (
    SemanticChunker,
    Chunk,
    CacheLevel,
)

__all__ = [
    'SemanticChunker',
    'Chunk',
    'CacheLevel',
]
