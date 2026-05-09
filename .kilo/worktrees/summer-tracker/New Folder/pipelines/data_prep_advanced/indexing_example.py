#!/usr/bin/env python3
"""
Example usage of the enterprise IndexingService

This demonstrates how to use the new IndexingService with:
- Adapter pattern
- PostgreSQL catalog
- Outbox pattern
- Idempotency
- Retry logic
"""

import asyncio
from typing import List
from .indexing import (
    IndexItem,
    build_indexing_service_from_config,
    index_items
)


# ============================================================================
# Example 1: Basic Usage
# ============================================================================

async def example_basic():
    """Basic indexing example"""
    
    print("=" * 60)
    print("Example 1: Basic Indexing")
    print("=" * 60)
    
    # Configuration
    config = {
        "postgres": {
            "dsn": "postgresql://mahoun:mahoun@localhost:5432/mahoun"
        },
        "chroma": {
            "persist_dir": "./.chroma/mahoun",
            "collection_name": "legal_documents"
        },
        "bm25": {
            "index_dir": "./indexes/bm25"
        },
        "neo4j": {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "mahoun2024"
        },
        "service": {
            "parallelism": 4,
            "batch_size": 100,
            "retry_attempts": 3
        },
        "wandb": {
            "project": "mahoun-indexing",
            "enabled": False  # Disable for example
        }
    }
    
    # Create sample items
    items = []
    for i in range(10):
        content = f"این یک متن نمونه قانونی است. شماره {i}"
        
        item = IndexItem.from_chunk(
            doc_id=f"doc_{i // 3}",  # 3 chunks per doc
            chunk_id=f"chunk_{i}",
            content=content,
            index_version="v1",
            lang="fa",
            labels={"category": "قانون مدنی", "section": f"بخش {i}"},
            entities=[
                {"text": f"ماده {i}", "label": "ARTICLE"},
                {"text": "قانون مدنی", "label": "LAW_NAME"}
            ],
            embedding_vec=[0.1] * 768  # Dummy embedding
        )
        items.append(item)
    
    print(f"\nCreated {len(items)} items")
    
    # Build service
    service = await build_indexing_service_from_config(config)
    
    # Index items
    job_id = await service.build(
        items=items,
        index_version="v1",
        mode="incremental",
        meta={"source": "example", "batch": "1"}
    )
    
    print(f"\n✅ Indexing completed: job_id={job_id}")


# ============================================================================
# Example 2: Convenience Function
# ============================================================================

async def example_convenience():
    """Using convenience function"""
    
    print("\n" + "=" * 60)
    print("Example 2: Convenience Function")
    print("=" * 60)
    
    config = {
        "postgres": {"dsn": "postgresql://mahoun:mahoun@localhost:5432/mahoun"},
        "chroma": {"persist_dir": "./.chroma/mahoun"},
        "wandb": {"enabled": False}
    }
    
    # Create items
    items = [
        IndexItem.from_chunk(
            doc_id="doc_1",
            chunk_id="chunk_1",
            content="محتوای قانونی نمونه",
            index_version="v1"
        )
    ]
    
    # Index using convenience function
    job_id = await index_items(items, config, index_version="v1")
    
    print(f"\n✅ Job ID: {job_id}")


# ============================================================================
# Example 3: Batch Processing
# ============================================================================

async def example_batch():
    """Batch processing with large dataset"""
    
    print("\n" + "=" * 60)
    print("Example 3: Batch Processing")
    print("=" * 60)
    
    config = {
        "postgres": {"dsn": "postgresql://mahoun:mahoun@localhost:5432/mahoun"},
        "chroma": {"persist_dir": "./.chroma/mahoun"},
        "service": {
            "batch_size": 50,  # Process 50 items at a time
            "parallelism": 4
        },
        "wandb": {"enabled": False}
    }
    
    # Create large dataset
    items = []
    for i in range(500):
        item = IndexItem.from_chunk(
            doc_id=f"doc_{i // 10}",
            chunk_id=f"chunk_{i}",
            content=f"محتوای قانونی شماره {i}",
            index_version="v1",
            embedding_vec=[0.1] * 768
        )
        items.append(item)
    
    print(f"\nProcessing {len(items)} items in batches of 50...")
    
    service = await build_indexing_service_from_config(config)
    job_id = await service.build(items, index_version="v1")
    
    print(f"\n✅ Processed {len(items)} items: job_id={job_id}")


# ============================================================================
# Example 4: Idempotency Test
# ============================================================================

async def example_idempotency():
    """Test idempotency - indexing same items twice"""
    
    print("\n" + "=" * 60)
    print("Example 4: Idempotency Test")
    print("=" * 60)
    
    config = {
        "postgres": {"dsn": "postgresql://mahoun:mahoun@localhost:5432/mahoun"},
        "chroma": {"persist_dir": "./.chroma/mahoun"},
        "wandb": {"enabled": False}
    }
    
    # Create items
    items = [
        IndexItem.from_chunk(
            doc_id="doc_test",
            chunk_id="chunk_test",
            content="محتوای تست",
            index_version="v1"
        )
    ]
    
    service = await build_indexing_service_from_config(config)
    
    # Index first time
    print("\nIndexing first time...")
    job_id_1 = await service.build(items, index_version="v1")
    print(f"  Job 1: {job_id_1}")
    
    # Index second time (should be idempotent)
    print("\nIndexing second time (idempotent)...")
    job_id_2 = await service.build(items, index_version="v1")
    print(f"  Job 2: {job_id_2}")
    
    print("\n✅ Both jobs completed successfully")
    print("   (Check catalog to verify idempotency)")


# ============================================================================
# Example 5: Error Handling
# ============================================================================

async def example_error_handling():
    """Test error handling and retry"""
    
    print("\n" + "=" * 60)
    print("Example 5: Error Handling")
    print("=" * 60)
    
    config = {
        "postgres": {"dsn": "postgresql://mahoun:mahoun@localhost:5432/mahoun"},
        "chroma": {"persist_dir": "./.chroma/mahoun"},
        "service": {
            "retry_attempts": 3
        },
        "wandb": {"enabled": False}
    }
    
    items = [
        IndexItem.from_chunk(
            doc_id="doc_error",
            chunk_id="chunk_error",
            content="محتوای تست خطا",
            index_version="v1"
        )
    ]
    
    service = await build_indexing_service_from_config(config)
    
    try:
        job_id = await service.build(items, index_version="v1")
        print(f"\n✅ Job completed: {job_id}")
    except Exception as e:
        print(f"\n❌ Job failed: {e}")
        print("   (This is expected if adapters are not healthy)")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run all examples"""
    
    print("\n" + "=" * 60)
    print("IndexingService Examples")
    print("=" * 60)
    
    # Note: These examples require:
    # 1. PostgreSQL running with mahoun database
    # 2. ChromaDB directory accessible
    # 3. Neo4j running (optional)
    # 4. BM25 index directory accessible
    
    print("\n⚠️  Prerequisites:")
    print("   - PostgreSQL: postgresql://mahoun:mahoun@localhost:5432/mahoun")
    print("   - ChromaDB: ./.chroma/mahoun")
    print("   - Neo4j: bolt://localhost:7687 (optional)")
    print("   - BM25: ./indexes/bm25 (optional)")
    
    # Run examples
    try:
        await example_basic()
        # await example_convenience()
        # await example_batch()
        # await example_idempotency()
        # await example_error_handling()
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("   Make sure all prerequisites are met")


if __name__ == "__main__":
    asyncio.run(main())
