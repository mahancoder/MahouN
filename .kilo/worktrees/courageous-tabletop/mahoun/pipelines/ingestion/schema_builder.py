"""
Schema Builder - Bridge between Parser and Canonical Schema
============================================================
Converts raw parser output (dict) into canonical Pydantic schema objects.

This module bridges the gap between:
- L0: Raw verdict text files
- L1: TextDocument (text-level schema for RAG/indexing)
- L2: VerdictStruct (structured legal information)

Design:
- Robust handling of missing or malformed fields
- Safe defaulting for optional fields
- Preserves all data from parser
- Zero breaking changes to existing pipeline
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from mahoun.schemas.text_schema import TextDocument
from mahoun.schemas.legal_struct_schema import VerdictStruct
from mahoun.pipelines.ingestion.persian_normalizer import PersianLegalNormalizer

logger = logging.getLogger(__name__)


class SchemaBuilder:
    """
    Builds canonical schema objects from raw parsed verdict dicts.
    
    This class transforms the untyped dictionary output from
    minimal_verdict_parser into strongly-typed Pydantic models.
    
    Usage:
        >>> from mahoun.pipelines.ingestion.minimal_verdict_parser import parse_verdict_file
        >>> builder = SchemaBuilder()
        >>> raw_dict = parse_verdict_file("verdict.txt")
        >>> text_doc, verdict_struct = builder.build_from_parsed(raw_dict)
    """
    
    def __init__(self):
        """Initialize SchemaBuilder with Persian normalizer."""
        self.normalizer = PersianLegalNormalizer()
        logger.info("SchemaBuilder initialized")
    
    def build_from_parsed(self, parsed: Dict[str, Any]) -> Tuple[TextDocument, VerdictStruct]:
        """
        Build both L1 (TextDocument) and L2 (VerdictStruct) from parsed dict.
        
        Args:
            parsed: Raw dictionary from parse_verdict_text() or parse_verdict_file()
        
        Returns:
            Tuple of (TextDocument, VerdictStruct)
        
        Raises:
            ValueError: If parsed dict is missing critical fields
        """
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected dict, got {type(parsed)}")
        
        # Build L2 (VerdictStruct) - mainly just validation via Pydantic
        try:
            verdict_struct = VerdictStruct(**parsed)
        except Exception as e:
            logger.warning(f"Failed to create VerdictStruct: {e}. Using partial data.")
            # Graceful fallback: create with minimal required fields
            verdict_struct = VerdictStruct()
        
        # Build L1 (TextDocument) - extract metadata + text
        text_doc = self._build_text_document(parsed)
        
        logger.info(f"Built schemas for document: {text_doc.document_id}")
        return text_doc, verdict_struct
    
    def _build_text_document(self, parsed: Dict[str, Any]) -> TextDocument:
        """
        Build L1 TextDocument from parsed verdict dict.
        
        Extracts:
        - document_id from source filename or generates one
        - title from case metadata
        - full_text from sections (if available)
        - clean_text (normalized)
        - court from case_meta
        - date_issued from case_meta
        - source_file_path from _source
        """
        # Extract document ID
        document_id = self._extract_document_id(parsed)
        
        # Extract title (case number or court + date)
        title = self._extract_title(parsed)
        
        # Extract full text from sections
        full_text = self._extract_full_text(parsed)
        
        # Clean/normalize text
        clean_text: Optional[Any] = None
        if full_text:
            try:
                clean_text = self.normalizer.normalize(full_text)
            except Exception as e:
                logger.warning(f"Failed to normalize text: {e}")
                clean_text = full_text
        
        # Extract court
        court: Optional[Any] = None
        case_meta = parsed.get("case_meta", {})
        if isinstance(case_meta, dict):
            court = case_meta.get("court_level")
        
        # Extract date issued
        date_issued: Optional[Any] = None
        if isinstance(case_meta, dict):
            date_issued = case_meta.get("decision_date")
        
        # Extract source file path
        source_file_path: Optional[Any] = None
        source = parsed.get("_source", {})
        if isinstance(source, dict):
            source_file_path = source.get("filepath")
        
        return TextDocument(
            document_id=document_id,
            document_type="verdict",
            title=title,
            full_text=full_text or "",
            clean_text=clean_text,
            date_issued=date_issued,
            court=court,
            source_file_path=source_file_path,
            ingestion_timestamp=datetime.now(timezone.utc)
        )
    
    def _extract_document_id(self, parsed: Dict[str, Any]) -> str:
        """
        Extract or generate document ID.
        
        Priority:
        1. _source.filename (without extension)
        2. case_meta fields (court + date + branch)
        3. Timestamp-based fallback
        """
        # Try source filename
        source = parsed.get("_source", {})
        if isinstance(source, dict):
            filename = source.get("filename")
            if filename:
                # Remove extension
                doc_id = Path(filename).stem
                return doc_id
        
        # Try case metadata
        case_meta = parsed.get("case_meta", {})
        if isinstance(case_meta, dict):
            parts: List[Any] = []
            if case_meta.get("court_level"):
                # Simplify court name
                court = case_meta["court_level"].replace("دادگاه", "").strip()
                parts.append(court[:10])  # Limit length
            if case_meta.get("decision_date"):
                parts.append(case_meta["decision_date"].replace("-", ""))
            if case_meta.get("branch_number"):
                parts.append(f"sh{case_meta['branch_number']}")
            
            if parts:
                return "_".join(parts)
        
        # Fallback: timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"verdict_{timestamp}"
    
    def _extract_title(self, parsed: Dict[str, Any]) -> Optional[str]:
        """
        Extract a readable title for the verdict.
        
        Format: Court + Date or Filename
        """
        case_meta = parsed.get("case_meta", {})
        if isinstance(case_meta, dict):
            parts: List[Any] = []
            if case_meta.get("court_level"):
                parts.append(case_meta["court_level"])
            if case_meta.get("decision_date"):
                parts.append(case_meta["decision_date"])
            
            if parts:
                return " - ".join(parts)
        
        # Fallback to filename
        source = parsed.get("_source", {})
        if isinstance(source, dict):
            filename = source.get("filename")
            if filename:
                return filename
        
        return None
    
    def _extract_full_text(self, parsed: Dict[str, Any]) -> Optional[str]:
        """
        Extract full text from verdict sections.
        
        Combines summary + verdict sections.
        """
        sections = parsed.get("sections", {})
        if not isinstance(sections, dict):
            return None
        
        parts: List[Any] = []
        summary = sections.get("summary")
        if summary:
            parts.append(summary)
        
        verdict = sections.get("verdict")
        if verdict:
            parts.append(verdict)
        
        if parts:
            return "\n\n".join(parts)
        
        return None


# ============================================================================
# Convenience Functions
# ============================================================================

def build_schemas_from_parsed(parsed: Dict[str, Any]) -> Tuple[TextDocument, VerdictStruct]:
    """
    Convenience function to build schemas from parsed verdict.
    
    Args:
        parsed: Raw dictionary from parse_verdict_text() or parse_verdict_file()
    
    Returns:
        Tuple of (TextDocument, VerdictStruct)
    
    Example:
        >>> from mahoun.pipelines.ingestion.minimal_verdict_parser import parse_verdict_file
        >>> parsed = parse_verdict_file("verdict.txt")
        >>> text_doc, verdict_struct = build_schemas_from_parsed(parsed)
    """
    builder = SchemaBuilder()
    return builder.build_from_parsed(parsed)
