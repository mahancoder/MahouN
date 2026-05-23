# MAHOUN API Reference

Welcome to the MAHOUN API reference. This document provides detailed information about the endpoints available in the MAHOUN platform.

## Base URL
The API is typically served at `http://<host>:<port>/api/v1`.

## Authentication
Most endpoints require authentication. Use the `X-API-Key` header with your valid API key.

## Governance Enforcement

> [!IMPORTANT]
> **All reasoning endpoints are protected by the Fortress Validator and require an active GovernanceContext.** Responses from these endpoints always adhere to the `ProofCarryingResponse` format, containing a cryptographic `audit_hash`, `validation_timestamp`, deterministic `proof_tree`, and `correlation_id`.

### ProofCarryingResponse Fields
Every governed response includes these proof-carrying contract fields:

| Field | Type | Description |
|-------|------|-------------|
| `fortress_validated` | `bool` | Whether the response passed Fortress validation |
| `audit_hash` | `string` | SHA-256 hash for tamper-evident audit trail |
| `validation_timestamp` | `string` | ISO 8601 timestamp of validation |
| `correlation_id` | `string` | Unique correlation ID for end-to-end tracing |

---

## 1. Core Reasoning (Analysis)
**Router**: `/api/v1/reasoning`

### [POST] `/generate-verdict`
Generate an evidence-linked legal verdict with zero-hallucination guarantee.

**Governance Flow:**
1. Establish `GovernanceContext` (correlation lineage, runtime attestation)
2. Build case graph from facts
3. Find applicable rules and precedents
4. Detect and resolve contradictions (deterministic)
5. Generate verdict steps with evidence links
6. Write to immutable ledger
7. Generate cryptographic proof
8. Fortress validation (proof tree, agreement score, evidence linkage)

- **Request**: `VerdictGenerationRequest`
    - `question`: Required string — Legal question to answer
    - `facts`: List of `FactInput` — Case facts (each with `value`, optional `id`, `type`, `confidence`)
    - `case_id`: Optional string — Case identifier
    - `generate_proof`: Boolean (default: `true`) — Whether to generate cryptographic proof
- **Response**: `VerdictGenerationResponse` (extends `ProofCarryingResponse`)
    - `success`: Boolean
    - `verdict_id`: Unique ID for the verdict
    - `case_id`: Case identifier
    - `final_verdict`: The determined verdict text
    - `steps`: List of `VerdictStepResponse` — Each step contains `statement` and `evidence` references
    - `unresolved_conflicts`: List of strings — Any unresolved contradictions
    - `confidence_score`: Float (0-1)
    - `proof`: Optional `CryptographicProofResponse` — Graph state hash, reasoning chain hash, evidence Merkle root, signature
    - `ledger_entry_id`: Immutable ledger entry ID
    - `processing_time_ms`: Processing time in milliseconds
    - `metadata`: Additional metadata dictionary

**Error Codes:**
- `503`: Service unavailable in DESKTOP_MINIMAL mode (requires ENTERPRISE_FULL)
- `422`: Invalid input (missing question, invalid facts)
- `500`: Internal processing error

### [POST] `/verify-verdict`
Verify the cryptographic proof of a previously generated verdict.

**Verification Checks:**
1. Signature validity (Ed25519)
2. Timestamp validity (not in future)
3. Confidence range [0, 1]
4. Graph state integrity
5. Reasoning chain integrity

- **Request**: `VerdictVerificationRequest`
    - `verdict_id`: Required string — Verdict identifier
    - `proof`: Required `CryptographicProofResponse` — The proof to verify
- **Response**: `VerdictVerificationResponse` (extends `ProofCarryingResponse`)
    - `success`: Boolean
    - `verdict_id`: Verdict identifier
    - `is_valid`: Boolean — True if all verification checks pass
    - `verification_details`: Dictionary — Detailed check results (signature_valid, timestamp_valid, confidence_valid, verdict_id_match)
    - `timestamp`: ISO 8601 timestamp

### [POST] `/query-ledger`
Query the blockchain ledger for audit trail entries.

**Query Options:**
- By `case_id`: All verdicts for a case
- By `verdict_id`: Specific verdict entry
- By `node_id`: All verdicts using a graph node
- By time range: Entries in a time window

