# Core Reality Check
## واقعیت وضعیت هسته Mahoun

**تاریخ**: ۱۴۰۴/۱۱/۲۹  
**وضعیت**: ⚠️ هسته هنوز آلوده است

---

## 🔍 کشف واقعیت

### تصور اولیه (اشتباه)
- ✅ هسته در ۹ فوریه پاکسازی شد
- ✅ Gate 7 از آلودگی جلوگیری می‌کند
- ✅ معماری تمیز است

### واقعیت (بعد از بررسی Git History)
- ❌ هسته **هرگز** پاکسازی نشده
- ⚠️ Gate 7 فقط از **import های جدید** جلوگیری می‌کند
- ⚠️ فایل‌های Infrastructure از **اولین کامیت** (۳۰ دسامبر ۲۰۲۵) در `core/` هستند
- ✅ Gate 7 در ۹ فوریه فقط import violations را برطرف کرد، نه file structure را

---

## 📊 محتویات فعلی `mahoun/core/`

### ✅ فایل‌های صحیح (Domain Logic)
```
core/
├── models.py           ✅ Domain models
├── protocols.py        ✅ Interfaces
├── exceptions.py       ✅ Domain exceptions
├── validation.py       ✅ Domain validation
├── config.py           ✅ Configuration
├── settings.py         ✅ Settings
├── paths.py            ✅ Path utilities
├── secrets.py          ✅ Secrets management
├── serialization.py    ✅ Serialization
├── singleton.py        ✅ Singleton pattern
├── error_handling.py   ✅ Error handling
├── runtime_config.py   ✅ Runtime config
└── logging.py          ✅ Core logging
```

### ❌ فایل‌های نادرست (Infrastructure)
```
core/
├── health_cache.py     ❌ Infrastructure (monitoring)
├── health_checker.py   ❌ Infrastructure (monitoring)
├── graph/              ❌ باید در mahoun/graph/ باشد
├── ingest/             ❌ Infrastructure (pipelines)
├── llm/                ❌ Infrastructure
├── metrics/            ❌ Infrastructure (observability)
├── monitoring/         ❌ Infrastructure (observability)
└── rag/                ❌ Infrastructure
```

---

## 🎯 تحلیل Gate 7

### چه کاری انجام می‌دهد
Gate 7 بررسی می‌کند که:
- ماژول‌های هسته از ماژول‌های غیر-هسته **import نکنند**
- مثال: `mahoun/reasoning/` نمی‌تواند از `mahoun/agents/` import کند

### چه کاری انجام نمی‌دهد
Gate 7 بررسی **نمی‌کند** که:
- ❌ چه فایل‌هایی داخل `core/` هستند
- ❌ آیا فایل‌های Infrastructure در `core/` هستند
- ❌ آیا ساختار دایرکتوری صحیح است

---

## 💡 کشف مهم

**Gate 7 = Import Checker, NOT File Structure Checker**

```python
# این را تشخیص می‌دهد ✅
# mahoun/reasoning/engine.py
from mahoun.agents import DocParserAgent  # ❌ VIOLATION!

# این را تشخیص نمی‌دهد ❌
# mahoun/core/health_checker.py exists  # Should be in monitoring/
```

---

## 📈 نمره واقعی Core Independence

### محاسبه دقیق

```python
total_files_in_core = 21  # تعداد کل فایل‌ها
domain_files = 13         # فایل‌های domain
infrastructure_files = 8  # فایل‌های infrastructure

core_independence_score = (domain_files / total_files_in_core) * 100
# = (13 / 21) * 100
# = 61.9%
```

**نمره واقعی**: **۶۲/۱۰۰** ⚠️

**نمره قبلی (اشتباه)**: ۱۲/۱۰۰  
**نمره هدف**: ۹۰/۱۰۰

---

## 🔄 چرا Phase 0-3 هنوز لازم است

### دلیل ۱: فایل‌های Infrastructure در Core
```
❌ core/health_cache.py
❌ core/health_checker.py
❌ core/metrics/
❌ core/monitoring/
❌ core/llm/
❌ core/rag/
❌ core/ingest/
❌ core/graph/  (duplicate!)
```

