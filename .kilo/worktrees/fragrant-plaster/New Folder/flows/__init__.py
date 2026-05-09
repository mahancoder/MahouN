"""
MAHOUN Flows Module
===================

Workflow orchestration and RAG flows.

Components:
- Enhanced RAG: Advanced retrieval-augmented generation
- Query Flow: Query processing pipeline
- Document Flow: Document processing workflow
- Feedback Flow: User feedback integration

Features:
- Multi-stage RAG pipeline
- Hybrid search integration
- Reranking and filtering
- Answer generation
- Quality assurance
"""

__version__ = "2.0.0"

from .enhanced_rag import EnhancedRAGPipeline

__all__ = [
    "EnhancedRAGPipeline",
]
