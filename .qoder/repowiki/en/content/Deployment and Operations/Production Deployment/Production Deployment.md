# Production Deployment

<cite>
**Referenced Files in This Document**   
- [runtime.json](file://config/runtime.json)
- [runtime.py](file://config/runtime.py)
- [api/config.py](file://api/config.py)
- [mahoun/core/runtime_config.py](file://mahoun/core/runtime_config.py)
- [mahoun/core/secrets.py](file://mahoun/core/secrets.py)
- [docs/DEPLOYMENT.md](file://docs/DEPLOYMENT.md)
- [docs/DOCKER.md](file://docs/DOCKER.md)
- [Dockerfile.backend](file://Dockerfile.backend)
- [.env.example](file://.env.example)
- [docker-compose.yml](file://docker-compose.yml)
- [scripts/docker/validate_docker_setup.sh](file://scripts/docker/validate_docker_setup.sh)
- [scripts/docker/clean_legacy_state.sh](file://scripts/docker/clean_legacy_state.sh)
- [scripts/quickstart.sh](file://scripts/quickstart.sh)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Configuration Management](#configuration-management)
3. [Production Deployment Workflow](#production-deployment-workflow)
4. [Disaster Recovery Procedures](#disaster-recovery-procedures)
5. [Production-Specific Concerns](#production-specific-concerns)
6. [Validation Steps](#validation-steps)
7. [Conclusion](#conclusion)

## Introduction
This document provides comprehensive guidance for hardening the Mahoun platform for production use. It covers configuration management, deployment workflows, disaster recovery, and production-specific concerns. The platform is designed with enterprise-grade security, scalability, and observability in mind, following best practices for containerized deployments.

The system architecture is built around Docker Compose with profile-based deployments, allowing for flexible configuration across different environments. Security is prioritized through strict secrets management, network isolation, and comprehensive validation checks. The platform supports high-availability configurations with resource scaling strategies for critical components.

**Section sources**
- [docs/DEPLOYMENT.md](file://docs/DEPLOYMENT.md#L1-L77)
- [docs/DOCKER.md](file://docs/DOCKER.md#L1-L558)

## Configuration Management
The Mahoun platform employs a multi-layered configuration management system that combines JSON configuration files, environment variables, and Python-based settings classes to provide flexible and secure configuration options for production environments.

### Runtime Configuration with runtime.json
The primary configuration file `runtime.json` serves as the central configuration hub for the platform. This JSON file uses environment variable interpolation with default values, allowing for environment-specific overrides while maintaining sensible defaults.

```json
{
  "environment": {
    "mode": "${MAHOUN_ENV:-dev}",
    "debug": "${MAHOUN_DEBUG:-false}",
    "guard_mode": "${MAHOUN_GUARD_MODE:-STRICT}"
  },
  "features": {
    "graph_enabled": "${MAHOUN_ENABLE_GRAPH:-true}",
    "rag_enabled": "${MAHOUN_ENABLE_RAG:-true}",
    "self_improvement_enabled": "${MAHOUN_ENABLE_SELF_IMPROVEMENT:-false}"
  },
  "database": {
    "neo4j": {
      "uri": "${MAHOUN_NEO4J_URI:-}",
      "user": "${MAHOUN_NEO4J_USER:-neo4j}"
    },
    "redis": {
      "url": "${MAHOUN_REDIS_URL:-}"
    },
    "postgres": {
      "url": "${MAHOUN_POSTGRES_URL:-}"
    }
  }
}
```

The configuration system follows a hierarchy where environment variables take precedence over values in the JSON file, which in turn override hardcoded defaults. This allows for seamless transitions between development, staging, and production environments without modifying configuration files.

**Diagram sources**
- [config/runtime.json](file://config/runtime.json#L1-L89)

### Environment Variables for Feature Flags and Security
Environment variables are used extensively for feature flags and security settings, enabling dynamic configuration without code changes. The platform uses a consistent naming convention with the `MAHOUN_` prefix for all environment variables.

Key security-related environment variables include:
- `MAHOUN_ENV`: Specifies the deployment environment (dev, staging, prod)
- `SECURITY_JWT_SECRET`: Secret key for JWT authentication (must be ≥32 characters)
- `DB_NEO4J_PASSWORD` and `DB_POSTGRES_PASSWORD`: Database credentials
- `MAHOUN_GUARD_MODE`: Security enforcement level (OFF, WARN, STRICT, AUDIT)

Feature flags allow for granular control over platform capabilities:
- `MAHOUN_ENABLE_GRAPH`: Enables/disables knowledge graph features
- `MAHOUN_ENABLE_RAG`: Controls retrieval-augmented generation functionality
- `MAHOUN_ENABLE_SELF_IMPROVEMENT`: Toggles the self-improvement system

The `.env.example` file provides a template for environment configuration, with clear instructions for production use, including commands for generating cryptographically strong secrets using OpenSSL.

**Section sources**
- [config/runtime.json](file://config/runtime.json#L1-L89)
- [.env.example](file://.env.example#L1-L131)

### Advanced Configuration with Pydantic Settings
For more complex configuration needs, the platform implements Pydantic Settings V2 with comprehensive validation. The `api/config.py` module defines structured configuration classes with type hints, validation rules, and computed fields.

The configuration system includes:
- Hierarchical settings with nested configuration objects
- Automatic validation of configuration values
- Computed fields for derived configuration values
- Environment variable prefixing and case insensitivity
- Support for configuration hot-reload

The `Settings` class serves as the main configuration entry point, aggregating database, security, model, feature flag, and monitoring configurations into a single interface. Validation methods ensure that production deployments meet security requirements, such as disabling debug mode and enforcing rate limiting.

**Section sources**
- [api/config.py](file://api/config.py#L1-L435)

## Production Deployment Workflow
The production deployment workflow for the Mahoun platform follows a structured approach that emphasizes security, reliability, and observability. The process is designed to minimize downtime and ensure consistent deployments across environments.

### Secrets Management Best Practices
The platform enforces strict secrets management practices to prevent accidental exposure of sensitive information. The following principles are implemented:

1. **No .env files in production**: Production deployments must use external secret managers rather than `.env` files. Supported options include:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets
   - GitHub Actions Secrets (for CI/CD)

2. **Development vs. Production validation**: The `mahoun/core/secrets.py` module implements different validation rules based on environment:
   - Development: Allows safe placeholder values for convenience
   - Production/Staging: Rejects placeholder values and requires strong secrets

```python
def require_secret(name: str) -> str:
    """
    Get a required secret with strict validation.
    
    SECURITY POLICY:
    - In dev: allows dev defaults for convenience
    - In staging/prod: MUST be set AND not be a dev placeholder
    """
```

3. **Secret generation**: The documentation provides specific commands for generating strong secrets:
   ```bash
   # Generate strong passwords (32 bytes base64):
   openssl rand -base64 32
   
   # Generate strong JWT secret (64 hex chars = 32 bytes):
   openssl rand -hex 32
   ```

**Section sources**
- [mahoun/core/secrets.py](file://mahoun/core/secrets.py#L1-L212)
- [docs/DEPLOYMENT.md](file://docs/DEPLOYMENT.md#L26-L31)

### Network Security and Reverse Proxy Setup
The platform implements a defense-in-depth approach to network security, with multiple layers of protection:

1. **Port exposure minimization**: Only essential ports are exposed to the public internet:
   - Port 8000: FastAPI/MCP server (exposed via reverse proxy)
   - All other ports (Neo4j, Prometheus, Grafana) are restricted to internal network access

2. **Reverse proxy configuration**: Production deployments should use a reverse proxy (Nginx or Traefik) to:
   - Terminate SSL/TLS connections
   - Implement rate limiting
   - Provide additional security headers
   - Handle load balancing across multiple backend instances

3. **Internal network isolation**: Docker Compose creates an internal bridge network (`mahoun-internal`) for service-to-service communication, preventing direct external access to database and monitoring services.

4. **CORS configuration**: The API server implements strict CORS policies, with configurable allowed origins that should not use wildcards in production.

**Section sources**
- [docs/DEPLOYMENT.md](file://docs/DEPLOYMENT.md#L32-L39)
- [docker-compose.yml](file://docker-compose.yml#L424-L434)

### Resource Scaling Strategies for High-Availability
The platform supports high-availability configurations through horizontal and vertical scaling strategies:

1. **Horizontal scaling**: Multiple backend instances can be deployed behind a load balancer:
   - Configure multiple `backend` services in Docker Compose
   - Use external load balancer (nginx, traefik, or cloud provider LB)
   - Ensure session persistence or use Redis for session storage

2. **Vertical scaling**: Resource limits can be adjusted based on workload:
   ```yaml
   backend:
     deploy:
       resources:
         limits:
           cpus: '2.0'
           memory: 2G
         reservations:
           cpus: '0.5'
           memory: 512M
   ```

3. **Database clustering**: For high-traffic deployments:
   - Neo4j Enterprise Cluster for graph database
   - PostgreSQL streaming replication
   - Redis Sentinel for high availability

4. **Worker configuration**: The number of API workers can be scaled based on CPU cores:
   ```json
   "api": {
     "workers": "${MAHOUN_API_WORKERS:-1}"
   }
   ```

**Section sources**
- [docs/DEPLOYMENT.md](file://docs/DEPLOYMENT.md#L40-L45)
- [docs/DOCKER.md](file://docs/DOCKER.md#L378-L386)
- [docker-compose.yml](file://docker-compose.yml#L79-L87)

## Disaster Recovery Procedures
The Mahoun platform includes comprehensive disaster recovery procedures to ensure data integrity and minimize downtime in case of system failures.

### Backup Scripts for Databases and Application Data
The platform provides automated backup scripts that can be scheduled for regular execution. The backup strategy covers all critical data components:

1. **Database backups**:
   - Neo4j: Using `neo4j-admin database dump` command
   - PostgreSQL: Using `pg_dump` for logical backups
   - Redis: RDB snapshots and AOF files

2. **Application data backups**:
   - User uploads (`./uploads`)
   - Vector store data (`./vector_store_data`)
   - Generated outputs (`./output`)
   - Configuration and runtime data

The backup script `scripts/docker/backup.sh` implements a comprehensive backup procedure:

```bash
# Neo4j
docker compose exec neo4j neo4j-admin database dump neo4j --to-stdout \
  > "${BACKUP_DIR}/neo4j.dump"

# Postgres
docker compose exec postgres pg_dump -U mahoun mahoun \
  > "${BACKUP_DIR}/postgres.sql"

# Application data
tar czf "${BACKUP_DIR}/app_data.tar.gz" data/ uploads/ vector_store_data/
```

Backups should be stored in secure, off-site locations with appropriate retention policies (e.g., daily backups for 30 days, weekly backups for 12 weeks).

**Section sources**
- [docs/DOCKER.md](file://docs/DOCKER.md#L339-L362)
- [scripts/docker/backup.sh](file://scripts/docker/backup.sh)

### Restore Processes
The platform provides clear procedures for restoring from backups in case of data loss or system failure:

1. **Database restoration**:
   ```bash
   # Neo4j
   cat backups/20241229/neo4j.dump | \
     docker compose exec -T neo4j neo4j-admin database load neo4j --from-stdin
   
   # Postgres
   cat backups/20241229/postgres.sql | \
     docker compose exec -T postgres psql -U mahoun mahoun
   ```

2. **Application data restoration**:
   ```bash
   tar xzf backups/20241229/app_data.tar.gz
   ```

3. **Full system recovery**:
   - Stop all services
   - Restore databases and application data
   - Start services in the correct order (databases first, then application)
   - Validate system health and data integrity

The restore process should be tested regularly in a staging environment to ensure reliability.

**Section sources**
- [docs/DOCKER.md](file://docs/DOCKER.md#L364-L376)

## Production-Specific Concerns
The platform addresses several production-specific concerns to ensure reliability, performance, and maintainability in production environments.

### Log Rotation and Management
The platform implements comprehensive log management practices:

1. **Docker log rotation**: Configured in Docker daemon settings:
   ```json
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "10m",
       "max-file": "3"
     }
   }
   ```

2. **Application logging**: Configured through environment variables:
   - `LOG_LEVEL`: Controls verbosity (INFO, DEBUG, WARNING, ERROR)
   - `LOG_FORMAT`: Supports JSON, text, or structured formats

3. **Centralized logging**: Production deployments should forward logs to centralized logging systems (ELK stack, Splunk, or cloud provider logging services).

**Section sources**
- [docs/DEPLOYMENT.md](file://docs/DEPLOYMENT.md#L56-L66)
- [docs/DOCKER.md](file://docs/DOCKER.md#L414-L419)

### Persistent Volume Management
The platform uses named Docker volumes for persistent data storage, ensuring data persistence across container restarts:

```yaml
volumes:
  mahoun_neo4j_data:
  mahoun_postgres_data:
  mahoun_redis_data:
  mahoun_chromadb_data:
  mahoun_prometheus_data:
  mahoun_grafana_data:
```

Best practices for volume management include:
- Regular backup of named volumes
- Monitoring volume disk usage
- Using external storage (NFS, cloud storage) for high-availability setups
- Implementing volume cleanup procedures for legacy deployments

The `scripts/docker/clean_legacy_state.sh` script helps identify and remove legacy volumes from previous deployments that may cause conflicts.

**Section sources**
- [docs/DOCKER.md](file://docs/DOCKER.md#L182-L191)
- [docker-compose.yml](file://docker-compose.yml#L393-L423)
- [scripts/docker/clean_legacy_state.sh](file://scripts/docker/clean_legacy_state.sh)

### High-Availability Configurations for Databases
The platform supports high-availability database configurations for mission-critical deployments:

1. **Neo4j Causal Clustering**: For enterprise-grade graph database availability
2. **PostgreSQL Streaming Replication**: For relational data redundancy
3. **Redis Sentinel**: For cache and session store high availability
4. **ChromaDB Cluster**: For distributed vector storage

These configurations require additional infrastructure and should be implemented based on availability requirements and budget constraints.

**Section sources**
- [docs/DOCKER.md](file://docs/DOCKER.md#L378-L386)

## Validation Steps
The platform includes comprehensive validation steps to ensure deployment integrity and security compliance.

### Automated Validation with Scripts
The `scripts/docker/validate_docker_setup.sh` script performs comprehensive validation of the Docker environment:

1. **Prerequisites check**: Verifies Docker and Docker Compose installation
2. **File structure validation**: Ensures required files are present
3. **Dockerfile validation**: Checks for security best practices
4. **Compose file validation**: Validates health checks, profiles, and networks
5. **Security checks**: Detects hardcoded passwords and missing protections

The validation script outputs a detailed report and exits with a non-zero status if critical issues are found.

### Health Checks and Monitoring
The platform implements comprehensive health checks at multiple levels:

1. **Container health checks**: Built into Docker images
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
       CMD curl -f http://localhost:8000/system/health || exit 1
   ```

2. **Service health checks**: Configured in docker-compose.yml
   - Backend: `curl -f http://localhost:8000/system/health`
   - Frontend: `curl -f http://localhost/`
   - Neo4j: `cypher-shell RETURN 1`
   - Postgres: `pg_isready`

3. **Monitoring stack**: Includes Prometheus for metrics collection and Grafana for visualization, providing real-time insights into system performance and health.

**Section sources**
- [scripts/docker/validate_docker_setup.sh](file://scripts/docker/validate_docker_setup.sh)
- [Dockerfile.backend](file://Dockerfile.backend#L87-L89)
- [docker-compose.yml](file://docker-compose.yml#L71-L77)

## Conclusion
The Mahoun platform is designed with production readiness as a core principle, implementing comprehensive security, scalability, and reliability features. By following the guidelines outlined in this document, organizations can deploy the platform with confidence in its ability to handle production workloads securely and efficiently.

Key takeaways for production deployment include:
- Implement strict secrets management using external secret managers
- Minimize exposed attack surface through careful port management
- Implement comprehensive backup and disaster recovery procedures
- Scale resources appropriately based on workload requirements
- Validate deployments using automated scripts and monitoring

The platform's modular architecture and comprehensive documentation make it well-suited for enterprise deployments requiring high availability and strong security guarantees.