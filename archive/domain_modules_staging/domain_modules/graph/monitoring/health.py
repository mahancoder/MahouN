"""
Health Check System for Knowledge Graph
=======================================

Comprehensive health monitoring and status reporting.
"""

import logging
import time
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """
    Health check system for knowledge graph
    
    Monitors:
    - Neo4j connection
    - Graph statistics
    - Query performance
    - Data quality
    - System resources
    """
    
    def __init__(self, connection, query_service=None, analytics_service=None):
        """
        Initialize health check
        
        Args:
            connection: Neo4j connection
            query_service: GraphQueryService instance
            analytics_service: GraphAnalytics instance
        """
        self.connection = connection
        self.query_service = query_service
        self.analytics_service = analytics_service
        
        self.last_check_time = None
        self.last_check_result = None
    
    def check_connection(self) -> Dict:
        """
        Check Neo4j connection health
        
        Returns:
            Dictionary with connection status
        """
        try:
            start_time = time.time()
            
            # Simple query to test connection
            result = self.connection.execute_query("RETURN 1 as test")
            
            latency_ms = (time.time() - start_time) * 1000
            
            if result and result[0].get('test') == 1:
                status = HealthStatus.HEALTHY
                message = "Connection healthy"
            else:
                status = HealthStatus.DEGRADED
                message = "Connection degraded"
            
            return {
                'status': status.value,
                'message': message,
                'latency_ms': round(latency_ms, 2),
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Connection health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f"Connection failed: {str(e)}",
                'latency_ms': None,
                'timestamp': datetime.now().isoformat(),
            }
    
    def check_graph_statistics(self) -> Dict:
        """
        Check graph statistics
        
        Returns:
            Dictionary with graph statistics
        """
        try:
            # Get node count
            node_query = "MATCH (n) RETURN count(n) as count"
            node_result = self.connection.execute_query(node_query)
            node_count = node_result[0]['count'] if node_result else 0
            
            # Get edge count
            edge_query = "MATCH ()-[r]->() RETURN count(r) as count"
            edge_result = self.connection.execute_query(edge_query)
            edge_count = edge_result[0]['count'] if edge_result else 0
            
            # Determine status
            if node_count > 0 and edge_count > 0:
                status = HealthStatus.HEALTHY
                message = f"Graph contains {node_count} nodes and {edge_count} edges"
            elif node_count > 0:
                status = HealthStatus.DEGRADED
                message = f"Graph contains {node_count} nodes but no edges"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Graph is empty"
            
            return {
                'status': status.value,
                'message': message,
                'node_count': node_count,
                'edge_count': edge_count,
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Graph statistics check failed: {e}")
            return {
                'status': HealthStatus.UNKNOWN.value,
                'message': f"Failed to get statistics: {str(e)}",
                'node_count': None,
                'edge_count': None,
                'timestamp': datetime.now().isoformat(),
            }
    
    def check_query_performance(self) -> Dict:
        """
        Check query performance
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            # Test query performance
            queries = [
                ("simple_count", "MATCH (n) RETURN count(n) LIMIT 1"),
                ("node_lookup", "MATCH (n) RETURN n LIMIT 10"),
                ("relationship_query", "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 10"),
            ]
            
            results = {}
            total_time = 0
            
            for query_name, query in queries:
                start_time = time.time()
                try:
                    self.connection.execute_query(query)
                    duration_ms = (time.time() - start_time) * 1000
                    results[query_name] = round(duration_ms, 2)
                    total_time += duration_ms
                except Exception as e:
                    results[query_name] = f"error: {str(e)}"
            
            # Determine status based on average query time
            avg_time = total_time / len(queries)
            
            if avg_time < 100:
                status = HealthStatus.HEALTHY
                message = "Query performance is good"
            elif avg_time < 1000:
                status = HealthStatus.DEGRADED
                message = "Query performance is degraded"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Query performance is poor"
            
            return {
                'status': status.value,
                'message': message,
                'query_times_ms': results,
                'avg_time_ms': round(avg_time, 2),
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Query performance check failed: {e}")
            return {
                'status': HealthStatus.UNKNOWN.value,
                'message': f"Performance check failed: {str(e)}",
                'query_times_ms': {},
                'avg_time_ms': None,
                'timestamp': datetime.now().isoformat(),
            }
    
    def check_data_quality(self) -> Dict:
        """
        Check data quality
        
        Returns:
            Dictionary with data quality metrics
        """
        try:
            issues = []
            
            # Check for orphan nodes (nodes with no relationships)
            orphan_query = """
            MATCH (n)
            WHERE NOT (n)--()
            RETURN count(n) as count
            """
            orphan_result = self.connection.execute_query(orphan_query)
            orphan_count = orphan_result[0]['count'] if orphan_result else 0
            
            if orphan_count > 0:
                issues.append(f"{orphan_count} orphan nodes")
            
            # Check for nodes without required properties
            # (Example: Article nodes should have content)
            missing_props_query = """
            MATCH (a:Article)
            WHERE a.content IS NULL OR a.content = ''
            RETURN count(a) as count
            """
            try:
                missing_result = self.connection.execute_query(missing_props_query)
                missing_count = missing_result[0]['count'] if missing_result else 0
                
                if missing_count > 0:
                    issues.append(f"{missing_count} articles without content")
            except:
                pass  # Article label might not exist
            
            # Determine status
            if len(issues) == 0:
                status = HealthStatus.HEALTHY
                message = "Data quality is good"
            elif len(issues) <= 2:
                status = HealthStatus.DEGRADED
                message = f"Data quality issues: {', '.join(issues)}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Multiple data quality issues: {', '.join(issues)}"
            
            return {
                'status': status.value,
                'message': message,
                'issues': issues,
                'orphan_nodes': orphan_count,
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Data quality check failed: {e}")
            return {
                'status': HealthStatus.UNKNOWN.value,
                'message': f"Quality check failed: {str(e)}",
                'issues': [],
                'timestamp': datetime.now().isoformat(),
            }
    
    def check_embeddings(self) -> Dict:
        """
        Check embedding coverage
        
        Returns:
            Dictionary with embedding statistics
        """
        try:
            # Check nodes with embeddings
            embedding_query = """
            MATCH (n)
            WHERE n.embedding IS NOT NULL
            WITH labels(n)[0] as label, count(n) as with_embedding
            MATCH (m)
            WHERE labels(m)[0] = label
            WITH label, with_embedding, count(m) as total
            RETURN label, with_embedding, total,
                   toFloat(with_embedding) / total as coverage
            """
            
            results = self.connection.execute_query(embedding_query)
            
            coverage_by_type = {}
            total_coverage = 0
            
            for row in results:
                label = row['label']
                coverage = row['coverage']
                coverage_by_type[label] = {
                    'with_embedding': row['with_embedding'],
                    'total': row['total'],
                    'coverage': round(coverage * 100, 2)
                }
                total_coverage += coverage
            
            if results:
                avg_coverage = (total_coverage / len(results)) * 100
            else:
                avg_coverage = 0
            
            # Determine status
            if avg_coverage > 90:
                status = HealthStatus.HEALTHY
                message = f"Embedding coverage is good ({avg_coverage:.1f}%)"
            elif avg_coverage > 50:
                status = HealthStatus.DEGRADED
                message = f"Embedding coverage is partial ({avg_coverage:.1f}%)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Embedding coverage is low ({avg_coverage:.1f}%)"
            
            return {
                'status': status.value,
                'message': message,
                'avg_coverage_percent': round(avg_coverage, 2),
                'coverage_by_type': coverage_by_type,
                'timestamp': datetime.now().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Embedding check failed: {e}")
            return {
                'status': HealthStatus.UNKNOWN.value,
                'message': f"Embedding check failed: {str(e)}",
                'avg_coverage_percent': None,
                'timestamp': datetime.now().isoformat(),
            }
    
    def perform_full_check(self) -> Dict:
        """
        Perform full health check
        
        Returns:
            Complete health check report
        """
        logger.info("Performing full health check...")
        
        start_time = time.time()
        
        # Run all checks
        checks = {
            'connection': self.check_connection(),
            'graph_statistics': self.check_graph_statistics(),
            'query_performance': self.check_query_performance(),
            'data_quality': self.check_data_quality(),
            'embeddings': self.check_embeddings(),
        }
        
        # Determine overall status
        statuses = [check['status'] for check in checks.values()]
        
        if all(s == HealthStatus.HEALTHY.value for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY.value for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED.value for s in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNKNOWN
        
        duration_ms = (time.time() - start_time) * 1000
        
        result = {
            'overall_status': overall_status.value,
            'checks': checks,
            'check_duration_ms': round(duration_ms, 2),
            'timestamp': datetime.now().isoformat(),
        }
        
        self.last_check_time = datetime.now()
        self.last_check_result = result
        
        logger.info(f"Health check completed: {overall_status.value}")
        
        return result
    
    def get_last_check(self) -> Optional[Dict]:
        """Get last health check result"""
        return self.last_check_result


# ============================================================================
# Convenience Functions
# ============================================================================

def create_health_check(connection, query_service=None, analytics_service=None):
    """
    Create health check instance
    
    Args:
        connection: Neo4j connection
        query_service: GraphQueryService instance
        analytics_service: GraphAnalytics instance
    
    Returns:
        HealthCheck instance
    """
    return HealthCheck(connection, query_service, analytics_service)


def check_graph_health(connection) -> Dict:
    """
    Quick health check
    
    Args:
        connection: Neo4j connection
    
    Returns:
        Health check result
    """
    health_check = HealthCheck(connection)
    return health_check.perform_full_check()
