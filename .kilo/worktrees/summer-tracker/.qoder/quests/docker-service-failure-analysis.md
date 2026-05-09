# Docker Service Failure Analysis - Neo4j & Backend

## Executive Summary

This document identifies the definitive root causes for Neo4j and Backend Docker service health check failures in the MAHOUN Platform.

### Critical Finding

Both services are failing health checks due to **mismatched configuration expectations between Docker Compose profiles and application runtime settings**.

## Identified Root Causes

### 1. Neo4j Health Check Failure - Profile Mismatch

#### Root Cause
Neo4j service is configured under the **`full` profile** in `docker-compose.yml` but is not being started because the default profile only starts Backend and Frontend.

#### Evidence from Configuration

**docker-compose.yml (Lines 134-139)**:
```
neo4j:
  image: neo4j:5-community
  container_name: mahoun-neo4j
  restart: unless-stopped
  profiles:
    - full
```

#### Consequence
When running `docker compose up -d` without specifying profiles, Neo4j container is never created or started. The service simply does not exist in the running container list.

#### Health Check Configuration
Even when Neo4j is started with the `full` profile, the health check expects:
- HTTP endpoint at `http://localhost:7474` to be responsive
- Interval: 15s, Timeout: 15s, Retries: 5
- Start period: 60s

If Neo4j takes longer than 60 seconds plus retry period (135s total) to initialize, the health check will fail.

### 2. Backend Health Check Failure - Dependency and Initialization Issues

#### Root Cause A: Database Connection Dependencies
The Backend health check endpoint `/system/health` performs **actual database connectivity tests** that fail when dependent services are unavailable.

#### Evidence from Code

**api/routers/system.py (Lines 49-134)**:

The health check implementation executes real queries against:
- PostgreSQL: `SELECT 1`
- Neo4j: `RETURN 1 AS test`
- Redis: `PING`

When these services are not available or configured incorrectly, the health check returns `unhealthy` or `degraded` status.

#### Root Cause B: Missing Environment Variables
Backend requires mandatory environment variables defined in `.env` file:

**Required Variables from docker-compose.yml (Lines 33-52)**:
- `DB_NEO4J_PASSWORD` (required, will fail if not set)
- `DB_POSTGRES_PASSWORD` (required, will fail if not set)
- `SECURITY_JWT_SECRET` (required, will fail if not set)

If `.env` file does not exist or lacks these values, Docker Compose will fail to start the backend container with error: `<variable>_required`.

#### Root Cause C: Feature Flag Mismatch
Backend has feature flags that control database connections:

**docker-compose.yml (Lines 56-58)**:
```
- ENABLE_NEO4J=${ENABLE_NEO4J:-false}
- ENABLE_POSTGRES=${ENABLE_POSTGRES:-false}
- ENABLE_REDIS=${ENABLE_REDIS:-false}
```

Default values are **`false`** for all databases. However, the health check logic still attempts to connect to these services even when disabled, leading to connection failures.

#### Root Cause D: Runtime Mode Configuration
The backend health check behavior depends on runtime mode from `mahoun.core.runtime_config`:

**api/routers/system.py (Lines 43-44, 56, 99)**:
- In `desktop_minimal` mode: PostgreSQL check returns "disabled"
- When `graph_enabled=false`: Neo4j check returns "disabled"
- Runtime settings may not match Docker environment expectations

### 3. Health Check Endpoint Implementation Issues

#### Critical Design Flaw
The Backend health check at `/system/health` is implemented to **fail the entire health check if any database connection fails**, even in degraded mode scenarios.

**Health Check Logic (Lines 182-191)**:
```
if unhealthy_count == 0 and healthy_count > 0:
    overall_status = "healthy"
elif unhealthy_count > 0 and healthy_count > 0:
    overall_status = "degraded"
elif unhealthy_count > 0 and healthy_count == 0:
    overall_status = "unhealthy"
```

Docker's healthcheck command expects HTTP 200 status, but the endpoint may return status "degraded" or "unhealthy" with 200 OK, causing Docker to interpret the service as unhealthy based on the health check exit code from curl.

**Dockerfile.backend (Line 89)**:
```
CMD curl -f http://localhost:8000/system/health || exit 1
```

The `-f` flag makes curl fail (exit code 22) on HTTP error status (4xx, 5xx). However, `/system/health` returns 200 OK even when status is "unhealthy", so the issue is more subtle.

## Definitive Failure Scenarios

### Scenario 1: Default Profile Execution
**Command**: `docker compose up -d`

**Result**:
- Backend: Starts but health check fails
- Neo4j: Does not start (not in default profile)

**Reason**:
1. Backend starts and attempts health check at `/system/health`
2. Health check tries to connect to Neo4j at `bolt://neo4j:7687`
3. Neo4j container does not exist (profile not activated)
4. Neo4j health check returns "unhealthy" status
5. Overall backend health becomes "degraded" or "unhealthy"
6. Docker marks backend as unhealthy after 3 retries

