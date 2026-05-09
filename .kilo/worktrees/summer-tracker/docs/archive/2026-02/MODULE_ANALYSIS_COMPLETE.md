# Complete Module Analysis - Mahoun Platform

**Date**: 2026-02-09  
**Purpose**: Comprehensive analysis of ALL modules for manifest completion  
**Total Modules**: 25

---

## Analysis Methodology

For each module, I analyzed:
1. **Purpose**: What does it do?
2. **Type**: Core vs Non-Core
3. **Category**: Domain Logic, Infrastructure, Adapter, Runtime, Experimental, UI
4. **Dependencies**: What does it depend on?
5. **Stability**: Stable, Experimental, Deprecated
6. **Recommendation**: Keep as-is, Move, Refactor, or Remove

---

## 📊 Module Inventory

### ✅ CORE MODULES (6 modules)

#### 1. reasoning
- **Path**: `mahoun/reasoning/`
- **Files**: 15 Python files
- **Purpose**: Evidence-linked reasoning, chain of thought, causal inference, knowledge graph
- **Type**: CORE - Domain Logic
- **Key Classes**:
  - `EvidenceLinkedVerdictEngine` ✅
  - `ChainOfThoughtReasoner` ✅
  - `DeepLegalReasoningEngine` ✅
  - `CausalInferenceEngine` ✅
  - `LegalKnowledgeGraph` ✅
  - `PolicyEngine` ✅
  - `UnifiedReasoningEngine` ⚠️ (Facade - should be adapter)
- **Dependencies**: core.models, core.logging, graph
- **Violations Found**:
  - ❌ Imports from `guardrails` (non-core)
  - ❌ Imports from `uncertainty` (non-core)
  - ❌ Imports from `core.llm` (infrastructure in core!)
- **Recommendation**: KEEP as core, but fix violations

#### 2. graph
- **Path**: `mahoun/graph/`
- **Files**: 8+ Python files, 4 subdirectories
- **Purpose**: Knowledge graph construction, traversal, analytics, Neo4j integration
- **Type**: CORE - Domain Logic
- **Key Classes**:
  - `UltraGraphBuilder` ✅
  - `GraphAnalyticsEngine` ✅
  - `GraphNode`, `GraphEdge` ✅
- **Subdirectories**:
  - `neo4j/` → Connection, schema, query builder (Infrastructure!)
  - `services/` → RAG integration (Adapter!)
  - `training/` → GAT trainer (Experimental!)
  - `optimizer/` → Graph optimization (Infrastructure!)
- **Dependencies**: core.models, schemas
- **Violations Found**:
  - ⚠️ `neo4j/` should be in infrastructure
  - ⚠️ `services/` should be in adapters
  - ⚠️ `training/` should be in experimental
- **Recommendation**: KEEP core graph logic, MOVE subdirectories

#### 3. invariants
- **Path**: `mahoun/invariants/`
- **Files**: 3 Python files
- **Purpose**: System invariants enforcement, validation, versioning
- **Type**: CORE - Domain Logic
- **Key Classes**:
  - `InvariantSpec` ✅
  - `InvariantRegistry` ✅
  - Validation functions ✅
- **Dependencies**: None (pure domain)
- **Violations Found**: None ✅
- **Recommendation**: KEEP as-is ✅

#### 4. schemas
- **Path**: `mahoun/schemas/`
- **Files**: 5+ Python files, 1 subdirectory
- **Purpose**: Pydantic models for legal documents, verdicts, entities
- **Type**: CORE - Domain Models
- **Key Classes**:
  - `VerdictStruct` ✅
  - `TextDocument` ✅
  - `CaseMeta`, `LegalReferences`, `ExtractedEntities` ✅
- **Subdirectories**:
  - `contracts/` → Contract schemas (Core!)
- **Dependencies**: None (pure models)
- **Issues Found**:
  - ⚠️ `extra="allow"` everywhere (should be `extra="forbid"` for final outputs)
  - ⚠️ `field_labels_fa.py` → UI concern (should be in UI layer)
  - ⚠️ `legal_aware_schema.py` → Infrastructure concern (court hierarchy, legal metadata)
