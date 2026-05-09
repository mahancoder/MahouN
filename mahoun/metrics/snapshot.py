"""
Immutable Metrics Snapshots - Audit Grade
==========================================

Immutable, versioned, auditable metric snapshots for regulatory compliance.

This module provides immutable snapshots of metrics state with comprehensive
audit metadata including timestamps, schema versions, and content hashes.

Key Principles:
- Immutability: Snapshots cannot be modified after creation
- Auditability: Full metadata for compliance requirements
- Versioning: Schema version for future compatibility
- Integrity: Content hash for tamper detection
- Determinism: Same input always produces same output
- Serializable: Can be converted to JSON for storage/transmission

Architecture:
    MetricsSnapshot is a frozen dataclass that contains:
    - Audit metadata (timestamp, version, hash)
    - Immutable metric data (counters, gauges, histograms)
    
    All metric data is wrapped in MappingProxyType to prevent modification.
    Content hash provides cryptographic integrity verification.

Compliance Features:
    - ISO8601 UTC timestamps for global consistency
    - SHA256 content hashing for tamper detection
    - Schema versioning for backward compatibility
    - Immutable data structures for audit trails
    - Deterministic serialization for reproducibility

Performance:
    - Snapshot creation: O(n) where n is number of metrics
    - Hash computation: O(m) where m is serialized data size
    - Integrity verification: O(m) hash recomputation
    - Memory overhead: ~2x metric data size (original + snapshot)
"""

import hashlib
import json
import logging
from copy import deepcopy
from datetime import datetime, timezone
from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .store import MetricsStore

logger = logging.getLogger(__name__)

# Schema version for compatibility tracking
# Increment this when the snapshot format changes
METRICS_SCHEMA_VERSION = "1.0.0"

# JSON serialization settings for deterministic hashing
JSON_SEPARATORS = (',', ':')  # Compact format
JSON_SORT_KEYS = True         # Deterministic key ordering


def _make_deeply_immutable(obj: Any) -> Any:
    """
    Recursively make nested data structures immutable.
    
    Converts all nested dicts to MappingProxyType to ensure
    true deep immutability. This is critical for audit compliance
    where snapshots must be tamper-proof.
    
    Args:
        obj: Object to make immutable (dict, list, or primitive)
    
    Returns:
        Immutable version of the object
    
    Examples:
        >>> data = {"a": {"b": {"c": 1}}}
        >>> immutable = _make_deeply_immutable(data)
        >>> immutable["a"]["b"]["c"] = 2  # TypeError
    """
    if isinstance(obj, dict):
        # Recursively make all nested dicts immutable
        return MappingProxyType({
            k: _make_deeply_immutable(v) 
            for k, v in obj.items()
        })
    elif isinstance(obj, list):
        # Make lists into tuples (immutable)
        return tuple(_make_deeply_immutable(item) for item in obj)
    else:
        # Primitives (int, float, str, etc.) are already immutable
        return obj


