# Bootstrap Verdict Ingestion - VectorStore & Graph Integration

## Overview

This document describes the **VectorStore** and **Graph (Neo4j)** integration for the Bootstrap Verdict Ingestion pipeline (Scenario B).

After parsing raw Persian legal verdicts into structured JSON format, the system can optionally:
1. **Index into VectorStore** for semantic search and retrieval
2. **Ingest into Graph (Neo4j)** for relationship-based queries

Both integrations are **optional** and **gracefully degrade** if backends are unavailable.

---

## Architecture

```
Raw Verdict (.txt)
       ↓
[minimal_verdict_parser]  ← Rule-based parsing (NO LLM)
       ↓
verdict_struct (dict)
       ↓
       ├─→ JSON Output (.parsed.json)  [ALWAYS]
       ├─→ VectorStore Indexing        [OPTIONAL: --with-vectorstore]
       └─→ Graph Ingestion              [OPTIONAL: --with-graph]
```

---

## TASK 1: VectorStore Integration

### File
`pipelines/vector_store/manager.py`

### Functions

#### `build_verdict_chunks(verdict_struct: Dict, source_id: str) -> List[Dict]`

Converts a parsed verdict into searchable text chunks suitable for vector indexing.

**Chunking Strategy (Rule-based, NO LLM):**

| Chunk # | Section | Content | Purpose |
|---------|---------|---------|---------|
| 0 | `overview` | case_meta + claims + tags | High-level case description |
| 1 | `first_instance_summary` | decision + reasoning keywords | First instance court info |
| 2 | `appeal_court_reasoning` | result + key points | Appeal court analysis |
| 3 | `legal_references` | laws + articles + fiqh principles | Legal basis |
| 4 | `parties` | objectors + attorneys + respondents | Party information |

**Each chunk includes:**
- `text`: The searchable text content (UTF-8 Persian)
- `metadata`: Rich metadata dict with:
  - `source_id`: Unique verdict identifier
  - `section`: Which part of verdict
  - `chunk_index`: 0-based index
  - `case_type`: Type of case (e.g., "اعتراض ثالث")
  - `court_level`: Court level
  - `procedure_stage`: Procedural stage
  - `is_final`: Whether verdict is final
  - `tags_list`: Comma-separated system tags

**Example:**
```python
from pipelines.vector_store.manager import build_verdict_chunks

chunks = build_verdict_chunks(verdict_struct, "verdict_001")
# Returns:
# [
#   {
#     "text": "نوع پرونده: اعتراض ثالث...",
#     "metadata": {
#       "source_id": "verdict_001",
#       "section": "overview",
#       "chunk_index": 0,
#       "case_type": "اعتراض ثالث",
#       ...
#     }
#   },
#   ...
# ]
```

---

#### `index_verdict_struct(verdict_struct: Dict, source_id: str) -> None`

Main entry point for VectorStore indexing. This function:
1. Builds chunks using `build_verdict_chunks()`
2. Generates embeddings for each chunk
3. Inserts chunks + embeddings + metadata into VectorStore
4. Handles idempotency (deletes old chunks before re-indexing)

**Process:**
```
verdict_struct
    ↓
build_verdict_chunks()  → [chunk0, chunk1, chunk2, ...]
    ↓
embed_texts()           → [emb0, emb1, emb2, ...]
    ↓
VectorStore.insert()    → Indexed in ChromaDB/FAISS/etc.
```

**Idempotency:**
- Uses `source_id_chunkN` as unique document ID
- Deletes old chunks with same `source_id` before inserting new ones
- Safe to re-run on same verdict

**Error Handling:**
- If embeddings fail → raises Exception (caught by caller)
- If VectorStore unavailable → raises Exception (caught by caller)
- Caller (bootstrap_verdict_dataloader) catches and logs gracefully

**Example:**
```python
from pipelines.vector_store.manager import index_verdict_struct

index_verdict_struct(verdict_struct, "verdict_001")
# [INFO] [VS] Indexed 5 chunks for verdict verdict_001
```

---

### Metadata Filtering

The rich metadata enables powerful filtering during retrieval:

