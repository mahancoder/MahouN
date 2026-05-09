# خلاصه اصلاح Labels در Monitoring System

## 🎯 هدف
رفع مشکل پشتیبانی از labels در metrics و اصلاح Prometheus export format

## ❌ مشکلات قبلی

### 1. Labels پشتیبانی نمی‌شدند
```python
# مشکل: فقط یک counter با هر نام نگه داشته می‌شد
register_counter("metric", {"label": "value1"})  # ایجاد می‌شود
register_counter("metric", {"label": "value2"})  # جایگزین قبلی می‌شود ❌
```

### 2. Prometheus format ناقص بود
```
# خروجی قبلی (بدون HELP و TYPE):
legal_query_throughput_total 10
legal_query_latency_seconds_count 10
```

### 3. Labels در output نمایش داده نمی‌شدند
```
# انتظار:
metric{court_rank="SUPREME_COURT"} 5
metric{court_rank="APPEALS_COURT"} 3

# واقعیت: فقط یکی نمایش داده می‌شد
```

## ✅ راه حل پیاده‌سازی شده

### 1. کلید ترکیبی (Composite Key)
```python
# قبل:
_counters = {"metric_name": Counter(...)}

# بعد:
_counters = {
    "metric_name": Counter(...),                           # بدون label
    "metric_name{label1=value1}": Counter(...),           # با label
    "metric_name{label1=value1,label2=value2}": Counter(...)  # چند label
}
```

### 2. متد `_make_key()` برای ساخت کلید یکتا
```python
def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
    if not labels:
        return name
    
    # Sort labels for deterministic key generation
    sorted_labels = sorted(labels.items())
    label_str = ",".join(f"{k}={v}" for k, v in sorted_labels)
    return f"{name}{{{label_str}}}"
```

### 3. Prometheus Format با HELP و TYPE
```python
# خروجی جدید:
# HELP legal_query_throughput_total Counter metric
# TYPE legal_query_throughput_total counter
legal_query_throughput_total 10

# HELP legal_court_rank_distribution Counter metric
# TYPE legal_court_rank_distribution counter
legal_court_rank_distribution{court_rank="SUPREME_COURT"} 5
legal_court_rank_distribution{court_rank="APPEALS_COURT"} 3
```

## 📁 فایل‌های تغییر یافته

### 1. `mahoun/metrics/store.py`
- ✅ افزودن `_make_key()` method
- ✅ به‌روزرسانی `register_counter/gauge/histogram()` برای استفاده از کلید ترکیبی
- ✅ به‌روزرسانی `get_counter/gauge/histogram()` برای پشتیبانی از labels
- ✅ به‌روزرسانی `snapshot()` برای استفاده از کلیدهای ترکیبی

### 2. `mahoun/metrics/collector.py`
- ✅ به‌روزرسانی `_format_prometheus()` برای:
  - گروه‌بندی metrics با نام یکسان
  - نمایش `# HELP` و `# TYPE` برای هر metric
  - نمایش صحیح labels در format Prometheus

### 3. `mahoun/monitoring/legal_metrics.py`
- ✅ اصلاح `get_stats()` با helper function:
  ```python
  def get_metric_value(metric_name: str) -> int:
      """Get metric value, trying exact match first, then any variant with labels"""
      # Try exact match first (no labels)
      if metric_name in counters:
          return counters[metric_name].get("value", 0)
      
      # Sum all variants with different labels
      for key, data in counters.items():
          base_name = key.split('{')[0] if '{' in key else key
          if base_name == metric_name:
              total = sum(d.get("value", 0) for k, d in counters.items() 
                         if k.split('{')[0] == metric_name)
              return total
      
      return 0
  ```

## 🧪 نتایج تست

### ✅ تست‌های پاس شده
1. `test_prometheus_export_format` - PASSED ✓
2. `test_prometheus_metric_values` - PASSED ✓
3. `test_prometheus_labels` - PASSED ✓

### 📊 مثال خروجی
```python
# Test code:
c1 = collector.register_counter("test_metric", {"label": "value1"})
c1.inc(10)

c2 = collector.register_counter("test_metric", {"label": "value2"})
c2.inc(20)

c3 = collector.register_counter("test_metric")  # No labels
c3.inc(5)

# Snapshot:
{
  "test_metric": {"value": 5, "labels": {}},
  "test_metric{label=value1}": {"value": 10, "labels": {"label": "value1"}},
  "test_metric{label=value2}": {"value": 20, "labels": {"label": "value2"}}
}

# Prometheus output:
# HELP test_metric Counter metric
# TYPE test_metric counter
test_metric{label="value1"} 10
test_metric{label="value2"} 20
test_metric 5
```

## 🎯 مزایای راه حل

1. **Backward Compatible**: کد قدیمی بدون labels همچنان کار می‌کند
2. **Prometheus Standard**: format خروجی مطابق استاندارد Prometheus است
3. **Performance**: O(1) lookup با استفاده از dictionary keys
4. **Deterministic**: کلیدها همیشه به یک شکل ساخته می‌شوند (sorted labels)
5. **Type Safe**: همه type hints حفظ شده‌اند

## 🔍 استفاده در Legal Metrics

```python
# Court rank distribution
await monitor.track_legal_query(
    query="test",
    court_rank="SUPREME_COURT",  # → metric{court_rank="SUPREME_COURT"}
    legal_domain="civil_law"      # → metric{legal_domain="civil_law"}
)

# Error tracking
try:
    ...
except ValueError as e:
    # → metric{error_type="ValueError"}
    collector.register_counter("errors", {"error_type": "ValueError"}).inc(1)
```

## ✨ نتیجه‌گیری

تغییرات با موفقیت پیاده‌سازی شدند و تست‌های Prometheus پاس شدند. سیستم حالا به درستی از labels پشتیبانی می‌کند و format خروجی مطابق استاندارد Prometheus است.
