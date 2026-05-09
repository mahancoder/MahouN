# Requirements Document

## Introduction

The legal-aware schema design feature enables the Mahoun platform to hard-code court hierarchy and legal validity directly into the database structure, ensuring proper legal reasoning with zero hallucination guarantees. This system synchronizes vector and graph databases with explicit legal metadata and relationships to support high-stakes legal decisions in regulated industries.

## Glossary

- **Vector_Store**: ChromaDB vector database storing document embeddings with metadata
- **Graph_Store**: Neo4j graph database storing structured legal relationships
- **Legal_Document**: Any document with legal significance (statutes, verdicts, regulations)
- **Court_Hierarchy**: Structured ranking system for legal authority (Supreme > Appeals > First Instance)
- **Legal_Validity**: Status indicating whether a legal document is currently enforceable
- **Global_UID**: Unique identifier shared between vector and graph stores for the same document
- **Authority_Score**: Pre-calculated numerical score based on citation frequency and legal weight
- **Jalali_Date**: Persian calendar date system used in Iranian legal documents
- **Legal_Precedent**: Court decision that establishes a rule for future similar cases
- **Supersession**: Legal relationship where newer law replaces or modifies older law

## Requirements

### Requirement 1: Vector Store Legal Metadata Enhancement

**User Story:** As a legal AI system, I want to store legal metadata directly in vector chunks, so that I can filter and rank documents based on legal authority without additional database queries.

#### Acceptance Criteria

1. WHEN storing a legal document in the vector store, THE Vector_Store SHALL include court_rank as an integer field (1=Supreme, 2=Appeals, 3=First Instance)
2. WHEN storing a statute or regulation, THE Vector_Store SHALL include statute_status as an enumerated field (active, repealed, amended)
3. WHEN storing Iranian legal documents, THE Vector_Store SHALL include date_jalali as a string field for temporal resolution
4. WHEN calculating document importance, THE Vector_Store SHALL include authority_score as a float field based on citation analysis
5. WHEN retrieving documents, THE Vector_Store SHALL support filtering by any legal metadata field

### Requirement 2: Graph Schema Legal Relationship Modeling

**User Story:** As a legal reasoning engine, I want explicit legal relationships in the graph database, so that I can traverse legal connections and validate document authority.

#### Acceptance Criteria

1. WHEN creating legal document nodes, THE Graph_Store SHALL use distinct node labels (Article, Verdict, Law, Court)
2. WHEN a verdict cites an article, THE Graph_Store SHALL create a CITES relationship with status property
3. WHEN a law supersedes another law, THE Graph_Store SHALL create a SUPERSEDED_BY relationship
4. WHEN a higher court reviews a lower court decision, THE Graph_Store SHALL create AFFIRMS or REVERSES relationships
5. WHEN organizing legal topics, THE Graph_Store SHALL create HAS_SUBJECT relationships between laws and topics

### Requirement 3: Cross-System Identifier Synchronization

**User Story:** As a data consistency manager, I want identical document identifiers across vector and graph stores, so that I can prevent data silos and ensure referential integrity.

#### Acceptance Criteria

1. WHEN storing a document in both systems, THE System SHALL use identical doc_id in vector store and uid in graph store
2. WHEN querying documents, THE System SHALL be able to cross-reference between vector and graph stores using the global identifier
3. WHEN updating document metadata, THE System SHALL maintain identifier consistency across both stores
4. WHEN detecting identifier conflicts, THE System SHALL prevent storage and return a descriptive error
5. THE System SHALL validate that every vector document has a corresponding graph node with matching identifier

### Requirement 4: Legal-Aware Document Retrieval

**User Story:** As a legal research system, I want to automatically filter and rank documents based on legal validity and authority, so that I only return legally sound and authoritative results.

#### Acceptance Criteria

1. WHEN retrieving legal documents, THE System SHALL exclude documents with statute_status marked as "repealed"
2. WHEN ranking search results, THE System SHALL prioritize documents with higher court_rank values (lower numbers = higher authority)
3. WHEN multiple documents have the same topic, THE System SHALL rank by authority_score in descending order
4. WHEN handling temporal conflicts, THE System SHALL use date_jalali for chronological precedence resolution
5. WHEN a document is superseded, THE System SHALL return the superseding document instead of the original

### Requirement 5: Legal Precedent Validation

**User Story:** As a legal compliance officer, I want the system to validate legal precedent chains, so that I can ensure all cited authorities are currently valid and properly hierarchical.

#### Acceptance Criteria

1. WHEN traversing citation relationships, THE System SHALL verify that cited documents have not been superseded
2. WHEN validating court hierarchy, THE System SHALL ensure lower court decisions do not override higher court precedents
3. WHEN detecting contradictory precedents, THE System SHALL flag conflicts and provide resolution based on court hierarchy
4. WHEN a precedent is overturned, THE System SHALL update all dependent reasoning chains
5. THE System SHALL maintain an audit trail of all precedent validation decisions

### Requirement 6: Persian Legal Document Support

**User Story:** As an Iranian legal researcher, I want the system to handle Persian legal documents with Jalali dates, so that I can work with local legal materials in their native format.

#### Acceptance Criteria

1. WHEN processing Persian legal documents, THE System SHALL correctly parse and store Jalali dates
2. WHEN comparing document dates, THE System SHALL convert between Jalali and Gregorian calendars as needed
3. WHEN displaying Persian legal documents, THE System SHALL preserve original text encoding and formatting
4. WHEN searching Persian legal content, THE System SHALL support both Persian and transliterated queries
5. THE System SHALL handle mixed Persian-English legal documents with appropriate language detection

### Requirement 7: Zero-Hallucination Legal Reasoning

**User Story:** As a regulated industry user, I want every legal conclusion to be explicitly linked to verifiable evidence, so that I can maintain audit trails and regulatory compliance.

#### Acceptance Criteria

1. WHEN generating legal conclusions, THE System SHALL link every statement to specific graph nodes and relationships
2. WHEN a legal rule is cited, THE System SHALL verify the rule's current validity status before inclusion
3. WHEN contradictory evidence exists, THE System SHALL explicitly identify conflicts and resolution methodology
4. WHEN providing legal advice, THE System SHALL include confidence scores based on evidence strength
5. THE System SHALL maintain complete provenance chains from conclusion back to source documents

### Requirement 8: Migration and Data Consistency

**User Story:** As a system administrator, I want to migrate existing data to the new legal-aware schema, so that I can maintain historical data while gaining new legal reasoning capabilities.

#### Acceptance Criteria

1. WHEN migrating existing vector data, THE System SHALL preserve all original embeddings and add legal metadata fields
2. WHEN migrating existing graph data, THE System SHALL create new legal relationship types without losing existing connections
3. WHEN data migration fails, THE System SHALL provide rollback capabilities to restore previous state
4. WHEN validating migrated data, THE System SHALL ensure all documents have complete legal metadata
5. THE System SHALL provide migration progress reporting and error logging for troubleshooting