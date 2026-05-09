# Golden Path Specification

## Purpose

This document defines the single, real, always-present execution path of the system that satisfies all requirements for a production-grade, evidence-based retrieval system. The Golden Path represents the core functionality that works reliably on a laptop without GPU and produces meaningful, verifiable output.

## Scope

### Included in Golden Path

- Document ingestion pipeline (text extraction, parsing, normalization)
- Semantic chunking of documents
- Generation of embeddings using sentence-transformers
- Hybrid retrieval combining dense vector similarity and BM25 sparse retrieval
- Storage and retrieval from ChromaDB vector store
- Ranked evidence output with comprehensive metadata

### Explicitly NOT part of Golden Path

- LLM-based processing or enhancement
- Agent orchestration systems
- Graph database operations (Neo4j)
- PostgreSQL database operations
- Advanced reasoning engines
- Uncertainty quantification systems
- Self-improvement mechanisms
- MCP (Model Coordination Protocol) features
- Any component requiring external services beyond local file system and ChromaDB

## Step-by-Step Execution Flow

1. **Document Input**
   - Accepts TXT, DOCX, or PDF files
   - Graceful fallback for missing optional dependencies

2. **Text Extraction / Parsing**
   - Extracts raw text content from document formats
   - Handles encoding and formatting appropriately

3. **Persian Normalization**
   - Standardizes Persian text (digits, characters, whitespace)
   - Applies rule-based corrections for legal documents

4. **Semantic Chunking**
   - Splits documents into meaningful segments
   - Maintains context with configurable overlap
   - Preserves document structure and metadata

5. **Embedding Generation**
   - Converts text chunks to vector representations
   - Uses sentence-transformers library locally
   - Generates 768-dimensional embeddings

6. **Hybrid Retrieval**
   - Combines dense vector similarity with BM25 sparse retrieval
   - Supports multiple fusion algorithms (RRF, weighted sum)
   - Filters results based on metadata when specified

7. **Vector Store Operations**
   - Stores embeddings and metadata in ChromaDB
   - Retrieves similar documents based on queries
   - Manages document collections and persistence

8. **Ranked Evidence Output**
   - Returns results sorted by relevance scores
   - Includes comprehensive metadata for each result
   - Provides traceability for retrieval decisions

## Explicit Dependencies

- Python 3.12+
- sentence-transformers (for embeddings)
- ChromaDB (for vector storage)
- rank_bm25 (for sparse retrieval)
- Standard document processing libraries (where available)
  - python-docx (optional for DOCX files)
  - PyPDF2 or pdfminer (optional for PDF files)

## Explicit Non-Dependencies

- Ollama or any LLM service
- Neo4j graph database
- PostgreSQL relational database
- Redis caching system
- External APIs or cloud services
- GPU-accelerated computing
- Docker or containerization
- Kubernetes orchestration