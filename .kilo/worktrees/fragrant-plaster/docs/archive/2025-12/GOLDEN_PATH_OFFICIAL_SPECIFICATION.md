# Golden Path Official Specification

## Overview

This document consolidates the official specification for the Golden Path - the single, real, always-present execution path of the system that satisfies all requirements for a production-grade, evidence-based retrieval system.

## Part 1: Golden Path Definition

See [GOLDEN_PATH_SPECIFICATION.md](GOLDEN_PATH_SPECIFICATION.md) for the complete definition of the Golden Path including:

- Purpose and scope
- Step-by-step execution flow
- Explicit dependencies and non-dependencies

## Part 2: Health & Status Semantics

See [HEALTH_STATUS_SEMANTIC_CORRECTION.md](HEALTH_STATUS_SEMANTIC_CORRECTION.md) for the corrected health status semantics including:

- New STATUS ENUM with precise definitions
- Health reporting rules
- Canonical /health endpoint output format

## Part 3: End-to-End Testing

See [GOLDEN_PATH_E2E_TEST.md](GOLDEN_PATH_E2E_TEST.md) for the official end-to-end test specification including:

- Test name and preconditions
- Execution steps for success and failure paths
- Expected results and validation criteria
- Implementation examples

## Test Files

The following executable test files are provided:

1. [`tests/test_golden_path.py`](tests/test_golden_path.py) - Success path validation
2. [`tests/test_golden_path_failure.py`](tests/test_golden_path_failure.py) - Failure path validation

## Compliance Requirements

All system components MUST adhere to these specifications without exception:

1. **ZERO Feature Expansion**: No new capabilities beyond what's defined in the Golden Path
2. **ZERO Refactoring of Core Logic**: Work only with existing implementations
3. **Truthful Reporting**: The system MUST NEVER lie about its status or capabilities
4. **Evidence-Based Health**: Runtime evidence is REQUIRED for HEALTHY status
5. **Proper Error Handling**: Failures MUST be reported clearly without masking

## Audit Trail

This specification serves as the definitive reference for auditing the system's compliance with production-grade standards. Any deviation from these specifications constitutes a compliance failure that MUST be addressed.

## Version Control

- **Version**: 1.0
- **Date**: December 14, 2025
- **Author**: Senior Systems Engineer & Auditor
- **Status**: APPROVED - IMPLEMENTATION REQUIRED