- **Recommendation**: KEEP core schemas, MOVE UI labels, REVIEW legal_aware_schema

#### 5. ledger
- **Path**: `mahoun/ledger/`
- **Files**: 5 Python files
- **Purpose**: Immutable evidence ledger with hash chain integrity
- **Type**: CORE - Domain Logic
- **Key Classes**:
  - `EvidenceLedgerWriter` ✅
  - `LedgerEntry` ✅
  - `validate_entry` ✅
- **Dependencies**: core.models, invariants
- **Violations Found**:
  - ❌ `privacy.py` → Business logic in storage layer (should be domain service)
  - ❌ `guards.py` → Privacy filtering (should be domain service)
  - ❌ `storage.py` → Storage backends (should be infrastructure)
- **Recommendation**: KEEP core ledger logic, MOVE privacy filtering to domain service, MOVE storage to infrastructure

#### 6. core
- **Path**: `mahoun/core/`
- **Files**: 12+ Python files, 6 subdirectories
- **Purpose**: Core utilities, settings, models
- **Type**: CORE - BUT HEAVILY POLLUTED WITH INFRASTRUCTURE
- **Key Files**:
  - `models.py` ✅ (Domain models - KEEP)
  - `exceptions.py` ✅ (Domain exceptions - KEEP)
  - `protocols.py` ✅ (Abstractions - KEEP if exists)
- **Subdirectories** (ALL INFRASTRUCTURE - MUST MOVE):
  - `llm/` ❌ → LLM orchestration (Infrastructure)
  - `rag/` ❌ → RAG implementation (Infrastructure)
  - `graph/` ❌ → Graph utilities (Infrastructure)
  - `ingest/` ❌ → Data ingestion (Infrastructure)
  - `monitoring/` ❌ → System monitoring (Infrastructure)
  - `metrics/` ❌ → Metrics collection (Infrastructure)
- **Files** (ALL INFRASTRUCTURE - MUST MOVE):
  - `validation.py` ❌ → Input sanitization (Infrastructure)
  - `secrets.py` ❌ → Secret management (Infrastructure)
  - `config.py` ❌ → Configuration (Infrastructure)
  - `settings.py` ❌ → Settings (Infrastructure)
  - `serialization.py` ❌ → Serialization (Infrastructure)
  - `health_cache.py` ❌ → Health checks (Infrastructure)
  - `paths.py` ❌ → Path utilities (Infrastructure)
  - `runtime_config.py` ❌ → Runtime config (Infrastructure)
  - `singleton.py` ❌ → Singleton pattern (Infrastructure)
- **Recommendation**: **URGENT CLEANUP** - Keep only models, exceptions, protocols. Move everything else to infrastructure.

---

### 🔌 ADAPTER MODULES (5 modules)

#### 7. mcp
- **Path**: `mahoun/mcp/`
- **Files**: 5+ Python files
- **Purpose**: Model Context Protocol server for LLM integration
- **Type**: ADAPTER
- **Key Classes**: MCP server, registry, tools
- **Dependencies**: reasoning, graph, schemas
- **Stability**: Stable
- **Recommendation**: KEEP in adapters ✅

#### 8. rag
- **Path**: `mahoun/rag/`
- **Files**: 5+ Python files
- **Purpose**: Retrieval-Augmented Generation implementation
- **Type**: ADAPTER
- **Key Classes**: Query router, graph linker, evidence enrichment, indexing pipeline
- **Dependencies**: graph, schemas, retrieval
- **Stability**: Stable
- **Recommendation**: KEEP in adapters ✅

#### 9. retrieval
- **Path**: `mahoun/retrieval/`
- **Files**: 5+ Python files
- **Purpose**: Hybrid search (dense + sparse + graph)
- **Type**: ADAPTER
- **Key Classes**: Graph-enhanced retrieval, hybrid search, GAT reranker
- **Dependencies**: graph, schemas
- **Stability**: Stable
- **Recommendation**: KEEP in adapters ✅