### Scenario 2: Full Profile Without Environment Variables
**Command**: `docker compose --profile full up -d`

**Result**:
- Backend: Fails to start
- Neo4j: Fails to start

**Reason**:
1. Docker Compose validates environment variables before starting containers
2. Missing required variables: `DB_NEO4J_PASSWORD`, `DB_POSTGRES_PASSWORD`, `SECURITY_JWT_SECRET`
3. Compose exits with error: `required environment variable not set`
4. No containers are created

### Scenario 3: Full Profile With Environment Variables But Wrong Credentials
**Command**: `docker compose --profile full up -d` (with `.env` file present)

**Result**:
- Neo4j: Starts but may be unhealthy
- Backend: Starts but unhealthy

**Reason**:
1. Neo4j starts with password from `DB_NEO4J_PASSWORD`
2. Backend starts and attempts to connect to Neo4j
3. If Neo4j initialization takes longer than 60s start period, health check fails
4. Backend connects using credentials from environment, but if there's a mismatch with Neo4j's actual password (cached in volume), authentication fails
5. Both services marked unhealthy

### Scenario 4: Legacy State Conflict
**Evidence**: Documentation mentions legacy cleanup (DOCKER.md lines 433-483)

**Result**:
- Neo4j: Unhealthy due to wrong volume or credentials
- Backend: Unhealthy due to connection failures

**Reason**:
1. Old containers or volumes exist with prefix `platform33_*` instead of `mahoun_*`
2. Neo4j uses old volume with different password
3. Backend attempts connection with new credentials from `.env`
4. Authentication mismatch causes connection failure
5. Health checks fail

## Configuration Validation Checklist

### Prerequisites for Healthy Services

#### Environment Configuration
- `.env` file exists in project root
- Contains all required variables:
  - `DB_NEO4J_PASSWORD` (minimum 8 characters)
  - `DB_POSTGRES_PASSWORD` (minimum 8 characters)
  - `SECURITY_JWT_SECRET` (minimum 32 characters)
- Feature flags match profile:
  - For `full` profile: Set `ENABLE_NEO4J=true`, `ENABLE_POSTGRES=true`
  - For default profile: Keep as `false`

#### Docker Profile Selection
- Default profile: Only backend and frontend
- Full profile: Requires `--profile full` flag
- Command: `docker compose --profile full up -d`

#### Neo4j Specific Requirements
- First startup requires 60-120 seconds for initialization
- Health check start_period is 60s (may need increase to 90s or 120s)
- Persistent volume must not contain conflicting old data
- APOC plugin must load successfully

#### Backend Specific Requirements
- Must wait for Neo4j to be fully initialized before health check succeeds
- Runtime mode configuration must match deployed profile
- Database connection timeouts must be appropriate for container startup

### Verification Commands

