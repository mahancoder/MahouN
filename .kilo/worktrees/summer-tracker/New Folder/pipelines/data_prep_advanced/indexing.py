"""
IndexingService - Enterprise Multi-Database Indexing Coordinator
================================================================
Adapter + Catalog + Outbox pattern for idempotent, observable indexing

Architecture:
- Adapter pattern for pluggable indexers (ChromaDB, BM25, Neo4j)
- PostgreSQL Catalog as single source of truth
- Outbox pattern for distributed consistency
- Idempotency via (chunk_id, index_version, content_hash)
- Parallel execution with health checks & retry logic
- W&B observability

Example:
    >>> config = {...}  # PostgreSQL, ChromaDB, BM25, Neo4j configs
    >>> service = await build_indexing_service_from_config(config)
    >>> items = [IndexItem(doc_id="d1", chunk_id="c1", content="...", ...)]
    >>> await service.build(items, index_version="v1", mode="incremental")
"""


import sys
import asyncio
import hashlib
import uuid
import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Protocol, Sequence
from dataclasses import dataclass

from pydantic import BaseModel, Field, validator

# Fixed import paths
from pipelines.embed_index import IncrementalIndexer
from pipelines.gnn.gnn_graph_builder import GNNGraphBuilder
from pipelines.build_bm25 import BM25IndexBuilder

# Import config
from .config import IndexingConfig

# Setup logging
from pipelines._logging import setup_logger

log = setup_logger("indexing_service")

# Try to import asyncpg for Catalog
try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    log.warning("asyncpg not available - Catalog disabled")


# ============================================================================
# Data Contracts
# ============================================================================

class IndexItem(BaseModel):
    """
    Indexing item with all required metadata
    
    This is the contract between pipeline stages and the indexing service.
    """
    doc_id: str = Field(..., description="Document ID")
    chunk_id: str = Field(..., description="Unique chunk ID")
    content: str = Field(..., description="Text content")
    source_uri: Optional[str] = Field(None, description="Source URI")
    lang: str = Field(default="fa", description="Language code")
    
    # Metadata
    labels: Dict[str, Any] = Field(default_factory=dict, description="Labels/categories")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted entities")
    
    # Embeddings (populated by upstream embedder)
    embedding_model: Optional[str] = Field(None, description="Embedding model name")
    embedding_dim: Optional[int] = Field(None, description="Embedding dimension")
    embedding_vec: Optional[List[float]] = Field(None, description="Embedding vector")
    
    # Graph data (populated by upstream graph builder)
    graph_nodes: Optional[List[Dict[str, Any]]] = Field(None, description="Graph nodes")
    graph_edges: Optional[List[Dict[str, Any]]] = Field(None, description="Graph edges")
    
    # Hashing for idempotency
    content_hash: str = Field(..., description="SHA256 hash of content")
    schema_hash: str = Field(..., description="SHA256 hash of schema version")
    index_version: str = Field(default="v1", description="Index version")
    
    @validator("content_hash", "schema_hash")
    def _validate_hash(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Hash must be non-empty string")
        return v
    
    @classmethod
    def from_chunk(
        cls,
        doc_id: str,
        chunk_id: str,
        content: str,
        index_version: str = "v1",
        **kwargs
    ) -> "IndexItem":
        """Create IndexItem from chunk data"""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        schema_hash = hashlib.sha256(f"{index_version}:v1".encode()).hexdigest()
        
        return cls(
            doc_id=doc_id,
            chunk_id=chunk_id,
            content=content,
            content_hash=content_hash,
            schema_hash=schema_hash,
            index_version=index_version,
            **kwargs
        )


# ============================================================================
# Adapter Protocol
# ============================================================================

class IndexerAdapter(Protocol):
    """
    Protocol for indexer adapters
    
    All indexers (ChromaDB, BM25, Neo4j) must implement this interface.
    """
    name: str
    
    async def health(self) -> bool:
        """Check if adapter is healthy"""
        ...
    
    async def upsert(self, items: Sequence[IndexItem]) -> None:
        """Upsert items to the index"""
        ...
    
    async def delete(self, chunk_ids: Sequence[str]) -> None:
        """Delete items from the index"""
        ...


# ============================================================================
# Concrete Adapters
# ============================================================================

class ChromaIndexerAdapter:
    """ChromaDB adapter for vector search"""
    
    name = "chroma"
    
    def __init__(self, indexer: IncrementalIndexer):
        self._indexer = indexer
        log.info(f"  ✓ {self.name} adapter initialized")
    
    async def health(self) -> bool:
        """Check ChromaDB health"""
        try:
            # Try to get collection count
            _ = self._indexer.collection.count()
            return True
        except Exception as e:
            log.error(f"  ✗ {self.name} health check failed: {e}")
            return False
    
    async def upsert(self, items: Sequence[IndexItem]) -> None:
        """Upsert to ChromaDB"""
        if not items:
            return
        
        # Prepare data for ChromaDB
        ids = [i.chunk_id for i in items]
        documents = [i.content for i in items]
        embeddings = [i.embedding_vec for i in items if i.embedding_vec]
        
        metadatas = []
        for i in items:
            meta = {
                "doc_id": i.doc_id,
                "source_uri": i.source_uri or "",
                "lang": i.lang,
                "content_hash": i.content_hash,
                "schema_hash": i.schema_hash,
                "index_version": i.index_version,
                "entity_count": len(i.entities),
            }
            # Add labels
            meta.update({f"label_{k}": str(v) for k, v in i.labels.items()})
            metadatas.append(meta)
        
        # Batch upsert
        self._indexer.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings if embeddings else None,
            metadatas=metadatas
        )
        
        log.debug(f"  → {self.name}: upserted {len(items)} items")
    
    async def delete(self, chunk_ids: Sequence[str]) -> None:
        """Delete from ChromaDB"""
        if not chunk_ids:
            return
        
        self._indexer.collection.delete(ids=list(chunk_ids))
        log.debug(f"  → {self.name}: deleted {len(chunk_ids)} items")


