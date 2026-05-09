"""
Prometheus Metrics for Knowledge Graph
======================================

Comprehensive monitoring and metrics collection for the knowledge graph system.
"""

import logging
import time
from typing import Dict, Optional, Callable
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Try to import prometheus_client, fallback to mock if not available
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        Info,
        generate_latest,
        REGISTRY,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("prometheus_client not installed, using mock metrics")
    PROMETHEUS_AVAILABLE = False
    
    # Mock classes for when prometheus is not available
    class MockMetric:
        def __init__(self, *args, **kwargs):
            pass
        
        def inc(self, *args, **kwargs):
            pass
        
        def dec(self, *args, **kwargs):
            pass
        
        def set(self, *args, **kwargs):
            pass
        
        def observe(self, *args, **kwargs):
            pass
        
        def labels(self, *args, **kwargs):
            return self
        
        def time(self):
            return self
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
    
    Counter = MockMetric
    Histogram = MockMetric
    Gauge = MockMetric
    Summary = MockMetric
    Info = MockMetric
    
    def generate_latest():
        return b""
    
    REGISTRY = None


# ============================================================================
# Graph Query Metrics
# ============================================================================

# Query duration histogram
graph_query_duration_seconds = Histogram(
    'graph_query_duration_seconds',
    'Duration of graph queries in seconds',
    ['operation', 'status'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Query counter
graph_query_total = Counter(
    'graph_query_total',
    'Total number of graph queries',
    ['operation', 'status']
)

# Slow query counter
graph_slow_query_total = Counter(
    'graph_slow_query_total',
    'Total number of slow queries (>5s)',
    ['operation']
)

# ============================================================================
# Graph Statistics Metrics
# ============================================================================

# Node count by type
graph_node_count = Gauge(
    'graph_node_count',
    'Number of nodes in the graph',
    ['node_type']
)

# Edge count by type
graph_edge_count = Gauge(
    'graph_edge_count',
    'Number of edges in the graph',
    ['edge_type']
)

# Total graph size
graph_total_nodes = Gauge(
    'graph_total_nodes',
    'Total number of nodes in the graph'
)

graph_total_edges = Gauge(
    'graph_total_edges',
    'Total number of edges in the graph'
)

# ============================================================================
# Error Metrics
# ============================================================================

# Error counter
graph_error_total = Counter(
    'graph_error_total',
    'Total number of graph errors',
    ['error_type', 'operation']
)

# Connection errors
graph_connection_error_total = Counter(
    'graph_connection_error_total',
    'Total number of connection errors'
)

# Timeout errors
graph_timeout_total = Counter(
    'graph_timeout_total',
    'Total number of query timeouts',
    ['operation']
)

# ============================================================================
# Enrichment Metrics
# ============================================================================

# Enrichment duration
graph_enrichment_duration_seconds = Histogram(
    'graph_enrichment_duration_seconds',
    'Duration of graph enrichment operations',
    ['enrichment_type'],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
)

# Enrichment counter
graph_enrichment_total = Counter(
    'graph_enrichment_total',
    'Total number of enrichment operations',
    ['enrichment_type', 'status']
)

# Cache metrics
graph_cache_hit_total = Counter(
    'graph_cache_hit_total',
    'Total number of cache hits',
    ['cache_type']
)

graph_cache_miss_total = Counter(
    'graph_cache_miss_total',
    'Total number of cache misses',
    ['cache_type']
)

# ============================================================================
# Import Metrics
# ============================================================================

# Import duration
graph_import_duration_seconds = Histogram(
    'graph_import_duration_seconds',
    'Duration of import operations',
    ['import_type'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0]
)

# Import counter
graph_import_total = Counter(
    'graph_import_total',
    'Total number of import operations',
    ['import_type', 'status']
)

# Imported items
graph_imported_items_total = Counter(
    'graph_imported_items_total',
    'Total number of imported items',
    ['item_type']
)

# ============================================================================
# Analytics Metrics
# ============================================================================

# PageRank calculation duration
graph_pagerank_duration_seconds = Histogram(
    'graph_pagerank_duration_seconds',
    'Duration of PageRank calculation',
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0]
)

# Community detection duration
graph_community_detection_duration_seconds = Histogram(
    'graph_community_detection_duration_seconds',
    'Duration of community detection',
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0]
)

# ============================================================================
# System Metrics
# ============================================================================

# Connection pool size
graph_connection_pool_size = Gauge(
    'graph_connection_pool_size',
    'Current connection pool size'
)

# Active connections
graph_active_connections = Gauge(
    'graph_active_connections',
    'Number of active connections'
)

# System info
graph_system_info = Info(
    'graph_system_info',
    'Information about the graph system'
)

# ============================================================================
# Helper Functions and Decorators
# ============================================================================

