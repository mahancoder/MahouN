"""
Unit Tests for Relationship Builder
===================================

Tests for the RelationshipBuilder class covering:
- Co-occurrence relationship building
- Semantic relationship detection
- Relationship strength calculation
- Deduplication and merging
- Accuracy requirements (>85% for semantic)
"""

import pytest
from graph.builders.relationship_builder import (
    RelationshipBuilder,
    Relationship,
    build_relationships_from_text,
)
from graph.builders.entity_extractor import Entity


class TestRelationship:
    """Test Relationship dataclass"""

    def test_relationship_creation(self):
        """Test creating a relationship"""
        source = Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95)
        target = Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9)

        rel = Relationship(
            source_entity=source,
            target_entity=target,
            rel_type="REFERENCES",
            strength=0.9,
            confidence=0.95,
        )

        assert rel.source_entity == source
        assert rel.target_entity == target
        assert rel.rel_type == "REFERENCES"
        assert rel.strength == 0.9
        assert rel.confidence == 0.95

    def test_relationship_validation(self):
        """Test relationship validation"""
        source = Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95)
        target = Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9)

        # Test strength clamping
        rel = Relationship(
            source_entity=source,
            target_entity=target,
            rel_type="REFERENCES",
            strength=1.5,  # Should be clamped to 1.0
            confidence=0.95,
        )
        assert rel.strength == 1.0

        # Test confidence clamping
        rel = Relationship(
            source_entity=source,
            target_entity=target,
            rel_type="REFERENCES",
            strength=0.9,
            confidence=-0.1,  # Should be clamped to 0.0
        )
        assert rel.confidence == 0.0

    def test_relationship_equality(self):
        """Test relationship equality for deduplication"""
        source = Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95)
        target = Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9)

        rel1 = Relationship(
            source_entity=source,
            target_entity=target,
            rel_type="REFERENCES",
            strength=0.9,
            confidence=0.95,
        )

        rel2 = Relationship(
            source_entity=source,
            target_entity=target,
            rel_type="REFERENCES",
            strength=0.8,  # Different strength
            confidence=0.9,  # Different confidence
        )

        # Should be equal (same source, target, type)
        assert rel1 == rel2


