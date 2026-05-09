# Domain Modules - Archived

**Date**: May 6, 2026  
**Status**: ✅ Archived  
**Location**: `archive/domain_modules_staging/`

---

## Quick Summary

The `domain_modules/` staging area (307 files, 99K lines) has been **archived** instead of merged into the main codebase.

### Why?

✅ **Mahoun core is stable** - 101/101 tests passing  
❌ **Modules lack tests** - 0 test coverage  
❌ **Import paths broken** - All need fixing  
⚠️ **High integration risk** - 307 files without validation  

### Decision

**Archive now, integrate selectively later** when specific features are needed.

---

## What's Archived?

- **Core Infrastructure**: Adversarial detection, alerting, RBAC, PII scrubbing
- **Graph Systems**: Neo4j, GAT reranking, entity extraction
- **Pipelines**: Guardrails, caching, training
- **Monitoring**: Metrics, reliability, shadow deployment

**Quality**: 8.7-9.0/10 (Excellent code, but untested)

---

## How to Use

1. **Check archive**: `archive/domain_modules_staging/README.md`
2. **Review audit**: `archive/domain_modules_staging/DOMAIN_MODULES_AUDIT.md`
3. **Pick a module** (prefer S-Tier: 9.5-10/10)
4. **Fix imports** (relative → absolute)
5. **Write tests** before integration
6. **Merge incrementally**

### Top Modules to Consider:

- `adversarial_detector.py` (9.5/10) - OOD detection
- `alerting.py` (9.5/10) - PagerDuty/Slack
- `graph/neo4j/connection.py` (9.5/10) - Connection pooling
- `graph/services/rag_integration.py` (9.5/10) - Graph RAG
- `graph/retrieval/gat_reranker.py` (9.5/10) - GAT reranking

---

## Current Status

✅ **Mahoun Core**: Production-ready, 101/101 tests pass  
📦 **Domain Modules**: Archived for selective integration  
🎯 **Strategy**: Integrate when needed, test first  

---

For full details, see: `archive/domain_modules_staging/README.md`
