# تحلیل زیرساخت آموزش و فاین‌تیونینگ ماهون
# Mahoun Training Infrastructure Analysis

تاریخ: ۲۲ بهمن ۱۴۰۴ (۱۱ فوریه ۲۰۲۶)

## 🎯 خلاصه اجرایی / Executive Summary

سیستم ماهون دارای **زیرساخت کامل آموزش** است، اما **اتصال بین اسناد و آموزش** وجود ندارد.

**وضعیت فعلی:**
- ✅ Document Ingestion Pipeline (PDF, DOCX, TXT) - کامل
- ✅ Feedback to Training Pipeline - کامل و تست شده
- ✅ Advanced Training Infrastructure (LoRA, QLoRA, DoRA, AdaLoRA) - کامل
- ✅ Q&A Generator - کامل
- ❌ **Document → Training Dataset Connector - وجود ندارد**

---

## 📊 نقشه معماری فعلی / Current Architecture Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAHOUN TRAINING ECOSYSTEM                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  Document Upload │         │  User Feedback   │
│  (PDF/DOCX/TXT)  │         │   (Ratings/      │
│                  │         │   Corrections)   │
└────────┬─────────┘         └────────┬─────────┘
         │                            │
         │                            │
         ▼                            ▼
┌─────────────────────┐    ┌──────────────────────┐
│ Ingestion Pipeline  │    │ Feedback Pipeline    │
│ ─────────────────── │    │ ──────────────────── │
│ • Document Handlers │    │ • Quality Scoring    │
│ • OCR Processing    │    │ • Example Conversion │
│ • NER Extraction    │    │ • Dataset Creation   │
│ • Chunking          │    │                      │
│ • Embedding         │    │ ✅ FULLY CONNECTED   │
└────────┬────────────┘    └──────────┬───────────┘
         │                            │
         │                            │
         ▼                            ▼
┌─────────────────────┐    ┌──────────────────────┐
│   Vector Store      │    │  Training Dataset    │
│   (RAG Only)        │    │  (JSONL/JSON)        │
│                     │    │                      │
│ ❌ NOT CONNECTED    │    │ ✅ READY FOR TRAIN   │
│    TO TRAINING      │    │                      │
└─────────────────────┘    └──────────┬───────────┘
                                      │
         ┌────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│         Training Infrastructure              │
│         ─────────────────────────            │
│  • UltraAdvancedTrainer (LoRA/QLoRA/DoRA)   │
│  • UnslothRunner (Fast Training)            │
│  • Quantization (INT4/INT8/GPTQ/AWQ)        │
│  • Distributed Training (DDP/FSDP/DeepSpeed)│
│  • Gradient Checkpointing                   │
│  • Mixed Precision (FP16/BF16)              │
│                                              │
│  ✅ FULLY IMPLEMENTED                        │
└──────────────────────────────────────────────┘
```

---

## 🔍 تحلیل عمیق اجزا / Deep Component Analysis

### 1️⃣ Document Ingestion Pipeline
**مسیر:** `mahoun/pipelines/ingestion/`

**قابلیت‌ها:**
- ✅ PDF/DOCX/TXT parsing
- ✅ OCR for scanned documents
- ✅ Persian text normalization
- ✅ Legal NER (Named Entity Recognition)
- ✅ Enhanced chunking (semantic boundaries)
- ✅ Embedding generation
- ✅ Vector store integration

**خروجی:**
- Chunks → Vector Store (برای RAG)
- Metadata → Graph Database (اختیاری)

**مشکل:**
❌ هیچ مسیری برای تبدیل اسناد به دیتاست آموزشی وجود ندارد

---

### 2️⃣ Q&A Generator
**مسیر:** `mahoun/finetuning/qa_generator.py`

**قابلیت‌ها:**
- ✅ LLM-based Q&A generation
- ✅ Template-based extraction
- ✅ Extractive Q&A (از ساختار متن)
- ✅ Hybrid approach
- ✅ Quality validation
- ✅ Deduplication
- ✅ Persian/English support

**استراتژی‌های تولید:**
1. **LLM-Based:** استفاده از LLM برای تولید سوال/جواب
2. **Template-Based:** استخراج با الگوهای از پیش تعریف شده
3. **Extractive:** استخراج از ساختار متن (مثل "X: Y")
4. **Hybrid:** ترکیب همه روش‌ها

**وضعیت:**
✅ کامل اما **استفاده نمی‌شود** - هیچ کجا فراخوانی نشده

---

### 3️⃣ Feedback Pipeline
**مسیر:** `mahoun/finetuning/feedback_pipeline.py`

**قابلیت‌ها:**
- ✅ Feedback collection (Rating, Correction, Preference)
- ✅ Quality scoring (با فرمول پیچیده)
- ✅ Training example conversion
- ✅ Dataset creation with splits (train/eval/test)
- ✅ Multiple formats (JSONL, JSON)
- ✅ Persistence to disk

**Quality Scoring Formula:**
```python
score = 0.0
score += (rating / 5.0) * 0.4        # Rating component (0-0.4)
score += response_time_bonus * 0.2   # Response time (0-0.2)
score += confidence_score * 0.2      # Confidence (0-0.2)
score += feedback_type_bonus * 0.2   # Type bonus (0-0.2)

