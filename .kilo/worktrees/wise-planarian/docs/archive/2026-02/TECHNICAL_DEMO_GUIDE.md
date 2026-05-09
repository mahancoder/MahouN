# راهنمای Demo فنی Mahoun
## برای ارائه به مشتریان و سرمایه‌گذاران

### مرحله 1: مشکل را نشان دهید (2 دقیقه)
**چرا AI های موجود برای high-stakes decisions کافی نیستند؟**

- ChatGPT/Claude: هالوسیناسیون دارند، نمی‌توانید به آن‌ها اعتماد کنید
- RAG سنتی: فقط document retrieval است، reasoning ندارد
- سیستم‌های قدیمی: rule-based، انعطاف‌ناپذیر

**نشان دهید:**
```bash
# مثال از یک سیستم معمولی که هالوسیناسیون دارد
# vs Mahoun که هر claim را به evidence لینک می‌کند
```

### مرحله 2: معماری منحصر به فرد (5 دقیقه)

#### 2.1 Evidence-Linked Verdict Engine
**فایل کلیدی:** `mahoun/reasoning/evidence_linked_verdict.py`

```python
# نشان دهید چگونه هر verdict به گراف متصل است
# هیچ claim بدون evidence نیست
```

**تمایز رقابتی:**
- ✅ 100% Groundedness - هر جمله به source متصل است
- ✅ Zero Hallucination - اگر evidence نباشد، جواب نمی‌دهد
- ✅ Explainable - می‌توانید مسیر reasoning را ببینید

#### 2.2 Immutable Ledger
**فایل کلیدی:** `mahoun/ledger/writer.py`

```python
# نشان دهید چگونه هر تصمیم ثبت می‌شود
# و قابل audit است
```

**ارزش برای مشتری:**
- FDA/HIPAA compliance آماده
- کامل audit trail برای regulatory
- تضمین reproducibility

#### 2.3 Ultra Graph Builder
**فایل کلیدی:** `mahoun/graph/ultra_graph_builder.py`

```python
# نشان دهید چگونه از documents یک knowledge graph می‌سازد
# با entity extraction، relation extraction، contradiction detection
```

**قابلیت‌های منحصر به فرد:**
- Automatic contradiction detection
- Multi-hop reasoning روی گراف
- Semantic search + Graph traversal ترکیبی

### مرحله 3: Contract-Based Guarantees (3 دقیقه)

**فایل‌های کلیدی:**
- `mahoun/schemas/contracts/reasoning_contracts.py`
- `mahoun/invariants/ledger_invariants.py`
- `tests/contracts/test_reasoning_contracts.py`

```python
# نشان دهید چگونه invariant ها enforce می‌شوند
# این تضمین‌های سخت‌افزاری است، نه promise
```

**پیام کلیدی:**
"ما نمی‌گوییم سیستم ما خوب است - ما ثابت می‌کنیم با property-based testing"

### مرحله 4: Live Demo (10 دقیقه)

#### سناریو 1: Contract Analysis
```bash
# Upload یک قرارداد
# نشان دهید چگونه:
# 1. Entities extract می‌شود
# 2. Relations شناسایی می‌شود
# 3. Contradictions پیدا می‌شود
# 4. Verdict با evidence link داده می‌شود
```

**فایل‌های مرتبط:**
- `api/routers/ingest.py` - Document upload
- `mahoun/agents/doc_parser_agent.py` - Parsing
- `mahoun/graph/ultra_graph_builder.py` - Graph building
- `mahoun/reasoning/evidence_linked_verdict.py` - Reasoning

#### سناریو 2: Audit Trail
```bash
# نشان دهید چگونه می‌توانید:
# 1. هر تصمیم را trace کنید
# 2. ببینید چه evidence هایی استفاده شده
# 3. تصمیم را reproduce کنید
```

**فایل‌های مرتبط:**
- `mahoun/ledger/storage.py` - Ledger queries
- Frontend dashboard برای visualization

### مرحله 5: Production Readiness (3 دقیقه)

**نشان دهید:**

1. **CI/CD Pipeline:**
```bash
# نشان دهید gate های CI
cat ci/first_step/STAGES.md
```

