# Core Final Cleanup - Requirements

## Overview
Complete core cleanup: remove orphaned modules, fix metrics duplication, achieve 100% core independence.

## User Stories

### US-1: Clean Core Module
- AC-1.1: All infrastructure modules removed from core/
- AC-1.2: All orphaned prototypes removed
- AC-1.3: Only essential utilities remain
- AC-1.4: Core independence score = 100%

### US-2: Single Metrics Implementation
- AC-2.1: Only mahoun/metrics exists
- AC-2.2: All imports updated (3 files)
- AC-2.3: core/metrics removed
- AC-2.4: All tests pass

### US-3: Enterprise Monitoring Active
- AC-3.1: mahoun/monitoring integrated with API
- AC-3.2: Prometheus endpoint active
- AC-3.3: Legal metrics working
- AC-3.4: Documentation updated

### US-4: Clean LLM Structure
- AC-4.1: Decision on core/llm location
- AC-4.2: Imports updated if moved
- AC-4.3: Tests pass
- AC-4.4: Documentation updated

### US-5: Orphaned Modules Removed
- AC-5.1: core/graph/ removed
- AC-5.2: core/ingest/ removed
- AC-5.3: core/rag/ removed
- AC-5.4: core/monitoring/ removed

## Success Metrics
- Core independence: 100%
- Test pass rate: 100%
- Import violations: 0
- Orphaned modules: 0