# Special case: Corrections = 0.95 (gold data)
```

**وضعیت:**
✅ کامل و تست شده - **به API متصل است**

---

### 4️⃣ Training Infrastructure

#### A) UltraAdvancedTrainer
**مسیر:** `mahoun/rag/training/trainer.py`

**قابلیت‌ها:**
- ✅ Full fine-tuning
- ✅ LoRA (Low-Rank Adaptation)
- ✅ QLoRA (Quantized LoRA)
- ✅ DoRA (Weight-Decomposed LoRA)
- ✅ AdaLoRA (Adaptive LoRA)
- ✅ Quantization: INT4, INT8, GPTQ, AWQ
- ✅ Distributed: DDP, FSDP, DeepSpeed
- ✅ Gradient checkpointing
- ✅ Mixed precision (FP16/BF16/FP8)
- ✅ Learning rate scheduling
- ✅ Experiment tracking (WandB, TensorBoard)

**پیکربندی:**
```python
TrainingConfig(
    model_name_or_path="meta-llama/Llama-2-7b",
    training_mode=TrainingMode.QLORA,
    quantization=QuantizationConfig(load_in_4bit=True),
    lora_config=LoRAConfig(r=8, lora_alpha=16),
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    bf16=True,
    gradient_checkpointing=True
)
```

#### B) UnslothRunner
**مسیر:** `mahoun/finetuning/unsloth_runner.py`

**قابلیت‌ها:**
- ✅ Fast training with Unsloth
- ✅ 2x faster than standard training
- ✅ Lower memory usage
- ✅ Compatible with Hugging Face models

**وضعیت:**
✅ کامل - **از TrainingManager فراخوانی می‌شود**

---

### 5️⃣ Training Manager
**مسیر:** `mahoun/finetuning/trainer.py`

**قابلیت‌ها:**
- ✅ Dataset preparation from feedback
- ✅ Data augmentation integration
- ✅ Training job management
- ✅ Job history tracking
- ✅ Fallback to mock training (اگر Unsloth نصب نباشد)

**وضعیت:**
✅ کامل و به API متصل

---

## ❌ شکاف اصلی / Main Gap

### مسیر موجود (Feedback → Training):
```
User Feedback → FeedbackPipeline → TrainingDataset → Trainer ✅
```

### مسیر ناقص (Document → Training):
```
Document Upload → Ingestion → ??? → TrainingDataset → Trainer ❌
                              ↑
                         MISSING LINK
```

---

## 🔧 راه‌حل پیشنهادی / Proposed Solution

### گزینه ۱: اتصال سریع (Quick Connect)
**زمان:** 2-3 ساعت

ایجاد `DocumentToTrainingConnector` که:
1. از Ingestion Pipeline چانک‌ها را دریافت کند
2. از QAGenerator سوال/جواب تولید کند
3. به FeedbackPipeline یا مستقیم به Trainer بدهد

**فایل جدید:**
```python
# mahoun/finetuning/document_to_training.py

class DocumentToTrainingConnector:
    def __init__(self):
        self.qa_generator = QAGenerator()
        self.feedback_pipeline = FeedbackPipeline()
    
    async def process_document(self, doc_id: str, text: str):
        # 1. Generate Q&A pairs
        qa_pairs = await self.qa_generator.generate(text, doc_id)
        
        # 2. Convert to training examples
        examples = self._qa_to_examples(qa_pairs)
        
        # 3. Create dataset
        dataset = self.feedback_pipeline.create_dataset(
            examples, f"doc_{doc_id}_dataset"
        )
        
        return dataset
```

**API Endpoint:**
```python
# api/routers/finetuning.py

@router.post("/datasets/from-document")
async def create_dataset_from_document(
    file: UploadFile,
    dataset_name: str
):
    # Process document → Generate Q&A → Create dataset
    pass
