#!/usr/bin/env python3
"""
Cache Models and Data Structures
=================================
"""

from dataclasses import dataclass
from typing import Any, Optional, Dict
from datetime import datetime
from enum import Enum


class CacheStatus(Enum):
    """Cache entry status"""
    VALID = "valid"
    EXPIRED = "expired"
    EVICTED = "evicted"
    INVALID = "invalid"


@dataclass
class CachedItem:
    """Represents a cached item with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    size_bytes: int = 0
    compressed: bool = False
    tags: Optional[Dict[str, str]] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if item is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at
    
    @property
    def age_seconds(self) -> float:
        """Get age in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def ttl_seconds(self) -> Optional[float]:
        """Get remaining TTL in seconds"""
        if self.expires_at is None:
            return None
        remaining = (self.expires_at - datetime.now()).total_seconds()
        return max(0, remaining)


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_sets: int = 0
    cache_deletes: int = 0
    cache_evictions: int = 0
    total_size_bytes: int = 0
    avg_latency_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate"""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """Calculate miss rate"""
        return 1.0 - self.hit_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_sets": self.cache_sets,
            "cache_deletes": self.cache_deletes,
            "cache_evictions": self.cache_evictions,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "total_size_mb": self.total_size_bytes / (1024 * 1024),
            "avg_latency_ms": self.avg_latency_ms
        }
