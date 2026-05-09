"""
Neo4j Connection Management
============================

Production-ready connection pooling with retry logic.
"""


import os
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Optional, List, Tuple

import yaml


def retry_on_failure(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    max_backoff: float = 60.0
):
    """Decorator for retrying failed operations with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    
                    wait_time = min(backoff_factor ** attempt, max_backoff)
                    print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                    print(f"   Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
            
        return wrapper
    return decorator


class Neo4jConnection:
    """
    Singleton Neo4j connection with connection pooling
    
    Features:
    - Connection pooling
    - Automatic reconnection
    - Configuration from file or env
    - Health checks
    """
    
    _instance: Optional['Neo4jConnection'] = None
    _driver = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "neo4j",
        max_connection_pool_size: int = 50,
        connection_timeout: float = 30.0,
        max_transaction_retry_time: float = 30.0,
        config_path: Optional[str] = None
    ):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j URI (bolt://localhost:7687)
            user: Username
            password: Password
            database: Database name
            max_connection_pool_size: Max connections in pool
            connection_timeout: Connection timeout in seconds
            max_transaction_retry_time: Max retry time for transactions
            config_path: Path to config YAML file
        """
        # Only initialize once
        if self._driver is not None:
            return
            
        # Load from config file if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            uri = uri or config.get('uri')
            user = user or config.get('user')
            password = password or config.get('password')
            database = config.get('database', database)
            
            pool_config = config.get('connection_pool', {})
            max_connection_pool_size = pool_config.get('max_size', max_connection_pool_size)
            connection_timeout = pool_config.get('connection_timeout', connection_timeout)
            max_transaction_retry_time = pool_config.get(
                'max_transaction_retry_time',
                max_transaction_retry_time
            )
        
        # Fallback to environment variables
        uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = user or os.getenv('NEO4J_USER', 'neo4j')
        password = password or os.getenv('NEO4J_PASSWORD', 'neo4j')
        
        try:
            from neo4j import GraphDatabase
        except ImportError:
            raise RuntimeError(
                "neo4j driver not installed. Run: pip install neo4j"
            )
        
        self._driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_pool_size=max_connection_pool_size,
            connection_timeout=connection_timeout,
            max_transaction_retry_time=max_transaction_retry_time
        )
        
        self.database = database
        self.uri = uri
        
        print(f"✅ Connected to Neo4j at {uri}")
    
    @property
    def driver(self):
        """Get driver instance"""
        if self._driver is None:
            raise RuntimeError("Connection not initialized")
        return self._driver
    
    @contextmanager
    def session(self, **kwargs):
        """
        Context manager for Neo4j session
        
        Usage:
            with connection.session() as session:
                result = session.run(query)
        """
        session = self.driver.session(database=self.database, **kwargs)
        try:
            yield session
        finally:
            session.close()
    
    @retry_on_failure(max_attempts=3)
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Execute a query with retry logic
        
        Args:
            query: Cypher query
            parameters: Query parameters
            **kwargs: Additional session arguments
            
        Returns:
            Query result
        """
        with self.session(**kwargs) as session:
            result = session.run(query, parameters or {})
            return [record for record in result]
    
    @retry_on_failure(max_attempts=3)
    def execute_write(
        self,
        func: Callable,
        *args,
        **kwargs
    ):
        """
        Execute a write transaction with retry logic
        
        Args:
            func: Transaction function
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Transaction result
        """
        with self.session() as session:
            return session.execute_write(func, *args, **kwargs)
    
    @retry_on_failure(max_attempts=3)
    def execute_read(
        self,
        func: Callable,
        *args,
        **kwargs
    ):
        """
        Execute a read transaction with retry logic
        
        Args:
            func: Transaction function
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Transaction result
        """
        with self.session() as session:
            return session.execute_read(func, *args, **kwargs)
    
    @retry_on_failure(max_attempts=3)
    def execute_batch(
        self,
        queries: List[Tuple[str, Dict]],
        batch_size: int = 1000
    ) -> List:
        """
        Execute batch queries in a single transaction
        
        Args:
            queries: List of (query, parameters) tuples
            batch_size: Maximum queries per transaction
            
        Returns:
            List of results for each query
        """
        results = []
        
        with self.session() as session:
            # Process in batches
            for i in range(0, len(queries), batch_size):
                batch = queries[i:i + batch_size]
                
                def batch_transaction(tx):
                    batch_results = []
                    for query, params in batch:
                        result = tx.run(query, params or {})
                        batch_results.append([record for record in result])
                    return batch_results
                
                batch_results = session.execute_write(batch_transaction)
                results.extend(batch_results)
        
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Neo4j connection
        
        Returns:
            Dictionary with health status and metrics
        """
        health_status = {
            "status": "unhealthy",
            "connected": False,
            "response_time_ms": None,
            "node_count": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            # Test basic connectivity
            with self.session() as session:
                result = session.run("RETURN 1 AS num")
                if result.single()["num"] != 1:
                    health_status["error"] = "Unexpected query result"
                    return health_status
                
                # Get node count
                node_result = session.run("MATCH (n) RETURN count(n) AS count")
                node_count = node_result.single()["count"]
                
                response_time = (time.time() - start_time) * 1000
                
                health_status.update({
                    "status": "healthy",
                    "connected": True,
                    "response_time_ms": round(response_time, 2),
                    "node_count": node_count,
                    "database": self.database,
                    "uri": self.uri
                })
                
        except Exception as e:
            health_status["error"] = str(e)
        
        return health_status
    
    def verify_connectivity(self) -> bool:
        """Verify connection to Neo4j"""
        try:
            with self.session() as session:
                result = session.run("RETURN 1 AS num")
                return result.single()["num"] == 1
        except Exception as e:
            print(f"❌ Connection verification failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        with self.session() as session:
            # Node count
            node_result = session.run("MATCH (n) RETURN count(n) AS count")
            node_count = node_result.single()["count"]
            
            # Relationship count
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            rel_count = rel_result.single()["count"]
            
            # Labels
            label_result = session.run("CALL db.labels()")
            labels = [record["label"] for record in label_result]
            
            # Relationship types
            type_result = session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] for record in type_result]
            
            return {
                "node_count": node_count,
                "relationship_count": rel_count,
                "labels": labels,
                "relationship_types": rel_types,
                "database": self.database,
                "uri": self.uri
            }
    
    def close(self):
        """Close connection"""
        if self._driver:
            self._driver.close()
            self._driver = None
            print("✅ Neo4j connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class Neo4jConnectionPool:
    """
    Connection pool manager for Neo4j
    
    Manages multiple connections for high-throughput scenarios.
    """
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        pool_size: int = 10,
        **kwargs
    ):
        """
        Initialize connection pool
        
        Args:
            uri: Neo4j URI
            user: Username
            password: Password
            pool_size: Number of connections in pool
            **kwargs: Additional connection arguments
        """
        self.connections = []
        self.pool_size = pool_size
        self.current_idx = 0
        
        for _ in range(pool_size):
            conn = Neo4jConnection(uri, user, password, **kwargs)
            self.connections.append(conn)
    
    def get_connection(self) -> Neo4jConnection:
        """Get next connection from pool (round-robin)"""
        conn = self.connections[self.current_idx]
        self.current_idx = (self.current_idx + 1) % self.pool_size
        return conn
    
    def close_all(self):
        """Close all connections"""
        for conn in self.connections:
            conn.close()


# Global connection instance
_global_connection: Optional[Neo4jConnection] = None


def get_connection(
    uri: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs
) -> Neo4jConnection:
    """
    Get or create global Neo4j connection
    
    Args:
        uri: Neo4j URI
        user: Username
        password: Password
        **kwargs: Additional connection arguments
        
    Returns:
        Neo4jConnection instance
    """
    global _global_connection
    
    if _global_connection is None:
        _global_connection = Neo4jConnection(uri, user, password, **kwargs)
    
    return _global_connection


# Alias for backward compatibility
get_neo4j_driver = get_connection
