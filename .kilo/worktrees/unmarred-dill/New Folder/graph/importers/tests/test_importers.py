"""
Integration Tests for Graph Importers
=====================================

Tests for LawImporter, DocumentImporter, and BatchImporter.
"""

import pytest
from unittest.mock import Mock, MagicMock

from graph.importers.law_importer import LawImporter
from graph.importers.document_importer import DocumentImporter
from graph.importers.batch_importer import BatchImporter, BatchImportResult


class TestLawImporter:
    """Test LawImporter class"""

    @pytest.fixture
    def mock_connection(self):
        """Create mock Neo4j connection"""
        connection = Mock()
        connection.execute_query = MagicMock(return_value=[{"id": "test_id"}])
        return connection

    @pytest.fixture
    def importer(self, mock_connection):
        """Create LawImporter instance"""
        return LawImporter(mock_connection)

    def test_importer_initialization(self, importer):
        """Test importer initialization"""
        assert importer is not None
        assert importer.connection is not None

    def test_import_law_simple(self, importer, mock_connection):
        """Test importing a simple law"""
        articles = [
            {"number": 1, "content": "ماده اول"},
            {"number": 2, "content": "ماده دوم"},
        ]

        law_id = importer.import_law(
            name="قانون تست",
            full_name="قانون تست مصوب 1400",
            year=1400,
            category="مدنی",
            articles=articles,
        )

        # Should generate law ID
        assert law_id is not None
        assert "law_" in law_id

        # Should call execute_query multiple times
        assert mock_connection.execute_query.call_count > 0

    def test_import_law_with_notes(self, importer, mock_connection):
        """Test importing law with notes"""
        articles = [
            {
                "number": 1,
                "content": "ماده اول",
                "has_note": True,
                "notes": [{"number": 1, "content": "تبصره اول"}],
            }
        ]

        law_id = importer.import_law(
            name="قانون تست",
            full_name="قانون تست",
            year=1400,
            category="مدنی",
            articles=articles,
        )

        assert law_id is not None

    def test_import_law_with_clauses(self, importer, mock_connection):
        """Test importing law with clauses"""
        articles = [
            {
                "number": 1,
                "content": "ماده اول",
                "has_clause": True,
                "clauses": [{"number": 1, "content": "بند اول"}],
            }
        ]

        law_id = importer.import_law(
            name="قانون تست",
            full_name="قانون تست",
            year=1400,
            category="مدنی",
            articles=articles,
        )

        assert law_id is not None

    def test_generate_law_id(self, importer):
        """Test law ID generation"""
        law_id = importer._generate_law_id("قانون مدنی", 1307)
        assert "law_" in law_id
        assert "1307" in law_id

    def test_get_law_statistics(self, importer, mock_connection):
        """Test getting law statistics"""
        mock_connection.execute_query.return_value = [
            {
                "name": "قانون تست",
                "year": 1400,
                "article_count": 10,
                "note_count": 5,
                "clause_count": 3,
            }
        ]

        stats = importer.get_law_statistics("law_test_1400")

        assert stats["name"] == "قانون تست"
        assert stats["article_count"] == 10


class TestDocumentImporter:
    """Test DocumentImporter class"""

    @pytest.fixture
    def mock_connection(self):
        """Create mock Neo4j connection"""
        connection = Mock()
        connection.execute_query = MagicMock(return_value=[{"id": "test_id"}])
        return connection

    @pytest.fixture
    def importer(self, mock_connection):
        """Create DocumentImporter instance"""
        return DocumentImporter(mock_connection)

    def test_importer_initialization(self, importer):
        """Test importer initialization"""
        assert importer is not None
        assert importer.entity_extractor is not None
        assert importer.relationship_builder is not None

    def test_import_document_simple(self, importer, mock_connection):
        """Test importing a simple document"""
        text = "حکم دادگاه به استناد ماده 10 قانون مدنی صادر شد"

        stats = importer.import_document(
            document_id="doc_001", text=text, create_relationships=True
        )

        # Should extract entities
        assert stats["entity_count"] >= 0
        assert "entities_by_type" in stats

    def test_import_document_no_relationships(self, importer, mock_connection):
        """Test importing document without relationships"""
        text = "حکم دادگاه صادر شد"

        stats = importer.import_document(
            document_id="doc_002", text=text, create_relationships=False
        )

        # Should not create relationships
        assert stats["relationship_count"] == 0

    def test_map_entity_to_node_label(self, importer):
        """Test entity to node label mapping"""
        assert importer._map_entity_to_node_label("COURT") == "Court"
        assert importer._map_entity_to_node_label("VERDICT") == "Verdict"
        assert importer._map_entity_to_node_label("ARTICLE") == "Article"
        assert importer._map_entity_to_node_label("UNKNOWN") is None

    def test_generate_entity_node_id(self, importer):
        """Test entity node ID generation"""
        from graph.builders.entity_extractor import Entity

        entity = Entity(
            text="دادگاه", label="COURT", start=0, end=6, score=0.9
        )

        node_id = importer._generate_entity_node_id(entity)

        assert "court_" in node_id
        assert len(node_id) > 10  # Should have hash


