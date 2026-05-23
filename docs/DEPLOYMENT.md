# MAHOUN Deployment Guide 🚀

**Version**: 2.0.0
**Last Updated**: May 21, 2026

This guide covers the complete deployment lifecycle for the MAHOUN platform, including governance verification, staging deployment, smoke tests, and production hardening.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Local Development](#2-local-development)
3. [Staging Deployment](#3-staging-deployment)
4. [Production Deployment](#4-production-deployment)
5. [Governance Verification](#5-governance-verification)
6. [Smoke Tests](#6-smoke-tests)
7. [Monitoring Setup](#7-monitoring-setup)
8. [Rollback Procedures](#8-rollback-procedures)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.12+ | 3.12.x |
| Docker | 24.0+ | Latest stable |
| Docker Compose | 2.20+ | Latest stable |
| RAM | 8 GB | 16 GB |
| Disk | 20 GB | 50 GB (SSD) |

### Required Services

| Service | Purpose | Port |
|---------|---------|------|
| Neo4j | Knowledge graph | 7474 (HTTP), 7687 (Bolt) |
| PostgreSQL | Metadata storage | 5432 |
| Redis | Caching & distributed locks | 6379 |
| ChromaDB | Vector store | 8001 |
| Prometheus | Metrics collection | 9090 |
| Grafana | Dashboards | 3000 |

---

## 2. Local Development

### Quick Start

```bash
# Clone and enter project
git clone https://github.com/your-org/mahoun.git
cd mahoun

# Setup environment
cp .env.example .env
# EDIT .env WITH YOUR LOCAL SETTINGS

# Install Python dependencies
python -m venv venv
source venv/bin/activate
pip install -e ".[dev,full]"

# Start development services
make dev
# OR: docker-compose -f docker-compose.dev.yml up
```

### Local Test Execution

```bash
# Run unit tests (default: excludes integration/slow)
pytest tests/ -v --tb=short

# Run governance tests specifically
pytest tests/governance/ -v --tb=short

# Run fortress validator tests
pytest tests/test_fortress_validator.py -v --tb=short

# Run CI governance gate locally
python ci/scripts/fortress_governance_gate.py
```

---

## 3. Staging Deployment

### Pre-Deployment Checklist

- [ ] All CI/CD gates pass (unified governance workflow)
- [ ] Governance tests pass (`tests/governance/`)
- [ ] Fortress validator tests pass
- [ ] No security audit findings
- [ ] `RedLines.yaml` unchanged from approved version
- [ ] Docker images built successfully

### Deployment Steps

```bash
# 1. Build staging images
docker build -t mahoun/backend:staging -f Dockerfile.backend --target production .

# 2. Set staging environment
export MAHOUN_ENV=staging
export MAHOUN_GOVERNANCE_MODE=STRICT

# 3. Start staging stack
docker-compose -f docker-compose.prod.yml up -d

# 4. Wait for services to be healthy
docker-compose -f docker-compose.prod.yml ps

# 5. Run smoke tests against staging
./scripts/deploy_server.sh staging

# 6. Verify governance initialization
curl -s http://localhost:8000/health/governance | python -m json.tool
```

### Staging Governance Requirements

| Requirement | Expected Value |
|-------------|---------------|
| `MAHOUN_GOVERNANCE_MODE` | `STRICT` or `AUDIT` |
| GovernanceLock initialized | `true` |
| GovernanceLock integrity | `verified` |
| GovernanceLock immutability | `verified` |
| FortressValidator strict_mode | `true` |
| GovernanceContext enforcement | `active` |
| Provenance tracking | `enabled` |
| Proof-carrying responses | `enforced` |
| Prometheus alert rules loaded | `true` |

---

## 4. Production Deployment

### Pre-Production Checklist

- [ ] Staging deployment successful
- [ ] All smoke tests pass on staging
- [ ] Performance benchmarks within acceptable range
- [ ] Security team sign-off
- [ ] Governance audit metadata reviewed
- [ ] Monitoring alerts verified functional
- [ ] Rollback plan documented

### Secrets Management

**CRITICAL**: Do NOT store production passwords in `.env` files. Use:
- AWS Secrets Manager
- HashiCorp Vault (see `scripts/setup_vault.sh`)
- GitHub Actions Secrets (for CI/CD)

### Network Security

Ensure the following ports are **NOT** exposed to the public internet:

| Port | Service | Access |
|------|---------|--------|
| 7687 | Neo4j Bolt | Internal only |
| 5432 | PostgreSQL | Internal only |
| 6379 | Redis | Internal only |
| 9090 | Prometheus | VPN/SSH tunnel |
| 3000 | Grafana | VPN/SSH tunnel |

Only port `8000` (FastAPI/MCP) should be exposed via a Reverse Proxy (Nginx/Traefik) with TLS.

### Production Deployment Steps

```bash
# 1. Tag the release
git tag -a v$(cat VERSION) -m "Production release"

# 2. Build production images
make build-backend

# 3. Set production environment variables
export MAHOUN_ENV=production
export MAHOUN_GOVERNANCE_MODE=STRICT
# NEVER set MAHOUN_GOVERNANCE_MODE=DISABLED in production

# 4. Deploy
make prod

# 5. Verify governance state
curl -s http://localhost:8000/health/governance

# 6. Verify Fortress
curl -s http://localhost:8000/api/v1/reasoning/health

# 7. Run production smoke tests
pytest tests/test_smoke.py -v --tb=short
```

### Production Governance Requirements

| Requirement | Expected Value | Consequence if Missing |
|-------------|---------------|----------------------|
| `MAHOUN_ENV` | `production` | Mock environments block production features |
| `MAHOUN_GOVERNANCE_MODE` | `STRICT` | Falls back to STRICT (fail-closed) |
| GovernanceLock | Initialized STRICT | Defaults to STRICT if not initialized |
| GovernanceLock Immutability | Verified | System refuses to start |
| FortressValidator | `strict_mode=True` | SecurityBreachException on violations |
| GovernanceContext | Mandatory enforcement | GovernanceViolationError on bypass |
| Provenance Tracking | Cryptographic attestation | Graph mutations blocked |
| ProofCarryingResponse | All API responses | SecurityBreachException on violation |
| RedLines.yaml | Present, read-only | System refuses to start |
| Persistent keys | Configured | Uses ephemeral keys (insecure) |
| Ledger storage | Persistent path | Data loss on restart |
| Correlation Lineage | Tracked | Audit trail incomplete |

### Resource Scaling

For high-traffic deployments:
1. Use Neo4j Enterprise Cluster
2. Run multiple `mahoun-mcp` containers behind a load balancer
3. Increase `WORKERS` in `.env`
4. Configure Redis cluster for distributed locks

---

## 5. Governance Verification

After any deployment, verify governance state:

### 5.1 GovernanceLock Verification

```bash
# Check GovernanceLock status
python -c "
from mahoun.core.governance_lock import GovernanceLock
metadata = GovernanceLock.get_audit_metadata()
print(f'Initialized: {metadata[\"initialized\"]}')
print(f'Mode: {metadata[\"mode\"]}')
print(f'Integrity: {metadata[\"integrity_verified\"]}')
print(f'Immutability: {metadata[\"immutable\"]}')
print(f'Bypass attempts: {metadata[\"change_attempts\"]}')
print(f'Bypass log: {metadata[\"bypass_attempts\"]}')
"

# Expected output:
# Initialized: True
# Mode: STRICT
# Integrity: True
# Immutability: True
# Bypass attempts: 0
# Bypass log: []
```

### 5.2 FortressValidator Verification

```bash
# Check Fortress status
python -c "
from mahoun.core.fortress_validator import FortressValidator
v = FortressValidator(strict_mode=True)
print(f'Strict mode: {v.strict_mode}')
stats = v.get_stats()
print(f'Total validations: {stats[\"total_validations\"]}')
print(f'Passed: {stats[\"passed\"]}')
print(f'Failed: {stats[\"failed\"]}')
print(f'Avg execution time: {stats[\"avg_execution_time_ms\"]}ms')
"
```

### 5.3 GovernanceContext Verification

```bash
# Check GovernanceContext
python -c "
import asyncio
from mahoun.core.governance import GovernanceContextManager

async def check():
    async with GovernanceContextManager.active_context(
        correlation_id='deploy-verify',
        execution_mode='STRICT'
    ) as ctx:
        print(f'Context ID: {ctx.context_id}')
        print(f'Correlation ID: {ctx.correlation_id}')
        print(f'Execution mode: {ctx.execution_mode}')
        print(f'Governance scope: {ctx.governance_scope_injected}')
        print(f'Proof tracking: {ctx.proof_tracking_active}')
        print(f'Contradiction hooks: {ctx.contradiction_hooks_active}')
        print(f'Correlation lineage: {ctx.correlation_lineage}')
        
        # Get runtime attestation
        attestation = ctx.get_attestation()
        print(f'Attestation: {attestation}')
        
        # Validate governance scope
        is_valid = ctx.validate_governance_scope()
        print(f'Governance scope valid: {is_valid}')

asyncio.run(check())
"
```

### 5.4 Provenance Verification

```bash
# Check Provenance tracking
python -c "
import asyncio
from mahoun.core.governance import GovernanceContextManager

async def check():
    async with GovernanceContextManager.active_context(
        correlation_id='provenance-verify'
    ) as ctx:
        # Create provenance
        provenance = GovernanceContextManager.require_provenance(
            source='deployment_verification',
            author='system'
        )
        
        print(f'Source: {provenance.source}')
        print(f'Author: {provenance.author}')
        print(f'Timestamp: {provenance.timestamp}')
        print(f'Correlation ID: {provenance.correlation_id}')
        print(f'Governance scope ID: {provenance.governance_scope_id}')
        print(f'Runtime attestation ID: {provenance.runtime_attestation_id}')
        print(f'Provenance hash: {provenance.provenance_hash}')
        print(f'Provenance signature: {provenance.provenance_signature}')
        print(f'Lineage parent: {provenance.lineage_parent}')

asyncio.run(check())
"
```

### 5.5 API Proof-Carrying Contract Verification

```bash
# Test API endpoint with proof-carrying contract
curl -X POST http://localhost:8000/api/v1/reasoning/generate-verdict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "question": "Is this contract valid?",
    "facts": [
      {"value": "Contract was signed on 2024-01-01", "type": "TEMPORAL"}
    ],
    "generate_proof": true
  }' | python -c "
import sys, json
data = json.load(sys.stdin)

# Verify proof-carrying fields
assert 'fortress_validated' in data, 'Missing fortress_validated'
assert data['fortress_validated'] == True, 'fortress_validated must be True'
assert 'audit_hash' in data, 'Missing audit_hash'
assert len(data['audit_hash']) >= 16, 'audit_hash too short'
assert 'validation_timestamp' in data, 'Missing validation_timestamp'
assert 'correlation_id' in data, 'Missing correlation_id'

print('✅ Proof-carrying contract verified!')
print(f'Fortress validated: {data[\"fortress_validated\"]}')
print(f'Audit hash: {data[\"audit_hash\"]}')
print(f'Validation timestamp: {data[\"validation_timestamp\"]}')
print(f'Correlation ID: {data[\"correlation_id\"]}')
"
```

---

## 6. Smoke Tests

### Automated Smoke Tests (CI/CD)

The deployment-smoke job in the unified governance workflow runs:
1. **Import Integrity**: All governance modules import successfully
2. **GovernanceLock Initialization**: STRICT mode verified
3. **GovernanceLock Immutability**: Mode cannot be changed after initialization
4. **FortressValidator Instantiation**: Strict mode instantiation
5. **GovernanceContext Creation**: Context creation and attestation
6. **GovernanceContext Enforcement**: Operations require active context
7. **Provenance Creation**: Cryptographic attestation verified
8. **ProofCarryingResponse**: API contract enforcement verified
9. **Configuration Validation**: RedLines.yaml loaded
10. **Correlation Lineage**: Parent-child context tracking verified

### Manual Smoke Tests

```bash
# Test API health
curl -s http://localhost:8000/health | python -m json.tool

# Test governance health
curl -s http://localhost:8000/health/governance | python -m json.tool

# Test reasoning health
curl -s http://localhost:8000/api/v1/reasoning/health | python -m json.tool

# Test verdict generation (requires ENTERPRISE_FULL mode)
curl -X POST http://localhost:8000/api/v1/reasoning/generate-verdict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "question": "Is this contract valid?",
    "facts": [
      {"value": "Contract was signed on 2024-01-01", "type": "TEMPORAL"},
      {"value": "Both parties provided consideration", "type": "LEGAL"}
    ],
    "generate_proof": true
  }'
```

---

## 7. Monitoring Setup

### Prometheus Configuration

The Prometheus config (`monitoring/prometheus/prometheus.yml`) must include alert rules:

```yaml
rule_files:
  - '/etc/prometheus/alerts/*.yml'
```

Alert rule files:
- `governance_alerts.yml` — Governance bypass, Fortress failures, missing context
- `deployment_alerts.yml` — Service health, resource usage, ledger integrity
- `legal_monitoring_alerts.yml` — Legal-specific processing alerts

### Grafana Dashboards

Import the following dashboards:
- `monitoring/grafana/dashboards/governance_fortress.json` — Governance & Fortress monitoring
- `monitoring/grafana/dashboards/main.json` — General system monitoring
- `monitoring/grafana/dashboards/legal_monitoring.json` — Legal processing monitoring

### Critical Alerts Configuration

These alerts **MUST** be routed to immediate notification channels:

| Alert | Severity | Action Required |
|-------|----------|----------------|
| `GovernanceBypassAttemptDetected` | CRITICAL | Immediate security review |
| `GovernanceLockBypassAttempts` | CRITICAL | Security incident |
| `GovernanceLockNotInitialized` | CRITICAL | Restart service |
| `FortressValidationFailureHigh` | CRITICAL | Check for hallucination spike |
| `MissingGovernanceContext` | HIGH | Check reasoning operations |
| `ProofTreeViolationSpike` | CRITICAL | > 5 missing proof trees per minute |
| `AgreementScoreThresholdBreach` | HIGH | Frequent agreement score failures |
| `ProvenanceIntegrityFailure` | CRITICAL | Cryptographic attestation failed |
| `LedgerIntegrityFailure` | CRITICAL | Forensic investigation |
| `ProofCarryingContractViolation` | CRITICAL | API contract enforcement failed |
| `CorrelationLineageBreak` | HIGH | Audit trail incomplete |
| `ServiceDown` | CRITICAL | Infrastructure response |

---

## 8. Rollback Procedures

### Quick Rollback

```bash
# Rollback to previous version
docker-compose -f docker-compose.prod.yml down
docker tag mahoun/backend:previous mahoun/backend:latest
docker-compose -f docker-compose.prod.yml up -d

# Verify governance state after rollback
curl -s http://localhost:8000/health/governance
```

### Database Backup & Restore

```bash
# Backup (run before deployment)
make db-backup
# OR:
docker exec mahoun-postgres-prod pg_dump -U mahoun mahoun > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
make db-restore
```

---

## 9. Troubleshooting

| Issue | Solution |
|-------|----------|
| Neo4j connection refused | Ensure Neo4j container is healthy and `NEO4J_URI` is correct |
| GovernanceLock not initialized | Check `MAHOUN_GOVERNANCE_MODE` env var and startup logs |
| GovernanceLock immutability failed | System has been tampered with - investigate immediately |
| FortressValidator strict_mode=False | Verify `MAHOUN_ENV=production` is set |
| Missing governance context | Ensure all reasoning calls go through `GovernanceContextManager.active_context()` |
| Provenance creation failed | Check governance context is active and attestation service is running |
| ProofCarryingResponse validation failed | Verify all API responses inherit from ProofCarryingResponse |
| Correlation lineage broken | Check parent-child context creation and lineage tracking |
| Rate limit 429 errors | Check IP load and adjust settings in `mahoun/mcp/server.py` |
| Auth errors | Ensure `X-API-Key` matches the `MCP_API_KEY` in environment |
| Ledger integrity failure | Check disk space and file permissions on ledger storage |
| Prometheus alerts not firing | Verify `rule_files` directive in `prometheus.yml` and alert file paths |

### Log Rotation

Configure Docker log rotation in `daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Emergency Governance Override

In case of critical production issues requiring governance relaxation:

> [!CAUTION]
> This procedure requires security team authorization and generates a forensic audit entry.

```bash
# 1. Generate daily authorization token
python -c "
import hashlib
from datetime import datetime, UTC
today = datetime.now(UTC).strftime('%Y-%m-%d')
token = hashlib.sha256(f'MAHOUN_DEV_OVERRIDE_{today}'.encode()).hexdigest()
print(f'Token for {today}: {token}')
"

# 2. Set environment (AUDIT mode only, never DISABLED in production)
export MAHOUN_GOVERNANCE_MODE=AUDIT
export MAHOUN_GOVERNANCE_OVERRIDE_TOKEN=<token_from_step_1>

# 3. Restart service
docker-compose -f docker-compose.prod.yml restart backend

# 4. CRITICAL: Revert to STRICT after issue resolved
export MAHOUN_GOVERNANCE_MODE=STRICT
docker-compose -f docker-compose.prod.yml restart backend
```
