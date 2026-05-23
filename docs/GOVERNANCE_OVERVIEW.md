# MahouN Governance & Provenance Overview

**Version**: 2.0.0
**Last Updated**: May 21, 2026

---

## 1. Core Governance Philosophy

MahouN is built on a **Governance-Native Execution Substrate**. Security, compliance, and deterministic execution are not bolted-on features — they are foundational requirements enforced at the lowest levels of the architecture.

**The Governance Hierarchy:**

```
Truth > Determinism > Governance > Autonomy
```

Every reasoning step, API call, and graph mutation must be governed by strict rules, leaving no room for unvalidated autonomy or "hallucinated" behaviors.

### Key Principles

| Principle | Description |
|-----------|-------------|
| **Fail-Closed** | If governance state is unknown, assume maximum enforcement |
| **Zero Bypass** | No environment variable, runtime flag, or code path can disable governance |
| **Cryptographic Provenance** | Every mutation carries a cryptographic attestation chain |
| **Append-Only Audit** | All governance events are written to an immutable ledger |
| **Deterministic Resolution** | Identical inputs always produce identical outputs |

---

## 2. Governance Architecture Components

```
┌──────────────────────────────────────────────────────────────┐
│                      API Layer                                │
│   ┌─────────────────────────────────────────────────────┐    │
│   │          GovernanceContextManager                    │    │
│   │  • Correlation ID assignment                         │    │
│   │  • Execution scope tracking                          │    │
│   │  • Runtime attestation                               │    │
│   └────────────────────┬────────────────────────────────┘    │
│                        │                                      │
│   ┌────────────────────▼────────────────────────────────┐    │
│   │     FortressProtectedReasoningService                │    │
│   │  • Automatic response validation                     │    │
│   │  • SecurityBreachException on violations             │    │
│   │  • Forensic audit trail generation                   │    │
│   └────────────────────┬────────────────────────────────┘    │
│                        │                                      │
│   ┌────────────────────▼────────────────────────────────┐    │
│   │            FortressValidator                         │    │
│   │  • Proof tree validation                             │    │
│   │  • Agreement score check (≥ 0.85)                    │    │
│   │  • Evidence linkage verification                     │    │
│   │  • Contradiction detection                           │    │
│   │  • RedLines.yaml constitution enforcement            │    │
│   └────────────────────┬────────────────────────────────┘    │
│                        │                                      │
│   ┌────────────────────▼────────────────────────────────┐    │
│   │           GovernanceLock (Immutable)                  │    │
│   │  • Set ONCE at process startup                       │    │
│   │  • Cannot be changed after initialization            │    │
│   │  • Bypass attempts logged and rejected               │    │
│   │  • Integrity verified via SHA-256 hash               │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                               │
│   ┌─────────────────────────────────────────────────────┐    │
│   │          Provenance & Audit Trail                    │    │
│   │  • ProvenanceTracker (cryptographic attestation)     │    │
│   │  • ImmutableLedger (blockchain audit)                │    │
│   │  • ProofCarryingResponse (API response contract)     │    │
│   └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. The Fortress Validator

**File**: `mahoun/core/fortress_validator.py`

The `FortressValidator` is the primary mechanism for forensic validation. It intercepts all AI reasoning outputs and ensures they comply with the `RedLines.yaml` constitution.

### Validation Gates

| Gate | Threshold | Description |
|------|-----------|-------------|
| **Proof Tree** | Required | Every decision must carry a fully deterministic proof tree |
| **Agreement Score** | ≥ 0.85 | Hybrid reasoning (neural + symbolic) must achieve agreement |
| **Evidence Linkage** | 100% | Facts derived from graph must be explicitly cited |
| **Contradiction Detection** | Zero tolerance | Rejects outputs where LLM contradicts symbolic logic |

### Execution Modes

| Mode | Behavior |
|------|----------|
| `ENTERPRISE_FULL` | Full graph reasoning with all validations |
| `DESKTOP_MINIMAL` | Limited mode, graph operations restricted |

### CI/CD Enforcement

The validator runs in **strict fail-closed mode** in CI/CD. Any commit that:
- Bypasses the Fortress Validator
- Lowers threshold requirements
- Introduces logic that fails validation gates
- Sets `strict_mode=False` in production code

...will instantly break the build (Gates 9, 10, 11 in the unified governance workflow).

---

## 4. Governance Lock

**File**: `mahoun/core/governance_lock.py`

The `GovernanceLock` prevents runtime governance bypass via environment variables or code manipulation.

### Security Properties

1. **Initialization Lock**: Mode is set ONCE at process startup
2. **Immutability**: Mode CANNOT be changed after initialization
3. **Forensic Logging**: All bypass attempts are logged with timestamps
4. **Cryptographic Authorization**: `DISABLED` mode requires daily rotating token
5. **Fail-Closed Default**: Uninitialized state defaults to `STRICT`

### Governance Modes

| Mode | Environment | Description |
|------|-------------|-------------|
| `STRICT` | Production | Full enforcement, no exceptions |
| `AUDIT` | Staging | Log violations but don't block |
| `DISABLED` | Local dev ONLY | Requires cryptographic auth token |

### Usage

```python
# At application startup (ONCE):
from mahoun.core.governance_lock import GovernanceLock, GovernanceMode

