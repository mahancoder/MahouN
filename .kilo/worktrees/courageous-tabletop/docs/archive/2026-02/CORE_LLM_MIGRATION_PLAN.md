# Migration Plan: mahoun/core/llm → mahoun/llm
## خارج کردن LLM از هسته

تاریخ: 2026-02-23

## چرا این کار را انجام می‌دهیم؟

1. **LLM management یک infrastructure concern است، نه core:**
   - Core باید فقط models، protocols، و config داشته باشد
   - LLM orchestration یک implementation detail است

2. **هسته تحت تاثیر نیست:**
   - `mahoun/core/__init__.py` هیچ چیزی از llm export نمی‌کند
   - همه imports مستقیم هستند: `from mahoun.core.llm.orchestrator`

3. **Separation of Concerns:**
   - Core = تعاریف و قراردادها
   - LLM = پیاده‌سازی و مدیریت مدل‌ها

## Migration Path

### مرحله 1: Move فولدر
```bash
# از mahoun/core/llm به mahoun/llm
mv mahoun/core/llm mahoun/llm
```

### مرحله 2: Update Imports
تغییر همه imports از:
```python
from mahoun.core.llm.orchestrator import get_orchestrator
```
به:
```python
from mahoun.llm.orchestrator import get_orchestrator
```

### فایل‌هایی که باید update شوند:

1. **mahoun/rag/query_router.py**
   ```python
   - from mahoun.core.llm.orchestrator import get_orchestrator, ModelCapability
   + from mahoun.llm.orchestrator import get_orchestrator, ModelCapability
   ```

2. **mahoun/reasoning/adapters.py**
   ```python
   - from mahoun.core.llm.orchestrator import get_orchestrator
   + from mahoun.llm.orchestrator import get_orchestrator
   ```

3. **mahoun/agents/orchestrator.py**
   ```python
   - from mahoun.core.llm.ultra_loader import UltraModelLoader
   - from mahoun.core.llm.router import ExpertRouter
   - from mahoun.core.llm.bandit import BanditController
   - from mahoun.core.llm.uncertainty import UncertaintyModel
   - from mahoun.core.llm.ultra_engine import UltraLLMEngine
   - from mahoun.core.llm.fallback import AVAILABLE_MODELS, MODEL_CAPS
   + from mahoun.llm.ultra_loader import UltraModelLoader
   + from mahoun.llm.router import ExpertRouter
   + from mahoun.llm.bandit import BanditController
   + from mahoun.llm.uncertainty import UncertaintyModel
   + from mahoun.llm.ultra_engine import UltraLLMEngine
   + from mahoun.llm.fallback import AVAILABLE_MODELS, MODEL_CAPS
   ```

4. **mahoun/llm/orchestrator.py** (خودش!)
   ```python
   - from mahoun.core.llm.local_driver import LocalLLMDriver
   + from mahoun.llm.local_driver import LocalLLMDriver
   ```

### مرحله 3: Update Tests

تست‌هایی که باید update شوند:
- `tests/test_llm_router_simple.py`
- `tests/test_llm_router_properties.py`
- `tests/test_local_llm_driver.py`
- `tests/test_llm_router_properties_complete.py`
- `tests/contracts/test_reasoning_protocols_contracts.py`

همه imports از `mahoun.core.llm` به `mahoun.llm` تغییر می‌کنند.

### مرحله 4: Update Documentation

فایل‌های doc که باید update شوند:
- `core_manifest.yaml`
- `MANIFEST_UPDATE_PROTOCOLS_ADAPTERS.md`
- `به‌روزرسانی_مانیفست_پروتکل_آداپتور.md`
- `MAHOUN_ARCHITECTURE_RECONCILIATION_FINAL.md`
- `ARCHITECTURE_CRISIS_ANALYSIS.md`

### مرحله 5: Update Examples

- `examples/reasoning_engine_demo.py`
- `demo/examples/reasoning_engine_demo.py`
- `demo_switching_logic.py`
- `demo_local_llm.py`

## Execution Script

