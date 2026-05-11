# Issue 1: Dual-Mode Semantic Divergence - Forensic Analysis

**Date**: 2026-05-06  
**Status**: IN PROGRESS  
**Severity**: CRITICAL ⚠️  
**Impact**: ZERO-HALLUCINATION GUARANTEE AT RISK

---

## 🔍 FORENSIC FINDINGS

### Current Protection Status

**✅ PROTECTION EXISTS** in 2 locations:
1. **Verdict Engine** (`mahoun/reasoning/evidence_linked_verdict.py`, lines 240-254)
2. **API Router** (`api/routers/reasoning.py`, lines 181-192)

### Entry Point Analysis

| Entry Point | Mode Check | Status | Risk Level |
|-------------|------------|--------|------------|
| **API `/generate-verdict`** | ✅ YES | Protected | LOW |
| **Direct Python API** | ✅ YES | Protected | LOW |
| **MCP Server** | ❌ NO | Not applicable | N/A |
| **Background Jobs** | ❓ UNKNOWN | Not verified | MEDIUM |
| **Test Suite** | ❌ NO | Bypasses check | LOW (test only) |

### Code Evidence

#### 1. Verdict Engine Protection (PRIMARY)

**File**: `mahoun/reasoning/evidence_linked_verdict.py` (lines 240-254)

```python
async def generate_verdict(self, question: str, facts: List[Any]) -> EvidenceLinkedVerdict:
    # ============================================================================
    # DUAL-MODE RESOURCE CHECK - CRITICAL
    # ============================================================================
    from mahoun.core.runtime_config import is_desktop_minimal, should_skip_graph
    
    if is_desktop_minimal() and should_skip_graph():
        raise RuntimeError(
            "Evidence-linked verdict generation requires full graph reasoning and "
            "ledger guarantees. This operation is not supported in DESKTOP_MINIMAL "
            "mode with graph disabled. Please run in ENTERPRISE_FULL mode or enable "
            "graph operations (MAHOUN_ENABLE_GRAPH=true)."
        )
```

**Analysis**:
- ✅ Fail-fast mechanism
- ✅ Clear error message
- ✅ Suggests remediation
- ⚠️ Can be bypassed if called directly from test code
- ⚠️ No logging of blocked attempts

---

#### 2. API Router Protection (SECONDARY)

**File**: `api/routers/reasoning.py` (lines 181-192)

```python
def get_verdict_engine() -> EvidenceLinkedVerdictEngine:
    """Get or create verdict engine instance"""
    global _verdict_engine

    if _verdict_engine is None:
        # Check if we're in DESKTOP_MINIMAL mode with graph disabled
        if is_desktop_minimal() and should_skip_graph():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "service_unavailable",
                    "message": "Reasoning API requires full graph operations. "
                    "Current mode: DESKTOP_MINIMAL with graph disabled. "
                    "Please run in ENTERPRISE_FULL mode or enable graph "
                    "(MAHOUN_ENABLE_GRAPH=true).",
                },
            )
```

**Analysis**:
- ✅ Returns HTTP 503 (Service Unavailable)
- ✅ Clear error message
- ✅ Prevents engine initialization
- ✅ Logged via FastAPI
- ⚠️ Only checked once (singleton pattern)

---

#### 3. MCP Server

**File**: `mahoun/mcp/server.py`

**Finding**: ❌ **NO VERDICT GENERATION TOOL**

MCP server currently does NOT expose verdict generation functionality.

**Tools Available**:
- `mahoun/mcp/tools/graph.py` - Graph operations
- `mahoun/mcp/tools/ingest.py` - Data ingestion
- `mahoun/mcp/tools/maintenance.py` - Maintenance
- `mahoun/mcp/tools/rag.py` - RAG operations
- `mahoun/mcp/tools/system.py` - System operations

**Risk**: LOW (no exposure)

---

### Configuration Analysis

**File**: `mahoun/core/runtime_config.py`

```python
def is_desktop_minimal() -> bool:
    """Quick check if running in desktop_minimal mode."""
    return get_runtime_settings().mode == "desktop_minimal"

def should_skip_graph() -> bool:
    """Quick check if graph operations should be skipped."""
    settings = get_runtime_settings()
    return not settings.graph_enabled or settings.graph_backend == "disabled_fallback"
```

**Environment Variables**:
- `MAHOUN_MODE`: "desktop_minimal" | "server_full" (default: server_full)
- `MAHOUN_GRAPH_ENABLED`: Enable/disable graph (bool, default: False in desktop_minimal)
- `MAHOUN_GRAPH_BACKEND`: "disabled_fallback" | "local_small" | "local_full" | "remote"

**Configuration Validation**: ❌ **MISSING**
- No startup validation
- No prevention of invalid combinations
- No fail-fast on misconfiguration

---

## 🚨 IDENTIFIED GAPS

### Gap 1: No Startup Validation

**Problem**: System can start with invalid configuration

**Scenario**:
```bash
# Invalid combination - should fail at startup
export MAHOUN_MODE=desktop_minimal
export MAHOUN_GRAPH_ENABLED=true  # ← Contradictory!
python -m mahoun.api.main
```

