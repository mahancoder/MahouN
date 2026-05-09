# pipelines/finetuning/lora_ner_trainer.py
"""
LoRA Fine-tuning for NER Models
- Efficient parameter tuning
- Legal entity recognition
- Persian-specific optimization
- Active learning integration
"""

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
)
from datasets import Dataset as HFDataset
from seqeval.metrics import classification_report, f1_score
import wandb

try:
    from peft import LoraConfig, get_peft_model, TaskType, PeftModel
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False

from pipelines._logging import setup_logger

log = setup_logger("lora_ner")


# Label mapping for legal NER
LABEL_LIST = [
    "O",  # Outside
    "B-PERSON",  # Person
    "I-PERSON",
    "B-ORG",  # Organization
    "I-ORG",
    "B-LOC",  # Location
    "I-LOC",
    "B-LAW",  # Law/Article
    "I-LAW",
    "B-DATE",  # Date
    "I-DATE",
    "B-MONEY",  # Money
    "I-MONEY",
    "B-CASE",  # Case number
    "I-CASE",
]

LABEL2ID = {label: i for i, label in enumerate(LABEL_LIST)}
ID2LABEL = {i: label for i, label in enumerate(LABEL_LIST)}


class NERDataset:
    """Prepare NER dataset"""

    @staticmethod
    def load_from_jsonl(file_path: str) -> List[Dict]:
        """Load annotated data from JSONL"""
        examples = []

        for line in open(file_path, "r", encoding="utf-8"):
            data = json.loads(line)

            # Expected format:
            # {"tokens": [...], "ner_tags": [...]}
            examples.append({"tokens": data["tokens"], "ner_tags": data["ner_tags"]})

        return examples

    @staticmethod
    def tokenize_and_align_labels(examples: Dict, tokenizer, label_all_tokens: bool = True):
        """Tokenize and align labels with subword tokens"""

        tokenized_inputs = tokenizer(
            examples["tokens"],
            truncation=True,
            is_split_into_words=True,
            padding="max_length",
            max_length=512,
        )

        labels = []
        for i, label in enumerate(examples["ner_tags"]):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            previous_word_idx = None
            label_ids = []

            for word_idx in word_ids:
                if word_idx is None:
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:
                    label_ids.append(LABEL2ID[label[word_idx]])
                else:
                    label_ids.append(LABEL2ID[label[word_idx]] if label_all_tokens else -100)

                previous_word_idx = word_idx

            labels.append(label_ids)

        tokenized_inputs["labels"] = labels
        return tokenized_inputs


