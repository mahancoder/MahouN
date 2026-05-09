# MAHOUN Backend - Zero-Hallucination AI Reasoning Platform
## Production Deployment Guide

> **Core Value**: Graph-based reasoning engine with 100% groundedness guarantee  
> **Architecture**: Evidence-Linked Verdict Engine + Ultra Graph Builder + Immutable Ledger  
> **Zero-Hallucination Guarantee**: Every conclusion is explicitly linked to evidence in knowledge graph

---

## 🎯 Quick Start (5 Minutes)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Generate secure secrets
make -f Makefile.backend generate-secrets

# 3. Edit .env with generated secrets
vim .env

# 4. Deploy everything
make -f Makefile.backend deploy
```

**Access Points:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/system/health
- Neo4j Browser: http://localhost:7474

---

## 🏗️ Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    MAHOUN Backend                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Evidence-Linked Verdict Engine (Zero-Hallucination) │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Ultra Graph Builder (Knowledge Graph Construction)   │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  5 Guardrails (Safety & Compliance Enforcement)       │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Immutable Ledger (Audit Trail & Reproducibility)    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                  ↓                   ↓
   ┌─────────┐      ┌──────────┐      ┌──────────┐
   │  Neo4j  │      │PostgreSQL│      │  Redis   │
   │ (Graph) │      │ (Audit)  │      │ (Cache)  │
   └─────────┘      └──────────┘      └──────────┘
```

### Critical Dependencies

1. **Neo4j** (CRITICAL) - Graph database for evidence-linked reasoning
   - Resource: 8 CPU, 16GB RAM
   - Plugins: APOC, Graph Data Science
   - Backup: Hourly (immutable reasoning graph)

2. **PostgreSQL** - Relational database for audit trail
   - Resource: 4 CPU, 8GB RAM
   - Backup: Daily (compliance records)

3. **Redis** - Cache and distributed locks
   - Resource: 2 CPU, 4GB RAM
   - Backup: Daily (session state)

4. **ChromaDB** - Vector store for RAG
   - Resource: 4 CPU, 8GB RAM
   - Backup: Weekly (embeddings)

---

## 📋 Prerequisites

### System Requirements

**Minimum (Development):**
- CPU: 4 cores
- RAM: 16GB
- Disk: 50GB SSD
- OS: Linux/macOS/Windows with Docker

**Recommended (Production):**
- CPU: 16+ cores
- RAM: 64GB+
- Disk: 500GB NVMe SSD
- OS: Ubuntu 22.04 LTS / RHEL 9

### Software Requirements

```bash
# Docker & Docker Compose
docker --version  # >= 24.0.0
docker-compose --version  # >= 2.20.0

# Make (for convenience)
make --version

# OpenSSL (for secret generation)
openssl version
```

---

## 🚀 Deployment

### Step 1: Environment Configuration

```bash
# Copy template
cp .env.example .env

# Generate secure secrets
make -f Makefile.backend generate-secrets

# Edit .env file
vim .env
```

**Critical Environment Variables:**

```bash
# Security (REQUIRED)
SECURITY_JWT_SECRET=<generated-secret>
API_KEY=<generated-secret>

# Database Passwords (REQUIRED)
DB_NEO4J_PASSWORD=<generated-secret>
DB_POSTGRES_PASSWORD=<generated-secret>
REDIS_PASSWORD=<generated-secret>

# Neo4j Configuration (CRITICAL for reasoning)
NEO4J_HEAP_SIZE=4G
NEO4J_PAGECACHE_SIZE=2G

# Backend Configuration
MAHOUN_GUARD_MODE=STRICT  # Zero-hallucination enforcement
UNIFIED_LOADER_WORKERS=4
MEMORY_SAFEGUARD_GB=2.0
```

### Step 2: Build Images

```bash
# Build production image
make -f Makefile.backend build

# Or build without cache (clean build)
make -f Makefile.backend build-no-cache
```

### Step 3: Start Services

```bash
# Start all services
make -f Makefile.backend start

# Or with monitoring (Prometheus)
make -f Makefile.backend monitoring
```

