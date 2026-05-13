# Schema & Database Architecture Audit
## بررسی بی‌رحمانه معماری اسکیما و دیتابیس

**تاریخ**: 2026-02-23  
**وضعیت**: 🔍 RUTHLESS AUDIT IN PROGRESS  
**هدف**: بررسی دقیق جریان دیتا از اسکیما تا دیتابیس (Neo4j + ChromaDB)

---

## 📊 EXECUTIVE SUMMARY

سیستم ماحون از یک معماری **3-Layer Schema** استفاده می‌کنه:

1. **L0 (Raw)**: فایل‌های خام (PDF, TXT, DOCX)
2. **L1 (TextDocument)**: متن نرمال‌شده برای RAG/Vector Store
3. **L2 (VerdictStruct)**: ساختار قانونی استخراج‌شده برای Graph

این دیتا توی **دو دیتابیس موازی** ذخیره می‌شه:
- **ChromaDB**: Vector embeddings برای semantic search
- **Neo4j**: Knowledge graph برای reasoning

---

## 🏗️ SCHEMA ARCHITECTURE

### L1 Schema: TextDocument (Vector Store)

```python
class TextDocument(BaseModel):
    document_id: str              # Global UID
    document_type: str            # verdict, law, article
    title: Optional[str]
    full_text: str                # متن کامل
    clean_text: Optional[str]     # متن نرمال‌شده
    date_issued: Optional[str]    # تاریخ صدور
    court: Optional[str]          # دادگاه
    source_file_path: Optional[str]
    ingestion_timestamp: datetime
```

**استفاده**: 
- ذخیره در ChromaDB با embedding 768-dimensional
- برای semantic search و RAG retrieval

**کیفیت**: ⭐⭐⭐⭐⭐ (9/10)
- ساده و کارآمد
- تمام فیلدهای ضروری موجود
- Persian-aware (UTF-8)

---

### L2 Schema: VerdictStruct (Knowledge Graph)

```python
class VerdictStruct(BaseModel):
    case_meta: CaseMeta                    # متادیتای پرونده
    parties: Parties                       # طرفین دعوا
    claims: Claims                         # خواسته‌ها
    first_instance_summary: FirstInstanceSummary
    appeal_court_reasoning: AppealCourtReasoning
    sections: VerdictSections              # بخش‌های معنایی
    legal_references: LegalReferences      # ارجاعات قانونی
    final_decision: FinalDecision
    entities: ExtractedEntities            # NER entities
    system_tags: List[str]
    parsing_quality: ParsingQuality
```

**استفاده**:
- ذخیره در Neo4j به صورت nodes و relationships
- برای graph reasoning و evidence linking

**کیفیت**: ⭐⭐⭐⭐⭐ (9/10)
- ساختار کامل و جامع
- NER entities با 5 نوع (Person, Org, Court, Law, Topic)
- Quality metrics برای confidence tracking

---

### L3 Schema: LegalAwareSchema (Enhanced Metadata)

```python
class LegalMetadata(BaseModel):
    court_rank: Optional[CourtRank]        # 1=Supreme, 2=Appeals, 3=First
    statute_status: StatuteStatus          # active, repealed, amended
    date_jalali: Optional[str]             # تاریخ شمسی
    date_gregorian: Optional[str]
    authority_score: float                 # امتیاز اعتبار
    citation_count: int                    # تعداد استنادات
    cited_by_higher_courts: bool
    legal_domain: Optional[str]            # civil, criminal, etc.
    superseded_by: Optional[str]           # منسوخ‌شده توسط
    supersedes: List[str]                  # منسوخ می‌کند
```

**استفاده**:
- Metadata enrichment برای هر دو vector و graph
- برای legal-aware filtering و ranking

**کیفیت**: ⭐⭐⭐⭐⭐ (10/10) - ENTERPRISE GRADE
- Court hierarchy support
- Temporal validity tracking
- Citation analysis
- Supersession management

---

