# گزارش ممیزی عمیق تست‌های Verification
## تاریخ: 2026-05-09
## وضعیت: 🔴 **مشکلات جدی شناسایی شد**

---

## ❌ مشکل اصلی: ماک‌سازی کامل سیستم

### 1. MockGraphBuilder - ماک کامل گراف‌بیلدر

**کد واقعی:**
```python
# mahoun/graph/ultra_graph_builder.py
class UltraGraphBuilder:
    def build_graph(self, entities: List[Dict], relationships: List[Dict], ...):
        # 500+ خط کد پیچیده
        # - Quality assessment
        # - Graph analytics
        # - Index building
        # - Metrics calculation
        # - Neo4j export
```

**کد تست (ماک):**
```python
# tests/verification/*.py
class MockGraphBuilder:
    def build_from_text(self, text, node_ids, edges):
        return {"id": f"fact_{hash(text) % 10000}", "type": "Fact", ...}, []
```

**❌ مشکل:**
- متد `build_from_text` در کد واقعی وجود ندارد!
- تست یک متد فیک رو ماک کرده
- کل لاجیک گراف‌بیلدر (500+ خط) bypass شده
- Quality assessment, analytics, indexing همه skip شدن

---

### 2. MockKnowledgeGraph - ماک کامل دانش‌گراف

**کد واقعی:**
```python
# mahoun/reasoning/knowledge_graph.py
class LegalKnowledgeGraph:
    def find_applicable_rules(self, facts):
        # Semantic matching
        # Rule retrieval from Neo4j/ChromaDB
        # Confidence scoring
        # Complex filtering
```

**کد تست (ماک):**
```python
class MockKnowledgeGraph:
    def find_applicable_rules(self, facts):
        return [{"id": "rule_1", "text": "Rule", "confidence": 0.9}]
```

**❌ مشکل:**
- همیشه یک rule ثابت برمی‌گردونه
- هیچ semantic matching واقعی نداره
- Neo4j/ChromaDB query نمی‌زنه
- Confidence scoring فیک هست

---

### 3. تست Category 1 (Easy) - ساده‌سازی شده

#### Test 1.1: Deterministic Reasoning Flow

**ادعا:** "Identical inputs produce identical graph IDs, verdict IDs, ledger hashes"

**واقعیت:**
```python
# Mock datetime برای determinism
with patch('mahoun.graph.ultra_graph_builder.datetime') as mock_graph_dt, \
     patch('mahoun.ledger.blockchain.datetime') as mock_ledger_dt, \
     patch('mahoun.reasoning.evidence_linked_verdict.datetime') as mock_engine_dt:
    
    mock_graph_dt.now.return_value = fixed_now
    mock_ledger_dt.now.return_value = fixed_now
    mock_engine_dt.now.return_value = fixed_now
```

**❌ مشکل:**
- تست determinism رو با ماک کردن datetime ثابت می‌کنه!
- این فریب هست - سیستم واقعی datetime واقعی استفاده می‌کنه
- اگر سیستم واقعی non-deterministic باشه، تست نمی‌فهمه

#### Test 1.2: Empty Evidence Rejection

**ادعا:** "Verdicts without evidence are rejected via EL-I3/G1"

**واقعیت:**
```python
with pytest.raises(Exception) as excinfo:
    await engine.generate_verdict("Question without facts?", [])
```

**❌ مشکل:**
- `Exception` خیلی کلی هست - هر exception رو قبول می‌کنه
- باید `InvariantViolation` یا `RuntimeError` مشخص باشه
- ممکنه به دلیل دیگه‌ای fail بشه و تست pass بشه

---

### 4. تست Category 2 (Medium) - ساده‌سازی شده

#### Test 2.1: Concurrent State Isolation

**ادعا:** "50 concurrent tasks don't leak state"

**واقعیت:**
```python
async def worker(i: int):
    facts = [f"Fact {i}.A", f"Fact {i}.B"]
    v = await engine.generate_verdict(f"Question {i}", facts)
    reg = get_registry()
    assert len(reg) < 50, f"State bleed detected! Registry has {len(reg)} nodes"
```

**❌ مشکل:**
- threshold `< 50` خیلی شل هست
- با MockGraphBuilder که فقط 2 node می‌سازه، باید `< 10` باشه
- تست واقعاً state bleed رو detect نمی‌کنه

#### Test 2.2: Ledger Commit Failure Rollback

**ادعا:** "State machine transitions to ERROR on ledger failure"

**واقعیت:**
```python
sm.transition(LegalTrigger.ERROR_OCCURRED)
assert sm.state == LegalState.ERROR
```

**❌ مشکل:**
- فقط state machine رو تست می‌کنه، نه ledger واقعی
- هیچ ledger failure واقعی simulate نشده
- هیچ rollback واقعی تست نشده

---

### 5. تست Category 3 (Extreme) - بهترین تست‌ها اما هنوز مشکل دارن

#### Test 3.A.1: Adversarial Evidence Injection

**✅ خوب:** از subclass استفاده می‌کنه تا hallucinated evidence inject کنه

**❌ مشکل:**
```python
class MaliciousEngine(EvidenceLinkedVerdictEngine):
    def _build_verdict_steps(self, *args, **kwargs):
        steps = super()._build_verdict_steps(*args, **kwargs)
        fake_evidence = EvidenceReference(node_id="fake_hallucinated_node", ...)
        steps.append(VerdictStep(statement="Defendant confessed.", evidence=[fake_evidence]))
        return steps
```

- هنوز MockGraphBuilder و MockKnowledgeGraph استفاده می‌کنه
- فقط یک بخش کوچیک از سیستم رو تست می‌کنه