```python
# Example: Search only in appeal court reasoning
results = vector_store.query(
    query_embedding=query_emb,
    top_k=10,
    filter_metadata={"section": "appeal_court_reasoning"}
)

# Example: Search only final verdicts
results = vector_store.query(
    query_embedding=query_emb,
    top_k=10,
    filter_metadata={"is_final": True}
)

# Example: Search specific case types
results = vector_store.query(
    query_embedding=query_emb,
    top_k=10,
    filter_metadata={"case_type": "اعتراض ثالث"}
)
```

---

## TASK 2: Graph (Neo4j) Integration

### File
`graph/neo4j/operations.py`

### Functions

#### `upsert_verdict_struct(verdict_struct: Dict) -> verdict_id`

Main entry point for Graph ingestion. This function:
1. Generates unique `verdict_id` from filepath or hash
2. Creates/updates `:Verdict` node with case metadata
3. Creates `:LawArticle` nodes and `REFERS_TO` relationships
4. Creates `:Tag` nodes and `HAS_TAG` relationships
5. Creates `:Person` nodes and `HAS_PARTY` relationships

**Graph Schema:**

```cypher
// Nodes
(:Verdict {
  verdict_id: String,
  court_level: String,
  procedure_stage: String,
  case_type: String,
  is_final: Boolean,
  finality_basis: String,
  created_at: DateTime,
  updated_at: DateTime
})

(:LawArticle {
  label: String,          // "ماده 348 آیین دادرسی مدنی"
  code: String,           // "آیین دادرسی مدنی"
  article_no: String,     // "348"
  created_at: DateTime
})

(:Person {
  display_name: String,   // "آقای محمد احمدی"
  father_name: String,    // "علی"
  created_at: DateTime
})

(:Tag {
  name: String,           // "اعتراض ثالث اجرایی"
  created_at: DateTime
})
```

**Relationships:**

```cypher
// Verdict refers to law articles
(v:Verdict)-[:REFERS_TO]->(a:LawArticle)

// Verdict has parties with roles
(v:Verdict)-[:HAS_PARTY {role: "third_party_objector"}]->(p:Person)
(v:Verdict)-[:HAS_PARTY {role: "respondent"}]->(p:Person)
(v:Verdict)-[:HAS_PARTY {role: "third_party_objector_attorney"}]->(p:Person)

// Verdict has tags
(v:Verdict)-[:HAS_TAG]->(t:Tag)
```

**Idempotency:**
- All operations use `MERGE` (not `CREATE`)
- Re-ingesting same verdict **updates** existing nodes
- Relationships are also `MERGE`d (no duplicates)

**Example:**
```python
from graph.neo4j.operations import upsert_verdict_struct

verdict_id = upsert_verdict_struct(verdict_struct)
# [INFO] [GRAPH] ✓ Upserted verdict verdict_001 into graph with all relationships
```

---

### Helper Functions

#### `_parse_law_article(article_str: str) -> Dict`

Parses law article strings into components:

```python
_parse_law_article("ماده 348 آیین دادرسی مدنی")
# Returns:
# {
#   "article_no": "348",
#   "code": "آیین دادرسی مدنی",
#   "label": "ماده 348 آیین دادرسی مدنی"
# }
```

#### `_generate_verdict_id(verdict_struct: Dict) -> str`

Generates unique ID for verdict:
1. Tries to use `verdict_struct["_source"]["filepath"]` filename stem
2. Falls back to MD5 hash of case_meta properties

---

### Example Cypher Queries

After ingestion, you can query the graph:

```cypher
// Find all verdicts that refer to a specific law article
MATCH (v:Verdict)-[:REFERS_TO]->(a:LawArticle {article_no: "348"})
RETURN v.verdict_id, v.case_type, a.label

// Find all verdicts involving a specific person
MATCH (v:Verdict)-[:HAS_PARTY]->(p:Person {display_name: "آقای محمد احمدی"})
RETURN v.verdict_id, v.case_type

// Find verdicts with specific tags
MATCH (v:Verdict)-[:HAS_TAG]->(t:Tag {name: "اعتراض ثالث اجرایی"})
RETURN v.verdict_id, v.court_level

// Find co-cited law articles
MATCH (a1:LawArticle)<-[:REFERS_TO]-(v:Verdict)-[:REFERS_TO]->(a2:LawArticle)
WHERE a1 <> a2
RETURN a1.label, a2.label, COUNT(v) as co_citations
ORDER BY co_citations DESC
```

