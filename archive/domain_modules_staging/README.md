# Domain Modules Staging Archive

**Archive Date**: May 6, 2026  
**Archived By**: Kiro AI  
**Reason**: Deferred integration - Core system stable, modules lack tests

---

## What Was This?

`domain_modules/` was a **staging area** for advanced features and enhancements to the Mahoun platform. It contained **307 Python files** with **99,537 lines of code** covering:

- **Core Infrastructure**: Adversarial detection, anomaly detection, alerting, RBAC, PII scrubbing
- **Graph Systems**: Neo4j integration, GAT reranking, entity extraction, relationship building
- **Pipelines**: Guardrails, caching, training, ingestion, query enhancement
- **Monitoring**: Metrics tracking, model reliability, shadow deployment
- **Advanced Features**: Uncertainty quantification, chain-of-thought explanations

---

## Why Was It Archived?

### Decision Rationale:

1. **Core System is Stable** ✅
   - Mahoun core has 101/101 tests passing
   - Production-ready functionality
   - No critical gaps

2. **High Integration Risk** ⚠️
   - 307 files without tests (0 test coverage)
   - All import paths broken (relative imports)
   - Heavy dependencies (torch, transformers, pytorch-geometric)
   - Unknown integration issues

3. **Time vs. Value** ⏰
   - Estimated 2-3 weeks for full integration
   - Uncertain ROI without tests
   - Better to integrate selectively when needed

4. **Better Strategy** 🎯
   - Keep modules available for future use
   - Integrate S-Tier modules individually when needed
   - Write tests before integration
   - Fix import paths incrementally

---

## Quality Assessment

### Overall Scores:
- **Category 1 (Core Infrastructure)**: 8.7/10 (Excellent)
- **Category 2 (Graph Systems)**: 8.9/10 (Excellent)
- **Category 3 (Pipelines)**: 9.0/10 (Excellent - Partial)

### Tier Distribution:
- **S-Tier (9.5-10)**: 7 modules - Production-ready, flagship quality
- **A-Tier (8.5-9.4)**: 8 modules - Excellent, minor fixes needed
- **B-Tier (8.0-8.4)**: 2 modules - Good, some gaps
- **C-Tier (7.0-7.9)**: 1 module - Functional but incomplete

### Top S-Tier Modules (Ready for Integration):
1. ✅ `adversarial_detector.py` (9.5/10) - Multi-method OOD detection
2. ✅ `alerting.py` (9.5/10) - PagerDuty/Slack/Email integration
3. ✅ `graph/neo4j/connection.py` (9.5/10) - Production-grade pooling
4. ✅ `graph/services/rag_integration.py` (9.5/10) - Multi-hop graph RAG
5. ✅ `graph/retrieval/gat_reranker.py` (9.5/10) - GAT with uncertainty
6. ✅ `flows/enhanced_rag.py` (9.5/10) - Complete RAG pipeline
7. ✅ `pipelines/guardrails/nli_verifier.py` (9.5/10) - NLI verification

---

## Critical Issues Found

### Blockers:
1. ❌ **Zero test coverage** - Not a single test file
2. ❌ **Broken imports** - All relative imports need fixing
3. ❌ **Missing dependencies** - `ultra_systems` module not found
4. ❌ **No integration tests** - Unknown compatibility with mahoun core

### Warnings:
1. ⚠️ **Heavy dependencies** - PyTorch, Transformers (optional but needed for many features)
2. ⚠️ **No persistence** - Most systems in-memory only
3. ⚠️ **No async support** - Many modules synchronous only
4. ⚠️ **Import conflicts** - Some modules duplicate mahoun core (e.g., `alerting.py`)

---

## How to Use This Archive

### If You Need a Module:

1. **Check the audit report**: `.kiro/DOMAIN_MODULES_AUDIT.md`
2. **Pick an S-Tier or A-Tier module**
3. **Fix import paths**:
   ```python
   # Change from:
   from ..core.models import Entity
   
   # To:
   from mahoun.core.models import Entity
   ```
4. **Write tests** before integration
5. **Verify dependencies** are available
6. **Test integration** with mahoun core
7. **Merge incrementally**

### Recommended Integration Order:

**Phase 1 (Low Risk)**:
- `pii_scrubber.py` - No dependencies, standalone
- `anomaly_detector.py` - Numpy only, standalone
- `alerting.py` - Already exists in mahoun, merge improvements

**Phase 2 (Medium Risk)**:
- `graph/neo4j/connection.py` - Replace mahoun Neo4j connection
- `graph/builders/embedding_generator.py` - Replace mahoun embedding
- `adversarial_detector.py` - Add as new feature

**Phase 3 (High Risk)**:
- `graph/services/rag_integration.py` - Major RAG enhancement
- `graph/retrieval/gat_reranker.py` - Requires PyTorch Geometric
- `flows/enhanced_rag.py` - Complete RAG redesign

---

## Archive Contents

```
domain_modules/
├── __init__.py
├── adversarial_detector.py (1,004 lines)
├── alerting.py (612 lines)
├── anomaly_detector.py (389 lines)
├── diagnostic_reports.py
├── metrics_endpoint.py
├── metrics_tracker.py (118 lines)
├── model_fallback.py (289 lines)
├── model_manager.py
├── model_reliability.py (156 lines)
├── pii_scrubber.py (156 lines)
├── rbac.py (329 lines)
├── retention.py
├── rolling_stats.py
├── shadow_deployment.py (1,038 lines)
├── wandb_logger.py
├── flows/ (15+ files)
├── graph/ (60+ files)
│   ├── builders/
│   ├── neo4j/
│   ├── retrieval/
│   └── services/
├── monitoring/ (10+ files)
├── orchestrator/ (20+ files)
├── pipelines/ (80+ files)
├── schemas/ (15+ files)
├── sdk/ (10+ files)
└── ultra_systems/ (40+ files)
```

**Total**: 307 files, 99,537 lines of code

---

## References

- **Full Audit Report**: `.kiro/DOMAIN_MODULES_AUDIT.md` (1,305 lines)
- **Implementation Status**: `.kiro/IMPLEMENTATION_STATUS_SCAN.md`
- **Original Location**: `domain_modules/` (now archived)
- **Archive Date**: May 6, 2026

---

## Decision Log

**Date**: May 6, 2026  
**Decision**: Archive domain_modules staging area  
**Rationale**: Core system stable (101/101 tests pass), modules lack tests (0 coverage), high integration risk (307 files), better to integrate selectively when needed  
**Approved By**: Project maintainer  
**Status**: ✅ Archived

---

## Future Actions

### When to Revisit:

1. **When a specific feature is needed** - Extract and integrate that module only
2. **When tests are written** - Add test coverage before integration
3. **When imports are fixed** - Fix relative imports to absolute
4. **When dependencies are verified** - Ensure all deps available

### Not Recommended:

- ❌ Bulk merge all 307 files
- ❌ Integration without tests
- ❌ Integration without fixing imports
- ❌ Integration without dependency verification

---

## Contact

For questions about this archive or specific modules:
- Check audit report: `.kiro/DOMAIN_MODULES_AUDIT.md`
- Review this README
- Test individual modules before integration

**Remember**: Quality over quantity. Integrate selectively, test thoroughly.
