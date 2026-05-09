"""
Pure Metrics State Container - Enterprise Grade
===============================================

Thread-safe, deterministic state container for metrics with zero side effects.

This module implements a pure state container that stores metric instances
without any business logic, I/O operations, or implicit mutations.

Key Principles:
- Single Responsibility: State storage ONLY
- Thread Safety: All operations protected by RLock
- Purity: No side effects in any method
- Determinism: Same input always produces same output
- Atomicity: Operations are all-or-nothing
- Immutability: Snapshots are deep copies

Architecture:
    MetricsStore stores three types of metrics in separate dictionaries:
    - Counters: Monotonically increasing values
    - Gauges: Values that can go up or down
    - Histograms: Collections of observed values with percentiles

Thread Safety:
    All operations use threading.RLock to ensure concurrent access safety.
    The lock is reentrant, allowing nested calls within the same thread.

Performance:
    - Registration: O(1) lookup + creation if needed
    - Retrieval: O(1) dictionary lookup
    - Snapshot: O(n) deep copy of all metrics
    - Reset: O(1) dictionary clear operations

Audit Compliance:
    - Deterministic behavior for reproducible results
    - Atomic operations for consistency
    - Immutable snapshots for audit trails
"""

import logging
import threading
from copy import deepcopy
from typing import Dict, Optional, Any, List

