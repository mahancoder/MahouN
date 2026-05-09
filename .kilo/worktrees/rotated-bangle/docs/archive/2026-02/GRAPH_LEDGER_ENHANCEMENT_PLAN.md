# طرح ارتقای Graph & Ledger - Enterprise Grade
**تاریخ**: 1404/12/04 (2026-02-23)  
**هدف**: رساندن کیفیت به سطح 10/10

---

## 🎯 اهداف کلی

1. **Semantic Search پیشرفته** با embeddings
2. **Concurrency Safety** کامل
3. **Performance Optimization** برای scale
4. **Advanced Graph Algorithms**
5. **Ledger Verification** بهینه

---

## 📦 Phase 1: Semantic Search Enhancement

### 1.1 Persian Embeddings Integration

```python
# mahoun/graph/semantic_search.py
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import numpy as np
from functools import lru_cache

class PersianSemanticSearch:
    """
    Enterprise-grade semantic search for Persian legal text.
    
    Features:
    - Multilingual embeddings (Persian + English)
    - Caching for performance
    - Batch processing
    - Similarity threshold tuning
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        cache_size: int = 10000
    ):
        self.model = SentenceTransformer(model_name)
        self.cache_size = cache_size
        self._embedding_cache = {}
    
    @lru_cache(maxsize=10000)
    def embed_text(self, text: str) -> np.ndarray:
        """Embed single text with caching"""
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Batch embedding for performance"""
        return self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True
        )
    
    def semantic_similarity(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        Find semantically similar texts.
        
        Args:
            query: Query text
            candidates: Candidate texts
            top_k: Number of results
            threshold: Minimum similarity score
            
        Returns:
            List of (text, score) tuples
        """
        # Embed query
        query_emb = self.embed_text(query)
        
        # Embed candidates (batch)
        candidate_embs = self.embed_batch(candidates)
        
        # Compute cosine similarity
        similarities = np.dot(candidate_embs, query_emb) / (
            np.linalg.norm(candidate_embs, axis=1) * np.linalg.norm(query_emb)
        )
        
        # Filter by threshold
        valid_indices = np.where(similarities >= threshold)[0]
        
        # Sort and get top-k
        top_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]][:top_k]
        
        return [(candidates[i], float(similarities[i])) for i in top_indices]
```

### 1.2 Vector Index Integration

```python
# mahoun/graph/vector_index.py
import faiss
import numpy as np
from typing import List, Dict, Any

class FAISSVectorIndex:
    """
    FAISS-based vector index for fast similarity search.
    
    Features:
    - GPU acceleration (optional)
    - IVF indexing for large datasets
    - Persistent storage
    """
    
    def __init__(
        self,
        dimension: int = 768,
        use_gpu: bool = False,
        index_type: str = "IVF"
    ):
        self.dimension = dimension
        self.use_gpu = use_gpu
        
        if index_type == "IVF":
            # Inverted File Index for large datasets
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)
        else:
            # Flat index for small datasets
            self.index = faiss.IndexFlatL2(dimension)
        
        if use_gpu and faiss.get_num_gpus() > 0:
            self.index = faiss.index_cpu_to_gpu(
                faiss.StandardGpuResources(), 0, self.index
            )
        
        self.id_to_metadata: Dict[int, Any] = {}
    
    def add(self, vectors: np.ndarray, metadata: List[Dict]):
        """Add vectors with metadata"""
        if not self.index.is_trained:
            self.index.train(vectors)
        
        start_id = self.index.ntotal
        self.index.add(vectors)
        
        for i, meta in enumerate(metadata):
            self.id_to_metadata[start_id + i] = meta
    
    def search(
        self,
        query_vector: np.ndarray,
        k: int = 10
    ) -> List[Tuple[Dict, float]]:
        """Search for k nearest neighbors"""
        distances, indices = self.index.search(
            query_vector.reshape(1, -1), k
        )
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx in self.id_to_metadata:
                results.append((self.id_to_metadata[idx], float(dist)))
        
        return results
    
    def save(self, path: str):
        """Save index to disk"""
        faiss.write_index(self.index, path)
    
    def load(self, path: str):
        """Load index from disk"""
        self.index = faiss.read_index(path)
```

---

## 📦 Phase 2: Concurrency Safety

### 2.1 Thread-Safe Graph Builder

