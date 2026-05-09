# Implementation Tasks: Domain Modules Integration

**Feature**: domain-modules-integration  
**Status**: In Progress (90% Complete - Only Missing Features Remain)  
**Timeline**: 1-2 weeks (Revised from 4 weeks)

---

## ✅ COMPLETED WORK (Already in mahoun core)

### Phase 1: Data Ingestion - ✅ 95% COMPLETE
- ✅ Document format handlers (TXT, DOCX, PDF, Image with OCR)
- ✅ Persian text normalization (digits, characters, typos, whitespace)
- ✅ Legal NER engine (25+ categories, 300+ keywords, oil & gas patterns)
- ✅ Metadata extraction (dates, document numbers, subjects, parties, signatures)
- ✅ Enhanced ingestion pipeline (LLM parser, NER, chunking, embedding, validation)
- ✅ Production pipeline (async, thread-safe, error handling, metrics)

### Phase 2: Knowledge Graph - ✅ 85% COMPLETE
- ✅ Ultra Graph Builder with Neo4j integration
- ✅ Entity extraction from legal documents
- ✅ Relationship building (citations, references, precedents)
- ✅ Graph construction from verdicts
- ✅ PageRank and centrality calculations
- ✅ Graph-based retrieval

### Phase 3: Enhanced RAG - ✅ 100% COMPLETE
- ✅ GAT Reranking (Graph Attention Networks)
- ✅ Uncertainty Quantification
- ✅ Chain-of-Thought reasoning
- ✅ Smart Cache (L1/L2 with Redis)
- ✅ Query Enhancement (intent detection, complexity analysis)
- ✅ Guardrails (NLI verification, citation auditing, hallucination detection)
- ✅ Answer Composer with CoT
- ✅ Policy Guardrails (PII redaction, content filtering)

**Note**: Enhanced RAG is fully implemented in `domain_modules/flows/enhanced_rag.py` and needs to be moved to mahoun core.

---

## 🚧 REMAINING WORK (Only Missing Features)

### Task 1: Implement Auto-Ingest Service

**Source**: `domain_modules/pipelines/ingestion/auto_ingest.py`

- [ ] 1.1 Create `mahoun/pipelines/ingestion/auto_ingest.py`
- [ ] 1.2 Implement FileSystemEventHandler with watchdog
- [ ] 1.3 Implement AutoIngestService class
- [ ] 1.4 Add file type filtering (.json, .txt, .pdf, .docx)
- [ ] 1.5 Add duplicate processing prevention
- [ ] 1.6 Integrate with existing IngestionPipelineV2
- [ ] 1.7 Add configuration for watch directory
- [ ] 1.8 Write unit tests
- [ ] 1.9 Write integration tests
- [ ] 1.10 Add documentation and examples

**Estimated Time**: 1 day

**Dependencies**: 
- `watchdog` library for file system monitoring
- Existing `IngestionPipelineV2` for document processing

---

### Task 2: Implement Comprehensive Validation Framework

**Source**: `domain_modules/pipelines/ingestion/validators.py`

- [ ] 2.1 Create `mahoun/pipelines/ingestion/validators.py`
- [ ] 2.2 Implement BaseValidator abstract class
- [ ] 2.3 Implement FileValidator (size, permissions, extensions)
- [ ] 2.4 Implement SchemaValidator (JSON schema validation)
- [ ] 2.5 Implement ContentValidator (length, language detection)
- [ ] 2.6 Implement LegalDocumentValidator (structure validation)
- [ ] 2.7 Implement QualityValidator (completeness, consistency)
- [ ] 2.8 Implement SecurityValidator (PII detection)
- [ ] 2.9 Implement ValidatorChain (composable validators)
- [ ] 2.10 Integrate with IngestionPipelineV2
- [ ] 2.11 Write unit tests for each validator
- [ ] 2.12 Write integration tests
- [ ] 2.13 Add documentation and examples

**Estimated Time**: 2 days

**Note**: Mahoun has basic validation in `validation_quality.py`, but this provides a more comprehensive framework.

---

### Task 3: Move Enhanced RAG to Mahoun Core

**Source**: `domain_modules/flows/enhanced_rag.py` (Production-ready)

- [ ] 3.1 Create `mahoun/flows/` directory
- [ ] 3.2 Move `enhanced_rag.py` to `mahoun/flows/`
- [ ] 3.3 Fix imports (update paths to mahoun modules)
- [ ] 3.4 Verify all dependencies are available:
  - [ ] SmartCache
  - [ ] AdvancedQueryEnhancer
  - [ ] GATRerankerService
  - [ ] UncertaintyService
  - [ ] AnswerComposerService
  - [ ] PolicyGuardrailsService
- [ ] 3.5 Update `mahoun/__init__.py` exports
- [ ] 3.6 Write integration tests
- [ ] 3.7 Update API endpoints to use EnhancedRAGPipeline
- [ ] 3.8 Add feature flags for gradual rollout
- [ ] 3.9 Write migration guide
- [ ] 3.10 Add documentation and examples

**Estimated Time**: 1 day

**Note**: This file is production-ready and just needs to be moved with import fixes.

---

### Task 4: Implement Data Orchestrator (Optional)

**Source**: `domain_modules/pipelines/ingestion/data_orchestrator.py`

**Status**: Optional - Provides advanced orchestration features

