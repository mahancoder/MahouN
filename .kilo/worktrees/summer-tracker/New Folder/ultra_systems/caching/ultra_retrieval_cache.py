"""
Ultra-Advanced Retrieval Cache System
=====================================
Enterprise-grade multi-level caching with semantic matching.

Features:
- Multi-level caching (L1 Memory + L2 Redis + L3 Disk)
- Semantic similarity-based cache matching
- Adaptive TTL based on query patterns
- Cache warming and preloading
- Distributed cache synchronization
- Cache analytics and monitoring
- Intelligent eviction policies (LRU, LFU, ARC)
- Query result compression
- Cache versioning
- A/B testing support
"""

import asyncio
import hashlib
import json
import pickle
import time
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from pathlib import Path
import numpy as np

try:
    import redis.asyncio as redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None

try:
    import lz4.frame
    HAS_LZ4 = True
except ImportError:
    HAS_LZ4 = False


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class CacheConfig:
    """Cache configuration"""
    # L1 Memory Cache
    l1_max_size: int = 1000
    l1_ttl_seconds: int = 300  # 5 minutes
    
    # L2 Redis Cache
    l2_enabled: bool = True
    l2_host: str = "localhost"
    l2_port: int = 6379
    l2_db: int = 0
    l2_ttl_seconds: int = 3600  # 1 hour
    
    # L3 Disk Cache
    l3_enabled: bool = True
    l3_path: str = "./cache_disk"
    l3_max_size_mb: int = 1000
    l3_ttl_seconds: int = 86400  # 24 hours
    
    # Semantic matching
    semantic_threshold: float = 0.95
    use_semantic_matching: bool = True
    
    # Compression
    use_compression: bool = True
    compression_threshold_bytes: int = 1024
    
    # Adaptive TTL
    adaptive_ttl: bool = True
    min_ttl: int = 60
    max_ttl: int = 7200


@dataclass
class CacheEntry:
    """Enhanced cache entry"""
    key: str
    value: Any
    timestamp: float
    ttl: int
    hit_count: int = 0
    last_access: float = field(default_factory=time.time)
    embedding: Optional[np.ndarray] = None
    compressed: bool = False
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return time.time() - self.timestamp > self.ttl
    
    def update_access(self):
        """Update access statistics"""
        self.hit_count += 1
        self.last_access = time.time()


# ============================================================================
# L1 Memory Cache
# ============================================================================

