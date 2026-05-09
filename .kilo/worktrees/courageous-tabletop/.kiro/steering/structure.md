# Project Structure

```
mahoun-platform/
├── mahoun/                 # Core platform package
│   ├── agents/             # AI agent implementations
│   ├── core/               # Core utilities, settings, health checks
│   ├── domain/             # Domain-specific engines (legal, healthcare, etc.)
│   ├── graph/              # Ultra Graph Builder, knowledge graph
│   ├── guardrails/         # Safety guardrails and constraints
│   ├── invariants/         # System invariants enforcement
│   ├── ledger/             # Immutable evidence ledger
│   ├── mcp/                # Model Context Protocol layer
│   ├── metrics/            # Prometheus metrics collection
│   ├── orchestrator/       # Workflow orchestration
│   ├── pipelines/          # Data processing pipelines
│   ├── rag/                # Retrieval-Augmented Generation
│   ├── reasoning/          # Evidence-Linked Verdict Engine
│   ├── retrieval/          # Hybrid search (dense + sparse + graph)
│   ├── schemas/            # Pydantic models and schemas
│   ├── tracing/            # Distributed tracing
│   └── uncertainty/        # Uncertainty quantification
│
├── api/                    # FastAPI REST API
│   ├── routers/            # API route handlers
│   ├── auth/               # Authentication dependencies
│   ├── main.py             # Application entry point
│   └── database.py         # Database connections
│
├── frontend/               # React/TypeScript frontend
│   └── src/                # Frontend source code
│
├── tests/                  # Test suite
│   ├── test_*.py           # Test modules
│   └── conftest.py         # Pytest fixtures
│
├── ci/                     # CI/CD scripts and gates
│   ├── first_step/         # Mandatory CI gates (0-7)
│   └── gates/              # Additional quality gates
│
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── monitoring/             # Grafana/Prometheus configs
├── config/                 # Runtime configuration
└── proof_pack/             # Verification artifacts
```

## Key Entry Points

- `api/main.py`: FastAPI application
- `mahoun/reasoning/evidence_linked_verdict.py`: Core verdict engine
- `mahoun/graph/ultra_graph_builder.py`: Knowledge graph builder
- `mahoun/mcp/`: MCP server for LLM integration

## Configuration Files

- `pyproject.toml`: Package metadata and dependencies
- `requirements.txt`: Pinned dependencies
- `mypy.ini`: Type checking configuration
- `pytest.ini`: Test configuration
- `.env`: Environment variables (copy from `.env.example`)
- `docker-compose.yml`: Container orchestration