---

## TASK 3: Orchestrator Integration

### Bootstrap Dataloader Hooks

The `orchestrator/bootstrap_verdict_dataloader.py` provides two hooks:

#### `index_in_vectorstore(verdict_struct, source_id) -> bool`

```python
def index_in_vectorstore(verdict_struct: Dict, source_id: str) -> bool:
    try:
        from pipelines.vector_store import manager as vs_manager
        vs_manager.index_verdict_struct(verdict_struct, source_id)
        return True
    except ImportError:
        print("[WARN] VectorStore manager not available")
        return False
    except Exception as e:
        print(f"[ERROR] VectorStore indexing failed: {e}")
        return False
```

**Graceful Degradation:**
- If `pipelines.vector_store.manager` not available → Warns, returns False
- If `index_verdict_struct` not found → Warns, returns False
- If embedding/indexing fails → Logs error, returns False
- **Application continues** (does not crash)

---

#### `push_to_graph(verdict_struct) -> bool`

```python
def push_to_graph(verdict_struct: Dict) -> bool:
    try:
        from graph.neo4j import operations as neo4j_ops
        neo4j_ops.upsert_verdict_struct(verdict_struct)
        return True
    except ImportError:
        print("[WARN] Graph loader not available")
        return False
    except Exception as e:
        print(f"[ERROR] Graph ingestion failed: {e}")
        return False
```

**Graceful Degradation:**
- If `graph.neo4j.operations` not available → Warns, returns False
- If `upsert_verdict_struct` not found → Warns, returns False
- If Neo4j connection/Cypher fails → Logs error, returns False
- **Application continues** (does not crash)

---

## Usage Examples

### Example 1: Basic Parsing (JSON only)

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts \
  --limit 10
```

**Result:**
- Parses 10 `.txt` files
- Writes 10 `.parsed.json` files
- **No VectorStore or Graph operations**

---

### Example 2: With VectorStore Indexing

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts \
  --with-vectorstore
```

**Result:**
- Parses all `.txt` files
- Writes `.parsed.json` files
- **Indexes each verdict into VectorStore** (if available)
- Gracefully warns if VectorStore unavailable

**Requirements:**
- ChromaDB or FAISS backend configured
- Embedding model available (sentence-transformers)
- numpy installed

---

### Example 3: With Graph Ingestion

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts \
  --with-graph
```

**Result:**
- Parses all `.txt` files
- Writes `.parsed.json` files
- **Ingests each verdict into Neo4j** (if available)
- Gracefully warns if Neo4j unavailable

**Requirements:**
- Neo4j server running (bolt://localhost:7687)
- `neo4j` Python driver installed
- Connection configured in `config/settings.py` or env vars

---

### Example 4: Full Integration

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts \
  --with-vectorstore \
  --with-graph \
  --limit 100
```

**Result:**
- Parses first 100 `.txt` files
- Writes 100 `.parsed.json` files
- **Indexes into VectorStore** (if available)
- **Ingests into Neo4j** (if available)
- Full RAG + Graph capabilities enabled

---

## Error Handling & Logging

### Graceful Degradation Levels

| Level | Behavior | Example |
|-------|----------|---------|
| **INFO** | Normal operation | `[VS] ✓ Indexed 5 chunks for verdict verdict_001` |
| **WARN** | Backend unavailable, continues | `[WARN] VectorStore manager not available` |
| **ERROR** | Operation failed, continues | `[ERROR] VectorStore indexing failed: Embedding count mismatch` |
| **FATAL** | Application cannot continue | (Never happens in current implementation) |

### Success Criteria

A file is marked as **successful** if:
- JSON parsing succeeds
- `.parsed.json` file is written

VectorStore and Graph operations are **optional**:
- Failures in VectorStore/Graph **do not** mark file as failed
- They are logged separately for debugging

---

## Performance Considerations

### VectorStore Indexing

- **Chunking:** ~5 chunks per verdict (fast, rule-based)
- **Embedding:** Depends on model (sentence-transformers: ~50-100ms per chunk)
- **Indexing:** ChromaDB insert: ~10-20ms per chunk
- **Total:** ~300-500ms per verdict (for 5 chunks)