```

---

### گزینه ۲: سیستم کامل (Complete System)
**زمان:** 1-2 روز

ایجاد یک پایپلاین جامع با:
1. Document upload با UI
2. Q&A generation با پیش‌نمایش
3. Human-in-the-loop validation
4. Automatic dataset creation
5. One-click training trigger

**اجزا:**
- Backend: `DocumentTrainingPipeline` class
- Frontend: Document upload + Q&A review UI
- API: Complete REST endpoints
- Tests: Integration tests

---

## 📁 فایل‌های کلیدی موجود / Existing Key Files

### Document Processing:
```
mahoun/pipelines/ingestion/
├── enhanced_pipeline.py          # Main ingestion pipeline
├── document_handlers.py          # PDF/DOCX/TXT handlers
├── ocr_handler.py                # OCR for scanned docs
├── enhanced_ner.py               # Named entity recognition
├── enhanced_chunker.py           # Semantic chunking
└── enhanced_embedding.py         # Embedding generation
```

### Training System:
```
mahoun/finetuning/
├── qa_generator.py               # Q&A generation ✅
├── feedback_pipeline.py          # Feedback → Training ✅
├── trainer.py                    # Training manager ✅
├── unsloth_runner.py             # Fast training ✅
├── data_augmentation.py          # Data augmentation ✅
└── quality_filter.py             # Quality filtering ✅

mahoun/rag/training/
├── trainer.py                    # UltraAdvancedTrainer ✅
└── config.py                     # Training configs ✅
```

### API:
```
api/routers/
├── finetuning.py                 # Fine-tuning API ✅
└── ingest.py                     # Document ingestion API ✅
```

---

## 🎯 توصیه / Recommendation

با توجه به اینکه:
1. ✅ همه اجزا موجود هستند
2. ✅ QAGenerator کامل است اما استفاده نمی‌شود
3. ✅ FeedbackPipeline تست شده و کار می‌کند
4. ❌ فقط یک connector ساده لازم است

**توصیه من:**

### 🚀 گزینه ۱ را انتخاب کنید (اتصال سریع)

**دلایل:**
- سریع (2-3 ساعت)
- استفاده از کدهای موجود
- بدون تغییر معماری
- قابل تست فوری
- می‌توان بعداً به گزینه ۲ ارتقا داد

**مراحل:**
1. ایجاد `mahoun/finetuning/document_to_training.py`
2. اتصال به `api/routers/finetuning.py`
3. تست با یک فایل نمونه
4. مستندسازی

---

## 📝 تسک فعلی در ادیتور / Current Editor Task

**تسک:** Documentation Quality Improvements
**وضعیت:** در حال انجام
**فایل:** `.kiro/specs/documentation-quality-improvements/tasks.md`

**این تسک شامل:**
- بهبود مستندات API
- اضافه کردن docstrings
- ایجاد راهنماهای استفاده
- بهبود کامنت‌ها

---

## 🤔 تصمیم‌گیری / Decision Point

### سوال شما:
> "نمی‌دونم این تسک که توی ادیتور هست رو ادامه بدم یا مسیر آموزش مدل‌های سیستم رو مدون‌ترش کنم"

### پاسخ من:

**اولویت ۱: مسیر آموزش را کامل کنید** 🎯

**دلایل:**
1. **تاثیر بیشتر:** اتصال Document → Training یک قابلیت کلیدی است
2. **سریع:** فقط 2-3 ساعت زمان می‌برد
3. **ارزش بالا:** به کاربران اجازه می‌دهد با آپلود فایل، مدل را آموزش دهند
4. **تکمیل معماری:** شکاف اصلی را پر می‌کند

**بعد از آن:**
- Documentation Quality را ادامه دهید
- یا به سراغ تسک‌های دیگر بروید

---

## 🎬 مراحل پیشنهادی / Suggested Steps

### مرحله ۱: ایجاد Connector (۱ ساعت)
```bash
# Create the connector file
touch mahoun/finetuning/document_to_training.py
```

### مرحله ۲: اتصال به API (۳۰ دقیقه)
```bash
# Update API router
# api/routers/finetuning.py
```

### مرحله ۳: تست (۳۰ دقیقه)
```bash
# Create test file
touch tests/test_document_to_training.py

# Run tests
pytest tests/test_document_to_training.py -v
```

### مرحله ۴: مستندسازی (۳۰ دقیقه)
```bash
# Update documentation
# docs/TRAINING_GUIDE.md
```

---

## 📊 مقایسه گزینه‌ها / Options Comparison

| معیار | ادامه Documentation | کامل کردن Training Path |
|-------|---------------------|-------------------------|
| زمان | 4-6 ساعت | 2-3 ساعت |
| تاثیر | متوسط | بالا |
| اولویت | پایین | بالا |
| پیچیدگی | متوسط | پایین |
| ارزش کاربر | متوسط | بالا |
| تکمیل معماری | خیر | بله |

---

## ✅ نتیجه‌گیری / Conclusion

**توصیه نهایی:**
1. ✅ **الان:** کامل کردن Document → Training connector (2-3 ساعت)
2. ⏭️ **بعد:** ادامه Documentation Quality
3. 🎯 **هدف:** یک سیستم کامل با قابلیت آموزش از فایل

**آیا می‌خواهید شروع کنیم؟** 🚀
