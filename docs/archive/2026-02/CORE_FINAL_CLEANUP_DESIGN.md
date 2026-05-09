# Core Final Cleanup - Design

## Architecture Overview

```
Current State:
mahoun/core/
├── metrics/          ❌ Duplicate (mahoun/metrics exists)
├── monitoring/       ❌ Orphaned (unused)
├── graph/           ❌ Empty (only __init__.py)
├── ingest/          ❌ Orphaned (mahoun/pipelines/ingestion exists)
├── rag/             ❌ Orphaned (mahoun/rag exists)
├── llm/             ⚠️  Decision needed
└── [essential]      ✅ Keep (config, settings, models, etc.)

Target State:
mahoun/core/
├── config.py        ✅ Essential
├── settings.py      ✅ Essential
├── models.py        ✅ Essential
├── protocols.py     ✅ Essential
├── validation.py    ✅ Essential
├── logging.py       ✅ Essential
├── exceptions.py    ✅ Essential
└── ...              ✅ Core utilities only
```

## Component Design

### 1. Metrics Consolidation

**Problem**: Two MetricsCollector implementations
```python
# Current (BAD):
mahoun.core.metrics.MetricsCollector  # 398 lines, basic
mahoun.metrics.MetricsCollector       # 613 lines, Prometheus

# Target (GOOD):
mahoun.metrics.MetricsCollector       # Single source of truth
```

**Solution**:
1. Add deprecation warning to core/metrics
2. Update 3 import locations:
   - `api/routers/metrics.py`
   - `tests/test_metrics.py`
   - `mahoun/agents/archive/base_agent_simple.py`
3. Remove core/metrics after 2 weeks

**Migration Path**:
```python
# Step 1: Add to mahoun/core/metrics/__init__.py
import warnings
warnings.warn(
    "mahoun.core.metrics is deprecated. Use mahoun.metrics instead.",
    DeprecationWarning,
    stacklevel=2
)
from mahoun.metrics import *  # Re-export

# Step 2: Update imports
# OLD: from mahoun.core.metrics import MetricsCollector
# NEW: from mahoun.metrics import MetricsCollector

# Step 3: Remove mahoun/core/metrics/
```

### 2. Monitoring Activation

**Problem**: Enterprise monitoring system (1,287 lines) unused

**Solution**: Integrate with API
```python
# api/main.py
from mahoun.monitoring.legal_metrics import legal_monitoring

@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=legal_monitoring.export_prometheus_metrics(),
        media_type="text/plain"
    )

@app.get("/metrics/legal")
async def legal_metrics():
    """Legal-specific metrics"""
    return legal_monitoring.get_comprehensive_stats()
```

**Features to Activate**:
- Prometheus export
- Legal query tracking
- SLA compliance monitoring
- Anomaly detection
- Performance profiling

### 3. Orphaned Module Removal

**Verification Process**:
```bash
# 1. Check usage
grep -r "from mahoun.core.graph" mahoun/ tests/ api/
grep -r "from mahoun.core.ingest" mahoun/ tests/ api/
grep -r "from mahoun.core.rag" mahoun/ tests/ api/
grep -r "from mahoun.core.monitoring" mahoun/ tests/ api/

# 2. If no results → safe to remove
rm -rf mahoun/core/graph/
rm -rf mahoun/core/ingest/
rm -rf mahoun/core/rag/
rm -rf mahoun/core/monitoring/
```

**Modules to Remove**:
- `core/graph/` → mahoun/graph/ exists (10x larger)
- `core/ingest/` → mahoun/pipelines/ingestion/ exists
- `core/rag/` → mahoun/rag/ exists
- `core/monitoring/` → mahoun/monitoring/ exists (unused but keep)

### 4. LLM Module Decision

**Analysis**:
```
mahoun/core/llm/
├── Used by: agents, reasoning, rag (3 modules)
├── Tests: 5 test files
├── Size: 9 files, ~2000 lines
└── Role: Infrastructure (routing, orchestration)
```

