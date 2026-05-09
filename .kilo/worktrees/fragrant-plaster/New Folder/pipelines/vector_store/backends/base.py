"""
Base Vector Store Backend
==========================
Abstract base class for all vector store implementations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
from ..models import SearchResult, VectorStoreConfig


class VectorStoreBackend(ABC):
    """
    Abstract base class for vector store backends
    
    All vector store implementations must inherit from this class
    and implement all abstract methods.
    """
    
    def __init__(self, config: VectorStoreConfig):
        """
        Initialize backend
        
        Args:
            config: Vector store configuration
        """
        self.config = config
        self.collection_name = config.collection_name
        self.dimension = config.dimension
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store connection"""
        pass
    
    @abstractmethod
    async def add_vectors(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add vectors to the store
        
        Args:
            ids: List of vector IDs
            embeddings: Array of embeddings (n_vectors, dimension)
            metadata: Optional list of metadata dicts
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar vectors
        
        Args:
            query_embedding: Query vector (dimension,)
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        """
        Delete vectors by IDs
        
        Args:
            ids: List of vector IDs to delete
        """
        pass
    
    @abstractmethod
    async def get(self, ids: List[str]) -> List[SearchResult]:
        """
        Get vectors by IDs
        
        Args:
            ids: List of vector IDs
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get total number of vectors in collection"""
        pass
    
    @abstractmethod
    async def backup(self, path: str) -> str:
        """
        Backup vector store to file
        
        Args:
            path: Backup file path
            
        Returns:
            Path to backup file
        """
        pass
    
    @abstractmethod
    async def restore(self, path: str) -> None:
        """
        Restore vector store from backup
        
        Args:
            path: Backup file path
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close connections and cleanup resources"""
        pass
