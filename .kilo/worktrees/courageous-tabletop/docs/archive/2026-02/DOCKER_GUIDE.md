# MAHOUN Platform - Docker Deployment Guide

## 🚀 Quick Start

### Development (Laptop-Safe)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and set your passwords
nano .env

# 3. Start development environment
make dev

# Or with databases
make dev-full
```

Access:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

### Production

```bash
# 1. Generate secure secrets
make generate-secrets

# 2. Add secrets to .env
nano .env

# 3. Start production (minimal)
make prod

# Or with all services
make prod-full
```

Access:
- Backend: http://localhost:8000
- Frontend: http://localhost:80
- Neo4j Browser: http://localhost:7474
- Grafana: http://localhost:3000

---

## 📦 Docker Images

### Backend Image Stages

1. **base**: Common dependencies
2. **builder**: Compile Python packages
3. **development**: With dev tools + hot-reload
4. **production**: Minimal, hardened, non-root
5. **testing**: With test dependencies

### Build Specific Stage

```bash
# Development
docker build -t mahoun/backend:dev \
  -f Dockerfile.backend \
  --target development .

# Production
docker build -t mahoun/backend:prod \
  -f Dockerfile.backend \
  --target production .

# Testing
docker build -t mahoun/backend:test \
  -f Dockerfile.backend \
  --target testing .
```

---

## 🔧 Configuration

### Environment Variables

Required (must set in `.env`):
```bash
SECURITY_JWT_SECRET=<generate-with-openssl>
API_KEY=<generate-with-openssl>
DB_NEO4J_PASSWORD=<generate-with-openssl>
DB_POSTGRES_PASSWORD=<generate-with-openssl>
REDIS_PASSWORD=<generate-with-openssl>
```

Generate with:
```bash
openssl rand -base64 32
```

Or use:
```bash
make generate-secrets
```

### Resource Limits

#### Development (Laptop-Safe)
```yaml
backend:
  cpus: '2.0'
  memory: 4G

neo4j:
  cpus: '1.0'
  memory: 2G
```

#### Production (Server)
```yaml
backend:
  cpus: '4.0'
  memory: 8G

neo4j:
  cpus: '4.0'
  memory: 8G
```

---

## 🎯 Deployment Profiles

### Minimal (Backend + Frontend Only)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Services:
- ✅ Backend
- ✅ Frontend
- ❌ Neo4j
- ❌ PostgreSQL
- ❌ Redis

### Full (All Databases)

```bash
docker-compose -f docker-compose.prod.yml --profile full up -d
```

Services:
- ✅ Backend
- ✅ Frontend
- ✅ Neo4j
- ✅ PostgreSQL
- ✅ Redis
- ✅ ChromaDB

### With Monitoring

```bash
docker-compose -f docker-compose.prod.yml --profile full --profile monitoring up -d
```

Services:
- ✅ All above
- ✅ Prometheus
- ✅ Grafana

---

## 🔍 Monitoring & Debugging

### View Logs

```bash
# All services
make logs

# Specific service
make logs-backend
make logs-neo4j

# Follow logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Check Health

```bash
# All services
make health

# Specific service
curl http://localhost:8000/system/health
```

### Resource Usage

```bash
make stats
```

### Shell Access

```bash
# Backend container
make shell-backend

# Neo4j cypher-shell
make shell-neo4j

# PostgreSQL
docker exec -it mahoun-postgres-prod psql -U mahoun -d mahoun
```

---

## 🗄️ Data Management

### Volumes

Production volumes:
```
mahoun_backend_data_prod
mahoun_neo4j_data_prod
mahoun_postgres_data_prod
mahoun_redis_data_prod
mahoun_chromadb_data_prod
```

### Backup

```bash
# Automated backup
make db-backup

# Manual PostgreSQL backup
docker exec mahoun-postgres-prod pg_dump -U mahoun mahoun > backup.sql

# Manual Neo4j backup
docker exec mahoun-neo4j-prod neo4j-admin database dump neo4j --to-path=/tmp
docker cp mahoun-neo4j-prod:/tmp/neo4j.dump ./neo4j_backup.dump
```

### Restore