### Step 4: Verify Deployment

```bash
# Check health of all services
make -f Makefile.backend health

# Show status
make -f Makefile.backend status

# View logs
make -f Makefile.backend logs
```

---

## 🔧 Operations

### Daily Operations

```bash
# View logs
make -f Makefile.backend logs-backend    # Backend only
make -f Makefile.backend logs-neo4j      # Neo4j only
make -f Makefile.backend logs            # All services

# Check resource usage
make -f Makefile.backend stats

# Restart services
make -f Makefile.backend restart
```

### Database Operations

```bash
# Backup all databases
make -f Makefile.backend db-backup

# Restore PostgreSQL
make -f Makefile.backend db-restore-postgres BACKUP_FILE=./backups/postgres_20240225.sql

# Restore Neo4j
make -f Makefile.backend db-restore-neo4j BACKUP_FILE=./backups/neo4j_20240225.dump

# Access database shells
make -f Makefile.backend shell-neo4j     # Neo4j Cypher shell
make -f Makefile.backend shell-postgres  # PostgreSQL shell
make -f Makefile.backend shell-redis     # Redis CLI
```

### Monitoring

```bash
# Start with Prometheus
make -f Makefile.backend monitoring

# View metrics
make -f Makefile.backend metrics

# Access Prometheus UI
open http://localhost:9090
```

---

## 🔒 Security

### Network Isolation

The deployment uses 4 isolated networks:

1. **mahoun-backend** (172.28.1.0/24) - Public-facing
2. **mahoun-database** (172.28.2.0/24) - Internal only
3. **mahoun-cache** (172.28.3.0/24) - Internal only
4. **mahoun-monitoring** (172.28.4.0/24) - Monitoring

Databases are NOT exposed to the internet by default.

### Non-Root Execution

Backend runs as user `mahoun` (UID 1000) with:
- No password login
- Restricted file permissions (700 for sensitive dirs)
- Minimal system capabilities

### Secret Management

```bash
# Generate new secrets
make -f Makefile.backend generate-secrets

# Never commit .env to git!
# .env is in .gitignore by default
```

### Security Scanning

```bash
# Scan images for vulnerabilities
make -f Makefile.backend scan
```

---

## 💾 Data Persistence

### Critical Volumes (MUST backup)

1. **backend_ledger** - Immutable audit trail
   - Backup: Hourly
   - Retention: Permanent
   - Location: `/var/lib/docker/volumes/mahoun_backend_ledger`

2. **neo4j_data** - Knowledge graph
   - Backup: Hourly
   - Retention: 90 days
   - Location: `/var/lib/docker/volumes/mahoun_neo4j_data`

3. **postgres_data** - Metadata & audit
   - Backup: Daily
   - Retention: 30 days
   - Location: `/var/lib/docker/volumes/mahoun_postgres_data`

### Backup Strategy

```bash
# Automated daily backup (add to crontab)
0 2 * * * cd /path/to/mahoun && make -f Makefile.backend db-backup

# Backup to remote storage (example with S3)
aws s3 sync ./backups/ s3://mahoun-backups/$(date +%Y%m%d)/
```

---

## 📊 Monitoring & Metrics

### Health Checks

```bash
# Quick health check
curl http://localhost:8000/system/health

# Detailed status
make -f Makefile.backend health
```

### Prometheus Metrics

Start with monitoring profile:

```bash
make -f Makefile.backend monitoring
```

**Available Metrics:**
- Backend: http://localhost:8000/metrics
- Neo4j: http://localhost:2004/metrics
- Prometheus UI: http://localhost:9090

**Key Metrics to Monitor:**
- `mahoun_verdict_latency_seconds` - Reasoning latency
- `mahoun_graph_nodes_total` - Knowledge graph size
- `mahoun_guardrail_violations_total` - Safety violations
- `mahoun_ledger_entries_total` - Audit trail growth

---

## 🧪 Testing

### Run Tests

```bash
# All tests
make -f Makefile.backend test

# Unit tests only (fast)
make -f Makefile.backend test-unit

# Integration tests (requires running services)
make -f Makefile.backend test-integration
```

