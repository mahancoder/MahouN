"""
Graph Schema Module
===================

Schema definitions for the knowledge graph.
"""

from graph.schema.node_types import (
    NodeType,
    NODE_TYPE_GROUPS,
    REQUIRED_PROPERTIES,
    OPTIONAL_PROPERTIES,
    get_all_node_types,
    get_node_types_by_group,
    get_required_properties,
    get_optional_properties,
)

__all__ = [
    'NodeType',
    'NODE_TYPE_GROUPS',
    'REQUIRED_PROPERTIES',
    'OPTIONAL_PROPERTIES',
    'get_all_node_types',
    'get_node_types_by_group',
    'get_required_properties',
    'get_optional_properties',
]
