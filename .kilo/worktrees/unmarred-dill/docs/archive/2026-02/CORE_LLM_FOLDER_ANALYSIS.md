# تحلیل فولدر mahoun/core/llm
## آنالیز وضعیت و تصمیم‌گیری

تاریخ: 2026-02-23

## وضعیت فعلی

### فایل‌های موجود در `mahoun/core/llm/`:
```
mahoun/core/llm/
├── __init__.py           # Lazy imports
├── bandit.py             # Multi-armed bandit for model selection
├── fallback.py           # Fallback chains
├── local_driver.py       # Local LLM driver (llama.cpp)
├── orchestrator.py       # Model lifecycle management
├── router.py             # Enterprise LLM router (1448 lines!)
├── ultra_engine.py       # Ultra LLM engine
├── ultra_loader.py       # Model loader
└── uncertainty.py        # Uncertainty quantification
```

### استفاده واقعی در کدبیس:

**فقط 4 فایل در mahoun از این ماژول استفاده می‌کنند:**

1. `mahoun/rag/query_router.py`
   ```python
   from mahoun.core.llm.orchestrator import get_orchestrator, ModelCapability
   ```

2. `mahoun/reasoning/adapters.py`
   ```python
   from mahoun.core.llm.orchestrator import get_orchestrator
   ```

3. `mahoun/core/llm/orchestrator.py` (خودش!)
   ```python
   from mahoun.core.llm.local_driver import LocalLLMDriver
   ```

4. `mahoun/agents/orchestrator.py`
   ```python
   from mahoun.core.llm.ultra_loader import UltraModelLoader
   from mahoun.core.llm.router import ExpertRouter
   from mahoun.core.llm.bandit import BanditController
   from mahoun.core.llm.uncertainty import UncertaintyModel
   from mahoun.core.llm.ultra_engine import UltraLLMEngine
   from mahoun.core.llm.fallback import AVAILABLE_MODELS, MODEL_CAPS
   ```
   **اما این import ها در try/except هستند و احتمالاً استفاده نمی‌شوند!**

### استفاده در تست‌ها:
- `tests/test_llm_router_simple.py`
- `tests/test_llm_router_properties.py`
- `tests/test_local_llm_driver.py`
- `tests/test_llm_router_properties_complete.py`

## تحلیل معماری

### مشکلات:

1. **Over-Engineering شدید:**
   - `router.py`: 1448 خط کد برای routing!
   - Circuit breakers، multi-armed bandits، uncertainty quantification
   - خیلی پیچیده برای use case فعلی

2. **استفاده محدود:**
   - فقط `orchestrator.py` و `ModelCapability` واقعاً استفاده می‌شوند
   - بقیه ماژول‌ها (bandit، ultra_engine، uncertainty) تقریباً unused

3. **Dependency به torch و transformers:**
   - این dependencies سنگین هستند
   - برای core module مناسب نیست

4. **تداخل با mahoun/reasoning:**
   - `mahoun/reasoning/adapters.py` از orchestrator استفاده می‌کند
   - اما reasoning خودش model management دارد

## گزینه‌های پیش رو

### گزینه 1: حذف کامل ❌
**نه! این خطرناک است چون:**
- `orchestrator.py` در 2 جای مهم استفاده می‌شود
- `ModelCapability` enum مورد استفاده است
- تست‌های زیادی روی router نوشته شده

### گزینه 2: Simplify و Refactor ✅ (توصیه می‌شود)

**مراحل:**

1. **نگه داشتن:**
   - `orchestrator.py` - در حال استفاده
   - `local_driver.py` - dependency orchestrator
   - `__init__.py` - interface

2. **Archive کردن (به mahoun/core/archive/llm/):**
   - `router.py` - خیلی پیچیده، کم استفاده
   - `bandit.py` - unused
   - `ultra_engine.py` - unused
   - `ultra_loader.py` - unused
   - `uncertainty.py` - unused
   - `fallback.py` - می‌تواند به orchestrator merge شود

3. **Simplify orchestrator.py:**
   - حذف dependency به router
   - ساده‌سازی ModelCapability
   - نگه داشتن فقط core functionality

### گزینه 3: Move به mahoun/infrastructure/ ⚠️

