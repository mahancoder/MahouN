"""
Unit Tests for RelationshipBuilder
==================================

Tests for relationship building functionality including:
- Co-occurrence relationships
- Semantic relationships
- Relationship strength calculation
- Batch operations
"""

import pytest
from graph.builders.entity_extractor import Entity
from graph.builders.relationship_builder import (
    RelationshipBuilder,
    Relationship,
    build_relationships
)


class TestRelationshipBuilder:
    """Test RelationshipBuilder class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.builder = RelationshipBuilder(max_distance=200)
        
        # Sample entities
        self.entities = [
            Entity(
                text="ماده 10",
                label="ARTICLE",
                start=50,
                end=57,
                score=0.95,
                source="regex"
            ),
            Entity(
                text="قانون مدنی",
                label="LAW_NAME",
                start=58,
                end=68,
                score=0.9,
                source="nlp"
            ),
            Entity(
                text="دادگاه تجدیدنظر",
                label="COURT",
                start=100,
                end=116,
                score=0.85,
                source="ner"
            ),
            Entity(
                text="دادنامه شماره 123",
                label="VERDICT",
                start=150,
                end=168,
                score=0.9,
                source="regex"
            )
        ]
        
        # Sample text
        self.text = (
            "در این پرونده، به استناد ماده 10 قانون مدنی، "
            "دادگاه تجدیدنظر رسیدگی کرد و دادنامه شماره 123 را صادر نمود."
        )
    
    def test_initialization(self):
        """Test RelationshipBuilder initialization"""
        builder = RelationshipBuilder(max_distance=300, min_co_occurrence=2)
        assert builder.max_distance == 300
        assert builder.min_co_occurrence == 2
        assert builder.significant_threshold == 5
    
    def test_build_co_occurrence_relationships(self):
        """Test co-occurrence relationship building"""
        relationships = self.builder.build_co_occurrence_relationships(
            self.entities,
            self.text
        )
        
        # Should find relationships between nearby entities
        assert len(relationships) > 0
        
        # Check relationship properties
        for rel in relationships:
            assert rel.rel_type == 'CO_OCCURS'
            assert 0 <= rel.strength <= 1
            assert 0 <= rel.confidence <= 1
            assert 'co_occurrence_count' in rel.metadata
            assert 'avg_distance' in rel.metadata
    
    def test_co_occurrence_distance_threshold(self):
        """Test that co-occurrence respects distance threshold"""
        # Create entities far apart
        far_entities = [
            Entity("entity1", "ARTICLE", 0, 10, 0.9, "test"),
            Entity("entity2", "LAW_NAME", 500, 510, 0.9, "test")
        ]
        
        text = "x" * 600
        
        relationships = self.builder.build_co_occurrence_relationships(
            far_entities,
            text
        )
        
        # Should not find relationships (too far apart)
        assert len(relationships) == 0
    
    def test_build_semantic_relationships_cites(self):
        """Test CITES relationship extraction"""
        text = "به استناد ماده 10 قانون مدنی، حکم صادر شد."
        
        entities = [
            Entity("ماده 10", "ARTICLE", 11, 17, 0.95, "regex"),
            Entity("قانون مدنی", "LAW_NAME", 18, 28, 0.9, "nlp"),
            Entity("حکم", "VERDICT", 30, 33, 0.85, "nlp")
        ]
        
        relationships = self.builder.build_semantic_relationships(text, entities)
        
        # Should find CITES relationship
        cites_rels = [r for r in relationships if r.rel_type == 'CITES']
        assert len(cites_rels) > 0
        
        # Check properties
        for rel in cites_rels:
            assert rel.confidence >= 0.9
            assert 'citation_text' in rel.metadata
    
    def test_build_semantic_relationships_references(self):
        """Test REFERENCES relationship extraction"""
        text = "مطابق ماده 20 قانون آیین دادرسی مدنی"
        
        entities = [
            Entity("ماده 20", "ARTICLE", 7, 13, 0.95, "regex"),
            Entity("قانون آیین دادرسی مدنی", "LAW_NAME", 14, 38, 0.9, "nlp")
        ]
        
        relationships = self.builder.build_semantic_relationships(text, entities)
        
        # Should find REFERENCES relationship
        ref_rels = [r for r in relationships if r.rel_type == 'REFERENCES']
        assert len(ref_rels) > 0
    
    def test_build_semantic_relationships_issued_by(self):
        """Test ISSUED_BY relationship extraction"""
        text = "دادنامه شماره 123 صادر شده توسط دادگاه تجدیدنظر"
        
        entities = [
            Entity("دادنامه شماره 123", "VERDICT", 0, 17, 0.9, "regex"),
            Entity("دادگاه تجدیدنظر", "COURT", 33, 49, 0.85, "ner")
        ]
        
        relationships = self.builder.build_semantic_relationships(text, entities)
        
        # Should find ISSUED_BY relationship
        issued_rels = [r for r in relationships if r.rel_type == 'ISSUED_BY']
        assert len(issued_rels) > 0
    
    def test_build_semantic_relationships_overturns(self):
        """Test OVERTURNS relationship extraction"""
        text = "دادگاه عالی نقض حکم بدوی را اعلام کرد"
        
        entities = [
            Entity("دادگاه عالی", "COURT", 0, 11, 0.85, "ner"),
            Entity("حکم بدوی", "VERDICT", 17, 26, 0.9, "nlp")
        ]
        
        relationships = self.builder.build_semantic_relationships(text, entities)
        
        # Should find OVERTURNS relationship
        overturn_rels = [r for r in relationships if r.rel_type == 'OVERTURNS']
        assert len(overturn_rels) > 0
    
    def test_build_semantic_relationships_confirms(self):
        """Test CONFIRMS relationship extraction"""
        text = "دادگاه تجدیدنظر تایید حکم بدوی نمود"
        
        entities = [
            Entity("دادگاه تجدیدنظر", "COURT", 0, 16, 0.85, "ner"),
            Entity("حکم بدوی", "VERDICT", 23, 32, 0.9, "nlp")
        ]
        
        relationships = self.builder.build_semantic_relationships(text, entities)
        
        # Should find CONFIRMS relationship
        confirm_rels = [r for r in relationships if r.rel_type == 'CONFIRMS']
        assert len(confirm_rels) > 0
    
    def test_calculate_relationship_strength(self):
        """Test relationship strength calculation"""
        entity1 = Entity("test1", "ARTICLE", 0, 5, 0.9, "test")
        entity2 = Entity("test2", "LAW_NAME", 10, 15, 0.8, "test")
        
        # Test with different parameters
        strength1 = self.builder.calculate_relationship_strength(
            entity1, entity2, co_occurrence_count=5, avg_distance=50
        )
        
        strength2 = self.builder.calculate_relationship_strength(
            entity1, entity2, co_occurrence_count=10, avg_distance=50
        )
        
        strength3 = self.builder.calculate_relationship_strength(
            entity1, entity2, co_occurrence_count=5, avg_distance=150
        )
        
        # More co-occurrences = higher strength
        assert strength2 > strength1
        
        # Closer distance = higher strength
        assert strength1 > strength3
        
        # All strengths should be in [0, 1]
        assert 0 <= strength1 <= 1
        assert 0 <= strength2 <= 1
        assert 0 <= strength3 <= 1
    
    def test_merge_relationships(self):
        """Test relationship merging"""
        entity1 = Entity("ماده 10", "ARTICLE", 0, 7, 0.9, "test")
        entity2 = Entity("قانون", "LAW_NAME", 10, 15, 0.8, "test")
        
        # Create duplicate relationships
        rel1 = Relationship(
            entity1, entity2, "CITES",
            strength=0.8, confidence=0.9, context="context1"
        )
        rel2 = Relationship(
            entity1, entity2, "CITES",
            strength=0.7, confidence=0.85, context="context2"
        )
        rel3 = Relationship(
            entity1, entity2, "REFERENCES",
            strength=0.6, confidence=0.8, context="context3"
        )
        
        relationships = [rel1, rel2, rel3]
        merged = self.builder.merge_relationships(relationships)
        
        # Should merge duplicates (rel1 and rel2)
        assert len(merged) == 2
        
        # Should keep highest confidence
        cites_rel = next(r for r in merged if r.rel_type == 'CITES')
        assert cites_rel.confidence == 0.9
    
    def test_filter_significant_relationships(self):
        """Test filtering for significant relationships"""
        entity1 = Entity("test1", "ARTICLE", 0, 5, 0.9, "test")
        entity2 = Entity("test2", "LAW_NAME", 10, 15, 0.8, "test")
        
        # Create relationships with different significance
        rel1 = Relationship(
            entity1, entity2, "CO_OCCURS",
            strength=0.5, confidence=0.7,
            metadata={'co_occurrence_count': 3}
        )
        rel2 = Relationship(
            entity1, entity2, "CO_OCCURS",
            strength=0.8, confidence=0.9,
            metadata={'co_occurrence_count': 10}
        )
        rel3 = Relationship(
            entity1, entity2, "CITES",
            strength=0.9, confidence=0.95
        )
        
        relationships = [rel1, rel2, rel3]
        significant = self.builder.filter_significant_relationships(relationships)
        
        # Should filter out rel1 (low count and confidence)
        # Should keep rel2 (high count) and rel3 (semantic)
        assert len(significant) >= 2
        assert rel3 in significant  # Semantic always significant
    
    def test_build_all_relationships(self):
        """Test building all relationships"""
        relationships = self.builder.build_all_relationships(
            self.entities,
            self.text
        )
        
        # Should find both co-occurrence and semantic relationships
        assert len(relationships) > 0
        
        # Check for different relationship types
        rel_types = {r.rel_type for r in relationships}
        assert len(rel_types) > 0
    
    def test_empty_entities(self):
        """Test with empty entity list"""
        relationships = self.builder.build_co_occurrence_relationships([], "text")
        assert len(relationships) == 0
    
    def test_single_entity(self):
        """Test with single entity"""
        single_entity = [self.entities[0]]
        relationships = self.builder.build_co_occurrence_relationships(
            single_entity,
            self.text
        )
        assert len(relationships) == 0
    
    def test_relationship_is_significant(self):
        """Test is_significant method"""
        entity1 = Entity("test1", "ARTICLE", 0, 5, 0.9, "test")
        entity2 = Entity("test2", "LAW_NAME", 10, 15, 0.8, "test")
        
        # Low count
        rel1 = Relationship(
            entity1, entity2, "CO_OCCURS",
            metadata={'co_occurrence_count': 3}
        )
        assert not rel1.is_significant()
        
        # High count
        rel2 = Relationship(
            entity1, entity2, "CO_OCCURS",
            metadata={'co_occurrence_count': 10}
        )
        assert rel2.is_significant()
    
    def test_semantic_accuracy(self):
        """Test semantic relationship extraction accuracy"""
        # Test text with multiple semantic patterns
        test_cases = [
            ("به استناد ماده 10", "CITES"),
            ("مطابق ماده 20 قانون", "REFERENCES"),
            ("صادر شده توسط دادگاه", "ISSUED_BY"),
            ("نقض حکم بدوی", "OVERTURNS"),
            ("تایید دادنامه", "CONFIRMS")
        ]
        
        total_found = 0
        total_expected = len(test_cases)
        
        for text_pattern, expected_type in test_cases:
            # Create appropriate entities
            entities = [
                Entity("ماده", "ARTICLE", 0, 4, 0.9, "test"),
                Entity("قانون", "LAW_NAME", 10, 15, 0.9, "test"),
                Entity("دادگاه", "COURT", 20, 26, 0.9, "test"),
                Entity("حکم", "VERDICT", 30, 33, 0.9, "test"),
                Entity("دادنامه", "VERDICT", 40, 47, 0.9, "test")
            ]
            
            relationships = self.builder.build_semantic_relationships(
                text_pattern,
                entities
            )
            
            # Check if expected type was found
            found_types = {r.rel_type for r in relationships}
            if expected_type in found_types:
                total_found += 1
        
        # Calculate accuracy
        accuracy = total_found / total_expected
        
        # Should achieve >85% accuracy as per requirements
        assert accuracy >= 0.85, f"Semantic accuracy {accuracy:.2%} < 85%"


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_build_relationships(self):
        """Test build_relationships convenience function"""
        entities = [
            Entity("ماده 10", "ARTICLE", 0, 7, 0.95, "regex"),
            Entity("قانون مدنی", "LAW_NAME", 8, 18, 0.9, "nlp")
        ]
        
        text = "ماده 10 قانون مدنی"
        
        relationships = build_relationships(entities, text)
        
        assert len(relationships) > 0
        assert all(isinstance(r, Relationship) for r in relationships)


class TestRelationshipDataClass:
    """Test Relationship data class"""
    
    def test_relationship_creation(self):
        """Test creating a Relationship"""
        entity1 = Entity("test1", "ARTICLE", 0, 5, 0.9, "test")
        entity2 = Entity("test2", "LAW_NAME", 10, 15, 0.8, "test")
        
        rel = Relationship(
            from_entity=entity1,
            to_entity=entity2,
            rel_type="CITES",
            strength=0.8,
            confidence=0.9,
            context="test context"
        )
        
        assert rel.from_entity == entity1
        assert rel.to_entity == entity2
        assert rel.rel_type == "CITES"
        assert rel.strength == 0.8
        assert rel.confidence == 0.9
    
    def test_relationship_to_dict(self):
        """Test converting Relationship to dict"""
        entity1 = Entity("test1", "ARTICLE", 0, 5, 0.9, "test")
        entity2 = Entity("test2", "LAW_NAME", 10, 15, 0.8, "test")
        
        rel = Relationship(entity1, entity2, "CITES")
        rel_dict = rel.to_dict()
        
        assert 'from_entity' in rel_dict
        assert 'to_entity' in rel_dict
        assert 'rel_type' in rel_dict
        assert rel_dict['rel_type'] == 'CITES'
    
    def test_relationship_strength_clamping(self):
        """Test that strength is clamped to [0, 1]"""
        entity1 = Entity("test1", "ARTICLE", 0, 5, 0.9, "test")
        entity2 = Entity("test2", "LAW_NAME", 10, 15, 0.8, "test")
        
        # Test values outside [0, 1]
        rel1 = Relationship(entity1, entity2, "CITES", strength=1.5)
        assert rel1.strength == 1.0
        
        rel2 = Relationship(entity1, entity2, "CITES", strength=-0.5)
        assert rel2.strength == 0.0
    
    def test_relationship_equality(self):
        """Test Relationship equality"""
        entity1 = Entity("test1", "ARTICLE", 0, 5, 0.9, "test")
        entity2 = Entity("test2", "LAW_NAME", 10, 15, 0.8, "test")
        
        rel1 = Relationship(entity1, entity2, "CITES")
        rel2 = Relationship(entity1, entity2, "CITES")
        rel3 = Relationship(entity1, entity2, "REFERENCES")
        
        assert rel1 == rel2
        assert rel1 != rel3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
