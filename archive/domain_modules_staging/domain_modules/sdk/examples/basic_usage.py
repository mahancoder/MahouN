#!/usr/bin/env python3
"""
MAHOUN SDK - Basic Usage Examples
==================================
Demonstrates basic usage of the MAHOUN Python SDK
"""

import sys
sys.path.append('../..')

from sdk import MahounClient, quick_chunk, quick_embed, quick_search


def example_1_chunking():
    """Example 1: Document Chunking"""
    print("=" * 60)
    print("Example 1: Document Chunking")
    print("=" * 60)
    
    # Initialize client
    client = MahounClient(base_url="http://localhost:8000")
    
    # Sample legal text
    text = """
    قانون مدنی ایران در ماده ۱۰ مقرر می‌دارد که هر شخصی که به سن رشد برسد،
    اهلیت انجام معاملات را دارد. سن رشد در قانون مدنی ایران برای پسران ۱۵ سال
    تمام قمری و برای دختران ۹ سال تمام قمری تعیین شده است. این در حالی است که
    در بسیاری از کشورها سن رشد ۱۸ سال تعیین شده است.
    """
    
    # Chunk the text
    result = client.chunking.chunk_text(
        text=text,
        chunk_size=256,
        overlap=30,
        strategy="semantic",
        quality_check=True
    )
    
    print(f"\n✅ Chunking completed!")
    print(f"   Job ID: {result['job_id']}")
    print(f"   Total chunks: {result['total_chunks']}")
    print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
    
    if result['quality_metrics']:
        print(f"\n📊 Quality Metrics:")
        for key, value in result['quality_metrics'].items():
            print(f"   {key}: {value}")
    
    print(f"\n📄 Chunks:")
    for i, chunk in enumerate(result['chunks'][:3], 1):  # Show first 3
        print(f"\n   Chunk {i}:")
        print(f"   Text: {chunk.text[:100]}...")
        print(f"   Tokens: {chunk.token_count}")
        if chunk.coherence_score:
            print(f"   Coherence: {chunk.coherence_score:.2f}")
    
    client.close()


def example_2_embedding():
    """Example 2: Text Embedding"""
    print("\n" + "=" * 60)
    print("Example 2: Text Embedding")
    print("=" * 60)
    
    client = MahounClient(base_url="http://localhost:8000")
    
    # Single text embedding
    text = "قانون مدنی ایران"
    
    result = client.embedding.embed_text(
        text=text,
        model="sentence-transformers/all-mpnet-base-v2",
        normalize=True
    )
    
    print(f"\n✅ Embedding generated!")
    print(f"   Dimension: {result['dimension']}")
    print(f"   Model: {result['model']}")
    print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
    print(f"   First 5 values: {result['embedding'][:5]}")
    
    # Batch embedding
    texts = [
        "قانون مدنی",
        "قانون تجارت",
        "قانون جزا"
    ]
    
    batch_result = client.embedding.embed_batch(
        texts=texts,
        batch_size=32
    )
    
    print(f"\n✅ Batch embedding completed!")
    print(f"   Total embeddings: {batch_result['total_embeddings']}")
    print(f"   Processing time: {batch_result['processing_time_ms']:.2f}ms")
    
    client.close()


def example_3_retrieval():
    """Example 3: Vector Search and Retrieval"""
    print("\n" + "=" * 60)
    print("Example 3: Vector Search and Retrieval")
    print("=" * 60)
    
    client = MahounClient(base_url="http://localhost:8000")
    
    # First, store some documents
    print("\n📥 Storing documents...")
    
    documents = [
        "قانون مدنی ایران در ماده ۱۰ سن رشد را تعیین می‌کند",
        "قانون تجارت ایران شامل مقررات مربوط به معاملات تجاری است",
        "قانون جزا مجازات‌های مختلف را برای جرائم تعیین می‌کند"
    ]
    
    for doc in documents:
        result = client.retrieval.store_document(
            text=doc,
            collection="legal_docs",
            chunk_before_store=False
        )
        print(f"   ✓ Stored document {result['document_id']}")
    
    # Now search
    print("\n🔍 Searching...")
    
    search_result = client.retrieval.search(
        query="سن رشد در قانون مدنی",
        collection="legal_docs",
        top_k=5,
        threshold=0.3
    )
    
    print(f"\n✅ Search completed!")
    print(f"   Query ID: {search_result['query_id']}")
    print(f"   Total results: {search_result['total_results']}")
    print(f"   Search time: {search_result['search_time_ms']:.2f}ms")
    
    print(f"\n📋 Results:")
    for i, result in enumerate(search_result['results'], 1):
        print(f"\n   Result {i}:")
        print(f"   Score: {result.score:.4f}")
        print(f"   Text: {result.text[:100]}...")
    
    # Hybrid search
    print("\n🔍 Hybrid search...")
    
    hybrid_result = client.retrieval.hybrid_search(
        query="قانون تجارت",
        collection="legal_docs",
        top_k=3,
        dense_weight=0.7,
        sparse_weight=0.3
    )
    
    print(f"\n✅ Hybrid search completed!")
    print(f"   Total results: {hybrid_result['total_results']}")
    print(f"   Search time: {hybrid_result['search_time_ms']:.2f}ms")
    
    client.close()


def example_4_convenience_functions():
    """Example 4: Using Convenience Functions"""
    print("\n" + "=" * 60)
    print("Example 4: Convenience Functions")
    print("=" * 60)
    
    text = "قانون مدنی ایران"
    
    # Quick chunk
    print("\n📄 Quick chunking...")
    chunks = quick_chunk(text, chunk_size=128)
    print(f"   ✓ Got {len(chunks)} chunks")
    
    # Quick embed
    print("\n🔢 Quick embedding...")
    embedding = quick_embed(text)
    print(f"   ✓ Got embedding with {len(embedding)} dimensions")
    
    # Quick search
    print("\n🔍 Quick search...")
    results = quick_search("قانون مدنی", top_k=3)
    print(f"   ✓ Got {len(results)} results")


def example_5_context_manager():
    """Example 5: Using Context Manager"""
    print("\n" + "=" * 60)
    print("Example 5: Context Manager Usage")
    print("=" * 60)
    
    # Using context manager (automatically closes connection)
    with MahounClient(base_url="http://localhost:8000") as client:
        # Check health
        health = client.health_check()
        print(f"\n✅ API Health: {health['status']}")
        
        # List chunking strategies
        strategies = client.chunking.list_strategies()
        print(f"\n📋 Available chunking strategies:")
        for name, info in strategies['strategies'].items():
            print(f"   • {name}: {info['description']}")
        
        # List embedding models
        models = client.embedding.list_models()
        print(f"\n🤖 Available embedding models:")
        for name, info in models['models'].items():
            print(f"   • {name}: {info['description']}")
        
        # List collections
        collections = client.retrieval.list_collections()
        print(f"\n📚 Available collections:")
        print(f"   Total: {collections['total']}")
        for coll in collections['collections']:
            print(f"   • {coll}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("MAHOUN SDK - Basic Usage Examples")
    print("=" * 60)
    print("\nMake sure the MAHOUN API is running at http://localhost:8000")
    print("\nPress Enter to continue or Ctrl+C to exit...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        return
    
    try:
        example_1_chunking()
        example_2_embedding()
        example_3_retrieval()
        example_4_convenience_functions()
        example_5_context_manager()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure:")
        print("  1. MAHOUN API is running at http://localhost:8000")
        print("  2. All required services are available")
        print("  3. You have proper network connectivity")


if __name__ == "__main__":
    main()
