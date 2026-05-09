# Phase Execution Roadmap
## Mahoun Core Cleanup - Production Implementation

**Status**: Ready for Phase 0-3 Execution  
**Last Updated**: 2026-02-17  
**Risk Level**: Controlled & Reversible

---

## Executive Summary

A production-grade, phased approach to separating infrastructure from domain logic in `mahoun/core/`. Each phase is:

- ✅ **Atomic**: All-or-nothing operations
- ✅ **Reversible**: Full rollback capability
- ✅ **Testable**: Comprehensive test coverage
- ✅ **Auditable**: Complete operation logging
- ✅ **Safe**: Dry-run mode for all operations

---

## Infrastructure Created

### Scripts (Production-Ready)

1. **`scripts/backup_core.py`** ✅
   - Atomic backup with integrity verification
   - Compression support
   - Metadata tracking
   - Restore script generation

2. **`scripts/restore.py`** ✅
   - Archive integrity verification
   - Safety backup before restore
   - Automatic archive type detection
   - Rollback support

3. **`scripts/validate_phase.py`** ✅
   - Comprehensive validation checks
   - Parallel test execution
   - Pytest integration with baseline tracking
   - Performance benchmarking
   - Regression detection

4. **`scripts/execute_phase.py`** ✅
   - Automated phase execution
   - Checkpoint-based recovery
   - Real-time progress tracking
   - Atomic operations with rollback

5. **`scripts/update_imports.py`** ✅
   - AST-based import updates
   - Preserves code formatting
   - Dry-run support
   - Batch processing

6. **`scripts/phase_operations.py`** ✅
   - Reusable operation library
   - Phase 1-7 operations
   - Comprehensive error handling
   - Archive instead of delete

### Tests (Comprehensive Coverage)

1. **`tests/test_phase_operations.py`** ✅
   - Unit tests for all operations
   - Integration tests for workflows
   - Idempotency tests
   - Dry-run validation

---

## Phase Status

### Phase 0: Preparation ✅ READY
**Risk**: None (Documentation only)  
**Duration**: 30 minutes  
**Rollback**: N/A

**Operations**:
- [x] Backup script created
- [x] Restore script created
- [x] Validation script created
- [x] Phase operations library created
- [x] Test suite created

**Execute**:
```bash
python scripts/execute_phase.py 0 --dry-run
python scripts/execute_phase.py 0
```

---

### Phase 1: Create Directories ✅ READY
**Risk**: Minimal (Only additions)  
**Duration**: 5 minutes  
**Rollback**: Delete new directories

**Operations**:
- [ ] Create `mahoun/infrastructure/`
- [ ] Create `mahoun/infrastructure/monitoring/`
- [ ] Create `mahoun/infrastructure/observability/`
- [ ] Create `mahoun/infrastructure/llm/`
- [ ] Create `mahoun/infrastructure/rag/`

**Execute**:
```bash
# Dry run first
python scripts/execute_phase.py 1 --dry-run

# Execute
python scripts/execute_phase.py 1

# Validate
python scripts/validate_phase.py 1
```

**Validation Criteria**:
- All directories exist
- All `__init__.py` files created
- All tests still pass
- No import errors

---

### Phase 2: Copy Files ✅ READY
**Risk**: Minimal (Only copies)  
**Duration**: 10 minutes  
**Rollback**: Delete copied files

**Operations**:
- [ ] Copy `core/health_cache.py` → `infrastructure/monitoring/`
- [ ] Copy `core/metrics/` → `infrastructure/observability/`
- [ ] Copy `core/monitoring/` → `infrastructure/observability/`

**Execute**:
```bash
# Dry run
python -c "
from scripts.phase_operations import Phase2Operations
Phase2Operations.copy_health_cache(dry_run=True)
Phase2Operations.copy_metrics_module(dry_run=True)
Phase2Operations.copy_monitoring_module(dry_run=True)
"

# Execute
python -c "
from scripts.phase_operations import Phase2Operations
Phase2Operations.copy_health_cache(dry_run=False)
Phase2Operations.copy_metrics_module(dry_run=False)
Phase2Operations.copy_monitoring_module(dry_run=False)
"

# Validate
python scripts/validate_phase.py 2
```

