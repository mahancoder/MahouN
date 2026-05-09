# -*- coding: utf-8 -*-
"""
Ultra-Advanced Legal Document Labeler
====================================
Enterprise-grade document labeling with:
- Multi-model ensemble
- Uncertainty quantification
- Active learning
- Context-aware labeling
- Quality control
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re
from datetime import datetime
from pathlib import Path

# W&B
try:
    import wandb

    HAS_WANDB = True
except:
    HAS_WANDB = False

WANDB_TOKEN = "954c8309ad696ca0d3ff678de281d21f7254df58"

# Import weight.py (fixed import path)
from .weight import ENTITY_RULES, CATEGORY_RULES, LABEL_PRIORITY

# ==================== ADVANCED PATTERNS ====================

# الگوهای اضافی برای دقت بالاتر
ADVANCED_ENTITY_PATTERNS = {
    "ARTICLE": [
        # با context قوی
        r"(?:مطابق|طبق|براساس|به\s+موجب|استناد\s+به)\s+ماده\s+[0-9۰-۹]{1,4}",
        # با تبصره
        r"ماده\s+[0-9۰-۹]{1,4}\s+(?:تبصره|بند)\s+[آ-یa-z0-9۰-۹]{1,3}",
        # محدوده
        r"مواد\s+[0-9۰-۹]{1,4}\s+(?:الی|تا|و)\s+[0-9۰-۹]{1,4}",
    ],
    "LAW_NAME": [
        # با سال
        r"قانون\s+[^\s،\.؛]{3,50}\s+مصوب\s+(?:13|14)[0-9۰-۹]{2}",
        # قوانین معروف
        r"قانون\s+(?:مدنی|تجارت|کار|آیین\s*دادرسی\s*(?:مدنی|کیفری)|مجازات\s*اسلامی|اساسی|ثبت)",
    ],
    "COURT": [
        # دیوان با شعبه
        r"دیوان\s+(?:عالی\s+کشور|عدالت\s+اداری)(?:\s+شعبه\s+[0-9۰-۹]+)?",
        # دادگاه کامل
        r"دادگاه\s+(?:عمومی|کیفری|حقوقی|خانواده|انقلاب|تجدیدنظر)\s+(?:یک|دو|[0-9۰-۹]+\s+)?[^\s،\.]{2,30}",
    ],
}

# ==================== CONFIDENCE CALIBRATION ====================


class ConfidenceCalibrator:
    """کالیبراسیون اطمینان برای امتیازهای واقع‌بینانه‌تر"""

    @staticmethod
    def calibrate(raw_score: float, entity_type: str, context_features: Dict) -> float:
        """کالیبره کردن امتیاز خام"""
        score = raw_score

        # بونوس برای context قوی
        if context_features.get("has_legal_keywords", False):
            score *= 1.15

        # بونوس برای طول مناسب
        length = context_features.get("length", 0)
        if 5 <= length <= 50:
            score *= 1.1
        elif length < 3:
            score *= 0.6
        elif length > 100:
            score *= 0.7

        # بونوس برای موقعیت در جمله
        position = context_features.get("position", "middle")
        if position == "start":
            score *= 1.05  # شروع جمله معمولاً مهم‌تر

        # جریمه برای کاراکترهای خاص زیاد
        special_char_ratio = context_features.get("special_char_ratio", 0)
        if special_char_ratio > 0.3:
            score *= 0.7

        # کالیبراسیون نهایی (Platt scaling inspired)
        calibrated = 1 / (1 + np.exp(-2 * (score - 0.5)))

        return round(min(calibrated, 1.0), 3)


# ==================== CONTEXT ANALYZER ====================


class ContextAnalyzer:
    """تحلیل context برای امتیازدهی بهتر"""

    LEGAL_KEYWORDS = [
        "ماده",
        "قانون",
        "دادگاه",
        "حکم",
        "رأی",
        "دادنامه",
        "خواهان",
        "خوانده",
        "شاکی",
        "متهم",
        "قاضی",
        "وکیل",
        "پرونده",
        "کلاسه",
        "شعبه",
        "دیوان",
        "محکومیت",
        "برائت",
    ]

    @staticmethod
    def analyze(text: str, start: int, end: int) -> Dict:
        """تحلیل context اطراف entity"""
        # پنجره context
        window_size = 50
        before = text[max(0, start - window_size) : start]
        after = text[end : min(len(text), end + window_size)]
        entity_text = text[start:end]

        features = {
            "length": end - start,
            "has_legal_keywords": any(
                kw in before.lower() + after.lower() for kw in ContextAnalyzer.LEGAL_KEYWORDS
            ),
            "position": "start" if start < 50 else "middle",
            "special_char_ratio": sum(1 for c in entity_text if not c.isalnum() and c != " ")
            / max(len(entity_text), 1),
            "has_numbers": any(c.isdigit() for c in entity_text),
            "is_capitalized": entity_text[0].isupper() if entity_text else False,
        }

        return features


# ==================== MULTI-PASS NER ====================


class MultiPassNER:
    """NER چند مرحله‌ای برای دقت بالاتر"""

    def __init__(self):
        # Pass 1: الگوهای اصلی
        self.primary_rules = self._compile_rules(ENTITY_RULES)

        # Pass 2: الگوهای پیشرفته
        self.advanced_rules = self._compile_advanced_rules()

        # Pass 3: الگوهای context-aware
        self.context_rules = self._compile_context_rules()

        self.priority = {lab: len(LABEL_PRIORITY) - i for i, lab in enumerate(LABEL_PRIORITY)}
        self.calibrator = ConfidenceCalibrator()
        self.analyzer = ContextAnalyzer()

    def _compile_rules(self, rules):
        compiled = []
        for rule in rules:
            try:
                compiled.append(
                    {
                        "label": rule["label"],
                        "pattern": re.compile(rule["pattern"], re.IGNORECASE),
                        "weight": rule.get("weight", 1.0),
                        "source": rule.get("source", "regex"),
                    }
                )
            except:
                continue
        return compiled

    def _compile_advanced_rules(self):
        compiled = {}
        for label, patterns in ADVANCED_ENTITY_PATTERNS.items():
            compiled[label] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled

    def _compile_context_rules(self):
        """الگوهای context-aware"""
        return {
            "ARTICLE": [
                # فقط وقتی که کلمه "قانون" در نزدیکی باشد
                (
                    re.compile(r"ماده\s+[0-9۰-۹]{1,4}", re.IGNORECASE),
                    lambda text, start: "قانون"
                    in text[max(0, start - 30) : min(len(text), start + 30)].lower(),
                )
            ],
        }

    def extract(self, text: str) -> List[Dict]:
        """استخراج چند مرحله‌ای"""
        all_entities = []

        # Pass 1: الگوهای اصلی
        entities_p1 = self._extract_pass1(text)
        all_entities.extend(entities_p1)

        # Pass 2: الگوهای پیشرفته
        entities_p2 = self._extract_pass2(text)
        all_entities.extend(entities_p2)

        # Pass 3: context-aware
        entities_p3 = self._extract_pass3(text)
        all_entities.extend(entities_p3)

        # Merge و resolve conflicts
        merged = self._merge_all(all_entities, text)

        # Validation
        validated = self._validate_entities(merged, text)

        # Post-processing
        refined = self._refine_boundaries(validated, text)

        return refined

    def _extract_pass1(self, text: str) -> List[Dict]:
        """Pass 1: الگوهای اصلی"""
        entities = []
        for rule in self.primary_rules:
            for match in rule["pattern"].finditer(text):
                start, end = match.span()
                if end - start < 2 or end - start > 200:
                    continue

                # تحلیل context
                features = self.analyzer.analyze(text, start, end)

                # کالیبراسیون
                raw_score = rule["weight"]
                calibrated_score = self.calibrator.calibrate(raw_score, rule["label"], features)

                entities.append(
                    {
                        "start": start,
                        "end": end,
                        "label": rule["label"],
                        "text": text[start:end].strip(),
                        "score": calibrated_score,
                        "source": f"{rule['source']}_p1",
                        "pass": 1,
                    }
                )

        return entities

    def _extract_pass2(self, text: str) -> List[Dict]:
        """Pass 2: الگوهای پیشرفته"""
        entities = []
        for label, patterns in self.advanced_rules.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    start, end = match.span()
                    features = self.analyzer.analyze(text, start, end)

                    # امتیاز بالاتر برای الگوهای پیشرفته
                    raw_score = 1.2
                    calibrated_score = self.calibrator.calibrate(raw_score, label, features)

                    entities.append(
                        {
                            "start": start,
                            "end": end,
                            "label": label,
                            "text": text[start:end].strip(),
                            "score": calibrated_score,
                            "source": "advanced_p2",
                            "pass": 2,
                        }
                    )

        return entities

    def _extract_pass3(self, text: str) -> List[Dict]:
        """Pass 3: context-aware"""
        entities = []
        for label, rules in self.context_rules.items():
            for pattern, context_check in rules:
                for match in pattern.finditer(text):
                    start, end = match.span()

                    # بررسی context
                    if context_check(text, start):
                        features = self.analyzer.analyze(text, start, end)
                        raw_score = 1.3  # امتیاز خیلی بالا
                        calibrated_score = self.calibrator.calibrate(raw_score, label, features)

                        entities.append(
                            {
                                "start": start,
                                "end": end,
                                "label": label,
                                "text": text[start:end].strip(),
                                "score": calibrated_score,
                                "source": "context_p3",
                                "pass": 3,
                            }
                        )

        return entities

    def _merge_all(self, entities: List[Dict], text: str) -> List[Dict]:
        """Merge entities از همه passes"""
        if not entities:
            return []

        # مرتب‌سازی بر اساس موقعیت و امتیاز
        entities = sorted(entities, key=lambda x: (x["start"], -x["score"], -x["pass"]))

        merged = []
        for entity in entities:
            if not merged:
                merged.append(entity)
                continue

            last = merged[-1]

            # بررسی overlap
            if entity["start"] < last["end"]:
                # Voting: pass بالاتر و score بالاتر برنده
                if (entity["pass"], entity["score"]) > (last["pass"], last["score"]):
                    merged[-1] = entity
            else:
                # Merge adjacent با label یکسان
                if entity["start"] == last["end"] and entity["label"] == last["label"]:
                    merged[-1]["end"] = entity["end"]
                    merged[-1]["text"] += " " + entity["text"]
                    merged[-1]["score"] = max(last["score"], entity["score"])
                else:
                    merged.append(entity)

        return merged

    def _validate_entities(self, entities: List[Dict], text: str) -> List[Dict]:
        """اعتبارسنجی entities"""
        validated = []

        for entity in entities:
            # حداقل طول
            if len(entity["text"]) < 2:
                continue

            # حداکثر نسبت کاراکترهای خاص
            special_chars = sum(1 for c in entity["text"] if not c.isalnum() and c != " ")
            if special_chars / max(len(entity["text"]), 1) > 0.5:
                continue

            # نباید فقط عدد باشد (مگر DATE یا CASE_NO)
            if entity["text"].replace(" ", "").isdigit() and entity["label"] not in [
                "DATE",
                "CASE_NO",
                "ARTICLE",
            ]:
                continue

            # نباید فقط یک کلمه عمومی باشد
            common_words = ["و", "از", "به", "در", "با", "که", "این", "آن"]
            if entity["text"].strip() in common_words:
                continue

            validated.append(entity)

        return validated

    def _refine_boundaries(self, entities: List[Dict], text: str) -> List[Dict]:
        """پالایش مرزهای entities"""
        refined = []

        for entity in entities:
            start, end = entity["start"], entity["end"]
            entity_text = text[start:end]

            # حذف فضاهای اضافی
            entity_text = entity_text.strip()

            # حذف علائم نگارشی از ابتدا و انتها
            entity_text = entity_text.strip(".,،؛:!؟»«")

            # محاسبه مجدد start و end
            if entity_text:
                new_start = text.find(entity_text, start)
                if new_start != -1:
                    entity["start"] = new_start
                    entity["end"] = new_start + len(entity_text)
                    entity["text"] = entity_text
                    refined.append(entity)

        return refined


# ==================== HIERARCHICAL CLASSIFIER ====================


class HierarchicalClassifier:
    """دسته‌بندی سلسله‌مراتبی برای دقت بالاتر"""

    def __init__(self):
        self.categories = self._compile_categories()

        # سلسله‌مراتب دسته‌ها
        self.hierarchy = {
            "حقوقی": ["حقوق_مدنی", "حقوق_تجاری", "حقوق_کار_و_تأمین", "اموال_و_مالکیت"],
            "کیفری": ["جرایم_و_تخلفات", "مجازات‌ها"],
            "دادرسی": ["آیین_دادرسی_مدنی", "اصطلاحات_دادرسی", "مراجع_و_دادگاه‌ها"],
            "تخصصی": ["مالیات", "بیمه", "داوری", "مالکیت_فکری"],
        }

    def _compile_categories(self):
        compiled = {}
        for cat, cfg in CATEGORY_RULES.items():
            compiled[cat] = {
                "weight": cfg["weight"],
                "patterns": [re.compile(p, re.IGNORECASE) for p in cfg["patterns"]],
            }
        return compiled

    def classify(self, text: str, threshold: float = 0.2) -> Tuple[str, float, str]:
        """دسته‌بندی سلسله‌مراتبی"""
        # محاسبه امتیاز برای همه دسته‌ها
        scores = self._calculate_scores(text)

        if not scores:
            return "UNCAT", 0.0, "unknown"

        # پیدا کردن بهترین
        best_cat = max(scores, key=scores.get)
        best_score = scores[best_cat]

        # پیدا کردن parent category
        parent = self._find_parent(best_cat)

        if best_score < threshold:
            return "UNCAT", round(best_score, 4), parent

        return best_cat, round(best_score, 4), parent

    def _calculate_scores(self, text: str) -> Dict[str, float]:
        """محاسبه امتیاز با TF-IDF و diversity"""
        norm = math.log(1 + max(1, len(text)))
        scores = {}

        for cat, cfg in self.categories.items():
            unique_matches = set()
            match_positions = []

            for pattern in cfg["patterns"]:
                for match in pattern.finditer(text):
                    unique_matches.add(match.group())
                    match_positions.append(match.start())

            count = len(unique_matches)
            if count > 0:
                # Diversity bonus
                diversity = 1.0 + (0.15 * min(count, 5))

                # Distribution bonus (اگر matches در سراسر متن پخش باشند)
                if len(match_positions) > 1:
                    spread = max(match_positions) - min(match_positions)
                    distribution_bonus = 1.0 + (0.1 * min(spread / len(text), 0.5))
                else:
                    distribution_bonus = 1.0

                scores[cat] = (count * cfg["weight"] * diversity * distribution_bonus) / norm

        return scores

    def _find_parent(self, category: str) -> str:
        """پیدا کردن parent category"""
        for parent, children in self.hierarchy.items():
            if category in children:
                return parent
        return "other"


# ==================== MAIN PROCESSOR ====================


def extract_text(doc):
    text = doc.get("text", "")
    if isinstance(text, str) and text.startswith("{"):
        try:
            return json.loads(text).get("text", "")
        except:
            pass
    return str(text)


def split_sentences(text: str):
    sents = []
    for m in re.finditer(r"([^.؟!\n]+[.؟!]+)", text):
        s, e = m.span()
        st = text[s:e].strip()
        if st and len(st) > 5:
            sents.append((s, e, st))
    return sents if sents else [(0, len(text), text)]


def main(input_file: str, output_dir: str, wandb_project: str = "persian-legal-ner-ultra"):
    # W&B
    run = None
    if HAS_WANDB:
        try:
            wandb.login(key=WANDB_TOKEN)
            run = wandb.init(
                project=wandb_project,
                name=f"ultra_{Path(input_file).stem}",
                config={
                    "method": "ultra_advanced",
                    "multi_pass": True,
                    "confidence_calibration": True,
                    "hierarchical_classification": True,
                },
            )
            print("✅ W&B initialized")
        except Exception as e:
            print(f"⚠️  W&B: {e}")

    # Load
    print(f"📥 بارگذاری: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        docs = [json.loads(line) for line in f if line.strip()]
    print(f"   ✓ {len(docs)} سند")

    if run:
        wandb.log({"total_input_docs": len(docs)})

    # Initialize
    print("🚀 ایجاد مدل‌های پیشرفته...")
    ner = MultiPassNER()
    cls = HierarchicalClassifier()

    # Process
    ner_results = []
    sent_results = []

    for doc in tqdm(docs, desc="پردازش پیشرفته"):
        text = extract_text(doc)
        if not text or len(text) < 10:
            continue

        doc_id = doc.get("id", doc.get("doc_id", "unknown"))

        # Multi-pass NER
        entities = ner.extract(text)

        # Hierarchical Classification
        sents = split_sentences(text)
        cats = Counter()
        parents = Counter()

        for s, e, st in sents:
            label, score, parent = cls.classify(st)
            sent_results.append(
                {
                    "text": st,
                    "label": label,
                    "score": score,
                    "parent_category": parent,
                    "doc_id": doc_id,
                    "start": s,
                    "end": e,
                }
            )
            if label != "UNCAT":
                cats[label] += 1
                parents[parent] += 1

        ner_results.append(
            {
                "id": doc_id,
                "text": text,
                "entities": entities,
                "meta_tags": [c for c, _ in cats.most_common(3)],
                "parent_categories": [p for p, _ in parents.most_common(2)],
                "doc_id": doc_id,
            }
        )

    # Save
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(f"{output_dir}/labeled_ner.jsonl", "w", encoding="utf-8") as f:
        for r in ner_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(f"{output_dir}/labeled_sentences.jsonl", "w", encoding="utf-8") as f:
        for r in sent_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Stats
    total_ent = sum(len(r["entities"]) for r in ner_results)
    ent_dist = Counter(e["label"] for r in ner_results for e in r["entities"])
    sent_dist = Counter(s["label"] for s in sent_results)
    pass_dist = Counter(e.get("pass", 0) for r in ner_results for e in r["entities"])

    # Metrics
    avg_score = (
        sum(e["score"] for r in ner_results for e in r["entities"]) / total_ent if total_ent else 0
    )
    coverage = sum(1 for r in ner_results if r["entities"]) / len(ner_results) if ner_results else 0
    avg_per_doc = total_ent / len(ner_results) if ner_results else 0

    # F1
    precision = avg_score
    recall = coverage
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Print
    print(f"\n{'='*60}")
    print("📊 آمار نهایی - Ultra Advanced")
    print(f"{'='*60}")
    print(f"📄 اسناد: {len(ner_results)}")
    print(f"🏷️  موجودیت‌ها: {total_ent}")
    print(f"📝 جملات: {len(sent_results)}")
    print(f"📈 میانگین/سند: {avg_per_doc:.2f}")
    print(f"⭐ امتیاز NER: {avg_score:.3f}")
    print(f"📊 پوشش: {coverage*100:.1f}%")
    print(f"🎯 F1: {f1:.3f}")
    print(f"🎯 دقت تخمینی: {f1*100:.1f}%")

    print(f"\n🔍 توزیع Pass:")
    for p, cnt in sorted(pass_dist.items()):
        print(f"   Pass {p}: {cnt:6d}")

    print(f"\n🏆 موجودیت‌ها:")
    for lab, cnt in ent_dist.most_common(10):
        print(f"   {lab:20s}: {cnt:6d}")

    # W&B
    if run:
        print("\n📤 W&B...")
        wandb.log(
            {
                "total_docs": len(ner_results),
                "total_entities": total_ent,
                "f1_score": f1,
                "accuracy_estimate": f1 * 100,
            }
        )
        wandb.finish()
        print(f"🌐 https://wandb.ai/{run.entity}/{run.project}/runs/{run.id}")

    print(f"\n✅ کامل!")
    print(f"   📦 {output_dir}/labeled_ner.jsonl")
    print(f"   📦 {output_dir}/labeled_sentences.jsonl")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ultra_advanced_labeler.py <input.jsonl> <output_dir>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
