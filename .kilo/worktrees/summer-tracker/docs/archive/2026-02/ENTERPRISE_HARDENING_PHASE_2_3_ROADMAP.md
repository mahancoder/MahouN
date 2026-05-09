# Enterprise Hardening - Phase 2 & 3 Roadmap

**تاریخ شروع**: 2026-02-24  
**هدف**: رسیدن از 88% به 100% enterprise-ready

---

## 📊 وضعیت فعلی

| معیار | مقدار |
|-------|-------|
| نمره فعلی | 44/50 (88%) |
| نمره هدف Phase 2 | 46/50 (92%) |
| نمره هدف Phase 3 | 50/50 (100%) |

---

## 🔄 Phase 2: Dependencies + Integration (88% → 92%)

**هدف**: نصب dependencies و integration testing  
**مدت زمان تخمینی**: 2-3 ساعت  
**بهبود نمره**: +2 امتیاز

### Task 2.1: نصب Security Dependencies ✅

```bash
# Install cryptography for encryption
pip install cryptography

# Install PyNaCl for signing
pip install PyNaCl
```

**نتیجه مورد انتظار**:
- 5 تست skipped → 5 تست PASSED
- Encryption fully functional
- Signing fully functional

### Task 2.2: Integration با Ledger Writer

**فایل‌های تغییر**:
- `mahoun/execution/controller.py` - fix ledger integration
- `mahoun/ledger/writer.py` - add get_ledger_writer()

**مشکل فعلی**:
```python
ERROR: cannot import name 'get_ledger_writer' from 'mahoun.ledger.writer'
```

**راه حل**:
```python
# mahoun/ledger/writer.py
def get_ledger_writer() -> EvidenceLedgerWriter:
    """Get singleton ledger writer instance"""
    global _ledger_writer
    if _ledger_writer is None:
        _ledger_writer = EvidenceLedgerWriter()
    return _ledger_writer
```

### Task 2.3: Integration با Redis (DistributedLock)

**نیاز**:
- Redis server running
- redis-py installed

```bash
# Install redis
pip install redis

# Start Redis (Docker)
docker run -d -p 6379:6379 redis:latest
```

**تست**:
```python
# Test distributed lock
from mahoun.concurrency import DistributedLock

lock = DistributedLock("test_resource")
with lock:
    # Critical section
    pass
```

### Task 2.4: Integration Tests

**فایل جدید**: `tests/test_enterprise_integration.py`

```python
def test_encryption_with_ledger():
    """Test encryption integration with ledger"""
    pass

def test_distributed_lock_with_redis():
    """Test distributed lock with real Redis"""
    pass

def test_execution_controller_full_pipeline():
    """Test full pipeline with all components"""
    pass
```

**نمره بعد از Phase 2**: 46/50 (92%)

---

## 📅 Phase 3: ACID + Snapshot + Partitioning (92% → 100%)

**هدف**: پیاده‌سازی features پیشرفته  
**مدت زمان تخمینی**: 8-10 ساعت  
**بهبود نمره**: +4 امتیاز

### Task 3.1: ACID Transaction Manager

**فایل جدید**: `mahoun/storage/transaction_manager.py`

**Features**:
- Begin/commit/rollback transactions
- ACID guarantees
- Isolation levels (READ_COMMITTED, SERIALIZABLE)
- Savepoints
- Nested transactions

**مثال**:
```python
class TransactionManager:
    """ACID transaction manager for Mahoun"""
    
    def begin_transaction(self, isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED):
        """Begin new transaction"""
        pass
    
    def commit(self):
        """Commit transaction"""
        pass
    
    def rollback(self):
        """Rollback transaction"""
        pass
    
    def savepoint(self, name: str):
        """Create savepoint"""
        pass
```

**نمره بهبود**: Storage Semantics 3/5 → 5/5 (+2)

### Task 3.2: Snapshot Isolation

**فایل جدید**: `mahoun/storage/snapshot_manager.py`

**Features**:
- MVCC (Multi-Version Concurrency Control)
- Snapshot reads
- Version management
- Garbage collection

**مثال**:
```python
class SnapshotManager:
    """Snapshot isolation for concurrent reads"""
    
    def create_snapshot(self) -> Snapshot:
        """Create new snapshot"""
        pass
    
    def read_at_snapshot(self, snapshot: Snapshot, key: str):
        """Read data at specific snapshot"""
        pass
    
    def cleanup_old_snapshots(self):
        """Garbage collect old snapshots"""
        pass
```