**Current Behavior**: Starts successfully, fails at runtime  
**Expected Behavior**: Fail-fast at startup with clear error

---

### Gap 2: No Monitoring/Alerting

**Problem**: No visibility into mode enforcement

**Missing**:
- No metrics for blocked requests
- No alerts when mode check triggers
- No dashboard for mode distribution

**Impact**: Cannot detect:
- Misconfiguration in production
- Attempts to bypass mode checks
- Mode-related performance issues

---

### Gap 3: Test Suite Bypasses Check

**Problem**: Tests directly instantiate engine without mode check

**Example** (`tests/test_evidence_linked_verdict.py`):
```python
engine = EvidenceLinkedVerdictEngine(builder, kg, ledger_writer)
verdict = await engine.generate_verdict(question, facts)  # ← Bypasses mode check!
```

**Risk**: LOW (test environment only)  
**Concern**: Tests don't validate mode enforcement

---

### Gap 4: No Configuration File Validation

**Problem**: YAML config files not validated

**Files**:
- `configs/runtime_profile.yaml`
- `configs/runtime_profile_desktop.yaml`

**Missing Validation**:
- Schema validation
- Constraint validation (e.g., desktop_minimal + graph_enabled)
- Required field validation

---

### Gap 5: Singleton Pattern Weakness

**Problem**: API router checks mode only once (singleton)

**Scenario**:
```python
# 1. Start in ENTERPRISE_FULL mode
engine = get_verdict_engine()  # ← Check passes, engine created

# 2. Change environment variable (hot reload)
os.environ["MAHOUN_MODE"] = "desktop_minimal"
os.environ["MAHOUN_GRAPH_ENABLED"] = "false"

# 3. Call again
engine = get_verdict_engine()  # ← Returns cached engine, no check!
```

**Risk**: MEDIUM (requires hot reload, rare in production)

---

## ✅ STRENGTHS

1. **Defense in Depth**: Two layers of protection (engine + API)
2. **Clear Error Messages**: Users know exactly what's wrong
3. **Fail-Fast**: Errors raised immediately, not silently ignored
4. **Documented**: Mode constraints documented in code comments

---

## 🎯 REQUIRED FIXES

### Fix 1: Startup Configuration Validation ⭐ **CRITICAL**

**Priority**: P0  
**Effort**: 2-3 hours

**Implementation**:
```python
# mahoun/core/config_validator.py

def validate_runtime_config() -> None:
    """Validate runtime configuration at startup."""
    settings = get_runtime_settings()
    
    # Rule 1: desktop_minimal + graph_enabled = INVALID
    if settings.mode == "desktop_minimal" and settings.graph_enabled:
        if settings.graph_backend not in ["disabled_fallback", "remote"]:
            raise ConfigurationError(
                "Invalid configuration: desktop_minimal mode cannot use "
                f"graph_backend='{settings.graph_backend}'. "
                "Use 'disabled_fallback' or 'remote' instead."
            )
    
    # Rule 2: Verdict generation requires graph
    if not settings.graph_enabled:
        logger.warning(
            "Graph operations disabled - verdict generation will be unavailable"
        )
    
    # Rule 3: Validate Neo4j credentials if graph enabled
    if settings.graph_enabled and settings.graph_backend == "local_full":
        if not settings.graph_neo4j_password:
            raise ConfigurationError(
                "Neo4j password required for local_full graph backend"
            )
```

**Integration**:
```python
# api/main.py

@app.on_event("startup")
async def startup_validation():
    """Validate configuration on startup."""
    from mahoun.core.config_validator import validate_runtime_config
    validate_runtime_config()
```

---

### Fix 2: Monitoring & Metrics ⭐ **HIGH**

**Priority**: P1  
**Effort**: 2-3 hours

**Implementation**:
```python
# mahoun/reasoning/evidence_linked_verdict.py

from mahoun.metrics import verdict_generation_blocked

async def generate_verdict(self, question: str, facts: List[Any]) -> EvidenceLinkedVerdict:
    if is_desktop_minimal() and should_skip_graph():
        # Log blocked attempt
        log.warning(
            "Verdict generation blocked due to mode constraint",
            extra={
                "mode": "desktop_minimal",
                "graph_enabled": False,
                "question_preview": question[:50],
            }
        )
        
        # Increment metric
        verdict_generation_blocked.labels(
            mode="desktop_minimal",
            reason="graph_disabled"
        ).inc()
        
        raise RuntimeError(...)
```

**Metrics**:
- `verdict_generation_blocked_total{mode, reason}` - Counter
- `verdict_generation_mode{mode}` - Gauge
- `verdict_generation_duration_seconds{mode}` - Histogram

---

### Fix 3: Configuration File Schema Validation ⭐ **MEDIUM**

**Priority**: P2  
**Effort**: 2-3 hours

