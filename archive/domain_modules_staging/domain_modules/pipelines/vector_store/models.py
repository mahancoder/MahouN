"""
Vector Store Data Models
=========================
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
import numpy as np


@dataclass
class SearchResult:
    """Single search result from vector store"""
    id: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'score': float(self.score),
            'metadata': self.metadata,
        }
        if self.text:
            result['text'] = self.text
        if self.embedding is not None:
            result['embedding'] = self.embedding.tolist()
        return result


@dataclass
class VectorStoreConfig:
    """Configuration for vector store"""
    backend: Literal['chromadb', 'faiss', 'qdrant'] = 'chromadb'
    collection_name: str = 'default'
    dimension: int = 768
    distance_metric: Literal['cosine', 'l2', 'ip'] = 'cosine'
    
    # ChromaDB specific
    chromadb_path: Optional[str] = None
    chromadb_host: Optional[str] = None
    chromadb_port: Optional[int] = None
    
    # FAISS specific
    faiss_index_type: str = 'Flat'
    faiss_nlist: int = 100
    faiss_nprobe: int = 10
    
    # Common
    batch_size: int = 100
    enable_backup: bool = True
    backup_interval: int = 3600  # seconds


@dataclass
class BackupMetadata:
    """Metadata for vector store backup"""
    backup_id: str
    timestamp: datetime
    collection_name: str
    num_vectors: int
    dimension: int
    backend: str
    file_path: str
    size_bytes: int
    checksum: str