**Bottleneck:** Embedding generation (can be parallelized)

---

### Graph Ingestion

- **Verdict node:** 1 MERGE (~10ms)
- **Law articles:** Up to 50 MERGE + 50 relationships (~500ms)
- **Tags:** Up to 30 MERGE + 30 relationships (~300ms)
- **Parties:** Up to 10 MERGE + 10 relationships (~100ms)
- **Total:** ~900ms per verdict

**Bottleneck:** Network latency to Neo4j (can batch operations)

---

### Recommendations

For **10,000+ verdicts**:
1. Use `--limit` for incremental processing
2. Run overnight for large datasets
3. Consider parallelization (future enhancement)
4. Monitor disk space (VectorStore + Neo4j grow)

---

## Troubleshooting

### Issue: "VectorStore manager not available"

**Cause:** `pipelines.vector_store.manager` not found or import error

**Solution:**
- Check that file exists: `pipelines/vector_store/manager.py`
- Check imports: `python -c "from pipelines.vector_store.manager import index_verdict_struct"`
- Install dependencies: ChromaDB, sentence-transformers

---

### Issue: "Graph loader not available"

**Cause:** `graph.neo4j.operations` not found or neo4j driver missing

**Solution:**
- Install neo4j driver: `pip install neo4j`
- Check Neo4j server: `bolt://localhost:7687`
- Configure connection in `config/settings.py`

---

### Issue: "Embedding count mismatch"

**Cause:** Embedding service returned wrong number of embeddings

**Solution:**
- Check embedding model is loaded
- Install numpy: `pip install numpy`
- Check model compatibility (multilingual Persian support)

---

### Issue: "Neo4j connection failed"

**Cause:** Neo4j server not running or wrong credentials

**Solution:**
- Start Neo4j: `neo4j start` or Docker container
- Check credentials: `NEO4J_USER`, `NEO4J_PASSWORD` env vars
- Test connection: `python -c "from graph.neo4j.connection import get_connection; get_connection().verify()"`

---

## Dependencies

### VectorStore Integration

```
Required:
- pipelines/vector_store/manager.py (VectorStoreManager)
- pipelines/embed_index.py (EmbeddingService)

Optional (for full functionality):
- chromadb (or faiss-cpu)
- sentence-transformers
- numpy
```

### Graph Integration

```
Required:
- graph/neo4j/operations.py (GraphOperations)
- graph/neo4j/connection.py (Neo4jConnection)

Optional (for full functionality):
- neo4j (Python driver)
- Neo4j server (bolt://localhost:7687)
```

---

## Future Enhancements

### Potential Improvements

1. **Batch Processing**
   - Batch multiple verdicts into single VectorStore/Graph transactions
   - Reduce network overhead

2. **Parallel Processing**
   - Use multiprocessing for embedding generation
   - Use async for Neo4j operations

3. **Advanced Chunking**
   - Semantic chunking (split by topic)
   - Overlapping chunks for better context

4. **Graph Enrichment**
   - Link related verdicts (similar cases)
   - Extract implicit relationships (judge citations)

5. **Monitoring**
   - Track indexing/ingestion success rates
   - Dashboard for ingestion pipeline health

---

## Appendix: Code Locations

```
MAHOUN_v2_core_only_baseline/
├── pipelines/
│   ├── ingestion/
│   │   └── minimal_verdict_parser.py (verdict parsing)
│   ├── vector_store/
│   │   └── manager.py (VectorStore integration) ← NEW
│   └── embed_index.py (embedding generation)
├── graph/
│   └── neo4j/
│       ├── operations.py (Graph integration) ← UPDATED
│       ├── connection.py (Neo4j connection) ← UPDATED
│       └── monitoring.py (metrics) ← UPDATED
├── orchestrator/
│   └── bootstrap_verdict_dataloader.py (CLI entrypoint) ← USES NEW FUNCTIONS
└── docs/
    ├── BOOTSTRAP_VERDICTS.md (overall pipeline)
    └── BOOTSTRAP_INTEGRATION.md (this file)
```

---

**Last Updated:** 2025-11-27

