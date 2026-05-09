# بررسی وضعیت موارد بعدی (Next Steps Status Analysis)
**تاریخ**: 2026-02-22  
**وضعیت کلی**: بررسی سه مورد از لیست Next Steps

---

## خلاصه اجرایی

از سه مورد پیشنهادی در لیست Next Steps:
- ❌ **مورد 1**: Fix remaining 8 violations - **تکمیل نشده** (8 violation همچنان باقی است)
- ❌ **مورد 2**: Add integration tests for adapters - **تکمیل نشده** (هیچ تست یافت نشد)
- ❌ **مورد 3**: Create ADRs for adapter pattern - **تکمیل نشده** (هیچ ADR یافت نشد)

**نتیجه**: هیچ یک از سه مورد تکمیل نشده‌اند.

---

## مورد 1: Fix Remaining 8 Violations in core/health_checker.py

### وضعیت فعلی: ❌ تکمیل نشده

### نتایج Boundary Checker:
```
❌ BOUNDARY VIOLATIONS FOUND: 8

Core Module: core (6 violation(s))
--------------------------------------------------------------------------------
1. mahoun/core/health_checker.py:93
   Core module 'core' imports from non-core 'pipelines'
   Statement: from mahoun.pipelines.llm.ollama_llm import OllamaLLMService

2. mahoun/core/health_checker.py:142
   Core module 'core' imports from non-core 'pipelines'
   Statement: from mahoun.pipelines.vector_store.manager import VectorStoreManager

3. mahoun/core/health_checker.py:285
   Core module 'core' imports from non-core 'agents'
   Statement: from mahoun.agents import UltraDocParserAgent, DisputeAgent, ...

4. mahoun/core/health_checker.py:351
   Core module 'core' imports from non-core 'retrieval'
   Statement: from mahoun.retrieval.ultra_hybrid_search import UltraHybridSearch

5. mahoun/core/health_checker.py:427
   Core module 'core' imports from non-core 'self_improve'
   Statement: from mahoun.self_improve.ultra_self_improvement_system import UltraSelfImprovementSystem

6. mahoun/core/health_checker.py:395
   Core module 'core' imports from non-core 'uncertainty'
   Statement: from mahoun.uncertainty.gaussian_process import GaussianProcessUncertainty

Core Module: schemas (2 violation(s))
--------------------------------------------------------------------------------
7. mahoun/schemas/legal_migration_service.py:32
   Core module 'schemas' imports from non-core 'rag'
   Statement: from mahoun.rag.hybrid_rag_service import HybridRAGService

8. mahoun/schemas/legal_migration_service.py:1329
   Core module 'schemas' imports from non-core 'rag'
   Statement: from mahoun.rag.hybrid_rag_service import create_hybrid_rag_service
```

### تحلیل:

#### 6 Violations در health_checker.py:
- **ماهیت**: health_checker.py یک ماژول infrastructure است که برای health check تمام سیستم طراحی شده
- **مشکل معماری**: این فایل در `mahoun/core/` قرار دارد اما core نیست
- **راه‌حل پیشنهادی**: 
  1. ✅ **بهترین راه‌حل**: انتقال به `mahoun/infrastructure/health_checker.py`
  2. ⚠️ **راه‌حل موقت**: ایجاد adapter pattern (مانند reasoning module)
  3. ❌ **راه‌حل ضعیف**: نادیده گرفتن (قابل قبول نیست)

#### 2 Violations در legal_migration_service.py:
- **ماهیت**: این فایل یک utility/service است نه schema
- **مشکل معماری**: فایل در `mahoun/schemas/` قرار دارد اما schema نیست
- **راه‌حل پیشنهادی**:
  1. ✅ **بهترین راه‌حل**: انتقال به `mahoun/services/legal_migration_service.py`
  2. ⚠️ **راه‌حل موقت**: ایجاد adapter pattern

### اولویت: 🔴 MEDIUM (نه فوری اما مهم)

**دلیل اولویت متوسط**:
- این violations در ماژول‌های infrastructure/utility هستند نه core domain logic
- reasoning module (که critical بود) قبلاً fix شده است
- این موارد بر zero-hallucination guarantee تأثیر مستقیم ندارند

---

