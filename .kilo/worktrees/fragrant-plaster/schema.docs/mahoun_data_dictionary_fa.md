# MAHOUN Data Dictionary - فرهنگ داده‌های محون
# Persian Legal Verdict Schema - English ↔ Persian

این سند شامل توضیحات دوزبانه (انگلیسی ↔ فارسی) برای تمام فیلدهای schema محون می‌باشد.

This document contains bilingual (English ↔ Persian) documentation for all MAHOUN schema fields.

---

## L2 Schema: VerdictStruct (ساختار آرای قضایی)

### case_meta (اطلاعات پرونده)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `case_meta.court_level` | درجه دادگاه | سطح دادگاه صادرکننده رأی (بدوی، تجدیدنظر، دیوان عالی کشور) | `"دادگاه تجدیدنظر"` |
| `case_meta.procedure_stage` | مرحله رسیدگی | مرحله‌ای از رسیدگی که این رأی در آن صادر شده است | `"تجدیدنظر"` |
| `case_meta.case_type` | نوع دعوا | نوع پرونده یا دعوا (مدنی، کیفری، اعتراض ثالث، و...) | `"اعتراض ثالث اجرایی"` |
| `case_meta.is_final` | قطعیت | آیا این رأی قطعی است یا خیر | `true` / `false` |
| `case_meta.finality_basis` | دلیل قطعیت | دلیل قطعیت رأی (عدم اعتراض، طی مراحل قانونی، و...) | `"عدم اعتراض"` |
| `case_meta.branch_number` | شماره شعبه | شماره شعبه دادگاه صادرکننده | `"10"` |
| `case_meta.city` | شهر | شهر دادگاه | `"تهران"` |
| `case_meta.province` | استان | استان دادگاه | `"تهران"` |
| `case_meta.decision_date` | تاریخ تصمیم | تاریخ صدور رأی (فرمت ISO: YYYY-MM-DD) | `"1403-08-15"` |

---

### parties (اطراف دعوا)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `parties.respondents` | خواندگان/محکوم‌علیه | لیست اطراف خوانده یا محکوم‌علیه در پرونده | `[{title: "آقای", name: "احمد"}]` |
| `parties.third_party_objector` | معترض ثالث | شخص ثالثی که به رأی اعتراض کرده است | `{title: "خانم", name: "سارا"}` |
| `parties[].title` | عنوان | عنوان شخص (آقای، خانم، شرکت، و...) | `"آقای"` |
| `parties[].name` | نام | نام شخص | `"احمد رضایی"` |
| `parties[].father_name` | نام پدر | نام پدر شخص | `"علی"` |

---

### claims (خواسته‌ها)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `claims.main` | خواسته‌های اصلی | لیست خواسته‌های اصلی در دعوا | `["مطالبه وجه چک", "خسارت تأخیر تأدیه"]` |
| `claims.execution_files` | پرونده‌های اجرایی | ارجاع به شماره پرونده‌های اجرایی مرتبط | `["9809980998000123"]` |

---

### first_instance_summary (خلاصه دادگاه بدوی)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `first_instance_summary.court` | دادگاه بدوی | نام دادگاه بدوی که رأی اولیه را صادر کرده | `"دادگاه عمومی حقوقی تهران"` |
| `first_instance_summary.result` | نتیجه | خلاصه نتیجه رأی دادگاه بدوی | `"رد دعوا"` |

---

### appeal_court_reasoning (استدلال دادگاه تجدیدنظر)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `appeal_court_reasoning.extract` | استخراج از متن | بخش استخراج‌شده از استدلال دادگاه تجدیدنظر | `"با توجه به مدارک..."` |
| `appeal_court_reasoning.result` | نتیجه | نتیجه رسیدگی تجدیدنظر | `"نقض رأی بدوی"` |

---

### sections (بخش‌های رأی)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `sections.summary` | گردشکار | بخش گردشکار (تاریخچه رسیدگی و خلاصه ادعاها) | `"خواهان دعوایی..."` |
| `sections.verdict` | رأی دادگاه | بخش رأی دادگاه (استدلال و حکم) | `"با توجه به محتویات پرونده..."` |

---

