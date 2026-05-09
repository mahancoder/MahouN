# Core Archive

This directory contains archived modules that were moved out of core/ during cleanup.

## Why Archive Instead of Delete?

1. **Auditability**: Full history preserved for compliance
2. **Safety**: Can restore if needed
3. **Reference**: Code may contain useful patterns
4. **Zero Risk**: No data loss

## Archived Modules

### graph/ (Archived: 2026-02-20)
- **Reason**: Empty module, only __init__.py
- **Replacement**: mahoun/graph/ (production version)
- **Usage**: None found
- **Files**:
  - `__init__.py` (empty stub)

### ingest/ (Archived: 2026-02-20)
- **Reason**: Orphaned prototype
- **Replacement**: mahoun/pipelines/ingestion/
- **Usage**: None found
- **Files**:
  - `__init__.py` (empty stub)

### rag/ (Archived: 2026-02-20)
- **Reason**: Orphaned prototype with vector_store.py
- **Replacement**: mahoun/rag/ (production version)
- **Usage**: None found
- **Files**:
  - `__init__.py` (empty stub)
  - `vector_store.py` (prototype implementation)

## Restoration Process

If you need to restore a module:

```bash
# Example: restore graph module
cp -r mahoun/core/archive/graph/ mahoun/core/graph/
```

**Note**: Restoration should only be done if absolutely necessary. Use production modules instead.

## Cleanup Schedule

- **Week 1-4**: Archive period (modules in archive/)
- **Week 5-8**: Verification period (confirm no issues)
- **Week 9+**: Can be deleted if confirmed unused

## Verification

Before archiving, we verified zero usage:

```bash
# Verified no imports of archived modules
grep -r "from mahoun.core.graph" mahoun/ tests/ api/
grep -r "from mahoun.core.ingest" mahoun/ tests/ api/
grep -r "from mahoun.core.rag" mahoun/ tests/ api/
```

All searches returned no results, confirming these modules are orphaned.

## Production Replacements

| Archived Module | Production Replacement | Status |
|----------------|----------------------|--------|
| core/graph/ | mahoun/graph/ | ✅ Active (10x larger) |
| core/ingest/ | mahoun/pipelines/ingestion/ | ✅ Active |
| core/rag/ | mahoun/rag/ | ✅ Active |

## Contact

If you have questions about archived modules, see:
- `CORE_FINAL_CLEANUP_TASKS.md` for cleanup rationale
- `CORE_FINAL_CLEANUP_DESIGN.md` for architectural decisions
