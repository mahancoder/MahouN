"""
Smart Multi-Level Caching System for RAG
========================================

Advanced caching with:
- Multi-level cache (Memory + Redis)
- Adaptive TTL based on query patterns
- Semantic similarity matching
- Cache warming and preloading
- Analytics and monitoring
- Batch operations
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None

from mahoun.pipelines._logging import setup_logger

log = setup_logger("smart_cache")


class CacheLevel(str, Enum):
    """Cache levels"""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    MISS = "miss"


@dataclass
class CacheEntry:
    """Enhanced cache entry with analytics"""
    query: str
    results: List[Dict]
    timestamp: float
    hit_count: int = 0
    last_access: float = field(default_factory=time.time)
    embedding: Optional[np.ndarray] = None
    ttl: int = 3600  # Adaptive TTL
    popularity_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return time.time() - self.timestamp > self.ttl
    
    def update_access(self):
        """Update access statistics"""
        self.hit_count += 1
        self.last_access = time.time()
        # Update popularity score (exponential moving average)
        time_factor = 1.0 / (1.0 + (time.time() - self.timestamp) / 3600)
        self.popularity_score = 0.7 * self.popularity_score + 0.3 * time_factor
    
    def to_dict(self) -> Dict:
        """Convert to dict for serialization"""
        return {
            'query': self.query,
            'results': self.results,
            'timestamp': self.timestamp,
            'hit_count': self.hit_count,
            'last_access': self.last_access,
            'ttl': self.ttl,
            'popularity_score': self.popularity_score,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """Create from dict"""
        return cls(
            query=data['query'],
            results=data['results'],
            timestamp=data['timestamp'],
            hit_count=data.get('hit_count', 0),
            last_access=data.get('last_access', time.time()),
            ttl=data.get('ttl', 3600),
            popularity_score=data.get('popularity_score', 0.0),
            metadata=data.get('metadata', {}),
        )


class AdaptiveTTLManager:
    """
    Manage adaptive TTL based on query patterns
    
    Popular queries get longer TTL
    Rare queries get shorter TTL
    """
    
    def __init__(
        self,
        min_ttl: int = 300,      # 5 minutes
        max_ttl: int = 86400,    # 24 hours
        default_ttl: int = 3600,  # 1 hour
    ):
        self.min_ttl = min_ttl
        self.max_ttl = max_ttl
        self.default_ttl = default_ttl
        self.query_stats: Dict[str, Dict] = defaultdict(lambda: {
            'access_count': 0,
            'last_access': time.time(),
            'avg_interval': 0,
        })
    
    def compute_ttl(self, query: str, entry: Optional[CacheEntry] = None) -> int:
        """
        Compute adaptive TTL based on query patterns
        
        Args:
            query: Query string
            entry: Existing cache entry (if any)
            
        Returns:
            TTL in seconds
        """
        stats = self.query_stats[query]
        
        # Update stats
        current_time = time.time()
        if stats['access_count'] > 0:
            interval = current_time - stats['last_access']
            stats['avg_interval'] = (
                0.7 * stats['avg_interval'] + 0.3 * interval
            )
        stats['access_count'] += 1
        stats['last_access'] = current_time
        
        # Compute TTL based on access frequency
        if stats['access_count'] < 2:
            return self.default_ttl
        
        # More frequent access = longer TTL
        avg_interval = stats['avg_interval']
        if avg_interval < 60:  # < 1 minute
            ttl = self.max_ttl
        elif avg_interval < 300:  # < 5 minutes
            ttl = self.max_ttl // 2
        elif avg_interval < 3600:  # < 1 hour
            ttl = self.default_ttl
        else:
            ttl = self.min_ttl
        
        # Consider popularity if entry exists
        if entry and entry.popularity_score > 0.5:
            ttl = int(ttl * 1.5)
        
        return min(max(ttl, self.min_ttl), self.max_ttl)
    
    def get_stats(self) -> Dict:
        """Get TTL manager statistics"""
        return {
            'tracked_queries': len(self.query_stats),
            'min_ttl': self.min_ttl,
            'max_ttl': self.max_ttl,
            'default_ttl': self.default_ttl,
        }


class SmartCache:
    """
    Multi-level smart cache with adaptive TTL
    
    Features:
    - L1: In-memory LRU cache (fast)
    - L2: Redis cache (persistent, shared)
    - Semantic similarity matching
    - Adaptive TTL
    - Cache analytics
    """
    
    def __init__(
        self,
        max_l1_size: int = 1000,
        max_l2_size: int = 10000,
        similarity_threshold: float = 0.92,
        enable_redis: bool = True,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_prefix: str = "mahoun:cache:",
    ):
        """
        Initialize smart cache
        
        Args:
            max_l1_size: Max L1 (memory) cache size
            max_l2_size: Max L2 (Redis) cache size
            similarity_threshold: Semantic similarity threshold
            enable_redis: Enable Redis L2 cache
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database number
            redis_prefix: Redis key prefix
        """
        self.max_l1_size = max_l1_size
        self.max_l2_size = max_l2_size
        self.similarity_threshold = similarity_threshold
        self.redis_prefix = redis_prefix
        
        # L1: Memory cache (OrderedDict for LRU)
        self.l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # L2: Redis cache
        self.redis_client: Optional[redis.Redis] = None
        if enable_redis and HAS_REDIS:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=False,  # We'll handle encoding
                )
                self.redis_client.ping()
                log.info(f"✅ Redis L2 cache connected: {redis_host}:{redis_port}")
            except Exception as e:
                log.warning(f"⚠️ Redis connection failed: {e}, using L1 only")
                self.redis_client = None
        else:
            log.info("Redis L2 cache disabled")
        
        # Adaptive TTL manager
        self.ttl_manager = AdaptiveTTLManager()
        
        # Embedding model (lazy load)
        self._embedding_model = None
        
        # Statistics
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0,
            'l1_evictions': 0,
            'l2_evictions': 0,
            'semantic_matches': 0,
        }
    
    def _get_embedding_model(self):
        """Lazy load embedding model"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer("BAAI/bge-m3")
                log.info("✅ Embedding model loaded for semantic cache")
            except Exception as e:
                log.warning(f"⚠️ Failed to load embedding model: {e}")
        return self._embedding_model
    
    def _embed_query(self, query: str) -> Optional[np.ndarray]:
        """Generate query embedding"""
        model = self._get_embedding_model()
        if model is None:
            return None
        try:
            embedding = model.encode([query], normalize_embeddings=True)[0]
            return embedding
        except Exception as e:
            log.error(f"Embedding failed: {e}")
            return None
    
    def _compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity"""
        return float(np.dot(emb1, emb2))
    
    def _hash_query(self, query: str) -> str:
        """Generate cache key"""
        return hashlib.sha256(query.encode()).hexdigest()
    
    def _redis_key(self, key: str) -> str:
        """Generate Redis key with prefix"""
        return f"{self.redis_prefix}{key}"
    
    def get(self, query: str, use_semantic: bool = True) -> Tuple[Optional[List[Dict]], CacheLevel]:
        """
        Get from cache (multi-level)
        
        Args:
            query: Query string
            use_semantic: Use semantic similarity matching
            
        Returns:
            Tuple of (results, cache_level)
        """
        key = self._hash_query(query)
        
        # Try L1 (memory) first
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if not entry.is_expired():
                entry.update_access()
                self.l1_cache.move_to_end(key)
                self.stats['l1_hits'] += 1
                log.debug(f"L1 HIT: {query[:50]}")
                return entry.results, CacheLevel.L1_MEMORY
            else:
                # Expired, remove
                del self.l1_cache[key]
        
        # Try L2 (Redis)
        if self.redis_client:
            try:
                redis_key = self._redis_key(key)
                data = self.redis_client.get(redis_key)
                if data:
                    entry_dict = json.loads(data)
                    entry = CacheEntry.from_dict(entry_dict)
                    
                    if not entry.is_expired():
                        entry.update_access()
                        # Promote to L1
                        self._put_l1(key, entry)
                        # Update in Redis
                        self._put_l2(key, entry)
                        self.stats['l2_hits'] += 1
                        log.debug(f"L2 HIT (promoted to L1): {query[:50]}")
                        return entry.results, CacheLevel.L2_REDIS
                    else:
                        # Expired, remove
                        self.redis_client.delete(redis_key)
            except Exception as e:
                log.error(f"Redis get error: {e}")
        
        # Try semantic matching if enabled
        if use_semantic:
            result = self._semantic_match(query)
            if result:
                self.stats['semantic_matches'] += 1
                return result, CacheLevel.L1_MEMORY
        
        # Cache miss
        self.stats['misses'] += 1
        log.debug(f"MISS: {query[:50]}")
        return None, CacheLevel.MISS
    
    def _semantic_match(self, query: str) -> Optional[List[Dict]]:
        """Try to find semantically similar cached query"""
        if not self.l1_cache:
            return None
        
        query_emb = self._embed_query(query)
        if query_emb is None:
            return None
        
        best_match = None
        best_similarity = 0.0
        
        for key, entry in self.l1_cache.items():
            if entry.is_expired():
                continue
            
            if entry.embedding is not None:
                similarity = self._compute_similarity(query_emb, entry.embedding)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = entry
        
        if best_match and best_similarity >= self.similarity_threshold:
            best_match.update_access()
            log.debug(f"Semantic match: similarity={best_similarity:.3f}")
            return best_match.results
        
        return None
    
    def put(self, query: str, results: List[Dict], metadata: Optional[Dict] = None):
        """
        Put in cache (multi-level)
        
        Args:
            query: Query string
            results: Results to cache
            metadata: Optional metadata
        """
        key = self._hash_query(query)
        
        # Compute adaptive TTL
        ttl = self.ttl_manager.compute_ttl(query)
        
        # Create entry with embedding
        query_emb = self._embed_query(query)
        entry = CacheEntry(
            query=query,
            results=results,
            timestamp=time.time(),
            embedding=query_emb,
            ttl=ttl,
            metadata=metadata or {},
        )
        
        # Put in L1
        self._put_l1(key, entry)
        
        # Put in L2 (Redis)
        if self.redis_client:
            self._put_l2(key, entry)
    
    def _put_l1(self, key: str, entry: CacheEntry):
        """Put in L1 cache with LRU eviction"""
        # Evict if full
        if len(self.l1_cache) >= self.max_l1_size and key not in self.l1_cache:
            evicted_key, evicted_entry = self.l1_cache.popitem(last=False)
            self.stats['l1_evictions'] += 1
            log.debug(f"L1 evicted: {evicted_entry.query[:50]}")
        
        self.l1_cache[key] = entry
        self.l1_cache.move_to_end(key)
    
    def _put_l2(self, key: str, entry: CacheEntry):
        """Put in L2 (Redis) cache"""
        if not self.redis_client:
            return
        
        try:
            redis_key = self._redis_key(key)
            # Don't serialize embedding (too large)
            entry_dict = entry.to_dict()
            data = json.dumps(entry_dict)
            
            # Set with TTL
            self.redis_client.setex(
                redis_key,
                entry.ttl,
                data
            )
        except Exception as e:
            log.error(f"Redis put error: {e}")
    
    def batch_get(self, queries: List[str]) -> Dict[str, Optional[List[Dict]]]:
        """
        Batch get from cache
        
        Args:
            queries: List of queries
            
        Returns:
            Dict mapping query to results (None if miss)
        """
        results = {}
        for query in queries:
            result, _ = self.get(query, use_semantic=False)
            results[query] = result
        return results
    
    def batch_put(self, items: List[Tuple[str, List[Dict]]]):
        """
        Batch put to cache
        
        Args:
            items: List of (query, results) tuples
        """
        for query, results in items:
            self.put(query, results)
    
    def invalidate(self, query: str):
        """Invalidate cache entry"""
        key = self._hash_query(query)
        
        # Remove from L1
        if key in self.l1_cache:
            del self.l1_cache[key]
        
        # Remove from L2
        if self.redis_client:
            try:
                redis_key = self._redis_key(key)
                self.redis_client.delete(redis_key)
            except Exception as e:
                log.error(f"Redis delete error: {e}")
    
    def clear(self):
        """Clear all caches"""
        self.l1_cache.clear()
        
        if self.redis_client:
            try:
                # Delete all keys with prefix
                pattern = f"{self.redis_prefix}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                log.error(f"Redis clear error: {e}")
        
        # Reset stats
        for key in self.stats:
            self.stats[key] = 0
    
    def get_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        total_requests = (
            self.stats['l1_hits'] +
            self.stats['l2_hits'] +
            self.stats['misses']
        )
        
        hit_rate = (
            (self.stats['l1_hits'] + self.stats['l2_hits']) / total_requests
            if total_requests > 0 else 0
        )
        
        return {
            'l1_size': len(self.l1_cache),
            'l1_max_size': self.max_l1_size,
            'l1_hits': self.stats['l1_hits'],
            'l1_evictions': self.stats['l1_evictions'],
            'l2_enabled': self.redis_client is not None,
            'l2_hits': self.stats['l2_hits'],
            'l2_evictions': self.stats['l2_evictions'],
            'misses': self.stats['misses'],
            'semantic_matches': self.stats['semantic_matches'],
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'l1_hit_rate': self.stats['l1_hits'] / total_requests if total_requests > 0 else 0,
            'l2_hit_rate': self.stats['l2_hits'] / total_requests if total_requests > 0 else 0,
            'ttl_stats': self.ttl_manager.get_stats(),
        }
    
    def get_popular_queries(self, top_k: int = 10) -> List[Tuple[str, float]]:
        """Get most popular cached queries"""
        queries = [
            (entry.query, entry.popularity_score)
            for entry in self.l1_cache.values()
        ]
        queries.sort(key=lambda x: x[1], reverse=True)
        return queries[:top_k]


# Global cache instance
_global_cache: Optional[SmartCache] = None


def get_global_cache() -> SmartCache:
    """Get or create global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = SmartCache()
    return _global_cache


