# Requirements Document: Contract Formalization Phase

## Introduction

The Contract Formalization Phase establishes explicit, machine-verifiable contracts for all six core modules of the Mahoun platform. This phase transforms implicit interface assumptions into formal Pydantic schemas that define inputs, outputs, and failure modes. The goal is to create enforceable contracts that enable automated validation, improve auditability, and prevent interface degradation.

This phase is part of the Architecture Hardening initiative and builds directly on Phase 1 (Core Boundary Lock), which established clear boundaries between core and non-core modules.

## Glossary

- **Contract**: A formal specification of a module's inputs, outputs, and failure modes using Pydantic schemas
- **Contract_Schema**: A Pydantic model that defines validation rules, required fields, and constraints
- **Contract_Test**: An automated test that validates contract compliance without testing behavior
- **Input_Contract**: A Pydantic schema defining valid inputs to a function or method
- **Output_Contract**: A Pydantic schema defining the structure and constraints of function outputs
- **Error_Contract**: A Pydantic schema defining error types and failure modes
- **Core_Module**: One of the six essential modules (reasoning, graph, invariants, schemas, ledger, core)
- **Public_Interface**: The set of classes, functions, and methods exposed by a module for external use
- **Contract_Violation**: A runtime error where data does not conform to its contract schema
- **Schema_Validation**: The process of checking data against a Pydantic schema
- **Invariant_Enforcement**: Validation that system invariants (e.g., I1: 100% groundedness) are maintained

## Requirements

### Requirement 1: Interface Analysis and Documentation

**User Story:** As a platform architect, I want comprehensive documentation of all core module interfaces, so that I can design accurate contracts.

#### Acceptance Criteria

1. THE System SHALL analyze the public interface of each Core_Module
2. THE System SHALL document all public classes, functions, and methods for each Core_Module
3. THE System SHALL identify all input parameters, return types, and exceptions for each public interface
4. THE System SHALL document the purpose and usage of each public interface
5. THE System SHALL identify implicit assumptions and constraints in existing interfaces
6. THE System SHALL create an interface analysis document for each Core_Module

### Requirement 2: Input Contract Creation

**User Story:** As a compliance engineer, I want explicit input validation rules, so that invalid data is rejected before processing.

#### Acceptance Criteria

1. WHEN a Core_Module function accepts input, THEN THE System SHALL define an Input_Contract using Pydantic
2. THE Input_Contract SHALL specify all required fields with appropriate types
3. THE Input_Contract SHALL specify validation rules (min_length, max_length, ge, le, pattern)
4. THE Input_Contract SHALL use `extra="forbid"` to reject unexpected fields
5. THE Input_Contract SHALL include field descriptions explaining each parameter
6. THE Input_Contract SHALL include example values in `json_schema_extra`
7. WHEN input violates the contract, THEN THE System SHALL raise a clear validation error

### Requirement 3: Output Contract Creation

**User Story:** As an integration partner, I want guaranteed output structures, so that I can reliably parse responses.

#### Acceptance Criteria

1. WHEN a Core_Module function returns output, THEN THE System SHALL define an Output_Contract using Pydantic
2. THE Output_Contract SHALL specify all fields that will be present in the output
3. THE Output_Contract SHALL specify field types and constraints
4. THE Output_Contract SHALL use `extra="forbid"` to ensure clean data structures
5. THE Output_Contract SHALL include field descriptions explaining each output field
6. THE Output_Contract SHALL include example values in `json_schema_extra`
7. WHEN output violates the contract, THEN THE System SHALL raise a clear validation error

### Requirement 4: Error Contract Creation

**User Story:** As a system operator, I want documented failure modes, so that I can handle errors appropriately.

#### Acceptance Criteria

1. WHEN a Core_Module function can fail, THEN THE System SHALL define an Error_Contract for each failure mode
2. THE Error_Contract SHALL specify an `error_type` field with a pattern constraint listing all valid error types
3. THE Error_Contract SHALL specify a `message` field with human-readable error description
4. THE Error_Contract SHALL specify an optional `details` field for additional error context
5. THE Error_Contract SHALL use `extra="forbid"` to ensure clean error structures
6. THE System SHALL document all possible failure modes for each public interface
7. WHEN an error occurs, THEN THE System SHALL return data conforming to the Error_Contract

### Requirement 5: Contract Schema Organization

**User Story:** As a developer, I want organized contract schemas, so that I can easily find and use them.