**منطق:**
- LLM management یک infrastructure concern است
- نه core concern
- اما این breaking change بزرگی است

### گزینه 4: Keep as-is با Documentation 📝

**اگر زمان کم است:**
- فقط یک README.md اضافه کنید
- مشخص کنید کدام ماژول‌ها production-ready هستند
- بقیه را experimental علامت بزنید

## توصیه نهایی: گزینه 2 (Simplify)

### Plan اجرایی:

#### Phase 1: Archive Unused Modules (کم خطر)
```bash
mkdir -p mahoun/core/archive/llm
mv mahoun/core/llm/router.py mahoun/core/archive/llm/
mv mahoun/core/llm/bandit.py mahoun/core/archive/llm/
mv mahoun/core/llm/ultra_engine.py mahoun/core/archive/llm/
mv mahoun/core/llm/ultra_loader.py mahoun/core/archive/llm/
mv mahoun/core/llm/uncertainty.py mahoun/core/archive/llm/
mv mahoun/core/llm/fallback.py mahoun/core/archive/llm/
```

#### Phase 2: Update Imports
```python
# mahoun/agents/orchestrator.py
# Comment out or remove unused imports
# try:
#     from mahoun.core.llm.ultra_loader import UltraModelLoader
#     ...
# except ImportError:
#     pass
```

#### Phase 3: Simplify orchestrator.py
- حذف dependency به router
- ساده‌سازی ModelCapability enum
- نگه داشتن فقط:
  - `get_orchestrator()`
  - `ModelCapability` enum
  - `get_driver(capability)` method

#### Phase 4: Update Tests
- نگه داشتن تست‌های orchestrator
- Archive کردن تست‌های router

#### Phase 5: Documentation
```markdown
# mahoun/core/llm/README.md

## LLM Module

### Production-Ready:
- `orchestrator.py` - Model lifecycle management
- `local_driver.py` - Local LLM driver

### Archived (Experimental):
- `router.py` - Enterprise router (over-engineered)
- `bandit.py` - Multi-armed bandit (unused)
- `ultra_engine.py` - Ultra engine (experimental)
- `uncertainty.py` - Uncertainty quantification (unused)

See `mahoun/core/archive/llm/` for archived modules.
```

## تاثیر بر سیستم

### Breaking Changes: خیر
- فقط ماژول‌های unused archive می‌شوند
- orchestrator و local_driver باقی می‌مانند
- API عمومی تغییر نمی‌کند

### Benefits:
1. **Clarity:** مشخص می‌شود چه چیزی production است
2. **Maintainability:** کد کمتر برای نگهداری
3. **Performance:** dependencies کمتر
4. **Documentation:** واضح‌تر می‌شود

### Risks: کم
- تست‌های archive شده ممکن است fail شوند (قابل قبول)
- اگر کسی از router استفاده می‌کرد، باید به archive برود (بعید است)

## Timeline پیشنهادی

### اگر زمان دارید (2-3 ساعت):
1. Phase 1: Archive unused (30 min)
2. Phase 2: Update imports (30 min)
3. Phase 3: Simplify orchestrator (1 hour)
4. Phase 4: Update tests (30 min)
5. Phase 5: Documentation (30 min)

### اگر زمان ندارید (30 دقیقه):
1. فقط یک README.md اضافه کنید
2. مشخص کنید کدام ماژول‌ها production هستند
3. بقیه را "experimental" علامت بزنید

## نتیجه‌گیری

**تصمیم: Simplify (گزینه 2)**

این فولدر یک نمونه از over-engineering است که در مراحل اولیه پروژه اتفاق افتاده. 
بیشتر ماژول‌ها unused هستند و فقط orchestrator واقعاً مورد استفاده است.

**Action Items:**
1. ✅ Archive unused modules
2. ✅ Simplify orchestrator
3. ✅ Add documentation
4. ✅ Update tests

**Priority: Medium**
- نه فوری (سیستم کار می‌کند)
- اما برای maintainability مهم است
- می‌تواند در یک refactoring sprint انجام شود

---

**نکته مهم:** این تحلیل نشان می‌دهد که گاهی بهتر است کد ساده‌تر بنویسیم تا کد "enterprise-grade" پیچیده که استفاده نمی‌شود!
