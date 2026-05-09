# pipelines/embed_index.py
"""
Advanced Embedding & Indexing with:
- Multi-model support
- Batch processing with progress
- FP16/BF16 optimization
- Incremental indexing
- Metadata enrichment
- Quality checks
"""
import os
import argparse
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import hashlib
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import chromadb
from chromadb.config import Settings
import numpy as np

# Optional WandB
try:
    import wandb
    HAS_WANDB = True
except ImportError:
    HAS_WANDB = False
    wandb = None

from ._config import load_config
from ._logging import setup_logger

log = setup_logger("embed")


@dataclass
class EmbeddingConfig:
    """Embedding configuration"""

    model_name: str
    batch_size: int
    max_length: int = 512
    normalize: bool = True
    use_fp16: bool = True
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class AdvancedEmbedder:
    """Advanced embedding system"""

    def __init__(self, config: EmbeddingConfig):
        self.config = config

        log.info(f"Loading model: {config.model_name} on {config.device}")
        self.model = SentenceTransformer(config.model_name, device=config.device)
        self.model.eval()

        # Enable FP16 if available
        if config.use_fp16 and config.device == "cuda":
            self.model = self.model.half()
            log.info("FP16 enabled")

        log.info(f"Model loaded: {config.model_name}")

    def embed_batch(self, texts: List[str], show_progress: bool = False) -> np.ndarray:
        """Embed a batch of texts"""

        with torch.inference_mode():
            embeddings = self.model.encode(
                texts,
                batch_size=self.config.batch_size,
                show_progress_bar=show_progress,
                device=self.config.device,
                convert_to_numpy=True,
                normalize_embeddings=self.config.normalize,
            )

        return embeddings

    def embed_with_metadata(
        self, records: List[Dict], text_field: str = "text"
    ) -> tuple[List[str], List[str], List[np.ndarray], List[Dict]]:
        """
        Embed records with metadata
        Returns: (ids, texts, embeddings, metadatas)
        """
        ids = []
        texts = []
        metadatas = []

        for rec in records:
            text = rec.get(text_field, "")
            if not text or len(text.strip()) < 10:
                log.warning(f"Skipping empty/short text for {rec.get('id')}")
                continue

            # Truncate if needed
            text_truncated = text[: self.config.max_length * 4]  # Rough char estimate

            ids.append(rec["id"])
            texts.append(text_truncated)

            # Prepare metadata
            meta = rec.get("meta", {}).copy()
            meta["text_length"] = len(text)
            meta["truncated"] = len(text) > len(text_truncated)
            metadatas.append(meta)

        # Embed
        log.info(f"Embedding {len(texts)} documents...")
        embeddings = self.embed_batch(texts, show_progress=True)

        return ids, texts, embeddings, metadatas


class IncrementalIndexer:
    """Incremental vector indexing"""

    def __init__(self, persist_dir: str, collection_name: str):
        self.persist_dir = persist_dir
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path=persist_dir, settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            collection_name, metadata={"hnsw:space": "cosine"}
        )

        log.info(f"Collection: {collection_name} ({self.collection.count()} docs)")

    def index_batch(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: np.ndarray,
        metadatas: List[Dict],
        batch_size: int = 1000,
    ):
        """Index in batches"""

        total = len(ids)
        for i in tqdm(range(0, total, batch_size), desc="Indexing"):
            end = min(i + batch_size, total)

            self.collection.upsert(
                ids=ids[i:end],
                documents=documents[i:end],
                embeddings=embeddings[i:end].tolist(),
                metadatas=metadatas[i:end],
            )

        log.info(f"Indexed {total} documents")

    def get_stats(self) -> Dict:
        """Get collection statistics"""
        count = self.collection.count()

        # Sample to get metadata stats
        if count > 0:
            sample = self.collection.get(limit=min(100, count))

            categories = {}
            for meta in sample.get("metadatas", []):
                cat = meta.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1
        else:
            categories = {}

        return {
            "total_documents": count,
            "collection_name": self.collection_name,
            "category_distribution": categories,
        }


