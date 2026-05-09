# 🚨 CRITICAL: Type Duplication Crisis in Core Architecture

## تاریخ: 2026-02-10
## وضعیت: CRITICAL - نیاز به رفع فوری

---

## مشکل اصلی

**دو تا تعریف مختلف از QueryType و QueryClassification داریم:**

### 1. تعریف در Core Protocols (هسته سیستم)
```python
# mahoun/core/protocols.py
class QueryType(str, Enum):
    CONTRACT = "contract"
    DELAY_ANALYSIS = "delay_analysis"
    LEGAL_INQUIRY = "legal_inquiry"
    TECHNICAL_INQUIRY = "technical_inquiry"
    CYPHER_GENERATION = "cypher_generation"
    GENERAL = "general"

@dataclass(frozen=True)
class QueryClassificationResult:
    query: str
    query_type: QueryType
    confidence: float
    keywords_found: List[str]
    metadata: Dict[str, Any]
    required_capability: Optional[str] = None
```

### 2. تعریف در RAG Layer
```python
# mahoun/rag/query_router.py
class QueryType(str, Enum):  # ⚠️ DUPLICATE!
    CONTRACT = "contract"
    DELAY_ANALYSIS = "delay_analysis"
    LEGAL_INQUIRY = "legal_inquiry"
    TECHNICAL_INQUIRY = "technical_inquiry"
    CYPHER_GENERATION = "cypher_generation"
    GENERAL = "general"

@dataclass
class QueryClassification:  # ⚠️ DIFFERENT NAME!
    query: str
    query_type: QueryType
    confidence: float
    keywords_found: List[str]
    metadata: Dict[str, Any]
    required_capability: Optional[str] = None
```

---

## چرا این مشکل CRITICAL است؟

### 1. نقض Dependency Inversion Principle (DIP)
- **هسته سیستم** (`mahoun.core.protocols`) نباید به **لایه RAG** وابسته باشد
- **لایه RAG** باید به **هسته سیستم** وابسته باشد (نه برعکس!)

### 2. Type Incompatibility
```python
# این کار نمی‌کنه! ❌
rag_result = await query_router.classify("query")
# rag_result is QueryClassification (from RAG)

assert isinstance(rag_result, QueryClassificationResult)  # FAILS!
# QueryClassificationResult is from protocols
```

### 3. نقض Single Source of Truth
- دو تعریف مختلف = دو منبع حقیقت
- تغییر در یکی نیاز به تغییر در دیگری
- احتمال inconsistency بالا

### 4. Testing Nightmare
- تست‌ها باید با دو تایپ مختلف کار کنند
- نیاز به adapter/converter functions
- پیچیدگی غیرضروری

---

## تأثیر بر Architecture

### Layering Violation
```
┌─────────────────────────────────────┐
│   Application Layer                 │
│   (API, CLI, etc.)                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Reasoning Layer                   │
│   (UnifiedReasoningEngine)          │
│   Uses: QueryClassificationResult   │ ← از protocols استفاده می‌کنه
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   RAG Layer                         │
│   (QueryRouter)                     │
│   Returns: QueryClassification      │ ← تایپ متفاوت برمی‌گردونه! ❌
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Core Layer (Protocols)            │
│   Defines: QueryClassificationResult│
└─────────────────────────────────────┘
```

**مشکل**: RAG Layer باید از Core Layer استفاده کنه، نه اینکه تایپ خودش رو تعریف کنه!

---

## راه‌حل‌های ممکن

### گزینه 1: حذف تعریف از RAG Layer (RECOMMENDED ✅)
```python
# mahoun/rag/query_router.py
from mahoun.core.protocols import QueryType, QueryClassificationResult

class QueryRouter:
    async def classify(self, query: str) -> QueryClassificationResult:
        # استفاده از تایپ از protocols
        return QueryClassificationResult(...)
```

**مزایا:**
- ✅ Single source of truth
- ✅ Type compatibility
- ✅ Follows DIP
- ✅ No adapters needed

**معایب:**
- ⚠️ نیاز به تغییر در QueryRouter
- ⚠️ ممکنه کدهای دیگه هم تغییر کنند

### گزینه 2: Adapter Pattern (TEMPORARY WORKAROUND)
```python
def convert_rag_to_protocol(rag: QueryClassification) -> QueryClassificationResult:
    return QueryClassificationResult(
        query=rag.query,
        query_type=QueryType[rag.query_type.name],
        confidence=rag.confidence,
        keywords_found=rag.keywords_found,
        metadata=rag.metadata,
        required_capability=rag.required_capability,
    )
```