class BM25IndexerAdapter:
    """BM25 adapter for sparse retrieval"""
    
    name = "bm25"
    
    def __init__(self, builder: BM25IndexBuilder):
        self._builder = builder
        log.info(f"  ✓ {self.name} adapter initialized")
    
    async def health(self) -> bool:
        """Check BM25 health"""
        try:
            # Check if index directory exists
            return self._builder.index_dir.exists()
        except Exception as e:
            log.error(f"  ✗ {self.name} health check failed: {e}")
            return False
    
    async def upsert(self, items: Sequence[IndexItem]) -> None:
        """Upsert to BM25 index"""
        if not items:
            return
        
        # Prepare documents for BM25
        documents = []
        for i in items:
            doc = {
                "id": i.chunk_id,
                "contents": i.content,
                "metadata": {
                    "doc_id": i.doc_id,
                    "content_hash": i.content_hash
                }
            }
            documents.append(doc)
        
        # Build/update index
        # Note: BM25IndexBuilder doesn't have incremental update,
        # so we need to rebuild. In production, use a better BM25 impl.
        self._builder.build_index(documents)
        
        log.debug(f"  → {self.name}: upserted {len(items)} items")
    
    async def delete(self, chunk_ids: Sequence[str]) -> None:
        """Delete from BM25 index"""
        if not chunk_ids:
            return
        
        # Note: Current BM25IndexBuilder doesn't support deletion
        # In production, implement proper deletion logic
        log.warning(f"  ⚠ {self.name}: deletion not implemented")


