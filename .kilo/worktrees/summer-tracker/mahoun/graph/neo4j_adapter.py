"""
Neo4j Adapter for Hybrid Search
===============================

Adapter for integrating Neo4j with the HybridSearch engine.
Provides batching, pagination, and query template support.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

logger = logging.getLogger(__name__)


@dataclass
class Neo4jQueryTemplate:
    """Query template for Neo4j"""
    name: str
    cypher_query: str
    default_params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class Neo4jSearchResult:
    """Search result from Neo4j"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    relationships: List[Dict[str, Any]] = field(default_factory=list)


class Neo4jAdapter:
    """
    Neo4j adapter for HybridSearch
    
    Features:
    - Batch operations
    - Pagination
    - Query templates
    - Connection pooling
    """
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j"
    ):
        """
        Initialize Neo4j adapter
        
        Args:
            uri: Neo4j URI (bolt://localhost:7687)
            user: Username
            password: Password
            database: Database name
        """
        if not HAS_NEO4J:
            raise ImportError(
                "neo4j driver not installed. "
                "Install it with: pip install neo4j"
            )
        
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
        
        # Query templates
        self.query_templates: Dict[str, Neo4jQueryTemplate] = {}
        
        # Initialize default templates
        self._init_default_templates()
    
    def _init_default_templates(self):
        """Initialize default query templates"""
        self.query_templates["entity_search"] = Neo4jQueryTemplate(
            name="entity_search",
            cypher_query="""
                MATCH (n)
                WHERE toLower(n.name) CONTAINS toLower($query)
                RETURN n.id AS id, n.name AS content, 1.0 AS score,
                       properties(n) AS metadata
                ORDER BY score DESC
                SKIP $offset
                LIMIT $limit
            """,
            default_params={"limit": 10, "offset": 0},
            description="Search for entities by name"
        )
        
        self.query_templates["relationship_search"] = Neo4jQueryTemplate(
            name="relationship_search",
            cypher_query="""
                MATCH (a)-[r]->(b)
                WHERE toLower(r.type) CONTAINS toLower($query)
                RETURN a.id + '->' + b.id AS id, 
                       a.name + ' ' + r.type + ' ' + b.name AS content,
                       1.0 AS score,
                       properties(r) AS metadata
                ORDER BY score DESC
                SKIP $offset
                LIMIT $limit
            """,
            default_params={"limit": 10, "offset": 0},
            description="Search for relationships by type"
        )
        
        self.query_templates["path_search"] = Neo4jQueryTemplate(
            name="path_search",
            cypher_query="""
                MATCH p = (start)-[*1..3]->(end)
                WHERE toLower(start.name) CONTAINS toLower($query) 
                   OR toLower(end.name) CONTAINS toLower($query)
                RETURN toString(id(p)) AS id,
                       [n IN nodes(p) | n.name] AS content,
                       1.0 AS score,
                       {path_length: length(p)} AS metadata
                ORDER BY length(p)
                SKIP $offset
                LIMIT $limit
            """,
            default_params={"limit": 10, "offset": 0},
            description="Search for paths between entities"
        )
        
        self.query_templates["community_search"] = Neo4jQueryTemplate(
            name="community_search",
            cypher_query="""
                MATCH (n)
                WHERE toLower(n.name) CONTAINS toLower($query)
                WITH n
                MATCH (n)-[:BELONGS_TO]->(c:Community)
                RETURN c.id AS id,
                       c.name AS content,
                       1.0 AS score,
                       {community_size: size((c)<-[:BELONGS_TO]-())} AS metadata
                ORDER BY score DESC
                SKIP $offset
                LIMIT $limit
            """,
            default_params={"limit": 10, "offset": 0},
            description="Search for communities containing entities"
        )
    
    async def initialize(self) -> None:
        """Initialize Neo4j driver"""
        logger.info(f"Initializing Neo4j adapter: {self.uri}")
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        
        # Verify connection
        try:
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j connection verified")
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
            raise
    
    def _execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute query with error handling
        
        Args:
            query: Cypher query
            parameters: Query parameters
            
        Returns:
            Query results
        """
        if self.driver is None:
            raise RuntimeError("Adapter not initialized. Call initialize() first.")
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Neo4jSearchResult]:
        """
        Search nodes and relationships with pagination
        
        Args:
            query: Search query
            limit: Number of results
            offset: Offset for pagination
            filter: Additional filters
            
        Returns:
            List of search results
        """
        # Default search - look for nodes with matching properties
        cypher_query = """
            MATCH (n)
            WHERE any(prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS toLower($query))
            RETURN n.id AS id, 
                   head([prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS toLower($query) | toString(n[prop])]) AS content,
                   1.0 AS score,
                   properties(n) AS metadata
            ORDER BY score DESC
            SKIP $offset
            LIMIT $limit
        """
        
        parameters = {
            "query": query,
            "limit": limit,
            "offset": offset
        }
        
        results = self._execute_query(cypher_query, parameters)
        
        search_results = []
        for record in results:
            search_results.append(Neo4jSearchResult(
                id=record.get("id", ""),
                content=record.get("content", ""),
                score=record.get("score", 0.0),
                metadata=record.get("metadata", {})
            ))
        
        return search_results
    
    async def search_with_template(
        self,
        template_name: str,
        **kwargs
    ) -> List[Neo4jSearchResult]:
        """
        Search using a predefined query template
        
        Args:
            template_name: Name of the query template
            **kwargs: Query parameters
            
        Returns:
            List of search results
        """
        if template_name not in self.query_templates:
            raise ValueError(f"Unknown query template: {template_name}")
        
        template = self.query_templates[template_name]
        
        # Merge parameters
        parameters = template.default_params.copy()
        parameters.update(kwargs)
        
        # Execute query
        results = self._execute_query(template.cypher_query, parameters)
        
        search_results = []
        for record in results:
            search_results.append(Neo4jSearchResult(
                id=record.get("id", ""),
                content=record.get("content", ""),
                score=record.get("score", 0.0),
                metadata=record.get("metadata", {})
            ))
        
        return search_results
    
    async def get_node(self, node_id: str) -> Optional[Neo4jSearchResult]:
        """
        Get node by ID
        
        Args:
            node_id: Node ID
            
        Returns:
            Node or None if not found
        """
        cypher_query = """
            MATCH (n {id: $node_id})
            RETURN n.id AS id, 
                   head([prop IN keys(n) WHERE prop <> 'id' | toString(n[prop])]) AS content,
                   1.0 AS score,
                   properties(n) AS metadata
        """
        
        results = self._execute_query(cypher_query, {"node_id": node_id})
        
        if results:
            record = results[0]
            return Neo4jSearchResult(
                id=record.get("id", ""),
                content=record.get("content", ""),
                score=record.get("score", 0.0),
                metadata=record.get("metadata", {})
            )
        
        return None
    
    async def get_relationships(
        self,
        node_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a node
        
        Args:
            node_id: Node ID
            limit: Maximum number of relationships
            
        Returns:
            List of relationships
        """
        cypher_query = """
            MATCH (n {id: $node_id})-[r]->(m)
            RETURN n.id AS source_id,
                   m.id AS target_id,
                   type(r) AS relationship_type,
                   properties(r) AS metadata
            LIMIT $limit
        """
        
        return self._execute_query(cypher_query, {
            "node_id": node_id,
            "limit": limit
        })
    
    async def add_nodes(
        self,
        nodes: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> None:
        """
        Add nodes in batches
        
        Args:
            nodes: List of node dictionaries with 'id' and properties
            batch_size: Batch size for insertion
        """
        if self.driver is None:
            raise RuntimeError("Adapter not initialized. Call initialize() first.")
        
        # Process in batches
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i + batch_size]
            
            # Build Cypher query for batch
            query_parts = []
            parameters = {}
            
            for idx, node in enumerate(batch):
                param_prefix = f"node_{idx}_"
                set_clauses = []
                
                for key, value in node.items():
                    if key != 'id':  # Skip id as it's used in MATCH
                        set_clauses.append(f"n.{key} = ${param_prefix}{key}")
                        parameters[f"{param_prefix}{key}"] = value
                
                query_parts.append(f"""
                    MERGE (n {{id: ${param_prefix}id}})
                    SET {', '.join(set_clauses)}
                """)
                
                parameters[f"{param_prefix}id"] = node.get('id')
            
            # Execute batch
            cypher_query = "WITH 1 as dummy\n" + "\n".join(query_parts)
            
            with self.driver.session(database=self.database) as session:
                session.run(cypher_query, parameters)
            
            logger.debug(f"Added batch of {len(batch)} nodes")
    
    async def add_relationships(
        self,
        relationships: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> None:
        """
        Add relationships in batches
        
        Args:
            relationships: List of relationship dictionaries
            batch_size: Batch size for insertion
        """
        if self.driver is None:
            raise RuntimeError("Adapter not initialized. Call initialize() first.")
        
        # Process in batches
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i + batch_size]
            
            # Build Cypher query for batch
            query_parts = []
            parameters = {}
            
            for idx, rel in enumerate(batch):
                param_prefix = f"rel_{idx}_"
                
                query_parts.append(f"""
                    MATCH (a {{id: ${param_prefix}source_id}}), (b {{id: ${param_prefix}target_id}})
                    MERGE (a)-[r:{rel.get('type', 'RELATED_TO')}]->(b)
                    SET r += ${param_prefix}properties
                """)
                
                parameters[f"{param_prefix}source_id"] = rel.get('source_id')
                parameters[f"{param_prefix}target_id"] = rel.get('target_id')
                parameters[f"{param_prefix}properties"] = {
                    k: v for k, v in rel.items() 
                    if k not in ['source_id', 'target_id', 'type']
                }
            
            # Execute batch
            cypher_query = "WITH 1 as dummy\n" + "\n".join(query_parts)
            
            with self.driver.session(database=self.database) as session:
                session.run(cypher_query, parameters)
            
            logger.debug(f"Added batch of {len(batch)} relationships")
    
    async def delete_nodes(self, node_ids: List[str]) -> None:
        """
        Delete nodes by IDs
        
        Args:
            node_ids: Node IDs to delete
        """
        if self.driver is None:
            raise RuntimeError("Adapter not initialized. Call initialize() first.")
        
        cypher_query = """
            MATCH (n {id: $node_id})
            DETACH DELETE n
        """
        
        with self.driver.session(database=self.database) as session:
            for node_id in node_ids:
                session.run(cypher_query, {"node_id": node_id})
        
        logger.debug(f"Deleted {len(node_ids)} nodes")
    
    def add_query_template(self, template: Neo4jQueryTemplate) -> None:
        """
        Add a custom query template
        
        Args:
            template: Query template to add
        """
        self.query_templates[template.name] = template
        logger.debug(f"Added query template: {template.name}")
    
    async def count_nodes(self) -> int:
        """
        Get total node count
        
        Returns:
            Number of nodes
        """
        cypher_query = "MATCH (n) RETURN count(n) AS count"
        results = self._execute_query(cypher_query)
        return results[0]["count"] if results else 0
    
    async def close(self) -> None:
        """Close connection"""
        if self.driver:
            self.driver.close()
            self.driver = None
            logger.info("Neo4j adapter closed")