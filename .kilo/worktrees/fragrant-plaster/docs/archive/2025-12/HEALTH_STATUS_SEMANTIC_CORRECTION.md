# Health & Status Semantic Correction

## New Health Status Semantics

To ensure the system never lies and maintains clear separation between runtime survival and truth reporting, we introduce the following STATUS ENUM with precise semantics:

### Status Definitions

- **HEALTHY**: Component is actively used in Golden Path and is fully operational
- **AVAILABLE**: Component exists and is functional but NOT used in Golden Path
- **DISABLED**: Component is explicitly turned off by design/configuration
- **UNAVAILABLE**: Component dependency is missing or cannot be initialized
- **DEGRADED**: Component is used in Golden Path but partially impaired

## Health Reporting Rules

1. **Overall Status Calculation**:
   - ONLY Golden Path components affect `overall_status`
   - Non-Golden components MUST be reported separately
   - A component with `initialized=false` can NEVER be HEALTHY

2. **Truth Enforcement**:
   - The system MUST NEVER report HEALTHY for unverified components
   - Runtime survival and truth reporting are SEPARATED
   - Missing dependencies MUST be reported as UNAVAILABLE, not HEALTHY

## Canonical /health Endpoint Output

```json
{
  "overall_status": "HEALTHY",
  "golden_path_status": "HEALTHY",
  "golden_path_components": {
    "ingestion_pipeline": {
      "status": "HEALTHY",
      "message": "Document ingestion pipeline is operational",
      "details": {
        "initialized": true,
        "text_handlers_available": ["txt"],
        "optional_handlers": {
          "docx": "UNAVAILABLE",
          "pdf": "UNAVAILABLE"
        }
      }
    },
    "vector_store": {
      "status": "HEALTHY",
      "message": "ChromaDB vector store is operational",
      "details": {
        "backend": "chromadb",
        "initialized": true,
        "collections": 1,
        "documents_stored": 0
      }
    },
    "embedding_service": {
      "status": "HEALTHY",
      "message": "Sentence transformer embedding service is ready",
      "details": {
        "model_loaded": true,
        "model_name": "paraphrase-multilingual-MiniLM-L12-v2"
      }
    },
    "hybrid_search": {
      "status": "HEALTHY",
      "message": "Hybrid search engine is operational",
      "details": {
        "dense_retrieval": "HEALTHY",
        "sparse_retrieval": "UNAVAILABLE",
        "fusion_methods": ["RRF", "WEIGHTED_SUM"]
      }
    }
  },
  "non_critical_components": {
    "ollama": {
      "status": "DISABLED",
      "message": "Ollama integration is disabled in this runtime mode",
      "details": {
        "enabled": false,
        "mode": "desktop_minimal"
      }
    },
    "graph": {
      "status": "DISABLED",
      "message": "Graph system is disabled (expected in desktop_minimal mode)",
      "details": {
        "enabled": false,
        "mode": "desktop_minimal"
      }
    },
    "postgresql": {
      "status": "DISABLED",
      "message": "PostgreSQL integration is disabled in this runtime mode",
      "details": {
        "enabled": false,
        "mode": "desktop_minimal"
      }
    },
    "redis": {
      "status": "DISABLED",
      "message": "Redis integration is disabled in this runtime mode",
      "details": {
        "enabled": false,
        "mode": "desktop_minimal"
      }
    }
  }
}
```

## Implementation Notes

1. **Runtime Evidence Requirement**: 
   - All HEALTHY statuses MUST be backed by runtime evidence (counts, IDs, latency measurements)
   - Static responses or import success do NOT constitute health proof

2. **Separation of Concerns**:
   - Golden Path components directly impact system usability
   - Non-critical components are reported but don't affect overall system status

3. **Graceful Degradation**:
   - DISABLED components are intentionally turned off and don't represent failures
   - UNAVAILABLE components indicate missing dependencies that may be optionally installed
   - DEGRADED components are partially functional but may impact quality of results