# MAHOUN Governance Integration - Developer Guide

**Version**: 2.0.0  
**Last Updated**: 2026-05-21  
**Status**: Production Ready

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Development Environment Setup](#2-development-environment-setup)
3. [Working with Governance Components](#3-working-with-governance-components)
4. [Testing Governance Features](#4-testing-governance-features)
5. [Common Development Patterns](#5-common-development-patterns)
6. [Debugging and Troubleshooting](#6-debugging-and-troubleshooting)
7. [Best Practices](#7-best-practices)
8. [CI/CD Integration](#8-cicd-integration)

---

## 1. Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (for full stack)
- Neo4j (optional, for graph operations)
- Basic understanding of async/await patterns
- Familiarity with Pydantic models

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd mahoun-platform

# Install dependencies
make install

# Run linting
make lint

# Run type checking
make typecheck

# Run tests (fast, unit only)
make test-fast

# Run full CI gates
make ci-first-step
```

---

## 2. Development Environment Setup

### 2.1 Local Development Mode

For local development, you can use `DESKTOP_MINIMAL` mode which reduces resource requirements:

```bash
# Set environment variables
export MAHOUN_ENV=development
export MAHOUN_EXECUTION_MODE=DESKTOP_MINIMAL
export MAHOUN_GUARD_MODE=AUDIT  # Log violations but don't block

# Run the application
uvicorn api.main:app --reload
```

### 2.2 Governance Lock Initialization

**CRITICAL**: GovernanceLock must be initialized at application startup:

```python
# In api/main.py or your application entry point
from mahoun.core.governance_lock import GovernanceLock, GovernanceMode

@app.on_event("startup")
async def startup_event():
    # Initialize governance lock (ONCE)
    if not GovernanceLock._initialized:
        mode = GovernanceMode.STRICT if os.getenv("MAHOUN_ENV") == "production" else GovernanceMode.AUDIT
        GovernanceLock.initialize(mode=mode)
    
    # Verify governance is enabled
    if not GovernanceLock.is_enforcement_enabled():
        raise RuntimeError("Governance enforcement disabled!")
```

### 2.3 Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| `MAHOUN_ENV` | `development`, `staging`, `production` | Environment mode |
| `MAHOUN_EXECUTION_MODE` | `DESKTOP_MINIMAL`, `ENTERPRISE_FULL` | Execution mode |
| `MAHOUN_GUARD_MODE` | `OFF`, `WARN`, `STRICT`, `AUDIT` | Runtime guard mode |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Logging level |
| `NEO4J_URI` | URI string | Neo4j connection (optional) |
| `NEO4J_PASSWORD` | Password | Neo4j password |

---

## 3. Working with Governance Components

### 3.1 Using GovernanceContext

**CRITICAL**: All reasoning operations MUST run within a governance context.

```python
from mahoun.core.governance import GovernanceContextManager

# Basic usage - async context manager
async def my_reasoning_operation():
    async with GovernanceContextManager.active_context(
        correlation_id="req-123",
        execution_mode="STRICT"
    ) as ctx:
        # All operations in this scope are governed
        # Provenance is automatically tracked
        result = await reasoning_service.reason(request)
        return result

# Nested contexts (child contexts inherit parent lineage)
async def parent_operation():
    async with GovernanceContextManager.active_context(
        correlation_id="parent-123"
    ) as parent_ctx:
        # Parent operation
        result1 = await some_operation()
        
        # Create child context
        child_ctx = parent_ctx.create_child_context(
            child_correlation_id="child-456"
        )
        
        # Child operation inherits parent lineage
        result2 = await another_operation(child_ctx)
        
        return result1, result2

# Require active context (fail-closed)
def operation_requiring_context():
    ctx = GovernanceContextManager.require_context()
    # Raises GovernanceViolationError if no context
    return ctx.correlation_id
```

### 3.2 Creating Provenance Metadata

```python
from mahoun.core.governance import GovernanceContextManager

# Automatically creates provenance with full governance attestation
provenance = GovernanceContextManager.require_provenance(
    source="document_ingestion",
    author="ingestion_pipeline"
)

# Provenance includes:
# - correlation_id: From active governance context
# - governance_scope_id: ID of governance scope
# - runtime_attestation_id: Cryptographic attestation
# - provenance_hash: SHA-256 hash for integrity
# - provenance_signature: Cryptographic signature
# - timestamp: Governance-controlled timestamp
# - lineage_parent: Parent provenance ID (if nested)
```

### 3.3 Using FortressValidator

```python
from mahoun.core.fortress_validator import FortressValidator

# Create validator
validator = FortressValidator(strict_mode=True)

# Validate a reasoning response
validation_result = await validator.validate(
    response=reasoning_response,
    correlation_id="req-123"
)

# Check result
if validation_result.passed:
    print(f"✅ Validation passed: {validation_result.forensic_hash}")
    print(f"⏱️  Execution time: {validation_result.execution_time_ms}ms")
else:
    print(f"❌ Validation failed!")
    for violation in validation_result.violations:
        print(f"  - {violation['type']}: {violation['message']}")
    
    # In strict mode, this raises SecurityBreachException
    # In audit mode, this logs but continues

# Get statistics
stats = validator.get_stats()
print(f"Total validations: {stats['total_validations']}")
print(f"Pass rate: {stats['passed'] / stats['total_validations'] * 100:.2f}%")
```

### 3.4 Using FortressProtectedReasoningService

```python
from mahoun.reasoning.fortress_integration import create_fortress_protected_service

# Wrap your reasoning service with Fortress protection
protected_service = create_fortress_protected_service(
    reasoning_service=unified_reasoning_service,
    strict_mode=True
)

# Execute reasoning (auto-validated)
async def generate_verdict(request):
    async with GovernanceContextManager.active_context(
        correlation_id=request.case_id
    ) as ctx:
        # Reasoning is automatically validated
        response = await protected_service.reason(
            request=request,
            correlation_id=ctx.correlation_id
        )
        
        # Response includes proof-carrying metadata
        assert response.fortress_validated == True
        assert len(response.audit_hash) >= 16
        assert response.correlation_id == ctx.correlation_id
        
        return response

# Batch processing
async def batch_reasoning(requests):
    responses = await protected_service.reason_batch(
        requests=requests,
        correlation_id_prefix="batch-123"
    )
    return responses

# Health check
health = await protected_service.health_check()
print(f"Service status: {health['status']}")
```

### 3.5 Creating ProofCarryingResponse Models

```python
from mahoun.api.models.proof_carrying import ProofCarryingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List

class MyCustomResponse(ProofCarryingResponse):
    """Custom API response with proof-carrying contract."""
    
    # Your custom fields
    result: str = Field(..., description="Operation result")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # ProofCarryingResponse fields are inherited:
    # - fortress_validated: bool
    # - audit_hash: str
    # - validation_timestamp: str
    # - correlation_id: str

# Usage in API endpoint
@router.post("/my-endpoint")
async def my_endpoint(request: MyRequest) -> MyCustomResponse:
    async with GovernanceContextManager.active_context(
        correlation_id=str(uuid.uuid4())
    ) as ctx:
        # Your logic here
        result = await process_request(request)
        
        # Create response with proof-carrying metadata
        return MyCustomResponse(
            result=result.value,
            confidence=result.confidence,
            metadata=result.metadata,
            fortress_validated=True,
            audit_hash=generate_audit_hash(result),
            validation_timestamp=datetime.now(timezone.utc).isoformat(),
            correlation_id=ctx.correlation_id
        )
```

---

## 4. Testing Governance Features

### 4.1 Unit Testing with GovernanceLock

```python
import pytest
from mahoun.core.governance_lock import GovernanceLock, GovernanceMode

@pytest.fixture(autouse=True)
def reset_governance_lock():
    """Reset GovernanceLock before each test."""
    GovernanceLock._initialized = False
    GovernanceLock._mode = None
    GovernanceLock._initialization_timestamp = None
    yield
    # Cleanup after test
    GovernanceLock._initialized = False

def test_governance_lock_initialization():
    """Test GovernanceLock initialization."""
    # Initialize in STRICT mode
    lock = GovernanceLock.initialize(mode=GovernanceMode.STRICT)
    
    assert GovernanceLock.is_enforcement_enabled()
    assert GovernanceLock.get_mode() == GovernanceMode.STRICT
    assert GovernanceLock.verify_integrity()
    assert GovernanceLock.verify_immutable()

def test_governance_lock_immutability():
    """Test that mode cannot be changed after initialization."""
    GovernanceLock.initialize(mode=GovernanceMode.STRICT)
    
    # Attempt to re-initialize should fail
    with pytest.raises(RuntimeError, match="already initialized"):
        GovernanceLock.initialize(mode=GovernanceMode.AUDIT)
    
    # Mode should remain STRICT
    assert GovernanceLock.get_mode() == GovernanceMode.STRICT
```

### 4.2 Testing with GovernanceContext

```python
import pytest
from mahoun.core.governance import GovernanceContextManager, GovernanceViolationError

@pytest.mark.asyncio
async def test_governance_context_required():
    """Test that operations require active governance context."""
    
    # Without context, should raise error
    with pytest.raises(GovernanceViolationError):
        GovernanceContextManager.require_context()
    
    # With context, should succeed
    async with GovernanceContextManager.active_context(
        correlation_id="test-123"
    ) as ctx:
        active_ctx = GovernanceContextManager.require_context()
        assert active_ctx.correlation_id == "test-123"

@pytest.mark.asyncio
async def test_governance_context_lineage():
    """Test correlation lineage tracking."""
    
    async with GovernanceContextManager.active_context(
        correlation_id="parent-123"
    ) as parent_ctx:
        # Create child context
        child_ctx = parent_ctx.create_child_context(
            child_correlation_id="child-456"
        )
        
        # Child should have parent in lineage
        assert "parent-123" in child_ctx.correlation_lineage
        assert child_ctx.correlation_id == "child-456"
```

### 4.3 Testing FortressValidator

```python
import pytest
from mahoun.core.fortress_validator import FortressValidator
from mahoun.reasoning.models import ReasoningResponse

@pytest.mark.asyncio
async def test_fortress_validator_success():
    """Test successful validation."""
    validator = FortressValidator(strict_mode=True)
    
    # Create valid response
    response = ReasoningResponse(
        verdict="Contract is valid",
        confidence=0.95,
        proof_tree={"root": "valid_proof"},
        agreement_score=0.90,
        derived_facts=["fact1", "fact2"],
        audit_trail=["step1", "step2"]
    )
    
    # Validate
    result = await validator.validate(response, correlation_id="test-123")
    
    assert result.passed
    assert result.correlation_id == "test-123"
    assert len(result.violations) == 0
    assert len(result.forensic_hash) >= 16

@pytest.mark.asyncio
async def test_fortress_validator_failure():
    """Test validation failure."""
    validator = FortressValidator(strict_mode=False)  # Non-strict for testing
    
    # Create invalid response (missing proof_tree)
    response = ReasoningResponse(
        verdict="Contract is valid",
        confidence=0.95,
        proof_tree=None,  # Missing!
        agreement_score=0.90,
        derived_facts=["fact1"],
        audit_trail=["step1"]
    )
    
    # Validate
    result = await validator.validate(response, correlation_id="test-123")
    
    assert not result.passed
    assert len(result.violations) > 0
    assert any(v["type"] == "PROOF_TREE_MISSING" for v in result.violations)
```

### 4.4 Integration Testing

```python
import pytest
from httpx import AsyncClient
from api.main import app

@pytest.mark.asyncio
async def test_api_endpoint_with_governance():
    """Test API endpoint with full governance integration."""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Make request
        response = await client.post(
            "/api/v1/reasoning/generate-verdict",
            json={
                "question": "Is the contract valid?",
                "facts": [
                    {"value": "Contract signed on 2026-01-01"},
                    {"value": "Both parties are adults"}
                ],
                "case_id": "test-case-123"
            },
            headers={"X-API-Key": "test-key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify proof-carrying contract
        assert data["fortress_validated"] == True
        assert len(data["audit_hash"]) >= 16
        assert "validation_timestamp" in data
        assert data["correlation_id"] == "test-case-123"
        
        # Verify verdict data
        assert data["success"] == True
        assert "verdict_id" in data
        assert "final_verdict" in data
```

---

## 5. Common Development Patterns

### 5.1 Pattern: Governed API Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException
from mahoun.core.governance import GovernanceContextManager
from mahoun.reasoning.fortress_integration import create_fortress_protected_service
from mahoun.api.models.proof_carrying import ProofCarryingResponse
import uuid

router = APIRouter()

@router.post("/my-reasoning-endpoint")
async def my_reasoning_endpoint(
    request: MyRequest,
    reasoning_service = Depends(get_reasoning_service)
) -> MyResponse:
    """
    Governed reasoning endpoint with full Fortress protection.
    """
    
    # Step 1: Create governance context
    correlation_id = request.correlation_id or str(uuid.uuid4())
    
    async with GovernanceContextManager.active_context(
        correlation_id=correlation_id,
        execution_mode="STRICT"
    ) as ctx:
        try:
            # Step 2: Wrap service with Fortress protection
            protected_service = create_fortress_protected_service(
                reasoning_service=reasoning_service,
                strict_mode=True
            )
            
            # Step 3: Execute reasoning (auto-validated)
            result = await protected_service.reason(
                request=request,
                correlation_id=ctx.correlation_id
            )
            
            # Step 4: Return response with proof-carrying metadata
            return MyResponse(
                success=True,
                result=result.verdict,
                confidence=result.confidence,
                fortress_validated=True,
                audit_hash=result.audit_hash,
                validation_timestamp=result.validation_timestamp,
                correlation_id=ctx.correlation_id
            )
            
        except SecurityBreachException as e:
            # Fortress validation failed
            raise HTTPException(
                status_code=503,
                detail=f"Validation failed: {e.message}"
            )
        except Exception as e:
            # Other errors
            raise HTTPException(
                status_code=500,
                detail=f"Internal error: {str(e)}"
            )
```

### 5.2 Pattern: Graph Mutation with Provenance

```python
from mahoun.core.governance import GovernanceContextManager

async def add_node_to_graph(node_data: dict):
    """
    Add node to graph with full provenance tracking.
    """
    
    # Require active governance context
    ctx = GovernanceContextManager.require_context()
    
    # Create provenance metadata
    provenance = GovernanceContextManager.require_provenance(
        source="graph_mutation",
        author="system"
    )
    
    # Add provenance to node data
    node_data["provenance"] = {
        "source": provenance.source,
        "timestamp": provenance.timestamp,
        "correlation_id": provenance.correlation_id,
        "governance_scope_id": provenance.governance_scope_id,
        "runtime_attestation_id": provenance.runtime_attestation_id,
        "provenance_hash": provenance.provenance_hash,
        "provenance_signature": provenance.provenance_signature
    }
    
    # Perform graph mutation
    await graph_service.add_node(node_data)
    
    return node_data
```

### 5.3 Pattern: Batch Processing with Governance

```python
async def batch_process_documents(documents: List[Document]):
    """
    Process multiple documents with governance context.
    """
    
    results = []
    
    # Create parent governance context
    async with GovernanceContextManager.active_context(
        correlation_id=f"batch-{uuid.uuid4()}"
    ) as parent_ctx:
        
        for i, doc in enumerate(documents):
            # Create child context for each document
            child_ctx = parent_ctx.create_child_context(
                child_correlation_id=f"{parent_ctx.correlation_id}-doc-{i}"
            )
            
            # Process document with child context
            result = await process_document(doc, child_ctx)
            results.append(result)
        
        return results
```

---

## 6. Debugging and Troubleshooting

### 6.1 Common Issues

#### Issue: "GovernanceLock not initialized"

**Cause**: GovernanceLock.initialize() not called at startup.

**Solution**:
```python
# In api/main.py
@app.on_event("startup")
async def startup_event():
    GovernanceLock.initialize(mode=GovernanceMode.STRICT)
```

#### Issue: "GovernanceViolationError: No active governance context"

**Cause**: Reasoning operation attempted without active context.

**Solution**:
```python
# Wrap operation in governance context
async with GovernanceContextManager.active_context() as ctx:
    result = await reasoning_service.reason(request)
```

#### Issue: "SecurityBreachException: Validation failed"

**Cause**: Response failed Fortress validation.

**Solution**:
```python
# Check validation result
validation_result = await validator.validate(response)
if not validation_result.passed:
    for violation in validation_result.violations:
        print(f"Violation: {violation['type']} - {violation['message']}")
```

### 6.2 Debugging Tools

#### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("mahoun.core.governance").setLevel(logging.DEBUG)
logging.getLogger("mahoun.core.fortress_validator").setLevel(logging.DEBUG)
```

#### Inspect Governance Context

```python
ctx = GovernanceContextManager.get_current_context()
if ctx:
    print(f"Context ID: {ctx.context_id}")
    print(f"Correlation ID: {ctx.correlation_id}")
    print(f"Execution mode: {ctx.execution_mode}")
    print(f"Lineage: {ctx.correlation_lineage}")
    print(f"Attestation: {ctx.get_attestation()}")
```

#### Check GovernanceLock Status

```python
metadata = GovernanceLock.get_audit_metadata()
print(f"Initialized: {metadata['initialized']}")
print(f"Mode: {metadata['mode']}")
print(f"Integrity: {metadata['integrity_verified']}")
print(f"Bypass attempts: {metadata['change_attempts']}")
```

---

## 7. Best Practices

### 7.1 Governance Context Management

✅ **DO**:
- Always use `async with GovernanceContextManager.active_context()` for reasoning operations
- Create child contexts for nested operations
- Use meaningful correlation IDs (e.g., case IDs, request IDs)
- Check for active context with `require_context()` in critical paths

❌ **DON'T**:
- Don't perform reasoning without governance context
- Don't reuse correlation IDs across unrelated operations
- Don't bypass governance context for "quick tests"

### 7.2 Provenance Tracking

✅ **DO**:
- Always create provenance for graph mutations
- Use `GovernanceContextManager.require_provenance()` for automatic attestation
- Include meaningful source and author information
- Track lineage for nested operations

❌ **DON'T**:
- Don't create provenance manually (use factory methods)
- Don't modify provenance after creation (immutable)
- Don't skip provenance for "temporary" data

### 7.3 Fortress Validation

✅ **DO**:
- Use `strict_mode=True` in production
- Handle `SecurityBreachException` appropriately
- Log validation failures with full context
- Monitor validation metrics

❌ **DON'T**:
- Don't disable Fortress validation in production
- Don't lower thresholds to pass validation
- Don't catch and ignore `SecurityBreachException`

### 7.4 Testing

✅ **DO**:
- Reset GovernanceLock in test fixtures
- Test both success and failure paths
- Test governance bypass prevention
- Use integration tests for full governance flow

❌ **DON'T**:
- Don't skip governance tests
- Don't mock governance components in integration tests
- Don't disable governance for "faster" tests

---

## 8. CI/CD Integration

### 8.1 Required CI Gates

All governance-related code must pass these gates:

1. **Forbidden Pattern Scan**: No direct env access, no silent exceptions
2. **Architecture Compliance**: Layer boundary integrity
3. **Type Checking**: Strict mypy on governance modules
4. **Governance Kernel Tests**: Unit tests for governance components
5. **Determinism Tests**: 3x repeat to catch non-deterministic behavior
6. **Governance Coverage**: 100% coverage on governance paths
7. **Fortress Validator Tests**: Integration tests
8. **Governance Integration Tests**: Full governance test suite
9. **Governance Lock Immutability**: Tampering prevention tests

### 8.2 Running CI Locally

```bash
# Run all CI gates
make ci-first-step

# Run specific gates
pytest tests/governance/ -v
mypy mahoun/core/governance/ --strict
ruff check mahoun/core/governance/
```

### 8.3 Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## 9. Additional Resources

- **API Reference**: `/docs/API_REFERENCE.md`
- **Governance Overview**: `/docs/GOVERNANCE_OVERVIEW.md`
- **Deployment Guide**: `/docs/DEPLOYMENT.md`
- **Architecture**: `/docs/ARCHITECTURE.md`
- **CI Architecture**: `/docs/CI_ARCHITECTURE.md`

---

## 10. Support

For questions or issues:
1. Check this developer guide
2. Review test examples in `tests/governance/`
3. Check CI/CD logs for detailed error messages
4. Review Prometheus metrics for runtime issues

---

**Last Updated**: 2026-05-21  
**Version**: 2.0.0
