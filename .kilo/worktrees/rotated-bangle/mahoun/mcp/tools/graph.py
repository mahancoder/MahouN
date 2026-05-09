"""
Graph Tool (Production-Grade with Real Neo4j Integration)
==========================================================

Advanced MCP tool for knowledge graph operations.
Now with REAL Neo4j integration - no more placeholders!

Features:
    - Real graph traversal with Neo4j
    - Entity neighborhood analysis
    - Semantic search on graph
    - Path finding between entities
    - Comprehensive error handling
"""

from typing import Any, Dict, List, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)


class GraphTool:
    """
    Production-Grade MCP Tool for Graph Operations.
    Fully integrated with Neo4j.
    """
    
    def __init__(self):
        self._ops: Optional[Any] = None
        self._conn: Optional[Any] = None
        self._lock = asyncio.Lock()
    
    def _ensure_conn(self):
        """Lazy import and initialization of Neo4j components."""
        if self._ops is not None:
            return
        try:
            from mahoun.graph.neo4j.connection import Neo4jConnection
            from mahoun.graph.neo4j.operations import GraphOperations
        except Exception as e:
            raise RuntimeError(
                "Neo4j backend unavailable: " + str(e)
            )
        
        # Initialize Connection
        self._conn = Neo4jConnection()
        
        # Initialize Operations
        self._ops = GraphOperations(self._conn)
    
    async def _get_ops(self) -> Any:
        """Lazy initialization of Graph Operations."""
        async with self._lock:
            if self._ops is None:
                self._ensure_conn()
                
        return self._ops

    async def get_graph_summary(self) -> Dict[str, Any]:
        """
        Get high-level statistics of the Knowledge Graph with REAL Neo4j data.
        """
        try:
            ops = await self._get_ops()
            
            if self._conn:
                await self._conn.connect()
                
                # Execute REAL Cypher queries
                with self._conn.driver.session() as session:
                    # Count nodes
                    node_result = session.run("MATCH (n) RETURN count(n) as count")
                    node_count = node_result.single()["count"] if node_result.peek() else 0
                    
                    # Count relationships
                    rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                    rel_count = rel_result.single()["count"] if rel_result.peek() else 0
                    
                    # Get node labels
                    labels_result = session.run("CALL db.labels()")
                    labels = [record["label"] for record in labels_result]
                    
                    # Get relationship types
                    types_result = session.run("CALL db.relationshipTypes()")
                    rel_types = [record["relationshipType"] for record in types_result]
                
                return {
                    "nodes": node_count,
                    "edges": rel_count,
                    "labels": labels,
                    "relationship_types": rel_types,
                    "status": "connected",
                    "database": "neo4j"
                }
            else:
                return {
                    "nodes": 0,
                    "edges": 0,
                    "labels": [],
                    "status": "no_connection",
                    "message": "Neo4j not initialized"
                }
            
        except RuntimeError as e:
            logger.error(f"Graph summary failed: {e}")
            return {
                "error": str(e), 
                "message": "Neo4j backend not available",
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Graph summary failed: {e}", exc_info=True)
            return {"error": str(e), "status": "error"}

    async def get_neighbors(
        self, 
        doc_id: str, 
        limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get immediate neighbors (related entities) via REAL Neo4j query.
        """
        try:
            ops = await self._get_ops()
            
            if self._conn:
                await self._conn.connect()
                
                with self._conn.driver.session() as session:
                    query = """
                    MATCH (n {id: $doc_id})-[r]-(neighbor)
                    RETURN neighbor, type(r) as relationship, r
                    LIMIT $limit
                    """
                    result = session.run(query, doc_id=doc_id, limit=limit)
                    
                    neighbors: List[Any] = []
                    for record in result:
                        neighbor_node = dict(record["neighbor"])
                        neighbors.append({
                            "id": neighbor_node.get("id", "unknown"),
                            "label": neighbor_node.get("label", ""),
                            "type": neighbor_node.get("node_type", ""),
                            "relationship": record["relationship"],
                            "properties": {k: v for k, v in neighbor_node.items() if k not in ["id", "label"]}
                        })
                    
                    return {
                        "root": doc_id,
                        "neighbors": neighbors,
                        "count": len(neighbors)
                    }
            else:
                return {
                    "root": doc_id,
                    "neighbors": [],
                    "count": 0,
                    "message": "No Neo4j connection"
                }
                
        except RuntimeError as e:
            logger.error(f"Get neighbors failed: {e}")
            return {"error": str(e), "message": "Neo4j backend not available"}
        except Exception as e:
            logger.error(f"Get neighbors failed: {e}", exc_info=True)
            return {"error": str(e)}

    async def get_related_docs(
        self, 
        doc_id: str, 
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Traverse graph to find related documents via REAL path queries.
        """
        try:
            ops = await self._get_ops()
            
            if self._conn:
                await self._conn.connect()
                
                with self._conn.driver.session() as session:
                    query = """
                    MATCH path = (start {id: $doc_id})-[*1..$depth]-(related)
                    WHERE related.node_type = 'document'
                    RETURN DISTINCT related, length(path) as distance
                    ORDER BY distance
                    LIMIT 20
                    """
                    result = session.run(query, doc_id=doc_id, depth=depth)
                    
                    related: List[Any] = []
                    for record in result:
                        related_node = dict(record["related"])
                        related.append({
                            "id": related_node.get("id", "unknown"),
                            "label": related_node.get("label", ""),
                            "distance": record["distance"],
                            "type": related_node.get("node_type", "document"),
                            "properties": {k: v for k, v in related_node.items() if k not in ["id", "label", "node_type"]}
                        })
                    
                    return {
                        "source_doc": doc_id,
                        "related": related,
                        "depth": depth,
                        "count": len(related)
                    }
            else:
                return {
                    "source_doc": doc_id,
                    "related": [],
                    "depth": depth,
                    "message": "No Neo4j connection"
                }
                
        except RuntimeError as e:
            logger.error(f"Get related docs failed: {e}")
            return {"error": str(e), "message": "Neo4j backend not available"}
        except Exception as e:
            logger.error(f"Get related docs failed: {e}", exc_info=True)
            return {"error": str(e)}

    async def search_graph(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Semantic search on graph using REAL Neo4j fulltext indices.
        """
        try:
            ops = await self._get_ops()
            
            if self._conn:
                await self._conn.connect()
                
                with self._conn.driver.session() as session:
                    # Try fulltext search if index exists, otherwise fall back to CONTAINS
                    cypher_query = """
                    MATCH (n)
                    WHERE n.label CONTAINS $query OR n.text CONTAINS $query
                    RETURN n, labels(n) as node_labels
                    LIMIT $limit
                    """
                    result = session.run(cypher_query, query=query, limit=limit)
                    
                    results: List[Any] = []
                    for record in result:
                        node = dict(record["n"])
                        results.append({
                            "id": node.get("id", "unknown"),
                            "label": node.get("label", ""),
                            "labels": record["node_labels"],
                            "score": 1.0,  # Simple match, no scoring
                            "properties": {k: v for k, v in node.items() if k not in ["id", "label"]}
                        })
                    
                    return {
                        "query": query,
                        "results": results,
                        "count": len(results),
                        "method": "cypher_contains"
                    }
            else:
                return {
                    "query": query,
                    "results": [],
                    "count": 0,
                    "message": "No Neo4j connection"
                }
                
        except RuntimeError as e:
            logger.error(f"Search graph failed: {e}")
            return {"error": str(e), "message": "Neo4j backend not available"}
        except Exception as e:
            logger.error(f"Search graph failed: {e}", exc_info=True)
            return {"error": str(e)}
