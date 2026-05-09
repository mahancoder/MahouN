# راهنمای کامل Graph Partitioning برای Mahoun

**تاریخ**: 2026-02-24  
**مخاطب**: معماران سیستم و توسعه‌دهندگان

---

## 📚 فهرست مطالب

1. [مفهوم Graph Partitioning](#مفهوم)
2. [چرا نیاز داریم؟](#چرا-نیاز-داریم)
3. [استراتژی‌های Partitioning](#استراتژی‌ها)
4. [معماری پیشنهادی برای Mahoun](#معماری-mahoun)
5. [پیاده‌سازی عملی](#پیاده‌سازی)
6. [Trade-offs و چالش‌ها](#چالش‌ها)

---

## 🎯 مفهوم Graph Partitioning {#مفهوم}

### تعریف ساده
Graph Partitioning یعنی تقسیم یک گراف بزرگ به چندین بخش کوچک‌تر (partitions) به گونه‌ای که:
1. هر partition مستقل قابل پردازش باشد
2. ارتباطات بین partitions کمینه شود
3. بار کاری بین partitions متعادل باشد

### مثال ساده
فرض کن یک گراف 1 میلیون نود داری:
```
بدون Partitioning:
┌─────────────────────────────┐
│  1,000,000 nodes            │
│  در یک Neo4j instance       │
│  RAM: 64GB                  │
│  Query time: 10s            │
└─────────────────────────────┘

با Partitioning:
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ P1       │  │ P2       │  │ P3       │  │ P4       │
│ 250K     │  │ 250K     │  │ 250K     │  │ 250K     │
│ nodes    │  │ nodes    │  │ nodes    │  │ nodes    │
│ RAM: 16GB│  │ RAM: 16GB│  │ RAM: 16GB│  │ RAM: 16GB│
│ Time: 2s │  │ Time: 2s │  │ Time: 2s │  │ Time: 2s │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

---

## 🤔 چرا نیاز داریم؟ {#چرا-نیاز-داریم}

### مشکلات گراف بزرگ در Mahoun

#### 1. محدودیت حافظه
```python
# مثال: یک پرونده حقوقی بزرگ
case = {
    "documents": 10_000,      # 10K سند
    "entities": 50_000,       # 50K entity (افراد، شرکت‌ها، قراردادها)
    "facts": 200_000,         # 200K fact
    "relationships": 500_000  # 500K رابطه
}

# حافظه مورد نیاز (تخمینی):
memory_per_node = 1_KB
total_memory = (50_000 + 200_000) * 1_KB = 250 MB (فقط nodes)
total_memory_with_edges = 250_MB + (500_000 * 0.5_KB) = 500 MB

# اما با 100 پرونده همزمان:
total = 500_MB * 100 = 50 GB!
```

#### 2. کندی Query
```cypher
// Query بدون partition: باید کل گراف را جستجو کند
MATCH (e:Entity)-[r:RELATED_TO*1..5]-(f:Fact)
WHERE e.case_id IN [1, 2, 3, ..., 100]
RETURN e, r, f
// زمان: 30 ثانیه برای 100 پرونده

// Query با partition: فقط partition مربوطه
MATCH (e:Entity)-[r:RELATED_TO*1..5]-(f:Fact)
WHERE e.case_id = 42  // فقط یک پرونده
RETURN e, r, f
// زمان: 0.5 ثانیه
```

#### 3. Scalability
```
بدون Partitioning:
- 1 Neo4j instance
- Vertical scaling فقط (RAM بیشتر)
- محدودیت: 1TB RAM max

با Partitioning:
- N Neo4j instances
- Horizontal scaling (افزودن instance جدید)
- محدودیت: تقریباً نامحدود
```

---

## 🎨 استراتژی‌های Partitioning {#استراتژی‌ها}

### 1. Hash-Based Partitioning

**مفهوم**: از hash function برای تعیین partition استفاده می‌کنیم.

```python
def get_partition(entity_id: str, num_partitions: int) -> int:
    """Hash-based partitioning"""
    return hash(entity_id) % num_partitions

# مثال:
entity_id = "person_12345"
partition = get_partition(entity_id, 4)  # → 2
# این entity در partition 2 ذخیره می‌شود
```

**مزایا**:
- ✅ ساده و سریع
- ✅ توزیع یکنواخت
- ✅ بدون نیاز به metadata

**معایب**:
- ❌ Entities مرتبط ممکن است در partitions مختلف باشند
- ❌ Cross-partition queries زیاد

**کاربرد در Mahoun**: برای entities که ارتباط کمی دارند (مثل users)

---

### 2. Range-Based Partitioning

**مفهوم**: بر اساس محدوده‌ای از یک attribute تقسیم می‌کنیم.

```python
def get_partition_by_date(timestamp: datetime, partitions: List[Tuple]) -> int:
    """Range-based partitioning by date"""
    # Partitions: [(2020-01, 2020-12), (2021-01, 2021-12), ...]
    for i, (start, end) in enumerate(partitions):
        if start <= timestamp <= end:
            return i
    return len(partitions) - 1  # default

# مثال:
doc_date = datetime(2021, 6, 15)
partition = get_partition_by_date(doc_date, [
    (datetime(2020, 1, 1), datetime(2020, 12, 31)),  # P0: 2020
    (datetime(2021, 1, 1), datetime(2021, 12, 31)),  # P1: 2021
    (datetime(2022, 1, 1), datetime(2022, 12, 31)),  # P2: 2022
])  # → 1 (partition 2021)
```

**مزایا**:
- ✅ Queries بر اساس range خیلی سریع
- ✅ مناسب برای time-series data
- ✅ Archive قدیمی‌ها آسان

**معایب**:
- ❌ توزیع نامتعادل (hot partitions)
- ❌ نیاز به مدیریت ranges

**کاربرد در Mahoun**: برای documents بر اساس تاریخ

---

### 3. Domain-Based Partitioning (پیشنهاد برای Mahoun)

**مفهوم**: بر اساس domain logic تقسیم می‌کنیم.

```python
class DomainPartitioner:
    """Domain-based partitioning for Mahoun"""
    
    def get_partition(self, entity: Entity) -> str:
        """
        Partition strategy:
        - هر case_id یک partition
        - همه entities یک case در یک partition
        """
        if hasattr(entity, 'case_id'):
            return f"case_{entity.case_id}"
        elif hasattr(entity, 'domain'):
            return f"domain_{entity.domain}"
        else:
            return "default"

# مثال:
case_123_entities = [
    Entity(id="person_1", case_id=123),
    Entity(id="contract_5", case_id=123),
    Entity(id="fact_42", case_id=123),
]

# همه در partition "case_123" ذخیره می‌شوند
for entity in case_123_entities:
    partition = partitioner.get_partition(entity)
    # → "case_123"
```

**مزایا**:
- ✅ Entities مرتبط در یک partition
- ✅ Cross-partition queries کم
- ✅ Isolation بین cases
- ✅ مناسب برای Mahoun (هر case مستقل است)

**معایب**:
- ❌ توزیع نامتعادل (cases بزرگ vs کوچک)
- ❌ نیاز به rebalancing

**کاربرد در Mahoun**: استراتژی اصلی ✅

---

### 4. Hybrid Partitioning (پیشنهاد نهایی)

**مفهوم**: ترکیب چند استراتژی

```python
class HybridPartitioner:
    """Hybrid partitioning for Mahoun"""
    
    def get_partition(self, entity: Entity) -> str:
        """
        Strategy:
        1. اگر case_id دارد → domain-based
        2. اگر تاریخ دارد → range-based
        3. در غیر این صورت → hash-based
        """
        # Level 1: Domain (case_id)
        if hasattr(entity, 'case_id'):
            case_id = entity.case_id
            # Level 2: Hash برای توزیع cases
            shard = hash(case_id) % 4  # 4 shards
            return f"shard_{shard}/case_{case_id}"
        
        # Level 2: Range (date)
        elif hasattr(entity, 'created_at'):
            year = entity.created_at.year
            return f"archive_{year}"
        
        # Level 3: Hash (default)
        else:
            shard = hash(entity.id) % 4
            return f"shard_{shard}/default"

# مثال:
entities = [
    Entity(id="p1", case_id=123),      # → "shard_2/case_123"
    Entity(id="p2", case_id=456),      # → "shard_1/case_456"
    Entity(id="d1", created_at=2020),  # → "archive_2020"
    Entity(id="u1"),                   # → "shard_3/default"
]
```

**مزایا**:
- ✅ بهترین از همه استراتژی‌ها
- ✅ توزیع متعادل
- ✅ Cross-partition queries کم
- ✅ Flexible

**معایب**:
- ❌ پیچیده‌تر
- ❌ نیاز به مدیریت دقیق

---

## 🏗️ معماری پیشنهادی برای Mahoun {#معماری-mahoun}

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Graph Router Layer                        │
│  - Partition selection                                       │
│  - Query routing                                             │
│  - Cross-partition query coordination                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │      Partition Manager                   │
        │  - Partition metadata                    │
        │  - Rebalancing                           │
        │  - Health monitoring                     │
        └─────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                            │
        ▼                                            ▼
┌──────────────────┐                    ┌──────────────────┐
│  Partition 0     │                    │  Partition 1     │
│  (Neo4j)         │                    │  (Neo4j)         │
│                  │                    │                  │
│  Cases: 1-1000   │                    │  Cases: 1001-2000│
│  Nodes: 250K     │                    │  Nodes: 250K     │
│  Edges: 500K     │                    │  Edges: 500K     │
└──────────────────┘                    └──────────────────┘
        │                                            │
        ▼                                            ▼
┌──────────────────┐                    ┌──────────────────┐
│  Partition 2     │                    │  Partition 3     │
│  (Neo4j)         │                    │  (Neo4j)         │
│                  │                    │                  │
│  Cases: 2001-3000│                    │  Archive (old)   │
│  Nodes: 250K     │                    │  Nodes: 1M       │
│  Edges: 500K     │                    │  Edges: 2M       │
└──────────────────┘                    └──────────────────┘
```

### Component Details

#### 1. Graph Router
```python
class GraphRouter:
    """Routes queries to appropriate partitions"""
    
    def route_query(self, query: Query) -> List[str]:
        """
        Determine which partitions to query
        
        Returns:
            List of partition IDs
        """
        # Extract partition key from query
        if query.has_case_id():
            case_id = query.get_case_id()
            return [self._get_partition_for_case(case_id)]
        
        # Cross-partition query
        elif query.is_global():
            return self._get_all_partitions()
        
        # Default
        else:
            return [self._get_default_partition()]
```

#### 2. Partition Manager
```python
class PartitionManager:
    """Manages partition metadata and operations"""
    
    def __init__(self):
        self.partitions: Dict[str, PartitionInfo] = {}
        self.metadata_store = MetadataStore()
    
    def create_partition(self, partition_id: str) -> Partition:
        """Create new partition"""
        partition = Partition(
            id=partition_id,
            neo4j_uri=self._allocate_neo4j_instance(),
            status="active"
        )
        self.partitions[partition_id] = partition
        return partition
    
    def rebalance(self):
        """Rebalance partitions if needed"""
        # Check partition sizes
        for partition in self.partitions.values():
            if partition.size > THRESHOLD:
                self._split_partition(partition)
```

---

## 💻 پیاده‌سازی عملی {#پیاده‌سازی}

### مثال کامل برای Mahoun

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
import hashlib

@dataclass
class PartitionInfo:
    """Partition metadata"""
    id: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    case_ids: List[int]
    node_count: int
    status: str  # active, readonly, archived

class MahounGraphPartitioner:
    """
    Graph partitioning for Mahoun Platform
    
    Strategy: Hybrid (domain + hash)
    - Primary: case_id (domain-based)
    - Secondary: hash for load balancing
    """
    
    def __init__(self, num_shards: int = 4):
        self.num_shards = num_shards
        self.partitions: Dict[str, PartitionInfo] = {}
        self._init_partitions()
    
    def _init_partitions(self):
        """Initialize partition metadata"""
        for shard in range(self.num_shards):
            partition_id = f"shard_{shard}"
            self.partitions[partition_id] = PartitionInfo(
                id=partition_id,
                neo4j_uri=f"bolt://neo4j-{shard}:7687",
                neo4j_user="neo4j",
                neo4j_password="password",
                case_ids=[],
                node_count=0,
                status="active"
            )
    
    def get_partition_for_case(self, case_id: int) -> str:
        """
        Get partition ID for a case
        
        Args:
            case_id: Case identifier
            
        Returns:
            Partition ID (e.g., "shard_2")
        """
        # Hash-based distribution across shards
        shard = hash(case_id) % self.num_shards
        return f"shard_{shard}"
    
    def get_partition_for_entity(self, entity_id: str, case_id: Optional[int] = None) -> str:
        """
        Get partition ID for an entity
        
        Args:
            entity_id: Entity identifier
            case_id: Optional case ID (if entity belongs to a case)
            
        Returns:
            Partition ID
        """
        if case_id is not None:
            return self.get_partition_for_case(case_id)
        else:
            # Default: hash-based
            shard = hash(entity_id) % self.num_shards
            return f"shard_{shard}"
    
    def get_connection(self, partition_id: str) -> GraphDatabase.driver:
        """Get Neo4j connection for partition"""
        partition = self.partitions[partition_id]
        return GraphDatabase.driver(
            partition.neo4j_uri,
            auth=(partition.neo4j_user, partition.neo4j_password)
        )
    
    def execute_query(self, case_id: int, cypher: str, params: Dict = None):
        """
        Execute query on appropriate partition
        
        Args:
            case_id: Case ID
            cypher: Cypher query
            params: Query parameters
        """
        partition_id = self.get_partition_for_case(case_id)
        driver = self.get_connection(partition_id)
        
        with driver.session() as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]
    
    def execute_cross_partition_query(self, cypher: str, params: Dict = None):
        """
        Execute query across all partitions
        
        Warning: Expensive operation!
        """
        results = []
        for partition_id in self.partitions.keys():
            driver = self.get_connection(partition_id)
            with driver.session() as session:
                result = session.run(cypher, params or {})
                results.extend([record.data() for record in result])
        return results

# Usage Example
partitioner = MahounGraphPartitioner(num_shards=4)

# Query single case (fast)
case_123_facts = partitioner.execute_query(
    case_id=123,
    cypher="MATCH (f:Fact {case_id: $case_id}) RETURN f",
    params={"case_id": 123}
)

# Query all cases (slow - avoid if possible)
all_facts = partitioner.execute_cross_partition_query(
    cypher="MATCH (f:Fact) RETURN f LIMIT 100"
)
```

---

## ⚖️ Trade-offs و چالش‌ها {#چالش‌ها}

### Trade-offs

| معیار | بدون Partitioning | با Partitioning |
|-------|-------------------|-----------------|
| **Scalability** | محدود (vertical) | نامحدود (horizontal) |
| **Query Speed** | کند برای گراف بزرگ | سریع برای single partition |
| **Cross-partition Query** | N/A | کند و پیچیده |
| **Complexity** | ساده | پیچیده |
| **Cost** | کم (1 instance) | زیاد (N instances) |
| **Maintenance** | آسان | سخت |

### چالش‌های اصلی

#### 1. Cross-Partition Queries
```python
# مثال: پیدا کردن همه entities مرتبط با یک person
# اگر person در partition 1 و entities در partition 2, 3, 4

# بدون partition: یک query
MATCH (p:Person {id: "person_123"})-[r]-(e:Entity)
RETURN e

# با partition: باید همه partitions را جستجو کنیم
results = []
for partition in all_partitions:
    results += query_partition(partition, cypher)
# کند و پیچیده!
```

**راه حل**: 
- Denormalization: کپی کردن entities پرکاربرد در همه partitions
- Caching: cache کردن cross-partition results
- Graph index: نگه‌داری index از cross-partition edges

#### 2. Rebalancing
```python
# مثال: partition 1 خیلی بزرگ شده
partition_1_size = 10_GB  # خیلی بزرگ!
partition_2_size = 1_GB   # خیلی کوچک!

# نیاز به rebalancing:
# 1. انتخاب cases برای انتقال
# 2. کپی کردن data
# 3. به‌روزرسانی metadata
# 4. حذف data قدیمی

# چالش: downtime و consistency
```

**راه حل**:
- Online rebalancing: بدون downtime
- Incremental migration: به تدریج
- Monitoring: تشخیص زودهنگام

#### 3. Consistency
```python
# مثال: transaction بین دو partition
# Partition 1: ایجاد entity
# Partition 2: ایجاد relationship

# اگر partition 1 موفق و partition 2 fail شود؟
# → Inconsistency!
```

**راه حل**:
- Two-phase commit (2PC)
- Saga pattern
- Eventual consistency (قابل قبول برای Mahoun)

---

## 🎯 توصیه نهایی برای Mahoun

### استراتژی پیشنهادی

```python
class MahounPartitionStrategy:
    """
    Recommended partitioning strategy for Mahoun
    
    Level 1: Domain (case_id)
    - هر case در یک partition
    - Isolation بین cases
    
    Level 2: Hash (load balancing)
    - توزیع cases بین shards
    - 4-8 shards برای شروع
    
    Level 3: Archive (time-based)
    - Cases قدیمی (>2 سال) در archive partition
    - Read-only
    """
    
    def get_partition(self, case_id: int, created_at: datetime) -> str:
        # Archive old cases
        if (datetime.now() - created_at).days > 730:  # 2 years
            return "archive"
        
        # Active cases: hash-based distribution
        shard = hash(case_id) % 4
        return f"shard_{shard}"
```

### مراحل پیاده‌سازی

1. **Phase 1**: Single partition (فعلی) ✅
2. **Phase 2**: 4 shards با domain-based partitioning
3. **Phase 3**: Archive partition برای cases قدیمی
4. **Phase 4**: Auto-rebalancing

---

**نتیجه**: Graph Partitioning برای Mahoun ضروری است اما باید به تدریج و با دقت پیاده‌سازی شود. استراتژی domain-based (case_id) بهترین گزینه است.