class TestBatchImporter:
    """Test BatchImporter class"""

    @pytest.fixture
    def mock_connection(self):
        """Create mock Neo4j connection"""
        connection = Mock()
        connection.execute_query = MagicMock(return_value=[])
        return connection

    @pytest.fixture
    def importer(self, mock_connection):
        """Create BatchImporter instance"""
        return BatchImporter(mock_connection, max_workers=2, batch_size=10)

    def test_importer_initialization(self, importer):
        """Test importer initialization"""
        assert importer is not None
        assert importer.max_workers == 2
        assert importer.batch_size == 10

    def test_import_batch_empty(self, importer):
        """Test importing empty batch"""
        result = importer.import_batch([])

        assert result.total_documents == 0
        assert result.successful == 0
        assert result.failed == 0

    def test_import_batch_single_document(self, importer):
        """Test importing single document"""
        documents = [
            {"id": "doc_001", "text": "حکم دادگاه صادر شد", "metadata": {}}
        ]

        result = importer.import_batch(documents)

        assert result.total_documents == 1
        # May succeed or fail depending on mock setup
        assert result.successful + result.failed == 1

    def test_import_batch_multiple_documents(self, importer):
        """Test importing multiple documents"""
        documents = [
            {"id": f"doc_{i:03d}", "text": f"متن سند {i}", "metadata": {}}
            for i in range(5)
        ]

        result = importer.import_batch(documents)

        assert result.total_documents == 5
        assert result.successful + result.failed == 5

    def test_batch_import_result_to_dict(self):
        """Test BatchImportResult to_dict"""
        result = BatchImportResult(
            total_documents=10,
            successful=8,
            failed=2,
            total_entities=100,
            total_relationships=50,
            duration_seconds=5.5,
        )

        result_dict = result.to_dict()

        assert result_dict["total_documents"] == 10
        assert result_dict["successful"] == 8
        assert result_dict["failed"] == 2
        assert result_dict["success_rate"] == 0.8

    def test_import_batch_with_progress_callback(self, importer):
        """Test batch import with progress callback"""
        documents = [
            {"id": f"doc_{i:03d}", "text": f"متن سند {i}", "metadata": {}}
            for i in range(3)
        ]

        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        result = importer.import_batch(documents, progress_callback)

        # Should have called progress callback
        assert len(progress_calls) > 0


class TestIntegration:
    """Integration tests (require actual Neo4j connection)"""

    @pytest.mark.skip(reason="Requires Neo4j connection")
    def test_end_to_end_law_import(self):
        """Test end-to-end law import"""
        from graph.neo4j.connection import Neo4jConnection

        connection = Neo4jConnection(
            uri="bolt://localhost:7687", user="neo4j", password="password"
        )

        importer = LawImporter(connection)

        articles = [
            {"number": 1, "content": "ماده اول قانون تست"},
            {"number": 2, "content": "ماده دوم قانون تست"},
        ]

        law_id = importer.import_law(
            name="قانون تست",
            full_name="قانون تست مصوب 1400",
            year=1400,
            category="مدنی",
            articles=articles,
        )

        # Verify import
        stats = importer.get_law_statistics(law_id)
        assert stats["article_count"] == 2

        # Cleanup
        importer.delete_law(law_id)

    @pytest.mark.skip(reason="Requires Neo4j connection")
    def test_end_to_end_document_import(self):
        """Test end-to-end document import"""
        from graph.neo4j.connection import Neo4jConnection

        connection = Neo4jConnection(
            uri="bolt://localhost:7687", user="neo4j", password="password"
        )

        importer = DocumentImporter(connection)

        text = """
        رأی دادگاه بدوی در پرونده مطروحه به خواسته تنفیذ مبایعه‌نامه
        به استناد ماده 348 قانون آیین دادرسی مدنی حکم صادر شد.
        """

        stats = importer.import_document("doc_test_001", text)

        assert stats["entity_count"] > 0
        assert stats["relationship_count"] > 0
