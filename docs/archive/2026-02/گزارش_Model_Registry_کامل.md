# گزارش کامل: Model Registry برای Fine-Tuning Pipeline ✅

**تاریخ**: ۱۴۰۳/۱۱/۲۴  
**وضعیت**: آماده تولید  
**پوشش تست**: ۱۴ از ۱۴ تست موفق

---

## خلاصه

یک **Model Registry** حرفه‌ای و سبک‌وزن برای پایپلاین fine-tuning سیستم ماحون پیاده‌سازی شد. این registry با امنیت thread-safe، تمام مدل‌های fine-tuned شده را با metadata کامل، مسیرهای GGUF، معیارها و دسته‌بندی domain ردیابی می‌کند.

---

## چه چیزی ساخته شد؟

### ۱. ماژول اصلی Registry (`mahoun/finetuning/model_registry.py`)

**قابلیت‌ها**:
- ✅ کلاس **ModelMetadata** با فیلدهای جامع
- ✅ کلاس **ModelRegistry** با عملیات thread-safe
- ✅ ذخیره‌سازی JSON (نوشتن atomic)
- ✅ جستجو بر اساس job_id، domain، status، tags
- ✅ پیدا کردن بهترین مدل بر اساس معیار (minimize/maximize)
- ✅ مدیریت مسیرهای GGUF (q4_k_m, q5_k_m, f16)
- ✅ آمار و خروجی خلاصه
- ✅ الگوی Singleton با `get_registry()`

**متدهای کلیدی**:
```python
# ثبت مدل
registry.register(metadata)
registry.update_status(job_id, "completed")
registry.update_metrics(job_id, {"final_loss": 0.23})
registry.add_gguf_path(job_id, "q4_k_m", "./path/to/model.gguf")

# جستجو
model = registry.get_model(job_id)
models = registry.list_models(domain="legal", status="completed")
best = registry.get_best_model(metric="final_loss", domain="legal")

# مدیریت
registry.delete_model(job_id)
stats = registry.get_statistics()
registry.export_summary("./models/summary.md")
```

### ۲. یکپارچه‌سازی با TrainingManager (`mahoun/finetuning/trainer.py`)

**به‌روزرسانی‌ها**:
- ✅ یکپارچه‌سازی ModelRegistry در TrainingManager
- ✅ ثبت خودکار مدل‌ها هنگام شروع آموزش
- ✅ به‌روزرسانی خودکار وضعیت در پایان/خطا
- ✅ ثبت خودکار مسیرهای GGUF export
- ✅ استخراج و ذخیره معیارهای آموزش
- ✅ اضافه شدن پارامترهای `domain` و `tags` به `start_training_job()`
- ✅ متدهای جدید: `list_models()`، `get_best_model()`

**API بهبود یافته**:
```python
# شروع آموزش با domain و tags
job_id = await trainer.start_training_job(
    dataset_path="./datasets/legal_qa",
    base_model_name="unsloth/llama-3-8b-bnb-4bit",
    domain="legal",
    tags=["contracts", "iranian-law"]
)

# جستجوی مدل‌ها
models = trainer.list_models(domain="legal", status="completed")
best = trainer.get_best_model(metric="final_loss", domain="legal")
```

### ۳. تست‌های جامع (`tests/test_model_registry.py`)

**پوشش تست** (۱۴ تست، همه موفق):
- ✅ ثبت مدل
- ✅ به‌روزرسانی وضعیت
- ✅ به‌روزرسانی معیارها
- ✅ مدیریت مسیر GGUF
- ✅ لیست مدل‌ها (بدون فیلتر)
- ✅ لیست مدل‌ها (فیلتر domain)
- ✅ لیست مدل‌ها (فیلتر status)
- ✅ لیست مدل‌ها (فیلتر tags)
- ✅ بهترین مدل (minimize)
- ✅ بهترین مدل (maximize)
- ✅ حذف مدل
- ✅ پایداری (save/load)
- ✅ آمار
- ✅ خروجی خلاصه

### ۴. مثال Demo (`examples/finetuning_demo.py`)

**نمایش**:
- مقداردهی اولیه registry
- نمایش آمار
- جستجوی مدل بر اساس domain
- انتخاب بهترین مدل
- الگوهای استفاده رایج
- خروجی خلاصه

---

## معماری

