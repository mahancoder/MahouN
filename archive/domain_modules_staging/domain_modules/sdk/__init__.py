"""
MAHOUN Python SDK
=================

Official Python client library for MAHOUN Advanced Chunking & Vector DB API.

Quick Start:
    from sdk import MahounClient
    
    client = MahounClient(base_url="http://localhost:8000")
    result = client.chunking.chunk_text("Your text here")

For more examples, see sdk/examples.py or sdk/README.md
"""

from sdk.mahoun_client import (
    MahounClient,
    ChunkingClient,
    EmbeddingClient,
    RetrievalClient,
    Chunk,
    SearchResult,
    quick_chunk,
    quick_embed,
    quick_search,
)

__version__ = "1.0.0"
__author__ = "MAHOUN Team"
__email__ = "support@mahoun.ai"

__all__ = [
    "MahounClient",
    "ChunkingClient",
    "EmbeddingClient",
    "RetrievalClient",
    "Chunk",
    "SearchResult",
    "quick_chunk",
    "quick_embed",
    "quick_search",
]