def main():
    """Test smart cache"""
    print("=" * 60)
    print("Testing Smart Multi-Level Cache")
    print("=" * 60)
    
    # Create cache
    cache = SmartCache(
        max_l1_size=5,
        enable_redis=False,  # Disable for testing
        similarity_threshold=0.9,
    )
    
    # Test queries
    queries = [
        "قانون مدنی چیست",
        "قانون مدنی کدام است",  # Similar
        "حقوق جزا",
        "قانون مدنی چیست",  # Exact match
        "قانون مدنی",  # Similar
        "قرارداد",
        "قانون مدنی چیست",  # Popular query
    ]
    
    print("\nSimulating queries:")
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}] Query: {query}")
        
        # Try get
        results, level = cache.get(query)
        
        if results is None:
            # Simulate retrieval
            results = [{"id": f"doc{i}", "text": f"Result for {query}"}]
            cache.put(query, results)
            print(f"  → MISS, cached with adaptive TTL")
        else:
            print(f"  → HIT from {level.value}")
    
    # Show statistics
    print("\n" + "=" * 60)
    print("Cache Statistics:")
    print("=" * 60)
    stats = cache.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    
    # Show popular queries
    print("\n" + "=" * 60)
    print("Popular Queries:")
    print("=" * 60)
    for query, score in cache.get_popular_queries(top_k=5):
        print(f"  {query[:50]}: {score:.3f}")


if __name__ == "__main__":
    main()
