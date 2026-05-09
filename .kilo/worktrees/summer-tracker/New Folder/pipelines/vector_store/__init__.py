"""
Vector Store Management Module
===============================

Provides unified interface for multiple vector store backends with
backup, restore, and advanced search capabilities.

Components:
- VectorStoreManager: Main manager class
- VectorStoreBackend: Abstract base for backends
- ChromaDBBackend: ChromaDB implementation
- FAISSBackend: FAISS implementation
"""

__version__ = "1.0.0"

from pipelines.vector_store.backends.base import (
    VectorStoreBackend,
    SearchResult,
    VectorStoreConfig,
)
from pipelines.vector_store.manager import VectorStoreManager

__all__ = [
    "VectorStoreBackend",
    "SearchResult",
    "VectorStoreConfig",
    "VectorStoreManager",
]