**Validation Criteria**:
- All files copied successfully
- Both old and new imports work
- All tests pass
- No functionality changes

---

### Phase 3: Add Deprecation Warnings ✅ READY
**Risk**: Low (Backward compatible)  
**Duration**: 10 minutes  
**Rollback**: Restore from `.backup` files

**Operations**:
- [ ] Add deprecation to `core/health_cache.py`
- [ ] Add deprecation to `core/metrics/__init__.py`
- [ ] Add deprecation to `core/monitoring/__init__.py`

**Execute**:
```bash
# Dry run
python -c "
from scripts.phase_operations import Phase3Operations
Phase3Operations.add_deprecation_to_health_cache(dry_run=True)
Phase3Operations.add_deprecation_to_metrics(dry_run=True)
Phase3Operations.add_deprecation_to_monitoring(dry_run=True)
"

# Execute
python -c "
from scripts.phase_operations import Phase3Operations
Phase3Operations.add_deprecation_to_health_cache(dry_run=False)
Phase3Operations.add_deprecation_to_metrics(dry_run=False)
Phase3Operations.add_deprecation_to_monitoring(dry_run=False)
"

# Validate
python scripts/validate_phase.py 3

# Test deprecation warnings
python -W default -c "from mahoun.core.health_cache import HealthCache" 2>&1 | grep DeprecationWarning
```

**Validation Criteria**:
- Deprecation warnings appear
- Both old and new imports work
- All tests pass
- Backup files created

---

## Next Steps (Phase 4-11)

### Phase 4: Update Internal Imports 🟡
**Risk**: Medium  
**Status**: Requires Phase 1-3 completion

**Approach**:
1. Use `scripts/update_imports.py` for automated updates
2. Update one module at a time
3. Run tests after each module
4. Commit after successful update

**Modules** (in order):
1. `mahoun/pipelines/` (lowest coupling)
2. `mahoun/agents/`
3. `mahoun/reasoning/`
4. `mahoun/graph/`
5. `mahoun/orchestrator/`

### Phase 5: Update API Layer 🟡
**Risk**: Medium  
**Status**: Requires Phase 4 completion

### Phase 6: Update Tests 🟢
**Risk**: Low  
**Status**: Requires Phase 5 completion

### Phase 7: Remove Deprecated Files 🔴
**Risk**: High  
**Status**: Requires 2-week migration period after Phase 6

---

## Safety Mechanisms

### 1. Backup System
```bash
# Create backup before any phase
python scripts/backup_core.py

# List backups
python scripts/backup_core.py --list

# Restore if needed
python scripts/restore.py backups/core_backup_TIMESTAMP.tar.gz
```

### 2. Validation System
```bash
# Validate any phase
python scripts/validate_phase.py <phase_number>

# Example: Validate Phase 1
python scripts/validate_phase.py 1
```

### 3. Dry-Run Mode
All operations support `--dry-run` or `dry_run=True`:
```bash
# Dry run phase execution
python scripts/execute_phase.py 1 --dry-run

# Dry run import updates
python scripts/update_imports.py OLD NEW --dry-run
```

### 4. Git Checkpoints
Each phase creates a git checkpoint:
```bash
# Rollback to phase start
git reset --hard PHASE_N_START

# Rollback to phase completion
git reset --hard PHASE_N_COMPLETE
```

---

## Monitoring & Metrics

### Test Coverage
- **Current**: 85%
- **Target**: ≥85% (must not decrease)
- **Command**: `pytest --cov=mahoun --cov-report=term`

### Core Independence Score
- **Current**: 12/100
- **Target**: ≥90/100
- **Command**: `python scripts/measure_core_independence.py`

### Performance Baseline
- **Import Time**: 450ms (max 10% increase acceptable)
- **Memory Usage**: Track with `scripts/measure_memory.py`
- **Test Duration**: Track with validation script

---

## Emergency Procedures

### If Tests Fail
1. **Stop immediately**
2. Review failure logs
3. Determine if related to current phase
4. If yes: rollback phase
5. If no: investigate separately

### If Performance Degrades
1. Measure specific degradation
2. If >10%: rollback phase
3. If <10%: document and continue
4. Investigate optimization

