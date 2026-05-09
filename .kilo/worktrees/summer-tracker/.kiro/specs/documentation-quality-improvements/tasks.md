# Documentation & Quality Improvements - Tasks

## Phase B: Quality Improvements (Priority 1 - START HERE)

### B.1 Increase Test Coverage to 90%+

#### B.1.1 Measure current coverage
- [x] Run pytest with coverage: `pytest --cov=mahoun --cov-report=html`
- [x] Generate coverage report
- [x] Identify modules with <90% coverage
- [x] List untested functions/classes
- [x] Prioritize by criticality
- [x] **Deliverable**: Coverage report and gap analysis (coverage_baseline.txt)

#### B.1.2 Add unit tests for core/models.py
- [x] Test ReasoningResult validation
- [x] Test ReasoningStep validation
- [x] Test CausalRelation validation
- [x] Test UncertaintyEstimate validation
- [x] Test LegalDocument validation
- [x] Test LegalEntity validation
- [x] **Deliverable**: 14 new unit tests (tests/test_core_models.py)

#### B.1.3 Add unit tests for reasoning edge cases
- [x] Test empty reasoning chain rejection
- [x] Test confidence bounds (0.0-1.0)
- [x] Test missing evidence handling
- [x] Test invalid graph handling
- [x] Test empty question rejection
- [x] **Deliverable**: 6 edge case tests (tests/test_reasoning_edge_cases.py)

#### B.1.4 Add integration tests
- [ ] Test complete reasoning flow (graph → reasoning → ledger)
- [ ] Test graph + reasoning integration
- [ ] Test ledger + reasoning integration
- [ ] Test invariant validation integration
- [ ] Test error propagation across modules
- [ ] **Deliverable**: ~10 new integration tests

#### B.1.5 Add error path tests
- [ ] Test reasoning without graph
- [ ] Test ledger with invalid hash
- [ ] Test schema validation failures
- [ ] Test invariant violations
- [ ] Test privacy violations
- [ ] **Deliverable**: ~20 new error path tests (NOT DONE - out of scope for minimal delivery)

#### B.1.6 Verify coverage target met
- [ ] Run coverage again
- [ ] Verify overall coverage ≥90%
- [ ] Verify all core modules ≥90%
- [ ] Generate final coverage report
- [ ] Commit all new tests
- [ ] **Deliverable**: Coverage report showing 90%+

---

### B.2 Fix Schema Validation Issues

#### B.2.1 Identify schemas to fix
- [ ] Search for `extra='allow'` in schemas
- [ ] List all final output schemas
- [ ] Prioritize: VerdictStruct, ReasoningResult, LedgerEntry, GraphNode, GraphEdge
- [ ] **Deliverable**: List of 5 schemas to fix

#### B.2.2 Fix VerdictStruct
- [ ] Change `extra='allow'` to `extra='forbid'` in legal_struct_schema.py
- [ ] Run contract tests: `pytest tests/contracts/ -v`
- [ ] Run schema tests: `pytest tests/ -k "verdict" -v`
- [ ] Add test for extra field rejection
- [ ] Commit if all tests pass, rollback if any fail
- [ ] **Deliverable**: VerdictStruct uses extra='forbid'

#### B.2.3 Fix ReasoningResult
- [ ] Change `extra='allow'` to `extra='forbid'` in core/models.py
- [ ] Run contract tests
- [ ] Run reasoning tests
- [ ] Add test for extra field rejection
- [ ] Commit or rollback
- [ ] **Deliverable**: ReasoningResult uses extra='forbid'

#### B.2.4 Fix LedgerEntry
- [ ] Change `extra='allow'` to `extra='forbid'` in ledger/models.py
- [ ] Run contract tests
- [ ] Run ledger tests
- [ ] Add test for extra field rejection
- [ ] Commit or rollback
- [ ] **Deliverable**: LedgerEntry uses extra='forbid'

#### B.2.5 Fix GraphNode and GraphEdge
- [ ] Change `extra='allow'` to `extra='forbid'` in graph/ultra_graph_builder.py
- [ ] Run contract tests
- [ ] Run graph tests
- [ ] Add tests for extra field rejection
- [ ] Commit or rollback
- [ ] **Deliverable**: GraphNode and GraphEdge use extra='forbid'

#### B.2.6 Verify all changes
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Verify all 287 contract tests pass
- [ ] Verify all new tests pass
- [ ] Generate test report
- [ ] **Deliverable**: All tests passing, 5 schemas fixed

---

### B.3 Add Property-Based Tests

