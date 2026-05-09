# Issue 2: Race Condition in Contradiction Resolution - Forensic Analysis

**Date**: 2026-05-06  
**Status**: IN PROGRESS  
**Severity**: CRITICAL ⚠️  
**Impact**: NON-DETERMINISTIC CONTRADICTION HANDLING

---

## 🔍 FORENSIC FINDINGS

### Current Protection Status

**✅ LOCK EXISTS** but with critical limitations:

**File**: `mahoun/reasoning/evidence_linked_verdict.py` (lines 180-182)

```python
# CRITICAL: Asyncio lock for atomic contradiction resolution
self._resolution_lock = asyncio.Lock()
```

### The Problem: Instance-Level Lock

**Lock Scope**: `self._resolution_lock` = **INSTANCE-LEVEL**

**Implication**: Each `EvidenceLinkedVerdictEngine` instance has its own lock!

---

## 🚨 RACE CONDITION SCENARIOS

### Scenario 1: Multiple Engine Instances (CURRENT RISK)

```python
# Thread/Process 1
engine1 = EvidenceLinkedVerdictEngine(builder, kg, ledger)
verdict1 = await engine1.generate_verdict(question, facts)  # Lock 1

# Thread/Process 2 (concurrent)
engine2 = EvidenceLinkedVerdictEngine(builder, kg, ledger)
verdict2 = await engine2.generate_verdict(question, facts)  # Lock 2 (DIFFERENT!)

# PROBLEM: Lock 1 and Lock 2 are DIFFERENT locks!
# Both can resolve contradictions simultaneously → NON-DETERMINISTIC
```

**Risk Level**: **HIGH** in multi-instance deployments

---

### Scenario 2: API Router Singleton (CURRENT PROTECTION)

**File**: `api/routers/reasoning.py` (lines 175-210)

```python
_verdict_engine: Optional[EvidenceLinkedVerdictEngine] = None

def get_verdict_engine() -> EvidenceLinkedVerdictEngine:
    """Get or create verdict engine instance"""
    global _verdict_engine
    
    if _verdict_engine is None:
        # Initialize components
        _verdict_engine = EvidenceLinkedVerdictEngine(...)
    
    return _verdict_engine
```

**Analysis**:
- ✅ Singleton pattern ensures ONE engine instance per process
- ✅ All API requests use same engine → same lock
- ⚠️ Only protects within single process
- ❌ Does NOT protect across multiple processes/workers

---

### Scenario 3: Distributed Deployment (NO PROTECTION)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Worker 1      │     │   Worker 2      │     │   Worker 3      │
│                 │     │                 │     │                 │
│  Engine + Lock1 │     │  Engine + Lock2 │     │  Engine + Lock3 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        └───────────────────────┴───────────────────────┘
                                │
                        ┌───────▼────────┐
                        │  Load Balancer │
                        └────────────────┘
```

**Problem**: Each worker has its own engine instance with its own lock!

**Risk**: Multiple workers can resolve same contradiction simultaneously → **NON-DETERMINISTIC**

---

## 🔬 DETERMINISM ANALYSIS

### What Makes Contradiction Resolution Non-Deterministic?

**Resolution Strategies** (in order):

1. **Higher Confidence** - Deterministic if confidence values differ
2. **Higher Credibility** - Deterministic if credibility values differ
3. **Newer Date** - Deterministic if dates differ
4. **Graph Analytics Score** - **POTENTIALLY NON-DETERMINISTIC**

**Code** (`mahoun/reasoning/evidence_linked_verdict.py`, lines 1050-1070):

```python
def _calculate_node_score(self, node: GraphNode) -> float:
    """Calculate composite score for a node"""
    confidence = node.confidence
    match_score = node.properties.get("match_score", 0.0)
    similarity = node.properties.get("similarity", 0.0)
    relevance = node.properties.get("relevance_score", 0.0)
    
    # Weighted combination
    score = (
        confidence * 0.4
        + (match_score or similarity or relevance) * 0.3
        + (node.properties.get("usage_count", 0) / 100.0) * 0.3
    )
    
    return score
```

**Non-Determinism Sources**:
1. **`usage_count`** - Can change between calls if node is used elsewhere
2. **Floating-point arithmetic** - Rounding errors in concurrent calculations
3. **Property access order** - `match_score or similarity or relevance` depends on which is set

---

### Tie-Breaking Problem

**What if all strategies return `None`?**

```python
if resolution is not None:
    resolved_nodes[resolution.id] = resolution
    excluded_id = node2_id if resolution.id == node1_id else node1_id
    excluded_nodes.add(excluded_id)