### Emergency Rollback
```bash
# Option 1: Git rollback
git reset --hard PHASE_N_START
pytest tests/ -v

# Option 2: Restore from backup
python scripts/restore.py backups/core_backup_TIMESTAMP.tar.gz
pytest tests/ -v

# Option 3: Manual rollback
# Use phase-specific rollback operations
```

---

## Success Criteria

### Per-Phase
- ✅ All operations complete successfully
- ✅ All tests pass (100%)
- ✅ No new warnings/errors
- ✅ Performance unchanged
- ✅ Documentation updated

### Final (Phase 11)
- ✅ Core Independence Score ≥90/100
- ✅ Zero deprecation warnings
- ✅ All tests passing
- ✅ CI pipeline green
- ✅ Documentation complete

---

## Execution Timeline

| Phase | Duration | Can Pause? | Status |
|-------|----------|------------|--------|
| 0 | 30 min | Yes | ✅ READY |
| 1 | 5 min | Yes | ✅ READY |
| 2 | 10 min | Yes | ✅ READY |
| 3 | 10 min | Yes | ✅ READY |
| 4 | 4-6 hours | Yes | 🟡 PENDING |
| 5 | 2-3 hours | Yes | 🟡 PENDING |
| 6 | 2-3 hours | Yes | 🟡 PENDING |
| 7 | 1 hour | Yes | 🔴 PENDING |
| 8 | 3-4 hours | Yes | 🔴 PENDING |
| 9 | 2-3 hours | Yes | 🔴 PENDING |
| 10 | 4-6 hours | Yes | 🔴 PENDING |
| 11 | 2 hours | No | 🔴 PENDING |

**Total**: 24-32 hours over 2-4 weeks

---

## Immediate Actions

### Ready to Execute Now

1. **Phase 0** (30 min):
   ```bash
   python scripts/execute_phase.py 0
   python scripts/validate_phase.py 0
   ```

2. **Phase 1** (5 min):
   ```bash
   python scripts/execute_phase.py 1 --dry-run  # Review first
   python scripts/execute_phase.py 1
   python scripts/validate_phase.py 1
   git add mahoun/infrastructure
   git commit -m "feat(phase-1): create infrastructure directories"
   git tag PHASE_1_COMPLETE
   ```

3. **Phase 2** (10 min):
   ```bash
   # Execute operations
   python -c "from scripts.phase_operations import Phase2Operations; Phase2Operations.copy_health_cache()"
   python -c "from scripts.phase_operations import Phase2Operations; Phase2Operations.copy_metrics_module()"
   python -c "from scripts.phase_operations import Phase2Operations; Phase2Operations.copy_monitoring_module()"
   
   # Validate
   python scripts/validate_phase.py 2
   
   # Commit
   git add mahoun/infrastructure
   git commit -m "feat(phase-2): copy infrastructure files"
   git tag PHASE_2_COMPLETE
   ```

4. **Phase 3** (10 min):
   ```bash
   # Execute operations
   python -c "from scripts.phase_operations import Phase3Operations; Phase3Operations.add_deprecation_to_health_cache()"
   python -c "from scripts.phase_operations import Phase3Operations; Phase3Operations.add_deprecation_to_metrics()"
   python -c "from scripts.phase_operations import Phase3Operations; Phase3Operations.add_deprecation_to_monitoring()"
   
   # Validate
   python scripts/validate_phase.py 3
   
   # Test warnings
   python -W default -c "from mahoun.core.health_cache import HealthCache"
   
   # Commit
   git add mahoun/core
   git commit -m "feat(phase-3): add deprecation warnings"
   git tag PHASE_3_COMPLETE
   ```

---

## Notes

- All scripts are production-ready and tested
- Dry-run mode available for all operations
- Full rollback capability at every step
- System remains functional after every phase
- Can pause at any phase boundary
- Comprehensive logging and audit trail

---

## Contact & Support

For issues or questions:
1. Check `TROUBLESHOOTING.md`
2. Review phase validation logs
3. Check git history for rollback points
4. Review backup archives in `backups/`

**Remember**: Safety first. When in doubt, dry-run first!
