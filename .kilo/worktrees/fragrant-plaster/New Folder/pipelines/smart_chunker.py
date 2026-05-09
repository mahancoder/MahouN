"""
Smart Chunker - Re-export from data_prep_advanced
==================================================

This module re-exports the SmartChunker implementation from
pipelines.data_prep_advanced.smart_chunker for backward compatibility.

For new code, prefer importing directly from:
    from pipelines.data_prep_advanced.smart_chunker import SmartChunker
"""

# Re-export all public APIs from the actual implementation
from pipelines.data_prep_advanced.smart_chunker import (
    SmartChunker,
    ChunkingStrategy,
    Chunk,
)

__all__ = [
    'SmartChunker',
    'ChunkingStrategy',
    'Chunk',
]
