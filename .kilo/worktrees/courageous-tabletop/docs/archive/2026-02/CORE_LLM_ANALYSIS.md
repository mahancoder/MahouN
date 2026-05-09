# تحلیل ماژول‌های LLM در Core

## 📍 وضعیت فعلی

### ماژول‌های موجود در `mahoun/core/llm/`:
1. `__init__.py` - Lazy imports
2. `bandit.py` - Bandit controller
3. `fallback.py` - Fallback chains
4. `local_driver.py` - Local LLM driver
5. `orchestrator.py` - Model orchestrator
6. `router.py` - LLM router
7. `ultra_engine.py` - Ultra LLM engine
8. `ultra_loader.py` - Ultra model loader
9. `uncertainty.py` - Uncertainty model

## 📊 استفاده‌کنندگان (Usage Analysis)

### استفاده در Production Code:
1. **mahoun/agents/orchestrator.py** ✅
   - Import: `ultra_loader`, `router`, `bandit`, `uncertainty`, `ultra_engine`, `fallback`
   - نقش: Agent orchestration

2. **mahoun/reasoning/adapters.py** ✅
   - Import: `orchestrator.get_orchestrator()`
   - نقش: Reasoning engine integration

3. **mahoun/rag/query_router.py** ✅
   - Import: `orchestrator.get_orchestrator()`, `ModelCapability`
   - نقش: RAG query routing

### استفاده در Tests:
1. `tests/test_llm_router_simple.py`
2. `tests/test_llm_router_properties.py`
3. `tests/test_llm_router_properties_complete.py`
4. `tests/test_local_llm_driver.py`
5. `tests/contracts/test_reasoning_protocols_contracts.py`

### استفاده در Scripts/Demos:
1. `demo_switching_logic.py`
2. `demo_local_llm.py`
3. `scripts/verify_protocol_architecture.py`
4. `examples/reasoning_engine_demo.py`
5. `deadlock_audit_test.py`

## 🎯 تصمیم‌گیری

### آیا این ماژول‌ها Orphaned هستن؟
**❌ خیر** - این ماژول‌ها به طور فعال استفاده می‌شن در:
- Agents
- Reasoning
- RAG
- Multiple tests

### آیا باید جابجا بشن؟
**🤔 بله، احتمالاً باید به `mahoun/llm/` منتقل بشن**

#### دلایل انتقال:
1. **Separation of Concerns**: LLM management یک concern مستقل است، نه core utility
2. **Architecture Clarity**: Core باید فقط shared utilities داشته باشه
3. **Consistency**: مشابه `mahoun/reasoning/`, `mahoun/rag/`, etc.
4. **Scalability**: اگر LLM features بیشتر بشه، core شلوغ می‌شه

#### دلایل نگه‌داشتن در Core:
1. **Wide Usage**: در چندین ماژول استفاده می‌شه
2. **Infrastructure Role**: مثل orchestration و routing
3. **Breaking Changes**: تغییر imports در همه جا

## 📋 پیشنهاد نهایی

### گزینه 1: انتقال به `mahoun/llm/` (توصیه می‌شود) ⭐
```
mahoun/
├── llm/                    # NEW
│   ├── __init__.py
│   ├── bandit.py
│   ├── fallback.py
│   ├── local_driver.py
│   ├── orchestrator.py
│   ├── router.py
│   ├── ultra_engine.py
│   ├── ultra_loader.py
│   └── uncertainty.py
```

**مزایا:**
- معماری تمیزتر
- Core سبک‌تر می‌شه
- مطابق با structure.md نیست (چون llm در structure ذکر نشده)

**معایب:**
- باید همه imports رو update کنیم
- ممکنه چیزی بشکنه

### گزینه 2: نگه‌داشتن در Core (محافظه‌کارانه)
**مزایا:**
- هیچ چیزی نمی‌شکنه
- کمتر کار داره

**معایب:**
- Core شلوغ می‌مونه
- معماری واضح نیست

## 🚀 پلان اجرایی (اگر تصمیم به انتقال گرفتیم)

### Phase 1: آماده‌سازی
1. ✅ بررسی همه استفاده‌کنندگان (این فایل)
2. ⬜ ایجاد `mahoun/llm/` directory
3. ⬜ کپی کردن فایل‌ها به مکان جدید
4. ⬜ Update کردن `__init__.py` در llm

### Phase 2: Update Imports
1. ⬜ Update production code (3 files)
2. ⬜ Update tests (5 files)
3. ⬜ Update scripts/demos (5 files)
4. ⬜ Update backups (if needed)

### Phase 3: Testing
1. ⬜ Run all tests
2. ⬜ Check imports
3. ⬜ Verify no broken references

### Phase 4: Cleanup
1. ⬜ Delete `mahoun/core/llm/`
2. ⬜ Update documentation
3. ⬜ Commit changes

## ⚠️ ریسک‌ها

1. **Import Errors**: ممکنه جایی import رو از قلم بندازیم
2. **Circular Dependencies**: ممکنه circular import ایجاد بشه
3. **Test Failures**: ممکنه تست‌ها fail بشن
4. **Hidden References**: ممکنه reference‌های پنهان وجود داشته باشه

## 💡 توصیه

با توجه به:
- استفاده گسترده در production code
- ریسک بالای breaking changes
- عدم وجود llm در structure.md

**پیشنهاد می‌کنم:**
1. **فعلاً نگه‌داریم در core** تا پاکسازی‌های دیگه تموم بشه
2. بعداً در یک phase جداگانه منتقلش کنیم
3. یا اگر می‌خوای الان انتقال بدیم، باید خیلی دقیق باشیم

## 🎬 تصمیم نهایی شما؟

آیا می‌خواهید:
- A) الان منتقلش کنیم به `mahoun/llm/` (ریسک متوسط، معماری بهتر)
- B) فعلاً نگه‌داریم در core (ریسک صفر، معماری فعلی)
- C) بررسی بیشتر و تصمیم بعدی
