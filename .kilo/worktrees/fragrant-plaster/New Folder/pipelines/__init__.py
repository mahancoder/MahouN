"""
MAHOUN Data Pipelines
=====================

Comprehensive data processing pipelines for legal document ingestion,
preprocessing, embedding, and indexing.

Components:
- Ingestion: Document parsing and extraction
- Data Prep Advanced: Quality analysis, chunking, entity linking
- Labeling: Advanced labeling with uncertainty and active learning
- Embedding: Vector embedding generation
- Indexing: Multi-database indexing (PostgreSQL, Neo4j, ChromaDB)

Features:
- Multi-format document support (PDF, DOCX, TXT, JSON)
- Smart chunking with semantic boundaries
- Entity recognition and linking
- Quality assurance and validation
- Distributed processing support
"""

__version__ = "2.0.0"

from pipelines.ingestion.parsers import (
    BaseParser,
    ParserFactory,
    PDFParser,
    DOCXParser,
    JSONParser,
    TXTParser,
    LegalDocumentParser,
    ParseResult,
)
from pipelines.data_prep_advanced.pipeline import AdvancedDataPipeline
from pipelines.embed_index import EmbedIndexPipeline

# NEW: Smart Cache and Query Enhancement
try:
    from pipelines.smart_cache import SmartCache, CacheLevel, get_global_cache
    _HAS_SMART_CACHE = True
except ImportError:
    _HAS_SMART_CACHE = False
    SmartCache = None
    CacheLevel = None
    get_global_cache = None

try:
    from pipelines.advanced_query_enhancement import (
        AdvancedQueryEnhancer,
        QueryIntent,
        QueryComplexity,
        get_global_enhancer,
    )
    _HAS_QUERY_ENHANCEMENT = True
except ImportError:
    _HAS_QUERY_ENHANCEMENT = False
    AdvancedQueryEnhancer = None
    QueryIntent = None
    QueryComplexity = None
    get_global_enhancer = None

__all__ = [
    # Parsers
    "BaseParser",
    "ParserFactory",
    "PDFParser",
    "DOCXParser",
    "JSONParser",
    "TXTParser",
    "LegalDocumentParser",
    "ParseResult",
    # Pipelines
    "AdvancedDataPipeline",
    "EmbedIndexPipeline",
    # Smart Cache
    "SmartCache",
    "CacheLevel",
    "get_global_cache",
    # Query Enhancement
    "AdvancedQueryEnhancer",
    "QueryIntent",
    "QueryComplexity",
    "get_global_enhancer",
]
