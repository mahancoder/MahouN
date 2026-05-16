"""
Neo4j Connection Management
============================

Production-ready connection pooling with retry logic.
"""

import logging
import os
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from mahoun.core.governance.mutation_boundary import (
    MutationAuthorizationBoundary,
    GovernedNeo4jSession,
    MutationReceipt,
)
from mahoun.core.governance.validator_pipeline import ValidatorPipeline
from mahoun.core.governance.violations import GovernanceViolationError

_conn_logger = logging.getLogger(__name__)

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml: Optional[Any] = None
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
    Thread-safe Neo4j connection with connection pooling
    
    Features:
    - Thread-safe singleton pattern
    - Connection pooling
    - Automatic reconnection
    - Configuration from file or env
    - Health checks
    
    Note: This class uses a basic singleton pattern. For production use,
    prefer get_connection() which uses ThreadSafeSingleton.
    """
    
    _instance: Optional['Neo4jConnection'] = None
    _driver: Optional[Any] = None
    
    def __new__(cls, *args, **kwargs):
        # WARNING: This is NOT thread-safe!
        # Use get_connection() instead for thread-safe access
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
        # Only initialize once (Singleton pattern)
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # Load from config file if provided
        if config_path and os.path.exists(config_path) and HAS_YAML:
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
        
        # Fallback to environment variables (using secrets module for credentials)
        from mahoun.core.secrets import require_secret, get_secret
        
        uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = user or get_secret('NEO4J_USER', 'neo4j')
        password = password or require_secret('NEO4J_PASSWORD')
        
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
        self._initialized = True
        
        print(f"✅ Connected to Neo4j at {uri}")
    
    def verify_connection(self) -> bool:
        """
        Verify connection to Neo4j (synchronous)
        
        Returns:
            True if connection is valid, False otherwise
        """
        if self._driver is None:
             raise RuntimeError("Connection not initialized")
        return self.verify_connectivity()
    
    async def connect(self):
        """Asynchronous connection verification (Compatibility wrapper)"""
        return self.verify_connection()
    
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
    
    def _raw_execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Any]:
        """
        Internal execution method — calls MutationAuthorizationBoundary
        on EVERY query before reaching the driver.

        This is the single chokepoint for all Cypher execution.
        MutationAuthorizationBoundary.inspect() raises GovernanceViolationError
        if mutation Cypher is detected outside GovernedNeo4jSession.
        """
        MutationAuthorizationBoundary.inspect(query)
        with self.session(**kwargs) as s:
            result = s.run(query, parameters or {})
            return [record for record in result]

    @retry_on_failure(max_attempts=3)
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Any]:
        """
        Execute a READ-ONLY query.

        Mutation Cypher (MERGE/CREATE/DELETE/SET) will raise
        GovernanceViolationError unless called from GovernedNeo4jSession.
        Use governed_session() to perform any writes.

        Args:
            query: Cypher query (READ operations only)
            parameters: Query parameters

        Returns:
            Query results

        Raises:
            GovernanceViolationError: If mutation Cypher is detected.
        """
        return self._raw_execute(query, parameters, **kwargs)

    @contextmanager
    def governed_session(
        self,
        pipeline: Optional[ValidatorPipeline] = None,
        correlation_id: str = "",
    ) -> Generator[GovernedNeo4jSession, None, None]:
        """
        The ONLY authorized entry point for graph mutation.

        Yields a GovernedNeo4jSession which is the only surface that
        may execute mutation Cypher.  Direct execute_query() with
        MERGE/CREATE/DELETE/SET will raise GovernanceViolationError.

        Usage::

            with connection.governed_session(correlation_id="op-123") as session:
                session.write_node("Document", {"id": "d1", "provenance": {...}})
                session.write_relationship("Case", "c1", "CITES", "Law", "l1", {...})

        Args:
            pipeline: Optional ValidatorPipeline (creates default if None).
            correlation_id: Correlation ID for the session's audit trail.

        Yields:
            GovernedNeo4jSession
        """
        yield GovernedNeo4jSession(
            raw_executor=self._raw_execute,
            pipeline=pipeline,
            correlation_id=correlation_id,
        )
    
    def execute_write(self, *args, **kwargs):  # type: ignore[override]
        """
        REMOVED — constitutional violation.

        Direct execute_write() is forbidden. It bypasses the
        MutationAuthorizationBoundary. Use governed_session() instead.

        Raises:
            GovernanceViolationError: Always.
        """
        from mahoun.core.governance.violations import (
            GovernanceViolation, ViolationSeverity, ViolationCategory,
        )
        raise GovernanceViolationError(
            GovernanceViolation(
                category=ViolationCategory.ARCHITECTURE_BOUNDARY,
                severity=ViolationSeverity.CRITICAL,
                message=(
                    "execute_write() is constitutionally forbidden. "
                    "Use connection.governed_session() for all graph mutations."
                ),
                details={},
                source="Neo4jConnection.execute_write",
            )
        )
    
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
        results: List[Any] = []
        with self.session() as session:
            # Process in batches
            for i in range(0, len(queries), batch_size):
                batch = queries[i:i + batch_size]
                
                def batch_transaction(tx):
                    batch_results: List[Any] = []
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
    
    Uses Neo4j driver's built-in connection pooling for high-throughput scenarios.
    This is a lightweight wrapper that leverages the driver's native pool management.
    """
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        pool_size: int = 50,
        connection_timeout: float = 30.0,
        max_transaction_retry_time: float = 30.0,
        database: str = "neo4j",
        **kwargs
    ):
        """
        Initialize connection pool using Neo4j driver's native pooling
        
        Args:
            uri: Neo4j URI
            user: Username
            password: Password
            pool_size: Maximum connections in pool
            connection_timeout: Connection timeout in seconds
            max_transaction_retry_time: Max retry time for transactions
            database: Database name
            **kwargs: Additional connection arguments
        """
        try:
            from neo4j import GraphDatabase
        except ImportError:
            raise RuntimeError(
                "neo4j driver not installed. Run: pip install neo4j"
            )
        
        # Use driver's built-in connection pooling
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_pool_size=pool_size,
            connection_timeout=connection_timeout,
            max_transaction_retry_time=max_transaction_retry_time,
            **kwargs
        )
        self.database = database
        self.uri = uri
        
        print(f"✅ Connection pool initialized (max_size={pool_size}) at {uri}")
    
    @contextmanager
    def session(self, **kwargs):
        """
        Context manager for Neo4j session from pool
        
        Usage:
            with pool.session() as session:
                result = session.run(query)
        """
        session = self.driver.session(database=self.database, **kwargs)
        try:
            yield session
        finally:
            session.close()
    
    def close_all(self):
        """Close connection pool and all connections"""
        if self.driver:
            self.driver.close()
            print("✅ Connection pool closed")


# Thread-safe singleton for Neo4j connection
from mahoun.core.singleton import ThreadSafeSingleton

_neo4j_singleton = ThreadSafeSingleton["Neo4jConnection"]("Neo4jConnection")


def get_connection(
    uri: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs
) -> Neo4jConnection:
    """
    Get or create thread-safe global Neo4j connection
    
    This function uses ThreadSafeSingleton to ensure thread-safe access
    to the Neo4j connection across multiple threads.
    
    Args:
        uri: Neo4j URI
        user: Username
        password: Password
        **kwargs: Additional connection arguments
        
    Returns:
        Neo4jConnection instance (thread-safe singleton)
    """
    return _neo4j_singleton.get_instance(
        factory=lambda: Neo4jConnection(uri, user, password, **kwargs)
    )


# Alias for backward compatibility
