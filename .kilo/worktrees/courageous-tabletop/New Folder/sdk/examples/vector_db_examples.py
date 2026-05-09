#!/usr/bin/env python3
"""
Advanced Chunking & Vector DB SDK Examples
Demonstrates various use cases and features
"""

import sys
sys.path.append('..')

from sdk.vector_db_client import VectorDBClient
import time


def example_1_basic_chunking():
    """Example 1: Basic document chunking"""
    print("=" * 60)
    print("Example 1: Basic Document Chunking")
    print("=" * 60)
    
    client = VectorDBClient(base_url="http://localhost:8000")
    
    # Sample legal document
    document = """
    This Agreement is entered into as of January 1, 2024, by and between 
    Party A and Party B. The parties agree to the following terms and conditions.
    
    Article 1: Definitions
    For purposes of this Agreement, the following terms shall have the meanings set forth below.
    
    Article 2: Obligations
    Party A shall provide services as described in Exhibit A. Party B shall compensate 
    Party A according to the payment schedule in Exhibit B.
    
    Article 3: Term and Termination
    This Agreement shall commence on the Effective Date and continue for a period of 
    one year, unless terminated earlier in accordance with this Article.
    """
    
    # Chunk with semantic strategy
    chunks = client.chunk_text(
        text=document,
        chunk_size=256,
        overlap=30,
        strategy="semantic",
        quality_check=True
    )
    
    print(f"\nCreated {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}:")
        print(f"  Text: {chunk.text[:100]}...")
        print(f"  Tokens: {chunk.token_count}")
        print(f"  Coherence: {chunk.coherence_score}")
    
    # List available strategies
    strategies = client.list_chunking_strategies()
    print(f"\n\nAvailable strategies: {list(strategies.keys())}")


def example_2_embedding_generation():
    """Example 2: Generate embeddings"""
    print("\n" + "=" * 60)
    print("Example 2: Embedding Generation")
    print("=" * 60)
    
    client = VectorDBClient(base_url="http://localhost:8000")
    
    # Single embedding
    text = "Contract law governs agreements between parties"
    embedding = client.embed_text(text)
    
    print(f"\nSingle embedding:")
    print(f"  Dimension: {embedding.dimension}")
    print(f"  Model: {embedding.model}")
    print(f"  Processing time: {embedding.processing_time_ms:.2f}ms")
    print(f"  First 5 values: {embedding.embedding[:5]}")
    
    # Batch embeddings
    texts = [
        "Contract law and agreements",
        "Criminal law and prosecution",
        "Civil law and disputes",
        "International law and treaties"
    ]
    
    start_time = time.time()
    embeddings = client.embed_batch(texts, batch_size=2)
    elapsed = (time.time() - start_time) * 1000
    
    print(f"\n\nBatch embeddings:")
    print(f"  Texts: {len(texts)}")
    print(f"  Embeddings generated: {len(embeddings)}")
    print(f"  Total time: {elapsed:.2f}ms")
    print(f"  Avg time per text: {elapsed/len(texts):.2f}ms")


def example_3_document_storage_and_search():
    """Example 3: Store documents and search"""
    print("\n" + "=" * 60)
    print("Example 3: Document Storage and Search")
    print("=" * 60)
    
    client = VectorDBClient(base_url="http://localhost:8000")
    
    # Store multiple documents
    documents = [
        {
            "text": "Employment contracts define the relationship between employer and employee, including duties, compensation, and termination conditions.",
            "metadata": {"category": "employment", "type": "contract"}
        },
        {
            "text": "Non-disclosure agreements protect confidential information shared between parties during business negotiations.",
            "metadata": {"category": "confidentiality", "type": "nda"}
        },
        {
            "text": "Service level agreements specify the expected level of service between a service provider and customer.",
            "metadata": {"category": "service", "type": "sla"}
        }
    ]
    
    print("\nStoring documents...")
    for i, doc in enumerate(documents, 1):
        result = client.store_document(
            text=doc["text"],
            collection="legal_docs",
            metadata=doc["metadata"],
            chunk_before_store=True,
            chunk_size=256
        )
        print(f"  Document {i}: {result['chunks_stored']} chunks stored")
    
    # Search for relevant documents
    queries = [
        "employment agreement",
        "confidential information",
        "service provider"
    ]
    
    print("\n\nSearching documents:")
    for query in queries:
        results = client.search(
            query=query,
            collection="legal_docs",
            top_k=2,
            rerank=True
        )
        
        print(f"\n  Query: '{query}'")
        for j, result in enumerate(results, 1):
            print(f"    {j}. Score: {result.score:.3f}")
            print(f"       Text: {result.text[:80]}...")
            print(f"       Category: {result.metadata.get('category')}")


def example_4_hybrid_search():
    """Example 4: Hybrid search (dense + sparse)"""
    print("\n" + "=" * 60)
    print("Example 4: Hybrid Search")
    print("=" * 60)
    
    client = VectorDBClient(base_url="http://localhost:8000")
    
    query = "contract termination clause"
    
    # Dense search only
    print("\nDense search (vector similarity):")
    dense_results = client.search(
        query=query,
        collection="legal_docs",
        top_k=3
    )
    for i, result in enumerate(dense_results, 1):
        print(f"  {i}. Score: {result.score:.3f} - {result.text[:60]}...")
    
    # Hybrid search
    print("\n\nHybrid search (dense + sparse):")
    hybrid_results = client.hybrid_search(
        query=query,
        collection="legal_docs",
        top_k=3,
        dense_weight=0.7,
        sparse_weight=0.3
    )
    for i, result in enumerate(hybrid_results, 1):
        print(f"  {i}. Score: {result.score:.3f} - {result.text[:60]}...")


