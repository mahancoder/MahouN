#!/usr/bin/env python3
"""
Core Interfaces for Advanced Chunking & Vector DB System
Defines abstract base classes and interfaces for all components
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy as np


# ============================================================================
# Enums
# ============================================================================

class ChunkingStrategy(Enum):
    """Available chunking strategies"""
    SEMANTIC = "semantic"
    FIXED = "fixed"
    ADAPTIVE = "adaptive"


class VectorStoreBackendType(Enum):
    """Available vector store backends"""
    CHROMADB = "chromadb"
    FAISS = "faiss"
    QDRANT = "qdrant"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Chunk:
    """Represents a text chunk"""
    id: str
    text: str
    start_pos: int
    end_pos: int
    chunk_index: int
    token_count: int
    doc_id: Optional[str] = None
    coherence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


@dataclass
class SearchResult:
    """Represents a search result"""
    id: str
    score: float
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[np.ndarray] = None


@dataclass
class QualityReport:
    """Chunk quality analysis report"""
    overall_score: float
    coherence_score: float
    completeness_score: float
    boundary_quality_score: float
    entity_preservation_score: float
    recommendations: List[str]
    issues: List[Dict[str, Any]]


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int
    misses: int
    hit_rate: float
    total_size_mb: float
    item_count: int


# ============================================================================
# Chunking Interfaces
# ============================================================================

class IChunkingService(ABC):
    """Interface for chunking service"""
    
    @abstractmethod
    def chunk_document(
        self,
        text: str,
        doc_id: str,
        strategy: Optional[ChunkingStrategy] = None,
        chunk_size: int = 512,
        overlap: int = 50,
        metadata: Optional[Dict] = None
    ) -> List[Chunk]:
        """
        Chunk a document with automatic strategy selection
        
        Args:
            text: Document text
            doc_id: Document identifier
            strategy: Chunking strategy (auto-selected if None)
            chunk_size: Target chunk size in tokens
            overlap: Overlap between chunks
            metadata: Additional metadata
            
        Returns:
            List of chunks
        """
        pass
    
    @abstractmethod
    def chunk_batch(
        self,
        documents: List[Dict],
        parallel: bool = True,
        strategy: Optional[ChunkingStrategy] = None
    ) -> Dict[str, List[Chunk]]:
        """
        Chunk multiple documents in batch
        
        Args:
            documents: List of documents with 'text' and 'doc_id'
            parallel: Whether to process in parallel
            strategy: Chunking strategy
            
        Returns:
            Dictionary mapping doc_id to chunks
        """
        pass
    
    @abstractmethod
    def analyze_quality(
        self,
        chunks: List[Chunk]
    ) -> QualityReport:
        """
        Analyze chunk quality
        
        Args:
            chunks: List of chunks to analyze
            
        Returns:
            Quality analysis report
        """
        pass


class IChunkQualityAnalyzer(ABC):
    """Interface for chunk quality analyzer"""
    
    @abstractmethod
    def compute_coherence_score(self, chunks: List[Chunk]) -> float:
        """Compute coherence score for chunks"""
        pass
    
    @abstractmethod
    def compute_completeness_score(self, chunks: List[Chunk]) -> float:
        """Compute completeness score"""
        pass
    
    @abstractmethod
    def compute_boundary_quality(self, chunks: List[Chunk]) -> float:
        """Compute boundary quality score"""
        pass
    
    @abstractmethod
    def generate_report(self, chunks: List[Chunk]) -> QualityReport:
        """Generate comprehensive quality report"""
        pass


# ============================================================================
# Vector Store Interfaces
# ============================================================================

class IVectorStoreBackend(ABC):
    """Abstract base class for vector store backends"""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to vector store"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to vector store"""
        pass
    
    @abstractmethod
    def add_embeddings(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        metadata: List[Dict],
        collection: str = "default"
    ) -> None:
        """
        Add embeddings to store
        
        Args:
            ids: List of unique identifiers
            embeddings: Embedding vectors (shape: [n, dim])
            metadata: List of metadata dictionaries
            collection: Collection name
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter: Optional[Dict] = None,
        collection: str = "default"
    ) -> List[SearchResult]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter: Metadata filter
            collection: Collection name
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    def delete(
        self,
        ids: List[str],
        collection: str = "default"
    ) -> None:
        """
        Delete embeddings by IDs
        
        Args:
            ids: List of IDs to delete
            collection: Collection name
        """
        pass
    
    @abstractmethod
    def get_collection_stats(
        self,
        collection: str = "default"
    ) -> Dict[str, Any]:
        """
        Get collection statistics
        
        Args:
            collection: Collection name
            
        Returns:
            Statistics dictionary
        """
        pass


class IVectorStoreManager(ABC):
    """Interface for vector store manager"""
    
    @abstractmethod
    def add_embeddings(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        metadata: List[Dict],
        collection: str = "default"
    ) -> None:
        """Add embeddings to store"""
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter: Optional[Dict] = None,
        collection: str = "default"
    ) -> List[SearchResult]:
        """Search for similar embeddings"""
        pass
    
    @abstractmethod
    def backup(
        self,
        path: str,
        collection: Optional[str] = None
    ) -> None:
        """Backup vector store"""
        pass
    
    @abstractmethod
    def restore(
        self,
        path: str,
        collection: Optional[str] = None
    ) -> None:
        """Restore from backup"""
        pass


# ============================================================================
# Cache Interfaces
# ============================================================================

class ICacheManager(ABC):
    """Interface for cache manager"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set value in cache with optional TTL"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries"""
        pass
    
    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        pass


# ============================================================================
# Embedding Interfaces
# ============================================================================

class IEmbeddingService(ABC):
    """Interface for embedding service"""
    
    @abstractmethod
    def embed_text(
        self,
        text: str,
        model: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate embedding for single text
        
        Args:
            text: Input text
            model: Model name (uses default if None)
            
        Returns:
            Embedding vector
        """
        pass
    
    @abstractmethod
    def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            model: Model name
            batch_size: Batch size for processing
            
        Returns:
            Embedding matrix (shape: [n, dim])
        """
        pass
    
    @abstractmethod
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a model"""
        pass


