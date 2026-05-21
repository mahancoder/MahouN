# MahouN Governance & Provenance Overview

## 1. Core Governance Philosophy
MahouN is built on a **Governance-Native Execution Substrate**. This means that security, compliance, and deterministic execution are not bolted-on features; they are foundational requirements enforced at the lowest levels of the architecture.

The core philosophy is: **Truth > Determinism > Governance > Autonomy.**
Every reasoning step, API call, and graph mutation must be governed by strict rules, leaving no room for unvalidated autonomy or "hallucinated" behaviors.

## 2. The Fortress Validator
The `FortressValidator` is the primary mechanism for forensic validation. It intercepts all AI reasoning outputs and ensures they comply with the `RedLines.yaml` constitution before they are allowed to proceed.

### Validation Gates:
- **Proof Tree Requirement**: Every decision must carry a fully deterministic proof tree.
- **Agreement Score Check**: Hybrid reasoning (neural + symbolic) must achieve an agreement score of ≥ 0.85.
- **Evidence Linkage**: Facts derived from the graph must be explicitly cited as evidence.
- **Contradiction Detection**: Rejects outputs where the LLM contradicts the established symbolic graph logic.

### CI/CD Enforcement
The validator runs in a strict fail-closed mode in the CI/CD pipeline. Any commit that bypasses the Fortress Validator, lowers threshold requirements, or introduces logic that fails the validation gates will instantly break the build (`Gate 9`).

## 3. Governance Context Manager
All reasoning executions must run within a securely tracked context. The `GovernanceContextManager` guarantees that:
- Every execution has a unique correlation ID and forensic context.
- The provenance (lineage) of every piece of data is tracked from ingestion to the final output.
- Missing contexts result in a `SecurityBreachException`.

### Usage Pattern
```python
async with GovernanceContextManager() as ctx:
    # Operations are now governed and provenance is recorded
    result = await my_protected_service.reason(query, ctx)
```

## 4. Provenance and Lineage Tracking
Provenance refers to the undeniable, cryptographically verified history of how a verdict or decision was reached.
- **Data Provenance**: Every node in the Neo4j graph contains metadata regarding its source document, extraction timestamp, and the AI agent that processed it.
- **Execution Provenance**: `ProofCarryingResponse` objects ensure that the API always returns not just the answer, but the complete, verifiable audit trail (Proof Tree, Agreement Score, Execution Time, Audit Hash).

## 5. Deployment Hardening
To deploy the governance kernel safely:
- The system must not run with mock environments in production (`MAHOUN_ENV=production`).
- The `RedLines.yaml` configuration is read-only and immutable during runtime.
- Prometheus monitors (e.g., `GovernanceBypassAttemptDetected`) must be wired to PagerDuty or an equivalent alerting system to notify operators of zero-day bypass attempts.
