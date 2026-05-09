# Requirements Document: Domain Modules Integration (Ingestion, Graph, RAG)

## Overview

این سند نیازمندی‌های یکپارچه‌سازی ماژول‌های **data ingestion, knowledge graph building, و RAG** از `domain_modules/` به هسته Mahoun را مشخص می‌کند.

**Feature Name**: domain-modules-integration  
**Priority**: High  
**Target Release**: v1.1  
**Estimated Effort**: 4 weeks

---

## Business Requirements

### BR-1: Automated Legal Document Ingestion

**Description**: سیستم باید قادر به ingestion خودکار اسناد حقوقی با فرمت‌های مختلف باشد.

**Acceptance Criteria**:
- سیستم باید PDF, DOCX, TXT, JSON را پشتیبانی کند
- ingestion باید خودکار و بدون دخالت manual انجام شود
- metadata اسناد باید به طور خودکار استخراج شود
- خطاها باید به طور مناسب handle شوند

**Business Value**: کاهش 90% زمان manual data entry

---

### BR-2: Knowledge Graph Construction

**Description**: سیستم باید قادر به ساخت خودکار knowledge graph از اسناد حقوقی باشد.

**Acceptance Criteria**:
- entities حقوقی (قانون، ماده، پرونده، دادگاه) باید استخراج شوند
- روابط بین entities باید شناسایی شوند
- graph باید در Neo4j ذخیره شود
- hierarchy قوانین (قانون → فصل → ماده) باید حفظ شود

**Business Value**: دسترسی ساختاریافته به دانش حقوقی

---

### BR-3: Enhanced RAG with Graph

**Description**: سیستم RAG باید از knowledge graph برای بهبود retrieval استفاده کند.

**Acceptance Criteria**:
- retrieval باید از graph traversal استفاده کند
- multi-hop reasoning باید پشتیبانی شود
- نتایج باید از cache استفاده کنند
- latency باید < 500ms باشد (p95)

**Business Value**: افزایش 30% دقت پاسخ‌ها

---

## Functional Requirements

### FR-1: Document Parsing

**Description**: پارس کردن فرمت‌های مختلف اسناد

**Requirements**:
- FR-1.1: پارس PDF با پشتیبانی OCR
- FR-1.2: پارس DOCX با حفظ ساختار
- FR-1.3: پارس TXT با تشخیص encoding
- FR-1.4: پارس JSON برای داده‌های ساختاریافته
- FR-1.5: استخراج metadata (عنوان، تاریخ، نویسنده)

**Priority**: Must Have

---

### FR-2: Data Validation

**Description**: اعتبارسنجی داده‌های ingested

**Requirements**:
- FR-2.1: validation در برابر schema
- FR-2.2: بررسی کیفیت محتوا
- FR-2.3: بررسی completeness metadata
- FR-2.4: validation ساختار اسناد حقوقی

**Priority**: Must Have

---

### FR-3: Entity Extraction

**Description**: استخراج entities حقوقی از متن

**Requirements**:
- FR-3.1: استخراج LAW (قانون)
- FR-3.2: استخراج ARTICLE (ماده)
- FR-3.3: استخراج CASE (پرونده)
- FR-3.4: استخراج COURT (دادگاه)
- FR-3.5: استخراج PERSON (شخص)
- FR-3.6: استخراج ORGANIZATION (سازمان)
- FR-3.7: استخراج DATE (تاریخ)
- FR-3.8: استخراج LOCATION (مکان)
- FR-3.9: confidence scoring برای هر entity

**Priority**: Must Have

---

### FR-4: Relationship Extraction

**Description**: استخراج روابط بین entities

**Requirements**:
- FR-4.1: شناسایی REFERENCES (ارجاع)
- FR-4.2: شناسایی AMENDS (اصلاح)
- FR-4.3: شناسایی REPEALS (نسخ)
- FR-4.4: شناسایی CITES (استناد)
- FR-4.5: شناسایی APPLIES_TO (اعمال)
- FR-4.6: شناسایی CONTRADICTS (تناقض)
- FR-4.7: confidence scoring برای هر relationship

**Priority**: Must Have

---

### FR-5: Graph Import

**Description**: import داده‌ها به Neo4j

**Requirements**:
- FR-5.1: batch import برای entities
- FR-5.2: batch import برای relationships
- FR-5.3: transaction management
- FR-5.4: duplicate detection
- FR-5.5: error recovery
- FR-5.6: progress tracking

**Priority**: Must Have

---

### FR-6: Law Import

**Description**: import تخصصی قوانین

**Requirements**:
- FR-6.1: import hierarchy (قانون → فصل → ماده)
- FR-6.2: حل cross-references
- FR-6.3: tracking amendments
- FR-6.4: version management

**Priority**: Must Have

---

### FR-7: Graph-Aware Retrieval

**Description**: retrieval با استفاده از graph

**Requirements**:
- FR-7.1: retrieval بر اساس entity
- FR-7.2: retrieval بر اساس relationship
- FR-7.3: graph traversal (max 2 hops)
- FR-7.4: subgraph extraction
- FR-7.5: Cypher query generation