# ============================================================================
# Retrieval Interfaces
# ============================================================================

class IRetrievalService(ABC):
    """Interface for retrieval service"""
    
    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 10,
        collection: str = "default",
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            top_k: Number of results
            collection: Collection to search
            filters: Metadata filters
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        collection: str = "default"
    ) -> List[SearchResult]:
        """
        Hybrid search combining dense and sparse retrieval
        
        Args:
            query: Search query
            top_k: Number of results
            dense_weight: Weight for dense search
            sparse_weight: Weight for sparse search
            collection: Collection to search
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Rerank search results
        
        Args:
            query: Original query
            results: Initial search results
            top_k: Number of results to return
            
        Returns:
            Reranked results
        """
        pass


# ============================================================================
# Batch Processing Interfaces
# ============================================================================

class IBatchProcessor(ABC):
    """Interface for batch processor"""
    
    @abstractmethod
    def process_batch(
        self,
        items: List[Any],
        pipeline: List[callable],
        parallel: bool = True,
        checkpoint_interval: int = 100
    ) -> List[Any]:
        """
        Process items through pipeline
        
        Args:
            items: Items to process
            pipeline: List of processing functions
            parallel: Whether to process in parallel
            checkpoint_interval: Save checkpoint every N items
            
        Returns:
            Processed items
        """
        pass
    
    @abstractmethod
    def get_progress(self) -> Dict[str, Any]:
        """Get processing progress"""
        pass
    
    @abstractmethod
    def resume_from_checkpoint(
        self,
        checkpoint_path: str
    ) -> None:
        """Resume processing from checkpoint"""
        pass


# ============================================================================
# Monitoring Interfaces
# ============================================================================

class IMonitoringService(ABC):
    """Interface for monitoring service"""
    
    @abstractmethod
    def track_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Track a metric"""
        pass
    
    @abstractmethod
    def get_metrics(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Tuple[datetime, float]]:
        """Get metric values"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, str]:
        """Check system health"""
        pass