- **Request**: `LedgerQueryRequest`
    - `case_id`: Optional string
    - `verdict_id`: Optional string
    - `node_id`: Optional string
    - `start_time`: Optional string (ISO 8601)
    - `end_time`: Optional string (ISO 8601)
- **Response**: `LedgerQueryResponse` (extends `ProofCarryingResponse`)
    - `success`: Boolean
    - `entries`: List of ledger entry dictionaries
    - `total_count`: Integer — Total matching entries
    - `query_time_ms`: Float — Query processing time

### [GET] `/health`
Health check for the reasoning API subsystem.

- **Response**: Health status dictionary
    - `status`: "healthy", "unavailable", or "unhealthy"
    - `mode`: Current execution mode
    - `graph_enabled`: Boolean
    - `components`: Component initialization status
    - `timestamp`: ISO 8601 timestamp

---

## 2. Document Ingestion
**Router**: `/ingest`

### [POST] `/jobs`
Submit a document for asynchronous ingestion into the knowledge graph.
- **Request**: Multipart/Form-Data
    - `file`: UploadFile (PDF, DOCX, TXT)
- **Response**: Returns a `job_id`

### [GET] `/jobs/{job_id}`
Track the status of an ingestion job.
- **Statuses**: `queued`, `processing`, `completed`, `failed`

### [GET] `/dlq`
List items in the Dead Letter Queue (failed ingestion jobs).

---

## 3. Legal Search
**Router**: `/search`

### [POST] `/verdicts`
Search for legal verdicts using natural language.
- **Request**: `VerdictSearchRequest`
    - `query`: Search string
    - `filters`: Optional `SearchFilters` (court_level, date_range, etc.)
- **Response**: `VerdictSearchResponse`
    - `results`: List of `VerdictHit` objects with relevance scores

---

## 4. System Health
**Router**: `/health` (or `/system`)

### [GET] `/health`
Comprehensive health check for all system components.
- **Components**: PostgreSQL, Neo4j, Redis, Vector Store, GovernanceLock
- **Response**: Detailed latency and status for each component

### [GET] `/health/governance`
Governance-specific health check.
- **Response**: GovernanceLock audit metadata including:
    - `initialized`: Boolean
    - `mode`: Current governance mode (STRICT/AUDIT/DISABLED)
    - `integrity_verified`: Boolean
    - `change_attempts`: Number of bypass attempts
    - `bypass_attempts`: Detailed bypass attempt log

### [GET] `/status`
Lightweight API availability check.

---

## 5. Upload & Processing
**Router**: `/mahoun`

### [POST] `/upload`
Upload and process documents for analysis.
- **Request**: Multipart/Form-Data
    - `file`: UploadFile (PDF, DOCX, TXT)
    - `doc_type`: Optional string (contract, letter, etc.)
- **Response**: `DocumentUploadResponse`
    - `document_id`: Unique ID for the uploaded document
    - `normalized`: Dictionary of extracted/normalized content

### [POST] `/analyze_delay`
Analyze project delays based on schedules.
- **Request**: `DelayAnalysisRequest`
    - `project_id`: Required string
    - `baseline_schedule`: Optional dictionary
- **Response**: `DelayAnalysisResponse`
    - `delays`: List of identified delay events
    - `critical_path`: List of critical tasks

### [POST] `/generate_claim`
Generate a legal claim draft.
- **Request**: `ClaimGenerationRequest`
    - `claim_type`: Type of claim
    - `facts`: Fact description
- **Response**: `ClaimGenerationResponse`
    - `claim_content`: Generated claim text
    - `citations`: List of legal citations

### [POST] `/ask_contract`
Ask questions about a specific contract.
- **Request**: `ContractQueryRequest`
    - `query`: The question
    - `contract_id`: The document ID
- **Response**: `ContractQueryResponse`
    - `answer`: Reasoning response
    - `confidence`: Confidence score (0-1)
    - `verified`: Boolean indicating grounding in evidence

---

## Error Response Format
All API errors follow a consistent format:

```json
{
    "error": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {}
}
```

### Error Codes
| Code | Description |
|------|-------------|
| `VERDICT_GENERATION_ERROR` | Failed to generate verdict |
| `VERIFICATION_ERROR` | Failed to verify cryptographic proof |
| `VALIDATION_ERROR` | Input validation failed |
| `INTERNAL_ERROR` | Internal server error |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `AUTHENTICATION_ERROR` | Invalid or missing API key |