#### 10. domain
- **Path**: `mahoun/domain/`
- **Files**: 6+ Python files
- **Purpose**: Domain-specific engines (legal, healthcare, financial)
- **Type**: ADAPTER
- **Key Classes**:
  - `BaseDomainEngine`
  - `DelayAnalysisEngine`
  - `DisputeExtractionEngine`
  - `TimelineAnalyzer`
  - `ContractClauseReasoningEngine`
  - `DelayNarrativeGenerator`
- **Dependencies**: reasoning, graph, schemas
- **Stability**: Stable
- **Recommendation**: KEEP in adapters ✅

#### 11. agents
- **Path**: `mahoun/agents/`
- **Files**: 6+ Python files, 1 subdirectory
- **Purpose**: AI agent implementations for document parsing, timeline analysis, narrative generation
- **Type**: ADAPTER
- **Key Classes**:
  - `DocParserAgent`
  - `CriticAgent`
  - `UltraTimelineAgent`
  - `NarrativeAgent`
  - `DisputeAgent`
- **Subdirectories**:
  - `archive/` → Old agent implementations (Deprecated)
- **Dependencies**: schemas, reasoning
- **Stability**: Stable
- **Recommendation**: KEEP in adapters, CLEAN UP archive ✅

---

### ⚙️ RUNTIME MODULES (5 modules)

#### 12. orchestrator
- **Path**: `mahoun/orchestrator/`
- **Files**: 5+ Python files
- **Purpose**: Workflow orchestration, task coordination, runtime profiling
- **Type**: RUNTIME
- **Key Classes**: Orchestrator, runtime profile, smoke tests, demo MVP
- **Dependencies**: reasoning, graph, agents
- **Stability**: Stable
- **Recommendation**: KEEP in runtime ✅

#### 13. pipelines
- **Path**: `mahoun/pipelines/`
- **Files**: 10+ Python files, 3 subdirectories
- **Purpose**: Data ingestion and processing pipelines
- **Type**: RUNTIME
- **Subdirectories**:
  - `ingestion/` → Document ingestion, parsing, chunking
  - `graph/` → Entity linking, graph building
  - `llm/` → LLM integration (Ollama)
  - `sync/` → Graph-vector synchronization
- **Dependencies**: schemas, graph, agents
- **Stability**: Stable
- **Recommendation**: KEEP in runtime ✅

#### 14. metrics
- **Path**: `mahoun/metrics/`
- **Files**: 3 Python files
- **Purpose**: Prometheus metrics collection
- **Type**: RUNTIME
- **Key Classes**: Metrics collector, health checks
- **Dependencies**: None (infrastructure)
- **Stability**: Stable
- **Recommendation**: KEEP in runtime ✅

#### 15. tracing
- **Path**: `mahoun/tracing/`
- **Files**: 3 Python files
- **Purpose**: Distributed tracing for observability
- **Type**: RUNTIME
- **Key Classes**: Tracing provider, middleware
- **Dependencies**: None (infrastructure)
- **Stability**: Stable
- **Recommendation**: KEEP in runtime ✅

#### 16. monitoring
- **Path**: `mahoun/monitoring/`
- **Files**: 2 Python files
- **Purpose**: System health monitoring and alerting
- **Type**: RUNTIME
- **Key Classes**: Metrics endpoint, legal metrics
- **Dependencies**: core, metrics
- **Stability**: Stable
- **Recommendation**: KEEP in runtime ✅

---

### 🧪 EXPERIMENTAL MODULES (5 modules)

#### 17. finetuning
- **Path**: `mahoun/finetuning/`
- **Files**: 6+ Python files
- **Purpose**: Model fine-tuning capabilities (Unsloth, LoRA)
- **Type**: EXPERIMENTAL
- **Key Classes**: Unsloth runner, feedback pipeline, QA generator, quality filter, trainer
- **Dependencies**: schemas, reasoning
- **Stability**: Experimental
- **Feature Flag**: `ENABLE_FINETUNING`
- **Recommendation**: KEEP in experimental ✅

