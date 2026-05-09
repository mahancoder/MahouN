#!/usr/bin/env python3
"""
MAHOUN Python SDK
=================
Client library for interacting with MAHOUN Advanced Chunking & Vector DB API

Example Usage:
    from sdk.mahoun_client import MahounClient
    
    client = MahounClient(base_url="http://localhost:8000", api_key="your-api-key")
    
    # Chunk a document
    result = client.chunking.chunk_text("Your document text here")
    
    # Generate embeddings
    embedding = client.embedding.embed_text("Your text here")
    
    # Search documents
    results = client.retrieval.search("Your query here")
"""

import requests
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger("mahoun_sdk")


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
    coherence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """Represents a search result"""
    id: str
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    chunk_index: Optional[int] = None


# ============================================================================
# API Client Components
# ============================================================================

class ChunkingClient:
    """Client for chunking operations"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50,
        strategy: str = "semantic",
        quality_check: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Chunk a text document
        
        Args:
            text: Text to chunk
            chunk_size: Target chunk size in tokens
            overlap: Overlap between chunks
            strategy: Chunking strategy (semantic, fixed, adaptive)
            quality_check: Whether to run quality analysis
            metadata: Additional metadata
            
        Returns:
            Dictionary with chunking results
        """
        url = f"{self.base_url}/api/v1/chunking/chunk"
        
        payload = {
            "text": text,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "strategy": strategy,
            "quality_check": quality_check,
            "metadata": metadata or {}
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert to Chunk objects
        chunks = [
            Chunk(
                id=c["id"],
                text=c["text"],
                start_pos=c["start_pos"],
                end_pos=c["end_pos"],
                chunk_index=c["chunk_index"],
                token_count=c["token_count"],
                coherence_score=c.get("coherence_score"),
                metadata=c.get("metadata")
            )
            for c in data["chunks"]
        ]
        
        return {
            "job_id": data["job_id"],
            "status": data["status"],
            "chunks": chunks,
            "total_chunks": data["total_chunks"],
            "processing_time_ms": data["processing_time_ms"],
            "quality_metrics": data.get("quality_metrics"),
            "created_at": data["created_at"]
        }
    
    def list_strategies(self) -> Dict[str, Any]:
        """
        List available chunking strategies
        
        Returns:
            Dictionary of available strategies
        """
        url = f"{self.base_url}/api/v1/chunking/strategies"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check chunking service health"""
        url = f"{self.base_url}/api/v1/chunking/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


class EmbeddingClient:
    """Client for embedding operations"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def embed_text(
        self,
        text: str,
        model: str = "sentence-transformers/all-mpnet-base-v2",
        normalize: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            model: Embedding model to use
            normalize: Whether to normalize embedding
            metadata: Additional metadata
            
        Returns:
            Dictionary with embedding and metadata
        """
        url = f"{self.base_url}/api/v1/embedding/embed"
        
        payload = {
            "text": text,
            "model": model,
            "normalize": normalize,
            "metadata": metadata or {}
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def embed_batch(
        self,
        texts: List[str],
        model: str = "sentence-transformers/all-mpnet-base-v2",
        normalize: bool = True,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use
            normalize: Whether to normalize embeddings
            batch_size: Batch size for processing
            
        Returns:
            Dictionary with embeddings and metadata
        """
        url = f"{self.base_url}/api/v1/embedding/embed/batch"
        
        payload = {
            "texts": texts,
            "model": model,
            "normalize": normalize,
            "batch_size": batch_size
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_models(self) -> Dict[str, Any]:
        """
        List available embedding models
        
        Returns:
            Dictionary of available models
        """
        url = f"{self.base_url}/api/v1/embedding/models"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check embedding service health"""
        url = f"{self.base_url}/api/v1/embedding/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


class RetrievalClient:
    """Client for retrieval operations"""
    
    def __init__(self, base_url: str, session: requests.Session):
        self.base_url = base_url
        self.session = session
    
    def search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 10,
        threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = False
    ) -> Dict[str, Any]:
        """
        Perform vector similarity search
        
        Args:
            query: Search query text
            collection: Collection to search
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            filters: Metadata filters
            rerank: Whether to apply reranking
            
        Returns:
            Dictionary with search results
        """
        url = f"{self.base_url}/api/v1/retrieval/search"
        
        payload = {
            "query": query,
            "collection": collection,
            "top_k": top_k,
            "threshold": threshold,
            "filters": filters or {},
            "rerank": rerank
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert to SearchResult objects
        results = [
            SearchResult(
                id=r["id"],
                text=r["text"],
                score=r["score"],
                metadata=r.get("metadata"),
                chunk_index=r.get("chunk_index")
            )
            for r in data["results"]
        ]
        
        return {
            "query_id": data["query_id"],
            "query": data["query"],
            "results": results,
            "total_results": data["total_results"],
            "search_time_ms": data["search_time_ms"],
            "collection": data["collection"],
            "created_at": data["created_at"]
        }
    
    def hybrid_search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 10,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform hybrid search (dense + sparse)
        
        Args:
            query: Search query text
            collection: Collection to search
            top_k: Number of results to return
            dense_weight: Weight for dense search
            sparse_weight: Weight for sparse search
            filters: Metadata filters
            
        Returns:
            Dictionary with search results
        """
        url = f"{self.base_url}/api/v1/retrieval/search/hybrid"
        
        payload = {
            "query": query,
            "collection": collection,
            "top_k": top_k,
            "dense_weight": dense_weight,
            "sparse_weight": sparse_weight,
            "filters": filters or {}
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert to SearchResult objects
        results = [
            SearchResult(
                id=r["id"],
                text=r["text"],
                score=r["score"],
                metadata=r.get("metadata"),
                chunk_index=r.get("chunk_index")
            )
            for r in data["results"]
        ]
        
        return {
            "query_id": data["query_id"],
            "query": data["query"],
            "results": results,
            "total_results": data["total_results"],
            "search_time_ms": data["search_time_ms"],
            "collection": data["collection"],
            "created_at": data["created_at"]
        }
    
    def store_document(
        self,
        text: str,
        collection: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
        chunk_before_store: bool = True,
        chunk_size: int = 512
    ) -> Dict[str, Any]:
        """
        Store a document in the vector store
        
        Args:
            text: Document text
            collection: Collection name
            metadata: Document metadata
            chunk_before_store: Whether to chunk before storing
            chunk_size: Chunk size if chunking
            
        Returns:
            Dictionary with storage results
        """
        url = f"{self.base_url}/api/v1/retrieval/store"
        
        payload = {
            "text": text,
            "collection": collection,
            "metadata": metadata or {},
            "chunk_before_store": chunk_before_store,
            "chunk_size": chunk_size
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_collections(self) -> Dict[str, Any]:
        """
        List available collections
        
        Returns:
            Dictionary with collection list
        """
        url = f"{self.base_url}/api/v1/retrieval/collections"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check retrieval service health"""
        url = f"{self.base_url}/api/v1/retrieval/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


# ============================================================================
# Main Client
# ============================================================================

class MahounClient:
    """
    Main client for MAHOUN Advanced Chunking & Vector DB API
    
    Example:
        client = MahounClient(
            base_url="http://localhost:8000",
            api_key="your-api-key"
        )
        
        # Chunk text
        result = client.chunking.chunk_text("Your text here")
        
        # Generate embedding
        embedding = client.embedding.embed_text("Your text here")
        
        # Search
        results = client.retrieval.search("Your query here")
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize MAHOUN client
        
        Args:
            base_url: Base URL of the API
            api_key: API key for authentication
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        
        # Create session
        self.session = requests.Session()
        self.session.verify = verify_ssl
        
        # Set headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "MAHOUN-Python-SDK/1.0.0"
        })
        
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}"
            })
        
        # Initialize sub-clients
        self.chunking = ChunkingClient(self.base_url, self.session)
        self.embedding = EmbeddingClient(self.base_url, self.session)
        self.retrieval = RetrievalClient(self.base_url, self.session)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check overall API health
        
        Returns:
            Dictionary with health status
        """
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Close the client session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# ============================================================================
# Convenience Functions
# ============================================================================

def quick_chunk(
    text: str,
    base_url: str = "http://localhost:8000",
    api_key: Optional[str] = None,
    **kwargs
) -> List[Chunk]:
    """
    Quick function to chunk text
    
    Args:
        text: Text to chunk
        base_url: API base URL
        api_key: API key
        **kwargs: Additional chunking parameters
        
    Returns:
        List of Chunk objects
    """
    with MahounClient(base_url=base_url, api_key=api_key) as client:
        result = client.chunking.chunk_text(text, **kwargs)
        return result["chunks"]


def quick_embed(
    text: str,
    base_url: str = "http://localhost:8000",
    api_key: Optional[str] = None,
    **kwargs
) -> List[float]:
    """
    Quick function to generate embedding
    
    Args:
        text: Text to embed
        base_url: API base URL
        api_key: API key
        **kwargs: Additional embedding parameters
        
    Returns:
        Embedding vector
    """
    with MahounClient(base_url=base_url, api_key=api_key) as client:
        result = client.embedding.embed_text(text, **kwargs)
        return result["embedding"]


def quick_search(
    query: str,
    base_url: str = "http://localhost:8000",
    api_key: Optional[str] = None,
    **kwargs
) -> List[SearchResult]:
    """
    Quick function to search
    
    Args:
        query: Search query
        base_url: API base URL
        api_key: API key
        **kwargs: Additional search parameters
        
    Returns:
        List of SearchResult objects
    """
    with MahounClient(base_url=base_url, api_key=api_key) as client:
        result = client.retrieval.search(query, **kwargs)
        return result["results"]