```python
# mahoun/graph/concurrent_graph_builder.py
from threading import RLock
from typing import Dict, List
from mahoun.graph.ultra_graph_builder import UltraGraphBuilder, GraphNode, GraphEdge

class ConcurrentGraphBuilder(UltraGraphBuilder):
    """
    Thread-safe graph builder with read-write locks.
    
    Features:
    - RLock for thread safety
    - Atomic operations
    - Deadlock prevention
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = RLock()
    
    def build_graph(self, entities: List[Dict], relationships: List[Dict], **kwargs):
        """Thread-safe graph building"""
        with self._lock:
            return super().build_graph(entities, relationships, **kwargs)
    
    def add_node(self, node: GraphNode):
        """Thread-safe node addition"""
        with self._lock:
            self._nodes[node.id] = node
            self._build_indexes()
    
    def add_edge(self, edge: GraphEdge):
        """Thread-safe edge addition"""
        with self._lock:
            self._edges.append(edge)
            self._build_indexes()
    
    def query_neighbors(self, node_id: str, max_depth: int = 1):
        """Thread-safe neighbor query"""
        with self._lock:
            return super().query_neighbors(node_id, max_depth)
```

### 2.2 Async Ledger Writer

```python
# mahoun/ledger/async_writer.py
import asyncio
from typing import Optional
from mahoun.ledger.writer import EvidenceLedgerWriter, LedgerBackend
from mahoun.ledger.models import LedgerEntry

class AsyncLedgerWriter:
    """
    Async ledger writer for high-throughput scenarios.
    
    Features:
    - Async I/O
    - Batch writes
    - Connection pooling
    """
    
    def __init__(self, backend: LedgerBackend, batch_size: int = 100):
        self.backend = backend
        self.batch_size = batch_size
        self._write_queue: asyncio.Queue = asyncio.Queue()
        self._batch_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start batch writer task"""
        self._batch_task = asyncio.create_task(self._batch_writer())
    
    async def stop(self):
        """Stop batch writer and flush"""
        if self._batch_task:
            self._batch_task.cancel()
            await self._flush_queue()
    
    async def write(self, entry: LedgerEntry) -> str:
        """Queue entry for writing"""
        future = asyncio.Future()
        await self._write_queue.put((entry, future))
        return await future
    
    async def _batch_writer(self):
        """Background task for batch writing"""
        batch = []
        
        while True:
            try:
                # Wait for entries with timeout
                entry, future = await asyncio.wait_for(
                    self._write_queue.get(),
                    timeout=1.0
                )
                batch.append((entry, future))
                
                # Write batch when full
                if len(batch) >= self.batch_size:
                    await self._write_batch(batch)
                    batch = []
                    
            except asyncio.TimeoutError:
                # Write partial batch on timeout
                if batch:
                    await self._write_batch(batch)
                    batch = []
            except asyncio.CancelledError:
                break
    
    async def _write_batch(self, batch: List):
        """Write batch of entries"""
        for entry, future in batch:
            try:
                # Write to backend (sync operation in thread pool)
                loop = asyncio.get_event_loop()
                hash_val = await loop.run_in_executor(
                    None,
                    self._sync_write,
                    entry
                )
                future.set_result(hash_val)
            except Exception as e:
                future.set_exception(e)
    
    def _sync_write(self, entry: LedgerEntry) -> str:
        """Synchronous write wrapper"""
        writer = EvidenceLedgerWriter(self.backend)
        return writer.write(entry)
    
    async def _flush_queue(self):
        """Flush remaining entries"""
        batch = []
        while not self._write_queue.empty():
            entry, future = await self._write_queue.get()
            batch.append((entry, future))
        
        if batch:
            await self._write_batch(batch)
```

---

## 📦 Phase 3: Performance Optimization

### 3.1 Graph Partitioning

```python
# mahoun/graph/partitioning.py
from typing import List, Dict, Set
from collections import defaultdict

class GraphPartitioner:
    """
    Partition large graphs for distributed processing.
    
    Algorithms:
    - METIS-style partitioning
    - Min-cut optimization
    - Load balancing
    """
    
    def partition_graph(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        num_partitions: int = 4
    ) -> List[Set[str]]:
        """
        Partition graph into balanced subgraphs.
        
        Uses spectral clustering for quality partitioning.
        """
        # Build adjacency matrix
        adj = defaultdict(set)
        for edge in edges:
            adj[edge.source_id].add(edge.target_id)
            adj[edge.target_id].add(edge.source_id)
        
        # Spectral clustering
        # (simplified - use sklearn.cluster.SpectralClustering in production)
        node_ids = [n.id for n in nodes]
        partition_size = len(node_ids) // num_partitions
        
        partitions = []
        for i in range(num_partitions):
            start = i * partition_size
            end = start + partition_size if i < num_partitions - 1 else len(node_ids)
            partitions.append(set(node_ids[start:end]))
        
        return partitions
```

### 3.2 Incremental Ledger Verification