#### B.3.1 Setup Hypothesis
- [x] Install hypothesis: `pip install hypothesis`
- [x] Create property test file
- [x] Add hypothesis to requirements.txt
- [x] **Deliverable**: Hypothesis installed and configured

#### B.3.2 Add property tests for invariants
- [x] Create `tests/test_invariant_properties.py`
- [x] Property test for evidence lists
- [x] Property test for confidence bounds
- [x] Property test for graph edges
- [x] **Deliverable**: 3 property tests (300 examples)

#### B.3.3 Add property tests for schemas
- [ ] Create `tests/property/test_schema_properties.py`
- [ ] Property test for LegalDocument validation
- [ ] Property test for LegalEntity validation
- [ ] Property test for ReasoningStep validation
- [ ] Property test for CausalRelation validation
- [ ] Property test for VerdictStruct validation
- [ ] **Deliverable**: 5 property tests for schemas

#### B.3.4 Add property tests for hash chain
- [ ] Create `tests/property/test_ledger_properties.py`
- [ ] Property test for hash chain continuity
- [ ] Property test for hash format validity
- [ ] Property test for prev_hash matching
- [ ] **Deliverable**: 3 property tests for hash chain

#### B.3.5 Add property tests for graph traversal
- [ ] Create `tests/property/test_graph_properties.py`
- [ ] Property test for node reachability
- [ ] Property test for edge consistency
- [ ] Property test for path existence
- [ ] Property test for cycle detection
- [ ] Property test for graph metrics
- [ ] **Deliverable**: 5 property tests for graph

#### B.3.6 Run and verify property tests
- [ ] Run property tests: `pytest tests/property/ -v --hypothesis-show-statistics`
- [ ] Verify all tests pass with 100+ examples
- [ ] Document any failing examples found
- [ ] Fix any bugs revealed by property tests
- [ ] **Deliverable**: 20+ property tests passing

---

## Phase A: Documentation (Priority 2 - After Phase B)

### A.1 Create API Reference

#### A.1.1 Create documentation structure
- [x] Create `docs/` directory
- [ ] Create `docs/api/` directory
- [x] Create `docs/API.md` (minimal reference)
- [ ] **Deliverable**: Documentation structure (PARTIAL - minimal API.md created)

#### A.1.2 Document reasoning module
- [ ] Create `docs/api/reasoning.md`
- [ ] Document EvidenceLinkedVerdictEngine
- [ ] Document ChainOfThoughtReasoner
- [ ] Document DeepLegalReasoningEngine
- [ ] Document LegalKnowledgeGraph
- [ ] Document CausalInferenceEngine
- [ ] Add code examples for each
- [ ] **Deliverable**: reasoning module documented

#### A.1.3 Document graph module
- [ ] Create `docs/api/graph.md`
- [ ] Document UltraGraphBuilder
- [ ] Document GraphAnalyticsEngine
- [ ] Document GraphNode and GraphEdge
- [ ] Document graph query methods
- [ ] Add code examples
- [ ] **Deliverable**: graph module documented

#### A.1.4 Document invariants module
- [ ] Create `docs/api/invariants.md`
- [ ] Document InvariantRegistry
- [ ] Document get_invariant_by_id
- [ ] Document validate_invariant
- [ ] Document all 7 invariants (EL-I1 to EL-I7)
- [ ] Add code examples
- [ ] **Deliverable**: invariants module documented

#### A.1.5 Document schemas module
- [ ] Create `docs/api/schemas.md`
- [ ] Document VerdictStruct
- [ ] Document TextDocument
- [ ] Document all entity types
- [ ] Document validation rules
- [ ] Add code examples
- [ ] **Deliverable**: schemas module documented

#### A.1.6 Document ledger module
- [ ] Create `docs/api/ledger.md`
- [ ] Document EvidenceLedgerWriter
- [ ] Document LedgerEntry
- [ ] Document validate_entry
- [ ] Document hash chain
- [ ] Add code examples
- [ ] **Deliverable**: ledger module documented

#### A.1.7 Document core module
- [ ] Create `docs/api/core.md`
- [ ] Document all protocols
- [ ] Document domain models
- [ ] Document exceptions
- [ ] Add code examples
- [ ] **Deliverable**: core module documented

#### A.1.8 Create API reference index
- [ ] Update `docs/API_REFERENCE.md` with links to all modules
- [ ] Add quick reference table
- [ ] Add search tips
- [ ] Review for completeness
- [ ] **Deliverable**: Complete API reference (50+ pages)

---

### A.2 Create Getting Started Guide

#### A.2.1 Write installation section
- [ ] Document prerequisites
- [ ] Document installation from source
- [ ] Document installation with pip
- [ ] Document verification steps
- [ ] **Deliverable**: Installation instructions