else:
    # Cannot resolve - add to unresolved
    unresolved_conflicts.append(...)
    # Keep BOTH nodes
    resolved_nodes[node1_id] = node1
    resolved_nodes[node2_id] = node2
```

**Problem**: If two engines process same contradiction:
- Engine 1 might resolve it (one node excluded)
- Engine 2 might not resolve it (both nodes kept)
- **Result**: Different verdicts for same input!

---

## 🎯 ROOT CAUSES

### Root Cause 1: Instance-Level Lock

**Problem**: Lock is tied to engine instance, not shared across instances

**Impact**: Multiple engine instances = multiple locks = no protection

**Severity**: CRITICAL in multi-instance deployments

---

### Root Cause 2: Stateful Resolution

**Problem**: Resolution depends on mutable state (`usage_count`, `_edge_counter`)

**Impact**: Same input can produce different output depending on timing

**Severity**: HIGH - violates determinism requirement

---

### Root Cause 3: No Tie-Breaking Strategy

**Problem**: When all strategies fail, both nodes kept (non-deterministic)

**Impact**: Unresolved contradictions vary between runs

**Severity**: MEDIUM - affects verdict consistency

---

### Root Cause 4: Floating-Point Arithmetic

**Problem**: Floating-point calculations can have rounding errors

**Impact**: Scores might differ slightly between runs

**Severity**: LOW - rare but possible

---

## ✅ SOLUTION STRATEGIES

### Strategy A: Distributed Lock (Multi-Instance Protection)

**Approach**: Use distributed lock (Redis, database advisory lock)

**Pros**:
- ✅ Protects across multiple processes/workers
- ✅ Works in distributed deployments
- ✅ Minimal code changes

**Cons**:
- ❌ Requires external dependency (Redis/database)
- ❌ Performance overhead (network latency)
- ❌ Single point of failure (lock service)

**Implementation**:
```python
import redis
from redis.lock import Lock as RedisLock

class EvidenceLinkedVerdictEngine:
    def __init__(self, ...):
        self.redis_client = redis.Redis(...)
        self._resolution_lock_key = "mahoun:contradiction_resolution"
    
    async def _resolve_contradictions_async(self, ...):
        # Acquire distributed lock
        lock = self.redis_client.lock(
            self._resolution_lock_key,
            timeout=30,
            blocking_timeout=10
        )
        
        with lock:
            # Resolve contradictions
            ...
```

---

### Strategy B: Deterministic Resolution (RECOMMENDED) ⭐

**Approach**: Make resolution purely functional (no shared state, no locks needed)

**Pros**:
- ✅ No external dependencies
- ✅ No performance overhead
- ✅ Guaranteed determinism
- ✅ Simpler architecture

**Cons**:
- ❌ Requires refactoring resolution logic
- ❌ Need to remove stateful dependencies

**Implementation**:
```python
def _resolve_contradictions_deterministic(
    self,
    contradictions: List[Dict[str, Any]],
    rule_nodes: Dict[str, GraphNode],
    precedent_nodes: Dict[str, GraphNode],
) -> Tuple[Dict[str, GraphNode], List[str]]:
    """
    Resolve contradictions deterministically (NO LOCKS NEEDED)
    
    Determinism guarantees:
    1. Sort contradictions by node IDs (lexicographic order)
    2. Use only immutable node properties
    3. Deterministic tie-breaking (node ID comparison)
    4. No floating-point arithmetic
    """
    resolved_nodes: Dict[str, GraphNode] = {}
    unresolved_conflicts: List[str] = []
    all_nodes = {**rule_nodes, **precedent_nodes}
    
    # Group and SORT contradictions for determinism
    contradiction_groups = defaultdict(list)
    for contr in contradictions:
        key = tuple(sorted([contr["node1_id"], contr["node2_id"]]))
        contradiction_groups[key].append(contr)
    
    # Process in sorted order (deterministic)
    for (node1_id, node2_id) in sorted(contradiction_groups.keys()):
        node1 = all_nodes[node1_id]
        node2 = all_nodes[node2_id]
        
        # Strategy 1: Higher confidence (deterministic)
        if node1.confidence > node2.confidence:
            resolution = node1
        elif node2.confidence > node1.confidence:
            resolution = node2
        # Strategy 2: Deterministic tie-breaking (node ID)
        elif node1_id < node2_id:  # Lexicographic comparison
            resolution = node1
        else:
            resolution = node2
        
        resolved_nodes[resolution.id] = resolution
    
    # Add non-contradictory nodes
    for node_id, node in all_nodes.items():
        if node_id not in resolved_nodes:
            resolved_nodes[node_id] = node
    
    return resolved_nodes, unresolved_conflicts
