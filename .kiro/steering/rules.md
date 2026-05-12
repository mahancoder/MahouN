# MAHOUN PLATFORM - AGENT DIRECTIVE (STRICT)

You are operating on **KingMahouN**, an Enterprise-Grade, Domain-Driven Legal Knowledge Graph and Neuro-Symbolic AI Platform. This is NOT a basic script or a simple wrapper. It is a mission-critical system.

Before writing or modifying ANY code, you MUST adhere to the following architectural and behavioral rules:

## 1. Architectural Integrity (Domain-Driven Design)
* **Separation of Concerns:** The project is strictly divided into `builders`, `importers`, `services`, and `neo4j` infrastructure. NEVER mix ingestion logic with query logic.
* **Thread Safety:** Neo4j connections rely on `ThreadSafeSingleton` and native driver pooling. NEVER create standalone connections inside loops or generic functions. Always pass the connection or use `get_connection()`.
* **Idempotency is Mandatory:** When interacting with the Graph, ALWAYS use `MERGE` instead of `CREATE` for nodes and relationships to prevent duplication. Graph operations must be safely repeatable.

## 2. Reliability & Resilience Guardrails
* **Fail Gracefully:** External calls and database transactions MUST use the `@retry_on_failure` decorator with exponential backoff.
* **Transaction Bounds:** Use `execute_read`, `execute_write`, and `execute_batch` context managers. NEVER leave database sessions hanging.
* **Memory Constraints (O(1) mindset):** For bulk operations, use `BatchImporter` and Cypher `UNWIND`. Never load massive datasets into Python memory (lists). Use generators or batch chunks.

## 3. Data Integrity & Caching
* **Strict Ontology:** Entity labels (e.g., `ARTICLE`, `VERDICT`, `LAW_NAME`) and Relationship types (e.g., `CITES`, `OVERTURNS`, `CONFIRMS`) are rigidly defined. Do NOT invent new labels without explicit authorization.
* **Cache First:** Embeddings and heavy queries MUST utilize `EmbeddingCache` and `QueryCache` (with TTL/LRU). Always check the cache before triggering expensive LLM/Embedding inferences.

## 4. Testing & Validation Standard
* **Zero-Regression Rule:** The platform has a forensic-grade test suite (e.g., 53+ integration tests, strict memory leak checks). Any code you write MUST be accompanied by comprehensive tests covering:
  - Edge cases (Nulls, empty strings, Persian Unicode anomalies).
  - Accuracy thresholds (e.g., Entity extraction must maintain >90% accuracy).
  - Deduplication and Hash stability (`__hash__` and `__eq__` must align).

## 5. Coding Style
* Use Python 3.10+ type hinting (`typing` module) strictly for all function arguments and return types.
* Prefer Dataclasses (`@dataclass(frozen=True)` where possible) for immutable state transfer.
* Always include structured logging (`logger.info`, `logger.warning`) with contextual metadata instead of raw `print()` statements.

**PRIME DIRECTIVE:** Stabilize first, then optimize. Preserve existing architecture unless explicitly authorized to perform a structural overhaul. Think in systems, analyze failure modes, and guarantee mathematical/logical certainty in your code.