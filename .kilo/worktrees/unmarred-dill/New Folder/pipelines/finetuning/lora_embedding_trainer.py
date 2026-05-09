# pipelines/finetuning/lora_embedding_trainer.py
"""
LoRA Fine-tuning for Embedding Models
- Efficient parameter tuning with LoRA
- Contrastive learning
- Hard negative mining
- Domain adaptation for legal Persian
"""

import os
import json
import argparse
from pathlib import Path
from dataclasses import dataclass
import random

import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer, losses, InputExample
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
import numpy as np
from tqdm import tqdm

try:
    from peft import LoraConfig, get_peft_model, TaskType

    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    print("⚠️  PEFT not installed. Install with: pip install peft")

from pipelines._logging import setup_logger

log = setup_logger("lora_embedding")


@dataclass
class TrainingExample:
    """Training example for contrastive learning"""

    query: str
    positive: str
    negatives: List[str]
    label: float = 1.0


class LegalEmbeddingDataset(Dataset):
    """Dataset for legal document embeddings"""

    def __init__(self, examples: List[TrainingExample]):
        self.examples = examples

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]


class HardNegativeMiner:
    """Mine hard negatives for better training"""

    def __init__(self, model: SentenceTransformer, corpus: List[Dict]):
        self.model = model
        self.corpus = corpus
        self.corpus_embeddings = None

    def build_index(self):
        """Build corpus embeddings"""
        log.info("Building corpus index for hard negative mining...")

        texts = [doc["text"] for doc in self.corpus]
        self.corpus_embeddings = self.model.encode(
            texts, batch_size=64, show_progress_bar=True, convert_to_numpy=True
        )

        log.info(f"Index built: {len(self.corpus_embeddings)} documents")

    def mine_hard_negatives(self, query: str, positive_id: str, k: int = 5) -> List[str]:
        """Mine hard negatives (similar but not relevant)"""

        if self.corpus_embeddings is None:
            self.build_index()

        # Encode query
        query_emb = self.model.encode([query], convert_to_numpy=True)[0]

        # Compute similarities
        similarities = np.dot(self.corpus_embeddings, query_emb)

        # Get top-k most similar (excluding positive)
        top_indices = np.argsort(similarities)[::-1]

        hard_negatives = []
        for idx in top_indices:
            doc_id = self.corpus[idx]["id"]
            if doc_id != positive_id and len(hard_negatives) < k:
                hard_negatives.append(self.corpus[idx]["text"])

        return hard_negatives