# Import metric types from existing implementation
from .metrics import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class MetricsStore:
    """
    Thread-safe, pure state container for metrics.
    
    This class is responsible ONLY for storing metric instances and providing
    controlled access. It has NO awareness of system metrics, I/O operations,
    or any external concerns.
    
    Thread Safety:
        All public methods are protected by threading.RLock for concurrent access.
        The lock is reentrant to allow nested calls within the same thread.
    
    Purity Guarantee:
        - No side effects in read operations
        - No implicit mutations
        - No external I/O or network calls
        - No system metric awareness
    
    Determinism Guarantee:
        - Same inputs always produce same outputs
        - Operations are atomic (all-or-nothing)
        - State transitions are predictable
    """
    
    def __init__(self) -> None:
        """
        Initialize empty metrics store.
        
        Creates three empty dictionaries for storing different metric types
        and initializes the thread safety lock.
        """
        # Separate storage for each metric type
        # Key format: "metric_name" or "metric_name{label1=value1,label2=value2}"
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        
        # Thread safety lock (reentrant)
        self._lock = threading.RLock()
        
        logger.debug("MetricsStore initialized with empty state")
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """
        Create unique key from metric name and labels.
        
        Args:
            name: Metric name
            labels: Optional labels dictionary
        
        Returns:
            Unique key string combining name and sorted labels
        """
        if not labels:
            return name
        
        # Sort labels for deterministic key generation
        sorted_labels = sorted(labels.items())
        label_str = ",".join(f"{k}={v}" for k, v in sorted_labels)
        return f"{name}{{{label_str}}}"
    
    # ========================================================================
    # Registration Methods - Create metrics if they don't exist
    # ========================================================================
    
    def register_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> Counter:
        """
        Register or retrieve a counter metric.
        
        Thread-safe operation that creates a new counter if it doesn't exist,
        or returns the existing counter if it does.
        
        Args:
            name: Unique counter name (must be non-empty string)
            labels: Optional labels dictionary (default: empty dict)
        
        Returns:
            Counter instance (new or existing)
        
        Raises:
            ValueError: If name is empty or None
            TypeError: If labels is not a dictionary
        
        Thread Safety:
            Protected by RLock - safe for concurrent access
        
        Determinism:
            Same name+labels always returns the same Counter instance
        """
        if not name or not isinstance(name, str):
            raise ValueError("Counter name must be a non-empty string")
        
        if labels is not None and not isinstance(labels, dict):
            raise TypeError("Labels must be a dictionary or None")
        
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._counters:
                self._counters[key] = Counter(name=name, labels=labels or {})
                logger.debug(f"Created new counter: {key}")
            
            return self._counters[key]
    
    def register_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Gauge:
        """
        Register or retrieve a gauge metric.
        
        Thread-safe operation that creates a new gauge if it doesn't exist,
        or returns the existing gauge if it does.
        
        Args:
            name: Unique gauge name (must be non-empty string)
            labels: Optional labels dictionary (default: empty dict)
        
        Returns:
            Gauge instance (new or existing)
        
        Raises:
            ValueError: If name is empty or None
            TypeError: If labels is not a dictionary
        
        Thread Safety:
            Protected by RLock - safe for concurrent access
        
        Determinism:
            Same name+labels always returns the same Gauge instance
        """
        if not name or not isinstance(name, str):
            raise ValueError("Gauge name must be a non-empty string")
        
        if labels is not None and not isinstance(labels, dict):
            raise TypeError("Labels must be a dictionary or None")
        
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._gauges:
                self._gauges[key] = Gauge(name=name, labels=labels or {})
                logger.debug(f"Created new gauge: {key}")
            
            return self._gauges[key]
    
    def register_histogram(
        self, 
        name: str, 
        buckets: Optional[List[float]] = None, 
        labels: Optional[Dict[str, str]] = None
    ) -> Histogram:
        """
        Register or retrieve a histogram metric.
        
        Thread-safe operation that creates a new histogram if it doesn't exist,
        or returns the existing histogram if it does.
        
        Args:
            name: Unique histogram name (must be non-empty string)
            buckets: Bucket boundaries for histogram (default: standard buckets)
            labels: Optional labels dictionary (default: empty dict)
        
        Returns:
            Histogram instance (new or existing)
        
        Raises:
            ValueError: If name is empty or None, or buckets are invalid
            TypeError: If labels is not a dictionary or buckets not a list
        
        Thread Safety:
            Protected by RLock - safe for concurrent access
        
        Determinism:
            Same name always returns the same Histogram instance
        """
        if not name or not isinstance(name, str):
            raise ValueError("Histogram name must be a non-empty string")
        
        if labels is not None and not isinstance(labels, dict):
            raise TypeError("Labels must be a dictionary or None")
        
        if buckets is not None:
            if not isinstance(buckets, list):
                raise TypeError("Buckets must be a list or None")
            if not all(isinstance(b, (int, float)) for b in buckets):
                raise ValueError("All bucket values must be numbers")
            if buckets != sorted(buckets):
                raise ValueError("Bucket values must be in ascending order")
        
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._histograms:
                # Use default buckets if none provided
                default_buckets = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
                self._histograms[key] = Histogram(
                    name=name,
                    buckets=buckets or default_buckets,
                    labels=labels or {}
                )
                logger.debug(f"Created new histogram: {key}")
            
            return self._histograms[key]
    
    # ========================================================================
    # Retrieval Methods - Read-only access to existing metrics
    # ========================================================================
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[Counter]:
        """
        Get counter by name and optional labels (read-only).
        
        Thread-safe read operation that returns the counter if it exists,
        or None if it doesn't exist.
        
        Args:
            name: Counter name to lookup
            labels: Optional labels to match (if None, returns first counter with that name)
        
        Returns:
            Counter instance if found, None otherwise
        
        Thread Safety:
            Protected by RLock - safe for concurrent access
        
        Purity:
            No side effects - does not create or modify anything
        """
        with self._lock:
            if labels is not None:
                # Exact match with labels
                key = self._make_key(name, labels)
                return self._counters.get(key)
            else:
                # Return first counter with matching name (for backward compatibility)
                for key, counter in self._counters.items():
                    if counter.name == name:
                        return counter
                return None
    
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[Gauge]:
        """
        Get gauge by name and optional labels (read-only).
        
        Thread-safe read operation that returns the gauge if it exists,
        or None if it doesn't exist.
        
        Args:
            name: Gauge name to lookup
            labels: Optional labels to match (if None, returns first gauge with that name)
        
        Returns:
            Gauge instance if found, None otherwise
        
        Thread Safety:
            Protected by RLock - safe for concurrent access
        
        Purity:
            No side effects - does not create or modify anything
        """
        with self._lock:
            if labels is not None:
                # Exact match with labels
                key = self._make_key(name, labels)
                return self._gauges.get(key)
            else:
                # Return first gauge with matching name (for backward compatibility)
                for key, gauge in self._gauges.items():
                    if gauge.name == name:
                        return gauge
                return None
    
    def get_histogram(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[Histogram]:
        """
        Get histogram by name and optional labels (read-only).
        
        Thread-safe read operation that returns the histogram if it exists,
        or None if it doesn't exist.
        
        Args:
            name: Histogram name to lookup
            labels: Optional labels to match (if None, returns first histogram with that name)
        
        Returns:
            Histogram instance if found, None otherwise
        
        Thread Safety:
            Protected by RLock - safe for concurrent access
        
        Purity:
            No side effects - does not create or modify anything
        """
        with self._lock:
            if labels is not None:
                # Exact match with labels
                key = self._make_key(name, labels)
                return self._histograms.get(key)
            else:
                # Return first histogram with matching name (for backward compatibility)
                for key, histogram in self._histograms.items():
                    if histogram.name == name:
                        return histogram
                return None
    
    # ========================================================================
    # State Management - Atomic operations for state transitions
    # ========================================================================
    
    def reset(self) -> None:
        """
        Clear all metrics atomically.
        
        This is a destructive operation that removes all stored metrics.
        After reset, the store is in the same state as a new instance.
        
        Thread Safety:
            Protected by RLock - safe for concurrent access
        
        Atomicity:
            All dictionaries are cleared in a single atomic operation.
            If any part fails, the entire operation is rolled back.
        
        Determinism:
            After reset, the store always contains zero metrics.
        """
        with self._lock:
            try:
                # Store original state for rollback if needed
                original_counters = self._counters
                original_gauges = self._gauges
                original_histograms = self._histograms
                
                # Clear all metrics atomically
                self._counters = {}
                self._gauges = {}
                self._histograms = {}
                
                logger.debug("All metrics reset - store cleared")
                
            except Exception as e:
                # Rollback on any failure (though dict.clear() shouldn't fail)
                self._counters = original_counters
                self._gauges = original_gauges
                self._histograms = original_histograms
                
                logger.error(f"Failed to reset metrics store: {e}")
                raise
    
    def snapshot(self) -> Dict[str, Any]:
        """
        Create deep immutable snapshot of current state.
        
        Returns a deep copy of all metric data that cannot affect the store's
        internal state when modified. This is safe for serialization and
        external processing.
        
        Returns:
            Dictionary with structure:
            {
                "counters": {name: {"value": int, "labels": dict}},
                "gauges": {name: {"value": float, "labels": dict}},
                "histograms": {name: {"percentiles": dict, "count": int, "labels": dict}}
            }
        
        Thread Safety:
            Protected by RLock - safe for concurrent access
        
        Purity:
            No side effects - does not modify store state
        
        Immutability:
            Returned data is a deep copy - modifications won't affect store
        
        Performance:
            O(n) where n is the total number of metrics
        """
        with self._lock:
            try:
                # Use composite keys (name or name{labels}) for snapshot
                # This maintains backward compatibility while supporting labels
                snapshot_data = {
                    "counters": {
                        key: {
                            "value": counter.value,
                            "labels": deepcopy(counter.labels)
                        }
                        for key, counter in self._counters.items()
                    },
                    "gauges": {
                        key: {
                            "value": gauge.value,
                            "labels": deepcopy(gauge.labels)
                        }
                        for key, gauge in self._gauges.items()
                    },
                    "histograms": {
                        key: {
                            "percentiles": histogram.get_percentiles(),
                            "count": len(histogram.values),
                            "labels": deepcopy(histogram.labels)
                        }
                        for key, histogram in self._histograms.items()
                    }
                }
                
                logger.debug(f"Created snapshot with {len(self._counters)} counters, "
                           f"{len(self._gauges)} gauges, {len(self._histograms)} histograms")
                
                return snapshot_data
                
            except Exception as e:
                logger.error(f"Failed to create metrics snapshot: {e}")
                raise
    
    # ========================================================================
    # Introspection - For testing and debugging only
    # ========================================================================
    
    def _get_metric_counts(self) -> Dict[str, int]:
        """
        Get count of each metric type.
        
        This method is intended for testing and debugging only.
        It provides insight into the internal state without exposing
        the actual metric instances.
        
        Returns:
            Dictionary with counts: {"counters": int, "gauges": int, "histograms": int}
        
        Thread Safety:
            Protected by RLock - safe for concurrent access
        
        Note:
            This is a private method (prefixed with _) and should not be
            used in production code. It's provided for testing purposes only.
        """
        with self._lock:
            return {
                "counters": len(self._counters),
                "gauges": len(self._gauges),
                "histograms": len(self._histograms)
            }
    
    def _get_metric_names(self) -> Dict[str, List[str]]:
        """
        Get names of all metrics by type.
        
        This method is intended for testing and debugging only.
        
        Returns:
            Dictionary with metric names by type
        
        Thread Safety:
            Protected by RLock - safe for concurrent access
        """
        with self._lock:
            return {
                "counters": list(self._counters.keys()),
                "gauges": list(self._gauges.keys()),
                "histograms": list(self._histograms.keys())
            }
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        counts = self._get_metric_counts()
        return (f"MetricsStore(counters={counts['counters']}, "
                f"gauges={counts['gauges']}, histograms={counts['histograms']})")