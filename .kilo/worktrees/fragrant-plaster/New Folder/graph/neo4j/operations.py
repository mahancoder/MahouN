"""
Neo4j Graph Operations
=======================

High-level operations for graph manipulation.
"""


from typing import Any, Dict, List, Optional, Tuple

from graph.neo4j.connection import Neo4jConnection, get_connection
from graph.neo4j.monitoring import Neo4jMetrics


class GraphOperations:
    """High-level graph operations"""
    
    def __init__(
        self,
        connection: Optional[Neo4jConnection] = None,
        metrics: Optional[Neo4jMetrics] = None
    ):
        """
        Initialize graph operations
        
        Args:
            connection: Neo4j connection (uses global if None)
            metrics: Metrics tracker
        """
        self.conn = connection or get_connection()
        self.metrics = metrics or Neo4jMetrics()
    
    def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
        merge: bool = True
    ) -> Dict[str, Any]:
        """
        Create or merge a node
        
        Args:
            label: Node label
            properties: Node properties
            merge: Use MERGE instead of CREATE
            
        Returns:
            Created node properties
        """
        import time
        start = time.time()
        
        # Build property string
        prop_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        
        if merge:
            query = f"""
            MERGE (n:{label} {{{prop_str}}})
            ON CREATE SET n.created_at = datetime()
            ON MATCH SET n.updated_at = datetime()
            RETURN n
            """
        else:
            query = f"""
            CREATE (n:{label} {{{prop_str}}})
            SET n.created_at = datetime()
            RETURN n
            """
        
        result = self.conn.execute_query(query, properties)
        
        self.metrics.record_query(time.time() - start)
        
        return dict(result[0]["n"]) if result else {}
    
    def create_relationship(
        self,
        from_label: str,
        from_id: str,
        to_label: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
        merge: bool = True
    ) -> bool:
        """
        Create relationship between nodes
        
        Args:
            from_label: Source node label
            from_id: Source node ID
            to_label: Target node label
            to_id: Target node ID
            rel_type: Relationship type
            properties: Relationship properties
            merge: Use MERGE instead of CREATE
            
        Returns:
            Success status
        """
        import time
        start = time.time()
        
        props = properties or {}
        prop_str = ", ".join([f"{k}: ${k}" for k in props.keys()])
        
        if merge:
            query = f"""
            MATCH (a:{from_label} {{id: $from_id}})
            MATCH (b:{to_label} {{id: $to_id}})
            MERGE (a)-[r:{rel_type}]->(b)
            SET r += ${{{prop_str}}}
            SET r.updated_at = datetime()
            RETURN r
            """
        else:
            query = f"""
            MATCH (a:{from_label} {{id: $from_id}})
            MATCH (b:{to_label} {{id: $to_id}})
            CREATE (a)-[r:{rel_type} {{{prop_str}}}]->(b)
            SET r.created_at = datetime()
            RETURN r
            """
        
        params = {
            "from_id": from_id,
            "to_id": to_id,
            **props
        }
        
        try:
            self.conn.execute_query(query, params)
            self.metrics.record_query(time.time() - start)
            return True
        except Exception as e:
            self.metrics.record_error()
            print(f"❌ Failed to create relationship: {e}")
            return False
    
    def batch_create_nodes(
        self,
        label: str,
        nodes: List[Dict[str, Any]],
        batch_size: int = 1000,
        merge: bool = True
    ) -> int:
        """
        Batch create nodes
        
        Args:
            label: Node label
            nodes: List of node properties
            batch_size: Batch size
            merge: Use MERGE instead of CREATE
            
        Returns:
            Number of nodes created
        """
        import time
        
        total_created = 0
        
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i + batch_size]
            start = time.time()
            
            if merge:
                query = f"""
                UNWIND $rows AS row
                MERGE (n:{label} {{id: row.id}})
                SET n += row
                SET n.updated_at = datetime()
                ON CREATE SET n.created_at = datetime()
                """
            else:
                query = f"""
                UNWIND $rows AS row
                CREATE (n:{label})
                SET n = row
                SET n.created_at = datetime()
                """
            
            try:
                self.conn.execute_query(query, {"rows": batch})
                total_created += len(batch)
                self.metrics.record_query(time.time() - start)
            except Exception as e:
                self.metrics.record_error()
                print(f"❌ Batch {i//batch_size + 1} failed: {e}")
        
        return total_created
    
    def batch_create_relationships(
        self,
        relationships: List[Tuple[str, str, str, Dict[str, Any]]],
        from_label: str = "Document",
        to_label: str = "Document",
        batch_size: int = 1000,
        merge: bool = True
    ) -> int:
        """
        Batch create relationships
        
        Args:
            relationships: List of (from_id, to_id, rel_type, properties)
            from_label: Source node label
            to_label: Target node label
            batch_size: Batch size
            merge: Use MERGE instead of CREATE
            
        Returns:
            Number of relationships created
        """
        import time
        
        total_created = 0
        
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i + batch_size]
            start = time.time()
            
            # Convert to dict format
            rows = [
                {
                    "from_id": from_id,
                    "to_id": to_id,
                    "rel_type": rel_type,
                    "props": props
                }
                for from_id, to_id, rel_type, props in batch
            ]
            
            if merge:
                query = f"""
                UNWIND $rows AS row
                MATCH (a:{from_label} {{id: row.from_id}})
                MATCH (b:{to_label} {{id: row.to_id}})
                MERGE (a)-[r:RELATES]->(b)
                SET r += row.props
                SET r.updated_at = datetime()
                """
            else:
                query = f"""
                UNWIND $rows AS row
                MATCH (a:{from_label} {{id: row.from_id}})
                MATCH (b:{to_label} {{id: row.to_id}})
                CREATE (a)-[r:RELATES]->(b)
                SET r = row.props
                SET r.created_at = datetime()
                """
            
            try:
                self.conn.execute_query(query, {"rows": rows})
                total_created += len(batch)
                self.metrics.record_query(time.time() - start)
            except Exception as e:
                self.metrics.record_error()
                print(f"❌ Batch {i//batch_size + 1} failed: {e}")
        
        return total_created
    
    def batch_create_typed_relationships(
        self,
        relationships: List[Tuple[str, str, str, str, str, Dict[str, Any]]],
        batch_size: int = 1000,
        merge: bool = True
    ) -> int:
        """
        Batch create relationships with different types
        
        Supports creating relationships with different types in one batch.
        Uses transaction for consistency and rollback on error.
        
        Args:
            relationships: List of (from_label, from_id, to_label, to_id, rel_type, properties)
            batch_size: Batch size (default 1000)
            merge: Use MERGE instead of CREATE
            
        Returns:
            Number of relationships created
        """
        import time
        
        total_created = 0
        
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i + batch_size]
            start = time.time()
            
            # Group by relationship type for efficiency
            by_type = {}
            for from_label, from_id, to_label, to_id, rel_type, props in batch:
                key = (from_label, to_label, rel_type)
                if key not in by_type:
                    by_type[key] = []
                by_type[key].append({
                    "from_id": from_id,
                    "to_id": to_id,
                    "props": props or {}
                })
            
            # Execute in transaction
            try:
                with self.conn.driver.session() as session:
                    with session.begin_transaction() as tx:
                        for (from_label, to_label, rel_type), rows in by_type.items():
                            if merge:
                                query = f"""
                                UNWIND $rows AS row
                                MATCH (a:{from_label} {{id: row.from_id}})
                                MATCH (b:{to_label} {{id: row.to_id}})
                                MERGE (a)-[r:{rel_type}]->(b)
                                SET r += row.props
                                SET r.updated_at = datetime()
                                ON CREATE SET r.created_at = datetime()
                                """
                            else:
                                query = f"""
                                UNWIND $rows AS row
                                MATCH (a:{from_label} {{id: row.from_id}})
                                MATCH (b:{to_label} {{id: row.to_id}})
                                CREATE (a)-[r:{rel_type}]->(b)
                                SET r = row.props
                                SET r.created_at = datetime()
                                """
                            
                            tx.run(query, {"rows": rows})
                        
                        # Commit transaction
                        tx.commit()
                
                total_created += len(batch)
                self.metrics.record_query(time.time() - start)
                
            except Exception as e:
                self.metrics.record_error()
                print(f"❌ Batch {i//batch_size + 1} failed (rolled back): {e}")
                # Transaction automatically rolled back on exception
        
        return total_created
    
    def delete_node(self, label: str, node_id: str) -> bool:
        """Delete a node and its relationships"""
        query = f"""
        MATCH (n:{label} {{id: $id}})
        DETACH DELETE n
        """
        
        try:
            self.conn.execute_query(query, {"id": node_id})
            return True
        except Exception as e:
            print(f"❌ Failed to delete node: {e}")
            return False
    
    def get_node(self, label: str, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node by ID"""
        query = f"""
        MATCH (n:{label} {{id: $id}})
        RETURN n
        """
        
        result = self.conn.execute_query(query, {"id": node_id})
        return dict(result[0]["n"]) if result else None
    
    def update_node(
        self,
        label: str,
        node_id: str,
        properties: Dict[str, Any]
    ) -> bool:
        """Update node properties"""
        query = f"""
        MATCH (n:{label} {{id: $id}})
        SET n += $props
        SET n.updated_at = datetime()
        RETURN n
        """
        
        try:
            self.conn.execute_query(
                query,
                {"id": node_id, "props": properties}
            )
            return True
        except Exception as e:
            print(f"❌ Failed to update node: {e}")
            return False


# Convenience functions
def create_document(
    doc_id: str,
    title: str,
    content: str,
    **kwargs
) -> Dict[str, Any]:
    """Create a document node"""
    ops = GraphOperations()
    return ops.create_node(
        "Document",
        {"id": doc_id, "title": title, "content": content, **kwargs}
    )


def create_relationship(
    from_id: str,
    to_id: str,
    rel_type: str = "CITES",
    **properties
) -> bool:
    """Create relationship between documents"""
    ops = GraphOperations()
    return ops.create_relationship(
        "Document", from_id,
        "Document", to_id,
        rel_type, properties
    )


def batch_create_nodes(
    label: str,
    nodes: List[Dict[str, Any]],
    batch_size: int = 1000
) -> int:
    """Batch create nodes"""
    ops = GraphOperations()
    return ops.batch_create_nodes(label, nodes, batch_size)


def batch_create_relationships(
    relationships: List[Tuple[str, str, str, Dict[str, Any]]],
    batch_size: int = 1000
) -> int:
    """Batch create relationships"""
    ops = GraphOperations()
    return ops.batch_create_relationships(relationships, batch_size=batch_size)
