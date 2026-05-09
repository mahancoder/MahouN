# Validation Gates

<cite>
**Referenced Files in This Document**   
- [gate_0_integrity.sh](file://ci/first_step/gate_0_integrity.sh)
- [gate_1_lint.sh](file://ci/first_step/gate_1_lint.sh)
- [gate_2_types.sh](file://ci/first_step/gate_2_types.sh)
- [gate_3_reality.sh](file://ci/first_step/gate_3_reality.sh)
- [gate_4_antimock.sh](file://ci/first_step/gate_4_antimock.sh)
- [gate_5_determinism.sh](file://ci/first_step/gate_5_determinism.sh)
- [gate_6_artifacts.sh](file://ci/first_step/gate_6_artifacts.sh)
- [gate_7_mypy_non_regression.sh](file://ci/first_step/gate_7_mypy_non_regression.sh)
- [check_mypy_non_regression.py](file://ci/mypy/check_mypy_non_regression.py)
- [test_5_anti_mock.py](file://first_step_ci_cd/test_5_anti_mock.py)
- [test_1_imports.py](file://first_step_ci_cd/test_1_imports.py)
- [test_2_structure.py](file://first_step_ci_cd/test_2_structure.py)
- [test_3_contracts.py](file://first_step_ci_cd/test_3_contracts.py)
- [test_4_logic_light.py](file://first_step_ci_cd/test_4_logic_light.py)
- [ci_run_first_step.sh](file://scripts/ci_run_first_step.sh)
- [ci_run_gates.py](file://scripts/ci_run_gates.py)
- [README.md](file://ci/first_step/README.md)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Gate 0: Repo Integrity](#gate-0-repo-integrity)
3. [Gate 1: Format/Lint](#gate-1-formatlint)
4. [Gate 2: Type Safety](#gate-2-type-safety)
5. [Gate 3: Phase-1 Reality Tests](#gate-3-phase-1-reality-tests)
6. [Gate 4: Anti-Mock Proof](#gate-4-anti-mock-proof)
7. [Gate 5: Determinism Proof](#gate-5-determinism-proof)
8. [Gate 6: Artifact + Traceability](#gate-6-artifact--traceability)
9. [Gate 7: Mypy Non-Regression](#gate-7-mypy-non-regression)
10. [Pipeline Integration](#pipeline-integration)
11. [Conclusion](#conclusion)

## Introduction
The Validation Gates represent a comprehensive CI/CD pipeline designed to ensure code quality, integrity, and reliability before merging into the main branch. This eight-stage validation process systematically verifies different aspects of the codebase, from basic integrity checks to advanced type safety and determinism validation. Each gate serves as a checkpoint that must be passed before code can progress, creating a robust quality assurance framework that prevents regressions and maintains high standards across the codebase.

The gates are organized in a logical sequence that progresses from basic code hygiene to more sophisticated validation of implementation reality and type system consistency. This document details each of the eight validation stages, explaining their specific purpose, implementation logic, success criteria, and failure implications within the CI pipeline.

**Section sources**
- [README.md](file://ci/first_step/README.md#L1-L174)
- [ci_run_first_step.sh](file://scripts/ci_run_first_step.sh#L1-L182)

## Gate 0: Repo Integrity

Gate 0 serves as the first line of defense in the CI pipeline, focusing on codebase integrity and dependency correctness. This gate prevents placeholder patterns, incomplete implementations, and hardcoded secrets from entering the main codebase. It specifically targets critical runtime paths including `mahoun/core/`, `mahoun/domain/`, `mahoun/schemas/`, `mahoun/orchestrator/`, `mahoun/mcp/`, and `api/` while excluding test files and temporary directories.

The gate performs five key checks:
1. **Placeholder detection**: Scans for `pass` statements used as sole function bodies in critical paths
2. **TODO/FIXME detection**: Identifies TODO, FIXME, or XXX comments in core code (excluding approved exceptions)
3. **NotImplementedError detection**: Flags `raise NotImplementedError` statements in non-abstract code
4. **Empty return detection**: Finds functions that only return empty dictionaries or None
5. **Secrets detection**: Uses a Python scanner to detect hardcoded secrets and credentials

The implementation uses grep with carefully crafted patterns to identify violations, applying exclusions for test files and known abstract base classes. When secrets are detected, the gate applies a heavy penalty (incrementing violations by 10) to emphasize their severity. Success criteria require zero violations across all checks, ensuring that only complete, secure implementations pass through.

Failure implications are significant, as this gate blocks any code containing placeholders or secrets. The gate provides specific guidance for remediation, including removing placeholder statements, eliminating hardcoded secrets, and replacing empty returns with proper implementations.

**Section sources**
- [gate_0_integrity.sh](file://ci/first_step/gate_0_integrity.sh#L1-L210)
- [README.md](file://ci/first_step/README.md#L39-L45)

## Gate 1: Format/Lint

Gate 1 enforces code style consistency through static code analysis using the ruff tool. This gate ensures that all code adheres to established formatting and linting standards, promoting readability and maintainability across the codebase. The implementation runs two distinct checks: code linting and code formatting.

The linting check uses `ruff check` with a specific rule set (E, F, I, UP, N, W) to identify code quality issues, syntax errors, and style violations. The formatting check uses `ruff format --check` to verify that code follows the project's formatting conventions without making changes. Both checks output results in GitHub format for easy integration with CI/CD systems.

Success criteria require both the lint check and format check to pass. If either check fails, the gate fails and provides specific remediation instructions. For linting issues, developers are instructed to run `ruff check --fix .` to automatically fix many issues. For formatting issues, they are instructed to run `ruff format .` to reformat the code according to standards.

This gate plays a crucial role in maintaining code quality by catching style violations early in the development process. By automating code formatting and style enforcement, it eliminates debates about code style and allows developers to focus on logic and functionality rather than formatting details.

**Section sources**
- [gate_1_lint.sh](file://ci/first_step/gate_1_lint.sh#L1-L81)
- [README.md](file://ci/first_step/README.md#L52-L57)

## Gate 2: Type Safety

Gate 2 enforces type safety through static type checking, using a tiered approach with multiple type checkers. The gate prioritizes `basedpyright`, falls back to `pyright`, and then uses `mypy` if neither is available. This flexible approach ensures type checking can proceed even if the preferred tool is not installed.

For `mypy`, the gate implements a baseline approach that prevents new type errors from being introduced. It runs mypy on the `mahoun/`, `output/`, and `api/` directories, then compares the output against a baseline file (`mypy_baseline.txt`). Only new errors (those not present in the baseline) cause the gate to fail, allowing the team to gradually improve type coverage without being blocked by existing issues.

The implementation includes automatic installation of `basedpyright` if no type checker is found, ensuring the gate can run in any environment. The gate runs type checking with project-specific configuration from `pyproject.toml` to ensure consistent results across different development environments.

Success criteria require either no type errors (for pyright-based checkers) or no new type errors beyond the baseline (for mypy). Failure indicates type inconsistencies that could lead to runtime errors, and developers are instructed to fix the reported type errors before merging.

**Section sources**
- [gate_2_types.sh](file://ci/first_step/gate_2_types.sh#L1-L103)
- [README.md](file://ci/first_step/README.md#L59-L65)

## Gate 3: Phase-1 Reality Tests

Gate 3 validates the code against real system conditions through a comprehensive test suite that runs 137 laptop-safe reality tests. These tests verify that the implementation is real and functional, not just theoretical or placeholder code. The gate runs the `first_step_ci_cd/` test suite with pytest, using a 120-second timeout to prevent hanging tests.

The test suite is divided into five categories:
- 18 import tests that verify modules can be imported and are not empty
- 33 structure tests that validate class hierarchies and method signatures
- 29 contract tests that verify method contracts and type hints
- 27 light logic tests that check basic functionality
- 30 anti-mock tests that ensure implementations are real

The gate sets environment variables `MAHOUN_NO_EXTERNAL_CALLS=1` and `MAHOUN_TEST_MODE=1` to prevent external service calls and enable test mode, ensuring tests are isolated and repeatable. Success criteria require all tests to pass with no failures or errors. Failure indicates that the code does not meet basic functionality requirements, and developers are instructed to run `pytest first_step_ci_cd/ -v` locally to debug the issues.

This gate serves as a crucial reality check, ensuring that the code works as expected in practice, not just in theory.

**Section sources**
- [gate_3_reality.sh](file://ci/first_step/gate_3_reality.sh#L1-L87)
- [README.md](file://ci/first_step/README.md#L67-L79)
- [test_1_imports.py](file://first_step_ci_cd/test_1_imports.py#L1-L181)
- [test_2_structure.py](file://first_step_ci_cd/test_2_structure.py#L1-L273)
- [test_3_contracts.py](file://first_step_ci_cd/test_3_contracts.py#L1-L283)
- [test_4_logic_light.py](file://first_step_ci_cd/test_4_logic_light.py)

## Gate 4: Anti-Mock Proof

Gate 4 enforces the use of real dependencies over mocks by verifying that implementations are not stubs or placeholders. This gate has two components: running anti-mock tests and checking module complexity.

The first component runs `first_step_ci_cd/test_5_anti_mock.py`, which contains tests that prove implementations are real. These tests use introspection to verify that key methods have substantial code (not just a few lines), contain real logic (not just pass/raise/return statements), and perform meaningful operations like creating unique IDs, processing input data, and building content.

The second component checks module complexity by verifying that critical modules meet minimum line count thresholds. This prevents code from being replaced with trivial implementations. The gate checks:
- `mahoun/agents/base_agent.py`: minimum 500 lines
- `mahoun/agents/claim_agent.py`: minimum 400 lines  
- `output/base_generator.py`: minimum 40 lines
- `output/claim_generator.py`: minimum 35 lines

These thresholds are configurable in `complexity_thresholds.json`. The gate counts non-empty, non-comment lines to measure actual code complexity. Success criteria require both the anti-mock tests to pass and all modules to meet their minimum size requirements. Failure indicates that code may have been replaced with placeholders or significantly reduced in complexity.

**Section sources**
- [gate_4_antimock.sh](file://ci/first_step/gate_4_antimock.sh#L1-L121)
- [README.md](file://ci/first_step/README.md#L80-L89)
- [test_5_anti_mock.py](file://first_step_ci_cd/test_5_anti_mock.py#L1-L385)

## Gate 5: Determinism Proof

Gate 5 validates reproducible builds by ensuring tests produce identical results on repeated runs. This gate addresses non-determinism issues that can cause flaky tests and unreliable CI/CD pipelines. The implementation runs the test suite twice with identical conditions and compares the results.

The gate sets deterministic environment variables including `PYTHONHASHSEED=0`, `MAHOUN_NO_EXTERNAL_CALLS=1`, and `MAHOUN_TEST_MODE=1` to eliminate sources of randomness. It runs the tests, waits two seconds to ensure different timestamps, then runs them again. The comparison includes:
- Exit codes from both runs
- Test count summaries (passed/failed)
- Hashes of the JUnit XML output (with timestamps removed)

By removing timestamps from the XML before hashing, the gate focuses on the actual test results rather than timing differences. Success criteria require identical exit codes, test counts, and XML hashes between runs. Failure indicates non-deterministic behavior, which could be caused by:
- Use of random.random() without a seed
- Use of time.time() or datetime.now() in assertions
- Network calls that are not properly mocked
- File system dependencies
- Dictionary/set iteration order differences

The gate provides specific guidance for fixing non-determinism, including using fixed seeds for random operations and mocking time-based functions.

**Section sources**
- [gate_5_determinism.sh](file://ci/first_step/gate_5_determinism.sh#L1-L145)
- [README.md](file://ci/first_step/README.md#L91-L96)

## Gate 6: Artifact + Traceability

Gate 6 verifies build outputs by generating artifacts and metadata for traceability. This gate creates a comprehensive record of the CI/CD run, enabling auditing, debugging, and historical analysis. The implementation generates three key artifacts in a temporary directory:

1. **reality_report.json**: A machine-readable JSON file containing metadata about the CI run, including commit SHA, branch, Python version, timestamp, and gate results. This file serves as a digital fingerprint of the build.

2. **ci_summary.md**: A human-readable Markdown summary that presents gate results in a table format, lists generated files, and provides next steps for developers.

3. **junit.xml**: Test results from Gate 3, copied from the previous gate's output for archival and reporting purposes.

The gate collects metadata such as the current commit, branch, Python version, and timestamp to ensure the artifacts are contextually complete. Success criteria require all artifacts to be generated successfully. The gate outputs instructions for viewing the generated artifacts, facilitating debugging and verification.

This gate plays a critical role in ensuring traceability and reproducibility, providing a complete record that can be used for compliance, debugging, and historical analysis.

**Section sources**
- [gate_6_artifacts.sh](file://ci/first_step/gate_6_artifacts.sh#L1-L168)
- [README.md](file://ci/first_step/README.md#L100-L104)

## Gate 7: Mypy Non-Regression

Gate 7 prevents type system regressions by ensuring no new mypy errors are introduced. This gate complements Gate 2 by providing a more focused non-regression check specifically for mypy. The implementation uses a Python script (`check_mypy_non_regression.py`) that compares current mypy output against a baseline.

The script runs mypy via `run_mypy.sh`, parses the output to extract error lines, and normalizes them by using file basenames instead of full paths for stability across systems. It then compares the current errors against those in the baseline file (`ci/mypy/baseline.txt`), identifying only new errors (those not present in the baseline).

The comparison logic is sophisticated:
- It ignores summary lines like "Found X errors in Y files"
- It normalizes paths to basenames for cross-system stability
- It sorts errors for deterministic comparison
- It distinguishes between new errors (failures) and fixed errors (improvements)

Success criteria require zero new errors. Failure indicates that type hints have been degraded or removed, potentially introducing runtime type errors. The gate provides two remediation paths: fix the new errors, or intentionally update the baseline if the changes are valid (using `make mypy-baseline`).

This gate enables gradual type system improvement by allowing teams to maintain a baseline of known issues while preventing new ones from being introduced.

**Section sources**
- [gate_7_mypy_non_regression.sh](file://ci/first_step/gate_7_mypy_non_regression.sh#L1-L47)
- [check_mypy_non_regression.py](file://ci/mypy/check_mypy_non_regression.py#L1-L181)

## Pipeline Integration

The eight validation gates are integrated into a cohesive CI/CD pipeline through the `ci_run_first_step.sh` script, which runs gates 0-6 in sequence. The pipeline follows a fail-fast approach, stopping at the first failed gate to provide immediate feedback. Gate 7 runs separately as a non-regression check.

The integration script (`ci_run_first_step.sh`) provides a unified interface for running all gates, displaying progress, timing each gate, and generating a comprehensive summary at the end. It tracks results and durations for each gate, presenting a final verdict based on whether all gates passed.

The pipeline is designed with several key principles:
- **Progressive validation**: Gates are ordered from basic integrity checks to advanced validation
- **Fail-fast**: Stops at the first failure to provide rapid feedback
- **Comprehensive reporting**: Generates detailed summaries and artifacts
- **Developer-friendly**: Provides clear instructions for fixing failures

The gates can be run individually for debugging or all together for complete validation. This modular design allows developers to iterate quickly while ensuring comprehensive validation before merging.

**Section sources**
- [ci_run_first_step.sh](file://scripts/ci_run_first_step.sh#L1-L182)
- [ci_run_gates.py](file://scripts/ci_run_gates.py#L1-L260)

## Conclusion

The eight validation gates form a comprehensive CI/CD pipeline that ensures code quality, integrity, and reliability. Each gate serves a distinct purpose in the validation process, from basic integrity checks to advanced type safety and determinism validation. Together, they create a robust quality assurance framework that prevents regressions and maintains high standards across the codebase.

The pipeline's strength lies in its layered approach, where each gate builds upon the previous ones to provide increasingly sophisticated validation. Gate 0 ensures basic code integrity, Gate 1 enforces style consistency, Gate 2 validates type safety, Gate 3 verifies real functionality, Gate 4 confirms implementation reality, Gate 5 ensures determinism, Gate 6 provides traceability, and Gate 7 prevents type system regressions.

This comprehensive validation process enables the team to maintain a high-velocity development pace while ensuring code quality and reliability. By automating these checks in the CI/CD pipeline, the team can catch issues early, prevent regressions, and maintain confidence in their codebase.