```

**Key Changes**:
1. ✅ Sort contradictions by node IDs (deterministic order)
2. ✅ Use only immutable properties (confidence)
3. ✅ Deterministic tie-breaking (lexicographic node ID comparison)
4. ✅ No locks needed (pure function)

---

### Strategy C: Hybrid Approach

**Approach**: Deterministic resolution + distributed lock (defense in depth)

**Pros**:
- ✅ Deterministic even without lock
- ✅ Lock provides additional safety
- ✅ Best of both worlds

**Cons**:
- ❌ More complex
- ❌ Still requires external dependency

---

## 📊 COMPARISON

| Strategy | Determinism | Performance | Complexity | Dependencies |
|----------|-------------|-------------|------------|--------------|
| **A: Distributed Lock** | ⚠️ Partial | ❌ Slow | ⚠️ Medium | ❌ Redis |
| **B: Deterministic** ⭐ | ✅ Full | ✅ Fast | ✅ Low | ✅ None |
| **C: Hybrid** | ✅ Full | ⚠️ Medium | ❌ High | ❌ Redis |

**RECOMMENDATION**: **Strategy B (Deterministic Resolution)** ⭐

**Justification**:
1. Solves root cause (non-determinism)
2. No external dependencies
3. Better performance
4. Simpler architecture
5. Easier to test

---

## 🎯 IMPLEMENTATION PLAN

### Phase 1: Make Resolution Deterministic (4-5 hours)

1. **Refactor `_resolve_contradictions_async`** (2-3h)
   - Remove stateful dependencies
   - Add deterministic sorting
   - Add deterministic tie-breaking
   - Remove lock (no longer needed)

2. **Update Resolution Strategies** (1-2h)
   - Remove `usage_count` dependency
   - Use only immutable properties
   - Add deterministic tie-breaking to each strategy

3. **Add Tests** (1h)
   - Test determinism (same input → same output)
   - Test concurrent calls (no race conditions)
   - Test tie-breaking

### Phase 2: Remove Sync Wrapper (1 hour)

4. **Deprecate `generate_verdict_sync`** (1h)
   - Add deprecation warning
   - Update documentation
   - Migrate tests to async

### Phase 3: Validation (1 hour)

5. **Run Full Test Suite** (1h)
   - Verify all tests pass
   - Verify determinism
   - Verify performance

**Total Effort**: 6-7 hours (estimated 6-8h)

---

## 🧪 VALIDATION STRATEGY

### Test Cases

1. **Determinism Test**
   ```python
   # Same input should produce same output
   verdict1 = await engine.generate_verdict(question, facts)
   verdict2 = await engine.generate_verdict(question, facts)
   assert verdict1 == verdict2
   ```

2. **Concurrency Test**
   ```python
   # Concurrent calls should produce same output
   tasks = [
       engine.generate_verdict(question, facts)
       for _ in range(10)
   ]
   verdicts = await asyncio.gather(*tasks)
   assert all(v == verdicts[0] for v in verdicts)
   ```

3. **Tie-Breaking Test**
   ```python
   # Nodes with equal confidence should be resolved deterministically
   node1 = GraphNode(id="rule_a", confidence=0.9, ...)
   node2 = GraphNode(id="rule_b", confidence=0.9, ...)
   # Should always choose "rule_a" (lexicographic order)
   ```

---

## 📝 NEXT STEPS

1. ✅ Complete forensic analysis (DONE)
2. ⏳ Implement deterministic resolution
3. ⏳ Remove stateful dependencies
4. ⏳ Add deterministic tie-breaking
5. ⏳ Remove lock (no longer needed)
6. ⏳ Add tests
7. ⏳ Run full test suite
8. ⏳ Update documentation

---

**END OF ANALYSIS**