**Priority**: Must Have

---

### FR-8: Enhanced RAG

**Description**: RAG پیشرفته با graph

**Requirements**:
- FR-8.1: hybrid retrieval (vector + graph + BM25)
- FR-8.2: multi-hop reasoning
- FR-8.3: context expansion via graph
- FR-8.4: result caching
- FR-8.5: confidence scoring

**Priority**: Must Have

---

### FR-9: Smart Caching

**Description**: caching چند سطحی

**Requirements**:
- FR-9.1: L1 cache (memory)
- FR-9.2: L2 cache (Redis)
- FR-9.3: semantic similarity matching
- FR-9.4: adaptive TTL
- FR-9.5: cache analytics

**Priority**: Should Have

---

### FR-10: Data Orchestration

**Description**: هماهنگی end-to-end pipeline

**Requirements**:
- FR-10.1: orchestration از ingestion تا graph
- FR-10.2: parallel processing
- FR-10.3: error recovery
- FR-10.4: checkpoint/resume
- FR-10.5: progress monitoring

**Priority**: Must Have

---

## Non-Functional Requirements

### NFR-1: Performance

**Requirements**:
- NFR-1.1: Ingestion: 10+ documents/second
- NFR-1.2: Entity extraction: 100+ entities/second
- NFR-1.3: Graph import: 1000+ nodes/second
- NFR-1.4: RAG retrieval latency: < 500ms (p95)
- NFR-1.5: Cache hit rate: > 60%

**Priority**: Must Have

---

### NFR-2: Scalability

**Requirements**:
- NFR-2.1: پشتیبانی از 100K+ documents
- NFR-2.2: پشتیبانی از 1M+ graph nodes
- NFR-2.3: پشتیبانی از 10M+ relationships
- NFR-2.4: horizontal scaling برای ingestion
- NFR-2.5: connection pooling برای Neo4j

**Priority**: Must Have

---

### NFR-3: Reliability

**Requirements**:
- NFR-3.1: error recovery در ingestion
- NFR-3.2: transaction rollback در graph import
- NFR-3.3: retry logic با exponential backoff
- NFR-3.4: graceful degradation (fallback to vector-only RAG)
- NFR-3.5: comprehensive logging

**Priority**: Must Have

---

### NFR-4: Maintainability

**Requirements**:
- NFR-4.1: test coverage > 90%
- NFR-4.2: type hints برای همه functions
- NFR-4.3: docstrings برای همه public APIs
- NFR-4.4: clean architecture (zero boundary violations)
- NFR-4.5: absolute imports (no relative imports)

**Priority**: Must Have

---

### NFR-5: Observability

**Requirements**:
- NFR-5.1: structured logging
- NFR-5.2: progress tracking
- NFR-5.3: error reporting
- NFR-5.4: performance metrics
- NFR-5.5: cache analytics

**Priority**: Should Have

---

## Technical Requirements

### TR-1: Integration with Existing Code

**Requirements**:
- TR-1.1: استفاده از Neo4j connection موجود
- TR-1.2: integration با HybridRAGService موجود
- TR-1.3: استفاده از schemas موجود
- TR-1.4: backward compatibility برای APIs موجود

**Priority**: Must Have

---

### TR-2: Dependencies

**Requirements**:
- TR-2.1: PyPDF2 یا pdfplumber برای PDF
- TR-2.2: python-docx برای DOCX
- TR-2.3: transformers برای NER
- TR-2.4: redis برای L2 cache
- TR-2.5: استفاده از dependencies موجود (neo4j, sentence-transformers)

**Priority**: Must Have

---

### TR-3: Testing

**Requirements**:
- TR-3.1: unit tests برای همه modules
- TR-3.2: integration tests برای pipelines
- TR-3.3: performance tests
- TR-3.4: end-to-end tests
- TR-3.5: test data (real legal documents)

**Priority**: Must Have

---

### TR-4: Documentation

**Requirements**:
- TR-4.1: API documentation
- TR-4.2: usage examples
- TR-4.3: migration guide
- TR-4.4: architecture diagrams
- TR-4.5: performance benchmarks

**Priority**: Must Have

---

## User Stories

### US-1: Legal Researcher - Document Ingestion

**As a** legal researcher  
**I want to** automatically ingest legal documents  
**So that** I don't have to manually enter data

**Acceptance Criteria**:
- Given a folder of PDF documents
- When I run the ingestion pipeline
- Then all documents are parsed and validated
- And metadata is extracted automatically
- And errors are logged clearly

---

### US-2: Legal Researcher - Knowledge Graph Query

**As a** legal researcher  
**I want to** query the knowledge graph  
**So that** I can find related laws and cases

**Acceptance Criteria**:
- Given a law article
- When I query for related entities
- Then I see all referenced laws, cases, and amendments
- And relationships are clearly shown
- And results are returned in < 1 second

---

### US-3: Legal Researcher - Enhanced RAG