## 🗄️ DATABASE ARCHITECTURE

### Neo4j Knowledge Graph

**10 Node Types**:
1. **Law** (قانون): قوانین با embedding 1024-dim
2. **Article** (ماده): مواد قانونی با PageRank
3. **Note** (تبصره): تبصره‌های مواد
4. **Clause** (بند): بندهای مواد
5. **Court** (دادگاه): دادگاه‌ها با سلسله‌مراتب
6. **Branch** (شعبه): شعب دادگاه
7. **Verdict** (رأی): آرای قضایی با embedding
8. **Case** (پرونده): پرونده‌های قضایی
9. **Person** (شخص): اشخاص (hashed for privacy)
10. **Party** (طرف): طرفین دعوا

**Relationship Types**:
- `CITES`: (Verdict)-[:CITES]->(Article)
- `SUPERSEDED_BY`: (Article)-[:SUPERSEDED_BY]->(Article)
- `AFFIRMS`: (Verdict)-[:AFFIRMS]->(Verdict)
- `REVERSES`: (Verdict)-[:REVERSES]->(Verdict)
- `PART_OF`: (Article)-[:PART_OF]->(Law)
- `DECIDED_BY`: (Case)-[:DECIDED_BY]->(Court)

**Indexes**:
- ✅ Unique constraints on all node IDs
- ✅ BTree indexes on frequently searched fields
- ✅ Fulltext indexes on Law, Article, Verdict content
- ✅ Vector indexes on embeddings (768-dim for GGUF)

**Schema Quality**: ⭐⭐⭐⭐⭐ (9/10)
- Comprehensive node types
- Proper constraints and indexes
- Vector index support for hybrid retrieval
- Privacy-aware (hashed names)

---

### ChromaDB Vector Store

**Collection Structure**:
```python
{
    "ids": ["doc1_chunk0", "doc1_chunk1", ...],
    "embeddings": [[0.1, 0.2, ...], ...],  # 768-dim
    "documents": ["text content", ...],
    "metadatas": [
        {
            "source_id": "verdict_001",
            "section": "overview",
            "case_type": "اعتراض ثالث",
            "court_level": "تجدیدنظر",
            "is_final": true,
            "branch": "10",
            "city": "تهران",
            "decision_date": "1403-08-15",
            "person_count": 3,
            "law_count": 5,
            ...
        },
        ...
    ]
}
```

**Chunking Strategy** (Rule-based, NO LLM):
1. **Chunk 1**: Overview (case meta + claims + tags)
2. **Chunk 1.5**: Detailed claims list (if > 5 claims)
3. **Chunk 2**: First instance summary
4. **Chunk 3**: Appeal court reasoning
5. **Chunk 4**: Semantic sections (summary, verdict text)
6. **Chunk 5**: Legal references
7. **Chunk 6**: Parties summary

**Metadata Richness**:
- ✅ Case metadata (type, court, stage, finality)
- ✅ Geographic info (branch, city, province)
- ✅ Temporal info (decision_date)
- ✅ Entity counts (person_count, org_count, law_count)
- ✅ Entity names (first 5 persons, orgs, 10 laws)
- ✅ System tags (up to 20)

**Vector Store Quality**: ⭐⭐⭐⭐⭐ (9/10)
- Rich metadata for filtering
- Smart chunking strategy
- Entity-aware metadata
- Persian-optimized

---

## 🔄 DATA FLOW ANALYSIS

### Ingestion Pipeline

```
Raw File (L0)
    ↓
[minimal_verdict_parser]
    ↓
Parsed Dict
    ↓
[schema_builder]
    ↓
├─→ TextDocument (L1) ──→ [VectorStoreManager] ──→ ChromaDB
│                              ↓
│                         [embed_texts]
│                              ↓
│                         768-dim embeddings
│
└─→ VerdictStruct (L2) ──→ [UltraGraphBuilder] ──→ Neo4j
                               ↓
                          [create_nodes]
                               ↓
                          10 node types + relationships
```

