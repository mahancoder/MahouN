# Tech Stack

## Language & Runtime

- Python 3.12+
- FastAPI for REST API
- Uvicorn ASGI server

## Core Dependencies

- **pydantic** (>=2.6): Data validation and settings
- **numpy**: Numerical operations
- **neo4j** (optional): Graph database for knowledge graph
- **chromadb**: Vector store for RAG
- **sentence-transformers**: Embeddings for semantic search
- **torch**: ML/deep learning (CPU version in requirements)

## Build System

- **setuptools** with pyproject.toml
- **pip** for dependency management
- **Docker Compose** for containerized deployment

## Code Quality

- **ruff**: Linting and formatting
- **mypy**: Static type checking
- **pytest**: Testing framework
- **pre-commit**: Git hooks

## Common Commands

```bash
# Install dependencies
make install

# Run linting
make lint

# Auto-fix lint issues
make lint-fix

# Type checking
make typecheck

# Run tests (fast, unit only)
make test-fast

# Run full CI gates
make ci-first-step

# Start Docker stack
make docker-up

# Stop Docker stack
make docker-down

# Run Docker smoke tests
make docker-test
```

## Testing

```bash
# Default safe run (unit tests, 90s timeout)
pytest tests/ -v

# With coverage
pytest tests/ --cov=mahoun --cov-report=html

# Integration tests (requires external services)
MAHOUN_INTEGRATION=1 pytest tests/ -v -m "integration"

# Slow tests
MAHOUN_SLOW=1 pytest tests/ -v -m "slow"
```

## Environment Variables

- `MCP_API_KEY`: API authentication key
- `NEO4J_URI`: Neo4j connection string (optional)
- `NEO4J_PASSWORD`: Neo4j password
- `MAHOUN_GUARD_MODE`: Runtime mode (OFF, WARN, STRICT, AUDIT)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