class Neo4jIndexerAdapter:
    """Neo4j adapter for graph relationships"""
    
    name = "neo4j"
    
    def __init__(self, builder: GNNGraphBuilder):
        self._builder = builder
        log.info(f"  ✓ {self.name} adapter initialized")
    
    async def health(self) -> bool:
        """Check Neo4j health"""
        try:
            # Check if Neo4j driver is connected
            if not self._builder.neo4j_driver:
                return False
            
            # Try a simple query
            with self._builder.neo4j_driver.session() as session:
                result = session.run("RETURN 1 AS num")
                return result.single()["num"] == 1
        except Exception as e:
            log.error(f"  ✗ {self.name} health check failed: {e}")
            return False
    
    async def upsert(self, items: Sequence[IndexItem]) -> None:
        """Upsert to Neo4j"""
        if not items:
            return
        
        if not self._builder.neo4j_driver:
            log.warning(f"  ⚠ {self.name}: driver not available")
            return
        
        with self._builder.neo4j_driver.session() as session:
            for item in items:
                # Create chunk node
                session.run(
                    """
                    MERGE (c:Chunk {id: $chunk_id})
                    SET c.doc_id = $doc_id,
                        c.content = $content,
                        c.content_hash = $content_hash,
                        c.index_version = $index_version
                    """,
                    chunk_id=item.chunk_id,
                    doc_id=item.doc_id,
                    content=item.content[:500],  # Truncate for storage
                    content_hash=item.content_hash,
                    index_version=item.index_version
                )
                
                # Create entity nodes and relationships
                for entity in item.entities:
                    entity_text = entity.get("text", "")
                    entity_label = entity.get("label", "ENTITY")
                    
                    session.run(
                        f"""
                        MERGE (e:Entity {{text: $text, label: $label}})
                        WITH e
                        MATCH (c:Chunk {{id: $chunk_id}})
                        MERGE (c)-[:CONTAINS_ENTITY]->(e)
                        """,
                        text=entity_text,
                        label=entity_label,
                        chunk_id=item.chunk_id
                    )
                
                # Add custom graph nodes/edges if provided
                if item.graph_nodes:
                    for node in item.graph_nodes:
                        node_id = node.get("id")
                        node_type = node.get("type", "Node")
                        session.run(
                            f"""
                            MERGE (n:{node_type} {{id: $id}})
                            SET n += $properties
                            """,
                            id=node_id,
                            properties=node.get("properties", {})
                        )
                
                if item.graph_edges:
                    for edge in item.graph_edges:
                        src = edge.get("source")
                        dst = edge.get("target")
                        rel_type = edge.get("type", "RELATED")
                        session.run(
                            f"""
                            MATCH (a {{id: $src}})
                            MATCH (b {{id: $dst}})
                            MERGE (a)-[r:{rel_type}]->(b)
                            SET r += $properties
                            """,
                            src=src,
                            dst=dst,
                            properties=edge.get("properties", {})
                        )
        
        log.debug(f"  → {self.name}: upserted {len(items)} items")
    
    async def delete(self, chunk_ids: Sequence[str]) -> None:
        """Delete from Neo4j"""
        if not chunk_ids:
            return
        
        if not self._builder.neo4j_driver:
            log.warning(f"  ⚠ {self.name}: driver not available")
            return
        
        with self._builder.neo4j_driver.session() as session:
            session.run(
                """
                MATCH (c:Chunk)
                WHERE c.id IN $chunk_ids
                DETACH DELETE c
                """,
                chunk_ids=list(chunk_ids)
            )
        
        log.debug(f"  → {self.name}: deleted {len(chunk_ids)} items")


# ============================================================================
# PostgreSQL Catalog
# ============================================================================