**Pipeline Quality**: ⭐⭐⭐⭐ (8/10)
- Clear separation of concerns
- Parallel storage (vector + graph)
- No data loss between layers

**⚠️ CRITICAL ISSUE**: 
- **Global UID synchronization** بین ChromaDB و Neo4j ضعیف است
- `document_id` در TextDocument ≠ `id` در Neo4j nodes
- این می‌تونه باعث data silos بشه

---

## 🔍 RETRIEVAL ARCHITECTURE

### Hybrid Retrieval Strategy

```python
# 1. Vector Search (ChromaDB)
vector_results = await vector_store.query(
    query_embedding=embedding,
    top_k=20,
    filter_metadata={
        "court_level": "تجدیدنظر",
        "is_final": True
    }
)

# 2. Graph Search (Neo4j)
graph_results = neo4j.run("""
    MATCH (v:Verdict)-[:CITES]->(a:Article)
    WHERE a.number = 10
    RETURN v
""")

# 3. Hybrid Fusion
final_results = reciprocal_rank_fusion(
    vector_results,
    graph_results
)
```

**Retrieval Quality**: ⭐⭐⭐⭐ (8/10)
- Hybrid approach (vector + graph)
- Rich metadata filtering
- Reciprocal rank fusion

**⚠️ MISSING**:
- **Reranking** با court hierarchy
- **Authority scoring** در final ranking
- **Temporal filtering** (date ranges)

---

## 🚨 CRITICAL FINDINGS

### 🔴 HIGH SEVERITY

1. **Global UID Mismatch**
   - ChromaDB `document_id` ≠ Neo4j `id`
   - باعث می‌شه نتونیم cross-reference کنیم
   - **Fix**: Implement `GlobalIdentifier` schema

2. **No Semantic Search Integration**
   - `PersianSemanticSearch` ساخته شده ولی integrate نشده
   - `knowledge_graph.py` هنوز keyword matching استفاده می‌کنه
   - **Fix**: Replace keyword matching with semantic search

3. **No Concurrent Graph Usage**
   - `ConcurrentGraphBuilder` ساخته شده ولی استفاده نمی‌شه
   - `evidence_linked_verdict.py` هنوز `UltraGraphBuilder` استفاده می‌کنه
   - **Fix**: Migrate to concurrent builder

### 🟡 MEDIUM SEVERITY

4. **Embedding Dimension Mismatch**
   - Neo4j models: 1024-dim
   - ChromaDB actual: 768-dim (sentence-transformers)
   - **Fix**: Update Neo4j models to 768-dim

5. **No Async Ledger Usage**
   - `AsyncLedgerWriter` ساخته شده ولی استفاده نمی‌شه
   - Ledger writes هنوز synchronous هستن
   - **Fix**: Migrate to async writer

6. **Limited Legal Metadata**
   - `LegalMetadata` schema موجوده ولی populate نمی‌شه
   - Court hierarchy, authority scores missing
   - **Fix**: Implement metadata enrichment pipeline

### 🟢 LOW SEVERITY

7. **Test Coverage**
   - 1 failing test در semantic search (timeout issue)
   - **Fix**: Add model warmup fixture

8. **Documentation**
   - Schema relationships خوب document نشده
   - **Fix**: Add architecture diagrams

---

## 📈 QUALITY SCORES

| Component | Score | Grade |
|-----------|-------|-------|
| **L1 Schema (TextDocument)** | 9/10 | A |
| **L2 Schema (VerdictStruct)** | 9/10 | A |
| **L3 Schema (LegalMetadata)** | 10/10 | A+ |
| **Neo4j Schema** | 9/10 | A |
| **ChromaDB Integration** | 9/10 | A |
| **Data Flow** | 8/10 | B+ |
| **Retrieval Architecture** | 8/10 | B+ |
| **Global UID Sync** | 4/10 | D |
| **Integration** | 5/10 | D |
| **Overall** | 7.5/10 | B |