#### 18. self_improve
- **Path**: `mahoun/self_improve/`
- **Files**: 5+ Python files
- **Purpose**: Self-improvement and learning mechanisms (RL, active learning, hyperparameter optimization)
- **Type**: EXPERIMENTAL
- **Key Classes**: RL agent, orchestrator, hyperparameter optimization, active learning
- **Dependencies**: reasoning, graph
- **Stability**: Experimental
- **Feature Flag**: `ENABLE_SELF_IMPROVE`
- **Recommendation**: KEEP in experimental ✅

#### 19. flows
- **Path**: `mahoun/flows/`
- **Files**: 2 Python files
- **Purpose**: Advanced workflow patterns (enhanced RAG)
- **Type**: EXPERIMENTAL
- **Key Classes**: Enhanced RAG flow
- **Dependencies**: rag, retrieval
- **Stability**: Experimental
- **Feature Flag**: `ENABLE_FLOWS`
- **Recommendation**: KEEP in experimental ✅

#### 20. profiler
- **Path**: `mahoun/profiler/`
- **Files**: 2 Python files
- **Purpose**: Performance profiling and optimization
- **Type**: EXPERIMENTAL
- **Key Classes**: Profiler
- **Dependencies**: None
- **Stability**: Experimental
- **Feature Flag**: `ENABLE_PROFILER`
- **Recommendation**: KEEP in experimental ✅

#### 21. archive
- **Path**: `mahoun/archive/`
- **Files**: 2 Python files, 1 subdirectory
- **Purpose**: Archived/deprecated code
- **Type**: EXPERIMENTAL (Deprecated)
- **Key Files**:
  - `combined_labeling_augmentation.py`
  - `graph/ultra_gat_reranker.py`
- **Dependencies**: Various
- **Stability**: Deprecated
- **Recommendation**: KEEP for reference, but mark as deprecated ✅

---

### 🎨 UI MODULES (3 modules)

#### 22. dashboard
- **Path**: `mahoun/dashboard/`
- **Files**: 2 Python files
- **Purpose**: Web dashboard for system monitoring
- **Type**: UI
- **Key Classes**: Dashboard router
- **Dependencies**: core, schemas
- **Stability**: Stable
- **Recommendation**: KEEP in UI ✅

#### 23. guardrails
- **Path**: `mahoun/guardrails/`
- **Files**: 5+ Python files
- **Purpose**: Safety guardrails and constraints (NLI verifier, citation auditor, runtime invariants)
- **Type**: UI / RUNTIME (Hybrid)
- **Key Classes**:
  - `UltraNLIVerifier`
  - `UltraCitationAuditor`
  - `RuntimeInvariants`
- **Dependencies**: invariants, reasoning
- **Stability**: Stable
- **Note**: This is actually more RUNTIME than UI, but has UI components
- **Recommendation**: RECATEGORIZE as RUNTIME ✅

#### 24. uncertainty
- **Path**: `mahoun/uncertainty/`
- **Files**: 5+ Python files
- **Purpose**: Uncertainty quantification (ensemble, Gaussian process, calibration)
- **Type**: UI / RUNTIME (Hybrid)
- **Key Classes**: Uncertainty service, ensemble, Gaussian process, calibration
- **Dependencies**: reasoning
- **Stability**: Stable
- **Note**: This is actually more RUNTIME than UI, but has UI visualization
- **Recommendation**: RECATEGORIZE as RUNTIME ✅

#### 25. (No 25th module - total is 24)

---

## 📋 Summary Statistics

### By Type:
- **Core**: 6 modules (reasoning, graph, invariants, schemas, ledger, core)
- **Adapters**: 5 modules (mcp, rag, retrieval, domain, agents)
- **Runtime**: 7 modules (orchestrator, pipelines, metrics, tracing, monitoring, guardrails, uncertainty)
- **Experimental**: 5 modules (finetuning, self_improve, flows, profiler, archive)
- **UI**: 1 module (dashboard)

