# برنامه بهینه‌سازی سیستم ماهون برای لپتاپ
# Mahoun System Optimization Plan for Laptop

**Hardware:** 8GB RAM, 5-core CPU  
**Goal:** یکپارچه‌سازی کامل سیستم قبل از deployment روی سرور

---

## Phase 1: Memory Optimization (حافظه)

### 1.1 Vector Store Optimization
- **Current:** ChromaDB loads full embeddings in memory
- **Action:** 
  - Enable disk-based persistence
  - Use memory-mapped files
  - Limit batch size to 100 documents
  - Clear cache after each batch

### 1.2 Model Loading Strategy
- **Current:** Multiple models loaded simultaneously
- **Action:**
  - Lazy loading: load models only when needed
  - Unload unused models after 5 minutes
  - Use quantized models (int8) instead of float32
  - Share embeddings across components

### 1.3 Graph Database
- **Current:** Neo4j can consume 2-4GB RAM
- **Action:**
  - Use embedded Neo4j instead of server
  - Limit query result size to 1000 nodes
  - Enable query caching
  - OR: Use in-memory graph (NetworkX) for development

**Expected RAM Savings:** 3-4GB

---

## Phase 2: CPU Optimization (پردازنده)

### 2.1 Parallel Processing
- **Action:**
  - Use 3 workers (leave 2 cores for OS)
  - Batch processing for embeddings
  - Async I/O for all network calls
  - Thread pool for CPU-bound tasks

### 2.2 Model Inference
- **Action:**
  - Use ONNX Runtime (faster than PyTorch)
  - Enable CPU optimizations (AVX2, FMA)
  - Batch inference: process 10 documents at once
  - Cache embeddings for repeated queries

**Expected Speedup:** 2-3x faster

---

## Phase 3: Fine-tuning Pipeline (آموزش مدل)

### 3.1 Training Data Generation
```python
# Use existing document_to_training.py
# Generate training data from:
- Legal documents in vector store
- Reasoning chains from ledger
- Graph traversal patterns
```

### 3.2 Model Selection for Fine-tuning
**Option A: Small Models (Recommended for 8GB RAM)**
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (118MB)
- `HooshvareLab/bert-fa-base-uncased` (Persian, 440MB)
- Fine-tune on laptop: 2-4 hours

**Option B: Larger Models (Need 16GB+ RAM)**
- `xlm-roberta-large` - Too large for 8GB
- Use Google Colab or server for these

### 3.3 Training Configuration
```yaml
batch_size: 8  # Small for 8GB RAM
gradient_accumulation: 4  # Simulate batch_size=32
mixed_precision: fp16  # Save memory
max_epochs: 3
learning_rate: 2e-5
```

**Training Time Estimate:** 2-4 hours on laptop

---

## Phase 4: System Integration Testing

### 4.1 Component Integration
```bash
# Test each component individually
pytest tests/test_core_models.py -v
pytest tests/test_error_paths.py -v
pytest tests/test_invariant_properties.py -v

# Test full pipeline
pytest tests/test_golden_path.py -v
```

### 4.2 End-to-End Testing
```python
# Test complete workflow:
1. Ingest document → Vector store
2. Build knowledge graph
3. Generate reasoning chain
4. Write to ledger
5. Verify invariants
```

### 4.3 Performance Benchmarks
- Document ingestion: < 5 seconds per document
- Query response: < 2 seconds
- Graph traversal: < 1 second
- Memory usage: < 6GB peak

---

## Phase 5: Pre-deployment Checklist

### 5.1 Code Quality
- [ ] All tests passing
- [ ] No linting errors (`make lint`)
- [ ] Type checking clean (`make typecheck`)
- [ ] Coverage > 80%

### 5.2 Architecture Validation
- [ ] No boundary violations (core → non-core)
- [ ] All invariants enforced
- [ ] Protocols properly implemented
- [ ] Dependency injection working

### 5.3 Documentation
- [ ] API documentation complete
- [ ] Architecture diagrams updated
- [ ] Deployment guide written
- [ ] Troubleshooting guide ready

### 5.4 Performance
- [ ] Memory usage < 6GB
- [ ] Response time < 2s
- [ ] No memory leaks
- [ ] Graceful degradation under load

---

## Implementation Steps (Next Actions)

### Step 1: Memory Profiling
```bash
# Profile current memory usage
python -m memory_profiler scripts/profile_memory.py
```

### Step 2: Optimize Vector Store
```python
# Update mahoun/rag/hybrid_rag_service.py
# Enable disk persistence and memory limits
```

### Step 3: Implement Lazy Loading
```python
# Update mahoun/core/llm/orchestrator.py
# Add model unloading after timeout
```

### Step 4: Run Integration Tests
```bash
# Test on laptop with memory constraints
MAHOUN_MAX_MEMORY=6GB pytest tests/ -v
```

### Step 5: Fine-tune Embeddings
```bash
# Generate training data
python mahoun/finetuning/document_to_training.py

# Train model (2-4 hours)
python mahoun/finetuning/train_embeddings.py
```

---

## Expected Results

**Before Optimization:**
- Memory: 7-8GB (crashes on 8GB laptop)
- Speed: 5-10s per query
- Stability: Frequent OOM errors

**After Optimization:**
- Memory: 4-6GB (stable on 8GB laptop)
- Speed: 1-2s per query
- Stability: No crashes, graceful degradation

---

## Timeline

- **Week 1:** Memory optimization + CPU optimization (2-3 days)
- **Week 2:** Fine-tuning pipeline setup (2-3 days)
- **Week 3:** Integration testing + benchmarking (2-3 days)
- **Week 4:** Pre-deployment validation (1-2 days)

**Total:** 3-4 weeks to production-ready system

---

## Priority Tasks (Start Now)

1. **Create memory profiling script** - See current usage
2. **Optimize vector store** - Biggest memory consumer
3. **Implement lazy model loading** - Free up RAM
4. **Run integration tests** - Verify everything works together
5. **Generate fine-tuning data** - Prepare for model training

---

## Questions to Answer

1. آیا می‌خواهید روی مدل‌های فارسی تمرکز کنید یا چندزبانه؟
2. آیا Neo4j ضروری است یا می‌توانیم از NetworkX استفاده کنیم؟
3. آیا می‌خواهید embeddings را fine-tune کنید یا از pre-trained استفاده کنید؟
4. چه dataset‌هایی برای fine-tuning دارید؟

---

**Next Step:** کدام بخش را اول شروع کنیم؟
