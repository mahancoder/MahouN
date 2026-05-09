#!/usr/bin/env python3
"""
Unit tests for IndexingService

Run with:
    pytest test_indexing.py -v
    python -m pytest test_indexing.py -v --asyncio-mode=auto
"""

import pytest
import asyncio

from .indexing import (
    IndexItem,
    IndexerAdapter,
    ChromaIndexerAdapter,
    BM25IndexerAdapter,
    Neo4jIndexerAdapter,
    Catalog,
    IndexingService,
    retry_with_backoff
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_items() -> List[IndexItem]:
    """Create sample IndexItems for testing"""
    items = []
    for i in range(5):
        item = IndexItem.from_chunk(
            doc_id=f"doc_{i}",
            chunk_id=f"chunk_{i}",
            content=f"Test content {i}",
            index_version="v1",
            lang="fa",
            labels={"category": "test"},
            entities=[{"text": f"entity_{i}", "label": "TEST"}],
            embedding_vec=[0.1] * 768
        )
        items.append(item)
    return items


@pytest.fixture
def mock_catalog():
    """Mock Catalog"""
    catalog = Mock(spec=Catalog)
    catalog.start_job = AsyncMock(return_value="test-job-id")
    catalog.log_items = AsyncMock()
    catalog.mark_applied = AsyncMock()
    catalog.commit_job = AsyncMock()
    catalog.fail_job = AsyncMock()
    return catalog


@pytest.fixture
def mock_adapter():
    """Mock IndexerAdapter"""
    adapter = Mock(spec=IndexerAdapter)
    adapter.name = "test_adapter"
    adapter.health = AsyncMock(return_value=True)
    adapter.upsert = AsyncMock()
    adapter.delete = AsyncMock()
    return adapter


@pytest.fixture
def mock_wandb_logger():
    """Mock WandBLogger"""
    logger = Mock()
    logger.log_metrics = Mock()
    return logger


# ============================================================================
# Test IndexItem
# ============================================================================

def test_index_item_creation():
    """Test IndexItem creation"""
    item = IndexItem.from_chunk(
        doc_id="doc_1",
        chunk_id="chunk_1",
        content="Test content",
        index_version="v1"
    )
    
    assert item.doc_id == "doc_1"
    assert item.chunk_id == "chunk_1"
    assert item.content == "Test content"
    assert item.index_version == "v1"
    assert item.content_hash  # Should be generated
    assert item.schema_hash  # Should be generated


def test_index_item_validation():
    """Test IndexItem validation"""
    # Valid item
    item = IndexItem(
        doc_id="doc_1",
        chunk_id="chunk_1",
        content="Test",
        content_hash="abc123",
        schema_hash="def456"
    )
    assert item.content_hash == "abc123"
    
    # Invalid hash (empty)
    with pytest.raises(ValueError):
        IndexItem(
            doc_id="doc_1",
            chunk_id="chunk_1",
            content="Test",
            content_hash="",
            schema_hash="def456"
        )


# ============================================================================
# Test Retry Logic
# ============================================================================

@pytest.mark.asyncio
async def test_retry_success():
    """Test retry with successful execution"""
    call_count = 0
    
    async def success_func():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = await retry_with_backoff(success_func, attempts=3)
    
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_eventual_success():
    """Test retry with eventual success"""
    call_count = 0
    
    async def eventual_success():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary error")
        return "success"
    
    result = await retry_with_backoff(eventual_success, attempts=3, base_delay=0.01)
    
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_failure():
    """Test retry with all attempts failing"""
    call_count = 0
    
    async def always_fail():
        nonlocal call_count
        call_count += 1
        raise Exception("Permanent error")
    
    with pytest.raises(Exception, match="Permanent error"):
        await retry_with_backoff(always_fail, attempts=3, base_delay=0.01)
    
    assert call_count == 3


# ============================================================================
# Test Adapters
# ============================================================================

@pytest.mark.asyncio
async def test_adapter_protocol(mock_adapter, sample_items):
    """Test adapter protocol"""
    # Health check
    assert await mock_adapter.health()
    
    # Upsert
    await mock_adapter.upsert(sample_items)
    mock_adapter.upsert.assert_called_once_with(sample_items)
    
    # Delete
    chunk_ids = [item.chunk_id for item in sample_items]
    await mock_adapter.delete(chunk_ids)
    mock_adapter.delete.assert_called_once_with(chunk_ids)


# ============================================================================
# Test Catalog
# ============================================================================

@pytest.mark.asyncio
async def test_catalog_job_lifecycle(mock_catalog, sample_items):
    """Test catalog job lifecycle"""
    # Start job
    job_id = await mock_catalog.start_job("incremental", "v1", {"test": True})
    assert job_id == "test-job-id"
    
    # Log items
    await mock_catalog.log_items(job_id, sample_items)
    mock_catalog.log_items.assert_called_once()
    
    # Mark applied
    await mock_catalog.mark_applied(job_id, ["chunk_1"], "test_adapter")
    mock_catalog.mark_applied.assert_called_once()
    
    # Commit job
    await mock_catalog.commit_job(job_id)
    mock_catalog.commit_job.assert_called_once_with(job_id)


@pytest.mark.asyncio
async def test_catalog_job_failure(mock_catalog):
    """Test catalog job failure"""
    job_id = await mock_catalog.start_job("incremental", "v1")
    
    # Fail job
    await mock_catalog.fail_job(job_id, "Test error")
    mock_catalog.fail_job.assert_called_once_with(job_id, "Test error")


# ============================================================================
# Test IndexingService
# ============================================================================

@pytest.mark.asyncio
async def test_indexing_service_build_success(
    mock_adapter,
    mock_catalog,
    mock_wandb_logger,
    sample_items
):
    """Test successful indexing"""
    # Create service
    service = IndexingService(
        adapters=[mock_adapter],
        catalog=mock_catalog,
        logger=mock_wandb_logger,
        batch_size=10
    )
    
    # Build index
    job_id = await service.build(
        items=sample_items,
        index_version="v1",
        mode="incremental"
    )
    
    # Verify
    assert job_id == "test-job-id"
    mock_catalog.start_job.assert_called_once()
    mock_catalog.log_items.assert_called_once()
    mock_catalog.commit_job.assert_called_once()
    mock_adapter.health.assert_called_once()
    mock_adapter.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_indexing_service_health_check_failure(
    mock_adapter,
    mock_catalog,
    mock_wandb_logger,
    sample_items
):
    """Test indexing with unhealthy adapter"""
    # Make adapter unhealthy
    mock_adapter.health = AsyncMock(return_value=False)
    
    service = IndexingService(
        adapters=[mock_adapter],
        catalog=mock_catalog,
        logger=mock_wandb_logger
    )
    
    # Should raise error
    with pytest.raises(RuntimeError, match="unhealthy"):
        await service.build(sample_items, "v1")
    
    # Job should be marked as failed
    mock_catalog.fail_job.assert_called_once()


@pytest.mark.asyncio
async def test_indexing_service_adapter_failure(
    mock_adapter,
    mock_catalog,
    mock_wandb_logger,
    sample_items
):
    """Test indexing with adapter failure"""
    # Make adapter fail on upsert
    mock_adapter.upsert = AsyncMock(side_effect=Exception("Adapter error"))
    
    service = IndexingService(
        adapters=[mock_adapter],
        catalog=mock_catalog,
        logger=mock_wandb_logger,
        retry_attempts=2
    )
    
    # Should raise error after retries
    with pytest.raises(Exception, match="Adapter error"):
        await service.build(sample_items, "v1")
    
    # Job should be marked as failed
    mock_catalog.fail_job.assert_called_once()


@pytest.mark.asyncio
async def test_indexing_service_batch_processing(
    mock_adapter,
    mock_catalog,
    mock_wandb_logger
):
    """Test batch processing"""
    # Create many items
    items = []
    for i in range(25):
        item = IndexItem.from_chunk(
            doc_id=f"doc_{i}",
            chunk_id=f"chunk_{i}",
            content=f"Content {i}",
            index_version="v1"
        )
        items.append(item)
    
    service = IndexingService(
        adapters=[mock_adapter],
        catalog=mock_catalog,
        logger=mock_wandb_logger,
        batch_size=10  # Process in batches of 10
    )
    
    await service.build(items, "v1")
    
    # Should be called 3 times (10 + 10 + 5)
    assert mock_adapter.upsert.call_count == 3


@pytest.mark.asyncio
async def test_indexing_service_empty_items(
    mock_adapter,
    mock_catalog,
    mock_wandb_logger
):
    """Test indexing with empty items"""
    service = IndexingService(
        adapters=[mock_adapter],
        catalog=mock_catalog,
        logger=mock_wandb_logger
    )
    
    job_id = await service.build([], "v1")
    
    # Should return empty job_id
    assert job_id == ""
    
    # Should not call catalog or adapters
    mock_catalog.start_job.assert_not_called()
    mock_adapter.upsert.assert_not_called()


@pytest.mark.asyncio
async def test_indexing_service_multiple_adapters(
    mock_catalog,
    mock_wandb_logger,
    sample_items
):
    """Test indexing with multiple adapters"""
    # Create multiple adapters
    adapter1 = Mock(spec=IndexerAdapter)
    adapter1.name = "adapter1"
    adapter1.health = AsyncMock(return_value=True)
    adapter1.upsert = AsyncMock()
    
    adapter2 = Mock(spec=IndexerAdapter)
    adapter2.name = "adapter2"
    adapter2.health = AsyncMock(return_value=True)
    adapter2.upsert = AsyncMock()
    
    service = IndexingService(
        adapters=[adapter1, adapter2],
        catalog=mock_catalog,
        logger=mock_wandb_logger
    )
    
    await service.build(sample_items, "v1")
    
    # Both adapters should be called
    adapter1.upsert.assert_called_once()
    adapter2.upsert.assert_called_once()
    
    # Catalog should track both
    assert mock_catalog.mark_applied.call_count == 2


# ============================================================================
# Integration Tests (require real databases)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_chroma_adapter(sample_items):
    """Test real ChromaDB adapter (requires ChromaDB)"""
    pytest.skip("Requires ChromaDB setup")
    
    # from embed_index import IncrementalIndexer
    # indexer = IncrementalIndexer(
    #     persist_dir="./test_chroma",
    #     collection_name="test"
    # )
    # adapter = ChromaIndexerAdapter(indexer)
    # 
    # assert await adapter.health()
    # await adapter.upsert(sample_items)
    # 
    # # Cleanup
    # import shutil
    # shutil.rmtree("./test_chroma")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_catalog(sample_items):
    """Test real PostgreSQL catalog (requires PostgreSQL)"""
    pytest.skip("Requires PostgreSQL setup")
    
    # import asyncpg
    # pool = await asyncpg.create_pool(
    #     dsn="postgresql://mahoun:mahoun@localhost:5432/mahoun_test"
    # )
    # catalog = Catalog(pool)
    # 
    # job_id = await catalog.start_job("test", "v1")
    # await catalog.log_items(job_id, sample_items)
    # await catalog.commit_job(job_id)
    # 
    # await pool.close()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