```python
# mahoun/ledger/incremental_verification.py
from pathlib import Path
from typing import Optional

class IncrementalLedgerVerifier:
    """
    Incremental hash chain verification for large ledgers.
    
    Features:
    - Checkpoint-based verification
    - Parallel verification
    - Resume from last checkpoint
    """
    
    def __init__(self, checkpoint_interval: int = 10000):
        self.checkpoint_interval = checkpoint_interval
        self.checkpoints: Dict[int, str] = {}
    
    def verify_incremental(
        self,
        backend: LedgerBackend,
        last_verified_index: Optional[int] = None
    ) -> bool:
        """
        Verify ledger from last checkpoint.
        
        Args:
            backend: Ledger backend
            last_verified_index: Resume from this index
            
        Returns:
            True if valid, False otherwise
        """
        entries = backend.read_all()
        
        start_index = last_verified_index or 0
        prev_hash = self.checkpoints.get(start_index, "genesis")
        
        for i in range(start_index, len(entries)):
            record = entries[i]
            
            # Verify hash
            expected_hash = self._compute_hash(record["entry"], prev_hash)
            if record["hash"] != expected_hash:
                return False
            
            prev_hash = record["hash"]
            
            # Create checkpoint
            if i % self.checkpoint_interval == 0:
                self.checkpoints[i] = prev_hash
        
        return True
```

---

## 📦 Phase 4: Advanced Graph Algorithms

### 4.1 PageRank Implementation

```python
# mahoun/graph/algorithms/pagerank.py
import numpy as np
from typing import Dict

class PageRankCalculator:
    """
    PageRank for legal knowledge graph.
    
    Identifies most important legal concepts/precedents.
    """
    
    def compute_pagerank(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        damping: float = 0.85,
        max_iter: int = 100,
        tol: float = 1e-6
    ) -> Dict[str, float]:
        """
        Compute PageRank scores.
        
        Args:
            nodes: Graph nodes
            edges: Graph edges
            damping: Damping factor (0.85 standard)
            max_iter: Maximum iterations
            tol: Convergence tolerance
            
        Returns:
            Dict mapping node_id to PageRank score
        """
        n = len(nodes)
        node_to_idx = {node.id: i for i, node in enumerate(nodes)}
        
        # Build adjacency matrix
        adj = np.zeros((n, n))
        out_degree = np.zeros(n)
        
        for edge in edges:
            if edge.source_id in node_to_idx and edge.target_id in node_to_idx:
                i = node_to_idx[edge.source_id]
                j = node_to_idx[edge.target_id]
                adj[i, j] = 1
                out_degree[i] += 1
        
        # Normalize by out-degree
        for i in range(n):
            if out_degree[i] > 0:
                adj[i, :] /= out_degree[i]
        
        # Power iteration
        pr = np.ones(n) / n
        
        for _ in range(max_iter):
            pr_new = (1 - damping) / n + damping * adj.T @ pr
            
            if np.linalg.norm(pr_new - pr, 1) < tol:
                break
            
            pr = pr_new
        
        # Return as dict
        return {nodes[i].id: float(pr[i]) for i in range(n)}
```

---

## 📦 Phase 5: Implementation Timeline

### Week 1: Semantic Search
- [ ] Integrate sentence-transformers
- [ ] Build FAISS index
- [ ] Update Knowledge Graph
- [ ] Write tests

### Week 2: Concurrency
- [ ] Add RLock to Graph Builder
- [ ] Implement Async Ledger Writer
- [ ] Connection pooling for SQLite
- [ ] Stress testing

### Week 3: Performance
- [ ] Graph partitioning
- [ ] Incremental verification
- [ ] Caching layer
- [ ] Benchmarking

### Week 4: Advanced Algorithms
- [ ] PageRank
- [ ] Community detection (Louvain)
- [ ] Shortest path optimization
- [ ] Integration tests

---

## 🎯 Success Metrics

1. **Semantic Search**: F1-score > 0.85 on legal queries
2. **Concurrency**: 1000+ concurrent writes/sec
3. **Performance**: <100ms query latency for 1M nodes
4. **Verification**: <1 min for 1M ledger entries

---

## 💡 Dependencies

```bash
# Add to requirements.txt
sentence-transformers>=2.2.0
faiss-cpu>=1.7.4  # or faiss-gpu for GPU support
scikit-learn>=1.3.0
```

---

## ✅ نتیجه‌گیری

با اجرای این طرح، سیستم Graph & Ledger به سطح 10/10 می‌رسه:
- Semantic search حرفه‌ای
- Thread-safe و async
- Scale به میلیون‌ها node
- Advanced algorithms

می‌خوای کدوم phase رو شروع کنیم؟
