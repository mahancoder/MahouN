"""
Advanced Data Preparation Configuration
========================================
Centralized configuration for data preparation pipeline
"""

from pydantic import BaseModel, Field, validator
from pathlib import Path
from typing import List, Optional
from typing_extensions import Literal


class IngestionConfig(BaseModel):
    """Document ingestion configuration"""
    
    supported_formats: List[str] = Field(
        default=["pdf", "docx", "txt", "json", "jsonl"],
        description="Supported file formats"
    )
    use_ocr: bool = Field(default=False, description="Enable OCR for scanned documents")
    ocr_language: str = Field(default="fas+eng", description="OCR language")
    max_file_size_mb: int = Field(default=50, ge=1, le=500)
    parallel_workers: int = Field(default=4, ge=1, le=32)
    extract_metadata: bool = Field(default=True)
    preserve_structure: bool = Field(default=True)


class PreprocessingConfig(BaseModel):
    """Text preprocessing configuration"""
    
    normalize_unicode: bool = Field(default=True)
    normalize_persian: bool = Field(default=True)
    remove_extra_whitespace: bool = Field(default=True)
    redact_pii: bool = Field(default=True)
    fix_encoding: bool = Field(default=True)
    
    # Quality filters
    min_length: int = Field(default=50, ge=10)
    max_length: int = Field(default=1_000_000, ge=1000)
    min_word_count: int = Field(default=10, ge=1)
    require_persian: bool = Field(default=True)
    
    # Deduplication
    enable_deduplication: bool = Field(default=True)
    dedup_method: Literal["exact", "fuzzy", "semantic"] = Field(default="exact")
    fuzzy_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    
    # Performance
    batch_size: int = Field(default=100, ge=1)
    parallel_workers: int = Field(default=8, ge=1, le=32)


class ChunkingConfig(BaseModel):
    """Text chunking configuration"""
    
    method: Literal["classic", "semantic", "hybrid"] = Field(default="semantic")
    
    # Size parameters
    min_chunk_size: int = Field(default=300, ge=100)
    max_chunk_size: int = Field(default=800, ge=500)
    target_chunk_size: int = Field(default=600, ge=300)
    overlap_size: int = Field(default=80, ge=0)
    
    # Semantic chunking
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    coherence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    preserve_entities: bool = Field(default=True)
    preserve_sentences: bool = Field(default=True)
    
    # Models
    embedding_model: str = Field(default="BAAI/bge-m3")
    ner_model: str = Field(default="HooshvareLab/bert-base-parsbert-uncased")
    
    # Performance
    device: Literal["cpu", "cuda", "mps"] = Field(default="cuda")
    batch_size: int = Field(default=32, ge=1)
    
    @validator('max_chunk_size')
    def validate_max_size(cls, v, values):
        if 'min_chunk_size' in values and v <= values['min_chunk_size']:
            raise ValueError('max_chunk_size must be greater than min_chunk_size')
        return v