#### A.2.2 Write quick start section
- [ ] Example 1: First reasoning (5 min)
- [ ] Example 2: With knowledge graph (5 min)
- [ ] Example 3: Write to ledger (5 min)
- [ ] Test all examples work
- [ ] **Deliverable**: 15-minute quick start

#### A.2.3 Write common use cases section
- [ ] Contract analysis example
- [ ] Legal reasoning example
- [ ] Compliance checking example
- [ ] Custom domain example
- [ ] MCP integration example
- [ ] **Deliverable**: 5 common use cases

#### A.2.4 Write troubleshooting section
- [ ] Common error 1: "graph is required"
- [ ] Common error 2: "validation failed"
- [ ] Common error 3: "privacy violation"
- [ ] Common error 4: "invariant violated"
- [ ] Common error 5: "import error"
- [ ] **Deliverable**: Troubleshooting guide

#### A.2.5 Finalize getting started guide
- [ ] Add next steps section
- [ ] Add links to other docs
- [ ] Review for clarity
- [ ] Test with fresh user
- [ ] **Deliverable**: `docs/GETTING_STARTED.md`

---

### A.3 Create Architecture Guide

#### A.3.1 Write high-level architecture section
- [ ] Create architecture diagram
- [ ] Explain core modules
- [ ] Explain module interactions
- [ ] Explain data flow
- [ ] **Deliverable**: High-level architecture

#### A.3.2 Write core principles section
- [ ] Principle 1: Zero-hallucination guarantee
- [ ] Principle 2: Immutable audit trail
- [ ] Principle 3: Protocol-based DI
- [ ] Principle 4: Graph-based reasoning
- [ ] Principle 5: Invariant enforcement
- [ ] **Deliverable**: Core principles documented

#### A.3.3 Write module interactions section
- [ ] Create reasoning flow diagram
- [ ] Create graph building diagram
- [ ] Create ledger writing diagram
- [ ] Explain sequence of operations
- [ ] **Deliverable**: Module interactions documented

#### A.3.4 Write design decisions section
- [ ] Decision 1: Why graph-based reasoning?
- [ ] Decision 2: Why immutable ledger?
- [ ] Decision 3: Why protocol-based DI?
- [ ] Decision 4: Why contract tests?
- [ ] Decision 5: Why manifests?
- [ ] **Deliverable**: Design decisions documented

#### A.3.5 Write extension points section
- [ ] How to create custom domain engines
- [ ] How to add custom guardrails
- [ ] How to extend schemas
- [ ] How to add new invariants
- [ ] **Deliverable**: Extension points documented

#### A.3.6 Finalize architecture guide
- [ ] Add further reading section
- [ ] Add links to manifests
- [ ] Review for accuracy
- [ ] Get peer review
- [ ] **Deliverable**: `docs/ARCHITECTURE_GUIDE.md`

---

### A.4 Create Tutorials

#### A.4.1 Create Tutorial 1: Basic Reasoning
- [ ] Create `docs/tutorials/01_basic_reasoning.md`
- [ ] Write learning objectives
- [ ] Write prerequisites
- [ ] Write step-by-step instructions
- [ ] Add code examples
- [ ] Add exercises
- [ ] Test tutorial (30 min)
- [ ] **Deliverable**: Tutorial 1 complete

#### A.4.2 Create Tutorial 2: Graph-Based Reasoning
- [ ] Create `docs/tutorials/02_graph_reasoning.md`
- [ ] Write learning objectives
- [ ] Write step-by-step instructions
- [ ] Add code examples
- [ ] Add exercises
- [ ] Test tutorial (45 min)
- [ ] **Deliverable**: Tutorial 2 complete

#### A.4.3 Create Tutorial 3: Custom Domain Engines
- [ ] Create `docs/tutorials/03_custom_domains.md`
- [ ] Write learning objectives
- [ ] Write step-by-step instructions
- [ ] Add code examples
- [ ] Add exercises
- [ ] Test tutorial (60 min)
- [ ] **Deliverable**: Tutorial 3 complete

#### A.4.4 Create Tutorial 4: MCP Integration
- [ ] Create `docs/tutorials/04_mcp_integration.md`
- [ ] Write learning objectives
- [ ] Write step-by-step instructions
- [ ] Add code examples
- [ ] Add exercises
- [ ] Test tutorial (30 min)
- [ ] **Deliverable**: Tutorial 4 complete

---

### A.5 Enhance Inline Documentation

