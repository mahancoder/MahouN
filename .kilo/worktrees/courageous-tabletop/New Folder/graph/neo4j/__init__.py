"""
MAHOUN Neo4j Module
===================

Neo4j database connection and operations.

Components:
- Connection Manager: Database connection pooling
- Query Builder: Cypher query construction
- Transaction Manager: ACID transaction handling
- Batch Operations: Bulk data operations

Features:
- Connection pooling
- Automatic retry logic
- Query optimization
- Transaction management
- Error handling
"""

__version__ = "2.0.0"

from graph.neo4j.connection import Neo4jConnection, get_neo4j_driver
from graph.neo4j.query_builder import CypherQueryBuilder
from graph.neo4j.operations import GraphOperations
from graph.neo4j.schema import SchemaManager

# Alias for convenience
QueryBuilder = CypherQueryBuilder

__all__ = [
    "Neo4jConnection",
    "get_neo4j_driver",
    "QueryBuilder",
    "CypherQueryBuilder",
    "GraphOperations",
    "SchemaManager",
]