#### Acceptance Criteria

1. THE System SHALL create a `mahoun/schemas/contracts/` directory
2. THE System SHALL create one contract file per Core_Module: `{module}_contracts.py`
3. THE System SHALL organize contracts by public interface within each file
4. THE System SHALL include comprehensive docstrings for each contract schema
5. THE System SHALL export all contracts in the module's `__all__` list
6. THE System SHALL include validation rules and examples in each contract
7. THE System SHALL ensure contract files have no dependencies on non-core modules

### Requirement 6: Contract Test Creation

**User Story:** As a quality engineer, I want automated contract validation, so that contract violations are detected immediately.

#### Acceptance Criteria

1. THE System SHALL create a `tests/contracts/` directory
2. THE System SHALL create one test file per Core_Module: `test_{module}_contracts.py`
3. WHEN testing an Input_Contract, THEN THE System SHALL test valid inputs are accepted
4. WHEN testing an Input_Contract, THEN THE System SHALL test invalid inputs are rejected
5. WHEN testing an Output_Contract, THEN THE System SHALL test all required fields are present
6. WHEN testing an Error_Contract, THEN THE System SHALL test error types are validated
7. THE System SHALL ensure contract tests are independent of behavior tests
8. THE System SHALL ensure contract tests do not call actual module implementations

### Requirement 7: Reasoning Module Contracts

**User Story:** As a reasoning engine user, I want formal contracts for verdict generation, so that I can validate inputs and outputs.

#### Acceptance Criteria

1. THE System SHALL create contracts for `EvidenceLinkedVerdictEngine.generate_verdict()`
2. THE System SHALL create contracts for `ChainOfThoughtReasoner.reason()`
3. THE System SHALL create contracts for `DeepLegalReasoningEngine.deep_reason()`
4. THE System SHALL create contracts for evidence reference structures
5. THE System SHALL create contracts for reasoning step structures
6. THE System SHALL create contracts for causal relation structures
7. THE System SHALL enforce invariant I1 (100% groundedness) in verdict contracts

### Requirement 8: Graph Module Contracts

**User Story:** As a graph builder user, I want formal contracts for graph operations, so that I can validate graph construction and queries.

#### Acceptance Criteria

1. THE System SHALL create contracts for `UltraGraphBuilder.build_graph()`
2. THE System SHALL create contracts for graph node structures
3. THE System SHALL create contracts for graph edge structures
4. THE System SHALL create contracts for graph metrics
5. THE System SHALL create contracts for graph query operations (neighbors, paths, subgraphs)
6. THE System SHALL validate entity and relationship structures
7. THE System SHALL ensure graph quality metrics are properly typed

### Requirement 9: Invariants Module Contracts

**User Story:** As a compliance auditor, I want formal contracts for invariant validation, so that I can verify system guarantees.

#### Acceptance Criteria

1. THE System SHALL create contracts for `InvariantSpec` structure
2. THE System SHALL create contracts for invariant validation inputs
3. THE System SHALL create contracts for invariant validation outputs
4. THE System SHALL create contracts for invariant violation errors
5. THE System SHALL document all invariant IDs and their meanings
6. THE System SHALL ensure invariant contracts reference specific invariant specifications
7. THE System SHALL validate that invariant checks return boolean results

### Requirement 10: Schemas Module Contracts

**User Story:** As a schema designer, I want meta-contracts for schema validation, so that schemas themselves are validated.

#### Acceptance Criteria

1. THE System SHALL create meta-contracts for `VerdictStruct` validation
2. THE System SHALL create meta-contracts for `TextDocument` validation
3. THE System SHALL create contracts for schema field validation
4. THE System SHALL create contracts for schema configuration validation
5. THE System SHALL ensure meta-contracts validate schema structure
6. THE System SHALL ensure meta-contracts validate field types and constraints
7. THE System SHALL document the difference between schemas and contracts

### Requirement 11: Ledger Module Contracts

**User Story:** As an audit trail consumer, I want formal contracts for ledger entries, so that I can validate audit data.

#### Acceptance Criteria

1. THE System SHALL create contracts for `EvidenceLedgerWriter.write_entry()`
2. THE System SHALL create contracts for `LedgerEntry` structure
3. THE System SHALL create contracts for ledger validation
4. THE System SHALL create contracts for hash chain integrity
5. THE System SHALL enforce invariants EL-I1 through EL-I7 in ledger contracts
6. THE System SHALL validate that ledger entries are immutable
7. THE System SHALL ensure privacy-sensitive data is filtered per EL-I7