```bash
# PostgreSQL restore
docker exec -i mahoun-postgres-prod psql -U mahoun mahoun < backup.sql

# Neo4j restore
docker cp ./neo4j_backup.dump mahoun-neo4j-prod:/tmp/
docker exec mahoun-neo4j-prod neo4j-admin database load neo4j --from-path=/tmp
```

---

## 🔒 Security Best Practices

### 1. Change Default Passwords

```bash
# Generate secure passwords
make generate-secrets

# Add to .env
nano .env
```

### 2. Use Non-Root User

Backend runs as user `mahoun` (UID 1000):
```dockerfile
USER mahoun
```

### 3. Restrict Network Access

Internal networks:
- `mahoun-database`: Internal only
- `mahoun-cache`: Internal only
- `mahoun-backend`: External access
- `mahoun-monitoring`: Internal only

### 4. Enable TLS/SSL

For production, use reverse proxy (Nginx/Traefik) with Let's Encrypt:

```yaml
# docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
```

### 5. Scan for Vulnerabilities

```bash
make scan
```

---

## 🚨 Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker logs mahoun-backend-prod

# Check health
curl http://localhost:8000/system/health

# Restart
docker-compose -f docker-compose.prod.yml restart backend
```

### Database Connection Issues

```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check Neo4j logs
docker logs mahoun-neo4j-prod

# Test connection
docker exec mahoun-backend-prod curl -f bolt://neo4j:7687
```

### Out of Memory

```bash
# Check resource usage
docker stats

# Increase limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 16G  # Increase
```

### Permission Denied

```bash
# Fix ownership
sudo chown -R 1000:1000 ./data ./uploads ./output

# Or run as root (not recommended)
docker-compose -f docker-compose.prod.yml run --user root backend bash
```

---

## 📊 Performance Tuning

### Neo4j

```yaml
environment:
  NEO4J_dbms_memory_heap_max__size: 4G  # Increase for large graphs
  NEO4J_dbms_memory_pagecache_size: 2G  # Increase for better performance
```

### PostgreSQL

```yaml
environment:
  POSTGRES_SHARED_BUFFERS: 512MB  # 25% of RAM
  POSTGRES_EFFECTIVE_CACHE_SIZE: 2GB  # 50-75% of RAM
```

### Redis

```yaml
command: >
  redis-server
  --maxmemory 4gb  # Increase for large cache
  --maxmemory-policy allkeys-lru
```

### Backend Workers

```yaml
environment:
  UNIFIED_LOADER_WORKERS: 8  # Increase for more throughput
```

---

## 🔄 Updates & Maintenance

### Update Images

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart with new images
docker-compose -f docker-compose.prod.yml up -d
```

### Clean Up

```bash
# Remove stopped containers
make clean

# Remove everything (WARNING!)
make clean-all
```

### Prune Volumes

```bash
# Remove unused volumes
docker volume prune -f

# Remove specific volume
docker volume rm mahoun_backend_data_prod
```

---

## 📝 CI/CD Integration

### GitHub Actions

```yaml
name: Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build backend
        run: make ci-build VERSION=${{ github.sha }}
      
      - name: Run tests
        run: make ci-test
      
      - name: Push to registry
        run: make ci-push VERSION=${{ github.sha }}
```

### GitLab CI

```yaml
build:
  stage: build
  script:
    - make ci-build VERSION=$CI_COMMIT_SHA
    - make ci-test
    - make ci-push VERSION=$CI_COMMIT_SHA
```

---

## 🎓 Advanced Usage

### Multi-Stage Build Caching

```bash
# Build with cache
docker build \
  --cache-from mahoun/backend:latest \
  --cache-from mahoun/backend:cache \
  -t mahoun/backend:latest \
  -f Dockerfile.backend \
  --target production .
```

### Custom Network

```bash
# Create custom network
docker network create mahoun-custom

# Use in docker-compose
networks:
  mahoun-custom:
    external: true
```

### Health Check Customization

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/system/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Neo4j Docker Documentation](https://neo4j.com/docs/operations-manual/current/docker/)
- [PostgreSQL Docker Documentation](https://hub.docker.com/_/postgres)

---

## 🆘 Support

For issues or questions:
1. Check logs: `make logs`
2. Check health: `make health`
3. Review this guide
4. Contact: support@mahoun.ai
