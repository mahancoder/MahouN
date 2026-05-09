"""
Graph Retrieval Module
======================

Graph-enhanced retrieval components for MAHOUN.
"""

from graph.retrieval.graph_hop import (
    GraphHopRetriever,
    HopResult,
    expand_with_graph_hops
)

# Using ultra systems for enhanced GAT reranking
from ultra_systems.graph import UltraGATTrainer
from graph.retrieval.gat_reranker import (
    RerankResult,
    create_gat_reranker
)

# Map UltraGATTrainer to GATReranker for compatibility
GATReranker = UltraGATTrainer
GATRerankerModel = UltraGATTrainer

__all__ = [
    # Graph hop
    'GraphHopRetriever',
    'HopResult',
    'expand_with_graph_hops',
    
    # GAT reranker
    'GATReranker',
    'GATRerankerModel',
    'RerankResult',
    'create_gat_reranker',
]