**Implementation**:
```python
# mahoun/core/config_schema.py

from pydantic import BaseModel, field_validator

class RuntimeConfigSchema(BaseModel):
    """Schema for runtime_profile.yaml"""
    mode: Literal["desktop_minimal", "server_full"]
    graph: GraphConfigSchema
    retrieval: RetrievalConfigSchema
    
    @field_validator('graph')
    @classmethod
    def validate_graph_config(cls, v, info):
        mode = info.data.get('mode')
        if mode == 'desktop_minimal':
            if v.enabled and v.backend not in ['disabled_fallback', 'remote']:
                raise ValueError(
                    f"desktop_minimal mode cannot use graph_backend='{v.backend}'"
                )
        return v
```

---

### Fix 4: Test Suite Mode Enforcement ⭐ **LOW**

**Priority**: P3  
**Effort**: 1-2 hours

**Implementation**:
```python
# tests/conftest.py

@pytest.fixture(autouse=True)
def enforce_test_mode():
    """Ensure tests run in appropriate mode."""
    import os
    
    # Force ENTERPRISE_FULL for integration tests
    if "integration" in os.environ.get("PYTEST_CURRENT_TEST", ""):
        os.environ["MAHOUN_MODE"] = "server_full"
        os.environ["MAHOUN_GRAPH_ENABLED"] = "true"
    
    yield
    
    # Cleanup
    os.environ.pop("MAHOUN_MODE", None)
    os.environ.pop("MAHOUN_GRAPH_ENABLED", None)
```

---

### Fix 5: Singleton Cache Invalidation ⭐ **LOW**

**Priority**: P3  
**Effort**: 1 hour

**Implementation**:
```python
# api/routers/reasoning.py

def get_verdict_engine() -> EvidenceLinkedVerdictEngine:
    """Get or create verdict engine instance"""
    global _verdict_engine
    
    # Check mode EVERY time (not just on first call)
    if is_desktop_minimal() and should_skip_graph():
        # Clear cached engine if mode changed
        _verdict_engine = None
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={...}
        )
    
    if _verdict_engine is None:
        # Initialize engine
        ...
    
    return _verdict_engine
```

---

## 📊 RISK ASSESSMENT

### Current Risk Level: **MEDIUM** ⚠️

**Justification**:
- ✅ Primary protection exists (engine-level check)
- ✅ Secondary protection exists (API-level check)
- ❌ No startup validation (can start with invalid config)
- ❌ No monitoring (blind to mode issues)
- ⚠️ Singleton pattern weakness (rare edge case)

### After Fixes: **LOW** ✅

**With all fixes**:
- ✅ Startup validation (fail-fast on invalid config)
- ✅ Monitoring & metrics (full visibility)
- ✅ Configuration schema validation
- ✅ Test suite enforcement
- ✅ Singleton cache invalidation

---

## 🎯 IMPLEMENTATION PLAN

### Phase 1: Critical Fixes (4-5 hours)

1. **Startup Configuration Validation** (2-3h)
   - Create `config_validator.py`
   - Add validation rules
   - Integrate with FastAPI startup
   - Add tests

2. **Monitoring & Metrics** (2-3h)
   - Add Prometheus metrics
   - Add structured logging
   - Add alerting rules
   - Add dashboard

### Phase 2: Medium Priority (2-3 hours)

3. **Configuration Schema Validation** (2-3h)
   - Create Pydantic schemas
   - Add YAML validation
   - Add error messages
   - Add tests

### Phase 3: Low Priority (2-3 hours)

4. **Test Suite Enforcement** (1-2h)
   - Add pytest fixtures
   - Update test configuration
   - Add mode markers

5. **Singleton Cache Invalidation** (1h)
   - Update `get_verdict_engine()`
   - Add cache invalidation logic
   - Add tests

**Total Effort**: 8-11 hours (estimated 8-10h)

---

## 🧪 VALIDATION STRATEGY

### Test Cases

1. **Startup Validation**
   - ✅ Valid config → starts successfully
   - ✅ Invalid config → fails with clear error
   - ✅ Missing config → uses defaults

2. **Runtime Enforcement**
   - ✅ ENTERPRISE_FULL + graph enabled → verdict generated
   - ✅ DESKTOP_MINIMAL + graph disabled → 503 error
   - ✅ DESKTOP_MINIMAL + graph enabled (remote) → verdict generated

3. **Monitoring**
   - ✅ Blocked attempts logged
   - ✅ Metrics incremented
   - ✅ Alerts triggered

4. **Configuration Validation**
   - ✅ Valid YAML → parsed successfully
   - ✅ Invalid YAML → validation error
   - ✅ Invalid combination → validation error

---

## 📝 NEXT STEPS

1. ✅ Complete forensic analysis (DONE)
2. ⏳ Implement Fix 1: Startup validation
3. ⏳ Implement Fix 2: Monitoring & metrics
4. ⏳ Implement Fix 3: Configuration schema
5. ⏳ Implement Fix 4: Test suite enforcement
6. ⏳ Implement Fix 5: Singleton cache invalidation
7. ⏳ Run full test suite
8. ⏳ Update documentation

---

**END OF ANALYSIS**