GovernanceLock.initialize(mode=GovernanceMode.STRICT)

# Later in code:
if GovernanceLock.is_enforcement_enabled():
    # Proceed with full enforcement
    pass

# Integrity check:
assert GovernanceLock.verify_integrity(), "Lock tampered!"
assert GovernanceLock.verify_immutable(), "Lock not immutable!"
```

---

## 5. Governance Context Manager

**File**: `mahoun/core/governance/governance_context.py`

All reasoning executions **MUST** run within a securely tracked context.

### What It Guarantees

- **Correlation Lineage**: Every execution has a unique correlation ID
- **Proof Tracking**: Active proof tracking for audit trail
- **Governance Scope**: All operations run within governance scope
- **Runtime Attestation**: Cryptographic attestation of execution context
- **Child Contexts**: Hierarchical context inheritance for sub-operations

### Usage Pattern

```python
from mahoun.core.governance import GovernanceContextManager

# Primary usage — async context manager
async with GovernanceContextManager.active_context(
    correlation_id="case-12345",
    execution_mode="STRICT"
) as ctx:
    # All operations in this scope are governed
    # Provenance is automatically tracked
    result = await protected_service.reason(request, correlation_id=ctx.correlation_id)

# Require active context (fail-closed)
ctx = GovernanceContextManager.require_context()  # Raises if no context

# Require provenance metadata for graph operations
provenance = GovernanceContextManager.require_provenance(
    source="contract_analysis",
    author="system"
)
```

### Missing Context Behavior

If reasoning is attempted without an active `GovernanceContext`:
1. `GovernanceViolationError` is raised with category `GOVERNANCE_BYPASS`
2. Prometheus counter `mahoun_governance_missing_context_total` is incremented
3. Alert `MissingGovernanceContext` fires if rate > 0 for 1 minute

---

## 6. Provenance and Lineage Tracking

### Data Provenance

Every node in the Neo4j graph contains provenance metadata:
- **Source document**: Origin of the data
- **Extraction timestamp**: When the data was extracted
- **Processing agent**: Which AI agent processed it
- **Governance scope ID**: Which governance context authorized the mutation
- **Runtime attestation ID**: Cryptographic attestation of the execution environment

### Execution Provenance

`ProofCarryingResponse` objects ensure the API always returns:
- **Proof Tree**: Complete deterministic reasoning chain
- **Agreement Score**: Neural vs symbolic agreement metric
- **Execution Time**: Processing duration
- **Audit Hash**: SHA-256 tamper-evident hash
- **Correlation ID**: End-to-end tracing identifier
- **Validation Timestamp**: When Fortress validation occurred

### Provenance Creation

```python
from mahoun.core.governance import GovernanceContextManager

