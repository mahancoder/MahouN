"""
Graph Builders Module
====================

This module contains builders for constructing the legal knowledge graph.

Components:
- EntityExtractor: Extract entities from legal documents
- RelationshipBuilder: Build relationships between entities
- GraphBuilder: Build NetworkX and Neo4j graphs
"""

from graph.builders.entity_extractor import (
    EntityExtractor,
    Entity,
    extract_entities_from_text,
    extract_entities_batch,
    ENTITY_TYPES
)

# Using ultra systems for enhanced relationship extraction
from ultra_systems.graph import UltraRelationExtractor
from graph.builders.relationship_builder import (
    RelationshipBuilder,
    build_relationships_from_text,
    Relationship
)

# Define relationship types for compatibility
RELATIONSHIP_TYPES = {
    "CO_OCCURS",  # Co-occurrence relationship
    "CITES",  # Citation relationship
    "REFERENCES",  # Reference relationship
    "ISSUED_BY",  # Issued by relationship
    "OVERTURNS",  # Overturns/نقض relationship
    "CONFIRMS",  # Confirms/تایید relationship
    "CONTAINS",  # Contains relationship (Law -> Article)
    "HAS_NOTE",  # Has note relationship (Article -> Note)
    "HAS_CLAUSE",  # Has clause relationship (Article -> Clause)
    "BELONGS_TO",  # Belongs to relationship (Branch -> Court)
    "HEARD_IN",  # Heard in relationship (Case -> Court)
    "DECIDED_BY",  # Decided by relationship (Verdict -> Judge)
    "REPRESENTED_BY",  # Represented by relationship (Party -> Lawyer)
    "INVOLVES",  # Involves relationship (Case -> Person) - شامل شخص
    "APPEALS_TO",  # Appeals to relationship (Verdict -> Court) - تجدیدنظر/فرجام
    "FILED_BY",  # Filed by relationship (Case -> Person) - طرح شده توسط
    "AGAINST",  # Against relationship (Case -> Person) - علیه
    "BASED_ON",  # Based on relationship (Verdict -> Law/Article) - مبتنی بر
}

# Map UltraRelationExtractor to RelationshipBuilder for compatibility
# Relationship = UltraRelationExtractor

from graph.builders.graph_builder import (
    GraphBuilder
)

# Define build_graph_from_text for compatibility
build_graph_from_text = GraphBuilder().build_ultra_graph

__all__ = [
    # Entity extraction
    'EntityExtractor',
    'Entity',
    'extract_entities_from_text',
    'extract_entities_batch',
    'ENTITY_TYPES',
    
    # Relationship building
    'RelationshipBuilder',
    'Relationship',
    'build_relationships_from_text',
    'RELATIONSHIP_TYPES',
    
    # Graph building
    'GraphBuilder',
    'build_graph_from_text',
]
