# Official End-to-End Golden Path Test

## Test Name
Golden Path End-to-End Validation Test

## Preconditions
1. System is running in desktop_minimal mode
2. All Golden Path components are available
3. ChromaDB is accessible and writable
4. sentence-transformers library is installed
5. Basic TXT file handling is available

## Execution Steps

### Success Path Test

1. **Prepare Test Document**
   - Create a sample legal document in TXT format
   - Content should include Persian legal text with multiple paragraphs

2. **Document Ingestion**
   - Use `IngestionPipelineV2.ingest_file()` to process the document
   - Verify text was extracted successfully
   - Confirm document was parsed and normalized

3. **Chunking Verification**
   - Check that semantic chunking produced multiple text segments
   - Verify chunk metadata includes source document information
   - Confirm appropriate chunk sizes and overlap

4. **Embedding Generation**
   - Confirm embeddings were generated for each chunk
   - Verify embedding dimensions (768) match expected model output
   - Check that embedding generation completed without errors

5. **Vector Storage**
   - Confirm vectors were stored in ChromaDB
   - Verify document count in collection increased
   - Check that metadata was properly stored with embeddings

6. **Retrieval Validation**
   - Execute a hybrid search query using a relevant term from the document
   - Verify that results are returned with proper ranking
   - Confirm that scores are meaningful and differentiated

### Failure Path Test

1. **Vector Store Unavailability Simulation**
   - Stop or disconnect ChromaDB service
   - Attempt to ingest a new document

2. **Expected Behavior Verification**
   - Request should fail with appropriate error code (503 Service Unavailable)
   - Health check should report vector store as DEGRADED
   - No fake success responses should be returned
   - Error should be logged with sufficient detail for debugging

## Expected Results

### Success Path
- Document ingestion completes successfully with `success=True`
- At least 2 chunks are created from the test document
- Exactly N embeddings are generated (where N = number of chunks)
- All embeddings are successfully stored in vector database
- Search returns ranked results with scores between 0 and 1
- Health status reports all Golden Path components as HEALTHY

### Failure Path
- Document ingestion fails with appropriate error when vector store is unavailable
- HTTP response code is 503 (Service Unavailable)
- Health check reports vector store component as DEGRADED
- Error message clearly indicates the nature of the failure
- System does not mask the underlying issue with fake success responses

## Test Implementation Example

```python
import pytest
import tempfile
import os
from pathlib import Path

from mahoun.pipelines.ingestion.pipeline import IngestionPipelineV2
from mahoun.retrieval.hybrid_search_v2 import HybridSearchV2, RetrievalMethod, FusionMethod
from mahoun.pipelines.vector_store.manager import VectorStoreManager

@pytest.mark.asyncio
async def test_golden_path_e2e():
    """Test the complete Golden Path execution flow"""
    
    # Setup
    pipeline = IngestionPipelineV2()
    await pipeline.initialize()
    
    vector_store = VectorStoreManager()
    await vector_store.initialize()
    
    search = HybridSearchV2(vector_store=vector_store)
    await search.initialize()
    
    # Create test document
    test_content = """
    بسمه تعالی
    
    قرارداد خرید و فروش اموال منقول
    
    تاریخ: 1403/05/15
    شماره: 789456/1403
    
    طرف اول: شرکت تجارت نوین
    نام و نام خانوادگی: محمد رضایی
    کد ملی: 1234567890
    
    طرف دوم: شرکت توسعه صنعتی
    نام و نام خانوادگی: احمد محمدی
    کد ملی: 0987654321
    
    موضوع قرارداد: خرید و فروش ماشین آلات صنعتی
    
    متن کامل قرارداد...
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_path = f.name
    
    try:
        # Step 1: Document Ingestion
        doc_id = "test_contract_001"
        result = await pipeline.ingest_file(temp_path, doc_id=doc_id)
        
        # Verification
        assert result.success == True, f"Ingestion failed: {result.error}"
        assert result.chunks_created > 0, "No chunks were created"
        assert result.embeddings_created == result.chunks_created, \
            f"Mismatch between chunks ({result.chunks_created}) and embeddings ({result.embeddings_created})"
        assert result.indexed == True, "Document was not indexed in vector store"
        
        # Step 2: Retrieval
        query = "خرید و فروش ماشین آلات"
        search_result = await search.search(
            query=query,
            top_k=5,
            method=RetrievalMethod.HYBRID,
            fusion=FusionMethod.RRF
        )
        
        # Verification
        assert len(search_result.results) > 0, "No search results returned"
        assert all(0 <= r.score <= 1 for r in search_result.results), \
            "Search scores are not in expected range [0, 1]"
        
        # Check that our document appears in results
        doc_found = any(r.id.startswith(doc_id) for r in search_result.results)
        assert doc_found, "Original document not found in search results"
        
        # Step 3: Health Verification
        # This would typically be checked via the health endpoint
        
    finally:
        # Cleanup
        os.unlink(temp_path)
        await pipeline.close()
        await search.close()

@pytest.mark.asyncio
async def test_vector_store_failure_path():
    """Test system behavior when vector store is unavailable"""
    
    # This test would simulate vector store unavailability
    # and verify appropriate failure handling
    pass
```

## Test Coverage Requirements

This test MUST validate:
1. All steps of the Golden Path execute successfully
2. Runtime evidence is produced at each stage
3. Error conditions are handled appropriately
4. Health status accurately reflects system state
5. No false positives or masked failures occur