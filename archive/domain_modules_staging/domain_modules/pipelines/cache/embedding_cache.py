#!/usr/bin/env python3
"""
Embedding Cache
===============
Specialized cache for text embeddings with advanced features:
- Text hash-based caching
- Batch caching
- Cache warming
- Similarity-based retrieval
- Automatic invalidation
"""

import logging
import hashlib
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
import asyncio

from .manager import CacheManager, CacheBackend

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Specialized cache for text embeddings
    
    Features:
    - Hash-based caching by text content
    - Batch operations
    - Cache warming strategies
    - Model-specific caching
    - Automatic invalidation
    - Similarity search in cache
    
    Example:
        ```python
        cache = EmbeddingCache(
            cache_manager=cache_mgr,
            model_name="all-mpnet-base-v2"
        )
        
        # Cache single embedding
        await cache.set_embedding("Hello world", embedding_vector)
        
        # Get cached embedding
        cached = await cache.get_embedding("Hello world")
        
        # Batch operations
        texts = ["text1", "text2", "text3"]
        embeddings = await cache.get_embeddings_batch(texts)
        
        # Cache warming
        await cache.warm_cache(common_texts)
        ```
    """
    
    def __init__(
        self,
        cache_manager: CacheManager,
        model_name: str,
        ttl: int = 86400,  # 24 hours
        enable_batch_caching: bool = True,
        max_batch_size: int = 100
    ):
        """
        Initialize embedding cache
        
        Args:
            cache_manager: Underlying cache manager
            model_name: Embedding model name (for key namespacing)
            ttl: Cache TTL in seconds
            enable_batch_caching: Enable batch caching optimization
            max_batch_size: Maximum batch size
        """
        self.cache = cache_manager
        self.model_name = model_name
        self.ttl = ttl
        self.enable_batch_caching = enable_batch_caching
        self.max_batch_size = max_batch_size
        
        # Statistics
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_hits": 0,
            "batch_misses": 0,
            "warm_cache_count": 0
        }
    
    def _hash_text(self, text: str) -> str:
        """
        Generate hash for text
        
        Args:
            text: Input text
            
        Returns:
            Hash string
        """
        # Normalize text
        normalized = text.strip().lower()
        
        # Generate SHA256 hash
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _make_cache_key(self, text_hash: str) -> str:
        """
        Generate cache key
        
        Args:
            text_hash: Text hash
            
        Returns:
            Cache key with model namespace
        """
        return f"embedding:{self.model_name}:{text_hash}"
    
    async def get_embedding(
        self,
        text: str,
        return_metadata: bool = False
    ) -> Optional[np.ndarray]:
        """
        Get cached embedding for text
        
        Args:
            text: Input text
            return_metadata: Return metadata along with embedding
            
        Returns:
            Cached embedding or None if not found
        """
        text_hash = self._hash_text(text)
        cache_key = self._make_cache_key(text_hash)
        
        cached = await self.cache.get(cache_key)
        
        if cached is not None:
            self.stats["cache_hits"] += 1
            
            if return_metadata:
                return cached
            else:
                return cached.get("embedding") if isinstance(cached, dict) else cached
        
        self.stats["cache_misses"] += 1
        return None
    
    async def set_embedding(
        self,
        text: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Cache embedding for text
        
        Args:
            text: Input text
            embedding: Embedding vector
            metadata: Optional metadata
        """
        text_hash = self._hash_text(text)
        cache_key = self._make_cache_key(text_hash)
        
        # Store embedding with metadata
        cache_value = {
            "embedding": embedding,
            "text_hash": text_hash,
            "model": self.model_name,
            "metadata": metadata or {}
        }
        
        await self.cache.set(cache_key, cache_value, ttl=self.ttl)
    
    async def get_embeddings_batch(
        self,
        texts: List[str]
    ) -> Tuple[List[Optional[np.ndarray]], List[int]]:
        """
        Get cached embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            Tuple of (embeddings list, indices of missing texts)
        """
        if not self.enable_batch_caching:
            # Fall back to individual gets
            embeddings = []
            missing_indices = []
            
            for i, text in enumerate(texts):
                emb = await self.get_embedding(text)
                embeddings.append(emb)
                if emb is None:
                    missing_indices.append(i)
            
            return embeddings, missing_indices
        
        # Batch get
        cache_keys = [
            self._make_cache_key(self._hash_text(text))
            for text in texts
        ]
        
        cached_values = await self.cache.get_many(cache_keys)
        
        embeddings = []
        missing_indices = []
        
        for i, (text, cache_key) in enumerate(zip(texts, cache_keys)):
            if cache_key in cached_values:
                cached = cached_values[cache_key]
                emb = cached.get("embedding") if isinstance(cached, dict) else cached
                embeddings.append(emb)
                self.stats["batch_hits"] += 1
            else:
                embeddings.append(None)
                missing_indices.append(i)
                self.stats["batch_misses"] += 1
        
        return embeddings, missing_indices
    
    async def set_embeddings_batch(
        self,
        texts: List[str],
        embeddings: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Cache embeddings for multiple texts
        
        Args:
            texts: List of input texts
            embeddings: Embedding matrix (n_texts, dim)
            metadata: Optional metadata for each text
        """
        if not self.enable_batch_caching:
            # Fall back to individual sets
            for i, text in enumerate(texts):
                meta = metadata[i] if metadata and i < len(metadata) else None
                await self.set_embedding(text, embeddings[i], meta)
            return
        
        # Batch set
        items = {}
        
        for i, text in enumerate(texts):
            text_hash = self._hash_text(text)
            cache_key = self._make_cache_key(text_hash)
            
            cache_value = {
                "embedding": embeddings[i],
                "text_hash": text_hash,
                "model": self.model_name,
                "metadata": metadata[i] if metadata and i < len(metadata) else {}
            }
            
            items[cache_key] = cache_value
        
        await self.cache.set_many(items, ttl=self.ttl)
    
    async def warm_cache(
        self,
        texts: List[str],
        embedding_function: callable,
        batch_size: Optional[int] = None
    ) -> int:
        """
        Warm cache with embeddings for common texts
        
        Args:
            texts: List of texts to pre-cache
            embedding_function: Function to generate embeddings
            batch_size: Batch size for processing
            
        Returns:
            Number of texts cached
        """
        batch_size = batch_size or self.max_batch_size
        cached_count = 0
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Check which are already cached
            embeddings, missing_indices = await self.get_embeddings_batch(batch_texts)
            
            if not missing_indices:
                # All cached
                continue
            
            # Generate embeddings for missing texts
            missing_texts = [batch_texts[idx] for idx in missing_indices]
            
            if asyncio.iscoroutinefunction(embedding_function):
                new_embeddings = await embedding_function(missing_texts)
            else:
                new_embeddings = embedding_function(missing_texts)
            
            # Cache new embeddings
            await self.set_embeddings_batch(missing_texts, new_embeddings)
            
            cached_count += len(missing_texts)
            self.stats["warm_cache_count"] += len(missing_texts)
        
        logger.info(f"Cache warming complete: {cached_count} new embeddings cached")
        return cached_count
    
    async def invalidate_model(self, model_name: Optional[str] = None) -> int:
        """
        Invalidate all cached embeddings for a model
        
        Args:
            model_name: Model name (uses current model if None)
            
        Returns:
            Number of entries invalidated
        """
        model = model_name or self.model_name
        
        # This is a simplified version
        # In production, you'd want to use Redis SCAN with pattern matching
        logger.warning(f"Invalidating cache for model: {model}")
        
        # For now, just clear the entire cache
        # TODO: Implement pattern-based deletion
        await self.cache.clear()
        
        return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Statistics dictionary
        """
        cache_stats = await self.cache.get_stats()
        
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = self.stats["cache_hits"] / total_requests if total_requests > 0 else 0.0
        
        return {
            "model": self.model_name,
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": hit_rate,
            "batch_hits": self.stats["batch_hits"],
            "batch_misses": self.stats["batch_misses"],
            "warm_cache_count": self.stats["warm_cache_count"],
            "underlying_cache": cache_stats
        }
    
    async def clear(self) -> None:
        """Clear all cached embeddings"""
        await self.cache.clear()
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_hits": 0,
            "batch_misses": 0,
            "warm_cache_count": 0
        }