# Automatically creates provenance with full governance attestation
provenance = GovernanceContextManager.require_provenance(
    source="document_ingestion",
    author="ingestion_pipeline"
)
# Returns ProvenanceMetadata with:
#   - correlation_id
#   - governance_scope_id
#   - runtime_attestation_id
#   - cryptographic hash
```

---

## 7. CI/CD Governance Pipeline

The CI/CD pipeline is an **active architectural immune system**, not just a test runner.

### Gate Structure (Unified Governance Workflow)

| Gate | Name | Purpose |
|------|------|---------|
| 1 | Forbidden Pattern Scan | Detects direct env access, silent exceptions |
| 2 | Architecture Compliance | Validates layer boundary integrity |
| 3 | Schema Drift Detection | Catches configuration drift |
| 4 | Type Checking (mypy) | Strict type enforcement on governance modules |
| 5 | Governance Kernel Tests | Unit tests for governance components |
| 6 | Determinism Repeat Tests | 3x repeat to catch non-deterministic behavior |
| 7 | Governance Coverage (100%) | 100% coverage on governance paths |
| 8 | Ruff Lint | Code quality enforcement |
| 9 | Fortress Validator Tests | FortressValidator integration tests |
| 10 | **Fortress & Governance CI Gate** | Comprehensive governance validation |
| 11 | **Governance Integration Tests** | Full governance test suite |
| 12 | **Governance Lock Immutability** | GovernanceLock tampering prevention |

### Failure Policy

- **No `continue-on-error`**: Every gate is blocking
- **No `allow-failure`**: No soft-skip mechanisms
- **Fail-closed**: Unknown states default to failure
- **Forensic artifacts**: Security artifacts retained for 365 days

---

## 8. Monitoring & Alerting

### Critical Alerts (Prometheus)

| Alert | Severity | Trigger |
|-------|----------|---------|
| `GovernanceBypassAttemptDetected` | CRITICAL | Any bypass attempt (rate > 0) |
| `FortressValidationFailureHigh` | CRITICAL | > 5% validation failure rate |
| `MissingGovernanceContext` | HIGH | Reasoning without governance context |
| `ProofTreeViolationSpike` | CRITICAL | > 5 missing proof trees per minute |
| `AgreementScoreThresholdBreach` | HIGH | Frequent agreement score failures |
| `GovernanceLockNotInitialized` | CRITICAL | Lock not initialized within 2 minutes |
| `GovernanceLockBypassAttempts` | CRITICAL | Any lock bypass attempt |
| `LedgerIntegrityFailure` | CRITICAL | Immutable ledger integrity check failed |

### Grafana Dashboards

- **Governance & Fortress Monitor**: Real-time governance status, validation metrics, security breach events
- **Legal Monitoring**: Legal-specific monitoring for case processing

### Required Alerting Integrations

All CRITICAL alerts **MUST** trigger immediate pages via:
- PagerDuty
- Slack webhook
- Email notification

---

## 9. Deployment Hardening

To deploy the governance kernel safely:

1. **Environment**: Must be `MAHOUN_ENV=production`; mock environments are forbidden
2. **GovernanceLock**: Must be initialized in `STRICT` mode at startup
3. **FortressValidator**: Must run with `strict_mode=True`
4. **RedLines.yaml**: Read-only and immutable during runtime
5. **Prometheus**: Must have governance alert rules loaded
6. **Keys**: Persistent cryptographic keys (not ephemeral) for production
7. **Ledger**: Persistent storage path configured for immutable ledger

---

## 10. Related Documentation

| Document | Path | Description |
|----------|------|-------------|
| API Reference | `docs/API_REFERENCE.md` | Complete API endpoint documentation |
| Developer Guide | `FORTRESS_DEVELOPER_GUIDE.md` | Developer-facing security guide |
| Deployment Guide | `docs/DEPLOYMENT.md` | Production deployment procedures |
| Provenance Spec | `docs/EXPLANATION_PROVENANCE_LAYER_SPEC.md` | Provenance layer specification |
| CI Architecture | `docs/CI_ARCHITECTURE.md` | CI/CD pipeline architecture |
| RedLines Constitution | `constitution/RedLines.yaml` | Governance constitution |