class LoRAEmbeddingTrainer:
    """LoRA-based embedding model trainer"""

    def __init__(
        self,
        base_model: str = "BAAI/bge-m3",
        lora_r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.1,
        device: str = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        log.info(f"Loading base model: {base_model}")
        self.model = SentenceTransformer(base_model, device=self.device)

        # Apply LoRA
        if PEFT_AVAILABLE:
            self.apply_lora(lora_r, lora_alpha, lora_dropout)
        else:
            log.warning("PEFT not available, training full model")

        log.info(f"Model loaded on {self.device}")

    def apply_lora(self, r: int, alpha: int, dropout: float):
        """Apply LoRA to the model"""

        log.info(f"Applying LoRA: r={r}, alpha={alpha}, dropout={dropout}")

        # Get the transformer model
        transformer = self.model[0].auto_model

        # LoRA config
        lora_config = LoraConfig(
            r=r,
            lora_alpha=alpha,
            target_modules=["query", "key", "value"],  # Attention layers
            lora_dropout=dropout,
            bias="none",
            task_type=TaskType.FEATURE_EXTRACTION,
        )

        # Apply LoRA
        transformer = get_peft_model(transformer, lora_config)
        transformer.print_trainable_parameters()

        # Update model
        self.model[0].auto_model = transformer

        log.info("LoRA applied successfully")

    def prepare_training_data(
        self,
        qrels: Dict[str, List[str]],
        corpus: Dict[str, Dict],
        use_hard_negatives: bool = True,
        num_negatives: int = 3,
    ) -> List[InputExample]:
        """Prepare training data from qrels"""

        log.info("Preparing training data...")

        # Convert corpus to list
        corpus_list = list(corpus.values())

        # Hard negative miner
        miner = None
        if use_hard_negatives:
            miner = HardNegativeMiner(self.model, corpus_list)
            miner.build_index()

        examples = []

        for query, relevant_ids in tqdm(qrels.items(), desc="Preparing data"):
            if not relevant_ids:
                continue

            # Get positive document
            positive_id = relevant_ids[0]
            if positive_id not in corpus:
                continue

            positive_text = corpus[positive_id]["text"]

            # Get negatives
            if use_hard_negatives and miner:
                negatives = miner.mine_hard_negatives(query, positive_id, k=num_negatives)
            else:
                # Random negatives
                all_ids = list(corpus.keys())
                negative_ids = random.sample(
                    [id for id in all_ids if id not in relevant_ids],
                    min(num_negatives, len(all_ids) - len(relevant_ids)),
                )
                negatives = [corpus[id]["text"] for id in negative_ids]

            # Create training examples (query, positive, negative)
            for neg in negatives:
                examples.append(InputExample(texts=[query, positive_text, neg]))

        log.info(f"Prepared {len(examples)} training examples")
        return examples

    def train(
        self,
        train_examples: List[InputExample],
        eval_examples: List[InputExample] = None,
        output_dir: str = "models/lora_embedding",
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5,
        warmup_steps: int = 100,
        use_wandb: bool = False,
    ):
        """Train the model"""

        log.info(f"Starting training: {len(train_examples)} examples, {epochs} epochs")

        # DataLoader
        train_dataloader = DataLoader(train_examples, batch_size=batch_size, shuffle=True)

        # Loss function (Multiple Negatives Ranking Loss)
        train_loss = losses.MultipleNegativesRankingLoss(self.model)

        # Evaluator
        evaluator = None
        if eval_examples:
            # Convert to sentence pairs for evaluation
            eval_sentences1 = [ex.texts[0] for ex in eval_examples]
            eval_sentences2 = [ex.texts[1] for ex in eval_examples]
            eval_scores = [1.0] * len(eval_examples)  # All positives

            evaluator = EmbeddingSimilarityEvaluator(
                eval_sentences1, eval_sentences2, eval_scores, name="legal_eval"
            )

        # W&B
        if use_wandb:
            import wandb

            wandb.init(
                project=os.getenv("WANDB_PROJECT", "mahoun"),
                name="lora_embedding_training",
                config={
                    "epochs": epochs,
                    "batch_size": batch_size,
                    "learning_rate": learning_rate,
                    "num_examples": len(train_examples),
                },
            )

        # Train
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            evaluator=evaluator,
            epochs=epochs,
            warmup_steps=warmup_steps,
            output_path=output_dir,
            show_progress_bar=True,
            optimizer_params={"lr": learning_rate},
        )

        log.info(f"Training complete. Model saved to {output_dir}")

        if use_wandb:
            wandb.finish()

    def save_lora_weights(self, output_dir: str):
        """Save only LoRA weights"""

        if not PEFT_AVAILABLE:
            log.warning("PEFT not available, saving full model")
            self.model.save(output_dir)
            return

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save LoRA weights
        transformer = self.model[0].auto_model
        transformer.save_pretrained(output_path / "lora_weights")

        log.info(f"LoRA weights saved to {output_path / 'lora_weights'}")


def load_qrels(qrels_file: str) -> Dict[str, List[str]]:
    """Load qrels file"""
    with open(qrels_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_corpus(corpus_file: str) -> Dict[str, Dict]:
    """Load corpus from JSONL"""
    corpus = {}
    for line in open(corpus_file, "r", encoding="utf-8"):
        doc = json.loads(line)
        corpus[doc["id"]] = doc
    return corpus


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qrels", required=True, help="Training qrels JSON")
    ap.add_argument("--corpus", required=True, help="Corpus JSONL")
    ap.add_argument("--eval_qrels", help="Evaluation qrels JSON")
    ap.add_argument("--base_model", default="BAAI/bge-m3")
    ap.add_argument("--output_dir", default="models/lora_embedding")
    ap.add_argument("--lora_r", type=int, default=8)
    ap.add_argument("--lora_alpha", type=int, default=16)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--learning_rate", type=float, default=2e-5)
    ap.add_argument("--use_hard_negatives", action="store_true")
    ap.add_argument("--wandb", action="store_true")
    args = ap.parse_args()

    # Load data
    log.info("Loading data...")
    qrels = load_qrels(args.qrels)
    corpus = load_corpus(args.corpus)

    eval_qrels = None
    if args.eval_qrels:
        eval_qrels = load_qrels(args.eval_qrels)

    # Initialize trainer
    trainer = LoRAEmbeddingTrainer(
        base_model=args.base_model, lora_r=args.lora_r, lora_alpha=args.lora_alpha
    )

    # Prepare training data
    train_examples = trainer.prepare_training_data(
        qrels, corpus, use_hard_negatives=args.use_hard_negatives
    )

    eval_examples = None
    if eval_qrels:
        eval_examples = trainer.prepare_training_data(eval_qrels, corpus, use_hard_negatives=False)

    # Train
    trainer.train(
        train_examples,
        eval_examples=eval_examples,
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
