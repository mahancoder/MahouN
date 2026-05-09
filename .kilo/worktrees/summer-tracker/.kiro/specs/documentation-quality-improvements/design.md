# Documentation & Quality - Design

**Version**: 1.0  
**Updated**: 2026-02-10

---

## Goal

Score 8.0 → 9.0+ via **tests + docs only**. Zero logic changes.

---

## Phase B: Tests (Priority 1)

### B.1: Coverage 90%+

**Current**: ~80%  
**Target**: 90%+

```bash
pytest --cov=mahoun --cov-report=html
```

**Add**:
- Unit tests (error paths, edge cases)
- Integration tests (end-to-end)
- Property tests (invariants)

### B.2: Schema Strictness

Change `extra='allow'` → `extra='forbid'` for:
- VerdictStruct
- ReasoningResult
- LedgerEntry
- GraphNode/Edge

**Process**: One at a time, test, commit. Rollback if fails.

### B.3: Property Tests

```bash
pip install hypothesis
```

**Test**:
- EL-I1 to EL-I7 invariants
- Hash chain integrity
- Schema validation
- Graph traversal

---

## Phase A: Docs (Priority 2)

### A.1: API Reference

```
docs/api/
├── reasoning.md
├── graph.md
├── ledger.md
└── invariants.md
```

**Content**: Signatures, params, examples only.

### A.2: Getting Started

15-min quickstart:
1. Install
2. First verdict
3. With graph
4. Ledger write

### A.3: Architecture

- High-level diagram
- Core principles
- Design decisions
- Extension points

### A.4: Tutorials

1. Basic (30min)
2. Graph (45min)
3. Custom engines (60min)
4. MCP (30min)

### A.5: Docstrings

Add to all public APIs:
- Docstrings
- Type hints
- Examples

---

## Timeline

**Week 1**: Tests  
**Week 2**: Docs

---

## Success

- ✅ Coverage 90%+
- ✅ Schemas strict
- ✅ 20+ property tests
- ✅ Docs complete
- ✅ Score 9.0+