**نمره بهبود**: Storage Semantics 3/5 → 4/5 (+1)

### Task 3.3: Graph Partitioning

**فایل جدید**: `mahoun/graph/partitioner.py`

**Features**:
- Hybrid partitioning (domain + hash)
- Partition routing
- Cross-partition queries
- Rebalancing
- Metadata management

**مثال**:
```python
class GraphPartitioner:
    """Graph partitioning for scalability"""
    
    def get_partition_for_case(self, case_id: int) -> str:
        """Get partition ID for case"""
        pass
    
    def execute_query(self, case_id: int, cypher: str):
        """Execute query on appropriate partition"""
        pass
    
    def rebalance(self):
        """Rebalance partitions"""
        pass
```

**نمره بهبود**: Graph Scaling 3/5 → 5/5 (+2)

### Task 3.4: Probabilistic Threshold Policies

**فایل جدید**: `mahoun/uncertainty/threshold_policy.py`

**Features**:
- Formal threshold definitions
- Policy enforcement
- Deterministic override
- Audit trail

**مثال**:
```python
class ThresholdPolicy:
    """Threshold policies for probabilistic components"""
    
    def check_threshold(self, uncertainty: float, threshold: float) -> bool:
        """Check if uncertainty is within threshold"""
        pass
    
    def override(self, reason: str):
        """Deterministic override"""
        pass
```

**نمره بهبود**: Probabilistic Components 3/5 → 5/5 (+2)

---

## 📋 خلاصه Tasks

### Phase 2 (2-3 ساعت)
- [ ] Task 2.1: نصب cryptography و PyNaCl
- [ ] Task 2.2: Fix ledger integration
- [ ] Task 2.3: Setup Redis و test DistributedLock
- [ ] Task 2.4: نوشتن integration tests

### Phase 3 (8-10 ساعت)
- [ ] Task 3.1: TransactionManager (ACID)
- [ ] Task 3.2: SnapshotManager (Snapshot Isolation)
- [ ] Task 3.3: GraphPartitioner (Partitioning)
- [ ] Task 3.4: ThresholdPolicy (Probabilistic)

---

## 📈 پیشرفت نمرات

| دسته | فعلی | بعد Phase 2 | بعد Phase 3 |
|------|------|-------------|-------------|
| 1. Execution Governance | 5/5 | 5/5 | 5/5 |
| 2. State Model | 5/5 | 5/5 | 5/5 |
| 3. Ledger Architecture | 5/5 | 5/5 | 5/5 |
| 4. Storage Semantics | 3/5 | 3/5 | **5/5** |
| 5. Probabilistic Components | 3/5 | 3/5 | **5/5** |
| 6. Graph Scaling | 3/5 | 3/5 | **5/5** |
| 7. Concurrency Model | 5/5 | 5/5 | 5/5 |
| 8. Security Architecture | 4.5/5 | **5/5** | 5/5 |
| 9. Observability | 5/5 | 5/5 | 5/5 |
| 10. Legal Defensibility | 5/5 | 5/5 | 5/5 |
| **مجموع** | **44/50** | **46/50** | **50/50** |
| **درصد** | **88%** | **92%** | **100%** |

---

## 🎯 اولویت‌بندی

### اولویت بالا (حیاتی)
1. Task 2.1: Security dependencies
2. Task 2.2: Ledger integration
3. Task 3.1: ACID transactions

### اولویت متوسط (مهم)
4. Task 2.3: Redis integration
5. Task 3.2: Snapshot isolation
6. Task 3.4: Threshold policies

### اولویت پایین (بهبود)
7. Task 2.4: Integration tests
8. Task 3.3: Graph partitioning

---

## 🚀 شروع کار

بیا از Phase 2 شروع کنیم:

```bash
# Step 1: Install dependencies
pip install cryptography PyNaCl redis

# Step 2: Start Redis
docker run -d -p 6379:6379 redis:latest

# Step 3: Run tests
pytest tests/test_enterprise_hardening_comprehensive.py -v

# Step 4: Fix ledger integration
# (edit mahoun/ledger/writer.py)

# Step 5: Run integration tests
pytest tests/test_enterprise_integration.py -v
```

---

**آماده‌ای داداش؟** بیا شروع کنیم! 🚀