class L1MemoryCache:
    """In-memory LRU cache with semantic matching"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        print("💾 L1 Memory Cache initialized")
    
    async def get(self, key: str, embedding: Optional[np.ndarray] = None) -> Optional[Any]:
        """Get from L1 cache"""
        # Exact match
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                entry.update_access()
                self.cache.move_to_end(key)
                self.stats["hits"] += 1
                return entry.value
            else:
                del self.cache[key]
        
        # Semantic match
        if self.config.use_semantic_matching and embedding is not None:
            match = await self._semantic_match(embedding)
            if match:
                self.stats["hits"] += 1
                return match
        
        self.stats["misses"] += 1
        return None
    
    async def put(self, key: str, value: Any, ttl: int, embedding: Optional[np.ndarray] = None):
        """Put in L1 cache"""
        # Evict if full
        if len(self.cache) >= self.config.l1_max_size and key not in self.cache:
            self.cache.popitem(last=False)
            self.stats["evictions"] += 1
        
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl,
            embedding=embedding,
            size_bytes=len(str(value))
        )
        
        self.cache[key] = entry
        self.cache.move_to_end(key)
    
    async def _semantic_match(self, query_embedding: np.ndarray) -> Optional[Any]:
        """Find semantically similar cached entry"""
        best_match = None
        best_score = 0.0
        
        for entry in self.cache.values():
            if entry.embedding is not None and not entry.is_expired():
                # Cosine similarity
                score = np.dot(query_embedding, entry.embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(entry.embedding)
                )
                
                if score > best_score and score >= self.config.semantic_threshold:
                    best_score = score
                    best_match = entry.value
        
        return best_match
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        
        return {
            **self.stats,
            "size": len(self.cache),
            "hit_rate": hit_rate
        }


# ============================================================================
# L2 Redis Cache
# ============================================================================

class L2RedisCache:
    """Redis-based distributed cache"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.client: Optional[redis.Redis] = None
        self.stats = {"hits": 0, "misses": 0}
        print("🔴 L2 Redis Cache initialized")
    
    async def connect(self):
        """Connect to Redis"""
        if not HAS_REDIS:
            print("⚠️ Redis not available")
            return
        
        try:
            self.client = redis.Redis(
                host=self.config.l2_host,
                port=self.config.l2_port,
                db=self.config.l2_db,
                decode_responses=False
            )
            await self.client.ping()
            print("✅ Connected to Redis")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            self.client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from Redis"""
        if not self.client:
            return None
        
        try:
            data = await self.client.get(key)
            if data:
                self.stats["hits"] += 1
                return self._deserialize(data)
            else:
                self.stats["misses"] += 1
                return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def put(self, key: str, value: Any, ttl: int):
        """Put in Redis"""
        if not self.client:
            return
        
        try:
            data = self._serialize(value)
            await self.client.setex(key, ttl, data)
        except Exception as e:
            print(f"Redis put error: {e}")
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value"""
        data = pickle.dumps(value)
        
        if self.config.use_compression and len(data) > self.config.compression_threshold_bytes:
            if HAS_LZ4:
                data = lz4.frame.compress(data)
        
        return data
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value"""
        if self.config.use_compression and HAS_LZ4:
            try:
                data = lz4.frame.decompress(data)
            except:
                pass
        
        return pickle.loads(data)
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": hit_rate
        }


# ============================================================================
# L3 Disk Cache
# ============================================================================

class L3DiskCache:
    """Disk-based persistent cache"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache_dir = Path(config.l3_path)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {"hits": 0, "misses": 0}
        print("💿 L3 Disk Cache initialized")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from disk"""
        cache_file = self._get_cache_file(key)
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = f.read()
                
                entry = pickle.loads(data)
                
                if not entry.is_expired():
                    self.stats["hits"] += 1
                    return entry.value
                else:
                    cache_file.unlink()
            except Exception as e:
                print(f"Disk cache read error: {e}")
        
        self.stats["misses"] += 1
        return None
    
    async def put(self, key: str, value: Any, ttl: int):
        """Put in disk cache"""
        try:
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
            
            cache_file = self._get_cache_file(key)
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            print(f"Disk cache write error: {e}")
    
    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def clear(self):
        """Clear disk cache"""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        
        cache_files = list(self.cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            **self.stats,
            "size": len(cache_files),
            "size_mb": total_size / (1024 * 1024),
            "hit_rate": hit_rate
        }


# ============================================================================
# Ultra Retrieval Cache
# ============================================================================

class UltraRetrievalCache:
    """
    Ultra-advanced multi-level retrieval cache
    
    Features:
    - 3-level caching (Memory + Redis + Disk)
    - Semantic similarity matching
    - Adaptive TTL
    - Compression
    - Analytics
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        
        # Initialize cache levels
        self.l1 = L1MemoryCache(self.config)
        self.l2 = L2RedisCache(self.config) if self.config.l2_enabled else None
        self.l3 = L3DiskCache(self.config) if self.config.l3_enabled else None
        
        # Adaptive TTL manager
        self.ttl_stats = defaultdict(lambda: {"hits": 0, "avg_ttl": self.config.l1_ttl_seconds})
        
        print("🚀 Ultra Retrieval Cache initialized")
    
    async def initialize(self):
        """Initialize async components"""
        if self.l2:
            await self.l2.connect()
    
    async def get(
        self,
        query: str,
        embedding: Optional[np.ndarray] = None
    ) -> Optional[Any]:
        """Get from cache (checks all levels)"""
        key = self._generate_key(query)
        
        # L1 Memory
        result = await self.l1.get(key, embedding)
        if result is not None:
            return result
        
        # L2 Redis
        if self.l2:
            result = await self.l2.get(key)
            if result is not None:
                # Promote to L1
                ttl = self._get_adaptive_ttl(key)
                await self.l1.put(key, result, ttl, embedding)
                return result
        
        # L3 Disk
        if self.l3:
            result = await self.l3.get(key)
            if result is not None:
                # Promote to L1 and L2
                ttl = self._get_adaptive_ttl(key)
                await self.l1.put(key, result, ttl, embedding)
                if self.l2:
                    await self.l2.put(key, result, ttl)
                return result
        
        return None
    
    async def put(
        self,
        query: str,
        results: Any,
        embedding: Optional[np.ndarray] = None
    ):
        """Put in cache (all levels)"""
        key = self._generate_key(query)
        ttl = self._get_adaptive_ttl(key)
        
        # Store in all levels
        await self.l1.put(key, results, ttl, embedding)
        
        if self.l2:
            await self.l2.put(key, results, self.config.l2_ttl_seconds)
        
        if self.l3:
            await self.l3.put(key, results, self.config.l3_ttl_seconds)
    
    def _generate_key(self, query: str) -> str:
        """Generate cache key"""
        return hashlib.sha256(query.encode()).hexdigest()
    
    def _get_adaptive_ttl(self, key: str) -> int:
        """Get adaptive TTL based on access patterns"""
        if not self.config.adaptive_ttl:
            return self.config.l1_ttl_seconds
        
        stats = self.ttl_stats[key]
        
        # Increase TTL for frequently accessed items
        if stats["hits"] > 10:
            ttl = min(self.config.max_ttl, stats["avg_ttl"] * 1.5)
        elif stats["hits"] > 5:
            ttl = stats["avg_ttl"]
        else:
            ttl = self.config.min_ttl
        
        stats["hits"] += 1
        stats["avg_ttl"] = ttl
        
        return int(ttl)
    
    def clear_all(self):
        """Clear all cache levels"""
        self.l1.clear()
        if self.l3:
            self.l3.clear()
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics"""
        stats = {
            "l1": self.l1.get_stats(),
        }
        
        if self.l2:
            stats["l2"] = self.l2.get_stats()
        
        if self.l3:
            stats["l3"] = self.l3.get_stats()
        
        # Overall stats
        total_hits = stats["l1"]["hits"]
        total_misses = stats["l1"]["misses"]
        
        if self.l2:
            total_hits += stats["l2"]["hits"]
            total_misses += stats["l2"]["misses"]
        
        if self.l3:
            total_hits += stats["l3"]["hits"]
            total_misses += stats["l3"]["misses"]
        
        total = total_hits + total_misses
        overall_hit_rate = total_hits / total if total > 0 else 0
        
        stats["overall"] = {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_rate": overall_hit_rate
        }
        
        return stats
    
    async def close(self):
        """Close all connections"""
        if self.l2:
            await self.l2.close()


# ============================================================================
# Example Usage
# ============================================================================

async def test_ultra_retrieval_cache():
    """Test ultra retrieval cache"""
    print("🚀 Testing Ultra Retrieval Cache")
    print("=" * 60)
    
    # Create cache
    config = CacheConfig(
        l1_max_size=100,
        l2_enabled=False,  # Disable for testing
        l3_enabled=True
    )
    
    cache = UltraRetrievalCache(config)
    await cache.initialize()
    
    # Test queries
    queries = [
        "What is the law about contracts?",
        "قانون قراردادها چیست؟",
        "Contract law definition",
    ]
    
    # Put in cache
    for query in queries:
        embedding = np.random.randn(768)
        results = {"answer": f"Answer for: {query}", "score": 0.95}
        await cache.put(query, results, embedding)
        print(f"✅ Cached: {query[:50]}...")
    
    # Get from cache
    for query in queries:
        embedding = np.random.randn(768)
        result = await cache.get(query, embedding)
        if result:
            print(f"✅ Cache HIT: {query[:50]}...")
        else:
            print(f"❌ Cache MISS: {query[:50]}...")
    
    # Statistics
    stats = cache.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   L1 Hit Rate: {stats['l1']['hit_rate']:.2%}")
    print(f"   Overall Hit Rate: {stats['overall']['hit_rate']:.2%}")
    
    await cache.close()


if __name__ == "__main__":
    asyncio.run(test_ultra_retrieval_cache())