class LabelingConfig(BaseModel):
    """Entity labeling configuration"""
    
    # Entity types to extract
    entity_types: List[str] = Field(
        default=[
            "ARTICLE", "LAW_NAME", "COURT", "CASE_NUMBER",
            "VERDICT_NUMBER", "DATE", "PERSON", "ORGANIZATION",
            "LOCATION", "MONEY"
        ]
    )
    
    # Models
    ner_model: str = Field(default="HooshvareLab/bert-base-parsbert-uncased")
    use_ensemble: bool = Field(default=True)
    ensemble_models: List[str] = Field(default=[])
    
    # Model paths (for validation)
    model_base_path: Optional[Path] = Field(default=Path("./models"))
    
    # Confidence
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    calibrate_confidence: bool = Field(default=True)
    
    # Post-processing
    validate_entities: bool = Field(default=True)
    merge_overlapping: bool = Field(default=True)
    resolve_conflicts: bool = Field(default=True)
    
    # Performance
    device: Literal["cpu", "cuda", "mps", "auto"] = Field(default="auto")
    batch_size: int = Field(default=32, ge=1)
    
    @validator('device')
    def validate_device(cls, v):
        """Validate and auto-detect device"""
        if v == "auto":
            # Auto-detect best available device
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    return "mps"
                else:
                    return "cpu"
            except ImportError:
                return "cpu"
        return v
    
    @validator('model_base_path')
    def validate_model_paths(cls, v):
        """Validate that model base path exists"""
        if v and not v.exists():
            import warnings
            warnings.warn(f"Model base path does not exist: {v}. Models will be downloaded if needed.")
        return v
    
    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of warnings/errors
        
        Returns:
            List of validation messages (empty if all valid)
        """
        messages = []
        
        # Check model paths
        if self.model_base_path:
            parsbert_path = self.model_base_path / "parsbert-small"
            if not parsbert_path.exists():
                messages.append(f"Warning: ParsBERT model not found at {parsbert_path}")
        
        # Check device availability
        if self.device == "cuda":
            try:
                import torch
                if not torch.cuda.is_available():
                    messages.append("Warning: CUDA device requested but not available. Falling back to CPU.")
            except ImportError:
                messages.append("Warning: PyTorch not installed. Cannot validate device.")
        
        # Check confidence threshold
        if self.min_confidence < 0.5:
            messages.append(f"Warning: Low confidence threshold ({self.min_confidence}) may result in noisy entities.")
        
        return messages


class EmbeddingConfig(BaseModel):
    """Embedding generation configuration"""
    
    model_name: str = Field(default="BAAI/bge-m3")
    model_type: Literal["sentence-transformers", "huggingface"] = Field(
        default="sentence-transformers"
    )
    
    # Embedding parameters
    max_length: int = Field(default=512, ge=128, le=8192)
    normalize_embeddings: bool = Field(default=True)
    pooling_strategy: Literal["mean", "cls", "max"] = Field(default="mean")
    
    # Performance
    device: Literal["cpu", "cuda", "mps"] = Field(default="cuda")
    batch_size: int = Field(default=32, ge=1)
    use_fp16: bool = Field(default=True)
    
    # Caching
    cache_embeddings: bool = Field(default=True)
    cache_dir: Optional[Path] = Field(default=None)


class IndexingConfig(BaseModel):
    """Indexing configuration"""
    
    # Vector DB
    vector_db: Literal["chromadb", "faiss", "qdrant"] = Field(default="chromadb")
    vector_db_host: str = Field(default="localhost")
    vector_db_port: int = Field(default=8001)
    collection_name: str = Field(default="legal_documents")
    
    # BM25
    build_bm25: bool = Field(default=True)
    bm25_k1: float = Field(default=1.5, ge=0.0)
    bm25_b: float = Field(default=0.75, ge=0.0, le=1.0)
    
    # Graph DB
    build_graph: bool = Field(default=True)
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="mahoun2024")
    
    # PostgreSQL
    build_postgres: bool = Field(default=True)
    postgres_url: str = Field(
        default="postgresql://mahoun:mahoun2024@localhost:5432/mahoun"
    )


class QualityConfig(BaseModel):
    """Quality assurance configuration"""
    
    enable_quality_checks: bool = Field(default=True)
    
    # Metrics to track
    track_metrics: List[str] = Field(
        default=[
            "length_distribution",
            "entity_density",
            "coherence_scores",
            "duplication_rate",
            "processing_time"
        ]
    )
    
    # Thresholds
    min_quality_score: float = Field(default=0.6, ge=0.0, le=1.0)
    max_error_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    
    # Reporting
    generate_report: bool = Field(default=True)
    report_format: Literal["json", "html", "markdown"] = Field(default="markdown")
    save_failed_samples: bool = Field(default=True)


class MonitoringConfig(BaseModel):
    """Monitoring and logging configuration"""
    
    # W&B
    use_wandb: bool = Field(default=False)
    wandb_project: str = Field(default="mahoun-data-prep")
    wandb_entity: Optional[str] = Field(default=None)
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_to_file: bool = Field(default=True)
    log_dir: Path = Field(default=Path("./logs/data_prep"))
    
    # Progress tracking
    show_progress: bool = Field(default=True)
    progress_update_interval: int = Field(default=10, ge=1)


class DataPrepConfig(BaseModel):
    """Complete data preparation configuration"""
    
    # Sub-configurations
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    labeling: LabelingConfig = Field(default_factory=LabelingConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    # Global settings
    project_name: str = Field(default="mahoun-legal-ai")
    version: str = Field(default="2.0.0")
    random_seed: int = Field(default=42)
    
    # Paths
    input_dir: Path = Field(default=Path("./data/raw"))
    output_dir: Path = Field(default=Path("./data/processed"))
    cache_dir: Path = Field(default=Path("./data/cache"))
    
    class Config:
        env_file = ".env"
        env_prefix = "DATA_PREP_"


def load_config(config_path: Optional[Path] = None) -> DataPrepConfig:
    """Load configuration from file or environment"""
    if config_path and config_path.exists():
        import yaml
        with open(config_path) as f:
            config_dict = yaml.safe_load(f)
        return DataPrepConfig(**config_dict)
    return DataPrepConfig()


def save_config(config: DataPrepConfig, output_path: Path):
    """Save configuration to file"""
    import yaml
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(config.dict(), f, default_flow_style=False, allow_unicode=True)
