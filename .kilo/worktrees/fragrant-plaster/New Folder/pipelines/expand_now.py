#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""استخراج سریع 10% داده - پشتیبانی از JSONL, JSON, CSV, XML"""

import json
import random
import csv
import xml.etree.ElementTree as ET
import sys
from pathlib import Path


def load_jsonl(filepath):
    """بارگذاری JSONL"""
    docs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
                docs.append(doc)
            except:
                pass
            if i % 10000 == 0:
                print(f"   پردازش شده: {i} خط, معتبر: {len(docs)}")
    return docs


def load_json(filepath):
    """بارگذاری JSON"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        # اگر لیست باشد، مستقیم برگردان
        if isinstance(data, list):
            return data
        # اگر دیکشنری باشد، ببین آیا کلیدی داره که لیست باشه
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    return value
            # اگر نه، خود دیکشنری رو به عنوان یک سند برگردان
            return [data]
        return []


def load_csv(filepath):
    """بارگذاری CSV"""
    docs = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            docs.append(dict(row))
    return docs


def load_xml(filepath):
    """بارگذاری XML"""
    docs = []
    tree = ET.parse(filepath)
    root = tree.getroot()

    # سعی کن ساختارهای مختلف رو پیدا کنی
    # حالت 1: <root><item>...</item><item>...</item></root>
    for item in root:
        doc = {}
        for child in item:
            doc[child.tag] = child.text or ""
        if doc:
            docs.append(doc)

    # اگر هیچی پیدا نشد، خود root رو به عنوان یک سند برگردان
    if not docs:
        doc = {}
        for child in root:
            doc[child.tag] = child.text or ""
        if doc:
            docs.append(doc)

    return docs


def extract_text(doc):
    """استخراج متن از سند با فیلدهای مختلف"""
    # اگر خود doc یک رشته است
    if isinstance(doc, str):
        # ممکنه JSON string باشه
        if doc.strip().startswith("{"):
            try:
                doc = json.loads(doc)
            except:
                return doc.strip() if len(doc.strip()) > 50 else ""
        else:
            return doc.strip() if len(doc.strip()) > 50 else ""

    # اگر doc دیکشنری نیست
    if not isinstance(doc, dict):
        text = str(doc).strip()
        return text if len(text) > 50 else ""

    # فیلدهای احتمالی برای متن (به ترتیب اولویت)
    text_fields = [
        "متن_کامل",
        "متن",
        "text",
        "content",
        "body",
        "description",
        "توضیحات",
        "محتوا",
        "message",
        "Text",
        "Content",
        "CONTENT",
        "TEXT",  # حالت‌های مختلف
    ]

    # جستجوی فیلد متن
    for field in text_fields:
        if field in doc and doc[field]:
            value = doc[field]

            # اگر مقدار فیلد خودش JSON string باشه
            if isinstance(value, str) and value.strip().startswith("{"):
                try:
                    nested = json.loads(value)
                    if isinstance(nested, dict) and "text" in nested:
                        text = str(nested["text"]).strip()
                        if len(text) > 50:
                            return text
                except:
                    pass

            text = str(value).strip()
            if len(text) > 50:
                return text

    # اگر هیچ فیلد شناخته‌شده‌ای نبود، همه مقادیر رو ترکیب کن
    # ولی فیلدهای id و تاریخ رو نادیده بگیر
    ignore_fields = {
        "id",
        "ID",
        "_id",
        "date",
        "Date",
        "DATE",
        "timestamp",
        "created_at",
        "updated_at",
        "label",
        "multi_task_labels",
    }
    all_text = " ".join(
        str(v) for k, v in doc.items() if v and k not in ignore_fields and not k.startswith("_")
    )
    return all_text.strip() if len(all_text) > 50 else ""


def load_data(filepath):
    """بارگذاری خودکار بر اساس پسوند فایل"""
    path = Path(filepath)
    ext = path.suffix.lower()

    print(f"📄 نوع فایل: {ext}")

    if ext == ".jsonl":
        return load_jsonl(filepath)
    elif ext == ".json":
        return load_json(filepath)
    elif ext == ".csv":
        return load_csv(filepath)
    elif ext == ".xml":
        return load_xml(filepath)
    else:
        print(f"❌ فرمت پشتیبانی نمی‌شود: {ext}")
        print("فرمت‌های پشتیبانی شده: .jsonl, .json, .csv, .xml")
        sys.exit(1)


print("=" * 70)
print("🚀 شروع استخراج 10% داده")
print("=" * 70)

# تنظیمات
if len(sys.argv) > 1:
    SOURCE = sys.argv[1]
else:
    SOURCE = "/home/haji/Desktop/New Folder/12.jsonl"

SAMPLE_SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 4700
SEED = 42
OUTPUT = "DATASET/work/sampled_input.jsonl"  # نام استاندارد برای ورودی labeler

# بارگذاری
print(f"\n📥 بارگذاری: {SOURCE}")
all_docs = load_data(SOURCE)
print(f"✓ {len(all_docs)} سند بارگذاری شد")

# فیلتر کردن اسناد معتبر
print(f"\n🔍 فیلتر کردن اسناد معتبر...")
docs = []
for doc in all_docs:
    text = extract_text(doc)
    if text:
        doc["_extracted_text"] = text
        docs.append(doc)

print(f"✓ {len(docs)} سند معتبر (با متن > 50 کاراکتر)")

# نمونه‌برداری
print(f"\n🎲 نمونه‌برداری {SAMPLE_SIZE} سند (seed={SEED})...")
random.seed(SEED)
sampled = random.sample(docs, min(SAMPLE_SIZE, len(docs)))
print(f"✓ {len(sampled)} سند انتخاب شد")

# آماده‌سازی
print(f"\n🔧 آماده‌سازی...")
prepared = []
for i, doc in enumerate(sampled):
    prepared.append(
        {
            "id": f"batch2_{i:05d}",
            "text": doc.get("_extracted_text", extract_text(doc)),
            "doc_id": f"batch2_{i:05d}",
            "source": "batch2",
            "original_data": doc,  # حفظ داده اصلی
        }
    )

# ذخیره
print(f"\n💾 ذخیره: {OUTPUT}")
Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    for doc in prepared:
        f.write(json.dumps(doc, ensure_ascii=False) + "\n")

print(f"✓ {len(prepared)} سند ذخیره شد")

print(f"\n✅ آماده برای برچسب‌گذاری!")
print(f"\n📋 استفاده:")
print(f"   python3 expand_now.py <input_file> [sample_size]")
print(f"\n   مثال:")
print(f"   python3 expand_now.py data.json 1000")
print(f"   python3 expand_now.py data.csv 5000")
print(f"   python3 expand_now.py data.xml")
print(f"\nبرای برچسب‌گذاری اجرا کنید:")
print(f"   python3 DATASET/ultra_advanced_labeler.py {OUTPUT} DATASET/work/output")
print(f"\nفایل‌های خروجی:")
print(f"  - DATASET/work/output/labeled_ner.jsonl")
print(f"  - DATASET/work/output/labeled_sentences.jsonl")
print("=" * 70)
