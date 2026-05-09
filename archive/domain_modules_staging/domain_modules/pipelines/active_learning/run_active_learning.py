#!/usr/bin/env python3
"""
Advanced Active Learning Orchestration
=====================================

این اسکریپت، حلقه‌ی یادگیری فعال را برای داده‌های حقوقی MAHOUN پیاده‌سازی
می‌کند و نسبت به نسخه‌ی ساده، قابلیت‌های پیشرفته‌تری دارد:

1. پشتیبانی از انکودرهای مختلف ویژگی (آمار ساده یا SentenceTransformer).
2. استفاده از شبکه‌ی عصبی با Dropout برای تخمین عدم قطعیت (BALD/Entropy/QBC).
3. ثبت دقیق متریک‌ها (JSON و W&B در صورت موجود بودن کتابخانه).
4. شبیه‌سازی فرآیند annotation و ذخیره‌ی نمونه‌های انتخاب‌شده برای برچسب‌گذاری.
5. رابط برنامه‌نویسی برای ادغام با orchestrator یا cronjob (تابع `run_pipeline`).

اجرای نمونه:
    python pipelines/active_learning/run_active_learning.py \
        --label-name LAWYER \
        --rounds 5 \
        --encoder sbert \
        --save-history outputs/active_learning/history.json
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "PyTorch is required for the active learning pipeline. "
        "Install it with `pip install torch` و سپس اسکریپت را اجرا کنید."
    ) from exc

try:
    from sentence_transformers import SentenceTransformer

    _HAS_SENTENCE_TRANSFORMERS = True
except Exception:  # pragma: no cover - optional dependency
    _HAS_SENTENCE_TRANSFORMERS = False

try:  # pragma: no cover - optional dependency
    import wandb

    _HAS_WANDB = True
except Exception:
    _HAS_WANDB = False

from self_improve.active_learning import ActiveLearner


# ---------------------------------------------------------------------------
# Feature encoders
# ---------------------------------------------------------------------------


class FeatureEncoder:
    """Interface for converting raw texts into feature vectors."""

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        raise NotImplementedError


class SimpleStatsEncoder(FeatureEncoder):
    """Baseline encoder using lightweight statistical features."""

    LEGAL_KEYWORDS = [
        "ماده",
        "قانون",
        "دادگاه",
        "دادنامه",
        "دیوان",
        "شعبه",
        "حکم",
        "محکومیت",
        "وکیل",
        "شاکی",
        "متهم",
        "خواهان",
        "خوانده",
        "تجدیدنظر",
    ]

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        feats: List[np.ndarray] = []

        for text in texts:
            text = text or ""
            text_lower = text.lower()
            length = len(text)
            num_words = max(len(text_lower.split()), 1)
            num_sentences = (
                text.count(".") + text.count("؟") + text.count("!") + text.count("؛")
            )
            digits_ratio = sum(c.isdigit() for c in text) / max(length, 1)
            upper_ratio = sum(c.isupper() for c in text) / max(length, 1)
            avg_word_len = sum(len(w) for w in text_lower.split()) / num_words
            unique_ratio = len(set(text_lower.split())) / num_words
            keyword_hits = sum(
                1 for kw in self.LEGAL_KEYWORDS if kw in text_lower
            ) / len(self.LEGAL_KEYWORDS)
            punctuation_ratio = sum(c in ",؛؛؛:،" for c in text) / max(length, 1)

            vector = np.array(
                [
                    min(length / 4000.0, 1.0),
                    min(num_words / 1500.0, 1.0),
                    digits_ratio,
                    upper_ratio,
                    min(avg_word_len / 20.0, 1.0),
                    unique_ratio,
                    keyword_hits,
                    min(num_sentences / 40.0, 1.0),
                    punctuation_ratio,
                ],
                dtype=np.float32,
            )
            feats.append(vector)

        return np.vstack(feats)


class SentenceTransformerEncoder(FeatureEncoder):
    """Embedding encoder using SentenceTransformer models."""

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        if not _HAS_SENTENCE_TRANSFORMERS:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Install it via `pip install sentence-transformers` یا از انکودر simple استفاده کنید."
            )
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Sequence[str]) -> np.ndarray:  # pragma: no cover - heavy
        embeddings = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return embeddings.astype(np.float32)


def build_encoder(name: str, model_name: Optional[str]) -> FeatureEncoder:
    if name == "simple":
        return SimpleStatsEncoder()
    if name == "sbert":
        return SentenceTransformerEncoder(model_name=model_name or "")
    raise ValueError(f"Unknown encoder: {name}")


# ---------------------------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------------------------


@dataclass
class Example:
    text: str
    label: int
    meta: Dict[str, object]


def load_labeled_examples(path: Path, label_name: str) -> List[Example]:
    """Read labeled data and convert to binary classification examples."""
    examples: List[Example] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            text = record.get("text")
            if not isinstance(text, str):
                continue

            entities = record.get("entities") or []
            label = int(any(ent.get("label") == label_name for ent in entities))

            examples.append(
                Example(
                    text=text,
                    label=label,
                    meta={
                        "line_no": line_no,
                        "doc_id": record.get("doc_id"),
                    },
                )
            )

    if not examples:
        raise ValueError(f"No usable examples found in {path}")

    return examples


def collate_features(
    encoder: FeatureEncoder,
    examples: Sequence[Example],
) -> Tuple[torch.Tensor, torch.Tensor]:
    features = encoder.encode([ex.text for ex in examples])
    labels = np.array([ex.label for ex in examples], dtype=np.int64)
    return torch.tensor(features, dtype=torch.float32), torch.tensor(labels, dtype=torch.long)


# ---------------------------------------------------------------------------
# PyTorch datasets / model
# ---------------------------------------------------------------------------


class FeatureDataset(Dataset):
    def __init__(self, features: torch.Tensor, labels: torch.Tensor):
        self._features = features
        self._labels = labels.long()

    def __len__(self) -> int:  # pragma: no cover - trivial
        return self._labels.shape[0]

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self._features[idx], self._labels[idx]


class DropoutClassifier(nn.Module):
    """Two-layer classifier with dropout for MC inference."""

    def __init__(self, input_dim: int, hidden_dim: int = 128, dropout: float = 0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def build_loader(
    features: torch.Tensor,
    labels: torch.Tensor,
    batch_size: int,
    shuffle: bool,
) -> DataLoader:
    dataset = FeatureDataset(features, labels)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)


# ---------------------------------------------------------------------------
# Annotation management
# ---------------------------------------------------------------------------


class AnnotationStore:
    """Store selected samples for offline annotation or auditing."""

    def __init__(self, path: Optional[Path]):
        self.path = path
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, round_idx: int, selected: Sequence[Example]) -> None:
        if not self.path:
            return
        records = []
        for ex in selected:
            records.append(
                {
                    "round": round_idx,
                    "text": ex.text,
                    "label": ex.label,
                    "meta": ex.meta,
                }
            )
        with self.path.open("a", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Metrics logging
# ---------------------------------------------------------------------------


class MetricsLogger:
    """Log metrics locally and optionally to Weights & Biases."""

    def __init__(self, project: Optional[str], experiment_name: Optional[str]):
        self._history: List[Dict[str, float]] = []
        self._wandb_run = None

        if project and _HAS_WANDB:
            self._wandb_run = wandb.init(project=project, name=experiment_name, config={})
        elif project and not _HAS_WANDB:
            print("⚠️  wandb نصب نشده؛ فقط لاگ محلی ثبت می‌شود.")

    def log_round(self, metrics: Dict[str, float]) -> None:
        self._history.append(metrics)
        if self._wandb_run:
            self._wandb_run.log(metrics)

    def finish(self) -> None:
        if self._wandb_run:
            self._wandb_run.finish()

    @property
    def history(self) -> List[Dict[str, float]]:
        return list(self._history)


# ---------------------------------------------------------------------------
# Active learning experiment
# ---------------------------------------------------------------------------


@dataclass
class ActiveLearningConfig:
    label_name: str = "LAWYER"
    initial_size: int = 100
    query_size: int = 25
    rounds: int = 5
    test_split: float = 0.2
    batch_size: int = 32
    epochs: int = 5
    hidden_dim: int = 128
    dropout: float = 0.3
    lr: float = 1e-3
    weight_decay: float = 0.0
    mc_samples: int = 20
    acquisition: str = "bald"
    target_accuracy: float = 0.85
    random_baseline: int = 500


class ActiveLearningPipeline:
    def __init__(
        self,
        examples: Sequence[Example],
        encoder: FeatureEncoder,
        config: ActiveLearningConfig,
        logger: MetricsLogger,
        annotation_store: AnnotationStore,
        seed: int = 42,
    ):
        self.examples = list(examples)
        self.encoder = encoder
        self.config = config
        self.logger = logger
        self.annotation_store = annotation_store
        self.seed = seed

        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

        self.features, self.labels = collate_features(encoder, self.examples)

        (self.train_indices, self.pool_indices, self.test_indices,) = self._split_indices()

        model = DropoutClassifier(
            input_dim=self.features.shape[1],
            hidden_dim=config.hidden_dim,
            dropout=config.dropout,
        )

        self.learner = ActiveLearner(
            model=model,
            acquisition_strategy=config.acquisition,
            n_mc_samples=config.mc_samples,
        )

        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=config.lr,
            weight_decay=config.weight_decay,
        )
        self.criterion = nn.CrossEntropyLoss()

        self.test_loader = build_loader(
            self.features[self.test_indices],
            self.labels[self.test_indices],
            batch_size=config.batch_size,
            shuffle=False,
        )

    # ------------------------------------------------------------------
    def _split_indices(self) -> Tuple[List[int], List[int], List[int]]:
        indices = list(range(len(self.examples)))
        random.Random(self.seed).shuffle(indices)

        test_size = max(1, int(len(indices) * self.config.test_split))
        test_indices = indices[:test_size]
        start_train = test_size
        end_train = start_train + self.config.initial_size

        if end_train >= len(indices):
            raise ValueError("Initial size too large for dataset.")

        train_indices = indices[start_train:end_train]
        pool_indices = indices[end_train:]

        if not pool_indices:
            raise ValueError("Empty unlabeled pool; reduce initial size or test split.")

        return train_indices, pool_indices, test_indices

    # ------------------------------------------------------------------
    def _build_train_loader(self) -> DataLoader:
        return build_loader(
            self.features[self.train_indices],
            self.labels[self.train_indices],
            batch_size=self.config.batch_size,
            shuffle=True,
        )

    # ------------------------------------------------------------------
    def run(self) -> Dict[str, float]:
        for round_idx in range(1, self.config.rounds + 1):
            train_loader = self._build_train_loader()
            self.learner.update_model(
                train_loader=train_loader,
                optimizer=self.optimizer,
                criterion=self.criterion,
                n_epochs=self.config.epochs,
            )

            metrics = self.learner.evaluate(self.test_loader)
            metrics.update(
                {
                    "round": round_idx,
                    "train_size": len(self.train_indices),
                    "pool_size": len(self.pool_indices),
                }
            )
            self.logger.log_round(metrics)

            print(
                f"[Round {round_idx:02d}] train={len(self.train_indices):<4d} "
                f"pool={len(self.pool_indices):<4d} "
                f"accuracy={metrics['accuracy']:.3f}"
            )

            if not self.pool_indices:
                print("Pool exhausted; stopping early.")
                break

            budget = min(self.config.query_size, len(self.pool_indices))

            pool_tensor = self.features[self.pool_indices]
            selected_rel = self.learner.select_batch(pool_tensor, budget)
            newly_selected_indices = [self.pool_indices[i.item()] for i in selected_rel]

            selected_examples = [self.examples[idx] for idx in newly_selected_indices]
            self.annotation_store.append(round_idx, selected_examples)

            selected_set = set(newly_selected_indices)
            self.train_indices.extend(newly_selected_indices)
            self.pool_indices = [idx for idx in self.pool_indices if idx not in selected_set]

        savings = self.learner.compute_annotation_savings(
            random_baseline_annotations=self.config.random_baseline,
            target_accuracy=self.config.target_accuracy,
        )
        return savings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_pipeline(args: argparse.Namespace) -> Dict[str, float]:
    labeled_path = Path(args.labeled_path)

    examples = load_labeled_examples(labeled_path, args.label_name)

    encoder = build_encoder(args.encoder, args.encoder_model)

    annotation_store = AnnotationStore(
        Path(args.annotation_log) if args.annotation_log else None
    )

    logger = MetricsLogger(
        project=args.wandb_project,
        experiment_name=args.wandb_run_name,
    )

    config = ActiveLearningConfig(
        label_name=args.label_name,
        initial_size=args.initial_size,
        query_size=args.query_size,
        rounds=args.rounds,
        test_split=args.test_split,
        batch_size=args.batch_size,
        epochs=args.epochs,
        hidden_dim=args.hidden_dim,
        dropout=args.dropout,
        lr=args.lr,
        weight_decay=args.weight_decay,
        mc_samples=args.mc_samples,
        acquisition=args.strategy,
        target_accuracy=args.target_accuracy,
        random_baseline=args.random_baseline,
    )

    pipeline = ActiveLearningPipeline(
        examples=examples,
        encoder=encoder,
        config=config,
        logger=logger,
        annotation_store=annotation_store,
        seed=args.seed,
    )

    savings = pipeline.run()
    logger.finish()

    if args.save_history:
        history_path = Path(args.save_history)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("w", encoding="utf-8") as fh:
            json.dump(logger.history, fh, ensure_ascii=False, indent=2)
        print(f"✅ History written to {history_path}")

    print(
        "\n=== Active Learning Summary ===\n"
        f"Final accuracy: {logger.history[-1]['accuracy']:.3f}\n"
        f"Savings vs random: {savings['savings_pct']:.1f}% "
        f"(target reached: {savings['target_reached']})"
    )

    return savings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MAHOUN active learning pipeline.")
    parser.add_argument(
        "--labeled-path",
        default="data/raw/labeled_ner.jsonl",
        help="مسیر فایل JSONL شامل داده‌های برچسب‌خورده.",
    )
    parser.add_argument(
        "--label-name",
        default="LAWYER",
        help="نام برچسبی که به عنوان کلاس مثبت در نظر گرفته می‌شود.",
    )
    parser.add_argument(
        "--encoder",
        choices=["simple", "sbert"],
        default="simple",
        help="نوع انکودر ویژگی‌ها (simple یا sentence-transformer).",
    )
    parser.add_argument(
        "--encoder-model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="نام مدل SentenceTransformer (در حالت encoder=sbert).",
    )
    parser.add_argument(
        "--initial-size",
        type=int,
        default=100,
        help="تعداد نمونه‌های برچسب‌خورده‌ی اولیه.",
    )
    parser.add_argument(
        "--query-size",
        type=int,
        default=25,
        help="تعداد نمونه‌هایی که در هر دور برای annotation انتخاب می‌شوند.",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=5,
        help="حداکثر تعداد دورهای یادگیری فعال.",
    )
    parser.add_argument(
        "--test-split",
        type=float,
        default=0.2,
        help="نسبت داده‌هایی که برای ارزیابی کنار گذاشته می‌شود.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="سایز batch در آموزش/ارزیابی.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="تعداد epoch برای هر دور آموزش.",
    )
    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=128,
        help="ابعاد لایه‌ی مخفی مدل.",
    )
    parser.add_argument(
        "--dropout",
        type=float,
        default=0.3,
        help="احتمال Dropout برای مدل.",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-3,
        help="نرخ یادگیری.",
    )
    parser.add_argument(
        "--weight-decay",
        type=float,
        default=0.0,
        help="Weight decay برای Adam.",
    )
    parser.add_argument(
        "--mc-samples",
        type=int,
        default=20,
        help="تعداد نمونه‌گیری‌ها برای Monte Carlo Dropout.",
    )
    parser.add_argument(
        "--strategy",
        choices=["bald", "entropy", "qbc"],
        default="bald",
        help="استراتژی انتخاب نمونه.",
    )
    parser.add_argument(
        "--target-accuracy",
        type=float,
        default=0.85,
        help="آستانه‌ی دقت موردنظر برای محاسبه‌ی صرفه‌جویی annotation.",
    )
    parser.add_argument(
        "--random-baseline",
        type=int,
        default=500,
        help="تعداد annotation درSampling تصادفی برای مقایسه.",
    )
    parser.add_argument(
        "--annotation-log",
        default="",
        help="مسیر فایل JSONL برای ذخیره‌ی نمونه‌های انتخاب‌شده جهت برچسب‌گذاری.",
    )
    parser.add_argument(
        "--save-history",
        default="",
        help="مسیر فایل JSON برای ذخیره‌ی تاریخچه‌ی متریک‌ها.",
    )
    parser.add_argument(
        "--wandb-project",
        default="",
        help="نام پروژه‌ی W&B. اگر خالی باشد لاگینگ W&B انجام نمی‌شود.",
    )
    parser.add_argument(
        "--wandb-run-name",
        default="mahoun-active-learning",
        help="نام اجرای W&B (در صورت فعال بودن).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed تصادفی.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> Dict[str, float]:
    args = parse_args(argv)
    return run_pipeline(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()