**As a** legal researcher  
**I want to** ask questions about legal documents  
**So that** I get accurate answers with graph context

**Acceptance Criteria**:
- Given a legal question
- When I submit the query
- Then the system retrieves relevant documents using graph
- And provides context from related entities
- And caches the result for future queries
- And responds in < 500ms

---

### US-4: System Administrator - Bulk Import

**As a** system administrator  
**I want to** import a large corpus of legal documents  
**So that** the knowledge graph is populated

**Acceptance Criteria**:
- Given 1000+ legal documents
- When I run the bulk import
- Then all documents are processed in parallel
- And progress is tracked
- And errors are recoverable
- And the process completes in < 2 hours

---

### US-5: Developer - API Integration

**As a** developer  
**I want to** integrate the enhanced RAG into my application  
**So that** my users can benefit from graph-aware retrieval

**Acceptance Criteria**:
- Given the API documentation
- When I call the enhanced RAG API
- Then I receive results with graph context
- And the API is backward compatible
- And examples are provided

---

## Constraints

### C-1: Architecture

- باید clean architecture حفظ شود (zero boundary violations)
- باید از absolute imports استفاده شود
- باید با معماری موجود Mahoun سازگار باشد

---

### C-2: Performance

- RAG latency باید < 500ms باشد (p95)
- Graph import باید > 1000 nodes/sec باشد
- Cache hit rate باید > 60% باشد

---

### C-3: Compatibility

- باید با Neo4j 5.x سازگار باشد
- باید با Python 3.12+ سازگار باشد
- باید backward compatible با APIs موجود باشد

---

### C-4: Deployment

- فقط ENTERPRISE_FULL mode
- نیازی به DESKTOP_MINIMAL support نیست

---

## Assumptions

### A-1: Data Availability

- اسناد حقوقی در فرمت‌های استاندارد (PDF, DOCX) موجود هستند
- metadata اسناد در دسترس است (حداقل عنوان و تاریخ)

---

### A-2: Infrastructure

- Neo4j instance در دسترس است
- Redis instance برای caching در دسترس است
- منابع کافی برای NER models موجود است

---

### A-3: Existing Code

- Neo4j connection در mahoun core production-ready است
- HybridRAGService موجود قابل extend است
- schemas موجود کافی هستند

---

## Dependencies

### External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| PyPDF2 | ^3.0.0 | PDF parsing |
| pdfplumber | ^0.10.0 | Advanced PDF parsing |
| python-docx | ^1.0.0 | DOCX parsing |
| chardet | ^5.0.0 | Encoding detection |
| transformers | ^4.35.0 | NER models |
| torch | ^2.1.0 | ML backend |
| redis | ^5.0.0 | L2 cache |

### Internal Dependencies

| Module | Purpose |
|--------|---------|
| mahoun.graph.neo4j.connection | Neo4j connectivity |
| mahoun.rag.hybrid_rag_service | Existing RAG |
| mahoun.schemas | Data schemas |
| mahoun.core.runtime_config | Runtime settings |

---

## Risks

### R-1: Performance Degradation

**Risk**: Graph operations might slow down RAG

**Likelihood**: Medium  
**Impact**: High  
**Mitigation**: Smart caching, query optimization, optional graph retrieval

---

### R-2: Data Quality

**Risk**: Extracted entities/relationships might have low accuracy

**Likelihood**: Medium  
**Impact**: Medium  
**Mitigation**: Multi-stage validation, confidence scoring, manual review workflow

---

### R-3: Integration Complexity

**Risk**: Integration might break existing functionality

**Likelihood**: Low  
**Impact**: High  
**Mitigation**: Comprehensive tests, backward compatibility, feature flags

---

### R-4: Resource Requirements

**Risk**: NER models might require significant resources

**Likelihood**: Medium  
**Impact**: Medium  
**Mitigation**: Model optimization, batch processing, resource monitoring

---

## Success Metrics

### Functional Metrics

- ✅ 1000+ documents ingested successfully
- ✅ 85%+ entity extraction accuracy
- ✅ 100K+ graph nodes created
- ✅ Enhanced RAG working end-to-end
- ✅ 60%+ cache hit rate

### Quality Metrics

- ✅ 90%+ test coverage
- ✅ Zero boundary violations
- ✅ Zero critical bugs in production

### Performance Metrics

- ✅ RAG latency < 500ms (p95)
- ✅ Graph import > 1000 nodes/sec
- ✅ Ingestion > 10 docs/sec

---

## Out of Scope

این موارد در این فاز شامل نمی‌شوند:

- ❌ Monitoring modules (alerting, anomaly detection)
- ❌ Security modules (PII scrubber, RBAC)
- ❌ Training modules (LoRA fine-tuning)
- ❌ Advanced ML modules (GNN, active learning)
- ❌ Self-improvement modules
- ❌ DESKTOP_MINIMAL mode support
- ❌ Quantum/neuromorphic modules

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | - | - | - |
| Tech Lead | - | - | - |
| QA Lead | - | - | - |

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-06  
**Status**: Ready for Task Breakdown
