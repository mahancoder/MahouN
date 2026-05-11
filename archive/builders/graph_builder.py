"""
Graph Builder for Legal Knowledge Graph
========================================

Builds NetworkX and Neo4j graphs from extracted entities and relationships.
Integrates with entity_extractor and relationship_builder modules.

Now with Ultra-Advanced capabilities:
- Multi-source construction
- Real-time updates
- Quality assessment
- Advanced analytics
- Performance optimization
"""

import logging
from typing import List, Dict, Optional, Set, Tuple, Any
from collections import defaultdict, Counter
import time
from datetime import datetime

try:
    import networkx as nx
except ImportError:
    nx = None

# Neo4j imports handled dynamically
NEO4J_AVAILABLE = False

from graph.builders.entity_extractor import Entity
from graph.builders.relationship_builder import Relationship, RelationshipBuilder

# Import from ultra systems
from ultra_systems.graph import UltraGraphBuilder
from ultra_systems.graph.ultra_graph_builder import GraphNode, GraphEdge, GraphMetrics

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Build knowledge graphs from entities and relationships with ultra capabilities
    
    Supports:
    - NetworkX graphs (in-memory)
    - Neo4j graphs (persistent)
    - Graph statistics and validation
    - Ultra-advanced features from UltraGraphBuilder
    """
    
    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        use_neo4j: bool = False,
        enable_quality_assessment: bool = True,
        enable_analytics: bool = True,
        enable_real_time_updates: bool = True,
        batch_size: int = 1000,
    ):
        """
        Initialize GraphBuilder with ultra capabilities
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            use_neo4j: Whether to use Neo4j
            enable_quality_assessment: Enable quality assessment
            enable_analytics: Enable advanced analytics
            enable_real_time_updates: Enable real-time updates
            batch_size: Batch size for processing
        """
        self.use_neo4j = use_neo4j
        self.neo4j_driver = None
        
        # Initialize Neo4j if requested
        if self.use_neo4j:
            try:
                # Import neo4j dynamically
                from neo4j import GraphDatabase
                self.neo4j_driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password)
                )
                logger.info("Neo4j connection established")
                global NEO4J_AVAILABLE
                NEO4J_AVAILABLE = True
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                self.use_neo4j = False
        
        # Initialize relationship builder
        self.relationship_builder = RelationshipBuilder()
        
        # Initialize ultra graph builder
        self.ultra_builder = UltraGraphBuilder(
            enable_quality_assessment=enable_quality_assessment,
            enable_analytics=enable_analytics,
            enable_real_time_updates=enable_real_time_updates,
            batch_size=batch_size
        )
        
        logger.info(f"Ultra GraphBuilder initialized (use_neo4j={self.use_neo4j})")
    
    def build_networkx_graph(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> Optional[Any]:
        """
        Build NetworkX directed graph with ultra capabilities
        
        Args:
            entities: List of entities
            relationships: List of relationships
        
        Returns:
            NetworkX DiGraph or None if networkx not available
        """
        if nx is None:
            logger.error("NetworkX not available")
            return None
        
        try:
            # Create directed graph
            G = nx.DiGraph()
            
            # Add nodes (entities)
            for entity in entities:
                G.add_node(
                    entity.normalized_text,
                    label=entity.label,
                    text=entity.text,
                    score=entity.score,
                    source=entity.source,
                    start=entity.start,
                    end=entity.end,
                    metadata=entity.metadata
                )
            
            # Add edges (relationships)
            for rel in relationships:
                G.add_edge(
                    rel.source_entity.normalized_text,
                    rel.target_entity.normalized_text,
                    type=rel.rel_type,
                    strength=rel.strength,
                    confidence=rel.confidence,
                    properties=rel.properties
                )
            
            logger.info(
                f"Built NetworkX graph: {G.number_of_nodes()} nodes, "
                f"{G.number_of_edges()} edges"
            )
            
            return G
            
        except Exception as e:
            logger.error(f"Error building NetworkX graph: {e}")
            return None
    
    def build_neo4j_graph(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        clear_existing: bool = False
    ) -> bool:
        """
        Build Neo4j graph with ultra capabilities
        
        Args:
            entities: List of entities
            relationships: List of relationships
            clear_existing: Whether to clear existing data
        
        Returns:
            True if successful
        """
        if not self.use_neo4j or not self.neo4j_driver:
            logger.error("Neo4j not available")
            return False
        
        try:
            with self.neo4j_driver.session() as session:
                # Clear existing data if requested
                if clear_existing:
                    session.run("MATCH (n) DETACH DELETE n")
                    logger.info("Cleared existing Neo4j data")
                
                # Create nodes (entities)
                for entity in entities:
                    session.run(
                        f"""
                        MERGE (e:Entity {{id: $id}})
                        SET e.label = $label,
                            e.text = $text,
                            e.normalized_text = $normalized_text,
                            e.score = $score,
                            e.source = $source,
                            e.start = $start,
                            e.end = $end
                        """,
                        id=entity.normalized_text,
                        label=entity.label,
                        text=entity.text,
                        normalized_text=entity.normalized_text,
                        score=entity.score,
                        source=entity.source,
                        start=entity.start,
                        end=entity.end
                    )
                
                logger.info(f"Created {len(entities)} nodes in Neo4j")
                
                # Create relationships
                for rel in relationships:
                    session.run(
                        f"""
                        MATCH (a:Entity {{id: $source_id}})
                        MATCH (b:Entity {{id: $target_id}})
                        MERGE (a)-[r:{rel.rel_type}]->(b)
                        SET r.strength = $strength,
                            r.confidence = $confidence
                        """,
                        source_id=rel.source_entity.normalized_text,
                        target_id=rel.target_entity.normalized_text,
                        strength=rel.strength,
                        confidence=rel.confidence
                    )
                
                logger.info(f"Created {len(relationships)} relationships in Neo4j")
            
            return True
            
        except Exception as e:
            logger.error(f"Error building Neo4j graph: {e}")
            return False
    
    def build_ultra_graph(
        self,
        entities: List[Dict],
        relationships: List[Dict],
        source_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build ultra-advanced graph with quality assessment and analytics
        
        Args:
            entities: List of entity dictionaries
            relationships: List of relationship dictionaries
            source_id: Source document/dataset ID
        
        Returns:
            Ultra graph build result
        """
        return self.ultra_builder.build_graph(entities, relationships, source_id)
    
    def query_neighbors(self, node_id: str, max_depth: int = 1) -> List[Dict]:
        """
        Query neighbors of a node using ultra capabilities
        
        Args:
            node_id: Node ID to query
            max_depth: Maximum depth for neighbor search
        
        Returns:
            List of neighbor nodes
        """
        neighbors = self.ultra_builder.query_neighbors(node_id, max_depth)
        return [node.__dict__ for node in neighbors]
    
    def compute_analytics(self) -> Dict[str, Any]:
        """
        Compute advanced graph analytics using ultra capabilities
        
        Returns:
            Analytics results
        """
        return self.ultra_builder.compute_analytics()
    
    def get_subgraph(self, node_ids: List[str]) -> Dict[str, Any]:
        """
        Extract subgraph containing specified nodes
        
        Args:
            node_ids: List of node IDs
        
        Returns:
            Subgraph data
        """
        return self.ultra_builder.get_subgraph(node_ids)