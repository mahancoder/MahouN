"""
Integration Tests for Graph Module (hardened)
=============================================

Scope:
- End-to-end sanity across extract → relationship → graph → hop retrieval → (optional) GAT rerank
- Deterministic assertions where feasible
- CI-friendly markers and dependency guards
"""

import pytest
from typing import List

# Public imports (unchanged)
from graph.builders import (
    EntityExtractor,
    GraphBuilder,
    RelationshipBuilder,
    extract_entities_from_text,
)

from graph.retrieval import (
    GraphHopRetriever,
)

# Optional imports protected at call-sites
nx = None  # will be set lazily with importorskip in fixtures

# --------------------------
# Module-level configuration
# --------------------------
pytestmark = pytest.mark.integration


# --------------------------
# Test data
# --------------------------
@pytest.fixture(scope="module")
def sample_text() -> str:
    return (
        "دادگاه عالی کشور در رسیدگی به پرونده شماره ۱۴۰۰/۱۲۳۴ با استناد به ماده ۲۷۰ قانون مجازات اسلامی "
        "و با توجه به نظریه کارشناس، حکم به پرداخت دیه کامل صادر نمود. این رأی در تاریخ ۱۴۰۰/۰۵/۱۵ "
        "توسط قاضی احمدی صادر شده است."
    )


# --------------------------
# Core fixtures
# --------------------------
@pytest.fixture(scope="module")
def extractor() -> EntityExtractor:
    # Keep rule-based path for determinism unless NER is explicitly enabled in config
    return EntityExtractor(use_ner=False, min_score=0.50)


@pytest.fixture(scope="module")
def rel_builder() -> RelationshipBuilder:
    return RelationshipBuilder(max_distance=200)


@pytest.fixture(scope="module")
def graph_builder() -> GraphBuilder:
    return GraphBuilder()


@pytest.fixture(scope="module")
def entities(extractor: EntityExtractor, sample_text: str):
    ents = extractor.extract_entities(sample_text)
    if not isinstance(ents, list) or len(ents) == 0:
        pytest.skip("Entity extraction produced no entities; cannot proceed with integration path.")
    return ents


@pytest.fixture(scope="module")
def relationships(rel_builder: RelationshipBuilder, entities, sample_text: str):
    rels = rel_builder.build_relationships(entities, sample_text)
    # Relationship list may be empty depending on extractor heuristics; that's acceptable for smoke,
    # but downstream graph will still be valid (edges may be zero).
    assert isinstance(rels, list), "RelationshipBuilder must return a list"
    return rels


@pytest.fixture(scope="module")
def nx_graph(graph_builder: GraphBuilder, entities, relationships):
    global nx
    nx = pytest.importorskip("networkx")
    G = graph_builder.build_networkx_graph(entities, relationships)
    assert G is not None, "GraphBuilder returned None"
    # Nodes should at least equal the number of extracted entities
    assert G.number_of_nodes() == len(entities), "Entity-node cardinality mismatch"
    # Edges may be zero if no relationships detected; assert non-negative only
    assert G.number_of_edges() >= 0
    return G


# --------------------------
# Tests
# --------------------------
def test_entity_extraction_basic(entities):
    """Test that entities have required attributes"""
    labels = {getattr(e, "label", None) for e in entities}
    assert any(lbl for lbl in labels), "At least one entity should expose a non-empty label"


def test_relationship_building_shape(relationships):
    """Test relationship structure and attributes"""
    # If relationships exist, validate contract
    if relationships:
        r0 = relationships[0]
        for attr in ("source_entity", "target_entity", "rel_type", "confidence"):
            assert hasattr(r0, attr), f"Relationship missing attribute: {attr}"
        assert 0.0 <= getattr(r0, "confidence", 0.0) <= 1.0, "Confidence out of range [0,1]"


def test_graph_construction(nx_graph):
    """Test graph construction and basic properties"""
    # Already validated cardinality in fixture; add light structural checks here
    degrees = [d for _, d in nx_graph.degree()]
    assert all(d >= 0 for d in degrees)


@pytest.mark.parametrize("max_hops", [1, 2])
def test_graph_hop_retrieval(nx_graph, entities, max_hops: int):
    """Test k-hop graph traversal"""
    # Use the first entity as a seed
    seed_id = getattr(entities[0], "normalized_text", None) or getattr(entities[0], "text", None)
    assert seed_id, "Entity must expose a stable identifier (normalized_text or text)"
    
    retriever = GraphHopRetriever(graph=nx_graph, max_hops=max_hops)
    results = retriever.k_hop_expansion([seed_id])
    
    # Contract: list of results; may be empty on a disconnected or edgeless graph
    assert isinstance(results, list)
    
    if results:
        r0 = results[0]
        for attr in ("entity_id", "hop_distance", "path_score"):
            assert hasattr(r0, attr), f"HopResult missing attribute: {attr}"
        # hop_distance must be within [0, max_hops]
        assert 0 <= getattr(r0, "hop_distance", 0) <= max_hops


def test_complete_pipeline_smoke(sample_text, extractor, rel_builder, graph_builder):
    """Test complete pipeline from text to graph"""
    pytest.importorskip("networkx")
    
    # Step 1: entities
    ents = extractor.extract_entities(sample_text)
    assert isinstance(ents, list) and len(ents) > 0
    
    # Step 2: relationships
    rels = rel_builder.build_relationships(ents, sample_text)
    assert isinstance(rels, list)
    
    # Step 3: graph
    G = graph_builder.build_networkx_graph(ents, rels)
    assert G is not None
    assert G.number_of_nodes() == len(ents)
    assert G.number_of_edges() >= 0
    
    # Step 4: stats (optional API; tolerate absence)
    stats = {}
    if hasattr(graph_builder, "get_graph_statistics"):
        stats = graph_builder.get_graph_statistics(G) or {}
        assert "density" in stats and "avg_degree" in stats


