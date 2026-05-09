"""
Doc-Parser Agent (HAJIX Refactored)
====================================

Agent for document parsing and text extraction.

Dependencies:
    - DocumentNormalizer: Text normalization
    - MetadataExtractor: Metadata extraction
    - IngestionPipeline: Document processing
"""

from typing import Any, Dict, Optional
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DocParserAgent(BaseAgent):
    """
    Document parsing and analysis agent.
    
    Integrates with existing components:
        - Document Normalizer for JSON standardization
        - Metadata Extractor for field extraction
        - IngestionPipeline for processing and indexing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize agent with optional configuration."""
        super().__init__("doc_parser_agent", config)
        self.normalizer = None
        self.metadata_extractor = None
        self.ingestion_pipeline = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize dependencies from existing components."""
        if self._initialized:
            return
        
        try:
            from mahoun.pipelines.ingestion.document_normalizer import DocumentNormalizer
            from mahoun.pipelines.ingestion.metadata_extractor import MetadataExtractor
            from mahoun.pipelines.ingestion import IngestionPipeline
            
            self.normalizer = DocumentNormalizer()
            self.metadata_extractor = MetadataExtractor()
            self.ingestion_pipeline = IngestionPipeline()
            await self.ingestion_pipeline.initialize()
            
            self._initialized = True
            self.logger.info("DocParserAgent initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}", exc_info=True)
            raise
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and process a document.
        
        Args:
            input_data: Dictionary containing:
                - text: Document text (or file_path for file)
                - doc_type: Document type (optional)
                - metadata: Additional metadata (optional)
                - index: Whether to index (default: True)
        
        Returns:
            Result with document_id, normalized content, metadata, and index status
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            text = input_data.get("text")
            file_path = input_data.get("file_path")
            doc_type = input_data.get("doc_type")
            metadata = input_data.get("metadata", {})
            should_index = input_data.get("index", True)
            
            # Normalize document
            if file_path:
                normalized = await self.normalizer.normalize_file(
                    file_path=file_path,
                    doc_type=doc_type,
                    metadata=metadata
                )
            elif text:
                normalized = await self.normalizer.normalize_text(
                    text=text,
                    doc_type=doc_type or "document",
                    metadata=metadata
                )
            else:
                return await self.handle_error(
                    ValueError("Either 'text' or 'file_path' must be provided"),
                    input_data
                )
            
            # Extract additional metadata
            extracted_metadata = await self.metadata_extractor.extract(
                text=normalized.content["text"],
                doc_type=normalized.type
            )
            
            final_metadata = {**normalized.metadata, **extracted_metadata}
            
            # Index if requested
            indexed = False
            if should_index:
                result = await self.ingestion_pipeline.ingest_document(
                    doc_id=normalized.document_id,
                    text=normalized.content["text"],
                    metadata=final_metadata
                )
                indexed = result.success
            
            return {
                "success": True,
                "document_id": normalized.document_id,
                "normalized": self.normalizer.to_dict(normalized),
                "metadata": final_metadata,
                "indexed": indexed,
                "processing_info": normalized.processing_info
            }
            
        except Exception as e:
            return await self.handle_error(e, input_data)
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status including component availability."""
        status = super().get_status()
        status.update({
            "initialized": self._initialized,
            "normalizer_available": self.normalizer is not None,
            "metadata_extractor_available": self.metadata_extractor is not None,
            "ingestion_pipeline_available": self.ingestion_pipeline is not None
        })
        return status