#### Test 3.B.1: Cyclic Contradiction Deadlock

**✅ خوب:** MockKnowledgeGraph با cyclic=True سه rule متناقض برمی‌گردونه

**❌ مشکل:**
```python
class MockKnowledgeGraph:
    def __init__(self, cyclic=False, ambiguous=False):
        self.cyclic = cyclic
        
    def find_applicable_rules(self, facts):
        if self.cyclic:
            return [rule_A, rule_B, rule_C]  # 3 contradictory rules
```

- contradiction detection واقعی تست نمی‌شه
- semantic matching واقعی تست نمی‌شه
- فقط resolution logic تست می‌شه

#### Test 3.C.1: Hidden Mutable State Injection

**✅ عالی:** این تست واقعاً خوبه - canonical_serialize رو تست می‌کنه

**✅ بدون ماک:** از LedgerEntry واقعی استفاده می‌کنه

#### Test 3.D.1: Force Transition Critical Bypass

**✅ عالی:** State machine واقعی رو تست می‌کنه

**✅ بدون ماک:** از LegalReasoningStateMachine واقعی استفاده می‌کنه

#### Test 3.E.1: Ambiguous Contradiction Surfacing

**✅ خوب:** دو rule با confidence یکسان تست می‌کنه

**❌ مشکل:** هنوز MockKnowledgeGraph استفاده می‌کنه

---

## 📊 خلاصه مشکلات

### مشکلات اصلی:

1. **MockGraphBuilder فیک است**
   - متد `build_from_text` در کد واقعی وجود ندارد
   - 500+ خط لاجیک گراف‌بیلدر bypass شده

2. **MockKnowledgeGraph فیک است**
   - همیشه data ثابت برمی‌گردونه
   - Semantic matching, Neo4j query, confidence scoring همه skip شدن

3. **Datetime mocking برای determinism**
   - تست determinism رو با ماک کردن datetime ثابت می‌کنه
   - این فریب است - سیستم واقعی رو تست نمی‌کنه

4. **Exception handling خیلی کلی**
   - `pytest.raises(Exception)` هر exception رو قبول می‌کنه
   - باید exception type مشخص باشه

5. **Threshold های شل**
   - `len(reg) < 50` خیلی شل هست
   - باید دقیق‌تر باشه

6. **Ledger failure simulation نشده**
   - فقط state machine تست شده
   - هیچ ledger failure واقعی simulate نشده

---

## 🎯 تست‌های خوب (که نباید تغییر کنن):

1. ✅ Test 3.C.1: Hidden Mutable State Injection
2. ✅ Test 3.D.1: Force Transition Critical Bypass

این دو تست واقعاً خوبن و بدون ماک کار می‌کنن.

---

## 🔧 راه‌حل‌های پیشنهادی:

### راه‌حل 1: حذف Mock ها و استفاده از سیستم واقعی

```python
# به جای MockGraphBuilder
from mahoun.graph.ultra_graph_builder import UltraGraphBuilder

# به جای MockKnowledgeGraph
from mahoun.reasoning.knowledge_graph import LegalKnowledgeGraph
```

**مشکل:** نیاز به Neo4j, ChromaDB, و منابع سنگین

**راه‌حل:** استفاده از in-memory implementations یا test fixtures

### راه‌حل 2: Integration Tests با Docker

```yaml
# docker-compose.test.yml
services:
  test-verification:
    build: .
    depends_on:
      - neo4j
      - postgres
      - redis
    environment:
      - MAHOUN_MODE=enterprise_full
```

### راه‌حل 3: Partial Mocking (فقط external dependencies)

```python
# Mock فقط Neo4j/ChromaDB queries
# اما logic واقعی رو نگه دار
class TestKnowledgeGraph(LegalKnowledgeGraph):
    def __init__(self):
        # Skip Neo4j connection
        self.rules = [...]  # Test data
        
    def find_applicable_rules(self, facts):
        # Use REAL semantic matching logic
        # But query from self.rules instead of Neo4j
        return self._real_semantic_matching(facts, self.rules)
```

---

## 📈 امتیاز کیفیت تست‌ها:

| Category | Test Count | Real Tests | Mocked Tests | Score |
|----------|-----------|------------|--------------|-------|
| Easy     | 2         | 0          | 2            | 0/10  |
| Medium   | 2         | 0          | 2            | 0/10  |
| Extreme  | 5         | 2          | 3            | 4/10  |
| **Total**| **9**     | **2**      | **7**        | **2/10** |

---

## 🚨 نتیجه‌گیری:

**تست‌ها به شدت ساده‌سازی شده‌اند و سیستم واقعی را تست نمی‌کنند.**

7 از 9 تست (78%) از Mock استفاده می‌کنند که:
- متدهای فیک دارند (build_from_text)
- لاجیک واقعی را bypass می‌کنند
- Data ثابت برمی‌گردانند
- Determinism را با datetime mocking ثابت می‌کنند

**این تست‌ها فقط می‌توانند regression های ساده را detect کنند، نه bug های واقعی.**

---

## ✅ توصیه‌های فوری:

1. **حذف MockGraphBuilder و MockKnowledgeGraph**
2. **استفاده از in-memory implementations واقعی**
3. **حذف datetime mocking - تست determinism واقعی**
4. **Exception type های مشخص**
5. **Threshold های دقیق‌تر**
6. **Ledger failure simulation واقعی**
7. **Integration tests با Docker**

---

**امضا:** Kiro Forensic Architecture Guardian
**تاریخ:** 2026-05-09
**وضعیت:** 🔴 CRITICAL - نیاز به بازنویسی فوری