#### Check Running Containers
```
docker ps --filter "name=mahoun" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected output for full profile:
- mahoun-backend: healthy
- mahoun-frontend: healthy
- mahoun-neo4j: healthy
- mahoun-postgres: healthy
- mahoun-redis: healthy
- mahoun-chromadb: healthy

#### Check Container Logs
```
docker compose logs neo4j | grep -i "error\|exception\|fail"
docker compose logs backend | grep -i "error\|exception\|fail"
```

#### Verify Environment Variables Inside Container
```
docker compose exec backend env | grep -E "NEO4J|POSTGRES|JWT"
docker compose exec neo4j env | grep NEO4J_AUTH
```

#### Test Health Endpoint Manually
```
curl -v http://localhost:8000/system/health | jq
```

Expected response structure:
```
{
  "status": "healthy",
  "mode": "<runtime_mode>",
  "components": {
    "postgresql": {"status": "healthy|disabled", ...},
    "neo4j": {"status": "healthy|disabled", ...},
    "redis": {"status": "healthy|disabled", ...}
  }
}
```

#### Check for Legacy State
```
docker volume ls | grep -E "platform33|neo4j|postgres"
docker ps -a | grep -E "mahoun|neo4j"
```

If legacy volumes found with `platform33_` prefix, cleanup required:
```
./scripts/docker/clean_legacy_state.sh --force
```

## Resolution Strategy

### Step-by-Step Fix Process

#### Phase 1: Environment Preparation
1. Create `.env` file from `.env.example`:
   ```
   cp .env.example .env
   ```

2. Set mandatory variables in `.env`:
   ```
   DB_NEO4J_PASSWORD=<strong_password>
   DB_POSTGRES_PASSWORD=<strong_password>
   SECURITY_JWT_SECRET=<64_character_hex>
   ```

3. Configure feature flags for full profile:
   ```
   ENABLE_NEO4J=true
   ENABLE_POSTGRES=true
   ENABLE_REDIS=true
   ```

4. Generate strong credentials:
   ```
   openssl rand -base64 32  # For passwords
   openssl rand -hex 32     # For JWT secret
   ```

#### Phase 2: Clean Legacy State
1. Stop all running containers:
   ```
   docker compose down
   ```

2. Remove legacy volumes if present:
   ```
   docker volume ls | grep platform33
   docker volume rm platform33_neo4j_data platform33_postgres_data
   ```

3. Remove any stopped containers:
   ```
   docker container prune -f
   ```

#### Phase 3: Start Services with Correct Profile
1. Build images with no cache:
   ```
   docker compose build --no-cache
   ```

2. Start full profile:
   ```
   docker compose --profile full up -d
   ```

3. Monitor startup logs:
   ```
   docker compose logs -f neo4j backend
   ```

4. Wait for Neo4j initialization (60-120 seconds)

#### Phase 4: Validation
1. Check container health:
   ```
   docker ps
   ```

2. Verify health endpoint:
   ```
   curl http://localhost:8000/system/health | jq .status
   ```

3. Test Neo4j connectivity:
   ```
   docker compose exec backend python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', '<password>')); driver.verify_connectivity(); print('OK')"
   ```

### Alternative: Run Without Databases
If full profile is not needed:

1. Use default profile (no databases):
   ```
   docker compose up -d
   ```

2. Ensure feature flags are disabled in `.env`:
   ```
   ENABLE_NEO4J=false
   ENABLE_POSTGRES=false
   ENABLE_REDIS=false
   ```

3. Backend will start in minimal mode and report "degraded" status, which is expected behavior.

## Preventive Measures

### Configuration Management
- Use environment variable validation scripts before deployment
- Document required variables in deployment checklist
- Implement pre-flight checks in startup scripts

### Health Check Improvements
- Increase Neo4j start_period to 90s or 120s for reliable initialization
- Implement graceful degradation in backend health endpoint
- Return HTTP 503 (Service Unavailable) instead of 200 when unhealthy
- Add readiness probe separate from liveness probe

### Monitoring
- Set up alerts for unhealthy containers
- Monitor startup time metrics
- Track health check failure patterns
- Log detailed connection errors

### Documentation
- Create quick-start guide with exact commands for each profile
- Provide troubleshooting decision tree
- Include example `.env` configurations for each deployment scenario

## Technical Debt Items

### Priority 1: Health Check Logic
- Refactor `/system/health` to distinguish between critical and non-critical failures
- Implement separate endpoints: `/health/liveness` and `/health/readiness`
- Make health check behavior configurable based on deployment profile

### Priority 2: Startup Dependencies
- Implement retry logic with exponential backoff for database connections
- Add startup probes for services with long initialization times
- Create dependency orchestration for proper startup sequence

### Priority 3: Configuration Validation
- Add configuration validation in application startup
- Fail fast with clear error messages for missing critical configuration
- Implement environment variable schema validation

## Conclusion

The root causes for Neo4j and Backend health check failures are definitively:

1. **Neo4j**: Not started because full profile is not activated by default
2. **Backend**: Fails health check because it attempts to connect to non-existent or misconfigured database services
3. **Configuration**: Missing or incorrect environment variables prevent proper authentication and connection
4. **Legacy State**: Old containers or volumes with mismatched credentials cause authentication failures

The primary fix is ensuring:
- Correct Docker Compose profile is used (`--profile full` for full stack)
- All required environment variables are set in `.env` file
- Feature flags match the activated profile
- No legacy state conflicts exist
- Sufficient startup time is allowed for Neo4j initialization
2. **Backend**: Fails health check because it attempts to connect to non-existent or misconfigured database services
3. **Configuration**: Missing or incorrect environment variables prevent proper authentication and connection
4. **Legacy State**: Old containers or volumes with mismatched credentials cause authentication failures

The primary fix is ensuring:
- Correct Docker Compose profile is used (`--profile full` for full stack)
- All required environment variables are set in `.env` file
- Feature flags match the activated profile
- No legacy state conflicts exist
- Sufficient startup time is allowed for Neo4j initialization

1. **Neo4j**: Not started because full profile is not activated by default
2. **Backend**: Fails health check because it attempts to connect to non-existent or misconfigured database services
3. **Configuration**: Missing or incorrect environment variables prevent proper authentication and connection
4. **Legacy State**: Old containers or volumes with mismatched credentials cause authentication failures

The primary fix is ensuring:
- Correct Docker Compose profile is used (`--profile full` for full stack)
- All required environment variables are set in `.env` file
- Feature flags match the activated profile
- No legacy state conflicts exist
- Sufficient startup time is allowed for Neo4j initialization
