#!/usr/bin/env python3
"""
Configuration Management for Advanced Chunking & Vector DB System
Centralized configuration with validation and environment support
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import os
import yaml
import json


@dataclass
class ChunkingConfig:
    """Configuration for chunking service"""
    default_strategy: str = "semantic"
    default_chunk_size: int = 512
    default_overlap: int = 50
    min_chunk_size: int = 50
    max_chunk_size: int = 2048
    quality_threshold: float = 0.7
    enable_quality_analysis: bool = True


@dataclass
class VectorStoreConfig:
    """Configuration for vector store"""
    backend: str = "chromadb"  # chromadb, faiss, qdrant
    collection_name: str = "default"
    dimension: int = 768
    distance_metric: str = "cosine"  # cosine, l2, ip
    index_type: str = "hnsw"  # hnsw, flat, ivf
    
    # ChromaDB specific
    chromadb_path: str = "./data/chromadb"
    chromadb_host: Optional[str] = None
    chromadb_port: Optional[int] = None
    
    # FAISS specific
    faiss_index_path: str = "./data/faiss"
    faiss_nlist: int = 100
    faiss_nprobe: int = 10
    
    # Qdrant specific
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None
    qdrant_grpc_port: Optional[int] = None


@dataclass
class CacheConfig:
    """Configuration for cache manager"""
    enabled: bool = True
    backend: str = "redis"  # redis, memory
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    default_ttl: int = 3600  # 1 hour
    max_memory_mb: int = 1024
    eviction_policy: str = "lru"  # lru, lfu, fifo


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service"""
    default_model: str = "sentence-transformers/all-mpnet-base-v2"
    device: str = "cuda"  # cuda, cpu, mps
    batch_size: int = 32
    max_seq_length: int = 384
    normalize_embeddings: bool = True
    use_fp16: bool = True
    cache_embeddings: bool = True
    model_cache_dir: str = "./models"


@dataclass
class RetrievalConfig:
    """Configuration for retrieval service"""
    default_top_k: int = 10
    enable_reranking: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    enable_query_expansion: bool = False
    enable_hybrid_search: bool = True
    dense_weight: float = 0.7
    sparse_weight: float = 0.3