### By Stability:
- **Stable**: 18 modules
- **Experimental**: 5 modules
- **Deprecated**: 1 module (archive)

### Violations Found:
- **Core Pollution**: 9 subdirectories/files in `core/` that are infrastructure
- **Boundary Violations**: 5 imports from non-core in core modules
- **Leaky Abstractions**: 2 modules (ledger privacy, schemas labels)
- **Misplaced Code**: 3 subdirectories in `graph/` that should be elsewhere

---

## 🎯 Recommendations

### Immediate Actions (P0):
1. **Clean up `mahoun/core/`**:
   - Move `llm/`, `rag/`, `graph/`, `ingest/`, `monitoring/`, `metrics/` to `mahoun/infrastructure/`
   - Move `validation.py`, `secrets.py`, `config.py`, `settings.py`, etc. to `mahoun/infrastructure/`
   - Keep only `models.py`, `exceptions.py`, `protocols.py` in core

2. **Fix boundary violations in `reasoning`**:
   - Remove direct imports from `guardrails`, `uncertainty`
   - Use dependency injection with protocols

3. **Move privacy filtering from `ledger` to domain service**:
   - Create `mahoun/domain/privacy_service.py`
   - Ledger should be "dumb and obedient"

4. **Reorganize `graph` subdirectories**:
   - Move `graph/neo4j/` to `mahoun/infrastructure/neo4j/`
   - Move `graph/services/` to `mahoun/adapters/graph_services/`
   - Move `graph/training/` to `mahoun/experimental/graph_training/`

### Short-term Actions (P1):
5. **Recategorize modules**:
   - Move `guardrails` from UI to RUNTIME
   - Move `uncertainty` from UI to RUNTIME

6. **Fix schema issues**:
   - Change `extra="forbid"` for final outputs (VerdictStruct, etc.)
   - Move `field_labels_fa.py` to UI layer
   - Review `legal_aware_schema.py` for infrastructure concerns

### Long-term Actions (P2):
7. **Decompose God Classes**:
   - Break `LegalKnowledgeGraph` into Repository + SearchEngine + HistoryManager
   - Apply SRP to other large classes

8. **Clean up archive**:
   - Document what's in archive and why
   - Consider removing if no longer needed

---

## 📊 Final Module Classification

### CORE (6):
1. reasoning ✅
2. graph ✅ (but needs cleanup)
3. invariants ✅
4. schemas ✅ (but needs fixes)
5. ledger ✅ (but needs refactoring)
6. core ✅ (but needs MAJOR cleanup)

### INFRASTRUCTURE (NEW - to be created):
- llm/ (from core)
- rag/ (from core)
- graph/ (from core)
- ingest/ (from core)
- monitoring/ (from core)
- metrics/ (from core)
- validation.py (from core)
- secrets.py (from core)
- config.py (from core)
- settings.py (from core)
- serialization.py (from core)
- health_cache.py (from core)
- paths.py (from core)
- runtime_config.py (from core)
- singleton.py (from core)
- neo4j/ (from graph)
- storage/ (from ledger)

### ADAPTERS (5):
1. mcp ✅
2. rag ✅
3. retrieval ✅
4. domain ✅
5. agents ✅

### RUNTIME (7):
1. orchestrator ✅
2. pipelines ✅
3. metrics ✅
4. tracing ✅
5. monitoring ✅
6. guardrails ✅ (recategorized from UI)
7. uncertainty ✅ (recategorized from UI)

### EXPERIMENTAL (5):
1. finetuning ✅
2. self_improve ✅
3. flows ✅
4. profiler ✅
5. archive ✅ (deprecated)

### UI (1):
1. dashboard ✅

---

**Status**: ANALYSIS COMPLETE  
**Next Step**: Update manifests with this complete analysis