def example_5_bulk_ingestion():
    """Example 5: Bulk document ingestion"""
    print("\n" + "=" * 60)
    print("Example 5: Bulk Document Ingestion")
    print("=" * 60)
    
    client = VectorDBClient(base_url="http://localhost:8000")
    
    # Prepare bulk documents
    documents = []
    categories = ["contract", "policy", "regulation", "statute"]
    
    for i in range(20):
        doc = {
            "text": f"Legal document {i+1} containing important information about {categories[i % 4]} matters.",
            "metadata": {
                "doc_id": f"DOC-{i+1:03d}",
                "category": categories[i % 4],
                "year": 2024
            }
        }
        documents.append(doc)
    
    print(f"\nIngesting {len(documents)} documents...")
    start_time = time.time()
    
    result = client.bulk_ingest(
        documents=documents,
        collection="bulk_test",
        chunk_documents=True,
        generate_embeddings=True,
        batch_size=10
    )
    
    elapsed = (time.time() - start_time) * 1000
    
    print(f"\nIngestion complete:")
    print(f"  Total documents: {result['total_documents']}")
    print(f"  Successful: {result['successful']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Total chunks: {result['total_chunks']}")
    print(f"  Processing time: {elapsed:.2f}ms")
    print(f"  Avg time per doc: {elapsed/len(documents):.2f}ms")


def example_6_backup_and_restore():
    """Example 6: Backup and restore operations"""
    print("\n" + "=" * 60)
    print("Example 6: Backup and Restore")
    print("=" * 60)
    
    client = VectorDBClient(base_url="http://localhost:8000")
    
    # Create backup
    print("\nCreating backup...")
    backup = client.create_backup(
        collection="legal_docs",
        backup_type="full",
        destination="local",
        compression=True
    )
    
    print(f"  Backup ID: {backup['backup_id']}")
    print(f"  Size: {backup['size_mb']:.2f} MB")
    print(f"  Location: {backup['location']}")
    
    # List backups
    print("\n\nListing backups:")
    backups = client.list_backups(collection="legal_docs")
    for i, backup in enumerate(backups, 1):
        print(f"  {i}. {backup.get('backup_id')} - {backup.get('created_at')}")
    
    # Note: Restore would be done like this:
    # restore_result = client.restore_backup(
    #     backup_id=backup['backup_id'],
    #     target_collection="restored_docs",
    #     validate=True
    # )


def example_7_collection_management():
    """Example 7: Collection management"""
    print("\n" + "=" * 60)
    print("Example 7: Collection Management")
    print("=" * 60)
    
    client = VectorDBClient(base_url="http://localhost:8000")
    
    # List collections
    print("\nAvailable collections:")
    collections = client.list_collections()
    for collection in collections:
        print(f"  - {collection}")
    
    # Get collection stats
    if collections:
        collection = collections[0]
        print(f"\n\nStatistics for '{collection}':")
        stats = client.get_collection_stats(collection)
        print(f"  Documents: {stats['document_count']}")
        print(f"  Chunks: {stats['chunk_count']}")
        print(f"  Total size: {stats['total_size_mb']:.2f} MB")
        print(f"  Avg chunk size: {stats['avg_chunk_size']:.2f}")
        print(f"  Created: {stats['created_at']}")
        print(f"  Last updated: {stats['last_updated']}")
        
        # Optimize collection
        print(f"\n\nOptimizing collection '{collection}'...")
        result = client.optimize_collection(collection)
        print(f"  Optimization complete: {result['message']}")


def example_8_convenience_methods():
    """Example 8: Convenience methods"""
    print("\n" + "=" * 60)
    print("Example 8: Convenience Methods")
    print("=" * 60)
    
    client = VectorDBClient(base_url="http://localhost:8000")
    
    # Process document (all-in-one)
    print("\nProcessing document (chunk + embed + store):")
    document = "This is a sample legal document about intellectual property rights and licensing agreements."
    
    result = client.process_document(
        text=document,
        collection="convenience_test",
        chunk_size=128,
        metadata={"source": "example", "type": "ip"}
    )
    
    print(f"  Chunks: {result['chunks']}")
    print(f"  Document ID: {result['document_id']}")
    print(f"  Chunks stored: {result['chunks_stored']}")
    
    # Search with explanations
    print("\n\nSearch with explanations:")
    results = client.search_and_explain(
        query="intellectual property",
        collection="convenience_test",
        top_k=3
    )
    
    for i, result in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"    Text: {result['text'][:80]}...")
        print(f"    Score: {result['score']:.3f}")
        print(f"    Explanation: {result['explanation']}")


def example_9_health_monitoring():
    """Example 9: Health monitoring"""
    print("\n" + "=" * 60)
    print("Example 9: Health Monitoring")
    print("=" * 60)
    
    client = VectorDBClient(base_url="http://localhost:8000")
    
    print("\nChecking system health...")
    health = client.health_check()
    
    print("\nService status:")
    for service, status in health.items():
        emoji = "✅" if status == "healthy" else "❌"
        print(f"  {emoji} {service}: {status}")
    
    all_healthy = all(status == "healthy" for status in health.values())
    print(f"\n{'✅ All services healthy!' if all_healthy else '⚠️  Some services unhealthy'}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Advanced Chunking & Vector DB SDK Examples")
    print("=" * 60)
    
    examples = [
        example_1_basic_chunking,
        example_2_embedding_generation,
        example_3_document_storage_and_search,
        example_4_hybrid_search,
        example_5_bulk_ingestion,
        example_6_backup_and_restore,
        example_7_collection_management,
        example_8_convenience_methods,
        example_9_health_monitoring
    ]
    
    for example in examples:
        try:
            example()
            time.sleep(1)  # Brief pause between examples
        except Exception as e:
            print(f"\n❌ Error in {example.__name__}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