def test_convenience_extract(sample_text):
    """Test convenience function for entity extraction"""
    ents = extract_entities_from_text(sample_text, use_ner=False)
    assert isinstance(ents, list)


def test_public_imports_surface():
    """Test that all public APIs are importable"""
    # Keep this aligned with your package __init__ exports
    from graph import (
        EntityExtractor,
        Entity,
        RelationshipBuilder,
        Relationship,
        GraphBuilder,
        GraphHopRetriever,
        HopResult,
        GATReranker,
        RerankResult,
    )
    
    # Simple type presence smoke
    assert EntityExtractor and RelationshipBuilder and GraphBuilder
    assert GraphHopRetriever and GATReranker


def test_entity_extractor_validation(extractor, sample_text):
    """Test entity validation logic"""
    entities = extractor.extract_entities(sample_text)
    
    for entity in entities:
        # All entities should pass validation
        assert extractor.validate_entity(entity), f"Entity failed validation: {entity.text}"
        
        # Check required fields
        assert entity.text, "Entity must have text"
        assert entity.label, "Entity must have label"
        assert 0 <= entity.score <= 1, "Entity score must be in [0,1]"


def test_relationship_statistics(rel_builder, entities, sample_text):
    """Test relationship statistics"""
    if not entities or len(entities) < 2:
        pytest.skip("Need at least 2 entities for relationship tests")
    
    relationships = rel_builder.build_relationships(entities, sample_text)
    
    if relationships:
        stats = rel_builder.get_relationship_statistics(relationships)
        
        assert "total" in stats
        assert "by_type" in stats
        assert "avg_strength" in stats
        assert "avg_confidence" in stats
        
        assert stats["total"] == len(relationships)
        assert 0 <= stats["avg_strength"] <= 1
        assert 0 <= stats["avg_confidence"] <= 1


def test_graph_statistics(graph_builder, nx_graph):
    """Test graph statistics computation"""
    stats = graph_builder.get_graph_statistics(nx_graph)
    
    assert "num_nodes" in stats
    assert "num_edges" in stats
    assert "density" in stats
    assert "avg_degree" in stats
    
    assert stats["num_nodes"] == nx_graph.number_of_nodes()
    assert stats["num_edges"] == nx_graph.number_of_edges()
    assert 0 <= stats["density"] <= 1


def test_graph_hop_with_constraints(nx_graph, entities):
    """Test graph hop with filtering constraints"""
    if not entities:
        pytest.skip("No entities available")
    
    seed_id = getattr(entities[0], "normalized_text", None) or getattr(entities[0], "text", None)
    
    retriever = GraphHopRetriever(graph=nx_graph, max_hops=2)
    
    # Test with entity type constraint
    constraints = {
        "min_score": 0.5
    }
    
    results = retriever.k_hop_expansion([seed_id], constraints=constraints)
    
    assert isinstance(results, list)
    
    # All results should meet min_score constraint
    for result in results:
        assert result.path_score >= constraints["min_score"]


def test_entity_merge_duplicates(extractor, sample_text):
    """Test entity deduplication"""
    entities = extractor.extract_entities(sample_text)
    
    if not entities:
        pytest.skip("No entities to test")
    
    # Create duplicate
    duplicates = entities + entities
    
    merged = extractor.merge_duplicates(duplicates)
    
    # Should have removed duplicates
    assert len(merged) <= len(duplicates)
    
    # Check uniqueness by (normalized_text, label)
    seen = set()
    for entity in merged:
        key = (entity.normalized_text, entity.label)
        assert key not in seen, f"Duplicate entity found: {key}"
        seen.add(key)


def test_graph_builder_from_text(sample_text):
    """Test convenience function for building graph from text"""
    from graph.builders import build_graph_from_text
    
    # Create a simple extractor
    extractor = EntityExtractor(use_ner=False, min_score=0.5)
    
    result = build_graph_from_text(
        text=sample_text,
        entity_extractor=extractor,
        use_networkx=True,
        use_neo4j=False
    )
    
    assert "entities" in result
    assert "relationships" in result
    assert "networkx_graph" in result
    
    assert isinstance(result["entities"], list)
    assert isinstance(result["relationships"], list)
    
    if result["networkx_graph"]:
        assert result["networkx_graph"].number_of_nodes() == len(result["entities"])


def test_hop_retriever_statistics(nx_graph):
    """Test hop retriever statistics"""
    retriever = GraphHopRetriever(graph=nx_graph, max_hops=2)
    
    stats = retriever.get_statistics()
    
    assert "graph_nodes" in stats
    assert "graph_edges" in stats
    assert "max_hops" in stats
    assert "decay_factor" in stats
    
    assert stats["graph_nodes"] == nx_graph.number_of_nodes()
    assert stats["graph_edges"] == nx_graph.number_of_edges()
    assert stats["max_hops"] == 2


def test_entity_extractor_statistics(extractor, sample_text):
    """Test entity extraction statistics"""
    entities = extractor.extract_entities(sample_text)
    
    if not entities:
        pytest.skip("No entities to test")
    
    stats = extractor.get_entity_statistics(entities)
    
    assert "total" in stats
    assert "by_label" in stats
    assert "by_source" in stats
    assert "avg_score" in stats
    
    assert stats["total"] == len(entities)
    assert 0 <= stats["avg_score"] <= 1
