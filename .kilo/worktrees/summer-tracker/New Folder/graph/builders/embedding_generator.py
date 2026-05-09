"""
Embedding Generator for Legal Knowledge Graph
=============================================

This module generates embeddings for graph nodes using BGE-M3 model.
Supports batch processing, caching, and similarity search.
"""

import logging
import asyncio
import hashlib
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingCache:
    """Cache for embeddings to avoid recomputation"""
    
    cache_dir: Path = field(default_factory=lambda: Path(".cache/embeddings"))
    max_cache_size: int = 10000
    _cache: Dict[str, List[float]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize cache directory"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._load_cache()
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        key = self._get_cache_key(text)
        return self._cache.get(key)
    
    def set(self, text: str, embedding: List[float]):
        """Store embedding in cache"""
        if len(self._cache) >= self.max_cache_size:
            # Remove oldest entries
            keys_to_remove = list(self._cache.keys())[:100]
            for key in keys_to_remove:
                del self._cache[key]
        
        key = self._get_cache_key(text)
        self._cache[key] = embedding
    
    def _load_cache(self):
        """Load cache from disk"""
        cache_file = self.cache_dir / "embeddings.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self._cache = pickle.load(f)
                logger.info(f"Loaded {len(self._cache)} embeddings from cache")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
    
    def save_cache(self):
        """Save cache to disk"""
        cache_file = self.cache_dir / "embeddings.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self._cache, f)
            logger.info(f"Saved {len(self._cache)} embeddings to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def clear(self):
        """Clear cache"""
        self._cache.clear()
        cache_file = self.cache_dir / "embeddings.pkl"
        if cache_file.exists():
            cache_file.unlink()


logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Advanced Embedding Generator
    
    Generates embeddings for text using BGE-M3 model with:
    - Caching for performance
    - Batch processing
    - Async generation
    - Similarity search
    - Multiple pooling strategies
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        batch_size: int = 100,
        dimension: int = 1024,
        device: str = "cpu",
        use_cache: bool = True,
        pooling_strategy: str = "mean",
        normalize: bool = True,
    ):
        """
        Initialize EmbeddingGenerator
        
        Args:
            model_name: Model name or path
            batch_size: Batch size for processing
            dimension: Embedding dimension
            device: Device (cpu/cuda)
            use_cache: Use caching for embeddings
            pooling_strategy: Pooling strategy (mean/max/cls)
            normalize: Normalize embeddings to unit length
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.dimension = dimension
        self.device = device
        self.pooling_strategy = pooling_strategy
        self.normalize = normalize
        self.model = None
        self.tokenizer = None
        
        # Initialize cache
        self.cache = EmbeddingCache() if use_cache else None
        
        # Statistics
        self.stats = {
            'total_generated': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }

        logger.info(
            f"EmbeddingGenerator initialized (model={model_name}, "
            f"batch_size={batch_size}, dimension={dimension}, "
            f"pooling={pooling_strategy}, cache={use_cache})"
        )

    def _load_model(self):
        """Load embedding model (lazy loading)"""
        if self.model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("Model loaded successfully")

        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def generate_embedding(self, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """
        Generate embedding for single text
        
        Args:
            text: Input text
            use_cache: Use cache if available
        
        Returns:
            Embedding vector (1024 dimensions) or None
        """
        if not text or len(text.strip()) < 5:
            return None
        
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get(text)
            if cached is not None:
                self.stats['cache_hits'] += 1
                return cached
            self.stats['cache_misses'] += 1

        # Load model if needed
        self._load_model()

        if self.model is None:
            # Fallback: random embedding
            embedding = self._generate_random_embedding()
        else:
            try:
                # Generate embedding
                embedding = self.model.encode(
                    text, 
                    convert_to_numpy=True,
                    normalize_embeddings=self.normalize
                )

                # Ensure correct dimension
                if len(embedding) != self.dimension:
                    logger.warning(
                        f"Embedding dimension mismatch: {len(embedding)} != {self.dimension}"
                    )
                    # Pad or truncate
                    if len(embedding) < self.dimension:
                        embedding = np.pad(
                            embedding, (0, self.dimension - len(embedding))
                        )
                    else:
                        embedding = embedding[: self.dimension]
                
                embedding = embedding.tolist()

            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
                embedding = self._generate_random_embedding()
        
        # Store in cache
        if use_cache and self.cache and embedding:
            self.cache.set(text, embedding)
        
        self.stats['total_generated'] += 1
        return embedding

    def generate_batch_embeddings(
        self, texts: List[str], show_progress: bool = False
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for batch of texts
        
        Args:
            texts: List of input texts
            show_progress: Show progress bar
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Load model if needed
        self._load_model()

        if self.model is None:
            # Fallback: random embeddings
            return [self._generate_random_embedding() for _ in texts]

        embeddings = []

        try:
            # Process in batches
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]

                # Filter empty texts
                valid_texts = [t for t in batch if t and len(t.strip()) >= 5]

                if not valid_texts:
                    embeddings.extend([None] * len(batch))
                    continue

                # Generate embeddings
                batch_embeddings = self.model.encode(
                    valid_texts, convert_to_numpy=True, show_progress_bar=show_progress
                )

                # Convert to list
                for emb in batch_embeddings:
                    # Ensure correct dimension
                    if len(emb) != self.dimension:
                        if len(emb) < self.dimension:
                            emb = np.pad(emb, (0, self.dimension - len(emb)))
                        else:
                            emb = emb[: self.dimension]

                    embeddings.append(emb.tolist())

            logger.info(f"Generated {len(embeddings)} embeddings")

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            # Fallback
            embeddings = [self._generate_random_embedding() for _ in texts]

        return embeddings

    def find_similar_nodes(
        self,
        query_embedding: List[float],
        node_embeddings: List[Dict],
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Find similar nodes using cosine similarity
        
        Args:
            query_embedding: Query embedding vector
            node_embeddings: List of dicts with 'id' and 'embedding'
            top_k: Number of results to return
        
        Returns:
            List of similar nodes with similarity scores
        """
        if not query_embedding or not node_embeddings:
            return []

        similarities = []

        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)

        for node in node_embeddings:
            if "embedding" not in node or not node["embedding"]:
                continue

            node_vec = np.array(node["embedding"])
            node_norm = np.linalg.norm(node_vec)

            if query_norm == 0 or node_norm == 0:
                similarity = 0.0
            else:
                # Cosine similarity
                similarity = np.dot(query_vec, node_vec) / (query_norm * node_norm)

            similarities.append(
                {"id": node.get("id"), "similarity": float(similarity), "node": node}
            )

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return similarities[:top_k]

    async def generate_embedding_async(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding asynchronously
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            embedding = await loop.run_in_executor(
                executor, self.generate_embedding, text
            )
        return embedding

    async def generate_batch_embeddings_async(
        self, texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        Generate batch embeddings asynchronously
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embedding vectors
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            embeddings = await loop.run_in_executor(
                executor, self.generate_batch_embeddings, texts
            )
        return embeddings

    def _generate_random_embedding(self) -> List[float]:
        """Generate random embedding (fallback)"""
        return np.random.randn(self.dimension).tolist()

    def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Similarity score (0-1)
        """
        if not embedding1 or not embedding2:
            return 0.0

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(similarity)


# Convenience functions
def generate_embedding(text: str, model_name: str = "BAAI/bge-m3") -> Optional[List[float]]:
    """
    Convenience function to generate embedding
    
    Args:
        text: Input text
        model_name: Model name
    
    Returns:
        Embedding vector
    """
    generator = EmbeddingGenerator(model_name=model_name)
    return generator.generate_embedding(text)


def generate_batch_embeddings(
    texts: List[str], model_name: str = "BAAI/bge-m3", batch_size: int = 100
) -> List[Optional[List[float]]]:
    """
    Convenience function to generate batch embeddings
    
    Args:
        texts: List of input texts
        model_name: Model name
        batch_size: Batch size
    
    Returns:
        List of embedding vectors
    """
    generator = EmbeddingGenerator(model_name=model_name, batch_size=batch_size)
    return generator.generate_batch_embeddings(texts)


    def generate_embeddings_for_nodes(
        self,
        nodes: List[Dict],
        text_field: str = 'content',
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Generate embeddings for graph nodes
        
        Args:
            nodes: List of node dictionaries
            text_field: Field containing text to embed
            show_progress: Show progress bar
        
        Returns:
            List of nodes with embeddings added
        """
        texts = [node.get(text_field, '') for node in nodes]
        embeddings = self.generate_batch_embeddings(texts, show_progress)
        
        # Add embeddings to nodes
        for node, embedding in zip(nodes, embeddings):
            node['embedding'] = embedding
        
        return nodes
    
    def find_similar_texts(
        self,
        query_text: str,
        candidate_texts: List[str],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find similar texts using embeddings
        
        Args:
            query_text: Query text
            candidate_texts: List of candidate texts
            top_k: Number of results
        
        Returns:
            List of (text, similarity) tuples
        """
        # Generate query embedding
        query_emb = self.generate_embedding(query_text)
        if not query_emb:
            return []
        
        # Generate candidate embeddings
        candidate_embs = self.generate_batch_embeddings(candidate_texts)
        
        # Calculate similarities
        similarities = []
        for text, emb in zip(candidate_texts, candidate_embs):
            if emb:
                sim = self.calculate_similarity(query_emb, emb)
                similarities.append((text, sim))
        
        # Sort and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def cluster_embeddings(
        self,
        embeddings: List[List[float]],
        n_clusters: int = 10,
        method: str = 'kmeans'
    ) -> List[int]:
        """
        Cluster embeddings
        
        Args:
            embeddings: List of embedding vectors
            n_clusters: Number of clusters
            method: Clustering method (kmeans/hierarchical)
        
        Returns:
            List of cluster labels
        """
        if not embeddings or len(embeddings) < n_clusters:
            return list(range(len(embeddings)))
        
        try:
            from sklearn.cluster import KMeans, AgglomerativeClustering
            
            X = np.array(embeddings)
            
            if method == 'kmeans':
                clusterer = KMeans(n_clusters=n_clusters, random_state=42)
            else:
                clusterer = AgglomerativeClustering(n_clusters=n_clusters)
            
            labels = clusterer.fit_predict(X)
            return labels.tolist()
        
        except ImportError:
            logger.warning("sklearn not installed, cannot cluster")
            return list(range(len(embeddings)))
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return list(range(len(embeddings)))
    
    def reduce_dimensions(
        self,
        embeddings: List[List[float]],
        n_components: int = 2,
        method: str = 'pca'
    ) -> List[List[float]]:
        """
        Reduce embedding dimensions for visualization
        
        Args:
            embeddings: List of embedding vectors
            n_components: Target dimensions
            method: Reduction method (pca/tsne/umap)
        
        Returns:
            List of reduced embeddings
        """
        if not embeddings:
            return []
        
        try:
            from sklearn.decomposition import PCA
            
            X = np.array(embeddings)
            
            if method == 'pca':
                reducer = PCA(n_components=n_components)
            elif method == 'tsne':
                from sklearn.manifold import TSNE
                reducer = TSNE(n_components=n_components, random_state=42)
            elif method == 'umap':
                import umap
                reducer = umap.UMAP(n_components=n_components, random_state=42)
            else:
                reducer = PCA(n_components=n_components)
            
            reduced = reducer.fit_transform(X)
            return reduced.tolist()
        
        except ImportError:
            logger.warning(f"{method} not available, using PCA")
            try:
                from sklearn.decomposition import PCA
                reducer = PCA(n_components=n_components)
                reduced = reducer.fit_transform(np.array(embeddings))
                return reduced.tolist()
            except:
                return embeddings
        except Exception as e:
            logger.error(f"Dimension reduction failed: {e}")
            return embeddings
    
    def get_statistics(self) -> Dict:
        """Get generation statistics"""
        stats = self.stats.copy()
        if self.cache:
            stats['cache_size'] = len(self.cache._cache)
            if stats['total_generated'] > 0:
                stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_generated']
        return stats
    
    def save_cache(self):
        """Save cache to disk"""
        if self.cache:
            self.cache.save_cache()
    
    def clear_cache(self):
        """Clear embedding cache"""
        if self.cache:
            self.cache.clear()
            self.stats['cache_hits'] = 0
            self.stats['cache_misses'] = 0