**مزایا:**
- ✅ کار می‌کنه (فعلاً)
- ✅ نیاز به تغییر کم

**معایب:**
- ❌ Technical debt
- ❌ Performance overhead
- ❌ Complexity
- ❌ مشکل اصلی رو حل نمی‌کنه

### گزینه 3: Type Alias (WRONG ❌)
```python
# mahoun/rag/query_router.py
from mahoun.core.protocols import QueryClassificationResult as QueryClassification
```

**چرا اشتباهه:**
- ❌ فقط اسم رو عوض می‌کنه
- ❌ مشکل duplication رو حل نمی‌کنه
- ❌ Confusing

---

## تصمیم نهایی: گزینه 1 (Refactor RAG Layer)

### مراحل اجرا:

#### 1. حذف تعریف‌های duplicate از `mahoun/rag/query_router.py`
```python
# BEFORE ❌
class QueryType(str, Enum):
    CONTRACT = "contract"
    ...

@dataclass
class QueryClassification:
    ...

# AFTER ✅
from mahoun.core.protocols import QueryType, QueryClassificationResult
```

#### 2. تغییر return type در QueryRouter
```python
# BEFORE ❌
async def classify(self, query: str) -> QueryClassification:
    return QueryClassification(...)

# AFTER ✅
async def classify(self, query: str) -> QueryClassificationResult:
    return QueryClassificationResult(...)
```

#### 3. تغییر RoutedQueryResult
```python
# BEFORE ❌
@dataclass
class RoutedQueryResult:
    classification: QueryClassification  # از RAG

# AFTER ✅
from mahoun.core.protocols import RoutedQueryResult
# استفاده از تعریف protocols
```

#### 4. آپدیت تست‌ها
- حذف converter functions
- استفاده مستقیم از protocol types
- تست type compatibility

---

## Impact Analysis

### فایل‌هایی که باید تغییر کنند:

1. **mahoun/rag/query_router.py** (CRITICAL)
   - حذف QueryType enum
   - حذف QueryClassification dataclass
   - حذف RoutedQueryResult dataclass
   - import از protocols

2. **mahoun/reasoning/unified_engine.py** (MINOR)
   - ممکنه نیاز به آپدیت imports باشه

3. **tests/test_reasoning_protocols_real.py** (MINOR)
   - حذف converter function
   - ساده‌سازی تست‌ها

4. **mahoun/reasoning/adapters.py** (CHECK)
   - بررسی استفاده از types

### فایل‌هایی که ممکنه تأثیر بگیرند:

- `mahoun/rag/hybrid_rag_service.py`
- `examples/reasoning_engine_demo.py`
- سایر تست‌ها

---

## Verification Checklist

پس از refactoring:

- [ ] همه تست‌ها pass می‌شوند
- [ ] mypy errors نداریم
- [ ] فقط یک تعریف QueryType داریم
- [ ] فقط یک تعریف QueryClassificationResult داریم
- [ ] RAG Layer از Core Layer استفاده می‌کنه
- [ ] هیچ adapter/converter function نداریم
- [ ] Documentation آپدیت شده

---

## درس‌های آموخته شده

### 1. Always Define Core Types in Core Layer
- Domain types باید در `mahoun.core` باشند
- نه در لایه‌های بالاتر (RAG, API, etc.)

### 2. Follow Dependency Direction
```
Application → Reasoning → RAG → Core
                                  ↑
                            همه به اینجا وابسته‌اند
```

### 3. Single Source of Truth
- هر type فقط یک بار تعریف می‌شه
- در پایین‌ترین لایه‌ای که نیاز داره

### 4. Protocol-First Design
- اول protocols رو تعریف کن
- بعد implementations رو بساز
- نه برعکس!

---

## Priority: P0 (CRITICAL)

این مشکل باید **قبل از هر کار دیگه‌ای** حل بشه چون:
- ✅ تأثیر مستقیم بر architecture
- ✅ مانع testing واقعی
- ✅ Technical debt بالا
- ✅ نقض اصول SOLID

---

## Next Steps

1. ✅ این گزارش رو بخون و تأیید کن
2. ⏳ Refactor `mahoun/rag/query_router.py`
3. ⏳ آپدیت تست‌ها
4. ⏳ Run full test suite
5. ⏳ Verify mypy
6. ⏳ Update documentation

---

**تاریخ ایجاد**: 2026-02-10  
**وضعیت**: OPEN  
**اولویت**: P0 - CRITICAL  
**تخمین زمان**: 2-3 ساعت
