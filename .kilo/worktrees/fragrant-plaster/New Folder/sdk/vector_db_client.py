#!/usr/bin/env python3
"""
Advanced Chunking & Vector DB Python SDK
Provides a convenient Python client for interacting with the API
"""

import requests
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
import json
from datetime import datetime


@dataclass
class ChunkResult:
    """Represents a chunk result"""
    id: str
    text: str
    start_pos: int
    end_pos: int
    chunk_index: int
    token_count: int
    coherence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EmbeddingResult:
    """Represents an embedding result"""
    embedding: List[float]
    dimension: int
    model: str
    processing_time_ms: float


@dataclass
class SearchResult:
    """Represents a search result"""
    id: str
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    chunk_index: Optional[int] = None


class VectorDBClient:
    """
    Python client for Advanced Chunking & Vector DB API
    
    Example:
        >>> client = VectorDBClient(base_url="http://localhost:8000")
        >>> chunks = client.chunk_text("Your document text here")
        >>> embedding = client.embed_text("Your text here")
        >>> results = client.search("Your query", top_k=10)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize the Vector DB client
        
        Args:
            base_url: Base URL of the API server
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    # ========================================================================
    # Chunking Methods
    # ========================================================================
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50,
        strategy: str = "semantic",
        quality_check: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ChunkResult]:
        """
        Chunk a document into smaller pieces
        
        Args:
            text: Text to chunk
            chunk_size: Target chunk size in tokens
            overlap: Overlap between chunks in tokens
            strategy: Chunking strategy (semantic, fixed, adaptive)
            quality_check: Whether to run quality analysis
            metadata: Additional metadata
            
        Returns:
            List of ChunkResult objects
        """
        data = {
            "text": text,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "strategy": strategy,
            "quality_check": quality_check,
            "metadata": metadata or {}
        }
        
        response = self._request("POST", "/api/v1/chunking/chunk", data=data)
        
        chunks = []
        for chunk_data in response.get("chunks", []):
            chunk = ChunkResult(
                id=chunk_data["id"],
                text=chunk_data["text"],
                start_pos=chunk_data["start_pos"],
                end_pos=chunk_data["end_pos"],
                chunk_index=chunk_data["chunk_index"],
                token_count=chunk_data["token_count"],
                coherence_score=chunk_data.get("coherence_score"),
                metadata=chunk_data.get("metadata")
            )
            chunks.append(chunk)
        
        return chunks
    
    def list_chunking_strategies(self) -> Dict[str, Any]:
        """
        Get available chunking strategies
        
        Returns:
            Dictionary of available strategies with descriptions
        """
        response = self._request("GET", "/api/v1/chunking/strategies")
        return response.get("strategies", {})
    
    # ========================================================================
    # Embedding Methods
    # ========================================================================
    
    def embed_text(
        self,
        text: str,
        model: str = "sentence-transformers/all-mpnet-base-v2",
        normalize: bool = True
    ) -> EmbeddingResult:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            model: Embedding model to use
            normalize: Whether to normalize the embedding
            
        Returns:
            EmbeddingResult object
        """
        data = {
            "text": text,
            "model": model,
            "normalize": normalize
        }
        
        response = self._request("POST", "/api/v1/embedding/embed", data=data)
        
        return EmbeddingResult(
            embedding=response["embedding"],
            dimension=response["dimension"],
            model=response["model"],
            processing_time_ms=response["processing_time_ms"]
        )
    
    def embed_batch(
        self,
        texts: List[str],
        model: str = "sentence-transformers/all-mpnet-base-v2",
        normalize: bool = True,
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use
            normalize: Whether to normalize embeddings
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        data = {
            "texts": texts,
            "model": model,
            "normalize": normalize,
            "batch_size": batch_size
        }
        
        response = self._request("POST", "/api/v1/embedding/embed/batch", data=data)
        return response["embeddings"]
    
    def list_embedding_models(self) -> Dict[str, Any]:
        """
        Get available embedding models
        
        Returns:
            Dictionary of available models with specifications
        """
        response = self._request("GET", "/api/v1/embedding/models")
        return response.get("models", {})
    
    # ========================================================================
    # Retrieval Methods
    # ========================================================================
    
    def search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 10,
        threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = False
    ) -> List[SearchResult]:
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
            List of SearchResult objects
        """
        data = {
            "query": query,
            "collection": collection,
            "top_k": top_k,
            "threshold": threshold,
            "filters": filters,
            "rerank": rerank
        }
        
        response = self._request("POST", "/api/v1/retrieval/search", data=data)
        
        results = []
        for result_data in response.get("results", []):
            result = SearchResult(
                id=result_data["id"],
                text=result_data["text"],
                score=result_data["score"],
                metadata=result_data.get("metadata"),
                chunk_index=result_data.get("chunk_index")
            )
            results.append(result)
        
        return results
    
    def hybrid_search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 10,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
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
            List of SearchResult objects
        """
        data = {
            "query": query,
            "collection": collection,
            "top_k": top_k,
            "dense_weight": dense_weight,
            "sparse_weight": sparse_weight,
            "filters": filters
        }
        
        response = self._request("POST", "/api/v1/retrieval/search/hybrid", data=data)
        
        results = []
        for result_data in response.get("results", []):
            result = SearchResult(
                id=result_data["id"],
                text=result_data["text"],
                score=result_data["score"],
                metadata=result_data.get("metadata"),
                chunk_index=result_data.get("chunk_index")
            )
            results.append(result)
        
        return results
    
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
            collection: Target collection
            metadata: Document metadata
            chunk_before_store: Whether to chunk before storing
            chunk_size: Chunk size if chunking
            
        Returns:
            Storage result with document_id and chunks_stored
        """
        data = {
            "text": text,
            "collection": collection,
            "metadata": metadata,
            "chunk_before_store": chunk_before_store,
            "chunk_size": chunk_size
        }
        
        return self._request("POST", "/api/v1/retrieval/store", data=data)
    
    def list_collections(self) -> List[str]:
        """
        Get list of available collections
        
        Returns:
            List of collection names
        """
        response = self._request("GET", "/api/v1/retrieval/collections")
        return response.get("collections", [])
    
    # ========================================================================
    # Data Management Methods
    # ========================================================================
    
    def create_backup(
        self,
        collection: str = "default",
        backup_type: str = "full",
        destination: str = "local",
        compression: bool = True
    ) -> Dict[str, Any]:
        """
        Create a backup of a collection
        
        Args:
            collection: Collection to backup
            backup_type: Backup type (full, incremental)
            destination: Backup destination (local, s3, gcs)
            compression: Whether to compress backup
            
        Returns:
            Backup information
        """
        data = {
            "collection": collection,
            "backup_type": backup_type,
            "destination": destination,
            "compression": compression
        }
        
        return self._request("POST", "/api/v1/data/backup", data=data)
    
    def restore_backup(
        self,
        backup_id: str,
        target_collection: Optional[str] = None,
        validate: bool = True,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Restore a collection from backup
        
        Args:
            backup_id: Backup ID to restore
            target_collection: Target collection (default: original)
            validate: Validate backup before restore
            overwrite: Overwrite existing data
            
        Returns:
            Restore information
        """
        data = {
            "backup_id": backup_id,
            "target_collection": target_collection,
            "validate": validate,
            "overwrite": overwrite
        }
        
        return self._request("POST", "/api/v1/data/restore", data=data)
    
    def list_backups(self, collection: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of available backups
        
        Args:
            collection: Filter by collection
            
        Returns:
            List of backup information
        """
        params = {"collection": collection} if collection else None
        response = self._request("GET", "/api/v1/data/backups", params=params)
        return response.get("backups", [])
    
    def bulk_ingest(
        self,
        documents: List[Dict[str, Any]],
        collection: str = "default",
        chunk_documents: bool = True,
        generate_embeddings: bool = True,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Ingest multiple documents in bulk
        
        Args:
            documents: List of documents to ingest
            collection: Target collection
            chunk_documents: Whether to chunk documents
            generate_embeddings: Whether to generate embeddings
            batch_size: Batch size for processing
            
        Returns:
            Ingestion result
        """
        data = {
            "documents": documents,
            "collection": collection,
            "chunk_documents": chunk_documents,
            "generate_embeddings": generate_embeddings,
            "batch_size": batch_size
        }
        
        return self._request("POST", "/api/v1/data/ingest/bulk", data=data)
    
    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """
        Get statistics for a collection
        
        Args:
            collection: Collection name
            
        Returns:
            Collection statistics
        """
        return self._request("GET", f"/api/v1/data/collections/{collection}/stats")
    
    def delete_collection(self, collection: str, confirm: bool = False) -> Dict[str, str]:
        """
        Delete a collection
        
        Args:
            collection: Collection to delete
            confirm: Confirmation flag (must be True)
            
        Returns:
            Deletion confirmation
        """
        if not confirm:
            raise ValueError("Must set confirm=True to delete collection")
        
        params = {"confirm": "true"}
        return self._request("DELETE", f"/api/v1/data/collections/{collection}", params=params)
    
    def optimize_collection(self, collection: str) -> Dict[str, Any]:
        """
        Optimize a collection's indexes and storage
        
        Args:
            collection: Collection to optimize
            
        Returns:
            Optimization result
        """
        return self._request("POST", f"/api/v1/data/collections/{collection}/optimize")
    
    # ========================================================================
    # Health Check Methods
    # ========================================================================
    
    def health_check(self) -> Dict[str, str]:
        """
        Check API health status
        
        Returns:
            Health status for all services
        """
        services = ["chunking", "embedding", "retrieval", "data"]
        health_status = {}
        
        for service in services:
            try:
                response = self._request("GET", f"/api/v1/{service}/health")
                health_status[service] = response.get("status", "unknown")
            except Exception as e:
                health_status[service] = f"error: {str(e)}"
        
        return health_status
    
    # ========================================================================
    # Convenience Methods
    # ========================================================================
    
    def process_document(
        self,
        text: str,
        collection: str = "default",
        chunk_size: int = 512,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to chunk, embed, and store a document
        
        Args:
            text: Document text
            collection: Target collection
            chunk_size: Chunk size
            metadata: Document metadata
            
        Returns:
            Processing result with chunks and storage info
        """
        # Chunk the document
        chunks = self.chunk_text(text, chunk_size=chunk_size, metadata=metadata)
        
        # Store the document
        store_result = self.store_document(
            text=text,
            collection=collection,
            metadata=metadata,
            chunk_before_store=True,
            chunk_size=chunk_size
        )
        
        return {
            "chunks": len(chunks),
            "document_id": store_result.get("document_id"),
            "chunks_stored": store_result.get("chunks_stored"),
            "collection": collection
        }
    
    def search_and_explain(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search and return results with explanations
        
        Args:
            query: Search query
            collection: Collection to search
            top_k: Number of results
            
        Returns:
            Search results with explanations
        """
        results = self.search(query, collection=collection, top_k=top_k, rerank=True)
        
        explained_results = []
        for result in results:
            explained_results.append({
                "text": result.text,
                "score": result.score,
                "metadata": result.metadata,
                "explanation": f"Matched with score {result.score:.3f}"
            })
        
        return explained_results


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize client
    client = VectorDBClient(base_url="http://localhost:8000")
    
    # Example 1: Chunk a document
    print("Example 1: Chunking")
    chunks = client.chunk_text(
        text="This is a sample document. It contains multiple sentences. We will chunk it.",
        chunk_size=256,
        strategy="semantic"
    )
    print(f"Created {len(chunks)} chunks")
    
    # Example 2: Generate embedding
    print("\nExample 2: Embedding")
    embedding = client.embed_text("Sample text for embedding")
    print(f"Generated embedding with dimension {embedding.dimension}")
    
    # Example 3: Store and search
    print("\nExample 3: Store and Search")
    store_result = client.store_document(
        text="Legal document about contracts and agreements.",
        collection="legal_docs",
        metadata={"category": "contracts"}
    )
    print(f"Stored document: {store_result}")
    
    search_results = client.search(
        query="contract agreements",
        collection="legal_docs",
        top_k=5
    )
    print(f"Found {len(search_results)} results")
    
    # Example 4: Health check
    print("\nExample 4: Health Check")
    health = client.health_check()
    print(f"Health status: {health}")