class TestRelationshipBuilder:
    """Test RelationshipBuilder class"""

    @pytest.fixture
    def builder(self):
        """Create builder instance"""
        return RelationshipBuilder(max_distance=200, min_co_occurrence=1)

    @pytest.fixture
    def sample_entities(self):
        """Create sample entities"""
        return [
            Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95),
            Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9),
            Entity(text="دادگاه", label="COURT", start=50, end=56, score=0.85),
            Entity(text="حکم", label="VERDICT", start=60, end=63, score=0.9),
        ]

    def test_builder_initialization(self, builder):
        """Test builder initialization"""
        assert builder.max_distance == 200
        assert builder.min_co_occurrence == 1
        assert builder.significant_threshold == 5

    def test_build_co_occurrence_relationships_simple(self, builder):
        """Test building co-occurrence relationships"""
        entities = [
            Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95),
            Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9),
        ]

        text = "ماده 10 قانون مدنی"

        relationships = builder.build_co_occurrence_relationships(entities, text)

        # Should create one CO_OCCURS relationship
        assert len(relationships) >= 1
        assert any(r.rel_type == "CO_OCCURS" for r in relationships)

    def test_build_co_occurrence_relationships_distance(self, builder):
        """Test co-occurrence respects distance threshold"""
        entities = [
            Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95),
            Entity(
                text="قانون مدنی", label="LAW_NAME", start=250, end=260, score=0.9
            ),  # Too far
        ]

        text = "ماده 10" + " " * 250 + "قانون مدنی"

        relationships = builder.build_co_occurrence_relationships(entities, text)

        # Should not create relationship (too far)
        assert len(relationships) == 0

    def test_build_semantic_relationships_cites(self, builder):
        """Test semantic CITES relationship detection"""
        entities = [
            Entity(text="حکم", label="VERDICT", start=0, end=3, score=0.9),
            Entity(text="ماده 10", label="ARTICLE", start=20, end=27, score=0.95),
        ]

        text = "حکم به استناد ماده 10 صادر شد"

        relationships = builder.build_semantic_relationships(entities, text)

        # Should detect CITES relationship
        cites_rels = [r for r in relationships if r.rel_type == "CITES"]
        assert len(cites_rels) > 0

    def test_build_semantic_relationships_references(self, builder):
        """Test semantic REFERENCES relationship detection"""
        entities = [
            Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95),
            Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9),
        ]

        text = "ماده 10 قانون مدنی"

        relationships = builder.build_semantic_relationships(entities, text)

        # Should detect REFERENCES relationship
        ref_rels = [r for r in relationships if r.rel_type == "REFERENCES"]
        assert len(ref_rels) > 0

    def test_build_semantic_relationships_overturns(self, builder):
        """Test semantic OVERTURNS relationship detection"""
        entities = [
            Entity(text="دادنامه 1", label="VERDICT", start=0, end=9, score=0.9),
            Entity(text="دادنامه 2", label="VERDICT", start=20, end=29, score=0.9),
        ]

        text = "دادنامه 1 نقض حکم دادنامه 2"

        relationships = builder.build_semantic_relationships(entities, text)

        # Should detect OVERTURNS relationship
        overturn_rels = [r for r in relationships if r.rel_type == "OVERTURNS"]
        assert len(overturn_rels) > 0

    def test_build_semantic_relationships_confirms(self, builder):
        """Test semantic CONFIRMS relationship detection"""
        entities = [
            Entity(text="دادنامه 1", label="VERDICT", start=0, end=9, score=0.9),
            Entity(text="دادنامه 2", label="VERDICT", start=20, end=29, score=0.9),
        ]

        text = "دادنامه 1 تایید حکم دادنامه 2"

        relationships = builder.build_semantic_relationships(entities, text)

        # Should detect CONFIRMS relationship
        confirm_rels = [r for r in relationships if r.rel_type == "CONFIRMS"]
        assert len(confirm_rels) > 0

    def test_calculate_co_occurrence_strength(self, builder):
        """Test co-occurrence strength calculation"""
        # Close distance -> high strength
        assert builder._calculate_co_occurrence_strength(30) == 1.0

        # Medium distance -> medium strength
        assert builder._calculate_co_occurrence_strength(75) == 0.8

        # Far distance -> low strength
        assert builder._calculate_co_occurrence_strength(175) == 0.4

    def test_calculate_semantic_confidence(self, builder):
        """Test semantic confidence calculation"""
        source = Entity(text="حکم", label="VERDICT", start=0, end=3, score=0.95)
        target = Entity(text="ماده 10", label="ARTICLE", start=20, end=27, score=0.9)

        confidence = builder._calculate_semantic_confidence(
            "CITES", "به استناد ماده 10", source, target
        )

        # Should have high confidence for VERDICT -> ARTICLE CITES
        assert confidence >= 0.85

    def test_deduplicate_relationships(self, builder):
        """Test relationship deduplication"""
        source = Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95)
        target = Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9)

        relationships = [
            Relationship(
                source_entity=source,
                target_entity=target,
                rel_type="REFERENCES",
                strength=0.9,
                confidence=0.95,
            ),
            Relationship(
                source_entity=source,
                target_entity=target,
                rel_type="REFERENCES",
                strength=0.8,
                confidence=0.9,
            ),
            Relationship(
                source_entity=source,
                target_entity=target,
                rel_type="REFERENCES",
                strength=0.85,
                confidence=0.92,
            ),
        ]

        unique = builder._deduplicate_relationships(relationships)

        # Should keep only one (highest confidence)
        assert len(unique) == 1
        assert unique[0].confidence == 0.95

    def test_merge_relationships_significant(self, builder):
        """Test marking significant relationships"""
        source = Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95)
        target = Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9)

        # Create 6 duplicate relationships (above threshold of 5)
        relationships = [
            Relationship(
                source_entity=source,
                target_entity=target,
                rel_type="CO_OCCURS",
                strength=0.9,
                confidence=0.9,
                properties={"co_occurrence_count": 1},
            )
            for _ in range(6)
        ]

        merged = builder.merge_relationships(relationships)

        # Should merge into one and mark as significant
        assert len(merged) == 1
        assert merged[0].properties.get("significant") == True
        assert merged[0].properties.get("co_occurrence_count") == 6

    def test_calculate_relationship_strength(self, builder):
        """Test relationship strength calculation"""
        source = Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95)
        target = Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9)

        text = "ماده 10 قانون مدنی"

        strength = builder.calculate_relationship_strength(source, target, text)

        # Should have high strength (close distance, high scores)
        assert strength >= 0.8

    def test_get_relationship_statistics(self, builder):
        """Test relationship statistics"""
        source = Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95)
        target = Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9)

        relationships = [
            Relationship(
                source_entity=source,
                target_entity=target,
                rel_type="REFERENCES",
                strength=0.9,
                confidence=0.95,
            ),
            Relationship(
                source_entity=source,
                target_entity=target,
                rel_type="CO_OCCURS",
                strength=0.8,
                confidence=0.9,
            ),
        ]

        stats = builder.get_relationship_statistics(relationships)

        assert stats["total"] == 2
        assert stats["by_type"]["REFERENCES"] == 1
        assert stats["by_type"]["CO_OCCURS"] == 1
        assert 0.8 <= stats["avg_strength"] <= 0.9
        assert 0.9 <= stats["avg_confidence"] <= 0.95

    def test_build_relationships_combined(self, builder, sample_entities):
        """Test building both co-occurrence and semantic relationships"""
        text = "ماده 10 قانون مدنی در دادگاه حکم صادر شد"

        relationships = builder.build_relationships(sample_entities, text)

        # Should have both types
        assert len(relationships) > 0
        rel_types = set(r.rel_type for r in relationships)
        assert "CO_OCCURS" in rel_types