@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing"""
    enabled: bool = True
    max_workers: int = 4
    chunk_size: int = 100
    checkpoint_interval: int = 1000
    checkpoint_dir: str = "./data/checkpoints"
    enable_progress_bar: bool = True


@dataclass
class MonitoringConfig:
    """Configuration for monitoring"""
    enabled: bool = True
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    log_level: str = "INFO"
    log_file: Optional[str] = "./logs/vector_db.log"
    metrics_retention_days: int = 30


@dataclass
class SystemConfig:
    """Main system configuration"""
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    batch_processing: BatchProcessingConfig = field(default_factory=BatchProcessingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Global settings
    environment: str = "development"  # development, staging, production
    debug: bool = False
    data_dir: str = "./data"
    temp_dir: str = "./tmp"


class ConfigManager:
    """
    Configuration manager with environment support
    
    Example:
        >>> config = ConfigManager.load_from_file("config.yaml")
        >>> config = ConfigManager.load_from_env()
        >>> config.vector_store.backend = "faiss"
        >>> ConfigManager.save_to_file(config, "config.yaml")
    """
    
    @staticmethod
    def load_from_file(path: str) -> SystemConfig:
        """
        Load configuration from file
        
        Args:
            path: Path to config file (YAML or JSON)
            
        Returns:
            SystemConfig instance
        """
        path_obj = Path(path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, 'r') as f:
            if path.endswith('.yaml') or path.endswith('.yml'):
                data = yaml.safe_load(f)
            elif path.endswith('.json'):
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {path}")
        
        return ConfigManager._dict_to_config(data)
    
    @staticmethod
    def load_from_env() -> SystemConfig:
        """
        Load configuration from environment variables
        
        Environment variables should be prefixed with VECTOR_DB_
        Example: VECTOR_DB_CHUNKING_DEFAULT_STRATEGY=semantic
        
        Returns:
            SystemConfig instance
        """
        config = SystemConfig()
        
        # Chunking
        config.chunking.default_strategy = os.getenv(
            'VECTOR_DB_CHUNKING_DEFAULT_STRATEGY',
            config.chunking.default_strategy
        )
        config.chunking.default_chunk_size = int(os.getenv(
            'VECTOR_DB_CHUNKING_DEFAULT_CHUNK_SIZE',
            config.chunking.default_chunk_size
        ))
        
        # Vector Store
        config.vector_store.backend = os.getenv(
            'VECTOR_DB_BACKEND',
            config.vector_store.backend
        )
        config.vector_store.chromadb_path = os.getenv(
            'VECTOR_DB_CHROMADB_PATH',
            config.vector_store.chromadb_path
        )
        
        # Cache
        config.cache.enabled = os.getenv(
            'VECTOR_DB_CACHE_ENABLED',
            str(config.cache.enabled)
        ).lower() == 'true'
        config.cache.redis_host = os.getenv(
            'VECTOR_DB_REDIS_HOST',
            config.cache.redis_host
        )
        config.cache.redis_port = int(os.getenv(
            'VECTOR_DB_REDIS_PORT',
            config.cache.redis_port
        ))
        
        # Embedding
        config.embedding.default_model = os.getenv(
            'VECTOR_DB_EMBEDDING_MODEL',
            config.embedding.default_model
        )
        config.embedding.device = os.getenv(
            'VECTOR_DB_DEVICE',
            config.embedding.device
        )
        
        # Global
        config.environment = os.getenv(
            'VECTOR_DB_ENVIRONMENT',
            config.environment
        )
        config.debug = os.getenv(
            'VECTOR_DB_DEBUG',
            str(config.debug)
        ).lower() == 'true'
        
        return config
    
    @staticmethod
    def save_to_file(config: SystemConfig, path: str) -> None:
        """
        Save configuration to file
        
        Args:
            config: SystemConfig instance
            path: Path to save config file
        """
        data = ConfigManager._config_to_dict(config)
        
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            if path.endswith('.yaml') or path.endswith('.yml'):
                yaml.dump(data, f, default_flow_style=False)
            elif path.endswith('.json'):
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported config format: {path}")
    
    @staticmethod
    def _dict_to_config(data: Dict[str, Any]) -> SystemConfig:
        """Convert dictionary to SystemConfig"""
        config = SystemConfig()
        
        if 'chunking' in data:
            for key, value in data['chunking'].items():
                if hasattr(config.chunking, key):
                    setattr(config.chunking, key, value)
        
        if 'vector_store' in data:
            for key, value in data['vector_store'].items():
                if hasattr(config.vector_store, key):
                    setattr(config.vector_store, key, value)
        
        if 'cache' in data:
            for key, value in data['cache'].items():
                if hasattr(config.cache, key):
                    setattr(config.cache, key, value)
        
        if 'embedding' in data:
            for key, value in data['embedding'].items():
                if hasattr(config.embedding, key):
                    setattr(config.embedding, key, value)
        
        if 'retrieval' in data:
            for key, value in data['retrieval'].items():
                if hasattr(config.retrieval, key):
                    setattr(config.retrieval, key, value)
        
        if 'batch_processing' in data:
            for key, value in data['batch_processing'].items():
                if hasattr(config.batch_processing, key):
                    setattr(config.batch_processing, key, value)
        
        if 'monitoring' in data:
            for key, value in data['monitoring'].items():
                if hasattr(config.monitoring, key):
                    setattr(config.monitoring, key, value)
        
        # Global settings
        for key in ['environment', 'debug', 'data_dir', 'temp_dir']:
            if key in data:
                setattr(config, key, data[key])
        
        return config
    
    @staticmethod
    def _config_to_dict(config: SystemConfig) -> Dict[str, Any]:
        """Convert SystemConfig to dictionary"""
        return {
            'chunking': {
                'default_strategy': config.chunking.default_strategy,
                'default_chunk_size': config.chunking.default_chunk_size,
                'default_overlap': config.chunking.default_overlap,
                'min_chunk_size': config.chunking.min_chunk_size,
                'max_chunk_size': config.chunking.max_chunk_size,
                'quality_threshold': config.chunking.quality_threshold,
                'enable_quality_analysis': config.chunking.enable_quality_analysis,
            },
            'vector_store': {
                'backend': config.vector_store.backend,
                'collection_name': config.vector_store.collection_name,
                'dimension': config.vector_store.dimension,
                'distance_metric': config.vector_store.distance_metric,
                'index_type': config.vector_store.index_type,
                'chromadb_path': config.vector_store.chromadb_path,
                'faiss_index_path': config.vector_store.faiss_index_path,
            },
            'cache': {
                'enabled': config.cache.enabled,
                'backend': config.cache.backend,
                'redis_host': config.cache.redis_host,
                'redis_port': config.cache.redis_port,
                'redis_db': config.cache.redis_db,
                'default_ttl': config.cache.default_ttl,
                'max_memory_mb': config.cache.max_memory_mb,
                'eviction_policy': config.cache.eviction_policy,
            },
            'embedding': {
                'default_model': config.embedding.default_model,
                'device': config.embedding.device,
                'batch_size': config.embedding.batch_size,
                'max_seq_length': config.embedding.max_seq_length,
                'normalize_embeddings': config.embedding.normalize_embeddings,
                'use_fp16': config.embedding.use_fp16,
                'cache_embeddings': config.embedding.cache_embeddings,
                'model_cache_dir': config.embedding.model_cache_dir,
            },
            'retrieval': {
                'default_top_k': config.retrieval.default_top_k,
                'enable_reranking': config.retrieval.enable_reranking,
                'reranker_model': config.retrieval.reranker_model,
                'enable_query_expansion': config.retrieval.enable_query_expansion,
                'enable_hybrid_search': config.retrieval.enable_hybrid_search,
                'dense_weight': config.retrieval.dense_weight,
                'sparse_weight': config.retrieval.sparse_weight,
            },
            'batch_processing': {
                'enabled': config.batch_processing.enabled,
                'max_workers': config.batch_processing.max_workers,
                'chunk_size': config.batch_processing.chunk_size,
                'checkpoint_interval': config.batch_processing.checkpoint_interval,
                'checkpoint_dir': config.batch_processing.checkpoint_dir,
                'enable_progress_bar': config.batch_processing.enable_progress_bar,
            },
            'monitoring': {
                'enabled': config.monitoring.enabled,
                'prometheus_enabled': config.monitoring.prometheus_enabled,
                'prometheus_port': config.monitoring.prometheus_port,
                'log_level': config.monitoring.log_level,
                'log_file': config.monitoring.log_file,
                'metrics_retention_days': config.monitoring.metrics_retention_days,
            },
            'environment': config.environment,
            'debug': config.debug,
            'data_dir': config.data_dir,
            'temp_dir': config.temp_dir,
        }
    
    @staticmethod
    def get_default() -> SystemConfig:
        """Get default configuration"""
        return SystemConfig()
    
    @staticmethod
    def validate(config: SystemConfig) -> bool:
        """
        Validate configuration
        
        Args:
            config: SystemConfig to validate
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        # Validate chunking
        if config.chunking.default_chunk_size < config.chunking.min_chunk_size:
            raise ValueError("default_chunk_size must be >= min_chunk_size")
        
        if config.chunking.default_chunk_size > config.chunking.max_chunk_size:
            raise ValueError("default_chunk_size must be <= max_chunk_size")
        
        # Validate vector store
        valid_backends = ['chromadb', 'faiss', 'qdrant']
        if config.vector_store.backend not in valid_backends:
            raise ValueError(f"Invalid backend: {config.vector_store.backend}")
        
        # Validate cache
        if config.cache.enabled and config.cache.backend not in ['redis', 'memory']:
            raise ValueError(f"Invalid cache backend: {config.cache.backend}")
        
        # Validate retrieval
        if config.retrieval.dense_weight + config.retrieval.sparse_weight != 1.0:
            raise ValueError("dense_weight + sparse_weight must equal 1.0")
        
        return True


# Global config instance
_global_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get global configuration instance"""
    global _global_config
    
    if _global_config is None:
        # Try to load from file first
        config_paths = [
            'config/vector_db.yaml',
            'config/vector_db.yml',
            'vector_db_config.yaml',
            'vector_db_config.yml'
        ]
        
        for path in config_paths:
            if Path(path).exists():
                _global_config = ConfigManager.load_from_file(path)
                break
        
        # Fall back to environment variables
        if _global_config is None:
            _global_config = ConfigManager.load_from_env()
    
    return _global_config


def set_config(config: SystemConfig) -> None:
    """Set global configuration instance"""
    global _global_config
    ConfigManager.validate(config)
    _global_config = config
