"""
FAISS Backend Implementation
=============================
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
import pickle
from pathlib import Path

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    faiss = None

from .base import VectorStoreBackend
from ..models import SearchResult, VectorStoreConfig

logger = logging.getLogger(__name__)


class FAISSBackend(VectorStoreBackend):
    """
    FAISS vector store backend
    
    Features:
    - Fast similarity search
    - Multiple index types
    - GPU support
    - Efficient for large-scale
    """
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize FAISS backend"""
        super().__init__(config)
        
        if not HAS_FAISS:
            raise ImportError(
                "faiss is not installed. "
                "Install it with: pip install faiss-cpu or faiss-gpu"
            )
        
        self.index = None
        self.id_map = {}  # Map index position to ID
        self.metadata_map = {}  # Map ID to metadata
        self.next_idx = 0
    
    async def initialize(self) -> None:
        """Initialize FAISS index"""
        logger.info(f"Initializing FAISS backend: {self.collection_name}")
        
        # Create index based on type
        if self.config.faiss_index_type == 'Flat':
            # Exact search
            if self.config.distance_metric == 'cosine':
                self.index = faiss.IndexFlatIP(self.config.dimension)  # Inner product
            else:
                self.index = faiss.IndexFlatL2(self.config.dimension)  # L2 distance
        
        elif self.config.faiss_index_type == 'IVF':
            # Inverted file index (faster but approximate)
            quantizer = faiss.IndexFlatL2(self.config.dimension)
            self.index = faiss.IndexIVFFlat(
                quantizer,
                self.config.dimension,
                self.config.faiss_nlist
            )
            # Need to train IVF index
            self.index.nprobe = self.config.faiss_nprobe
        
        else:
            raise ValueError(f"Unknown FAISS index type: {self.config.faiss_index_type}")
        
        logger.info(f"FAISS index created: {self.config.faiss_index_type}")
    
    async def add_vectors(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add vectors to FAISS index"""
        if self.index is None:
            raise RuntimeError("Backend not initialized. Call initialize() first.")
        
        # Ensure embeddings are float32
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        
        # Normalize for cosine similarity
        if self.config.distance_metric == 'cosine':
            faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings)
        
        # Update mappings
        for i, doc_id in enumerate(ids):
            idx = self.next_idx + i
            self.id_map[idx] = doc_id
            if metadata and i < len(metadata):
                self.metadata_map[doc_id] = metadata[i]
        
        self.next_idx += len(ids)
        logger.debug(f"Added {len(ids)} vectors to FAISS index")
    
    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search FAISS index"""
        if self.index is None:
            raise RuntimeError("Backend not initialized. Call initialize() first.")
        
        # Ensure query is float32 and 2D
        query = query_embedding.astype(np.float32).reshape(1, -1)
        
        # Normalize for cosine similarity
        if self.config.distance_metric == 'cosine':
            faiss.normalize_L2(query)
        
        # Search
        distances, indices = self.index.search(query, top_k)
        
        # Convert to SearchResult
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            doc_id = self.id_map.get(int(idx))
            if doc_id is None:
                continue
            
            # Apply metadata filter if provided
            if filter:
                metadata = self.metadata_map.get(doc_id, {})
                if not all(metadata.get(k) == v for k, v in filter.items()):
                    continue
            
            results.append(SearchResult(
                id=doc_id,
                score=float(distances[0][i]),
                metadata=self.metadata_map.get(doc_id, {})
            ))
        
        return results
    
    async def delete(self, ids: List[str]) -> None:
        """Delete vectors (FAISS doesn't support deletion, need rebuild)"""
        logger.warning("FAISS doesn't support deletion. Consider rebuilding index.")
        # Remove from metadata
        for doc_id in ids:
            self.metadata_map.pop(doc_id, None)
    
    async def get(self, ids: List[str]) -> List[SearchResult]:
        """Get vectors by IDs (limited support in FAISS)"""
        results = []
        for doc_id in ids:
            if doc_id in self.metadata_map:
                results.append(SearchResult(
                    id=doc_id,
                    score=1.0,
                    metadata=self.metadata_map[doc_id]
                ))
        return results
    
    async def count(self) -> int:
        """Get total number of vectors"""
        if self.index is None:
            return 0
        return self.index.ntotal
    
    async def backup(self, path: str) -> str:
        """Backup FAISS index"""
        backup_path = Path(path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save index
        index_path = str(backup_path.with_suffix('.index'))
        faiss.write_index(self.index, index_path)
        
        # Save mappings
        mappings_path = str(backup_path.with_suffix('.pkl'))
        with open(mappings_path, 'wb') as f:
            pickle.dump({
                'id_map': self.id_map,
                'metadata_map': self.metadata_map,
                'next_idx': self.next_idx
            }, f)
        
        logger.info(f"FAISS index backed up to {index_path}")
        return index_path
    
    async def restore(self, path: str) -> None:
        """Restore FAISS index from backup"""
        backup_path = Path(path)
        
        # Load index
        index_path = str(backup_path.with_suffix('.index'))
        self.index = faiss.read_index(index_path)
        
        # Load mappings
        mappings_path = str(backup_path.with_suffix('.pkl'))
        with open(mappings_path, 'rb') as f:
            data = pickle.load(f)
            self.id_map = data['id_map']
            self.metadata_map = data['metadata_map']
            self.next_idx = data['next_idx']
        
        logger.info(f"FAISS index restored from {index_path}")
    
    async def close(self) -> None:
        """Close FAISS backend"""
        self.index = None
        logger.info("FAISS backend closed")