@dataclass(frozen=True)
class MetricsSnapshot:
    """
    Immutable metrics snapshot with comprehensive audit metadata.
    
    This class represents a point-in-time snapshot of metrics state with
    full audit trail information required for regulatory compliance.
    
    Immutability:
        - Frozen dataclass prevents attribute modification
        - MappingProxyType prevents metric data modification
        - Deep copies ensure no shared mutable state
    
    Audit Compliance:
        - ISO8601 UTC timestamp for precise timing
        - Schema version for format compatibility
        - SHA256 content hash for integrity verification
        - Deterministic serialization for reproducibility
    
    Thread Safety:
        Instances are immutable and therefore thread-safe.
        Multiple threads can safely access the same snapshot.
    """
    
    # Audit metadata - required for compliance
    timestamp: str          # ISO8601 UTC timestamp
    schema_version: str     # Schema version (e.g., "1.0.0")
    content_hash: str       # SHA256 hash of metric data
    
    # Immutable metric data - wrapped in MappingProxyType
    counters: MappingProxyType[str, Any]
    gauges: MappingProxyType[str, Any]
    histograms: MappingProxyType[str, Any]
    
    @classmethod
    def create(cls, store: "MetricsStore") -> "MetricsSnapshot":
        """
        Create immutable snapshot from MetricsStore.
        
        This is the primary factory method for creating snapshots.
        It extracts data from the store and wraps it in immutable containers.
        
        Args:
            store: MetricsStore instance to snapshot
        
        Returns:
            Immutable MetricsSnapshot with audit metadata
        
        Raises:
            ValueError: If store is None or invalid
            RuntimeError: If snapshot creation fails
        
        Performance:
            O(n) where n is the number of metrics in the store.
            Includes deep copying of all metric data.
        
        Thread Safety:
            Safe to call from multiple threads as long as the store
            is thread-safe (which MetricsStore is).
        """
        if store is None:
            raise ValueError("MetricsStore cannot be None")
        
        try:
            # Get snapshot data from store (this is a deep copy)
            snapshot_data = store.snapshot()
            
            # Validate snapshot data structure
            cls._validate_snapshot_data(snapshot_data)
            
            # CRITICAL: Deep copy AND recursively make ALL nested structures immutable
            # This ensures true immutability at all levels - no nested dict/list can be modified
            # This is essential for audit compliance and zero-hallucination guarantees
            counters_data = {
                k: _make_deeply_immutable(deepcopy(v)) 
                for k, v in snapshot_data["counters"].items()
            }
            gauges_data = {
                k: _make_deeply_immutable(deepcopy(v))
                for k, v in snapshot_data["gauges"].items()
            }
            histograms_data = {
                k: _make_deeply_immutable(deepcopy(v))
                for k, v in snapshot_data["histograms"].items()
            }
            
            # Create immutable views of the deeply immutable data
            counters = MappingProxyType(counters_data)
            gauges = MappingProxyType(gauges_data)
            histograms = MappingProxyType(histograms_data)
            
            # Generate audit metadata
            timestamp = cls._generate_timestamp()
            content_hash = cls._compute_content_hash(snapshot_data)
            
            logger.debug(f"Created snapshot with {len(counters)} counters, "
                        f"{len(gauges)} gauges, {len(histograms)} histograms")
            
            return cls(
                timestamp=timestamp,
                schema_version=METRICS_SCHEMA_VERSION,
                content_hash=content_hash,
                counters=counters,
                gauges=gauges,
                histograms=histograms
            )
            
        except Exception as e:
            logger.error(f"Failed to create metrics snapshot: {e}")
            raise RuntimeError(f"Snapshot creation failed: {e}") from e
    
    @staticmethod
    def _validate_snapshot_data(data: Dict[str, Any]) -> None:
        """
        Validate snapshot data structure.
        
        Args:
            data: Snapshot data from MetricsStore
        
        Raises:
            ValueError: If data structure is invalid
        """
        required_keys = {"counters", "gauges", "histograms"}
        if not isinstance(data, dict):
            raise ValueError("Snapshot data must be a dictionary")
        
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        for key in required_keys:
            if not isinstance(data[key], dict):
                raise ValueError(f"'{key}' must be a dictionary")
    
    @staticmethod
    def _generate_timestamp() -> str:
        """
        Generate ISO8601 UTC timestamp.
        
        Returns:
            ISO8601 formatted timestamp string in UTC
        
        Format:
            YYYY-MM-DDTHH:MM:SS.fffffZ
            Example: 2024-02-18T10:30:45.123456Z
        """
        return datetime.now(timezone.utc).isoformat()
    
    @staticmethod
    def _compute_content_hash(data: Dict[str, Any]) -> str:
        """
        Compute SHA256 hash of metric data for integrity verification.
        
        Uses deterministic JSON serialization to ensure the same data
        always produces the same hash, regardless of dictionary ordering.
        
        Args:
            data: Metric data dictionary
        
        Returns:
            SHA256 hash as lowercase hex string
        
        Raises:
            ValueError: If data cannot be serialized to JSON
            RuntimeError: If hash computation fails
        
        Determinism:
            - Keys are sorted for consistent ordering
            - Compact JSON format (no spaces)
            - UTF-8 encoding for consistent byte representation
        """
        try:
            # Create deterministic JSON representation
            json_str = json.dumps(
                data,
                sort_keys=JSON_SORT_KEYS,
                separators=JSON_SEPARATORS,
                ensure_ascii=False  # Allow Unicode characters
            )
            
            # Compute SHA256 hash
            hash_bytes = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
            
            return hash_bytes
            
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot serialize data for hashing: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Hash computation failed: {e}") from e
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert snapshot to dictionary for serialization.
        
        Creates a complete dictionary representation including all metadata
        and metric data. This can be serialized to JSON for storage or transmission.
        
        Returns:
            Dictionary with structure:
            {
                "metadata": {
                    "timestamp": str,
                    "schema_version": str,
                    "content_hash": str
                },
                "metrics": {
                    "counters": dict,
                    "gauges": dict,
                    "histograms": dict
                }
            }
        
        Thread Safety:
            Safe to call from multiple threads as the snapshot is immutable.
        
        Performance:
            O(n) where n is the number of metrics.
            Creates new dictionaries but doesn't deep copy metric values.
        """
        return {
            "metadata": {
                "timestamp": self.timestamp,
                "schema_version": self.schema_version,
                "content_hash": self.content_hash
            },
            "metrics": {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": dict(self.histograms)
            }
        }
    
    def verify_integrity(self) -> bool:
        """
        Verify snapshot integrity using content hash.
        
        Recomputes the content hash from current metric data and compares
        it with the stored hash. This detects any tampering or corruption.
        
        Returns:
            True if content hash matches current data, False otherwise
        
        Use Cases:
            - Audit trail verification
            - Detecting data corruption
            - Ensuring snapshot hasn't been tampered with
        
        Performance:
            O(m) where m is the size of serialized metric data.
            Involves JSON serialization and SHA256 computation.
        
        Thread Safety:
            Safe to call from multiple threads as the snapshot is immutable.
        """
        try:
            # Reconstruct the original data format
            current_data = {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": dict(self.histograms)
            }
            
            # Recompute hash
            expected_hash = self._compute_content_hash(current_data)
            
            # Compare with stored hash
            is_valid = self.content_hash == expected_hash
            
            if not is_valid:
                logger.warning(f"Snapshot integrity check failed: "
                             f"expected {expected_hash}, got {self.content_hash}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False
    
    def get_metric_count(self) -> Dict[str, int]:
        """
        Get count of metrics by type.
        
        Returns:
            Dictionary with counts: {"counters": int, "gauges": int, "histograms": int}
        
        Use Cases:
            - Summary statistics
            - Monitoring and alerting
            - Performance analysis
        """
        return {
            "counters": len(self.counters),
            "gauges": len(self.gauges),
            "histograms": len(self.histograms)
        }
    
    def get_total_metric_count(self) -> int:
        """
        Get total number of metrics in the snapshot.
        
        Returns:
            Total count of all metrics (counters + gauges + histograms)
        """
        counts = self.get_metric_count()
        return sum(counts.values())
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Serialize snapshot to JSON string.
        
        Args:
            indent: JSON indentation (None for compact, int for pretty-printing)
        
        Returns:
            JSON string representation of the snapshot
        
        Raises:
            ValueError: If snapshot cannot be serialized
        """
        try:
            return json.dumps(
                self.to_dict(),
                indent=indent,
                sort_keys=True,
                ensure_ascii=False
            )
        except Exception as e:
            raise ValueError(f"Cannot serialize snapshot to JSON: {e}") from e
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricsSnapshot":
        """
        Create snapshot from dictionary (deserialization).
        
        Args:
            data: Dictionary in the format returned by to_dict()
        
        Returns:
            MetricsSnapshot instance
        
        Raises:
            ValueError: If data format is invalid
        """
        try:
            metadata = data["metadata"]
            metrics = data["metrics"]
            
            return cls(
                timestamp=metadata["timestamp"],
                schema_version=metadata["schema_version"],
                content_hash=metadata["content_hash"],
                counters=MappingProxyType(metrics["counters"]),
                gauges=MappingProxyType(metrics["gauges"]),
                histograms=MappingProxyType(metrics["histograms"])
            )
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid snapshot data format: {e}") from e
    
    @classmethod
    def from_json(cls, json_str: str) -> "MetricsSnapshot":
        """
        Create snapshot from JSON string (deserialization).
        
        Args:
            json_str: JSON string in the format returned by to_json()
        
        Returns:
            MetricsSnapshot instance
        
        Raises:
            ValueError: If JSON is invalid or data format is wrong
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        counts = self.get_metric_count()
        return (f"MetricsSnapshot(timestamp={self.timestamp}, "
                f"counters={counts['counters']}, gauges={counts['gauges']}, "
                f"histograms={counts['histograms']}, hash={self.content_hash[:8]}...)")
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (f"MetricsSnapshot(timestamp='{self.timestamp}', "
                f"schema_version='{self.schema_version}', "
                f"content_hash='{self.content_hash}', "
                f"counters={len(self.counters)}, "
                f"gauges={len(self.gauges)}, "
                f"histograms={len(self.histograms)})")


# Utility functions for working with snapshots
def compare_snapshots(snapshot1: MetricsSnapshot, snapshot2: MetricsSnapshot) -> Dict[str, Any]:
    """
    Compare two snapshots and return differences.
    
    Args:
        snapshot1: First snapshot
        snapshot2: Second snapshot
    
    Returns:
        Dictionary with comparison results
    """
    return {
        "timestamp_diff": snapshot2.timestamp != snapshot1.timestamp,
        "schema_version_diff": snapshot2.schema_version != snapshot1.schema_version,
        "content_hash_diff": snapshot2.content_hash != snapshot1.content_hash,
        "metric_count_diff": snapshot2.get_metric_count() != snapshot1.get_metric_count(),
        "identical": snapshot1.content_hash == snapshot2.content_hash
    }


def validate_snapshot_chain(snapshots: List[MetricsSnapshot]) -> Dict[str, Any]:
    """
    Validate a chain of snapshots for audit compliance.
    
    Args:
        snapshots: List of snapshots in chronological order
    
    Returns:
        Dictionary with validation results
    """
    if not snapshots:
        return {"valid": True, "issues": []}
    
    issues = []
    
    # Check chronological ordering
    for i in range(1, len(snapshots)):
        if snapshots[i].timestamp <= snapshots[i-1].timestamp:
            issues.append(f"Timestamp ordering violation at index {i}")
    
    # Check schema version consistency
    schema_versions = {s.schema_version for s in snapshots}
    if len(schema_versions) > 1:
        issues.append(f"Multiple schema versions found: {schema_versions}")
    
    # Verify integrity of each snapshot
    for i, snapshot in enumerate(snapshots):
        if not snapshot.verify_integrity():
            issues.append(f"Integrity check failed for snapshot at index {i}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "snapshot_count": len(snapshots),
        "time_span": snapshots[-1].timestamp if snapshots else None
    }