# ✅ چک‌لیست عملیاتی فوری MAHOUN (Production Readiness)

## ۱️⃣ اقدامات Critical – مسدودکننده Production

### فعال‌سازی کامل Monitoring و Observability
- [ ] راه‌اندازی کامل ماژول `mahoun/monitoring/`
- [ ] بررسی و فعال کردن SLA Compliance و ML-based anomaly detection
- [ ] اتصال Prometheus/Grafana برای alerting لحظه‌ای

### Phase 4-7 Cleanup – حذف کدهای یتیم و پروتوتایپ
- [ ] شناسایی و حذف Orphaned Code در `mahoun/core/` و فولدرهای موازی
- [ ] اطمینان از اینکه هیچ تابع تکراری (Duplicate Logic) روی مسیر اصلی اجرا نمی‌شود

### Load & Stress Test دیتابیس‌ها
- [ ] اجرای تست Concurrency و Load روی Neo4j و Vector Storeها
- [ ] بررسی نقطه شکست و latency در مقیاس صنعتی
- [ ] مستندسازی Failover و Recovery Strategy

### Circuit Breaker و Retry Logic
- [ ] اطمینان از فعال بودن مکانیزم‌های Fail-Safe روی تمام endpointها و LLM/GAT connectors

### Fallback & Grounding Validation
- [ ] بررسی کامل EvidenceLinkedVerdict برای خروجی‌های غیرقطعی LLM
- [ ] تست مکانیزم‌های fallback روی Hallucination باقیمانده (~۱٪)

---

## ۲️⃣ اقدامات کوتاه‌مدت – امنیت و داده

### Prompt Injection Defense
- [ ] اعمال سخت‌گیرانه Validation و Sanitization روی مدارک و درخواست‌های کاربران
- [ ] پیاده‌سازی لایه‌های دفاعی در زمان Ingestion

### PII Data Masking
- [ ] فعال‌سازی NER-based Masking برای تمام اطلاعات هویتی کاربران و اسناد حقوقی
- [ ] تست عملکرد این لایه برای جلوگیری از Leakage

### Dependency / Supply Chain Verification
- [ ] بررسی تمام packageها و Docker images برای CVEهای شناخته‌شده
- [ ] اطمینان از بروزرسانی منظم و امنیت کانتینرها

---

## ۳️⃣ اقدامات میان‌مدت – پایداری و مقیاس‌پذیری

### High Availability برای دیتابیس‌ها
- [ ] استقرار کلاسترینگ Neo4j و Vector Store
- [ ] پیاده‌سازی مکانیزم‌های Replication و Failover

### Integration Testing
- [ ] سنجش عملکرد پایگاه داده و گراف‌ها در شرایط رقابتی (Race Condition و Concurrency)
- [ ] شبیه‌سازی سناریوهای بار بالا با Hypothesis

### Third-party Pentest
- [ ] ممیزی امنیتی Endpointهای عمومی توسط تیم خارجی
- [ ] بررسی نشت داده و آسیب‌پذیری‌های احتمالی
