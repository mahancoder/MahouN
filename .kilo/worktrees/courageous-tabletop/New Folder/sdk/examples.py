#!/usr/bin/env python3
"""
MAHOUN SDK Examples
===================
Comprehensive examples for using the MAHOUN Python SDK

Run examples:
    python sdk/examples.py
"""

from sdk.mahoun_client import MahounClient, quick_chunk, quick_embed, quick_search
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Basic Chunking
# ============================================================================

def example_basic_chunking():
    """Example: Chunk a document with default settings"""
    
    print("\n" + "="*60)
    print("Example 1: Basic Chunking")
    print("="*60)
    
    # Sample legal text
    text = """
    قانون مدنی ایران در ماده ۱۰ مقرر می‌دارد که قوانین راجع به اهلیت اشخاص 
    تابع قانون کشوری است که آن اشخاص تابعیت آن را دارند. این ماده یکی از 
    مهم‌ترین مواد در حقوق بین‌الملل خصوصی است و تعیین‌کننده قانون حاکم بر 
    اهلیت افراد در معاملات بین‌المللی می‌باشد.
    """
    
    # Initialize client
    client = MahounClient(base_url="http://localhost:8000")
    
    try:
        # Chunk the text
        result = client.chunking.chunk_text(
            text=text,
            chunk_size=256,
            overlap=30,
            strategy="semantic",
            quality_check=True
        )
        
        print(f"\n✅ Chunking completed!")
        print(f"Job ID: {result['job_id']}")
        print(f"Total chunks: {result['total_chunks']}")
        print(f"Processing time: {result['processing_time_ms']:.2f}ms")
        
        # Print chunks
        for chunk in result['chunks']:
            print(f"\nChunk {chunk.chunk_index}:")
            print(f"  Text: {chunk.text[:100]}...")
            print(f"  Tokens: {chunk.token_count}")
            if chunk.coherence_score:
                print(f"  Coherence: {chunk.coherence_score:.2f}")
        
        # Print quality metrics
        if result['quality_metrics']:
            print(f"\n📊 Quality Metrics:")
            for key, value in result['quality_metrics'].items():
                print(f"  {key}: {value}")
    
    finally:
        client.close()


# ============================================================================
# Example 2: Batch Embedding
# ============================================================================

def example_batch_embedding():
    """Example: Generate embeddings for multiple texts"""
    
    print("\n" + "="*60)
    print("Example 2: Batch Embedding")
    print("="*60)
    
    texts = [
        "قانون مدنی ایران",
        "قانون تجارت",
        "قانون آیین دادرسی مدنی",
        "قانون مجازات اسلامی"
    ]
    
    client = MahounClient(base_url="http://localhost:8000")
    
    try:
        # Generate embeddings
        result = client.embedding.embed_batch(
            texts=texts,
            model="sentence-transformers/all-mpnet-base-v2",
            normalize=True,
            batch_size=4
        )
        
        print(f"\n✅ Embedding completed!")
        print(f"Total embeddings: {result['total_embeddings']}")
        print(f"Dimension: {result['dimension']}")
        print(f"Model: {result['model']}")
        print(f"Processing time: {result['processing_time_ms']:.2f}ms")
        
        # Print first few values of each embedding
        for i, embedding in enumerate(result['embeddings']):
            print(f"\nEmbedding {i}: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")
    
    finally:
        client.close()


# ============================================================================
# Example 3: Document Storage and Search
# ============================================================================