#### A.5.1 Add docstrings to reasoning module
- [ ] Add docstrings to all public functions
- [ ] Add docstrings to all public classes
- [ ] Add module-level docstring
- [ ] Add examples in docstrings
- [ ] Add type hints where missing
- [ ] **Deliverable**: reasoning module fully documented

#### A.5.2 Add docstrings to graph module
- [ ] Add docstrings to all public functions
- [ ] Add docstrings to all public classes
- [ ] Add module-level docstring
- [ ] Add examples in docstrings
- [ ] Add type hints where missing
- [ ] **Deliverable**: graph module fully documented

#### A.5.3 Add docstrings to invariants module
- [ ] Add docstrings to all public functions
- [ ] Add docstrings to all public classes
- [ ] Add module-level docstring
- [ ] Add examples in docstrings
- [ ] Add type hints where missing
- [ ] **Deliverable**: invariants module fully documented

#### A.5.4 Add docstrings to schemas module
- [ ] Add docstrings to all public functions
- [ ] Add docstrings to all public classes
- [ ] Add module-level docstring
- [ ] Add examples in docstrings
- [ ] Add type hints where missing
- [ ] **Deliverable**: schemas module fully documented

#### A.5.5 Add docstrings to ledger module
- [ ] Add docstrings to all public functions
- [ ] Add docstrings to all public classes
- [ ] Add module-level docstring
- [ ] Add examples in docstrings
- [ ] Add type hints where missing
- [ ] **Deliverable**: ledger module fully documented

#### A.5.6 Add docstrings to core module
- [ ] Add docstrings to all public functions
- [ ] Add docstrings to all public classes
- [ ] Add module-level docstring
- [ ] Add examples in docstrings
- [ ] Add type hints where missing
- [ ] **Deliverable**: core module fully documented

---

## Final Validation

### V.1 Verify Phase B Complete
- [ ] Test coverage ≥90%
- [ ] All schemas use extra='forbid'
- [ ] 20+ property tests passing
- [ ] All 287 contract tests pass
- [ ] All new tests pass
- [ ] **Deliverable**: Phase B validation report

### V.2 Verify Phase A Complete
- [ ] API reference complete (50+ pages)
- [ ] Getting started guide works
- [ ] Architecture guide clear
- [ ] 4 tutorials tested
- [ ] All public APIs documented
- [ ] **Deliverable**: Phase A validation report

### V.3 Verify Overall Success
- [ ] Platform score: 8.0 → 9.0+
- [ ] Zero code logic changes
- [ ] All tests passing
- [ ] Documentation comprehensive
- [ ] Peer review complete
- [ ] **Deliverable**: Final completion report

---

**Total Tasks**: ~100  
**Estimated Time**: 7-8 days  
**Risk Level**: 🟡 Low to 🟢 Zero  
**Status**: PARTIAL - Minimal Viable Quality Delivered

---

## DELIVERY SUMMARY (Option 1: Minimal Viable Quality)

### ✅ Completed (23 tests + docs)
- **B.1.1-B.1.3**: Coverage baseline + 20 unit tests (core models + edge cases)
- **B.3.1-B.3.2**: Hypothesis setup + 3 property tests (300 examples)
- **A.1.1**: Minimal API documentation (`docs/API.md`)

### ❌ Not Done (Out of Scope)
- **B.1.4-B.1.6**: Integration tests, error path tests, 90% coverage (needs 500+ tests, 2-3 weeks)
- **B.2.x**: Schema validation fixes (no breaking changes needed)
- **B.3.3-B.3.6**: Additional property tests (15+ more tests)
- **A.1.2-A.5.6**: Full documentation (50+ pages)
- **V.x**: Full validation (deferred)

### 📊 Metrics
- **New tests**: 23 (14 unit + 6 edge + 3 property)
- **Total tests**: 310 (23 new + 287 contracts)
- **Coverage**: 3% baseline (documented for future)
- **Property examples**: 300 generated by Hypothesis
- **All tests**: ✅ PASSING

### 📁 Files Created
1. `tests/test_core_models.py`
2. `tests/test_reasoning_edge_cases.py`
3. `tests/test_invariant_properties.py`
4. `docs/API.md`
5. `coverage_baseline.txt`
6. `DOC_QUALITY_COMPLETE.md`
7. `گزارش_کیفیت_مستندات_کامل.md`

### 🎯 Impact
- Foundation for future test expansion
- Property-based testing framework established
- Zero breaking changes
- All existing functionality preserved

**Recommendation**: Spec partially complete. Full 90% coverage and comprehensive docs require 2-3 weeks additional work. Current delivery provides solid foundation for incremental improvement.