### legal_references (مراجع قانونی)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `legal_references.substantive_law` | مواد قانون ماهوی | مواد قانونی ماهوی مورد استناد | `["ماده 219 قانون مدنی", "ماده 310 قانون تجارت"]` |
| `legal_references.procedural_law` | مواد قانون شکلی | مواد قانونی آیین دادرسی مورد استناد | `["ماده 84 قانون آیین دادرسی مدنی"]` |
| `legal_references.fiqh_principles` | اصول فقهی | اصول و قواعد فقهی مورد استناد | `["قاعده لاضرر"]` |

---

### final_decision (تصمیم نهایی)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `final_decision.appeal_result` | نتیجه تجدیدنظر | نتیجه نهایی رسیدگی تجدیدنظر | `"نقض رأی بدوی"` |
| `final_decision.third_party_objection` | وضعیت اعتراض ثالث | پذیرش یا رد اعتراض ثالث | `"پذیرفته شده"` / `"رد شده"` |
| `final_decision.is_final` | قطعیت | آیا این رأی قطعی است | `true` / `false` |

---

### system_tags (برچسب‌های سیستمی)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `system_tags` | برچسب‌های سیستمی | برچسب‌های خودکار برای دسته‌بندی | `["تجدیدنظر", "اعتراض_ثالث", "مدنی"]` |

---

### _parsing_quality (کیفیت پردازش)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `_parsing_quality.confidence_score` | امتیاز اطمینان | امتیاز اطمینان استخراج (0.0 تا 1.0) | `0.85` |
| `_parsing_quality.metrics` | معیارهای کیفیت | معیارهای جزئی کیفیت استخراج | `{court_level_found: true}` |

---

### _source (منبع)

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `_source.filename` | نام فایل | نام فایل اصلی | `"verdict_001.txt"` |
| `_source.filepath` | مسیر فایل | مسیر کامل فایل | `"/data/verdicts/verdict_001.txt"` |
| `_source.file_size_bytes` | حجم فایل (بایت) | حجم فایل به بایت | `15234` |

---

## L1 Schema: TextDocument (سند متنی)

### Text Document Fields

| Field Path | Persian Label | Description (Persian) | Example |
|------------|---------------|----------------------|---------|
| `document_id` | شناسه سند | شناسه یکتای سند | `"verdict_2024_001"` |
| `document_type` | نوع سند | نوع سند (رأی، قانون، نظریه مشورتی، و...) | `"verdict"` |
| `title` | عنوان | عنوان یا شماره پرونده | `"پرونده 9809980998000001"` |
| `full_text` | متن کامل | متن کامل سند (خام) | `"رأی دادگاه..."` |
| `clean_text` | متن نرمال‌شده | متن نرمال‌شده و پاک‌شده | `"رای دادگاه..."` |
| `date_issued` | تاریخ صدور | تاریخ صدور رأی (فرمت ISO) | `"1403-08-15"` |
| `court` | مرجع صادرکننده | نام دادگاه یا مرجع صادرکننده | `"دادگاه تجدیدنظر تهران"` |
| `source_file_path` | مسیر فایل منبع | مسیر فایل اصلی سند | `"/data/verdicts/001.txt"` |
| `ingestion_timestamp` | زمان ایجاد | زمان ingestion در سیستم | `"2024-11-30T16:15:00Z"` |

---

## Usage Notes - نکات استفاده

### Persian Text Normalization - نرمال‌سازی متن فارسی

All extracted text undergoes normalization:
- Persian/Arabic digit conversion (۱۲۳ → 123)
- Character variant normalization (ي → ی, ك → ک)
- Typo correction (اقای → آقای)
- Whitespace cleanup

تمام متن‌های استخراج‌شده نرمال‌سازی می‌شوند:
- تبدیل ارقام فارسی/عربی به انگلیسی
- نرمال‌سازی کاراکترهای مختلف
- اصلاح غلط‌های رایج املایی
- پاکسازی فضاهای خالی

### Date Format - فرمت تاریخ

All dates are stored in ISO format (YYYY-MM-DD) for consistency.

تمام تاریخ‌ها در فرمت ISO (YYYY-MM-DD) ذخیره می‌شوند.

### Optional Fields - فیلدهای اختیاری

Most fields are optional (`Optional[...]`) to handle incomplete verdicts gracefully.

اکثر فیلدها اختیاری هستند تا رأی‌های ناقص به درستی پردازش شوند.

---

## Version Information

- Schema Version: L1/L2
- Last Updated: 2024-11-30
- Compatible with: minimal_verdict_parser.py v3+
