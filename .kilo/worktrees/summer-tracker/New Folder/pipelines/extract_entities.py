# ===============================================
#  extract_entities.py
#  نسخه‌ی پیشرفته برای استخراج موجودیت‌ها
# ===============================================

# For Colab: uncomment the line below
# !pip -q install transformers tqdm ftfy accelerate

from pathlib import Path
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from ftfy import fix_text

# استفاده از ماژول جایگزین به جای hazm
# Import Normalizer (fixed import path)
from .persian_legal_nlp import Normalizer

# -------------------------------
# تنظیمات پایه
# -------------------------------
MODEL_NAME = "HooshvareLab/bert-base-parsbert-uncased"  # مدل فارسی NER
DEVICE = 0 if torch.cuda.is_available() else -1  # خودکار GPU/CPU
normalizer = Normalizer()

# -------------------------------
# الگوهای Regex فارسی برای Rule
# -------------------------------
LAW_ARTICLE = re.compile(r"(?:ماده|تبصره)\s+\d+")
PERSON_LIKE = re.compile(r"(?:آقای|خانم)\s+([آ-ی]+)")
JUDGE_LIKE = re.compile(r"قاضی\s+([آ-ی]+)")
ORG_LIKE = re.compile(r"(?:سازمان|وزارت|شرکت|دادگستری|بانک)\s+[آ-ی]+")
CASE_NO = re.compile(r"\b\d{2,4}/\d{1,6}\b")


# -------------------------------
# Rule-based استخراج دستی
# -------------------------------
def extract_rule(text: str):
    def uniq(xs):
        return list(dict.fromkeys([x.strip() for x in xs if x.strip()]))

    return {
        "persons": uniq([m.group(1) for m in PERSON_LIKE.finditer(text)]),
        "judges": uniq([m.group(1) for m in JUDGE_LIKE.finditer(text)]),
        "orgs": uniq([m.group(0) for m in ORG_LIKE.finditer(text)]),
        "articles": uniq([m.group(0) for m in LAW_ARTICLE.finditer(text)]),
        "cases": uniq([m.group(0) for m in CASE_NO.finditer(text)]),
    }


# -------------------------------
# مدل NER (Transformers)
# -------------------------------
print("🔹 Loading NER model... (this may take ~30s)")
tok = AutoTokenizer.from_pretrained(MODEL_NAME)
mdl = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)
ner = pipeline("ner", model=mdl, tokenizer=tok, aggregation_strategy="simple", device=DEVICE)
print("✅ Model loaded.")

LABEL_MAP = {
    "PER": "persons",
    "PERSON": "persons",
    "ORG": "orgs",
    "LAW": "articles",
    "ARTICLE": "articles",
    "JUDGE": "judges",
}


def extract_ner(text: str, max_len=4000):
    out = {"persons": [], "orgs": [], "articles": [], "judges": []}
    for e in ner(text[:max_len]):
        lbl = e.get("entity_group") or e.get("entity") or ""
        lbl = lbl.split("-")[-1]
        key = LABEL_MAP.get(lbl)
        if key:
            out[key].append(e["word"])
    for k, v in out.items():
        out[k] = list(dict.fromkeys([x.strip() for x in v if x.strip()]))
    if not out["articles"]:
        out["articles"] = [m.group(0) for m in LAW_ARTICLE.finditer(text)]
    return out


# -------------------------------
# ادغام Rule و NER (Hybrid)
# -------------------------------
def merge_entities(a, b):
    keys = set(a.keys()) | set(b.keys())
    return {k: sorted(set(a.get(k, []) + b.get(k, []))) for k in keys}


# -------------------------------
# پردازش فولدر ورودی
# -------------------------------
def extract_entities_folder(src_dir, out_file, mode="hybrid"):
    src = Path(src_dir)
    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as w:
        for fp in tqdm(list(src.rglob("*.txt")), desc="Extracting entities"):
            text = fix_text(fp.read_text(encoding="utf-8"))
            text = normalizer.normalize(text)
            rule_ents = extract_rule(text) if mode in ["rule", "hybrid"] else {}
            ner_ents = extract_ner(text) if mode in ["ner", "hybrid"] else {}
            ents = (
                merge_entities(rule_ents, ner_ents) if mode == "hybrid" else (rule_ents or ner_ents)
            )

            rec = {
                "id": str(uuid.uuid4()),
                "source": str(fp),
                "text": text,
                "meta": {"category": "civil", "law_refs": ents.get("articles", [])},
                "entities": ents,
            }
            w.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\n✅ Saved extracted entities to: {out_path}")


# -------------------------------
# اجرای نمونه
# -------------------------------
# مسیر نمونه‌ها (می‌توانی تغییر دهی)
src_dir = "/content/DATASET/cleaned"
out_file = "/content/DATASET/jsonl/records.jsonl"

os.makedirs("/content/DATASET/jsonl", exist_ok=True)

extract_entities_folder(src_dir, out_file, mode="hybrid")