2. **Monitoring:**
```python
# Prometheus metrics
# Grafana dashboards
# Real-time health checks
```

3. **Multi-Domain Support:**
```bash
# نشان دهید domain های مختلف
ls mahoun/domain/
# aml, legal, healthcare, ...
```

### مرحله 6: Competitive Advantages (2 دقیقه)

**جدول مقایسه:**

| Feature | ChatGPT/Claude | Traditional RAG | Mahoun |
|---------|---------------|-----------------|---------|
| Zero Hallucination | ❌ | ❌ | ✅ |
| Evidence Linking | ❌ | Partial | ✅ Full |
| Audit Trail | ❌ | ❌ | ✅ Immutable |
| Contradiction Detection | ❌ | ❌ | ✅ Automatic |
| Regulatory Compliance | ❌ | ❌ | ✅ Built-in |
| Multi-hop Reasoning | Limited | ❌ | ✅ Graph-based |

### مرحله 7: ROI و Business Value (3 دقیقه)

**Use Cases با ROI مشخص:**

1. **Legal Tech:**
   - کاهش 80% زمان contract review
   - کاهش 95% خطای انسانی
   - کامل audit trail برای litigation

2. **Healthcare:**
   - HIPAA compliance خودکار
   - Drug interaction detection
   - Clinical decision support با evidence

3. **Financial Services:**
   - AML detection با explainability
   - Regulatory compliance automation
   - Fraud detection با audit trail

### فایل‌های کلیدی برای نشان دادن:

#### Core Engine (باید نشان دهید):
1. `mahoun/reasoning/evidence_linked_verdict.py` - قلب سیستم
2. `mahoun/graph/ultra_graph_builder.py` - Graph intelligence
3. `mahoun/ledger/writer.py` - Audit trail
4. `mahoun/schemas/contracts/reasoning_contracts.py` - Guarantees

#### Supporting Infrastructure (اگر وقت داشتید):
5. `mahoun/invariants/ledger_invariants.py` - Enforcement
6. `mahoun/uncertainty/gaussian_process.py` - Confidence scoring
7. `mahoun/reasoning/causal_inference.py` - Advanced reasoning
8. `ci/first_step/gate_7_architecture.sh` - Quality gates

#### Tests (برای اعتماد‌سازی):
9. `tests/contracts/test_reasoning_contracts.py` - Property tests
10. `tests/test_async_ledger_comprehensive.py` - Production quality

### نکات مهم برای Demo:

1. **شروع با مشکل:** همیشه با pain point مشتری شروع کنید
2. **نشان دادن، نه گفتن:** کد واقعی و test های passing را نشان دهید
3. **تمرکز روی تمایز:** چیزی که رقبا ندارند
4. **Business value:** همیشه به ROI برگردید
5. **Social proof:** اگر دارید، case study ها را ذکر کنید

### Script پیشنهادی (30 دقیقه):

```
00:00-02:00  Problem statement
02:00-07:00  Architecture overview
07:00-10:00  Contract guarantees
10:00-20:00  Live demo
20:00-23:00  Production readiness
23:00-25:00  Competitive analysis
25:00-28:00  ROI discussion
28:00-30:00  Q&A
```

### Backup Materials:

- `MAHOUN_ZERO_HALLUCINATION_EXECUTIVE_REPORT.md` - Executive summary
- `MAHOUN_ARCHITECTURE_EXPERT_REVIEW.md` - Technical deep dive
- `گزارش_ماهون_برای_غیرفنی‌ها.md` - برای مدیران غیرفنی
- `DEPLOYMENT_GUIDE.md` - برای سوالات deployment

### Questions متداول:

**Q: چطور از hallucination جلوگیری می‌کنید؟**
A: نشان دهید `evidence_linked_verdict.py` - هر claim به گراف لینک است

**Q: چطور compliance را تضمین می‌کنید؟**
A: نشان دهید `ledger/` - immutable audit trail

**Q: چطور با contradiction ها برخورد می‌کنید؟**
A: نشان دهید `ultra_graph_builder.py` - automatic detection

**Q: Performance چطور است؟**
A: نشان دهید `metrics/` و monitoring dashboards

**Q: چطور scale می‌کند؟**
A: نشان دهید async architecture و concurrent processing