## مورد 2: Add Integration Tests for Adapter Files

### وضعیت فعلی: ❌ تکمیل نشده

### نتایج جستجو:
```bash
# جستجو برای تست‌های adapter
grep -r "guardrails_adapter|rag_adapter|monitoring_adapter" tests/
# نتیجه: No matches found

# جستجو برای تست‌های reasoning با adapter
grep -r "test.*adapter" tests/*.py
# نتیجه: No matches found
```

### فایل‌های Adapter که نیاز به تست دارند:

1. **mahoun/reasoning/guardrails_adapter.py** (45 lines)
   - تست: `create_contradiction_detector()`
   - تست: graceful degradation when guardrails unavailable
   - تست: protocol compliance

2. **mahoun/reasoning/rag_adapter.py** (280 lines)
   - تست: `create_query_router()`
   - تست: `create_rag_service()`
   - تست: `validate_rag_availability()`
   - تست: `get_rag_adapter_info()`
   - تست: graceful degradation
   - تست: thread safety

3. **mahoun/reasoning/monitoring_adapter.py** (75 lines)
   - تست: `get_legal_query_decorator()`
   - تست: no-op decorator when monitoring unavailable
   - تست: decorator functionality when available

### تست‌های موجود مرتبط:

یافت شد: تست‌های reasoning موجود هستند اما adapter-specific نیستند:
- `tests/test_reasoning_edge_cases.py` - تست edge cases
- `tests/test_graph_based_reasoning.py` - تست reasoning با graph
- `tests/test_error_paths.py` - تست error handling
- `tests/test_monitoring_unification_strict.py` - تست monitoring integration

### پیشنهاد: ایجاد فایل‌های تست جدید

```python
# tests/test_reasoning_adapters.py - تست‌های unit
# tests/integration/test_reasoning_adapters_integration.py - تست‌های integration
```

### اولویت: 🟡 LOW-MEDIUM (مهم برای کیفیت اما نه فوری)

**دلیل**:
- Adapter pattern به خوبی طراحی شده و ساده است
- تست‌های موجود reasoning engine به طور غیرمستقیم adapter ها را تست می‌کنند
- اما برای production-grade system، تست‌های مستقیم ضروری هستند

---

## مورد 3: Create ADRs for Adapter Pattern Decisions

### وضعیت فعلی: ❌ تکمیل نشده

### نتایج جستجو:
```bash
# جستجو برای ADR files
find . -name "*ADR*" -o -name "*adr*" -o -name "*decision*"
# نتیجه: فقط فایل‌های sklearn و transformers در venv

# بررسی docs/
ls docs/
# نتیجه: هیچ ADR directory یافت نشد
```

### مستندات موجود:

✅ **مستندات خوب موجود است**:
1. `BOUNDARY_VIOLATIONS_FIX_COMPLETE.md` - گزارش کامل fix
2. `core_manifest.yaml` - مستندات معماری با changelog
3. `mahoun/reasoning/README.md` - احتمالاً شامل توضیحات adapter
4. Inline documentation در adapter files (comprehensive)

### ADR های پیشنهادی برای ایجاد:

#### ADR-001: Adapter Pattern for Cross-Boundary Dependencies
```markdown
# ADR-001: Adapter Pattern for Cross-Boundary Dependencies

## Status
Accepted (2026-02-22)

## Context
Core modules (reasoning, graph, ledger, etc.) need functionality from 
non-core modules (guardrails, rag, monitoring) but cannot import them 
directly due to architectural boundaries.

## Decision
Use runtime adapter pattern with:
- Factory functions for lazy initialization
- Graceful degradation when dependencies unavailable
- Protocol-based type safety
- Thread-safe implementations

## Consequences
+ Zero compile-time dependencies
+ Testable in isolation
+ Graceful degradation
- Slightly more complex code structure
- Runtime import overhead (minimal)
```

#### ADR-002: Protocol-Based Dependency Injection
```markdown
# ADR-002: Protocol-Based Dependency Injection

## Status
Accepted (2026-02-22)

## Context
Need type-safe contracts between core and non-core modules without 
creating hard dependencies.

## Decision
Define protocols in mahoun/core/protocols.py and use dependency 
injection at runtime.

## Consequences
+ Type safety without coupling
+ Easy to mock for testing
+ Clear contracts
- Requires discipline to maintain protocols
```