**Decision**: **Keep in core/** (for now)

**Rationale**:
1. Actively used by multiple modules
2. Infrastructure role (not domain-specific)
3. Moving would require updating many imports
4. Can be moved later in separate phase

**Alternative**: Move to `mahoun/llm/` in future phase

### 5. Core Independence Score

**Calculation**:
```python
# Before cleanup:
infrastructure_in_core = 8  # metrics, monitoring, graph, ingest, rag, llm, health_*
domain_in_core = 13
score = 13 / 21 = 62%

# After cleanup (remove orphaned):
infrastructure_in_core = 2  # llm, health_* (keep for now)
domain_in_core = 13
score = 13 / 15 = 87%

# After metrics consolidation:
infrastructure_in_core = 1  # llm only
domain_in_core = 13
score = 13 / 14 = 93%

# After LLM move (future):
infrastructure_in_core = 0
domain_in_core = 13
score = 13 / 13 = 100%
```

## Data Flow

### Metrics Flow
```
Application Code
    ↓
mahoun.metrics.MetricsCollector
    ↓
MetricsStore (thread-safe)
    ↓
Prometheus Export
    ↓
/metrics/prometheus endpoint
```

### Monitoring Flow
```
Legal Query
    ↓
legal_monitoring.track_legal_query()
    ↓
MetricsCollector + UltraPerformanceMonitor
    ↓
SLA Compliance Check
    ↓
Prometheus + Grafana
```

## API Design

### New Endpoints

```python
# Prometheus metrics
GET /metrics/prometheus
Response: text/plain (Prometheus format)

# Legal metrics
GET /metrics/legal
Response: {
  "total_queries": int,
  "avg_duration": float,
  "error_rate": float,
  "sla_compliance_rate": float,
  "queries_by_court": dict,
  "queries_by_domain": dict
}

# Health check
GET /health/detailed
Response: {
  "status": "healthy",
  "uptime": float,
  "metrics": {...}
}
```

## Testing Strategy

### Unit Tests
- Test metrics import from new location
- Test monitoring integration
- Test orphaned module removal (no imports)

### Integration Tests
- Test Prometheus endpoint
- Test legal metrics tracking
- Test SLA compliance

### Regression Tests
- All existing tests must pass
- No performance degradation
- No breaking changes

## Rollback Plan

### If metrics migration fails:
```bash
# Restore core/metrics
git checkout HEAD -- mahoun/core/metrics/

# Revert import changes
git checkout HEAD -- api/routers/metrics.py tests/test_metrics.py
```

### If monitoring integration fails:
```bash
# Remove endpoints
git checkout HEAD -- api/main.py

# Disable monitoring
# No code changes needed (just don't use it)
```

## Performance Considerations

- Metrics collection: < 1ms overhead
- Monitoring tracking: < 2ms overhead
- Prometheus export: < 10ms (cached)
- No impact on critical path

## Security Considerations

- Metrics endpoint: public (standard practice)
- Legal metrics: may need authentication
- No sensitive data in metrics
- Rate limiting on endpoints

## Documentation Updates

### Files to Update:
1. `README.md` - Update imports
2. `docs/API.md` - Add new endpoints
3. `ARCHITECTURE.md` - Update core structure
4. `MONITORING.md` - Add monitoring guide

### Migration Guide:
```markdown
# Metrics Migration Guide

## Old Import (Deprecated)
```python
from mahoun.core.metrics import MetricsCollector
```

## New Import
```python
from mahoun.metrics import MetricsCollector
```

## Timeline
- Week 1-2: Deprecation warnings
- Week 3: Remove old imports
- Week 4: Remove core/metrics
```

## Success Criteria

### Phase 1: Metrics Consolidation
- ✅ All imports updated
- ✅ Tests pass
- ✅ Deprecation warnings added

### Phase 2: Monitoring Activation
- ✅ Prometheus endpoint works
- ✅ Legal metrics tracked
- ✅ Documentation complete

### Phase 3: Orphaned Removal
- ✅ No usage found
- ✅ Directories removed
- ✅ Tests pass

### Phase 4: Validation
- ✅ Core independence: 93%+
- ✅ All tests pass
- ✅ CI/CD green
- ✅ No regressions