class LoRANERTrainer:
    """LoRA-based NER trainer"""

    def __init__(
        self,
        base_model: str = "HooshvareLab/bert-base-parsbert-uncased",
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.1,
        device: str = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.base_model_name = base_model

        log.info(f"Loading tokenizer and model: {base_model}")

        # Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)

        # Model
        self.model = AutoModelForTokenClassification.from_pretrained(
            base_model, num_labels=len(LABEL_LIST), id2label=ID2LABEL, label2id=LABEL2ID
        )

        # Apply LoRA
        if PEFT_AVAILABLE:
            self.apply_lora(lora_r, lora_alpha, lora_dropout)
        else:
            log.warning("PEFT not available, training full model")

        self.model.to(self.device)
        log.info(f"Model loaded on {self.device}")

    def apply_lora(self, r: int, alpha: int, dropout: float):
        """Apply LoRA to the model"""

        log.info(f"Applying LoRA: r={r}, alpha={alpha}, dropout={dropout}")

        lora_config = LoraConfig(
            r=r,
            lora_alpha=alpha,
            target_modules=["query", "key", "value"],
            lora_dropout=dropout,
            bias="none",
            task_type=TaskType.TOKEN_CLS,
        )

        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()

        log.info("LoRA applied successfully")

    def prepare_dataset(
        self, train_file: str, eval_file: str = None
    ) -> Tuple[HFDataset, HFDataset]:
        """Prepare datasets"""

        log.info("Loading training data...")
        train_examples = NERDataset.load_from_jsonl(train_file)

        # Convert to HuggingFace dataset
        train_dataset = HFDataset.from_dict(
            {
                "tokens": [ex["tokens"] for ex in train_examples],
                "ner_tags": [ex["ner_tags"] for ex in train_examples],
            }
        )

        # Tokenize
        train_dataset = train_dataset.map(
            lambda x: NERDataset.tokenize_and_align_labels(x, self.tokenizer), batched=True
        )

        eval_dataset = None
        if eval_file:
            log.info("Loading evaluation data...")
            eval_examples = NERDataset.load_from_jsonl(eval_file)
            eval_dataset = HFDataset.from_dict(
                {
                    "tokens": [ex["tokens"] for ex in eval_examples],
                    "ner_tags": [ex["ner_tags"] for ex in eval_examples],
                }
            )
            eval_dataset = eval_dataset.map(
                lambda x: NERDataset.tokenize_and_align_labels(x, self.tokenizer), batched=True
            )

        return train_dataset, eval_dataset

    def compute_metrics(self, p):
        """Compute NER metrics"""
        predictions, labels = p
        predictions = np.argmax(predictions, axis=2)

        # Remove ignored index (special tokens)
        true_predictions = [
            [ID2LABEL[p] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [ID2LABEL[l] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]

        # Compute F1
        f1 = f1_score(true_labels, true_predictions)

        return {"f1": f1, "report": classification_report(true_labels, true_predictions, digits=4)}

    def train(
        self,
        train_dataset: HFDataset,
        eval_dataset: HFDataset = None,
        output_dir: str = "models/lora_ner",
        epochs: int = 5,
        batch_size: int = 16,
        learning_rate: float = 3e-4,
        warmup_ratio: float = 0.1,
        use_wandb: bool = False,
    ):
        """Train the model"""

        log.info(f"Starting training: {len(train_dataset)} examples, {epochs} epochs")

        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            warmup_ratio=warmup_ratio,
            weight_decay=0.01,
            logging_dir=f"{output_dir}/logs",
            logging_steps=50,
            evaluation_strategy="epoch" if eval_dataset else "no",
            save_strategy="epoch",
            load_best_model_at_end=True if eval_dataset else False,
            metric_for_best_model="f1" if eval_dataset else None,
            report_to="wandb" if use_wandb else "none",
            fp16=torch.cuda.is_available(),
            gradient_accumulation_steps=2,
            save_total_limit=2,
        )

        # Data collator
        data_collator = DataCollatorForTokenClassification(self.tokenizer)

        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
            compute_metrics=self.compute_metrics if eval_dataset else None,
        )

        # Train
        trainer.train()

        # Save
        trainer.save_model(output_dir)
        self.tokenizer.save_pretrained(output_dir)

        log.info(f"Training complete. Model saved to {output_dir}")

        # Final evaluation
        if eval_dataset:
            log.info("Running final evaluation...")
            metrics = trainer.evaluate()
            log.info(f"Final metrics: {metrics}")

            # Print classification report
            if "eval_report" in metrics:
                print("\n" + "=" * 80)
                print("Classification Report:")
                print("=" * 80)
                print(metrics["eval_report"])

    def save_lora_weights(self, output_dir: str):
        """Save only LoRA weights"""

        if not PEFT_AVAILABLE:
            log.warning("PEFT not available")
            return

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.model.save_pretrained(output_path / "lora_weights")
        log.info(f"LoRA weights saved to {output_path / 'lora_weights'}")


def create_sample_data(output_file: str, num_samples: int = 100):
    """Create sample NER data for testing"""

    samples = []

    # Sample templates
    templates = [
        {
            "tokens": ["آقای", "احمدی", "در", "دادگاه", "تهران", "حاضر", "شد"],
            "ner_tags": ["O", "B-PERSON", "O", "B-ORG", "B-LOC", "O", "O"],
        },
        {
            "tokens": ["طبق", "ماده", "۱۰", "قانون", "مدنی"],
            "ner_tags": ["O", "B-LAW", "I-LAW", "I-LAW", "I-LAW"],
        },
        {"tokens": ["پرونده", "شماره", "۹۸۰۰۱۲۳"], "ner_tags": ["O", "O", "B-CASE"]},
    ]

    for _ in range(num_samples):
        samples.append(templates[_ % len(templates)])

    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    log.info(f"Created {num_samples} sample examples in {output_file}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_file", required=True, help="Training data JSONL")
    ap.add_argument("--eval_file", help="Evaluation data JSONL")
    ap.add_argument("--base_model", default="HooshvareLab/bert-base-parsbert-uncased")
    ap.add_argument("--output_dir", default="models/lora_ner")
    ap.add_argument("--lora_r", type=int, default=16)
    ap.add_argument("--lora_alpha", type=int, default=32)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--learning_rate", type=float, default=3e-4)
    ap.add_argument("--create_sample_data", action="store_true")
    ap.add_argument("--wandb", action="store_true")
    args = ap.parse_args()

    # Create sample data if requested
    if args.create_sample_data:
        create_sample_data(args.train_file, num_samples=100)
        if args.eval_file:
            create_sample_data(args.eval_file, num_samples=20)
        log.info("Sample data created. You can now train with this data.")
        return

    # Initialize trainer
    trainer = LoRANERTrainer(
        base_model=args.base_model, lora_r=args.lora_r, lora_alpha=args.lora_alpha
    )

    # Prepare datasets
    train_dataset, eval_dataset = trainer.prepare_dataset(args.train_file, args.eval_file)

    # Train
    trainer.train(
        train_dataset,
        eval_dataset=eval_dataset,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        use_wandb=args.wandb,
    )

    # Save LoRA weights
    trainer.save_lora_weights(args.output_dir)

    log.info("✅ Training complete!")


if __name__ == "__main__":
    main()