### Requirement 12: Core Module Contracts

**User Story:** As a core utilities user, I want formal contracts for domain models and protocols, so that I can validate core data structures.

#### Acceptance Criteria

1. THE System SHALL create contracts for `ReasoningResult` structure
2. THE System SHALL create contracts for `ReasoningStep` structure
3. THE System SHALL create contracts for `CausalRelation` structure
4. THE System SHALL create contracts for `UncertaintyEstimate` structure
5. THE System SHALL create contracts for protocol definitions
6. THE System SHALL ensure core contracts have no infrastructure dependencies
7. THE System SHALL validate that core contracts are pure domain models

### Requirement 13: Contract Validation Rules

**User Story:** As a contract designer, I want consistent validation rules, so that all contracts follow the same standards.

#### Acceptance Criteria

1. THE System SHALL use `extra="forbid"` in all contract schemas
2. THE System SHALL use `Field(...)` for all required fields
3. THE System SHALL use `Field(default=...)` or `Field(default_factory=...)` for optional fields
4. THE System SHALL use appropriate validators (min_length, max_length, ge, le, pattern)
5. THE System SHALL include `description` for all fields
6. THE System SHALL include `json_schema_extra` with examples for all contracts
7. THE System SHALL use `ConfigDict` for Pydantic v2 configuration

### Requirement 14: Contract Documentation

**User Story:** As a new developer, I want comprehensive contract documentation, so that I can understand how to use contracts.

#### Acceptance Criteria

1. THE System SHALL include module-level docstrings in each contract file
2. THE System SHALL include class-level docstrings for each contract schema
3. THE System SHALL document which requirements each contract validates
4. THE System SHALL document which invariants each contract enforces
5. THE System SHALL include usage examples in docstrings
6. THE System SHALL document failure modes in error contract docstrings
7. THE System SHALL create a `contracts/README.md` explaining the contract system

### Requirement 15: Backward Compatibility Preservation

**User Story:** As an existing user, I want contracts to be non-breaking, so that my code continues to work.

#### Acceptance Criteria

1. THE System SHALL NOT change existing function signatures
2. THE System SHALL NOT change existing return types
3. THE System SHALL NOT change existing behavior
4. THE System SHALL add contracts as validation layers, not replacements
5. WHEN contracts are added, THEN THE System SHALL ensure existing tests still pass
6. THE System SHALL ensure contracts are additive, not destructive
7. THE System SHALL validate backward compatibility through regression tests

### Requirement 16: Contract Test Independence

**User Story:** As a test engineer, I want contract tests separate from behavior tests, so that I can validate contracts without testing implementation.

#### Acceptance Criteria

1. THE System SHALL create contract tests that only validate schema compliance
2. THE System SHALL NOT call actual module implementations in contract tests
3. THE System SHALL test contract validation with mock data
4. THE System SHALL test that valid data passes validation
5. THE System SHALL test that invalid data fails validation
6. THE System SHALL test that validation errors are clear and actionable
7. THE System SHALL ensure contract tests run faster than behavior tests

### Requirement 17: Contract Coverage Completeness

**User Story:** As a project manager, I want complete contract coverage, so that all public interfaces are validated.

#### Acceptance Criteria

1. THE System SHALL create contracts for all public classes in each Core_Module
2. THE System SHALL create contracts for all public methods in each Core_Module
3. THE System SHALL create contracts for all public functions in each Core_Module
4. THE System SHALL document any interfaces that cannot be contracted
5. THE System SHALL ensure at least 90% of public interfaces have contracts
6. THE System SHALL create a coverage report showing contract completeness
7. THE System SHALL identify gaps in contract coverage

### Requirement 18: Phase Completion Validation

**User Story:** As a project stakeholder, I want clear completion criteria, so that I know when Phase 2 is done.

#### Acceptance Criteria

1. THE System SHALL verify all 6 Core_Modules have contract files
2. THE System SHALL verify all 6 Core_Modules have contract test files
3. THE System SHALL verify all contract tests pass
4. THE System SHALL verify contract coverage is at least 90%
5. THE System SHALL verify no backward compatibility is broken
6. THE System SHALL create a Phase 2 completion report
7. THE System SHALL commit all contract files and tests to git