---

## 🎯 RECOMMENDATIONS

### Phase 1: Critical Fixes (این هفته)

1. **Fix Global UID Synchronization**
   ```python
   # Implement GlobalIdentifier
   uid = generate_global_uid(document_type, source_id)
   
   # Use in both stores
   text_doc = TextDocument(document_id=uid, ...)
   verdict_node = VerdictNode(id=uid, ...)
   ```

2. **Integrate Semantic Search**
   ```python
   # Replace in knowledge_graph.py
   def find_applicable_rules(self, query: str):
       # OLD: keyword matching
       # NEW: semantic search
       results = self.semantic_search.semantic_similarity(
           query=query,
           candidates=self.rules,
           top_k=10
       )
   ```

3. **Migrate to Concurrent Graph**
   ```python
   # Replace in evidence_linked_verdict.py
   from mahoun.graph.concurrent_graph_builder import ConcurrentGraphBuilder
   
   self.graph = ConcurrentGraphBuilder()
   ```

### Phase 2: Enhancements (هفته بعد)

4. **Fix Embedding Dimensions**
   - Update Neo4j models: 1024 → 768
   - Update vector indexes
   - Regenerate embeddings if needed

5. **Implement Async Ledger**
   ```python
   from mahoun.ledger.async_writer import AsyncLedgerWriter
   
   self.ledger = AsyncLedgerWriter(batch_size=100)
   await self.ledger.write_batch(entries)
   ```

6. **Enrich Legal Metadata**
   - Calculate court_rank from case_meta
   - Compute authority_score from citations
   - Add temporal validity checks

### Phase 3: Advanced Features (ماه بعد)

7. **Implement Reranking**
   - Court hierarchy reranking
   - Authority score boosting
   - Temporal relevance decay

8. **Add Monitoring**
   - UID sync validation
   - Embedding quality metrics
   - Retrieval performance tracking

---

## 🏆 STRENGTHS

1. ✅ **Clean Schema Separation**: L1/L2/L3 واضح و منطقی
2. ✅ **Rich Metadata**: Entity counts, geographic info, temporal data
3. ✅ **Enterprise NER**: 5 entity types, 25 topic categories
4. ✅ **Privacy-Aware**: Hashed names در Neo4j
5. ✅ **Vector + Graph**: Hybrid architecture برای zero-hallucination
6. ✅ **Persian-Optimized**: UTF-8, Jalali dates, Persian field labels
7. ✅ **Quality Tracking**: Parsing confidence, validation status

---

## ⚠️ WEAKNESSES

1. ❌ **UID Mismatch**: ChromaDB ↔ Neo4j synchronization ضعیف
2. ❌ **No Integration**: ماژول‌های جدید (semantic search, concurrent graph) integrate نشدن
3. ❌ **Dimension Mismatch**: 1024 vs 768 در models
4. ❌ **No Reranking**: Court hierarchy در retrieval استفاده نمی‌شه
5. ❌ **Limited Metadata**: Legal metadata populate نمی‌شه
6. ❌ **Sync Ledger**: Async writer استفاده نمی‌شه

---

## 📊 FINAL VERDICT

**Overall Grade**: 7.5/10 (B)

**Summary**:
- Schema architecture عالیه (9/10)
- Database design قوی است (9/10)
- ولی **integration ضعیف** است (5/10)
- ماژول‌های جدید ساخته شدن ولی به سیستم اصلی وصل نشدن

**Next Steps**:
1. Fix UID synchronization (CRITICAL)
2. Integrate semantic search (CRITICAL)
3. Migrate to concurrent graph (CRITICAL)
4. Fix embedding dimensions (HIGH)
5. Implement async ledger (MEDIUM)

---

**تاریخ گزارش**: 2026-02-23  
**نویسنده**: Kiro AI Assistant  
**وضعیت**: ✅ AUDIT COMPLETE - READY FOR PHASE 1 FIXES