### دلیل ۲: Gate 7 کافی نیست
- Gate 7: جلوگیری از import های جدید
- Phase 0-3: پاکسازی فایل‌های موجود

### دلیل ۳: معماری ناقص
```
فعلی:
mahoun/
├── core/
│   ├── health_checker.py  ❌ Wrong place
│   ├── metrics/           ❌ Wrong place
│   └── monitoring/        ❌ Wrong place

هدف:
mahoun/
├── core/                  ✅ Pure domain
├── infrastructure/
│   ├── monitoring/
│   │   ├── health_checker.py  ✅ Right place
│   │   └── health_cache.py    ✅ Right place
│   └── observability/
│       ├── metrics/       ✅ Right place
│       └── monitoring/    ✅ Right place
```

---

## 🎯 راه حل

### مرحله ۱: به‌روزرسانی Gate 7

اضافه کردن بررسی ساختار فایل:

```python
# scripts/check_boundaries.py

def check_core_structure():
    """Check that core/ only contains domain files."""
    
    forbidden_in_core = [
        "health_cache.py",
        "health_checker.py",
        "metrics/",
        "monitoring/",
        "llm/",
        "rag/",
        "ingest/",
        "graph/",  # Should be in mahoun/graph/
    ]
    
    violations = []
    for item in forbidden_in_core:
        path = Path(f"mahoun/core/{item}")
        if path.exists():
            violations.append(f"Infrastructure file in core: {item}")
    
    return violations
```

### مرحله ۲: اجرای Phase 0-3

```bash
# Phase 1: Create infrastructure/
python scripts/execute_phase.py 1

# Phase 2: Copy files
python scripts/execute_phase.py 2

# Phase 3: Add deprecations
python scripts/execute_phase.py 3
```

### مرحله ۳: Phase 7 (بعد از migration period)

```bash
# Remove old files from core/
python scripts/execute_phase.py 7
```

---

## 📊 پیشرفت واقعی

### قبل از Architecture Hardening (قبل از ۹ فوریه)
- Import violations: ۳۲
- File structure: آلوده
- Core independence: ~۱۰/۱۰۰

### بعد از Architecture Hardening (۹ فوریه)
- Import violations: ✅ ۰
- File structure: ⚠️ هنوز آلوده
- Core independence: ~۶۲/۱۰۰

### بعد از Phase 0-3 (هدف)
- Import violations: ✅ ۰
- File structure: ✅ تمیز
- Core independence: ✅ ۹۰+/۱۰۰

---

## 🎉 دستاوردهای واقعی تاکنون

### ✅ انجام شده
1. **Gate 7 فعال**: جلوگیری از import violations
2. **Zero import violations**: هیچ ماژول هسته از غیر-هسته import نمی‌کند
3. **Protocol-based DI**: وابستگی‌ها از طریق Protocol
4. **CI enforcement**: خودکار و قابل اعتماد

### ⏳ در حال انجام
1. **File structure cleanup**: انتقال Infrastructure از core/
2. **Phase 0-3 automation**: اسکریپت‌های آماده
3. **Documentation**: مستندات کامل

### 🎯 باقی‌مانده
1. **Execute Phase 1-3**: ایجاد infrastructure/ و انتقال فایل‌ها
2. **Migration period**: ۲ هفته برای deprecation
3. **Execute Phase 7**: حذف فایل‌های قدیمی
4. **Final validation**: تست و اعتبارسنجی نهایی

---

## 💡 نتیجه‌گیری

### واقعیت
- ✅ Gate 7 کار می‌کند (import violations = 0)
- ⚠️ هسته هنوز آلوده است (file structure)
- ✅ Phase 0-3 هنوز لازم است

### اقدام بعدی
1. **الان**: کامیت اسکریپت‌ها و مستندات
2. **بعد**: اجرای Phase 1-3
3. **نهایی**: Phase 7 و پاکسازی کامل

---

**تاریخ**: ۱۴۰۴/۱۱/۲۹  
**وضعیت**: ⚠️ نیمه‌راه - Import ها تمیز، فایل‌ها آلوده  
**نمره واقعی**: ۶۲/۱۰۰ (نه ۱۲/۱۰۰)
