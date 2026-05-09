# pipelines/_config.py
import os, yaml
from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging


def _read_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f) or {}
        # Replace environment variables in config
        return _replace_env_vars(content)


def _replace_env_vars(obj: Any) -> Any:
    """Recursively replace ${VAR} with environment variables"""
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        var_name = obj[2:-1]
        return os.getenv(var_name, obj)
    return obj


@dataclass
class AppConfig:
    # embedding
    embed_model: str = "BAAI/bge-m3"
    embed_batch: int = 64
    chroma_dir: str = "embeddings/chroma"
    chroma_collection: str = "mahoun"
    # Chroma client mode
    use_chroma_http: bool = False
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # retrieval
    bm25_index_dir: str = "data/bm25_index"
    bm25_provider: str = "internal"  # "internal" | "pyserini"
    pyserini_search_k: int = 200
    hybrid_alpha: float = 0.65
    top_k_dense: int = 20
    top_k: int = 5

    # ner
    ner_model: str = "HooshvareLab/bert-base-parsbert-uncased"

    # reranker
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    rerank_top_r: int = 5
    rerank_device: Optional[str] = None  # "cpu"/"cuda"/None(auto)
    rerank_batch_size: int = 16
    ce_normalization: str = "sigmoid"  # "sigmoid" | "minmax"

    # nli
    nli_model: str = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"


@dataclass
class GNNConfig:
    """Configuration for GNN-Enhanced Graph System"""

    # Semantic Chunker
    semantic_chunker: Dict[str, Any] = None

    # GNN Graph Builder
    gnn_graph_builder: Dict[str, Any] = None

    # GAT Reranker
    gat_reranker: Dict[str, Any] = None

    # GAT Training
    gat_training: Dict[str, Any] = None

    # Graph Analytics
    graph_analytics: Dict[str, Any] = None

    # Performance
    performance: Dict[str, Any] = None

    # Logging
    logging: Dict[str, Any] = None

    # Error Handling
    error_handling: Dict[str, Any] = None


def load_config(app_yaml: str = "configs/app.yaml") -> AppConfig:
    d = _read_yaml(app_yaml)
    cfg = AppConfig(**{**AppConfig().__dict__, **d})
    # ENV overrides
    cfg.embed_model = os.getenv("EMBED_MODEL", cfg.embed_model)
    cfg.chroma_dir = os.getenv("CHROMA_DIR", cfg.chroma_dir)
    cfg.chroma_collection = os.getenv("CHROMA_COLLECTION", cfg.chroma_collection)
    cfg.hybrid_alpha = float(os.getenv("HYBRID_ALPHA", cfg.hybrid_alpha))
    # Validate and sanitize
    _validate_config(cfg)
    return cfg


def load_gnn_config(gnn_yaml: str = "configs/gnn_config.yaml") -> Optional[GNNConfig]:
    """Load GNN configuration from YAML file"""
    if not os.path.exists(gnn_yaml):
        return None

    d = _read_yaml(gnn_yaml)
    cfg = GNNConfig(
        semantic_chunker=d.get("semantic_chunker", {}),
        gnn_graph_builder=d.get("gnn_graph_builder", {}),
        gat_reranker=d.get("gat_reranker", {}),
        gat_training=d.get("gat_training", {}),
        graph_analytics=d.get("graph_analytics", {}),
        performance=d.get("performance", {}),
        logging=d.get("logging", {}),
        error_handling=d.get("error_handling", {}),
    )
    return cfg


def _validate_config(cfg: AppConfig) -> None:
    """Lightweight validation with corrective warnings instead of hard failures."""
    log = logging.getLogger("config")
    if cfg.top_k <= 0:
        log.warning("Invalid top_k <= 0; setting to 5")
        cfg.top_k = 5
    if cfg.top_k_dense <= 0:
        log.warning("Invalid top_k_dense <= 0; setting to 20")
        cfg.top_k_dense = 20
    if not (0.0 <= cfg.hybrid_alpha <= 1.0):
        log.warning("hybrid_alpha out of range; clamping to [0,1]")
        cfg.hybrid_alpha = max(0.0, min(1.0, cfg.hybrid_alpha))
    if cfg.rerank_top_r <= 0:
        log.warning("Invalid rerank_top_r <= 0; setting to 5")
        cfg.rerank_top_r = 5
    if cfg.rerank_batch_size <= 0:
        log.warning("Invalid rerank_batch_size <= 0; setting to 16")
        cfg.rerank_batch_size = 16
    if cfg.ce_normalization not in ("sigmoid", "minmax"):
        log.warning("Unknown ce_normalization; defaulting to 'sigmoid'")
        cfg.ce_normalization = "sigmoid"
    if cfg.bm25_provider not in ("internal", "pyserini"):
        log.warning("Unknown bm25_provider; defaulting to 'internal'")
        cfg.bm25_provider = "internal"
