# 🚀 نقشه عملیاتی بهبود معماری Graph

**تاریخ**: 2026-02-24  
**هدف**: رسیدن از 82/100 به 95/100  
**زمان**: 20 هفته (5 ماه)

---

## 📋 Phase 1: Quick Wins (هفته 1-2)

**هدف**: 82 → 85 (+3 امتیاز)  
**ریسک**: LOW  
**تیم**: 1 engineer

### Task 1.1: Query Optimization (3 روز)

```cypher
-- Add missing indexes
CREATE INDEX verdict_id IF NOT EXISTS 
FOR (v:Verdict) ON (v.verdict_id);

CREATE INDEX article_label IF NOT EXISTS 
FOR (a:LawArticle) ON (a.label);

CREATE INDEX document_embedding IF NOT EXISTS 
FOR (d:Document) ON (d.embedding);

CREATE INDEX case_id IF NOT EXISTS 
FOR (c:Case) ON (c.case_id);

-- Add composite indexes
CREATE INDEX verdict_court_date IF NOT EXISTS 
FOR (v:Verdict) ON (v.court_level, v.date);
```

**فایل**: `mahoun/graph/neo4j/schema.py`

```python
def create_performance_indexes(self):
    """Create indexes for performance"""
    indexes = [
        "CREATE INDEX verdict_id IF NOT EXISTS FOR (v:Verdict) ON (v.verdict_id)",
        "CREATE INDEX article_label IF NOT EXISTS FOR (a:LawArticle) ON (a.label)",
        "CREATE INDEX document_embedding IF NOT EXISTS FOR (d:Document) ON (d.embedding)",
        "CREATE INDEX case_id IF NOT EXISTS FOR (c:Case) ON (c.case_id)",
        "CREATE INDEX verdict_court_date IF NOT EXISTS FOR (v:Verdict) ON (v.court_level, v.date)",
    ]
    
    for index in indexes:
        try:
            self.conn.execute_query(index)
            logger.info(f"Created index: {index}")
        except Exception as e:
            logger.warning(f"Index creation failed: {e}")
```

**تاثیر**: -50% query latency  
**تست**: `pytest tests/test_graph_performance.py -k test_indexed_queries`

---

### Task 1.2: Monitoring Enhancement (2 روز)

**فایل**: `mahoun/graph/monitoring.py`

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
query_counter = Counter(
    'graph_queries_total',
    'Total graph queries',
    ['operation', 'status']
)