def compute_embedding_quality(embeddings: np.ndarray) -> Dict:
    """Compute embedding quality metrics"""

    # Compute pairwise similarities
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)
    similarities = normalized @ normalized.T

    # Remove diagonal
    np.fill_diagonal(similarities, 0)

    metrics = {
        "avg_similarity": float(similarities.mean()),
        "max_similarity": float(similarities.max()),
        "min_similarity": float(similarities.min()),
        "std_similarity": float(similarities.std()),
        "embedding_dim": embeddings.shape[1],
        "num_embeddings": embeddings.shape[0],
    }

    return metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True, help="Input JSONL file")
    ap.add_argument("--persist_dir", default=None, help="Chroma persist directory")
    ap.add_argument("--collection", default=None, help="Collection name")
    ap.add_argument("--model", default=None, help="Override embedding model")
    ap.add_argument("--batch_size", type=int, default=None, help="Batch size")
    ap.add_argument("--incremental", action="store_true", help="Incremental indexing")
    ap.add_argument("--compute_quality", action="store_true", help="Compute quality metrics")
    ap.add_argument("--wandb", action="store_true", help="Enable W&B logging")
    args = ap.parse_args()

    # Load config
    cfg = load_config()

    # Override config
    persist_dir = args.persist_dir or cfg.chroma_dir
    collection_name = args.collection or cfg.chroma_collection
    model_name = args.model or cfg.embed_model
    batch_size = args.batch_size or cfg.embed_batch

    # W&B init
    if args.wandb:
        wandb.init(
            project=os.getenv("WANDB_PROJECT", "mahoun"),
            name="embed-index",
            reinit=True,
            config={"model": model_name, "batch_size": batch_size, "collection": collection_name},
        )

    # Load data
    log.info(f"Loading data from {args.jsonl}")
    records = []
    for line in open(args.jsonl, "r", encoding="utf-8"):
        records.append(json.loads(line))

    log.info(f"Loaded {len(records)} records")

    # Initialize embedder
    embed_config = EmbeddingConfig(
        model_name=model_name, batch_size=batch_size, use_fp16=torch.cuda.is_available()
    )
    embedder = AdvancedEmbedder(embed_config)

    # Embed
    ids, texts, embeddings, metadatas = embedder.embed_with_metadata(records)

    log.info(f"Generated {len(embeddings)} embeddings")

    # Quality metrics
    if args.compute_quality:
        quality = compute_embedding_quality(embeddings)
        log.info(f"Quality metrics: {quality}")

        if args.wandb:
            wandb.log({"embedding_quality": quality})

    # Index
    indexer = IncrementalIndexer(persist_dir, collection_name)
    indexer.index_batch(ids, texts, embeddings, metadatas)

    # Stats
    stats = indexer.get_stats()
    log.info(f"Collection stats: {stats}")

    # W&B logging
    if args.wandb:
        wandb.log(
            {
                "num_documents": len(ids),
                "embedding_model": model_name,
                "embedding_dim": embeddings.shape[1],
                "collection_size": stats["total_documents"],
                "status": "completed",
            }
        )

        # Category distribution
        if stats.get("category_distribution"):
            wandb.log({"category_distribution": stats["category_distribution"]})

        # Embedding visualization (sample)
        if len(embeddings) > 0:
            from sklearn.decomposition import PCA

            # PCA to 2D
            pca = PCA(n_components=2)
            embeddings_2d = pca.fit_transform(embeddings[:1000])  # Sample

            # Create scatter plot data
            scatter_data = [
                [x, y, metadatas[i].get("category", "unknown")]
                for i, (x, y) in enumerate(embeddings_2d)
            ]

            table = wandb.Table(data=scatter_data, columns=["x", "y", "category"])
            wandb.log(
                {
                    "embedding_space": wandb.plot.scatter(
                        table, "x", "y", title="Embedding Space (PCA)"
                    )
                }
            )

        wandb.finish()

    log.info(f"✅ Indexing complete: {persist_dir}/{collection_name}")


if __name__ == "__main__":
    main()
