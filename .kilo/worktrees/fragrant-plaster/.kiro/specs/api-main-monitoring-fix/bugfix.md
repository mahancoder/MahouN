# Bugfix Requirements Document: API Main Monitoring Endpoints Corruption

## Introduction

The `api/main.py` file has suffered severe corruption during an interrupted edit operation, resulting in malformed monitoring endpoints. The file contains 134+ parse errors, making it non-functional. This bugfix restores the monitoring endpoints to their correct, working state while preserving all other functionality.

## Bug Analysis

### Current Behavior (Defect)

**1.1** WHEN the Python parser attempts to parse `api/main.py` THEN the system encounters 134+ parse errors including "Simple statements must be separated by newlines or semicolons"

**1.2** WHEN the `/metrics/legal` endpoint is examined THEN the docstring is truncated (ends with ````jso` instead of complete JSON example) AND the function body is missing

**1.3** WHEN the `/health/detailed` endpoint is examined THEN the function implementation is incomplete with fragmented code

**1.4** WHEN the `/metrics/reset` endpoint is examined THEN the function implementation is incomplete with fragmented code

**1.5** WHEN the `startup_event()` function is examined THEN the logging statements are fragmented and incomplete

**1.6** WHEN attempting to import `api.main` THEN the import fails due to syntax errors

**1.7** WHEN attempting to start the FastAPI server THEN the server fails to start due to parse errors

**1.8** WHEN examining lines 180-350 THEN multiple function bodies contain fragmented strings and incomplete statements

### Expected Behavior (Correct)

**2.1** WHEN the Python parser attempts to parse `api/main.py` THEN the system SHALL parse successfully with zero syntax errors

**2.2** WHEN the `/metrics/legal` endpoint is called THEN the system SHALL return `legal_monitoring.get_comprehensive_stats()` with complete docstring

**2.3** WHEN the `/health/detailed` endpoint is called THEN the system SHALL return comprehensive health status including uptime, component health, and SLA compliance

**2.4** WHEN the `/metrics/reset` endpoint is called in development THEN the system SHALL reset all monitoring metrics and return confirmation

**2.5** WHEN the `/metrics/reset` endpoint is called in production THEN the system SHALL return HTTP 403 with error message "Reset not allowed in production"

**2.6** WHEN the `startup_event()` function executes THEN the system SHALL log complete initialization messages for all monitoring endpoints

**2.7** WHEN attempting to import `api.main` THEN the import SHALL succeed without errors

**2.8** WHEN attempting to start the FastAPI server THEN the server SHALL start successfully and expose all monitoring endpoints

### Unchanged Behavior (Regression Prevention)

**3.1** WHEN any non-monitoring endpoint is called THEN the system SHALL CONTINUE TO function exactly as before

**3.2** WHEN the `/metrics/prometheus` endpoint is called THEN the system SHALL CONTINUE TO return Prometheus-formatted metrics

**3.3** WHEN the `/health` endpoint is called THEN the system SHALL CONTINUE TO return basic health status

**3.4** WHEN security middleware is applied THEN the system SHALL CONTINUE TO enforce CORS and trusted host policies

**3.5** WHEN the feedback pipeline is used THEN the system SHALL CONTINUE TO process feedback correctly

**3.6** WHEN any policy or experiment endpoint is called THEN the system SHALL CONTINUE TO function correctly

**3.7** WHEN the database initialization occurs THEN the system SHALL CONTINUE TO handle connection errors gracefully

## Bug Condition

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type FileContent
  OUTPUT: boolean
  
  // Returns true when the file is corrupted
  RETURN (
    X.path = "api/main.py" AND
    (X.contains_parse_errors() OR
     X.has_truncated_docstrings() OR
     X.has_fragmented_code() OR
     X.has_incomplete_functions())
  )
END FUNCTION
```

### Property Specification

```pascal
// Property: Fix Checking - File Parsing
FOR ALL X WHERE isBugCondition(X) DO
  result ← fix_monitoring_endpoints(X)
  ASSERT result.parse_errors = 0
  ASSERT result.has_complete_docstrings()
  ASSERT result.has_complete_functions()
  ASSERT result.can_import()
END FOR

// Property: Endpoint Functionality
FOR ALL endpoint IN ["/metrics/legal", "/health/detailed", "/metrics/reset"] DO
  ASSERT endpoint.has_complete_docstring()
  ASSERT endpoint.has_complete_implementation()
  ASSERT endpoint.returns_correct_type()
END FOR

// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

Where:
- **F**: The original (corrupted) file
- **F'**: The fixed file
- **isBugCondition(X)**: Returns true for corrupted monitoring endpoints
- **NOT isBugCondition(X)**: All other endpoints and functionality

## Counterexample

**Concrete example demonstrating the bug:**

```python
# Current (corrupted) state:
@app.get("/metrics/legal", tags=["monitoring"])
async def legal_metrics():
    """
    Legal-specific metrics and comprehensive statistics.
    
    **Response Example**:
    ```jso  # ← TRUNCATED HERE
    
# Expected (correct) state:
@app.get("/metrics/legal", tags=["monitoring"])
async def legal_metrics():
    """
    Legal-specific metrics and comprehensive statistics.
    
    Returns detailed legal query metrics including:
    - Total queries and throughput
    - Performance metrics (avg duration, P50, P95, P99)
    - Error rates and categorization
    - SLA compliance rates
    - Queries by court rank and legal domain
    - Cache performance
    - Authority scores
    
    **Response Example**:
    ```json
    {
      "total_queries": 1234,
      "queries_per_second": 2.5,
      "avg_duration_seconds": 0.45,
      "p95_latency": 0.8,
      "error_rate": 0.02,
      "sla_compliance_rate": 0.98,
      "queries_by_court": {
        "SUPREME_COURT": 456,
        "APPEALS_COURT": 789
      }
    }
    ```
    
    Returns:
        Comprehensive legal metrics dictionary
    """
    return legal_monitoring.get_comprehensive_stats()
```

## Affected Components

### Primary
- `api/main.py` (lines 180-350): Monitoring endpoints section

### Secondary
- None (corruption is isolated to one file)

### Dependencies
- `mahoun.monitoring.legal_metrics.legal_monitoring`: Provides monitoring functionality (UNCHANGED)
- `mahoun.metrics.get_metrics_collector`: Provides metrics collection (UNCHANGED)

## Root Cause

File edit operation was interrupted mid-write, causing:
1. Truncated docstrings (incomplete JSON examples)
2. Fragmented function bodies (split across multiple lines)
3. Incomplete statements (missing closing quotes, parentheses)
4. Parse errors throughout the monitoring section

## Impact Assessment

### Severity: CRITICAL
- **Functionality**: API server cannot start (100% broken)
- **Scope**: All monitoring endpoints non-functional
- **Users Affected**: All users (server won't start)
- **Data Loss**: None (monitoring data intact in `mahoun.monitoring`)

### Business Impact
- Phase 3 of Core Cleanup blocked
- Monitoring system inaccessible
- Cannot track legal query metrics
- Cannot check system health via API
- Development and testing blocked

## Success Criteria

### Functional
- ✅ `api/main.py` parses without errors
- ✅ All 4 monitoring endpoints functional
- ✅ Server starts successfully
- ✅ All existing tests pass
- ✅ No regression in non-monitoring endpoints

### Non-Functional
- ✅ Code follows existing style
- ✅ Docstrings are complete and accurate
- ✅ Error handling is consistent
- ✅ Security checks remain in place

## Testing Strategy

### Unit Tests
1. Test `/metrics/legal` returns dict with expected keys
2. Test `/health/detailed` returns health status
3. Test `/metrics/reset` blocks in production
4. Test `/metrics/reset` works in development

### Integration Tests
1. Test server starts without errors
2. Test all monitoring endpoints respond
3. Test Prometheus scraping works
4. Test health checks integrate correctly

### Regression Tests
1. Test all non-monitoring endpoints unchanged
2. Test security middleware still active
3. Test feedback pipeline still works
4. Test database initialization unchanged
