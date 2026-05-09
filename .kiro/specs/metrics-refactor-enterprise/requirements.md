# Metrics Layer Enterprise Refactoring - Requirements

## Executive Summary

Refactor the MAHOUN metrics layer from a monolithic collector into a clean, deterministic, enterprise-grade observability subsystem with strict separation of concerns, zero hidden side effects, and full audit compliance.

**Quality Bar**: This system scored 98/100. We maintain that standard.

---

## Problem Statement

### Current Issues

1. **Hidden State Mutation**: `update_system_metrics()` is called inside read operations (`get_all_metrics()`, `to_prometheus()`), violating read purity
2. **Non-Deterministic Reset**: After `reset()`, system metrics reappear automatically due to implicit injection
3. **Unclear Responsibilities**: `MetricsCollector` mixes state storage, system metric collection, and orchestration
4. **Testing Difficulty**: Cannot test in isolation due to tight coupling
5. **Audit Risk**: Non-deterministic behavior is unacceptable in regulated environments

### Root Cause

The current `MetricsCollector` class has multiple responsibilities:
- State storage (counters, gauges, histograms)
- System metrics collection (CPU, memory, uptime)
- Orchestration (registration, export, reset)
- Implicit behavior (auto-updating system metrics on read)

---

## Strategic Objectives

### Non-Negotiable Constraints

❌ **FORBIDDEN**:
- Breaking changes to public API
- Modifying existing metric names
- Changing Prometheus output format
- Removing backward compatibility
- Silent schema changes
- Behavioral regression in production

✅ **REQUIRED**:
- 100% backward compatibility
- Deterministic state transitions
- Zero hidden side effects
- Thread-safe operations
- Immutable snapshots
- Explicit lifecycle management

---

## Target Architecture

### Three-Layer Separation

```
┌─────────────────────────────────────────────────────┐
│         MetricsCollector (Orchestrator)             │
│  - Public API facade                                │
│  - Coordinates store + system provider              │
│  - Explicit lifecycle management                    │
│  - NO state storage                                 │
│  - NO implicit mutations                            │
└──────────────┬──────────────────────────────────────┘
               │
               ├─────────────────────┬─────────────────┐
               │                     │                 │
    ┌──────────▼──────────┐  ┌──────▼──────────┐  ┌──▼────────────┐
    │   MetricsStore      │  │ SystemMetrics   │  │  Snapshot     │
    │                     │  │ Provider        │  │  Utilities    │
    │ - Pure state        │  │                 │  │               │
    │ - Counters dict     │  │ - Isolated      │  │ - Immutable   │
    │ - Gauges dict       │  │ - No storage    │  │ - Deep copy   │
    │ - Histograms dict   │  │ - Returns dict  │  │ - Timestamped │
    │ - Thread-safe       │  │ - No mutation   │  │ - Versioned   │
    │ - No system logic   │  │ - Optional      │  │ - Hashable    │
    └─────────────────────┘  └─────────────────┘  └───────────────┘
```

---

## User Stories

### US-1: Pure State Container
**As a** developer  
**I want** a pure state container for metrics  
**So that** I can reason about state changes without hidden side effects

**Acceptance Criteria**:
- `MetricsStore` class exists in `mahoun/metrics/store.py`
- Stores counters, gauges, histograms in separate dictionaries
- Thread-safe with `threading.RLock`
- NO system metrics awareness
- NO external I/O
- NO auto-mutation
- Provides `reset()` method that clears all state
- Provides `snapshot()` method that returns deep immutable copy

---

### US-2: Isolated System Metrics Collection
**As a** developer  
**I want** system metrics collection isolated from state storage  
**So that** I can control when and how system metrics are collected

**Acceptance Criteria**:
- `SystemMetricsProvider` class exists in `mahoun/metrics/system_provider.py`
- Collects CPU, memory, uptime metrics
- Returns plain `Dict[str, float]`
- Does NOT store metrics internally
- Does NOT mutate any external state
- Can be disabled/mocked in tests
- Handles `psutil` import errors gracefully

---

### US-3: Explicit Orchestration
**As a** developer  
**I want** explicit control over metric lifecycle  
**So that** I can predict when state changes occur

**Acceptance Criteria**:
- `MetricsCollector` refactored to use `MetricsStore` + `SystemMetricsProvider`
- Constructor: `MetricsCollector(store: MetricsStore, system_provider: Optional[SystemMetricsProvider])`
- `collect_system_metrics()` method is EXPLICIT - must be called manually
- `snapshot()` is PURE - no side effects
- `to_prometheus()` is PURE - no state mutation
- `reset()` clears store only, no auto-repopulation
- All read operations are pure

---

### US-4: Deterministic Reset Behavior
**As a** developer  
**I want** reset to be deterministic  
**So that** tests are predictable and audit trails are clean

**Acceptance Criteria**:
- After `reset()`, all metrics are cleared
- System metrics do NOT reappear unless `collect_system_metrics()` is called
- Reset is atomic (all-or-nothing)
- Reset is thread-safe
- Reset behavior is identical in test and production

---

### US-5: Immutable Snapshots
**As a** compliance officer  
**I want** immutable metric snapshots  
**So that** audit trails cannot be tampered with

**Acceptance Criteria**:
- `MetricsSnapshot` class exists in `mahoun/metrics/snapshot.py`
- Snapshot is immutable (frozen dataclass or MappingProxyType)
- Includes timestamp (ISO8601)
- Includes schema version (e.g., "1.0.0")
- Includes content hash (SHA256)
- Deep copy of all metric data
- No reference to mutable state

---

### US-6: Thread Safety
**As a** developer  
**I want** thread-safe metric operations  
**So that** concurrent requests don't corrupt state

**Acceptance Criteria**:
- All mutation operations protected by `threading.RLock`
- Read operations either lock-protected or operate on immutable snapshot
- No race conditions in concurrent `record_*` calls
- No race conditions in concurrent `reset()` calls
- Stress test with 100+ concurrent threads passes

---

### US-7: Backward Compatibility
**As a** product owner  
**I want** zero breaking changes  
**So that** existing code continues to work

**Acceptance Criteria**:
- All existing public APIs preserved
- Migration layer (`metrics_migration.py`) continues to work
- All 17 existing tests pass without modification
- Prometheus export format unchanged
- Metric names unchanged
- No silent behavioral changes

---

## Success Criteria

✅ **MUST HAVE**:
1. All 17 existing tests pass without modification
2. New architecture implemented with 3 separate components
3. Read operations are pure (no side effects)
4. Reset is deterministic
5. Thread safety validated
6. 95%+ test coverage
7. Zero breaking changes
8. Performance parity or better

---

## References

- Current implementation: `mahoun/metrics/metrics.py`
- Migration layer: `mahoun/infrastructure/observability/metrics_migration.py`
- Existing tests: `tests/test_metrics.py`
- Product requirements: `.kiro/steering/product.md`
- Tech stack: `.kiro/steering/tech.md`
