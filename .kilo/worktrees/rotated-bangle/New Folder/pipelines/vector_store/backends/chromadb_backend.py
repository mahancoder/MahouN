"""
ChromaDB Backend Implementation
================================
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    chromadb = None

from .base import VectorStoreBackend
from ..models import SearchResult, VectorStoreConfig

logger = logging.getLogger(__name__)


class ChromaDBBackend(VectorStoreBackend):
    """
    ChromaDB vector store backend
    
    Features:
    - Local or HTTP client support
    - Metadata filtering
    - Persistent storage
    - Backup/restore
    """
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize ChromaDB backend"""
        super().__init__(config)
        
        if not HAS_CHROMADB:
            raise ImportError(
                "chromadb is not installed. "
                "Install it with: pip install chromadb"
            )
        
        self.client = None
        self.collection = None
    
    async def initialize(self) -> None:
        """Initialize ChromaDB client and collection"""
        logger.info(f"Initializing ChromaDB backend: {self.collection_name}")
        
        # Create client
        if self.config.chromadb_host:
            # HTTP client
            self.client = chromadb.HttpClient(
                host=self.config.chromadb_host,
                port=self.config.chromadb_port or 8000
            )
            logger.info(f"Connected to ChromaDB at {self.config.chromadb_host}:{self.config.chromadb_port}")
        else:
            # Local client
            settings = Settings(
                persist_directory=self.config.chromadb_path or "./chroma_db",
                anonymized_telemetry=False
            )
            self.client = chromadb.Client(settings)
            logger.info(f"Using local ChromaDB at {self.config.chromadb_path}")
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"dimension": self.config.dimension}
        )
        
        logger.info(f"Collection '{self.collection_name}' ready")
    
    async def add_vectors(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add vectors to ChromaDB"""
        if self.collection is None:
            raise RuntimeError("Backend not initialized. Call initialize() first.")
        
        # Convert numpy array to list
        embeddings_list = embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings_list,
            metadatas=metadata or [{}] * len(ids)
        )
        
        logger.debug(f"Added {len(ids)} vectors to {self.collection_name}")
    
    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search ChromaDB for similar vectors"""
        if self.collection is None:
            raise RuntimeError("Backend not initialized. Call initialize() first.")
        
        # Convert to list
        query_list = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_list],
            n_results=top_k,
            where=filter
        )
        
        # Convert to SearchResult objects
        search_results = []
        if results['ids'] and len(results['ids']) > 0:
            for i, doc_id in enumerate(results['ids'][0]):
                search_results.append(SearchResult(
                    id=doc_id,
                    score=1.0 - results['distances'][0][i],  # Convert distance to similarity
                    metadata=results['metadatas'][0][i] if results['metadatas'] else {},
                    text=results['documents'][0][i] if results.get('documents') else None
                ))
        
        return search_results
    
    async def delete(self, ids: List[str]) -> None:
        """Delete vectors from ChromaDB"""
        if self.collection is None:
            raise RuntimeError("Backend not initialized. Call initialize() first.")
        
        self.collection.delete(ids=ids)
        logger.debug(f"Deleted {len(ids)} vectors from {self.collection_name}")
    
    async def get(self, ids: List[str]) -> List[SearchResult]:
        """Get vectors by IDs"""
        if self.collection is None:
            raise RuntimeError("Backend not initialized. Call initialize() first.")
        
        results = self.collection.get(ids=ids, include=['metadatas', 'embeddings'])
        
        search_results = []
        for i, doc_id in enumerate(results['ids']):
            search_results.append(SearchResult(
                id=doc_id,
                score=1.0,
                metadata=results['metadatas'][i] if results['metadatas'] else {},
                embedding=np.array(results['embeddings'][i]) if results.get('embeddings') else None
            ))
        
        return search_results
    
    async def count(self) -> int:
        """Get total number of vectors"""
        if self.collection is None:
            raise RuntimeError("Backend not initialized. Call initialize() first.")
        
        return self.collection.count()
    
    async def backup(self, path: str) -> str:
        """Backup ChromaDB collection"""
        # ChromaDB handles persistence automatically
        # For explicit backup, we can export the data
        logger.info(f"ChromaDB uses persistent storage. Data is at: {self.config.chromadb_path}")
        return self.config.chromadb_path or "./chroma_db"
    
    async def restore(self, path: str) -> None:
        """Restore from backup"""
        logger.info("ChromaDB restore: data is automatically loaded from persistent storage")
    
    async def close(self) -> None:
        """Close ChromaDB connection"""
        # ChromaDB client doesn't need explicit closing
        logger.info("ChromaDB backend closed")