def example_document_storage_and_search():
    """Example: Store documents and perform search"""
    
    print("\n" + "="*60)
    print("Example 3: Document Storage and Search")
    print("="*60)
    
    # Sample documents
    documents = [
        {
            "text": "قانون مدنی ایران مجموعه قوانین حقوقی است که روابط خصوصی افراد را تنظیم می‌کند.",
            "metadata": {"category": "civil_law", "year": 1928}
        },
        {
            "text": "قانون تجارت مربوط به معاملات تجاری و تجار است.",
            "metadata": {"category": "commercial_law", "year": 1932}
        },
        {
            "text": "قانون آیین دادرسی مدنی رویه‌های دادگاه‌ها را مشخص می‌کند.",
            "metadata": {"category": "procedural_law", "year": 1939}
        }
    ]
    
    client = MahounClient(base_url="http://localhost:8000")
    
    try:
        # Store documents
        print("\n📥 Storing documents...")
        for i, doc in enumerate(documents):
            result = client.retrieval.store_document(
                text=doc["text"],
                collection="legal_docs",
                metadata=doc["metadata"],
                chunk_before_store=True,
                chunk_size=256
            )
            print(f"  Document {i+1}: {result['chunks_stored']} chunks stored")
        
        # Perform search
        print("\n🔍 Searching...")
        query = "قانون مدنی"
        
        search_result = client.retrieval.search(
            query=query,
            collection="legal_docs",
            top_k=5,
            threshold=0.5
        )
        
        print(f"\n✅ Search completed!")
        print(f"Query: {search_result['query']}")
        print(f"Total results: {search_result['total_results']}")
        print(f"Search time: {search_result['search_time_ms']:.2f}ms")
        
        # Print results
        for i, result in enumerate(search_result['results']):
            print(f"\nResult {i+1}:")
            print(f"  Score: {result.score:.4f}")
            print(f"  Text: {result.text[:100]}...")
            if result.metadata:
                print(f"  Metadata: {result.metadata}")
    
    finally:
        client.close()


# ============================================================================
# Example 4: Hybrid Search
# ============================================================================

def example_hybrid_search():
    """Example: Perform hybrid search (dense + sparse)"""
    
    print("\n" + "="*60)
    print("Example 4: Hybrid Search")
    print("="*60)
    
    client = MahounClient(base_url="http://localhost:8000")
    
    try:
        # Perform hybrid search
        query = "قانون مدنی و حقوق خصوصی"
        
        result = client.retrieval.hybrid_search(
            query=query,
            collection="legal_docs",
            top_k=10,
            dense_weight=0.7,
            sparse_weight=0.3
        )
        
        print(f"\n✅ Hybrid search completed!")
        print(f"Query: {result['query']}")
        print(f"Total results: {result['total_results']}")
        print(f"Search time: {result['search_time_ms']:.2f}ms")
        
        # Print top results
        for i, search_result in enumerate(result['results'][:3]):
            print(f"\nResult {i+1}:")
            print(f"  Score: {search_result.score:.4f}")
            print(f"  Text: {search_result.text[:100]}...")
    
    finally:
        client.close()


# ============================================================================
# Example 5: Using Convenience Functions
# ============================================================================

def example_convenience_functions():
    """Example: Use quick convenience functions"""
    
    print("\n" + "="*60)
    print("Example 5: Convenience Functions")
    print("="*60)
    
    text = "قانون مدنی ایران در ماده ۱۰ مقرر می‌دارد..."
    
    # Quick chunk
    print("\n📄 Quick chunking...")
    chunks = quick_chunk(
        text=text,
        chunk_size=128,
        strategy="semantic"
    )
    print(f"  Generated {len(chunks)} chunks")
    
    # Quick embed
    print("\n🔢 Quick embedding...")
    embedding = quick_embed(text=text)
    print(f"  Generated embedding with {len(embedding)} dimensions")
    
    # Quick search
    print("\n🔍 Quick search...")
    results = quick_search(
        query="قانون مدنی",
        collection="legal_docs",
        top_k=3
    )
    print(f"  Found {len(results)} results")


# ============================================================================
# Example 6: Context Manager Usage
# ============================================================================

def example_context_manager():
    """Example: Use client as context manager"""
    
    print("\n" + "="*60)
    print("Example 6: Context Manager")
    print("="*60)
    
    # Using context manager (automatically closes connection)
    with MahounClient(base_url="http://localhost:8000") as client:
        # Check health
        health = client.health_check()
        print(f"\n✅ API Health: {health['status']}")
        
        # Check individual services
        chunking_health = client.chunking.health_check()
        print(f"  Chunking: {chunking_health['status']}")
        
        embedding_health = client.embedding.health_check()
        print(f"  Embedding: {embedding_health['status']}")
        
        retrieval_health = client.retrieval.health_check()
        print(f"  Retrieval: {retrieval_health['status']}")
        
        # List available resources
        strategies = client.chunking.list_strategies()
        print(f"\n📋 Available chunking strategies: {len(strategies['strategies'])}")
        
        models = client.embedding.list_models()
        print(f"📋 Available embedding models: {len(models['models'])}")
        
        collections = client.retrieval.list_collections()
        print(f"📋 Available collections: {collections['total']}")


# ============================================================================
# Example 7: Error Handling
# ============================================================================

