# Governance Integration Documentation

**Version**: 2.0.0  
**Last Updated**: 2026-05-21  
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Core Components](#3-core-components)
4. [Governance Context](#4-governance-context)
5. [Provenance System](#5-provenance-system)
6. [API Integration](#6-api-integration)
7. [Developer Guide](#7-developer-guide)
8. [Deployment Guide](#8-deployment-guide)
9. [Testing](#9-testing)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Overview

The Governance Integration subsystem provides immutable governance enforcement, forensic validation, and cryptographic provenance tracking for all reasoning operations in the MAHOUN platform.

### Key Features

- **Immutable Governance**: GovernanceLock prevents runtime bypass
- **Forensic Validation**: FortressValidator ensures all outputs meet quality thresholds
- **Proof-Carrying Contracts**: All API responses include cryptographic attestation
- **Mandatory Context**: NO reasoning operation can execute without governance context
- **Cryptographic Provenance**: All data mutations have cryptographic integrity
- **Correlation Lineage**: Full traceability of execution chains

### Design Principles

1. **Fail-Closed**: Unknown states default to maximum enforcement
2. **Zero Bypass**: No environment variable or runtime flag can disable governance
3. **Cryptographic Attestation**: Every operation carries cryptographic proof
4. **Append-Only Audit**: All governance events written to immutable ledger
5. **Deterministic Resolution**: Identical inputs produce identical outputs

---

## 2. Architecture

### Component Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  api/routers/reasoning.py                                 │   │
│  │  - generate-verdict endpoint                              │   │
│  │  - verify-verdict endpoint                                │   │
│  │  - query-ledger endpoint                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ProofCarryingResponse (Pydantic Model)                   │   │
│  │  - fortress_validated: bool                               │   │
│  │  - audit_hash: str                                        │   │
│  │  - validation_timestamp: str                              │   │
│  │  - correlation_id: str                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Governance Context Layer (CRITICAL)                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  GovernanceContextManager                                 │   │
│  │  - active_context() async context manager                │   │
│  │  - Correlation lineage tracking                           │   │
│  │  - Runtime attestation generation                         │   │
│  │  - Proof tracking activation                              │   │
│  │  - Contradiction hooks activation                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Fortress Integration Layer                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FortressProtectedReasoningService                        │   │
│  │  - Wraps UnifiedReasoningService                          │   │
│  │  - Auto-validates all responses                           │   │
│  │  - Statistics tracking                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FortressValidator                                        │   │
│  │  - Validates proof_tree                                   │   │
│  │  - Validates agreement_score >= 0.85                      │   │
│  │  - Validates evidence linkage                             │   │
│  │  - Generates forensic audit trail                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Unified Reasoning Service                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  UnifiedReasoningService                                  │   │
│  │  - Symbolic reasoning                                     │   │
│  │  - Neural reasoning                                       │   │
│  │  - Hybrid reasoning                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  GovernanceLock (Immutable)                               │   │
│  │  - Mode set at startup                                    │   │
│  │  - Cannot be changed at runtime                           │   │
│  │  - Cryptographic authorization for DISABLED               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Provenance & Audit Layer (CRITICAL)             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ProvenanceTracker                                        │   │
│  │  - Cryptographic attestation (hash + signature)           │   │
│  │  - Governance-controlled timestamps                       │   │
│  │  - Correlation lineage graph                              │   │
│  │  - Immutable persistence contract                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  InferenceProvenance                                      │   │
│  │  - Rule chain tracking                                    │   │
│  │  - Evidence node tracking                                 │   │
│  │  - Contradiction branch tracking                          │   │
│  │  - Symbolic trace hashing                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Components

### 3.1 GovernanceLock

**Purpose**: Immutable governance enforcement that cannot be bypassed.

**File**: `mahoun/core/governance_lock.py`

**Key Properties**:
- Mode set ONCE at process startup
- Mode CANNOT be changed after initialization
- DISABLED mode requires cryptographic authorization
- Fail-closed if not initialized (defaults to STRICT)
- All bypass attempts logged with forensic context

**API**:
```python
from mahoun.core.governance_lock import GovernanceLock, GovernanceMode

# Initialize at application startup (ONCE)
GovernanceLock.initialize(mode=GovernanceMode.STRICT)

# Check if enforcement is enabled
if GovernanceLock.is_enforcement_enabled():
    # Proceed with full enforcement
    pass

# Get current mode
mode = GovernanceLock.get_mode()

# Verify integrity
assert GovernanceLock.verify_integrity(), "Lock tampered!"
assert GovernanceLock.verify_immutable(), "Lock not immutable!"

# Get audit metadata
metadata = GovernanceLock.get_audit_metadata()
# Returns: {
#   "initialized": bool,
#   "mode": str,
#   "integrity_verified": bool,
#   "change_attempts": int,
#   "bypass_attempts": List[Dict]
# }
```

**Governance Modes**:

| Mode | Environment | Description |
|------|-------------|-------------|
| `STRICT` | Production | Full enforcement, no exceptions |
| `AUDIT` | Staging | Log violations but don't block |
| `DISABLED` | Local dev ONLY | Requires cryptographic auth token |

**Security Properties**:
- Initialization lock prevents re-initialization
- Immutability verified via internal state tracking
- DISABLED mode requires daily rotating token: `SHA256("MAHOUN_DEV_OVERRIDE_{date}")`
- All bypass attempts logged with timestamp and stack trace

---

### 3.2 FortressValidator

**Purpose**: Final forensic validation layer for all reasoning outputs.

**File**: `mahoun/core/fortress_validator.py`

**Validation Checks**:

| Check | Threshold | Description |
|-------|-----------|-------------|
| **Proof Tree** | Required | Every decision must carry a fully deterministic proof tree |
| **Agreement Score** | ≥ 0.85 | Hybrid reasoning (neural + symbolic) must achieve agreement |
| **Evidence Linkage** | 100% | Facts derived from graph must be explicitly cited |
| **Audit Trail** | Complete | All reasoning steps must be logged |
| **Determinism** | Required | Identical inputs must produce identical outputs |
| **Contradiction Detection** | Zero tolerance | Rejects outputs where LLM contradicts symbolic logic |

**API**:
```python
from mahoun.core.fortress_validator import FortressValidator

# Create validator
validator = FortressValidator(strict_mode=True)

# Validate a reasoning response
validation_result = await validator.validate(
    response=reasoning_response,
    correlation_id="req-123"
)

# Check result
if validation_result.passed:
    print(f"Validation passed: {validation_result.forensic_hash}")
else:
    print(f"Violations: {validation_result.violations}")

# Get statistics
stats = validator.get_stats()
# Returns: {
#   "total_validations": int,
#   "passed": int,
#   "failed": int,
#   "avg_execution_time_ms": float
# }

# Get audit trail
audit_trail = validator.get_audit_trail(limit=100)
```

**ValidationResult**:
```python
class ValidationResult(BaseModel):
    passed: bool
    correlation_id: str
    timestamp: str
    execution_time_ms: float
    violations: List[Dict[str, Any]]
    warnings: List[str]
    forensic_hash: str
    metadata: Dict[str, Any]
```

---

### 3.3 FortressProtectedReasoningService

**Purpose**: Wrapper around UnifiedReasoningService with automatic validation.

**File**: `mahoun/reasoning/fortress_integration.py`

**API**:
```python
from mahoun.reasoning.fortress_integration import create_fortress_protected_service

# Create protected service
protected_service = create_fortress_protected_service(
    reasoning_service=unified_service,
    strict_mode=True
)

# Execute reasoning (auto-validated)
response = await protected_service.reason(
    request=request,
    correlation_id="req-123"
)

# Batch reasoning
responses = await protected_service.reason_batch(
    requests=[req1, req2, req3],
    correlation_id_prefix="batch-123"
)

# Get statistics
stats = protected_service.get_stats()

# Health check
health = await protected_service.health_check()
```

**Features**:
- Automatic validation of all responses
- Statistics tracking (total requests, passed, failed)
- Batch processing support
- Health check endpoint
- Correlation ID propagation

---

### 3.4 ProofCarryingResponse

**Purpose**: Pydantic base model for API responses with mandatory governance metadata.

**File**: `mahoun/api/models/proof_carrying.py`

**Fields**:

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `fortress_validated` | `bool` | Whether response passed Fortress validation | Required, must be True |
| `audit_hash` | `str` | SHA-256 hash for tamper detection | Required, 16-64 chars |
| `validation_timestamp` | `str` | ISO 8601 timestamp of validation | Required, ISO 8601 format |
| `correlation_id` | `str` | Unique tracing ID | Required, non-empty |

**Usage**:
```python
from mahoun.api.models.proof_carrying import ProofCarryingResponse

class MyAPIResponse(ProofCarryingResponse):
    result: str
    confidence: float
    metadata: Dict[str, Any]

# Create response (proof-carrying fields injected automatically)
response = MyAPIResponse(
    result="Contract is valid",
    confidence=0.95,
    metadata={"source": "reasoning_engine"},
    fortress_validated=True,
    audit_hash="abc123...",
    validation_timestamp="2026-05-21T10:30:00Z",
    correlation_id="req-123"
)
```

**Contract Enforcement**:
- `SecurityBreachException` raised if proof-carrying contract violated
- All fields validated at Pydantic level
- Automatic injection when validation passes

---

## 4. Governance Context

### 4.1 Overview

**CRITICAL**: NO reasoning operation can execute without an active governance context.
