# Monitoring Architecture Unification - Requirements (REFACTORING)

## Overview

This document specifies the business and technical requirements for REFACTORING Mahoun's monitoring architecture to eliminate dual-state management while preserving all enterprise features.

**Context**: This is NOT new development - it's cleanup of an existing world-class system.

## Business Requirements

### BR1: Zero Performance Degradation
**Priority**: Critical  
**Rationale**: Mahoun is a zero-hallucination platform for high-stakes decisions.

**Acceptance Criteria**:
- Metric tracking overhead < 1ms per operation
- P95 latency for verdict generation unchanged (±5%)
- Memory footprint reduced by ~1KB (9 fewer variables)
- CPU overhead unchanged

### BR2: Full Auditability (Preserved)
**Priority**: Critical  
**Rationale**: Regulatory compliance requires complete audit trails.

**Acceptance Criteria**:
- All existing audit features preserved
- Metrics include court rank, legal domain, authority score
- Audit trail includes timestamps, operation types, metadata
- No loss of monitoring data during refactoring

### BR3: Zero Data Loss During Refactoring
**Priority**: High  
**Rationale**: Continuous monitoring is essential.

**Acceptance Criteria**:
- No metrics lost during refactoring
- Rollback capability at each step
- All tests pass before and after

### BR4: Type Safety Compliance
**Priority**: High  
**Rationale**: Type safety prevents runtime errors.

**Acceptance Criteria**:
- 100% mypy compliance with strict mode
- All deque instances have explicit type annotations
- No `Any` types in public APIs
- Type checking passes in CI pipeline

### BR5: Deterministic Behavior (Preserved)
**Priority**: Critical  
**Rationale**: Mahoun's core invariant (I1) requires deterministic behavior.

**Acceptance Criteria**:
- Metrics operations remain deterministic
- Concurrent operations produce consistent results
- Percentile calculations unchanged
- Error rates calculated consistently

## Technical Requirements

### TR1: Remove Duplicate State
**Priority**: Critical  
**Rationale**: Eliminate architectural contamination.

**Acceptance Criteria**:
- Remove 9 duplicate counter variables from `__init__`
- All metric storage delegated to MetricsCollector
- Only rolling windows remain for percentile calculations
- No local counters that duplicate collector state

**Specific Variables to Remove**:
```python
# DELETE THESE (lines 220-230):
self.total_queries = 0
self.total_filtered = 0
self.total_errors = 0
self.cache_hits = 0
self.cache_misses = 0
self.queries_by_status = defaultdict(int)
self.queries_by_court = defaultdict(int)
self.queries_by_domain = defaultdict(int)
self.errors_by_type = defaultdict(int)
```

### TR2: Add Type Annotations
**Priority**: High  
**Rationale**: Type safety and mypy compliance.

**Acceptance Criteria**:
- All deques have explicit `Deque[T]` type hints
- Import `Deque` from `typing`
- No mypy errors in strict mode

**Specific Changes**:
```python
# ADD TYPE HINTS:
from typing import Deque

self.recent_durations: Deque[float] = deque(maxlen=window_size)
self.recent_filtered: Deque[int] = deque(maxlen=window_size)
self.recent_authority_scores: Deque[float] = deque(maxlen=window_size)
self.recent_query_metrics: Deque[LegalQueryMetrics] = deque(maxlen=window_size)
```

### TR3: Refactor get_stats() Method
**Priority**: Critical  
**Rationale**: Stats must come from collector, not local state.

**Acceptance Criteria**:
- Use `collector.snapshot()` to get metrics
- Extract counters from snapshot
- Calculate percentiles from rolling windows only
- No references to removed local state variables

### TR4: Refactor track_legal_query() Method
**Priority**: Critical  
**Rationale**: Remove local state updates.

**Acceptance Criteria**:
- Remove all `self.total_* +=` operations
- Keep only `self.m_*.inc()` calls (delegate to collector)
- Keep rolling window appends for percentiles
- Use labeled counters for court_rank and legal_domain

### TR5: Remove Deprecated Endpoint
**Priority**: Medium  
**Rationale**: Cleanup unused code.

**Acceptance Criteria**:
- Delete `mahoun/monitoring/metrics_endpoint.py`
- Verify `/internal/metrics` works
- Update documentation

### TR6: Preserve Advanced Features
**Priority**: Critical  
**Rationale**: Keep all enterprise functionality.

**Acceptance Criteria**:
- UltraPerformanceMonitor integration unchanged
- SLA tracking and alerting unchanged
- Decorator pattern unchanged
- Prometheus export unchanged
- Health checks unchanged
- All 1,287 lines of features preserved (except 9 duplicate variables)

## User Stories

### US1: As a DevOps Engineer
**I want** metrics to come from a single source of truth  
**So that** I can trust the monitoring data

**Acceptance Criteria**:
- All metrics accessible via `/internal/metrics`
- No discrepancies between local state and collector
- Prometheus scraping works correctly

### US2: As a Platform Developer
**I want** type-safe code with no mypy errors  
**So that** I can catch bugs at compile time

**Acceptance Criteria**:
- `mypy --strict mahoun/monitoring/legal_metrics.py` passes
- All deques have explicit type annotations
- No `Any` types in public APIs

### US3: As a QA Engineer
**I want** all existing tests to pass  
**So that** I know the refactoring didn't break anything

**Acceptance Criteria**:
- All unit tests pass
- All integration tests pass
- Property-based tests verify no state drift
- Decorator integration still works

### US4: As a System Architect
**I want** clean architecture with no duplication  
**So that** the codebase is maintainable

**Acceptance Criteria**:
- No duplicate state variables
- Single source of truth for metrics
- Clear separation of concerns

## Non-Functional Requirements

### NFR1: Performance
- Metric tracking overhead < 1ms
- No performance degradation
- Memory footprint reduced

### NFR2: Reliability
- 100% backward compatible
- All tests pass
- Rollback capability

### NFR3: Maintainability
- Type-safe code
- Clear documentation
- No duplicate state

### NFR4: Testability
- Unit tests updated
- Property-based tests added
- Integration tests verified

## Constraints

### C1: No New Dependencies
- This is pure refactoring
- No new packages required

### C2: Backward Compatibility
- All public APIs unchanged
- Same method signatures
- Same return types

### C3: Timeline
- 2 weeks maximum
- Week 1: Refactoring
- Week 2: Testing and cleanup

## Success Criteria

### Functional Success
- ✅ All tests pass
- ✅ Decorator integration verified
- ✅ Prometheus export works
- ✅ No duplicate state

### Non-Functional Success
- ✅ Type checking passes
- ✅ Performance unchanged
- ✅ Memory reduced
- ✅ Documentation updated

## Out of Scope

### NOT Changing
- UltraPerformanceMonitor integration
- SLA tracking logic
- Alert system
- Health checks
- Decorator pattern
- Prometheus export format
- Any other monitoring features

### NOT Adding
- New metrics
- New features
- New dependencies
- New endpoints

---

**Document Version**: 2.0 (Refactoring Approach)  
**Last Updated**: 2025-02-20  
**Status**: Ready for Implementation