#### ADR-003: Boundary Checker Exclusion for Adapters
```markdown
# ADR-003: Boundary Checker Exclusion for Adapters

## Status
Accepted (2026-02-22)

## Context
Adapter files (*_adapter.py) are explicitly designed for runtime 
imports and should not be flagged as boundary violations.

## Decision
Exclude *_adapter.py files from boundary checking.

## Consequences
+ Cleaner boundary check reports
+ Explicit architectural pattern
- Need to ensure adapters follow best practices
```

### اولویت: 🟢 LOW (مفید اما نه ضروری)

**دلیل**:
- مستندات خوبی در `BOUNDARY_VIOLATIONS_FIX_COMPLETE.md` و `core_manifest.yaml` موجود است
- ADR ها برای تیم‌های بزرگ و تصمیمات طولانی‌مدت مفیدتر هستند
- برای پروژه فعلی، مستندات موجود کافی است

---

## جمع‌بندی و توصیه‌ها

### وضعیت کلی: 0/3 تکمیل شده ❌

| مورد | وضعیت | اولویت | زمان تخمینی | توصیه |
|------|--------|--------|-------------|-------|
| 1. Fix 8 violations | ❌ تکمیل نشده | 🔴 MEDIUM | 2-3 ساعت | **انجام دهید** |
| 2. Integration tests | ❌ تکمیل نشده | 🟡 LOW-MEDIUM | 3-4 ساعت | انجام دهید (اما نه فوری) |
| 3. Create ADRs | ❌ تکمیل نشده | 🟢 LOW | 1-2 ساعت | اختیاری (مستندات کافی موجود است) |

### توصیه اولویت‌بندی:

#### 🔴 اولویت 1 (فوری): Fix 8 Boundary Violations
**چرا؟**
- معماری را تمیز می‌کند
- CI/CD gate را pass می‌کند
- نشان‌دهنده consistency در معماری است

**چگونه؟**
1. انتقال `health_checker.py` به `mahoun/infrastructure/`
2. انتقال `legal_migration_service.py` به `mahoun/services/`
3. به‌روزرسانی import ها
4. اجرای تست‌ها

**زمان**: 2-3 ساعت

---

#### 🟡 اولویت 2 (مهم): Add Integration Tests
**چرا؟**
- کیفیت کد را بالا می‌برد
- اطمینان از عملکرد صحیح adapter ها
- regression testing

**چگونه؟**
1. ایجاد `tests/test_reasoning_adapters.py`
2. ایجاد `tests/integration/test_reasoning_adapters_integration.py`
3. تست scenarios:
   - Adapter با dependency موجود
   - Adapter با dependency غیرموجود (graceful degradation)
   - Thread safety
   - Protocol compliance

**زمان**: 3-4 ساعت

---

#### 🟢 اولویت 3 (اختیاری): Create ADRs
**چرا؟**
- مستندسازی تصمیمات معماری
- مفید برای تیم‌های بزرگ
- historical record

**چگونه؟**
1. ایجاد `docs/adr/` directory
2. ایجاد ADR-001, ADR-002, ADR-003
3. لینک از README.md

**زمان**: 1-2 ساعت

---

## نتیجه‌گیری نهایی

### ✅ کارهای انجام شده (از session قبل):
- Reasoning module: 100% clean (0 violations)
- 3 enterprise-grade adapters created
- 18 failed tests fixed
- Manifests updated to v1.2.0
- Architecture score: 6/10 → 9/10

### ❌ کارهای باقی‌مانده:
- 8 boundary violations در core/health_checker.py و schemas/legal_migration_service.py
- Integration tests برای adapter files
- ADR documentation (اختیاری)

### 🎯 توصیه بعدی:
**شروع با اولویت 1**: Fix remaining 8 violations

این کار:
- معماری را 100% clean می‌کند
- CI gate 7 (architecture) را pass می‌کند
- نشان‌دهنده consistency و discipline در معماری است

**آیا می‌خواهید الان شروع کنیم؟** 🚀

---

**تهیه‌کننده**: Kiro AI Assistant  
**تاریخ**: 2026-02-22  
**نسخه**: 1.0