```bash
#!/bin/bash
# migrate_llm_out_of_core.sh

set -e

echo "🚀 Starting LLM migration from core..."

# Step 1: Move folder
echo "📦 Moving mahoun/core/llm to mahoun/llm..."
mv mahoun/core/llm mahoun/llm

# Step 2: Update imports in mahoun/
echo "🔄 Updating imports in mahoun/..."
find mahoun -name "*.py" -type f -exec sed -i 's/from mahoun\.core\.llm/from mahoun.llm/g' {} \;
find mahoun -name "*.py" -type f -exec sed -i 's/import mahoun\.core\.llm/import mahoun.llm/g' {} \;

# Step 3: Update imports in tests/
echo "🧪 Updating imports in tests/..."
find tests -name "*.py" -type f -exec sed -i 's/from mahoun\.core\.llm/from mahoun.llm/g' {} \;
find tests -name "*.py" -type f -exec sed -i 's/import mahoun\.core\.llm/import mahoun.llm/g' {} \;

# Step 4: Update imports in examples/
echo "📚 Updating imports in examples/..."
find examples -name "*.py" -type f -exec sed -i 's/from mahoun\.core\.llm/from mahoun.llm/g' {} \;

# Step 5: Update imports in demo/
echo "🎬 Updating imports in demo/..."
find demo -name "*.py" -type f -exec sed -i 's/from mahoun\.core\.llm/from mahoun.llm/g' {} \;

# Step 6: Update root-level demo files
echo "🎯 Updating root demo files..."
sed -i 's/from mahoun\.core\.llm/from mahoun.llm/g' demo_*.py 2>/dev/null || true

# Step 7: Update documentation
echo "📝 Updating documentation..."
find . -name "*.md" -type f -exec sed -i 's/mahoun\.core\.llm/mahoun.llm/g' {} \;
find . -name "*.yaml" -type f -exec sed -i 's/mahoun\.core\.llm/mahoun.llm/g' {} \;
find . -name "*.yml" -type f -exec sed -i 's/mahoun\.core\.llm/mahoun.llm/g' {} \;

echo "✅ Migration complete!"
echo ""
echo "Next steps:"
echo "1. Run tests: pytest tests/ -v"
echo "2. Check imports: python -c 'from mahoun.llm.orchestrator import get_orchestrator'"
echo "3. Verify no references to mahoun.core.llm remain"
```

## Verification Steps

### 1. Check no old imports remain:
```bash
grep -r "from mahoun.core.llm" mahoun/ tests/ examples/ demo/ || echo "✅ No old imports found"
grep -r "import mahoun.core.llm" mahoun/ tests/ examples/ demo/ || echo "✅ No old imports found"
```

### 2. Check new imports work:
```bash
python -c "from mahoun.llm.orchestrator import get_orchestrator, ModelCapability; print('✅ Import successful')"
```

### 3. Run tests:
```bash
pytest tests/test_llm_router_simple.py -v
pytest tests/test_local_llm_driver.py -v
pytest tests/contracts/test_reasoning_protocols_contracts.py -v
```

### 4. Check core is clean:
```bash
ls mahoun/core/llm 2>/dev/null && echo "❌ Old folder still exists" || echo "✅ Old folder removed"
```

## Rollback Plan

اگر مشکلی پیش آمد:
```bash
# Restore from git
git checkout mahoun/core/llm
git checkout mahoun/llm  # remove new location
git checkout mahoun/ tests/ examples/ demo/  # restore old imports
```

## Impact Analysis

### Breaking Changes: بله، اما محدود
- همه imports باید update شوند
- اما API تغییر نمی‌کند، فقط location

### Benefits:
1. ✅ Core تمیزتر می‌شود
2. ✅ Separation of concerns بهتر
3. ✅ LLM به عنوان یک ماژول مستقل
4. ✅ آماده برای future refactoring

### Risks: کم
- همه imports قابل trace هستند
- تست‌ها موجود هستند
- Rollback ساده است

## Timeline

**زمان تخمینی: 30-45 دقیقه**

1. Backup (5 min)
2. Run migration script (5 min)
3. Manual verification (10 min)
4. Run tests (10 min)
5. Fix any issues (10 min)
6. Final verification (5 min)

## Post-Migration Cleanup

بعد از migration موفق:

1. **Update .kiro/steering/structure.md:**
   ```markdown
   ├── mahoun/
   │   ├── llm/                # LLM orchestration and drivers (moved from core)
   │   ├── core/               # Core utilities, settings, health checks
   ```

2. **Add mahoun/llm/README.md:**
   ```markdown
   # Mahoun LLM Module
   
   LLM orchestration and model management.
   
   **Note:** This module was moved from `mahoun/core/llm` to `mahoun/llm`
   to better reflect its role as an infrastructure component.
   ```

3. **Update core_manifest.yaml:**
   - Remove llm from core dependencies
   - Add llm as separate module

## Decision: GO! 🚀

این migration:
- ✅ Safe است (قابل rollback)
- ✅ Beneficial است (بهتر کردن architecture)
- ✅ Testable است (تست‌ها موجود)
- ✅ Documented است (این plan!)

**آماده اجرا هستیم!**
