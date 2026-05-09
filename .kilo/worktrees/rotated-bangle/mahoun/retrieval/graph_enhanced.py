"""
Graph-Enhanced Retriever
========================
Implements the "Anchor & Expand" hybrid retrieval capability.

Algorithm:
1. Anchor: Find top-k nodes via Vector Similarity (GGUF embedding).
2. Expand: Traverse graph relationships (CITES, RELATED_TO, etc.).
3. Fusion: Combine and rerank results to capture "delicacy".
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from mahoun.pipelines.ingestion.enhanced_embedding import EnhancedEmbeddingService

logger = logging.getLogger(__name__)

@dataclass
class HybridResult:
    node_id: str
    label: str
    text: str
    score: float
    source: str  # "vector_anchor" or "graph_expansion"
    relationship: Optional[str] = None


class GraphEnhancedRetriever:
    """Retrieves legal context using both Vector similarity and Graph connectivity."""
    
    def __init__(self, neo4j_driver):
        self.neo4j = neo4j_driver
        self.embedding_service = EnhancedEmbeddingService(backend="auto")
        
        # Configuration
        self.anchor_k = 5
        self.expansion_depth = 1
        
        logger.info("GraphEnhancedRetriever initialized")

    async def retrieve(self, query: str) -> List[HybridResult]:
        """
        Execute Anchor & Expand retrieval.
        
        Args:
            query: Natural language query
        
        Returns:
            List of unique, relevant HybridResults
        """
        if not self.neo4j:
            logger.warning("No Neo4j driver available for graph retrieval")
            return []

        # 1. Generate Query Vector
        query_vector = self.embedding_service.embed_texts([query])[0]
        
        # 2. Execute Hybrid Cypher Query
        # This query finds anchors via vector index, then expands
        cypher_query = """
        // Step 1: Find Anchors (Verdict) using Vector Index
        CALL db.index.vector.queryNodes('verdict_embedding_idx', $k, $embedding)
        YIELD node as anchor, score
        WHERE score > 0.7  // Similarity threshold
        
        // Step 2: Expand to Related Nodes
        // Find things the verdict cites (Articles) or related Contracts
        OPTIONAL MATCH (anchor)-[r:CITES|RELATED_TO]->(expanded)
        
        // Step 3: Return both Anchor and Expanded context
        RETURN 
            anchor.id as anchor_id,
            labels(anchor)[0] as anchor_label,
            anchor.content as anchor_text,
            score as vector_score,
            collect({
                id: expanded.id,
                label: labels(expanded)[0],
                text: expanded.content,
                rel: type(r)
            }) as expansions
        """
        
        results = []
        
        try:
            with self.neo4j.session() as session:
                records = session.run(
                    cypher_query, 
                    embedding=query_vector.tolist(),  # Ensure list, not numpy
                    k=self.anchor_k
                )
                
                for record in records:
                    # add Anchor
                    results.append(HybridResult(
                        node_id=record["anchor_id"],
                        label=record["anchor_label"],
                        text=record["anchor_text"],
                        score=record["vector_score"],
                        source="vector_anchor"
                    ))
                    
                    # add Expansions
                    expansions = record["expansions"]
                    if expansions:
                        for exp in expansions:
                            if exp["id"]:  # Ensure valid node
                                results.append(HybridResult(
                                    node_id=exp["id"],
                                    label=exp["label"],
                                    text=exp["text"],
                                    score=record["vector_score"] * 0.9,  # Decay score slightly
                                    source="graph_expansion",
                                    relationship=exp["rel"]
                                ))
                                
            # Deduplicate by ID, keeping highest score
            unique_results = {}
            for r in results:
                if r.node_id not in unique_results or r.score > unique_results[r.node_id].score:
                    unique_results[r.node_id] = r
            
            # Sort by score
            final_results = sorted(unique_results.values(), key=lambda x: x.score, reverse=True)
            return final_results
            
        except Exception as e:
            logger.error(f"Graph retrieval failed: {e}")
            return []