class TestAccuracy:
    """Test accuracy requirements (>85% for semantic)"""

    @pytest.fixture
    def builder(self):
        """Create builder instance"""
        return RelationshipBuilder()

    def test_semantic_cites_accuracy(self, builder):
        """Test CITES detection accuracy"""
        test_cases = [
            (
                "حکم به استناد ماده 10 صادر شد",
                ["حکم", "ماده 10"],
                "CITES",
                True,
            ),
            (
                "مستند به ماده 20 قانون مدنی",
                ["مستند", "ماده 20"],
                "CITES",
                True,
            ),
            (
                "طبق ماده 30 تصمیم گرفته شد",
                ["طبق", "ماده 30"],
                "CITES",
                True,
            ),
            ("ماده 40 در قانون است", ["ماده 40", "قانون"], "CITES", False),
        ]

        total = 0
        correct = 0

        for text, entity_texts, expected_type, should_detect in test_cases:
            # Create entities
            entities = []
            for i, ent_text in enumerate(entity_texts):
                start = text.find(ent_text)
                end = start + len(ent_text)
                label = "VERDICT" if i == 0 else "ARTICLE"
                entities.append(
                    Entity(text=ent_text, label=label, start=start, end=end, score=0.9)
                )

            # Build relationships
            relationships = builder.build_semantic_relationships(entities, text)

            # Check if expected type was detected
            detected = any(r.rel_type == expected_type for r in relationships)

            total += 1
            if detected == should_detect:
                correct += 1

        accuracy = correct / total if total > 0 else 0

        # Should be > 85% accuracy
        assert (
            accuracy >= 0.85
        ), f"Semantic CITES accuracy {accuracy:.2%} is below 85%"

    def test_semantic_references_accuracy(self, builder):
        """Test REFERENCES detection accuracy"""
        test_cases = [
            ("ماده 10 قانون مدنی", ["ماده 10", "قانون مدنی"], "REFERENCES", True),
            ("تبصره 2 ماده 5", ["تبصره 2", "ماده 5"], "REFERENCES", True),
            ("بند الف ماده 20", ["بند الف", "ماده 20"], "REFERENCES", True),
        ]

        total = 0
        correct = 0

        for text, entity_texts, expected_type, should_detect in test_cases:
            entities = []
            for i, ent_text in enumerate(entity_texts):
                start = text.find(ent_text)
                end = start + len(ent_text)
                label = "ARTICLE" if i == 0 else "LAW_NAME"
                entities.append(
                    Entity(text=ent_text, label=label, start=start, end=end, score=0.9)
                )

            relationships = builder.build_semantic_relationships(entities, text)
            detected = any(r.rel_type == expected_type for r in relationships)

            total += 1
            if detected == should_detect:
                correct += 1

        accuracy = correct / total if total > 0 else 0
        assert (
            accuracy >= 0.85
        ), f"Semantic REFERENCES accuracy {accuracy:.2%} is below 85%"


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_build_relationships_from_text(self):
        """Test convenience function"""
        entities = [
            Entity(text="ماده 10", label="ARTICLE", start=0, end=7, score=0.95),
            Entity(text="قانون مدنی", label="LAW_NAME", start=10, end=20, score=0.9),
        ]

        text = "ماده 10 قانون مدنی"

        relationships = build_relationships_from_text(entities, text)

        assert isinstance(relationships, list)
        assert len(relationships) > 0
        assert all(isinstance(r, Relationship) for r in relationships)


class TestRealData:
    """Test with real legal document data"""

    @pytest.fixture
    def builder(self):
        """Create builder instance"""
        return RelationshipBuilder()

    def test_real_verdict_relationships(self, builder):
        """Test relationship building from real verdict text"""
        text = """
        رأی دادگاه بدوی در پرونده مطروحه به خواسته تنفیذ مبایعه‌نامه 
        و الزام خوانده به فک رهن برابر با دادنامه 0323 مورخ 1400/05/15
        به استناد ماده 348 قانون آیین دادرسی مدنی و ماده 353 قانون مذکور
        دادگاه محترم تجدید نظر برابر با دادنامه 1116 تایید حکم نمود.
        """

        # Create sample entities
        entities = [
            Entity(text="دادگاه بدوی", label="COURT", start=5, end=16, score=0.9),
            Entity(text="خوانده", label="PARTY", start=70, end=76, score=0.85),
            Entity(text="دادنامه 0323", label="VERDICT", start=110, end=122, score=0.9),
            Entity(text="ماده 348", label="ARTICLE", start=160, end=168, score=0.95),
            Entity(
                text="قانون آیین دادرسی مدنی",
                label="LAW_NAME",
                start=170,
                end=192,
                score=0.9,
            ),
            Entity(text="ماده 353", label="ARTICLE", start=195, end=203, score=0.95),
            Entity(text="دادنامه 1116", label="VERDICT", start=250, end=262, score=0.9),
        ]

        relationships = builder.build_relationships(entities, text)

        # Should build multiple relationships
        assert len(relationships) > 0

        # Should have different types
        rel_types = set(r.rel_type for r in relationships)
        assert len(rel_types) > 1

        # Should detect semantic relationships
        semantic_types = {"CITES", "REFERENCES", "CONFIRMS"}
        assert any(rt in semantic_types for rt in rel_types)