query_latency = Histogram(
    'graph_query_latency_seconds',
    'Query latency in seconds',
    ['operation'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
)

graph_size = Gauge(
    'graph_size_total',
    'Total graph size',
    ['type']  # nodes, edges
)

cache_hit_rate = Gauge(
    'graph_cache_hit_rate',
    'Cache hit rate'
)

class GraphMetrics:
    @staticmethod
    def record_query(operation: str, duration: float, success: bool):
        status = 'success' if success else 'error'
        query_counter.labels(operation=operation, status=status).inc()
        query_latency.labels(operation=operation).observe(duration)
    
    @staticmethod
    def update_graph_size(nodes: int, edges: int):
        graph_size.labels(type='nodes').set(nodes)
        graph_size.labels(type='edges').set(edges)
    
    @staticmethod
    def update_cache_hit_rate(rate: float):
        cache_hit_rate.set(rate)
```

**Integration در GraphQueryService**:

```python
def query(self, query: str, params: Dict, **kwargs):
    start = time.time()
    operation = self._extract_operation(query)  # MATCH, CREATE, etc.
    
    try:
        result = self._execute_query(query, params)
        duration = time.time() - start
        GraphMetrics.record_query(operation, duration, success=True)
        return result
    except Exception as e:
        duration = time.time() - start
        GraphMetrics.record_query(operation, duration, success=False)
        raise
```

**تاثیر**: +50% observability  
**تست**: Manual verification در Grafana

---

### Task 1.3: Slow Query Logging (1 روز)

**فایل**: `mahoun/graph/graph_query_service.py`

```python
class GraphQueryService:
    def __init__(self, config: GraphQueryConfig):
        # ... existing code ...
        self.slow_query_threshold = config.slow_query_threshold_ms or 1000
        self.slow_query_logger = logging.getLogger('mahoun.graph.slow_queries')
    
    def _log_slow_query(self, query: str, params: Dict, duration_ms: float):
        if duration_ms > self.slow_query_threshold:
            self.slow_query_logger.warning(
                f"Slow query detected",
                extra={
                    'duration_ms': duration_ms,
                    'query': query[:200],  # Truncate
                    'params': str(params)[:100],
                    'threshold_ms': self.slow_query_threshold
                }
            )
```

**تاثیر**: Easier debugging  
**تست**: `pytest tests/test_slow_query_logging.py`

---

### Task 1.4: Documentation Sprint (3 روز)

**فایل‌های جدید**:
1. `docs/graph/ARCHITECTURE.md` - معماری کلی
2. `docs/graph/API.md` - API documentation
3. `docs/graph/DEPLOYMENT.md` - راهنمای deployment
4. `docs/graph/TROUBLESHOOTING.md` - راهنمای عیب‌یابی

**محتوای ARCHITECTURE.md**:
```markdown
# Graph Architecture

## Overview
4-layer architecture: Storage → Query → Intelligence → Optimization

## Components
- UltraGraphBuilder: Document ingestion
- GraphQueryService: Query execution
- UltraGAT: GNN models
- GraphOptimizer: Graph optimization

## Data Flow
Document → Entities → Relations → Graph → Embeddings → Index

## Scalability
Current: 1M nodes
Target: 100M nodes (requires partitioning)
```

**تاثیر**: +100% developer productivity  
**تست**: Review با تیم

---

## 📈 Phase 2: Performance (هفته 3-6)

**هدف**: 85 → 88 (+3 امتیاز)  
**ریسک**: MEDIUM  
**تیم**: 2 engineers

### Task 2.1: Batch Operations (5 روز)

**فایل**: `mahoun/graph/batch_operations.py`

```python
from typing import List, Dict, Any
import asyncio

class BatchGraphOperations:
    def __init__(self, query_service: GraphQueryService):
        self.query_service = query_service
        self.batch_size = 100
    
    async def batch_insert_nodes(
        self,
        nodes: List[Dict[str, Any]],
        label: str
    ) -> List[str]:
        """Insert nodes in batches"""
        node_ids = []
        
        for i in range(0, len(nodes), self.batch_size):
            batch = nodes[i:i + self.batch_size]
            
            query = f"""
            UNWIND $nodes AS node
            CREATE (n:{label})
            SET n = node
            RETURN n.id AS node_id
            """
            
            result = await self.query_service.query_async(
                query,
                {'nodes': batch}
            )
            
            node_ids.extend([r['node_id'] for r in result.results])
        
        return node_ids
    
    async def batch_create_relationships(
        self,
        relationships: List[Dict[str, Any]],
        rel_type: str
    ) -> int:
        """Create relationships in batches"""
        created = 0
        
        for i in range(0, len(relationships), self.batch_size):
            batch = relationships[i:i + self.batch_size]
            
            query = f"""
            UNWIND $rels AS rel
            MATCH (a {{id: rel.from_id}})
            MATCH (b {{id: rel.to_id}})
            CREATE (a)-[r:{rel_type}]->(b)
            SET r = rel.properties
            RETURN count(r) AS count
            """
            
            result = await self.query_service.query_async(
                query,
                {'rels': batch}
            )
            
            created += result.results[0]['count']
        
        return created
    
    async def batch_get_embeddings(
        self,
        texts: List[str],
        model: Any
    ) -> np.ndarray:
        """Generate embeddings in batches"""
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            embeddings = await asyncio.to_thread(
                model.encode,
                batch,
                show_progress_bar=False
            )
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings)
```

**Integration در UltraGraphBuilder**:

```python
async def build_graph_async(self, documents: List[Dict]):
    batch_ops = BatchGraphOperations(self.query_service)
    
    # Extract all entities
    all_entities = []
    for doc in documents:
        entities = self.extract_entities(doc['text'])
        all_entities.extend(entities)
    
    # Batch insert
    await batch_ops.batch_insert_nodes(all_entities, 'Entity')
    
    # Extract all relations
    all_relations = []
    for doc in documents:
        relations = self.extract_relations(doc['text'])
        all_relations.extend(relations)
    
    # Batch create
    await batch_ops.batch_create_relationships(all_relations, 'RELATES_TO')
```

**تاثیر**: +50% throughput  
**تست**: `pytest tests/test_batch_operations.py`

---

### Task 2.2: Multi-Level Caching (4 روز)

**فایل**: `mahoun/graph/caching.py`

```python
from typing import Optional, Any
import redis
import pickle
import hashlib