```
mahoun/finetuning/
├── model_registry.py       # ✅ جدید: پیاده‌سازی اصلی registry
├── trainer.py              # ✅ به‌روز شده: یکپارچه با registry
├── __init__.py             # ✅ به‌روز شده: export کلاس‌های registry
├── unsloth_runner.py       # ✅ موجود: GGUF export (قبلاً انجام شده)
├── config.py               # ✅ موجود: تنظیمات
├── feedback_pipeline.py    # ✅ موجود: Feedback → training data
├── qa_generator.py         # ✅ موجود: تولید Q&A
├── quality_filter.py       # ✅ موجود: فیلتر کیفیت
└── data_augmentation.py    # ✅ موجود: افزایش داده

tests/
└── test_model_registry.py  # ✅ جدید: تست‌های جامع

examples/
└── finetuning_demo.py      # ✅ جدید: نمایش استفاده
```

---

## مدل داده

### ModelMetadata

```python
@dataclass
class ModelMetadata:
    job_id: str                          # شناسه یکتا
    base_model: str                      # نام مدل پایه
    dataset_path: str                    # مسیر dataset آموزش
    output_dir: str                      # دایرکتوری خروجی مدل
    gguf_paths: Dict[str, str]           # Quantization → مسیر GGUF
    metrics: Dict[str, float]            # معیارهای آموزش
    config: Dict[str, Any]               # تنظیمات آموزش
    domain: str = "general"              # دسته‌بندی domain
    created_at: str                      # زمان ISO
    status: str = "training"             # وضعیت
    tags: List[str]                      # برچسب‌های سفارشی
```

### ذخیره‌سازی Registry

**فرمت**: JSON (نوشتن atomic)  
**مکان**: `./models/registry.json` (قابل تنظیم)  
**امنیت Thread**: RLock برای دسترسی همزمان

---

## یکپارچه‌سازی با Pipeline موجود

### قبل (فقط TrainingManager)
```python
trainer = TrainingManager()
job_id = await trainer.start_training_job(dataset_path)
status = trainer.get_job_status(job_id)  # اطلاعات محدود
```

### بعد (با Registry)
```python
trainer = TrainingManager()  # خودکار registry می‌سازد
job_id = await trainer.start_training_job(
    dataset_path,
    domain="legal",
    tags=["contracts"]
)

# جستجوهای پیشرفته
models = trainer.list_models(domain="legal")
best = trainer.get_best_model(metric="final_loss", domain="legal")

# دسترسی مستقیم به registry
registry = get_registry()
model = registry.get_model(job_id)
print(model.gguf_paths)  # همه GGUF exports
print(model.metrics)     # همه معیارها
```

---

## تصمیمات طراحی کلیدی

### ۱. **سبک‌وزن و ساده**
- ذخیره‌سازی JSON (نه دیتابیس) برای سادگی
- بدون وابستگی خارجی (فقط stdlib)
- جستجوی سریع با dict در حافظه

### ۲. **Thread-Safe**
- RLock برای دسترسی همزمان
- نوشتن atomic فایل (temp file + rename)
- امن برای محیط‌های multi-threaded

### ۳. **آگاه از GGUF**
- فیلد اختصاصی `gguf_paths`
- ردیابی چندین سطح quantization
- پر شدن خودکار توسط TrainingManager

### ۴. **مبتنی بر Domain**
- دسته‌بندی domain (legal، medical و غیره)
- فیلتر بر اساس tag
- بهترین مدل برای هر domain

### ۵. **آماده تولید**
- مدیریت خطای جامع
- logging در همه سطوح
- تخریب graceful
- سازگار با نسخه قبلی (job_history قدیمی حفظ شده)

---

## مثال‌های استفاده

### ثبت پایه
```python
from mahoun.finetuning import ModelRegistry, ModelMetadata

registry = ModelRegistry()

metadata = ModelMetadata(
    job_id="job_20250213_120000",
    base_model="unsloth/llama-3-8b-bnb-4bit",
    dataset_path="./datasets/legal_qa",
    output_dir="./models/finetuned/job_20250213_120000",
    gguf_paths={
        "q4_k_m": "./models/.../gguf_q4_k_m/model.gguf",
        "q5_k_m": "./models/.../gguf_q5_k_m/model.gguf",
    },
    metrics={"final_loss": 0.23, "perplexity": 1.26},
    domain="legal",
    tags=["contracts", "iranian-law"]
)

registry.register(metadata)
```

### جستجوی بهترین مدل
```python
# بهترین مدل حقوقی بر اساس loss
best_legal = registry.get_best_model(
    metric="final_loss",
    domain="legal",
    minimize=True
)

print(f"بهترین مدل: {best_legal.job_id}")
print(f"Loss: {best_legal.metrics['final_loss']}")
print(f"GGUF exports: {list(best_legal.gguf_paths.keys())}")
```

---

## نتایج تست

```bash
$ pytest tests/test_model_registry.py -v

tests/test_model_registry.py::test_register_model PASSED
tests/test_model_registry.py::test_update_status PASSED
tests/test_model_registry.py::test_update_metrics PASSED
tests/test_model_registry.py::test_add_gguf_path PASSED