def example_error_handling():
    """Example: Proper error handling"""
    
    print("\n" + "="*60)
    print("Example 7: Error Handling")
    print("="*60)
    
    client = MahounClient(base_url="http://localhost:8000")
    
    try:
        # Try to chunk empty text (should fail)
        result = client.chunking.chunk_text(text="")
    except Exception as e:
        print(f"\n❌ Expected error caught: {type(e).__name__}")
        print(f"   Message: {str(e)}")
    
    try:
        # Try to search in non-existent collection
        result = client.retrieval.search(
            query="test",
            collection="non_existent_collection"
        )
    except Exception as e:
        print(f"\n❌ Expected error caught: {type(e).__name__}")
        print(f"   Message: {str(e)}")
    
    finally:
        client.close()


# ============================================================================
# Example 8: Advanced Workflow
# ============================================================================

def example_advanced_workflow():
    """Example: Complete document processing workflow"""
    
    print("\n" + "="*60)
    print("Example 8: Advanced Workflow")
    print("="*60)
    
    # Sample document
    document = """
    قانون مدنی ایران در ماده ۱۰ مقرر می‌دارد که قوانین راجع به اهلیت اشخاص 
    تابع قانون کشوری است که آن اشخاص تابعیت آن را دارند. این ماده یکی از 
    مهم‌ترین مواد در حقوق بین‌الملل خصوصی است.
    
    همچنین ماده ۱۱ قانون مدنی بیان می‌کند که قوانین راجع به اموال تابع قانون 
    محلی است که آن اموال در آنجا واقع است. این اصل در حقوق بین‌الملل خصوصی 
    به عنوان اصل lex rei sitae شناخته می‌شود.
    """
    
    with MahounClient(base_url="http://localhost:8000") as client:
        # Step 1: Chunk the document
        print("\n📄 Step 1: Chunking document...")
        chunk_result = client.chunking.chunk_text(
            text=document,
            chunk_size=256,
            strategy="semantic",
            quality_check=True
        )
        print(f"  ✓ Created {chunk_result['total_chunks']} chunks")
        
        # Step 2: Generate embeddings for each chunk
        print("\n🔢 Step 2: Generating embeddings...")
        chunk_texts = [chunk.text for chunk in chunk_result['chunks']]
        embed_result = client.embedding.embed_batch(
            texts=chunk_texts,
            normalize=True
        )
        print(f"  ✓ Generated {embed_result['total_embeddings']} embeddings")
        
        # Step 3: Store in vector database
        print("\n💾 Step 3: Storing in vector database...")
        store_result = client.retrieval.store_document(
            text=document,
            collection="legal_corpus",
            metadata={
                "source": "civil_code",
                "articles": ["10", "11"],
                "topic": "private_international_law"
            },
            chunk_before_store=True
        )
        print(f"  ✓ Stored {store_result['chunks_stored']} chunks")
        
        # Step 4: Perform search
        print("\n🔍 Step 4: Searching...")
        search_result = client.retrieval.search(
            query="اهلیت اشخاص در حقوق بین‌الملل",
            collection="legal_corpus",
            top_k=3,
            rerank=True
        )
        print(f"  ✓ Found {search_result['total_results']} results")
        
        # Step 5: Display results
        print("\n📊 Step 5: Results:")
        for i, result in enumerate(search_result['results']):
            print(f"\n  Result {i+1}:")
            print(f"    Score: {result.score:.4f}")
            print(f"    Text: {result.text[:80]}...")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all examples"""
    
    print("\n" + "="*60)
    print("MAHOUN SDK Examples")
    print("="*60)
    
    examples = [
        ("Basic Chunking", example_basic_chunking),
        ("Batch Embedding", example_batch_embedding),
        ("Document Storage and Search", example_document_storage_and_search),
        ("Hybrid Search", example_hybrid_search),
        ("Convenience Functions", example_convenience_functions),
        ("Context Manager", example_context_manager),
        ("Error Handling", example_error_handling),
        ("Advanced Workflow", example_advanced_workflow)
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nNote: Make sure the MAHOUN API is running at http://localhost:8000")
    print("      before running these examples.")
    
    # Run a specific example or all
    try:
        choice = input("\nEnter example number (or 'all' to run all): ").strip()
        
        if choice.lower() == 'all':
            for name, func in examples:
                try:
                    func()
                except Exception as e:
                    logger.error(f"Error in {name}: {e}")
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                examples[idx][1]()
            else:
                print("Invalid choice!")
    
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