class MultiLevelCache:
    def __init__(
        self,
        l1_size: int = 1000,
        l1_ttl: int = 300,
        redis_url: Optional[str] = None,
        l2_ttl: int = 3600
    ):
        # L1: In-memory LRU cache
        self.l1_cache = QueryCache(max_size=l1_size, ttl_seconds=l1_ttl)
        
        # L2: Redis cache
        self.l2_cache = redis.from_url(redis_url) if redis_url else None
        self.l2_ttl = l2_ttl
    
    def get(self, key: str) -> Optional[Any]:
        # Try L1 first
        value = self.l1_cache.get_by_key(key)
        if value is not None:
            return value
        
        # Try L2
        if self.l2_cache:
            value = self.l2_cache.get(key)
            if value:
                value = pickle.loads(value)
                # Promote to L1
                self.l1_cache.set_by_key(key, value)
                return value
        
        return None
    
    def set(self, key: str, value: Any):
        # Set in L1
        self.l1_cache.set_by_key(key, value)
        
        # Set in L2
        if self.l2_cache:
            self.l2_cache.setex(
                key,
                self.l2_ttl,
                pickle.dumps(value)
            )
    
    def invalidate(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        # Clear L1
        self.l1_cache.clear()
        
        # Clear L2
        if self.l2_cache:
            for key in self.l2_cache.scan_iter(match=pattern):
                self.l2_cache.delete(key)
```

**تاثیر**: +30% cache hit rate  
**تست**: `pytest tests/test_multi_level_cache.py`

---

### Task 2.3: Async Everywhere (6 روز)

**تغییرات در GraphQueryService**:

```python
class GraphQueryService:
    async def query_async(self, query: str, params: Dict) -> QueryResult:
        # Already implemented ✅
        pass
    
    async def multi_hop_traversal_async(self, ...):
        # Already implemented ✅
        pass
    
    async def batch_query_async(self, ...):
        # Already implemented ✅
        pass
```

**تغییرات در UltraGraphBuilder**:

```python
class UltraGraphBuilder:
    async def build_graph_async(self, documents: List[Dict]):
        # Parallel processing
        tasks = [
            self._process_document_async(doc)
            for doc in documents
        ]
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def _process_document_async(self, doc: Dict):
        # Extract entities
        entities = await asyncio.to_thread(
            self.extract_entities,
            doc['text']
        )
        
        # Generate embeddings
        embeddings = await asyncio.to_thread(
            self.model.encode,
            [e['text'] for e in entities]
        )
        
        # Insert to graph
        await self.query_service.batch_insert_nodes_async(entities)
        
        return {'doc_id': doc['id'], 'entity_count': len(entities)}
```

**تاثیر**: +40% throughput  
**تست**: `pytest tests/test_async_operations.py`

---

## 🔄 Phase 3: Scalability (هفته 7-14)

**هدف**: 88 → 92 (+4 امتیاز)  
**ریسک**: HIGH  
**تیم**: 3 engineers

### Task 3.1: Graph Partitioning (3 هفته)

**فایل**: `mahoun/graph/partitioning.py`

```python
from enum import Enum
from typing import List, Dict, Any
import hashlib

class PartitionStrategy(Enum):
    HASH = "hash"
    RANGE = "range"
    DOMAIN = "domain"

class GraphPartitioner:
    def __init__(
        self,
        num_partitions: int,
        strategy: PartitionStrategy = PartitionStrategy.DOMAIN
    ):
        self.num_partitions = num_partitions
        self.strategy = strategy
        
        # Partition connections
        self.partitions: List[Neo4jConnection] = []
        for i in range(num_partitions):
            conn = Neo4jConnection(
                uri=f"bolt://neo4j-{i}:7687",
                user="neo4j",
                password="password"
            )
            self.partitions.append(conn)
    
    def get_partition(self, key: str) -> int:
        """Determine partition for a key"""
        if self.strategy == PartitionStrategy.HASH:
            return self._hash_partition(key)
        elif self.strategy == PartitionStrategy.DOMAIN:
            return self._domain_partition(key)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def _hash_partition(self, key: str) -> int:
        """Hash-based partitioning"""
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return hash_value % self.num_partitions
    
    def _domain_partition(self, key: str) -> int:
        """Domain-based partitioning (e.g., by case_id prefix)"""
        # Example: case_id format: "CASE-2024-001"
        if key.startswith("CASE-"):
            year = int(key.split("-")[1])
            return year % self.num_partitions
        else:
            return self._hash_partition(key)
    
    async def query_partition(
        self,
        partition_id: int,
        query: str,
        params: Dict
    ) -> List[Dict]:
        """Query a specific partition"""
        conn = self.partitions[partition_id]
        return await conn.execute_query_async(query, params)
    
    async def query_all_partitions(
        self,
        query: str,
        params: Dict
    ) -> List[Dict]:
        """Query all partitions and merge results"""
        tasks = [
            self.query_partition(i, query, params)
            for i in range(self.num_partitions)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Merge results
        merged = []
        for result in results:
            merged.extend(result)
        
        return merged
    
    async def cross_partition_query(
        self,
        start_key: str,
        end_key: str,
        query: str
    ) -> List[Dict]:
        """Handle queries spanning multiple partitions"""
        start_partition = self.get_partition(start_key)
        end_partition = self.get_partition(end_key)
        
        if start_partition == end_partition:
            # Same partition - simple query
            return await self.query_partition(start_partition, query, {})
        else:
            # Cross-partition - need distributed query
            return await self._distributed_query(
                [start_partition, end_partition],
                query
            )
```

**تاثیر**: 10x scalability  
**تست**: `pytest tests/test_graph_partitioning.py`

---

### Task 3.2: ACID Transactions (2 هفته)

**فایل**: `mahoun/graph/transactions.py`

```python
from contextlib import contextmanager
from typing import Optional, Callable
import uuid

class Transaction:
    def __init__(self, tx_id: str, connection: Neo4jConnection):
        self.tx_id = tx_id
        self.connection = connection
        self.neo4j_tx = None
        self.savepoints: Dict[str, Any] = {}
    
    def begin(self):
        """Begin transaction"""
        self.neo4j_tx = self.connection.driver.session().begin_transaction()
    
    def commit(self):
        """Commit transaction"""
        if self.neo4j_tx:
            self.neo4j_tx.commit()
    
    def rollback(self):
        """Rollback transaction"""
        if self.neo4j_tx:
            self.neo4j_tx.rollback()
    
    def savepoint(self, name: str):
        """Create savepoint"""
        # Neo4j doesn't support savepoints natively
        # We simulate by storing state
        self.savepoints[name] = {
            'timestamp': time.time(),
            'operations': []
        }
    
    def rollback_to_savepoint(self, name: str):
        """Rollback to savepoint"""
        if name in self.savepoints:
            # Rollback operations after savepoint
            pass

class GraphTransactionManager:
    def __init__(self, connection: Neo4jConnection):
        self.connection = connection
        self.active_transactions: Dict[str, Transaction] = {}
    
    def begin_transaction(self) -> Transaction:
        """Begin new transaction"""
        tx_id = str(uuid.uuid4())
        tx = Transaction(tx_id, self.connection)
        tx.begin()
        self.active_transactions[tx_id] = tx
        return tx
    
    @contextmanager
    def transaction(self):
        """Context manager for transactions"""
        tx = self.begin_transaction()
        try:
            yield tx
            tx.commit()
        except Exception as e:
            tx.rollback()
            raise
        finally:
            del self.active_transactions[tx.tx_id]
    
    async def distributed_transaction(
        self,
        partitions: List[int],
        operations: List[Callable]
    ):
        """2-Phase Commit for distributed transactions"""
        # Phase 1: Prepare
        prepared = []
        for partition_id, operation in zip(partitions, operations):
            try:
                result = await operation()
                prepared.append((partition_id, result))
            except Exception as e:
                # Rollback all
                for p_id, _ in prepared:
                    await self._rollback_partition(p_id)
                raise
        
        # Phase 2: Commit
        for partition_id, result in prepared:
            await self._commit_partition(partition_id)
```

**تاثیر**: Data consistency guarantee  
**تست**: `pytest tests/test_transactions.py`

---

## 🧠 Phase 4: Intelligence (هفته 15-20)

**هدف**: 92 → 95 (+3 امتیاز)  
**ریسک**: MEDIUM  
**تیم**: 2 engineers

### Task 4.1: Advanced GNN (2 هفته)

**فایل**: `mahoun/graph/advanced_gnn.py`

```python
import torch
import torch.nn as nn

class GraphSAGE(nn.Module):
    """GraphSAGE for inductive learning"""
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        super().__init__()
        self.conv1 = SAGEConv(input_dim, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, output_dim)
    
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        return x

class HeterogeneousGNN(nn.Module):
    """RGCN for heterogeneous graphs"""
    def __init__(self, num_node_types: int, num_edge_types: int):
        super().__init__()
        self.node_embeddings = nn.ModuleList([
            nn.Embedding(1000, 128)
            for _ in range(num_node_types)
        ])
        
        self.rgcn = RGCNConv(128, 128, num_edge_types)
    
    def forward(self, x, edge_index, edge_type):
        x = self.rgcn(x, edge_index, edge_type)
        return x
```

**تاثیر**: +20% accuracy  
**تست**: `pytest tests/test_advanced_gnn.py`

---

### Task 4.2: AutoML (2 هفته)

**فایل**: `mahoun/graph/automl.py`

```python
from optuna import create_study, Trial

class GNNAutoML:
    def __init__(self, train_data, val_data):
        self.train_data = train_data
        self.val_data = val_data
    
    def objective(self, trial: Trial) -> float:
        # Hyperparameters
        hidden_dim = trial.suggest_int('hidden_dim', 64, 512)
        num_layers = trial.suggest_int('num_layers', 2, 4)
        dropout = trial.suggest_float('dropout', 0.1, 0.5)
        lr = trial.suggest_loguniform('lr', 1e-4, 1e-2)
        
        # Build model
        model = UltraGAT(
            config=GATConfig(
                hidden_dim=hidden_dim,
                num_layers=num_layers,
                dropout=dropout
            ),
            input_dim=384
        )
        
        # Train
        trainer = UltraGATTrainer(model, self.train_data)
        trainer.train(epochs=50, lr=lr)
        
        # Evaluate
        val_loss, val_acc = trainer.evaluate(self.val_data)
        
        return val_acc
    
    def search(self, n_trials: int = 100):
        study = create_study(direction='maximize')
        study.optimize(self.objective, n_trials=n_trials)
        
        return study.best_params
```

**تاثیر**: Optimal hyperparameters  
**تست**: `pytest tests/test_automl.py`

---

### Task 4.3: Online Learning (2 هفته)

**فایل**: `mahoun/graph/online_learning.py`

```python
class OnlineGNNLearner:
    def __init__(self, model: UltraGAT):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
        self.buffer = []
        self.buffer_size = 1000
    
    def update(self, new_data: Dict):
        """Incremental update with new data"""
        # Add to buffer
        self.buffer.append(new_data)
        
        # Train when buffer is full
        if len(self.buffer) >= self.buffer_size:
            self._train_on_buffer()
            self.buffer = []
    
    def _train_on_buffer(self):
        """Train on buffered data"""
        # Convert buffer to batch
        batch = self._buffer_to_batch(self.buffer)
        
        # Forward pass
        output = self.model(batch.x, batch.edge_index)
        loss = F.cross_entropy(output, batch.y)
        
        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
```

**تاثیر**: Adaptive model  
**تست**: `pytest tests/test_online_learning.py`

---

## 📊 تخمین منابع

### تیم مورد نیاز

| Phase | Engineers | Weeks | Person-Weeks |
|-------|-----------|-------|--------------|
| Phase 1 | 1 | 2 | 2 |
| Phase 2 | 2 | 4 | 8 |
| Phase 3 | 3 | 8 | 24 |
| Phase 4 | 2 | 6 | 12 |
| **Total** | - | **20** | **46** |

### بودجه تخمینی

- Senior Engineer: $150/hour
- 46 person-weeks × 40 hours/week = 1840 hours
- 1840 hours × $150/hour = **$276,000**

### Infrastructure

- Neo4j Enterprise (3 nodes): $50k/year
- Redis Cluster: $10k/year
- Monitoring (Grafana Cloud): $5k/year
- **Total**: $65k/year

---

## ✅ Success Metrics

### Performance

- [ ] Query latency < 10ms (p95)
- [ ] Throughput > 1000 qps
- [ ] Cache hit rate > 80%
- [ ] Error rate < 0.1%

### Scalability

- [ ] Support 100M nodes
- [ ] Support 1B edges
- [ ] Linear scaling با partitions
- [ ] 99.9% availability

### Quality

- [ ] Test coverage > 80%
- [ ] Zero critical bugs
- [ ] Documentation complete
- [ ] Security audit passed

---

## 🎯 نتیجه‌گیری

این نقشه عملیاتی مسیر واضحی برای رسیدن از 82/100 به 95/100 ارائه می‌دهد.

**کلید موفقیت**:
1. شروع با Quick Wins
2. تمرکز بر Performance
3. سرمایه‌گذاری در Scalability
4. بهبود مستمر Intelligence

**ریسک‌های اصلی**:
- Phase 3 (Scalability) پیچیده است
- نیاز به تست extensive
- احتمال تاخیر در timeline

**توصیه**: شروع فوری با Phase 1 (این هفته!)