- [ ] 4.1 Create `mahoun/pipelines/ingestion/orchestrator.py`
- [ ] 4.2 Implement DataFile dataclass
- [ ] 4.3 Implement IngestionConfig dataclass
- [ ] 4.4 Implement DataIngestionOrchestrator class
- [ ] 4.5 Add multi-source support (PDF, DOCX, JSON, TXT, XML)
- [ ] 4.6 Add parallel processing with worker pools
- [ ] 4.7 Add retry logic with exponential backoff
- [ ] 4.8 Add deduplication (hash-based + content-based)
- [ ] 4.9 Add incremental updates (track processed files)
- [ ] 4.10 Add progress tracking and statistics
- [ ] 4.11 Integrate with existing pipeline
- [ ] 4.12 Write unit tests
- [ ] 4.13 Write integration tests
- [ ] 4.14 Add documentation and examples

**Estimated Time**: 2 days

**Note**: This is optional - mahoun has basic orchestration in IngestionPipelineV2.

---

### Task 5: Comprehensive Testing

- [ ] 5.1 Write unit tests for auto-ingest service
- [ ] 5.2 Write unit tests for validators
- [ ] 5.3 Write unit tests for enhanced RAG
- [ ] 5.4 Write integration tests (ingest → graph → RAG)
- [ ] 5.5 Setup test environment (Neo4j, Redis)
- [ ] 5.6 Prepare test data (100+ legal documents)
- [ ] 5.7 Test error scenarios
- [ ] 5.8 Test edge cases
- [ ] 5.9 Achieve 90%+ test coverage
- [ ] 5.10 Fix any failing tests

**Estimated Time**: 2 days

---

### Task 6: Performance Testing & Optimization

- [ ] 6.1 Benchmark auto-ingest (files/sec)
- [ ] 6.2 Benchmark validation (docs/sec)
- [ ] 6.3 Benchmark enhanced RAG (latency p50, p95, p99)
- [ ] 6.4 Benchmark cache hit rate
- [ ] 6.5 Identify bottlenecks
- [ ] 6.6 Optimize critical paths
- [ ] 6.7 Re-run benchmarks
- [ ] 6.8 Document performance metrics

**Estimated Time**: 1 day

---

### Task 7: Documentation & Examples

- [ ] 7.1 Write API documentation for auto-ingest
- [ ] 7.2 Write API documentation for validators
- [ ] 7.3 Write API documentation for enhanced RAG
- [ ] 7.4 Create usage examples for each module
- [ ] 7.5 Write migration guide
- [ ] 7.6 Create architecture diagrams
- [ ] 7.7 Document performance benchmarks
- [ ] 7.8 Write troubleshooting guide
- [ ] 7.9 Update README.md

**Estimated Time**: 1 day

---

### Task 8: Deployment Preparation

- [ ] 8.1 Update requirements.txt (add watchdog)
- [ ] 8.2 Update pyproject.toml
- [ ] 8.3 Create deployment checklist
- [ ] 8.4 Prepare rollback plan
- [ ] 8.5 Update CI/CD pipeline
- [ ] 8.6 Create monitoring dashboards

**Estimated Time**: 0.5 day

---

### Task 9: Final Review & Sign-off

- [ ] 9.1 Code review (all new modules)
- [ ] 9.2 Architecture review
- [ ] 9.3 Security review
- [ ] 9.4 Performance review
- [ ] 9.5 Documentation review
- [ ] 9.6 Obtain sign-off from stakeholders

**Estimated Time**: 0.5 day

---

## Summary

**Total Remaining Tasks**: 9 (down from 24)  
**Total Remaining Subtasks**: ~80 (down from 200+)  
**Revised Duration**: 1-2 weeks (down from 4 weeks)  
**Team Size**: 1 developer

### Revised Phase Breakdown

| Phase | Duration | Tasks | Focus |
|-------|----------|-------|-------|
| Core Integration | 3 days | 1-3 | Auto-ingest, Validators, Enhanced RAG |
| Optional Features | 2 days | 4 | Data Orchestrator (optional) |
| Testing & QA | 3 days | 5-6 | Comprehensive testing & optimization |
| Documentation | 2 days | 7-9 | Docs, deployment, review |

### Priority Levels

**High Priority** (Must Have):
- ✅ Task 1: Auto-Ingest Service
- ✅ Task 2: Validation Framework
- ✅ Task 3: Enhanced RAG Integration
- ✅ Task 5: Comprehensive Testing

**Medium Priority** (Should Have):
- ⚠️ Task 6: Performance Testing
- ⚠️ Task 7: Documentation

**Low Priority** (Nice to Have):
- ❌ Task 4: Data Orchestrator (optional)

### Critical Path

1. **Day 1-3**: Implement missing features (Tasks 1-3)
2. **Day 4-6**: Testing and optimization (Tasks 5-6)
3. **Day 7-8**: Documentation and deployment (Tasks 7-9)

---

## 📊 Progress Tracking

**Overall Progress**: 90% Complete

- ✅ Data Ingestion: 95% (only auto-ingest missing)
- ✅ Knowledge Graph: 85% (production-ready)
- ✅ Enhanced RAG: 100% (needs to be moved)
- ⚠️ Testing: 30% (needs comprehensive tests)
- ⚠️ Documentation: 50% (needs updates)

---

**Document Version**: 2.0  
**Last Updated**: 2026-05-06  
**Status**: Revised - Only Missing Features Remain

**See Also**: `.kiro/IMPLEMENTATION_STATUS_SCAN.md` for detailed analysis
