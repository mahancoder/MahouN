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
from typing import Any, Optional

__version__ = "2.0.0"

try:
    import neo4j  # type: ignore
    _NEO4J_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    neo4j: Optional[Any] = None
    _NEO4J_AVAILABLE = False

class _Neo4jMissingDependency(RuntimeError):
    pass

def _raise():
    raise _Neo4jMissingDependency(
        "Neo4j backend is not installed. Install with: pip install neo4j"
    )

if _NEO4J_AVAILABLE:
    try:
        from mahoun.graph.neo4j.query_builder import CypherQueryBuilder
        from mahoun.graph.neo4j.operations import GraphOperations
        from mahoun.graph.neo4j.schema import SchemaManager, Constraint, Index
    except (ImportError, ModuleNotFoundError):
        # Submodules failed to import (e.g., missing dependencies)
        _NEO4J_AVAILABLE = False
        neo4j: Optional[Any] = None
        # Define stub classes
        class Neo4jConnection:
            def __init__(self, *a, **kw): _raise()

        
        def get_connection(*a, **kw): _raise()

        class CypherQueryBuilder:
            def __init__(self, *a, **kw): _raise()

        class GraphOperations:
            def __init__(self, *a, **kw): _raise()

        class SchemaManager:
            def __init__(self, *a, **kw): _raise()
            
        class Constraint:
            def __init__(self, *a, **kw): _raise()
            
        class Index:
            def __init__(self, *a, **kw): _raise()
else:
    # Define stub classes when neo4j package is not available
    class Neo4jConnection:
        def __init__(self, *a, **kw): _raise()

    
    def get_connection(*a, **kw): _raise()

    class CypherQueryBuilder:
        def __init__(self, *a, **kw): _raise()

    class GraphOperations:
        def __init__(self, *a, **kw): _raise()

    class SchemaManager:
        def __init__(self, *a, **kw): _raise()

    class Constraint:
        def __init__(self, *a, **kw): _raise()

    class Index:
        def __init__(self, *a, **kw): _raise()

# Alias for convenience
QueryBuilder = CypherQueryBuilder

__all__ = [
    "Neo4jConnection",
    "get_connection",
    "QueryBuilder",
    "CypherQueryBuilder",
    "GraphOperations",
    "SchemaManager",
    "Constraint",
    "Index",
]
