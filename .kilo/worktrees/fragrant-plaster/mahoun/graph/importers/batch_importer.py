"""
Batch Importer for Legal Knowledge Graph
========================================

This module handles batch import of multiple documents with parallel processing.
"""

import logging
import time
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from graph.neo4j.connection import Neo4jConnection
from graph.importers.document_importer import DocumentImporter

logger = logging.getLogger(__name__)


@dataclass
class BatchImportResult:
    """Result of batch import operation"""

    total_documents: int
    successful: int
    failed: int
    total_entities: int
    total_relationships: int
    duration_seconds: float
    errors: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total_documents": self.total_documents,
            "successful": self.successful,
            "failed": self.failed,
            "total_entities": self.total_entities,
            "total_relationships": self.total_relationships,
            "duration_seconds": self.duration_seconds,
            "success_rate": (
                self.successful / self.total_documents if self.total_documents > 0 else 0
            ),
            "errors": self.errors,
        }


class BatchImporter:
    """
    Batch Importer
    
    Handles batch import of multiple documents with:
    - Parallel processing using ThreadPoolExecutor
    - Progress tracking and logging
    - Error handling for individual documents
    - Statistics aggregation
    """

    def __init__(
        self,
        connection: Neo4jConnection,
        max_workers: int = 4,
        batch_size: int = 100,
    ):
        """
        Initialize BatchImporter
        
        Args:
            connection: Neo4j connection instance
            max_workers: Maximum number of parallel workers
            batch_size: Number of documents per batch
        """
        self.connection = connection
        self.max_workers = max_workers
        self.batch_size = batch_size

        logger.info(
            f"BatchImporter initialized (max_workers={max_workers}, batch_size={batch_size})"
        )

    def import_batch(
        self,
        documents: List[Dict],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchImportResult:
        """
        Import a batch of documents
        
        Args:
            documents: List of document dictionaries with 'id', 'text', 'metadata'
            progress_callback: Optional callback function(current, total)
        
        Returns:
            BatchImportResult with statistics
        """
        start_time = time.time()

        total_documents = len(documents)
        successful = 0
        failed = 0
        total_entities = 0
        total_relationships = 0
        errors = []

        logger.info(f"Starting batch import of {total_documents} documents")

        # Process in batches
        for batch_start in range(0, total_documents, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_documents)
            batch = documents[batch_start:batch_end]

            logger.info(
                f"Processing batch {batch_start//self.batch_size + 1}: "
                f"documents {batch_start+1}-{batch_end}"
            )

            # Process batch with parallel workers
            batch_results = self._process_batch_parallel(batch)

            # Aggregate results
            for result in batch_results:
                if result["success"]:
                    successful += 1
                    total_entities += result.get("entity_count", 0)
                    total_relationships += result.get("relationship_count", 0)
                else:
                    failed += 1
                    errors.append(
                        {
                            "document_id": result["document_id"],
                            "error": result.get("error", "Unknown error"),
                        }
                    )

            # Progress callback
            if progress_callback:
                progress_callback(batch_end, total_documents)

        duration = time.time() - start_time

        result = BatchImportResult(
            total_documents=total_documents,
            successful=successful,
            failed=failed,
            total_entities=total_entities,
            total_relationships=total_relationships,
            duration_seconds=duration,
            errors=errors,
        )

        logger.info(
            f"Batch import completed: {successful}/{total_documents} successful "
            f"({failed} failed) in {duration:.2f}s"
        )

        return result

    def _process_batch_parallel(self, batch: List[Dict]) -> List[Dict]:
        """
        Process a batch of documents in parallel
        
        Args:
            batch: List of documents
        
        Returns:
            List of result dictionaries
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all documents
            future_to_doc = {
                executor.submit(self._import_single_document, doc): doc
                for doc in batch
            }

            # Collect results as they complete
            for future in as_completed(future_to_doc):
                doc = future_to_doc[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to import document {doc.get('id')}: {e}")
                    results.append(
                        {
                            "document_id": doc.get("id"),
                            "success": False,
                            "error": str(e),
                        }
                    )

        return results

    def _import_single_document(self, document: Dict) -> Dict:
        """
        Import a single document
        
        Args:
            document: Document dictionary with 'id', 'text', 'metadata'
        
        Returns:
            Result dictionary
        """
        try:
            document_id = document.get("id")
            text = document.get("text", "")
            metadata = document.get("metadata", {})

            if not document_id or not text:
                return {
                    "document_id": document_id,
                    "success": False,
                    "error": "Missing document_id or text",
                }

            # Create document importer for this thread
            importer = DocumentImporter(self.connection)

            # Import document
            stats = importer.import_document(document_id, text, metadata)

            return {
                "document_id": document_id,
                "success": True,
                "entity_count": stats.get("entity_count", 0),
                "relationship_count": stats.get("relationship_count", 0),
            }

        except Exception as e:
            logger.error(f"Error importing document {document.get('id')}: {e}")
            return {
                "document_id": document.get("id"),
                "success": False,
                "error": str(e),
            }

    def import_from_jsonl(
        self,
        file_path: str,
        max_documents: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchImportResult:
        """
        Import documents from JSONL file
        
        Args:
            file_path: Path to JSONL file
            max_documents: Maximum number of documents to import (None = all)
            progress_callback: Optional callback function(current, total)
        
        Returns:
            BatchImportResult with statistics
        """
        import json

        documents = []

        logger.info(f"Loading documents from {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if max_documents and i >= max_documents:
                    break

                try:
                    doc = json.loads(line)
                    documents.append(doc)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {i+1}: {e}")

        logger.info(f"Loaded {len(documents)} documents from {file_path}")

        return self.import_batch(documents, progress_callback)

    def get_import_statistics(self) -> Dict:
        """
        Get overall import statistics from graph
        
        Returns:
            Dictionary with statistics
        """
        query = """
        MATCH (n)
        WITH labels(n)[0] as label, count(n) as count
        RETURN label, count
        ORDER BY count DESC
        """

        result = self.connection.execute_query(query)

        stats = {"nodes_by_type": {}, "total_nodes": 0}

        for row in result:
            label = row["label"]
            count = row["count"]
            stats["nodes_by_type"][label] = count
            stats["total_nodes"] += count

        # Get relationship counts
        rel_query = """
        MATCH ()-[r]->()
        WITH type(r) as rel_type, count(r) as count
        RETURN rel_type, count
        ORDER BY count DESC
        """

        rel_result = self.connection.execute_query(rel_query)

        stats["relationships_by_type"] = {}
        stats["total_relationships"] = 0

        for row in rel_result:
            rel_type = row["rel_type"]
            count = row["count"]
            stats["relationships_by_type"][rel_type] = count
            stats["total_relationships"] += count

        return stats


# Convenience function
def import_documents_batch(
    connection: Neo4jConnection,
    documents: List[Dict],
    max_workers: int = 4,
    batch_size: int = 100,
) -> BatchImportResult:
    """
    Convenience function to import documents in batch
    
    Args:
        connection: Neo4j connection
        documents: List of documents
        max_workers: Maximum parallel workers
        batch_size: Batch size
    
    Returns:
        BatchImportResult
    """
    importer = BatchImporter(connection, max_workers, batch_size)
    return importer.import_batch(documents)
