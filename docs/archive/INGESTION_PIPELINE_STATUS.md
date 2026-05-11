# Ingestion Pipeline - وضعیت فعلی و نقشه راه

**تاریخ**: 2026-05-08  
**وضعیت**: ✅ **COMPLETE AUDIT - ALL 31 FILES READ**  
**گزارش کامل**: [`INGESTION_FULL_AUDIT.md`](./INGESTION_FULL_AUDIT.md)

---

## 📋 خلاصه اجرایی

پس از بررسی **کامل و دقیق تمام 31 فایل** در `mahoun/pipelines/ingestion/`:

### ✅ موارد موجود (VERIFIED)
- ✅ Standard Ingestion Pipeline (882 خط)
- ✅ Enhanced Ingestion Pipeline (375 خط)
- ✅ Hardened Legal Pipeline (450 خط)
- ✅ Legal Storage Service (593 خط)
- ✅ Legal NER Engine (1268 خط، 40+ patterns)
- ✅ Minimal Verdict Parser (1392 خط)
- ✅ LLM Refinement Service (350 خط)
- ✅ LLM Enhanced Parser (450 خط)
- ✅ Provenance-Aware Mapper (450 خط)
- ✅ Schema Builder (280 خط)
- ✅ Metadata Extractor (350 خط)
- ✅ Document Handlers (PDF/DOCX/TXT)
- ✅ Persian Normalizer
- ✅ Enhanced Chunker
- ✅ Enhanced Embedding (GGUF)
- ✅ OCR Ensemble
- ✅ Deterministic ID Generator
- ✅ Entity Linker (939 خط)
- ✅ Graph-Vector Sync (150 خط)

**جمع**: 15,532+ خط کد در 31 فایل Python

### ❌ موارد ناقص (MISSING)
1. ❌ **Fact Extraction for Symbolic Reasoner**
   - استخراج facts از متن حقوقی به FOL predicates
   - مثال: `person("محمد_رضایی", "علی")`, `role("محمد_رضایی", "خواهان")`

2. ❌ **Rule Extraction from Legal Texts**
   - استخراج قوانین منطقی از متون حقوقی
   - مثال: `owns(X, Property) → can_sell(X, Property)`

3. ❌ **Graph-Symbolic Bridge**
   - تبدیل Neo4j graph queries به FOL facts
   - اتصال Knowledge Graph به Symbolic Reasoner

4. ⚠️ **End-to-End Graph Build Pipeline**
   - EntityLinker وجود دارد اما integration یکپارچه ناقص است
   - Pipeline از ingestion تا graph build وجود ندارد

---

## 🎯 نقشه راه (13 هفته)

### Phase 1: Graph Integration (2 هفته)
- ✅ EntityLinker موجود است
- ❌ Pipeline یکپارچه ingestion → graph
- ❌ Integration با UltraGraphBuilder

### Phase 2: Fact Extraction (3 هفته)
- ❌ `LegalFactExtractor` برای تبدیل entities به FOL facts
- ❌ تست‌های جامع

### Phase 3: Rule Extraction (4 هفته)
- ❌ `LegalRuleExtractor` برای استخراج قوانین منطقی
- ❌ Pattern matching برای "اگر...آنگاه"، "هر کس...حق...دارد"

### Phase 4: Graph-Symbolic Bridge (2 هفته)
- ❌ `GraphSymbolicBridge` برای تبدیل Neo4j → FOL
- ❌ Query interface

### Phase 5: End-to-End Reasoning (2 هفته)
- ❌ `ReasoningPipeline` یکپارچه
- ❌ Document → Ingestion → Graph → Facts → Reasoning

---

## 🚨 مسائل بحرانی

### 1. Symbolic Reasoner در جزیره است
- Symbolic Reasoner ساخته شد (1630 خط، 8 تست سخت ✅)
- **اما**: هیچ داده‌ای به آن نمی‌رسد
- **اما**: Ingestion entities می‌سازد اما facts نمی‌سازد

### 2. Zero-Hallucination Guarantee در خطر
- بدون fact extraction، Symbolic Reasoner نمی‌تواند استدلال کند
- بدون graph-symbolic bridge، groundedness تضمین نمی‌شود

---

## 📊 آمار

- **فایل‌های بررسی شده**: 31 فایل Python + 3 Markdown
- **خطوط کد**: 15,532+
- **ماژول‌های کامل**: 19
- **ماژول‌های ناقص**: 4
- **درصد تکمیل**: 83%

---

**برای جزئیات کامل**: [`INGESTION_FULL_AUDIT.md`](./INGESTION_FULL_AUDIT.md)