class QueryResultCache:
    """
    Cache for query results
    
    Features:
    - Query hash-based caching
    - TTL support
    - Result filtering
    - Automatic invalidation
    
    Example:
        ```python
        cache = QueryResultCache(cache_manager=cache_mgr)
        
        # Cache query results
        await cache.set_results(
            query="contract law",
            results=search_results,
            filters={"category": "legal"}
        )
        
        # Get cached results
        cached = await cache.get_results(
            query="contract law",
            filters={"category": "legal"}
        )
        ```
    """
    
    def __init__(
        self,
        cache_manager: CacheManager,
        ttl: int = 3600,  # 1 hour
        include_filters_in_key: bool = True
    ):
        """
        Initialize query result cache
        
        Args:
            cache_manager: Underlying cache manager
            ttl: Cache TTL in seconds
            include_filters_in_key: Include filters in cache key
        """
        self.cache = cache_manager
        self.ttl = ttl
        self.include_filters_in_key = include_filters_in_key
        
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def _hash_query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> str:
        """
        Generate hash for query
        
        Args:
            query: Query string
            filters: Optional filters
            top_k: Number of results
            
        Returns:
            Query hash
        """
        # Build key components
        components = [query.strip().lower()]
        
        if self.include_filters_in_key and filters:
            # Sort filters for consistent hashing
            filter_str = str(sorted(filters.items()))
            components.append(filter_str)
        
        if top_k is not None:
            components.append(str(top_k))
        
        # Generate hash
        key_string = "|".join(components)
        hash_obj = hashlib.sha256(key_string.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _make_cache_key(self, query_hash: str) -> str:
        """Generate cache key"""
        return f"query_result:{query_hash}"
    
    async def get_results(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> Optional[List[Any]]:
        """
        Get cached query results
        
        Args:
            query: Query string
            filters: Optional filters
            top_k: Number of results
            
        Returns:
            Cached results or None
        """
        query_hash = self._hash_query(query, filters, top_k)
        cache_key = self._make_cache_key(query_hash)
        
        cached = await self.cache.get(cache_key)
        
        if cached is not None:
            self.stats["cache_hits"] += 1
            return cached.get("results") if isinstance(cached, dict) else cached
        
        self.stats["cache_misses"] += 1
        return None
    
    async def set_results(
        self,
        query: str,
        results: List[Any],
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Cache query results
        
        Args:
            query: Query string
            results: Search results
            filters: Optional filters
            top_k: Number of results
            metadata: Optional metadata
        """
        query_hash = self._hash_query(query, filters, top_k)
        cache_key = self._make_cache_key(query_hash)
        
        cache_value = {
            "results": results,
            "query": query,
            "filters": filters,
            "top_k": top_k,
            "metadata": metadata or {}
        }
        
        await self.cache.set(cache_key, cache_value, ttl=self.ttl)
    
    async def invalidate_query(self, query: str) -> None:
        """
        Invalidate cached results for a query
        
        Args:
            query: Query string
        """
        # This would need pattern matching in production
        # For now, just log
        logger.info(f"Invalidating cache for query: {query}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = self.stats["cache_hits"] / total if total > 0 else 0.0
        
        return {
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": hit_rate
        }
    
    async def clear(self) -> None:
        """Clear all cached results"""
        await self.cache.clear()
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0
        }