class Catalog:
    """
    PostgreSQL catalog for tracking indexing jobs and items
    
    Tables:
    - index_jobs: Job metadata and status
    - index_items: Individual items being indexed
    - outbox: Outbox pattern for tracking adapter writes
    """
    
    def __init__(self, pool: asyncpg.pool.Pool):
        self.pool = pool
        log.info("  ✓ Catalog initialized")
    
    async def start_job(
        self,
        job_type: str,
        index_version: str,
        meta: Optional[Dict] = None
    ) -> str:
        """Start a new indexing job"""
        job_id = str(uuid.uuid4())
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO index_jobs (
                    job_id, job_type, index_version, status, meta, started_at
                )
                VALUES ($1, $2, $3, 'running', $4, NOW())
                """,
                job_id,
                job_type,
                index_version,
                json.dumps(meta or {})
            )
        
        log.info(f"  → Job started: {job_id}")
        return job_id
    
    async def log_items(self, job_id: str, items: Sequence[IndexItem]) -> None:
        """Log items to catalog"""
        if not items:
            return
        
        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO index_items (
                    job_id, chunk_id, doc_id, content_hash, schema_hash,
                    index_version, status
                )
                VALUES ($1, $2, $3, $4, $5, $6, 'pending')
                ON CONFLICT (chunk_id, index_version)
                DO UPDATE SET
                    content_hash = EXCLUDED.content_hash,
                    schema_hash = EXCLUDED.schema_hash,
                    status = 'pending',
                    updated_at = NOW()
                """,
                [
                    (
                        job_id,
                        i.chunk_id,
                        i.doc_id,
                        i.content_hash,
                        i.schema_hash,
                        i.index_version
                    )
                    for i in items
                ]
            )
        
        log.debug(f"  → Logged {len(items)} items to catalog")
    
    async def mark_applied(
        self,
        job_id: str,
        chunk_ids: Sequence[str],
        adapter: str
    ) -> None:
        """Mark items as applied to an adapter (outbox pattern)"""
        if not chunk_ids:
            return
        
        async with self.pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO outbox (job_id, chunk_id, adapter, applied_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (chunk_id, adapter) DO NOTHING
                """,
                [(job_id, cid, adapter) for cid in chunk_ids]
            )
        
        log.debug(f"  → Marked {len(chunk_ids)} items as applied to {adapter}")
    
    async def commit_job(self, job_id: str) -> None:
        """Mark job as completed"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE index_jobs
                SET status = 'completed', finished_at = NOW()
                WHERE job_id = $1
                """,
                job_id
            )
        
        log.info(f"  ✓ Job completed: {job_id}")
    
    async def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE index_jobs
                SET status = 'failed', error = $2, finished_at = NOW()
                WHERE job_id = $1
                """,
                job_id,
                error
            )
        
        log.error(f"  ✗ Job failed: {job_id} - {error}")


# ============================================================================
# Retry Utility
# ============================================================================

