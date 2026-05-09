"""
Graph Module - Enterprise Graph Builder
========================================

Exports the recommended graph builder for production use.

For backward compatibility, UltraGraphBuilder is still available,
but ConcurrentGraphBuilder is recommended for production.
"""

from mahoun.graph.ultra_graph_builder import (
    UltraGraphBuilder,
    GraphNode,
    GraphEdge
)

# Import concurrent builder (recommended for production)
try:
    from mahoun.graph.concurrent_graph_builder import ConcurrentGraphBuilder
    HAS_CONCURRENT_BUILDER = True
except ImportError:
    HAS_CONCURRENT_BUILDER = False
    ConcurrentGraphBuilder = None  # type: ignore

# Default builder (use concurrent if available)
if HAS_CONCURRENT_BUILDER:
    DefaultGraphBuilder = ConcurrentGraphBuilder
else:
    DefaultGraphBuilder = UltraGraphBuilder

__all__ = [
    "UltraGraphBuilder",
    "ConcurrentGraphBuilder",
    "DefaultGraphBuilder",
    "GraphNode",
    "GraphEdge",
]