---

## 🔄 Updates & Maintenance

### Update to Latest Version

```bash
# Pull latest images
make -f Makefile.backend pull

# Restart with new images
make -f Makefile.backend update
```

### Cleanup

```bash
# Remove stopped containers
make -f Makefile.backend clean

# Remove all data (WARNING: destructive!)
make -f Makefile.backend clean-volumes

# Deep clean (everything)
make -f Makefile.backend prune
```

---

## 🐛 Troubleshooting

### Backend Not Starting

```bash
# Check logs
make -f Makefile.backend logs-backend

# Common issues:
# 1. Missing environment variables
make -f Makefile.backend env-check

# 2. Port already in use
lsof -i :8000

# 3. Database not ready
make -f Makefile.backend health
```

### Neo4j Connection Issues

```bash
# Check Neo4j logs
make -f Makefile.backend logs-neo4j

# Verify Neo4j is running
docker exec mahoun-neo4j cypher-shell -u neo4j -p $DB_NEO4J_PASSWORD "RETURN 1"

# Check memory allocation
docker stats mahoun-neo4j
```

### Out of Memory

```bash
# Check resource usage
make -f Makefile.backend stats

# Adjust memory limits in docker-compose.backend.yml:
# backend: 16G -> 32G
# neo4j: 16G -> 32G
```

### Performance Issues

```bash
# Check slow queries in Neo4j
docker exec mahoun-neo4j cypher-shell -u neo4j -p $DB_NEO4J_PASSWORD \
  "CALL dbms.listQueries() YIELD query, elapsedTimeMillis WHERE elapsedTimeMillis > 1000 RETURN query, elapsedTimeMillis"

# Check PostgreSQL slow queries
docker exec mahoun-postgres psql -U mahoun -d mahoun -c \
  "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10"
```

---

## 📚 API Documentation

Once deployed, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🎯 Zero-Hallucination Guarantees

### Invariant I1: 100% Groundedness

Every reasoning step MUST link to graph evidence:

```python
# Example verdict structure
{
  "verdict": "APPROVED",
  "confidence": 0.95,
  "evidence_chain": [
    {"node_id": "n123", "type": "Contract", "property": "status"},
    {"node_id": "n456", "type": "Clause", "property": "compliance"}
  ],
  "reasoning_path": ["n123", "r789", "n456"],
  "ledger_entry_id": "led_abc123"
}
```

### Fail-Fast Design

System will REFUSE to operate if:
- Graph database is unavailable
- Evidence chain is incomplete
- Guardrails detect violations
- Ledger write fails

**No silent degradation. No partial results.**

---

## 🔐 Compliance & Audit

### Immutable Ledger

Every operation is recorded in the immutable ledger:

```bash
# View ledger entries
docker exec mahoun-backend ls -la /app/ledger/

# Ledger structure:
# /app/ledger/
#   ├── 2024/
#   │   ├── 02/
#   │   │   ├── 25/
#   │   │   │   ├── verdict_001.json
#   │   │   │   ├── verdict_002.json
```

### Audit Trail

PostgreSQL stores complete audit trail:

```sql
-- Query audit trail
SELECT * FROM audit_log 
WHERE entity_type = 'verdict' 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## 📞 Support

### Logs Location

- Backend: `docker logs mahoun-backend`
- Neo4j: `docker logs mahoun-neo4j`
- PostgreSQL: `docker logs mahoun-postgres`

### Debug Mode

```bash
# Start in development mode with debug logging
docker-compose -f docker-compose.dev.yml up
```

---

## 📝 License

Proprietary - MAHOUN Platform

---

## 🚀 Next Steps

1. ✅ Deploy backend
2. ✅ Verify health checks
3. ✅ Configure monitoring
4. ✅ Set up automated backups
5. ✅ Test API endpoints
6. ✅ Review security settings
7. ✅ Configure alerting
8. ✅ Document custom workflows

---

**Built with ❤️ for Zero-Hallucination AI Reasoning**