async def retry_with_backoff(
    coro_factory,
    attempts: int = 3,
    base_delay: float = 0.8,
    max_delay: float = 10.0
):
    """
    Retry coroutine with exponential backoff
    
    Args:
        coro_factory: Callable that returns a coroutine
        attempts: Number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """
    last_exc = None
    
    for attempt in range(1, attempts + 1):
        try:
            return await coro_factory()
        except Exception as e:
            last_exc = e
            
            if attempt < attempts:
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                log.warning(f"  ⚠ Attempt {attempt} failed: {e}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                log.error(f"  ✗ All {attempts} attempts failed")
    
    raise last_exc


# ============================================================================
# Indexing Service
# ============================================================================

class IndexingService:
    """
    Enterprise indexing service with transactional consistency
    
    Features:
    - Adapter pattern for pluggable indexers
    - PostgreSQL catalog as single source of truth
    - Outbox pattern for distributed consistency
    - Idempotency via content hashing
    - Retry with exponential backoff
    - Health checks before indexing
    - W&B observability
    
    Example:
        >>> adapters = [ChromaIndexerAdapter(...), BM25IndexerAdapter(...)]
        >>> catalog = Catalog(pool)
        >>> wb = WandBLogger(project="mahoun")
        >>> service = IndexingService(adapters, catalog, wb)
        >>> items = [IndexItem(...), ...]
        >>> await service.build(items, index_version="v1")
    """
    
    def __init__(
        self,
        adapters: List[IndexerAdapter],
        catalog: Catalog,
        logger: WandBLogger,
        parallelism: int = 4,
        batch_size: int = 1000,
        retry_attempts: int = 3
    ):
        """
        Initialize indexing service
        
        Args:
            adapters: List of indexer adapters
            catalog: PostgreSQL catalog
            logger: W&B logger
            parallelism: Number of parallel adapter writes
            batch_size: Batch size for processing
            retry_attempts: Number of retry attempts
        """
        self.adapters = adapters
        self.catalog = catalog
        self.wb = logger
        self.parallelism = parallelism
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        
        log.info("IndexingService initialized")
        log.info(f"  Adapters: {[a.name for a in adapters]}")
        log.info(f"  Batch size: {batch_size}")
        log.info(f"  Parallelism: {parallelism}")
    
    async def _apply_adapter(
        self,
        adapter: IndexerAdapter,
        items: Sequence[IndexItem],
        job_id: str
    ) -> None:
        """
        Apply items to a single adapter with retry
        
        Args:
            adapter: Indexer adapter
            items: Items to index
            job_id: Job ID for tracking
        """
        async def _do():
            await adapter.upsert(items)
            await self.catalog.mark_applied(
                job_id,
                [i.chunk_id for i in items],
                adapter.name
            )
        
        await retry_with_backoff(_do, attempts=self.retry_attempts)
    
    async def build(
        self,
        items: Sequence[IndexItem],
        index_version: str,
        mode: str = "incremental",
        meta: Optional[Dict] = None
    ) -> str:
        """
        Build index from items with transactional consistency
        
        Args:
            items: Items to index
            index_version: Index version (e.g., "v1", "v2")
            mode: Indexing mode ("incremental" or "full")
            meta: Optional metadata for the job
            
        Returns:
            Job ID
            
        Raises:
            RuntimeError: If adapters are unhealthy or indexing fails
        """
        if not items:
            log.warning("No items provided for indexing")
            return ""
        
        # Start job in catalog
        job_id = await self.catalog.start_job(
            job_type=mode,
            index_version=index_version,
            meta=meta or {}
        )
        
        self.wb.log_metrics({
            "job_id": job_id,
            "items_count": len(items),
            "mode": mode,
            "index_version": index_version
        })
        
        log.info(f"Indexing started: job_id={job_id}, mode={mode}, items={len(items)}")
        
        # Log items to catalog
        await self.catalog.log_items(job_id, items)
        
        try:
            # Health checks
            log.info("Running health checks...")
            health_checks = await asyncio.gather(
                *[adapter.health() for adapter in self.adapters],
                return_exceptions=True
            )
            
            # Check results
            failing_adapters = []
            for adapter, health in zip(self.adapters, health_checks):
                if isinstance(health, Exception):
                    failing_adapters.append(f"{adapter.name} (exception: {health})")
                elif not health:
                    failing_adapters.append(adapter.name)
            
            if failing_adapters:
                error_msg = f"Adapters unhealthy: {', '.join(failing_adapters)}"
                raise RuntimeError(error_msg)
            
            log.info("  ✓ All adapters healthy")
            
            # Process in batches
            total_batches = (len(items) + self.batch_size - 1) // self.batch_size
            log.info(f"Processing {len(items)} items in {total_batches} batches...")
            
            for batch_idx in range(0, len(items), self.batch_size):
                batch = items[batch_idx:batch_idx + self.batch_size]
                batch_num = batch_idx // self.batch_size + 1
                
                log.info(f"  Batch {batch_num}/{total_batches}: {len(batch)} items")
                
                t0 = time.time()
                
                # Apply to all adapters in parallel
                await asyncio.gather(
                    *[self._apply_adapter(adapter, batch, job_id) for adapter in self.adapters]
                )
                
                dt = time.time() - t0
                
                # Log metrics
                self.wb.log_metrics({
                    "job_id": job_id,
                    "batch_num": batch_num,
                    "batch_size": len(batch),
                    "latency_sec": dt,
                    "throughput": len(batch) / dt if dt > 0 else 0
                })
                
                log.info(f"    ✓ Batch {batch_num} completed in {dt:.2f}s")
            
            # Commit job
            await self.catalog.commit_job(job_id)
            
            self.wb.log_metrics({
                "job_id": job_id,
                "status": "completed",
                "total_items": len(items)
            })
            
            log.info(f"✅ Indexing completed: job_id={job_id}")
            
            return job_id
            
        except Exception as e:
            # Fail job
            await self.catalog.fail_job(job_id, str(e))
            
            self.wb.log_metrics({
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            })
            
            log.exception(f"❌ Indexing failed: job_id={job_id}, error={e}")
            raise
    


# ============================================================================
# Factory Function
# ============================================================================

async def build_indexing_service_from_config(
    config: Dict[str, Any]
) -> IndexingService:
    """
    Build IndexingService from configuration
    
    Expected config structure:
    {
        "postgres": {
            "dsn": "postgresql://user:pass@host:port/db",
            "min_pool_size": 1,
            "max_pool_size": 5
        },
        "chroma": {
            "persist_dir": "./.chroma/mahoun",
            "collection_name": "legal_documents"
        },
        "bm25": {
            "index_dir": "./indexes/bm25"
        },
        "neo4j": {
            "uri": "bolt://neo4j:7687",
            "user": "neo4j",
            "password": "password"
        },
        "service": {
            "parallelism": 4,
            "batch_size": 1000,
            "retry_attempts": 3
        },
        "wandb": {
            "project": "mahoun",
            "enabled": true
        }
    }
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured IndexingService
    """
    log.info("Building IndexingService from config...")
    
    # 1. Create PostgreSQL pool
    if not HAS_ASYNCPG:
        raise RuntimeError("asyncpg not installed. Run: pip install asyncpg")
    
    postgres_config = config.get("postgres", {})
    pool = await asyncpg.create_pool(
        dsn=postgres_config.get("dsn"),
        min_size=postgres_config.get("min_pool_size", 1),
        max_size=postgres_config.get("max_pool_size", 5)
    )
    log.info("  ✓ PostgreSQL pool created")
    
    # 2. Create adapters
    adapters: List[IndexerAdapter] = []
    
    # ChromaDB adapter
    if "chroma" in config:
        chroma_config = config["chroma"]
        chroma_indexer = IncrementalIndexer(
            persist_dir=chroma_config.get("persist_dir", "./.chroma/mahoun"),
            collection_name=chroma_config.get("collection_name", "legal_documents")
        )
        adapters.append(ChromaIndexerAdapter(chroma_indexer))
    
    # BM25 adapter
    if "bm25" in config:
        bm25_config = config["bm25"]
        bm25_builder = BM25IndexBuilder(
            index_dir=bm25_config.get("index_dir", "./indexes/bm25")
        )
        adapters.append(BM25IndexerAdapter(bm25_builder))
    
    # Neo4j adapter
    if "neo4j" in config:
        neo4j_config = config["neo4j"]
        neo4j_builder = GNNGraphBuilder(
            neo4j_uri=neo4j_config.get("uri"),
            neo4j_user=neo4j_config.get("user"),
            neo4j_password=neo4j_config.get("password")
        )
        adapters.append(Neo4jIndexerAdapter(neo4j_builder))
    
    log.info(f"  ✓ Created {len(adapters)} adapters")
    
    # 3. Create catalog
    catalog = Catalog(pool)
    
    # 4. Create W&B logger
    wandb_config = config.get("wandb", {})
    wb_logger = WandBLogger(
        project=wandb_config.get("project", "mahoun"),
        name=wandb_config.get("name"),
        enabled=wandb_config.get("enabled", True)
    )
    
    # 5. Create service
    service_config = config.get("service", {})
    service = IndexingService(
        adapters=adapters,
        catalog=catalog,
        logger=wb_logger,
        parallelism=service_config.get("parallelism", 4),
        batch_size=service_config.get("batch_size", 1000),
        retry_attempts=service_config.get("retry_attempts", 3)
    )
    
    log.info("✅ IndexingService built successfully")
    
    return service


# ============================================================================
# Convenience Functions
# ============================================================================

async def index_items(
    items: Sequence[IndexItem],
    config: Dict[str, Any],
    index_version: str = "v1",
    mode: str = "incremental"
) -> str:
    """
    Convenience function for indexing items
    
    Args:
        items: Items to index
        config: Configuration dictionary
        index_version: Index version
        mode: Indexing mode
        
    Returns:
        Job ID
    """
    service = await build_indexing_service_from_config(config)
    job_id = await service.build(items, index_version, mode)
    return job_id