def track_query_duration(operation: str):
    """
    Decorator to track query duration
    
    Usage:
        @track_query_duration('find_articles')
        def find_articles(self, ...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                graph_error_total.labels(
                    error_type=type(e).__name__,
                    operation=operation
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                
                # Record duration
                graph_query_duration_seconds.labels(
                    operation=operation,
                    status=status
                ).observe(duration)
                
                # Count query
                graph_query_total.labels(
                    operation=operation,
                    status=status
                ).inc()
                
                # Track slow queries
                if duration > 5.0:
                    graph_slow_query_total.labels(operation=operation).inc()
                    logger.warning(
                        f"Slow query detected: {operation} took {duration:.2f}s"
                    )
        
        return wrapper
    return decorator


def track_enrichment_duration(enrichment_type: str):
    """
    Decorator to track enrichment duration
    
    Usage:
        @track_enrichment_duration('citation_network')
        async def analyze_citations(self, ...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                
                graph_enrichment_duration_seconds.labels(
                    enrichment_type=enrichment_type
                ).observe(duration)
                
                graph_enrichment_total.labels(
                    enrichment_type=enrichment_type,
                    status=status
                ).inc()
        
        return wrapper
    return decorator


@contextmanager
def track_operation(operation: str, metric_type: str = 'query'):
    """
    Context manager to track operation duration
    
    Usage:
        with track_operation('import_laws', 'import'):
            # do import
            pass
    """
    start_time = time.time()
    status = 'success'
    
    try:
        yield
    except Exception as e:
        status = 'error'
        graph_error_total.labels(
            error_type=type(e).__name__,
            operation=operation
        ).inc()
        raise
    finally:
        duration = time.time() - start_time
        
        if metric_type == 'query':
            graph_query_duration_seconds.labels(
                operation=operation,
                status=status
            ).observe(duration)
        elif metric_type == 'import':
            graph_import_duration_seconds.labels(
                import_type=operation
            ).observe(duration)


def update_graph_statistics(stats: Dict):
    """
    Update graph statistics metrics
    
    Args:
        stats: Dictionary with graph statistics
    """
    # Update node counts
    if 'nodes_by_type' in stats:
        for node_type, count in stats['nodes_by_type'].items():
            graph_node_count.labels(node_type=node_type).set(count)
    
    # Update edge counts
    if 'edges_by_type' in stats:
        for edge_type, count in stats['edges_by_type'].items():
            graph_edge_count.labels(edge_type=edge_type).set(count)
    
    # Update totals
    if 'total_nodes' in stats:
        graph_total_nodes.set(stats['total_nodes'])
    
    if 'total_edges' in stats:
        graph_total_edges.set(stats['total_edges'])


def record_cache_hit(cache_type: str = 'query'):
    """Record a cache hit"""
    graph_cache_hit_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str = 'query'):
    """Record a cache miss"""
    graph_cache_miss_total.labels(cache_type=cache_type).inc()


def record_import(item_type: str, count: int = 1):
    """Record imported items"""
    graph_imported_items_total.labels(item_type=item_type).inc(count)


def record_connection_error():
    """Record a connection error"""
    graph_connection_error_total.inc()


def record_timeout(operation: str):
    """Record a query timeout"""
    graph_timeout_total.labels(operation=operation).inc()


def update_connection_pool_metrics(pool_size: int, active: int):
    """Update connection pool metrics"""
    graph_connection_pool_size.set(pool_size)
    graph_active_connections.set(active)


def set_system_info(info: Dict):
    """Set system information"""
    if PROMETHEUS_AVAILABLE:
        graph_system_info.info(info)


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format"""
    if PROMETHEUS_AVAILABLE:
        return generate_latest(REGISTRY)
    return b""


# ============================================================================
# Metrics Collection Class
# ============================================================================

class GraphMetricsCollector:
    """
    Centralized metrics collector for the knowledge graph
    """
    
    def __init__(self, connection=None):
        """
        Initialize metrics collector
        
        Args:
            connection: Neo4j connection (optional)
        """
        self.connection = connection
        self.enabled = PROMETHEUS_AVAILABLE
        
        if not self.enabled:
            logger.warning("Prometheus metrics disabled (prometheus_client not installed)")
    
    def collect_graph_statistics(self):
        """Collect and update graph statistics"""
        if not self.connection:
            return
        
        try:
            # Get node counts
            node_query = """
            MATCH (n)
            WITH labels(n)[0] as label, count(n) as count
            RETURN label, count
            """
            
            node_results = self.connection.execute_query(node_query)
            
            nodes_by_type = {r['label']: r['count'] for r in node_results}
            total_nodes = sum(nodes_by_type.values())
            
            # Get edge counts
            edge_query = """
            MATCH ()-[r]->()
            WITH type(r) as type, count(r) as count
            RETURN type, count
            """
            
            edge_results = self.connection.execute_query(edge_query)
            
            edges_by_type = {r['type']: r['count'] for r in edge_results}
            total_edges = sum(edges_by_type.values())
            
            # Update metrics
            stats = {
                'nodes_by_type': nodes_by_type,
                'edges_by_type': edges_by_type,
                'total_nodes': total_nodes,
                'total_edges': total_edges,
            }
            
            update_graph_statistics(stats)
            
            logger.info(
                f"Updated graph statistics: {total_nodes} nodes, {total_edges} edges"
            )
            
            return stats
        
        except Exception as e:
            logger.error(f"Failed to collect graph statistics: {e}")
            return None
    
    def collect_connection_metrics(self):
        """Collect connection pool metrics"""
        if not self.connection:
            return
        
        try:
            # Get connection pool info (if available)
            # This depends on the Neo4j driver implementation
            pool_size = getattr(self.connection, 'pool_size', 0)
            active = getattr(self.connection, 'active_connections', 0)
            
            update_connection_pool_metrics(pool_size, active)
        
        except Exception as e:
            logger.error(f"Failed to collect connection metrics: {e}")
    
    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format"""
        return get_metrics()


# ============================================================================
# Convenience Functions
# ============================================================================

def initialize_metrics(connection=None, system_info: Optional[Dict] = None):
    """
    Initialize metrics system
    
    Args:
        connection: Neo4j connection
        system_info: System information dictionary
    """
    collector = GraphMetricsCollector(connection)
    
    # Set system info
    if system_info:
        set_system_info(system_info)
    
    # Collect initial statistics
    if connection:
        collector.collect_graph_statistics()
        collector.collect_connection_metrics()
    
    logger.info("Metrics system initialized")
    
    return collector
