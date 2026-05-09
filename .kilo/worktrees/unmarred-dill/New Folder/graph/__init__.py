"""
MAHOUN Graph Module
===================

Neo4j knowledge graph operations for legal entities, relationships,
and semantic search.

Components:
- Schema: Node types and relationship definitions
- Neo4j: Database connection and operations
- Builders: Graph construction from documents
- Services: Query and traversal services
- Importers: Bulk data import utilities
- Validation: Schema and data validation
- Backup: Graph backup and recovery
- Security: RBAC and data anonymization

Features:
- Legal entity modeling (laws, articles, cases, precedents)
- Semantic relationship tracking
- Citation networks
- Temporal versioning
- Full-text search integration
- Role-based access control
- Data anonymization
"""

__version__ = "2.0.0"

# Schema
from graph.schema import (
    NodeType,
    NODE_TYPE_GROUPS,
    get_all_node_types,
    get_node_types_by_group,
)

# Neo4j Connection
from graph.neo4j import (
    Neo4jConnection,
    get_neo4j_driver,
    QueryBuilder,
    GraphOperations,
    SchemaManager,
)

# Builders
# Using ultra systems for enhanced functionality
from ultra_systems.graph import (
    UltraGraphBuilder,
    UltraRelationExtractor,
    UltraGATTrainer,
    UltraGraphQueryService
)
from graph.builders import (
    EntityExtractor,
    Entity,
    RelationshipBuilder,
    build_graph_from_text,
)
# Map Ultra classes to existing names for compatibility
GraphBuilder = UltraGraphBuilder
GraphQueryService = UltraGraphQueryService

# Retrieval
from graph.retrieval import (
    GraphHopRetriever,
    HopResult,
    expand_with_graph_hops,
    GATReranker,
    GATRerankerModel,
    RerankResult,
    create_gat_reranker,
)

# Services
# Using ultra systems for enhanced functionality
from ultra_systems.graph import UltraGraphQueryService
from graph.services import (
    GraphAnalytics,
)
# Map UltraGraphQueryService to GraphQueryService for compatibility
GraphQueryService = UltraGraphQueryService

# Importers
from graph.importers import (
    LawImporter,
    DocumentImporter,
    BatchImporter,
)

# Validation
from graph.validation import (
    DataQualityValidator,
    validate_graph_quality,
)

# Backup
from graph.backup import (
    Neo4jBackupManager,
    create_backup,
    restore_backup,
)

# Security
from graph.security import (
    DataAnonymizer,
    RBACManager,
    Role,
    Permission,
)

__all__ = [
    # Schema
    "NodeType",
    "NODE_TYPE_GROUPS",
    "get_all_node_types",
    "get_node_types_by_group",
    # Neo4j
    "Neo4jConnection",
    "get_neo4j_driver",
    "QueryBuilder",
    "GraphOperations",
    "SchemaManager",
    # Builders
    "EntityExtractor",
    "Entity",
    "RelationshipBuilder",
    "Relationship",
    "GraphBuilder",
    "build_graph_from_text",
    # Retrieval
    "GraphHopRetriever",
    "HopResult",
    "expand_with_graph_hops",
    "GATReranker",
    "GATRerankerModel",
    "RerankResult",
    "create_gat_reranker",
    # Services
    "GraphQueryService",
    "GraphAnalytics",
    # Importers
    "LawImporter",
    "DocumentImporter",
    "BatchImporter",
    # Validation
    "DataQualityValidator",
    "validate_graph_quality",
    # Backup
    "Neo4jBackupManager",
    "create_backup",
    "restore_backup",
    # Security
    "DataAnonymizer",
    "RBACManager",
    "Role",
    "Permission",
]
