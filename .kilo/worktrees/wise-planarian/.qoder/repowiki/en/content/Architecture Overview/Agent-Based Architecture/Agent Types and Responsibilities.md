# Agent Types and Responsibilities

<cite>
**Referenced Files in This Document**   
- [mahoun/agents/__init__.py](file://mahoun/agents/__init__.py)
- [mahoun/agents/base_agent.py](file://mahoun/agents/base_agent.py)
- [mahoun/agents/factory.py](file://mahoun/agents/factory.py)
- [mahoun/agents/orchestrator.py](file://mahoun/agents/orchestrator.py)
- [mahoun/agents/ultra_factory.py](file://mahoun/agents/ultra_factory.py)
- [mahoun/agents/doc_parser_agent.py](file://mahoun/agents/doc_parser_agent.py)
- [mahoun/agents/contract_agent.py](file://mahoun/agents/contract_agent.py)
- [mahoun/agents/dispute_agent.py](file://mahoun/agents/dispute_agent.py)
- [mahoun/agents/delay_agent.py](file://mahoun/agents/delay_agent.py)
- [mahoun/agents/risk_assessment_agent.py](file://mahoun/agents/risk_assessment_agent.py)
- [mahoun/agents/ultra_delay_agent.py](file://mahoun/agents/ultra_delay_agent.py)
- [mahoun/agents/ultra_risk_assessment_agent.py](file://mahoun/agents/ultra_risk_assessment_agent.py)
- [mahoun/agents/ultra_precedent_agent.py](file://mahoun/agents/ultra_precedent_agent.py)
- [mahoun/agents/ultra_timeline_agent.py](file://mahoun/agents/ultra_timeline_agent.py)
- [mahoun/agents/narrative_agent.py](file://mahoun/agents/narrative_agent.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Core Agent Architecture](#core-agent-architecture)
3. [Agent Factory and Initialization](#agent-factory-and-initialization)
4. [Document Parser Agent](#document-parser-agent)
5. [Contract Agent](#contract-agent)
6. [Delay Agent](#delay-agent)
7. [Dispute Agent](#dispute-agent)
8. [Risk Assessment Agent](#risk-assessment-agent)
9. [Timeline Agent](#timeline-agent)
10. [Legal Precedent Agent](#legal-precedent-agent)
11. [Narrative Agent](#narrative-agent)
12. [Critic Agent](#critic-agent)
13. [Ultra Agent Variants](#ultra-agent-variants)
14. [Agent Orchestration](#agent-orchestration)
15. [Error Handling and Performance](#error-handling-and-performance)
16. [Conclusion](#conclusion)

## Introduction
The MAHOUN system employs a sophisticated multi-agent architecture designed for comprehensive legal document analysis and decision support. This document details the specialized AI agents within the system, their responsibilities, implementation details, and interactions with core systems. The agents are built on a robust foundation that includes circuit breakers, retry mechanisms, health monitoring, and graceful degradation. They interact with key systems such as the knowledge graph, RAG (Retrieval-Augmented Generation) system, and LLM (Large Language Model) router to provide domain-specific expertise in areas like contract analysis, dispute identification, delay assessment, and risk evaluation. This documentation provides a thorough explanation of each agent type, their interfaces, input/output schemas, and configuration options, making the system accessible to both beginners and experienced developers.

## Core Agent Architecture

The foundation of the MAHOUN agent system is the `UltraBaseAgent` class, which provides enterprise-grade patterns for reliability and resilience. All specialized agents inherit from this base class, ensuring a consistent implementation of critical features.

```mermaid
classDiagram
class UltraBaseAgent {
+str name
+AgentConfig config
+AgentState _state
+CircuitBreaker _circuit_breaker
+Dict[str, Any] _metrics
+logging.Logger logger
+__init__(name : str, config : Optional[AgentConfig])
+initialize() bool
+close() None
+process(input_data : Dict, correlation_id : Optional[str]) AgentResult
+health_check() Dict[str, Any]
+get_metrics() Dict[str, Any]
+get_status() Dict[str, Any]
}
class AgentConfig {
+int max_retries
+float retry_base_delay
+float retry_max_delay
+float retry_exponential_base
+int circuit_breaker_threshold
+float circuit_breaker_timeout
+float operation_timeout
+float initialization_timeout
+float health_check_interval
+str log_level
+bool enable_correlation_id
+bool enable_fallback
+float fallback_timeout
}
class AgentResult~T~ {
+bool success
+Optional[T] data
+Optional[str] error
+Optional[str] error_type
+Optional[str] correlation_id
+float processing_time_ms
+int retries_used
+bool fallback_used
+List[str] warnings
+to_dict() Dict[str, Any]
}
class AgentState {
<<enumeration>>
CREATED
INITIALIZING
READY
PROCESSING
DEGRADED
FAILED
SHUTDOWN
}
class CircuitBreakerState {
<<enumeration>>
CLOSED
OPEN
HALF_OPEN
}
class CircuitBreaker {
+CircuitBreakerState state
+int failure_count
+Optional[datetime] last_failure_time
+int threshold
+float timeout
+record_success() None
+record_failure() None
+can_execute() bool
}
UltraBaseAgent --> AgentConfig : "has"
UltraBaseAgent --> AgentResult : "returns"
UltraBaseAgent --> AgentState : "uses"
UltraBaseAgent --> CircuitBreaker : "uses"
CircuitBreaker --> CircuitBreakerState : "uses"
```

**Diagram sources**
- [mahoun/agents/base_agent.py](file://mahoun/agents/base_agent.py#L1-L576)

**Section sources**
- [mahoun/agents/base_agent.py](file://mahoun/agents/base_agent.py#L1-L576)

## Agent Factory and Initialization

Agents are created and managed through factory patterns that provide centralized control and lifecycle management. The system includes both a legacy `AgentFactory` and an enhanced `UltraAgentFactory` for creating Ultra agents with additional enterprise features.

```mermaid
classDiagram
class AgentFactory {
+create_agent(agent_type : str, config : Optional[Dict]) BaseAgent
+create_all_agents(config : Optional[Dict]) Dict[str, BaseAgent]
+list_available_agents() List[str]
+get_agent_info(agent_type : str) Dict[str, Any]
+register_agent(agent_type : str, agent_class : Type[BaseAgent]) None
}
class UltraAgentFactory {
+create(agent_type : str, config : Optional[Dict], use_singleton : bool) UltraBaseAgent
+get_or_create(agent_type : str, config : Optional[Dict]) UltraBaseAgent
+create_all(config : Optional[Dict], categories : Optional[List]) Dict[str, UltraBaseAgent]
+list_available() List[Dict[str, Any]]
+get_agent_info(agent_type : str) Dict[str, Any]
+health_check_all() Dict[str, Dict[str, Any]]
+shutdown_all() None
+register(name : str, agent_class : Type[UltraBaseAgent], ...) None
}
class LegacyAgentAdapter {
+__init__(legacy_agent, name : str)
+_initialize_impl() None
+_process_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_fallback_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
}
AgentFactory --> BaseAgent : "creates"
UltraAgentFactory --> UltraBaseAgent : "creates"
UltraAgentFactory --> LegacyAgentAdapter : "wraps"
LegacyAgentAdapter --> BaseAgent : "adapts"
```

**Diagram sources**
- [mahoun/agents/factory.py](file://mahoun/agents/factory.py#L1-L182)
- [mahoun/agents/ultra_factory.py](file://mahoun/agents/ultra_factory.py#L1-L590)

**Section sources**
- [mahoun/agents/factory.py](file://mahoun/agents/factory.py#L1-L182)
- [mahoun/agents/ultra_factory.py](file://mahoun/agents/ultra_factory.py#L1-L590)

## Document Parser Agent

The Document Parser Agent is responsible for extracting and processing text from various document formats, including PDF, DOCX, and images. It integrates with NER (Named Entity Recognition), legal storage, and intelligent chunking systems to provide comprehensive document analysis.

### Domain Responsibilities
- Extract text from multi-format documents (PDF, DOCX, TXT, images)
- Perform OCR (Optical Character Recognition) for scanned documents
- Apply Persian legal text normalization
- Parse verdict structure into a standardized format
- Extract legal entities using NER
- Create intelligent document chunks with coherence scoring
- Store processed documents in ChromaDB and PostgreSQL

### Interfaces and Configuration
The agent uses the `DocParserConfig` class for configuration, which extends the base `AgentConfig`.

```mermaid
classDiagram
class DocParserConfig {
+bool enable_ner
+float ner_confidence_threshold
+bool enable_legal_storage
+bool enable_chromadb_storage
+int chunk_size
+int chunk_overlap
+bool enable_coherence_scoring
+bool enable_ocr
+str ocr_language
+int min_text_length
+int max_text_length
}
class UltraDocParserAgent {
+__init__(config : Optional[DocParserConfig])
+_initialize_impl() None
+_process_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_fallback_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_extract_text_from_file(file_path : str, correlation_id : Optional[str]) str
+_parse_verdict(text : str, correlation_id : Optional[str]) Dict[str, Any]
+_extract_entities(text : str, correlation_id : Optional[str]) Dict[str, List[Dict[str, Any]]]
+_create_chunks(text : str, doc_id : str, verdict_struct : Dict, correlation_id : Optional[str]) List[Dict[str, Any]]
+_store_document(doc_id : str, verdict_struct : Dict, chunks : List, source_file : Optional[str], correlation_id : Optional[str]) Dict[str, Any]
+_calculate_quality_metrics(text : str, verdict_struct : Dict, entities : Dict, chunks : List) Dict[str, Any]
+_health_check_impl() Dict[str, Any]
+get_doc_metrics() Dict[str, Any]
}
UltraDocParserAgent --> DocParserConfig : "uses"
UltraDocParserAgent --> UltraBaseAgent : "inherits"
```

**Diagram sources**
- [mahoun/agents/doc_parser_agent.py](file://mahoun/agents/doc_parser_agent.py#L1-L566)

**Section sources**
- [mahoun/agents/doc_parser_agent.py](file://mahoun/agents/doc_parser_agent.py#L1-L566)

### Input/Output Schema
**Input Schema:**
```json
{
  "text": "string (optional)",
  "file_path": "string (optional)",
  "doc_id": "string (optional)",
  "doc_type": "string (optional)",
  "metadata": "object (optional)",
  "skip_storage": "boolean (optional)",
  "skip_ner": "boolean (optional)"
}
```

**Output Schema:**
```json
{
  "doc_id": "string",
  "doc_type": "string",
  "verdict_struct": "object",
  "entities": "object",
  "chunks": "array",
  "chunks_count": "integer",
  "storage_result": "object",
  "quality_metrics": "object",
  "processing_time_ms": "number",
  "metadata": "object"
}
```

### Core System Interactions
- **Knowledge Graph**: Entities extracted by NER are used to build and enrich the knowledge graph.
- **RAG System**: Document chunks are indexed in the vector store for retrieval.
- **LLM Router**: The agent uses the LLM router for text processing and entity extraction.

### Example Usage
```python
from mahoun.agents import UltraAgentFactory

# Create and initialize the agent
agent = await UltraAgentFactory.create("doc_parser")

# Process a document
result = await agent.process({
    "file_path": "/path/to/document.pdf",
    "doc_type": "verdict"
})
```

## Contract Agent

The Contract Agent specializes in analyzing contract clauses, answering contractual questions, and providing risk assessments. It uses chain-of-thought reasoning and NLI (Natural Language Inference) verification to ensure accurate and reliable responses.

### Domain Responsibilities
- Analyze contract clauses for risk and compliance
- Answer complex contractual questions using multi-step reasoning
- Verify answers using NLI (Natural Language Inference)
- Provide confidence calibration and citation tracking
- Perform clause-level risk scoring and recommendations

### Interfaces and Configuration
The agent uses the `ContractAgentConfig` class for configuration, which includes settings for reasoning, verification, and clause analysis.

```mermaid
classDiagram
class ReasoningMode {
<<enumeration>>
SIMPLE
CHAIN_OF_THOUGHT
MULTI_HOP
AUTO
}
class RiskLevel {
<<enumeration>>
CRITICAL
HIGH
MEDIUM
LOW
MINIMAL
}
class ClauseType {
<<enumeration>>
PAYMENT
PRICE_ADJUSTMENT
ADVANCE_PAYMENT
RETENTION
BANK_GUARANTEE
DELIVERY
SCOPE_OF_WORK
TIMELINE
MILESTONES
ACCEPTANCE
SUBCONTRACTING
WARRANTY
PERFORMANCE_BOND
INSURANCE
LIABILITY
INDEMNIFICATION
LIMITATION
CONSEQUENTIAL_DAMAGES
TERMINATION
SUSPENSION
EXPIRY
PENALTY
LIQUIDATED_DAMAGES
DELAY_PENALTY
FORCE_MAJEURE
DISPUTE
ARBITRATION
GOVERNING_LAW
JURISDICTION
CONFIDENTIALITY
INTELLECTUAL_PROPERTY
NON_COMPETE
NON_SOLICITATION
ASSIGNMENT
AMENDMENT
NOTICE
ENTIRE_AGREEMENT
SEVERABILITY
WAIVER
COMPLIANCE
ANTI_CORRUPTION
SANCTIONS
DATA_PROTECTION
ENVIRONMENTAL
HEALTH_SAFETY
GENERAL
}
class ContractAgentConfig {
+int top_k
+int rerank_top_k
+float min_relevance_score
+ReasoningMode reasoning_mode
+bool enable_chain_of_thought
+int max_reasoning_steps
+bool enable_verification
+float verification_threshold
+int max_answer_length
+bool include_citations
+bool include_confidence
+bool enable_clause_analysis
+bool enable_risk_scoring
+float risk_threshold_critical
+float risk_threshold_high
+float risk_threshold_medium
}
class ClauseRisk {
+str clause_id
+str clause_text
+ClauseType clause_type
+RiskLevel risk_level
+float risk_score
+List[str] risk_factors
+List[str] recommendations
+List[str] legal_references
+to_dict() Dict[str, Any]
}
class ContractAnalysis {
+int total_clauses
+int analyzed_clauses
+List[ClauseRisk] clauses
+float overall_risk_score
+RiskLevel overall_risk_level
+int high_risk_clauses
+str summary
+to_dict() Dict[str, Any]
}
class ReasoningStep {
+int step_number
+str thought
+str action
+str observation
+float confidence
}
class ReasoningChain {
+str question
+List[ReasoningStep] steps
+str final_answer
+float total_confidence
+bool verified
+to_dict() Dict[str, Any]
}
class UltraContractAgent {
+__init__(config : Optional[ContractAgentConfig])
+_initialize_impl() None
+_process_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_fallback_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_retrieve_documents(query : str, top_k : int, correlation_id : Optional[str]) List[Dict[str, Any]]
+_select_reasoning_mode(query : str, rag_results : List[Dict]) ReasoningMode
+_chain_of_thought_reasoning(query : str, context : str, rag_results : List[Dict], correlation_id : Optional[str]) tuple
+_simple_reasoning(query : str, rag_results : List[Dict], correlation_id : Optional[str]) tuple
+_verify_answer(answer : str, evidence : List[str], correlation_id : Optional[str]) bool
+_build_citations(rag_results : List[Dict]) List[Dict[str, Any]]
+_health_check_impl() Dict[str, Any]
+get_contract_metrics() Dict[str, Any]
}
UltraContractAgent --> ContractAgentConfig : "uses"
UltraContractAgent --> UltraBaseAgent : "inherits"
UltraContractAgent --> ReasoningChain : "produces"
UltraContractAgent --> ContractAnalysis : "produces"
```

**Diagram sources**
- [mahoun/agents/contract_agent.py](file://mahoun/agents/contract_agent.py#L1-L1685)

**Section sources**
- [mahoun/agents/contract_agent.py](file://mahoun/agents/contract_agent.py#L1-L1685)

### Input/Output Schema
**Input Schema:**
```json
{
  "query": "string",
  "context": "string (optional)",
  "top_k": "integer (optional)",
  "reasoning_mode": "string (optional)",
  "skip_verification": "boolean (optional)"
}
```

**Output Schema:**
```json
{
  "answer": "string",
  "confidence": "number",
  "verified": "boolean",
  "reasoning_chain": "object",
  "citations": "array",
  "metadata": "object"
}
```

### Core System Interactions
- **Knowledge Graph**: Contract clauses and relationships are stored and queried from the knowledge graph.
- **RAG System**: The agent uses the hybrid RAG service for retrieving relevant contract clauses and legal precedents.
- **LLM Router**: The reasoning service uses the LLM router for chain-of-thought reasoning.

### Example Usage
```python
from mahoun.agents import UltraAgentFactory

# Create and initialize the agent
agent = await UltraAgentFactory.create("contract")

# Analyze a contract question
result = await agent.process({
    "query": "Is delay penalty claimable under these conditions?",
    "reasoning_mode": "cot"
})
```

## Delay Agent

The Delay Agent analyzes project delays by integrating timeline data, schedule information, and RAG results to identify, classify, and attribute delays.

### Domain Responsibilities
- Identify delays from project documents and timelines
- Classify delays by type (excusable, non-excusable, concurrent)
- Attribute responsibility for delays to parties (contractor, client, force majeure)
- Analyze impact on critical path
- Support forensic schedule analysis

### Interfaces and Configuration
The agent uses a simple configuration dictionary and integrates with existing components.

```mermaid
classDiagram
class DelayAgent {
+__init__(config : Optional[Dict])
+initialize() None
+_process_impl(input_data : Dict) Dict[str, Any]
+_extract_delays(results : list, timeline : list) list
+_extract_delay_days(text : str) int
+_analyze_delays(delays : list, baseline : dict, actual : dict) dict
+_identify_critical_path(timeline : list) list
+_attribute_responsibility(delays : list) dict
}
DelayAgent --> BaseAgent : "inherits"
```

**Diagram sources**
- [mahoun/agents/delay_agent.py](file://mahoun/agents/delay_agent.py#L1-L220)

**Section sources**
- [mahoun/agents/delay_agent.py](file://mahoun/agents/delay_agent.py#L1-L220)

### Input/Output Schema
**Input Schema:**
```json
{
  "project_id": "string",
  "baseline_schedule": "object (optional)",
  "actual_schedule": "object (optional)",
  "query": "string"
}
```

**Output Schema:**
```json
{
  "delays": "array",
  "delay_analysis": "object",
  "critical_path": "array",
  "attribution": "object",
  "timeline": "array",
  "metadata": "object"
}
```

### Core System Interactions
- **Knowledge Graph**: Timeline events and dependencies are stored in the knowledge graph.
- **RAG System**: The agent uses the hybrid RAG service to search for delay-related information.
- **LLM Router**: The reasoning service is used for analyzing delay causes and impacts.

### Example Usage
```python
from mahoun.agents import AgentFactory

# Create and initialize the agent
agent = await AgentFactory.create_agent("delay")

# Analyze project delays
result = await agent.process({
    "project_id": "P12345",
    "query": "Analyze delays in project execution"
})
```

## Dispute Agent

The Dispute Agent detects and analyzes disputes, contract violations, and risks by combining RAG, reasoning, and citation extraction capabilities.

### Domain Responsibilities
- Detect disputes and contract violations
- Classify disputes by type (financial, temporal, quality, contractual)
- Score dispute severity
- Assess overall risk level
- Generate legal references and recommendations
- Extract related clauses for backward compatibility

### Interfaces and Configuration
The agent uses a simple configuration dictionary and integrates with multiple components.

```mermaid
classDiagram
class DisputeType {
<<enumeration>>
FINANCIAL
TEMPORAL
QUALITY
CONTRACTUAL
PROCEDURAL
OTHER
}
class DisputeSeverity {
<<enumeration>>
CRITICAL
HIGH
MEDIUM
LOW
}
class DisputeAgent {
+__init__(config : Optional[Dict])
+initialize() None
+_process_impl(input_data : Dict) Dict[str, Any]
+_deep_analysis(query : str, documents : List[str]) tuple
+_classify_disputes(disputes : List[Dict]) List[Dict]
+_calculate_severity(disputes : List[Dict]) List[Dict]
+_find_legal_references(disputes : List[Dict]) List[Dict]
+_assess_risk(disputes : List[Dict], violations : List[Dict]) Dict[str, Any]
+_generate_recommendations(disputes : List[Dict], risk_assessment : Dict) List[str]
+_summarize_types(disputes : List[Dict]) Dict[str, int]
+_extract_related_clauses(citations : List[Any]) List[Dict]
}
DisputeAgent --> BaseAgent : "inherits"
```

**Diagram sources**
- [mahoun/agents/dispute_agent.py](file://mahoun/agents/dispute_agent.py#L1-L429)

**Section sources**
- [mahoun/agents/dispute_agent.py](file://mahoun/agents/dispute_agent.py#L1-L429)

### Input/Output Schema
**Input Schema:**
```json
{
  "query": "string",
  "documents": "array (optional)",
  "focus_areas": "array (optional)"
}
```

**Output Schema:**
```json
{
  "disputes": "array",
  "violations": "array",
  "related_clauses": "array",
  "citations": "array",
  "dispute_types": "object",
  "risk_assessment": "object",
  "legal_references": "array",
  "recommendations": "array",
  "metadata": "object"
}
```

### Core System Interactions
- **Knowledge Graph**: Dispute relationships and legal references are stored in the knowledge graph.
- **RAG System**: The agent uses the hybrid RAG service and query router for comprehensive search.
- **LLM Router**: The reasoning service is used for deep analysis of disputes.

### Example Usage
```python
from mahoun.agents import AgentFactory

# Create and initialize the agent
agent = await AgentFactory.create_agent("dispute")

# Analyze disputes
result = await agent.process({
    "query": "Identify disputes in the contract execution",
    "documents": ["doc1", "doc2"]
})
```

## Risk Assessment Agent

The Risk Assessment Agent evaluates the risk of legal claims by analyzing strengths, weaknesses, success probability, and cost-benefit analysis.

### Domain Responsibilities
- Assess strengths and weaknesses of a legal case
- Calculate success probability
- Perform cost-benefit analysis
- Generate strategic recommendations
- Integrate with dispute analysis for comprehensive risk assessment

### Interfaces and Configuration
The agent uses a simple configuration dictionary and integrates with multiple components.

```mermaid
classDiagram
class RiskAssessmentAgent {
+__init__(config : Optional[Dict])
+initialize() None
+_process_impl(input_data : Dict) Dict[str, Any]
+_assess_strengths_weaknesses(case_description : str, dispute_result : Dict, documents : List[str]) tuple
+_calculate_success_probability(strengths : List[str], weaknesses : List[str], dispute_result : Dict) float
+_calculate_overall_risk(success_prob : float, dispute_risk : Dict) Dict[str, Any]
+_analyze_cost_benefit(claim_type : str, success_prob : float, overall_risk : Dict) Dict[str, Any]
+_generate_strategic_recommendations(overall_risk : Dict, success_prob : float, strengths : List[str], weaknesses : List[str]) List[str]
}
RiskAssessmentAgent --> BaseAgent : "inherits"
```

**Diagram sources**
- [mahoun/agents/risk_assessment_agent.py](file://mahoun/agents/risk_assessment_agent.py#L1-L288)

**Section sources**
- [mahoun/agents/risk_assessment_agent.py](file://mahoun/agents/risk_assessment_agent.py#L1-L288)

### Input/Output Schema
**Input Schema:**
```json
{
  "case_description": "string",
  "documents": "array",
  "claim_type": "string"
}
```

**Output Schema:**
```json
{
  "overall_risk": "object",
  "success_probability": "number",
  "strengths": "array",
  "weaknesses": "array",
  "cost_benefit": "object",
  "recommendations": "array",
  "dispute_analysis": "object",
  "metadata": "object"
}
```

### Core System Interactions
- **Knowledge Graph**: Case strengths, weaknesses, and risk factors are stored in the knowledge graph.
- **RAG System**: The agent uses the hybrid RAG service to gather relevant case information.
- **LLM Router**: The reasoning service is used for assessing strengths and weaknesses.

### Example Usage
```python
from mahoun.agents import AgentFactory

# Create and initialize the agent
agent = await AgentFactory.create_agent("risk_assessment")

# Assess risk of a claim
result = await agent.process({
    "case_description": "Claim for delay damages in construction project",
    "claim_type": "delay",
    "documents": ["contract", "correspondence"]
})
```

## Timeline Agent

The Timeline Agent extracts and analyzes temporal events from legal documents, checking for consistency and validating event sequences.

### Domain Responsibilities
- Extract dates and events from text
- Normalize Persian and Gregorian dates
- Classify event types (contractual, performance, correspondence, legal, financial)
- Check temporal consistency and detect conflicts
- Generate visual timeline support

### Interfaces and Configuration
The agent uses the `TimelineConfig` class for configuration.

```mermaid
classDiagram
class EventType {
<<enumeration>>
CONTRACTUAL
PERFORMANCE
CORRESPONDENCE
LEGAL
FINANCIAL
DELAY
OTHER
}
class TimelineEvent {
+str id
+str date_raw
+str date_normalized
+str description
+EventType event_type
+str source_doc_id
+float confidence
+List[str] dependencies
+Dict[str, Any] metadata
+to_dict() Dict
}
class TimelineResult {
+List[TimelineEvent] events
+Optional[str] start_date
+Optional[str] end_date
+int duration_days
+float consistency_score
+List[str] gaps_detected
+List[Dict] conflicting_events
}
class TimelineConfig {
+float min_confidence
+bool detect_causality
+bool normalize_dates
}
class UltraTimelineAgent {
+__init__(config : Optional[TimelineConfig])
+_initialize_impl() None
+_process_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_extract_events_from_docs(docs : List[Dict]) List[TimelineEvent]
+_find_date(text : str) Tuple[Optional[str], Optional[str]]
+_classify_event_type(text : str) EventType
+_check_consistency(events : List[TimelineEvent]) Tuple[float, List[Dict]]
+_calc_duration(start : Optional[str], end : Optional[str]) int
}
UltraTimelineAgent --> TimelineConfig : "uses"
UltraTimelineAgent --> UltraBaseAgent : "inherits"
UltraTimelineAgent --> TimelineEvent : "produces"
UltraTimelineAgent --> TimelineResult : "produces"
```

**Diagram sources**
- [mahoun/agents/ultra_timeline_agent.py](file://mahoun/agents/ultra_timeline_agent.py#L1-L290)

**Section sources**
- [mahoun/agents/ultra_timeline_agent.py](file://mahoun/agents/ultra_timeline_agent.py#L1-L290)

### Input/Output Schema
**Input Schema:**
```json
{
  "query": "string (optional)",
  "documents": "array (optional)"
}
```

**Output Schema:**
```json
{
  "timeline": "array",
  "analysis": "object"
}
```

### Core System Interactions
- **Knowledge Graph**: Temporal events and dependencies are stored as nodes and relationships.
- **RAG System**: The agent uses the hybrid RAG service to retrieve relevant documents for timeline extraction.
- **LLM Router**: The reasoning service could be used for causal link analysis.

### Example Usage
```python
from mahoun.agents import UltraAgentFactory

# Create and initialize the agent
agent = await UltraAgentFactory.create("timeline")

# Extract timeline
result = await agent.process({
    "query": "Extract all events from the contract execution"
})
```

## Legal Precedent Agent

The Legal Precedent Agent searches for similar legal cases and precedents, extracting legal principles and generating comparisons.

### Domain Responsibilities
- Search for legal precedents using semantic similarity
- Extract legal principles from precedents
- Generate case comparison analysis
- Rank precedents by relevance
- Provide recommendations based on findings

### Interfaces and Configuration
The agent uses the `PrecedentAgentConfig` class for configuration.

```mermaid
classDiagram
class PrecedentType {
<<enumeration>>
SUPREME_COURT
APPEAL_COURT
GENERAL_COURT
ADMINISTRATIVE
UNKNOWN
}
class RelevanceLevel {
<<enumeration>>
HIGHLY_RELEVANT
RELEVANT
SOMEWHAT_RELEVANT
LOW_RELEVANCE
}
class PrecedentAgentConfig {
+int top_k
+float min_similarity
+bool extract_principles
+bool generate_comparison
+int max_precedents
}
class LegalPrecedent {
+str doc_id
+str content
+float similarity
+PrecedentType precedent_type
+RelevanceLevel relevance
+Optional[str] court_name
+Optional[str] case_number
+Optional[str] date
+List[str] legal_principles
}
class LegalPrinciple {
+str text
+str source_doc
+float confidence
+Optional[str] category
}
class UltraPrecedentAgent {
+__init__(config : Optional[PrecedentAgentConfig])
+_initialize_impl() None
+_process_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_fallback_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_build_search_query(case_description : str, case_type : str, legal_issues : List[str]) str
+_search_precedents(query : str, correlation_id : Optional[str]) List[Dict]
+_process_results(results : List[Dict], court_preference : Optional[str]) List[LegalPrecedent]
+_detect_court_type(content : str) PrecedentType
+_assess_relevance(score : float) RelevanceLevel
+_extract_court_name(content : str) Optional[str]
+_extract_principles(precedents : List[LegalPrecedent]) List[LegalPrinciple]
+_generate_comparison(case_description : str, precedents : List[LegalPrecedent]) Dict[str, Any]
+_generate_recommendations(precedents : List[LegalPrecedent], principles : List[LegalPrinciple]) List[str]
+_precedent_to_dict(p : LegalPrecedent) Dict
+_principle_to_dict(p : LegalPrinciple) Dict
+_health_check_impl() Dict[str, Any]
}
UltraPrecedentAgent --> PrecedentAgentConfig : "uses"
UltraPrecedentAgent --> UltraBaseAgent : "inherits"
UltraPrecedentAgent --> LegalPrecedent : "produces"
UltraPrecedentAgent --> LegalPrinciple : "produces"
```

**Diagram sources**
- [mahoun/agents/ultra_precedent_agent.py](file://mahoun/agents/ultra_precedent_agent.py#L1-L445)

**Section sources**
- [mahoun/agents/ultra_precedent_agent.py](file://mahoun/agents/ultra_precedent_agent.py#L1-L445)

### Input/Output Schema
**Input Schema:**
```json
{
  "case_description": "string",
  "case_type": "string (optional)",
  "legal_issues": "array (optional)",
  "court_preference": "string (optional)"
}
```

**Output Schema:**
```json
{
  "precedents": "array",
  "legal_principles": "array",
  "comparison": "object",
  "recommendations": "array",
  "metadata": "object"
}
```

### Core System Interactions
- **Knowledge Graph**: Precedent relationships and legal principles are stored in the knowledge graph.
- **RAG System**: The agent uses the hybrid RAG service for semantic search of precedents.
- **LLM Router**: The reasoning service could be used for extracting legal principles.

### Example Usage
```python
from mahoun.agents import UltraAgentFactory

# Create and initialize the agent
agent = await UltraAgentFactory.create("precedent")

# Search for precedents
result = await agent.process({
    "case_description": "Dispute over construction delay penalties",
    "case_type": "construction",
    "legal_issues": ["delay", "penalty", "compensation"]
})
```

## Narrative Agent

The Narrative Agent generates comprehensive legal-technical narratives by integrating information from various sources and analyses.

### Domain Responsibilities
- Generate legal-technical narratives combining legal and technical aspects
- Structure narratives into sections (introduction, analysis, conclusions)
- Integrate citations from legal sources
- Use reasoning for coherent narrative generation
- Support different narrative types (legal, technical, combined)

### Interfaces and Configuration
The agent uses a simple configuration dictionary and integrates with multiple components.

```mermaid
classDiagram
class NarrativeAgent {
+__init__(config : Optional[Dict])
+initialize() None
+_process_impl(input_data : Dict) Dict[str, Any]
+_build_context(topic : str, context : str, analysis_results : dict) str
+_generate_section(section_title : str, context : str, results : list) str
+_combine_sections(sections : dict) str
+_generate_simple_narrative(topic : str, context : str, results : list) str
+_extract_conclusions(narrative : str, results : list) list
}
NarrativeAgent --> BaseAgent : "inherits"
```

**Diagram sources**
- [mahoun/agents/narrative_agent.py](file://mahoun/agents/narrative_agent.py#L1-L225)

**Section sources**
- [mahoun/agents/narrative_agent.py](file://mahoun/agents/narrative_agent.py#L1-L225)

### Input/Output Schema
**Input Schema:**
```json
{
  "topic": "string",
  "context": "string (optional)",
  "analysis_results": "object (optional)",
  "narrative_type": "string (optional)"
}
```

**Output Schema:**
```json
{
  "narrative": "string",
  "sections": "object",
  "citations": "array",
  "conclusions": "array",
  "metadata": "object"
}
```

### Core System Interactions
- **Knowledge Graph**: Narrative elements and relationships are stored in the knowledge graph.
- **RAG System**: The agent uses the hybrid RAG service to retrieve relevant information for narrative generation.
- **LLM Router**: The reasoning service is used for generating narrative sections.

### Example Usage
```python
from mahoun.agents import AgentFactory

# Create and initialize the agent
agent = await AgentFactory.create_agent("narrative")

# Generate a narrative
result = await agent.process({
    "topic": "Analysis of construction delay claims",
    "context": "Project P12345, contract signed on 2023-01-01",
    "analysis_results": {"delays": [...], "risks": [...]}
})
```

## Critic Agent

The Critic Agent is responsible for verifying the integrity and faithfulness of responses generated by other agents. It acts as a red-teaming component to ensure the reliability of the system's outputs.

### Domain Responsibilities
- Verify the faithfulness of answers to their supporting evidence
- Detect potential hallucinations in generated responses
- Provide integrity reports for agent outputs
- Integrate with the orchestrator's integrity guard

### Interfaces and Configuration
The Critic Agent uses the base agent configuration and implements the standard processing interface.

```mermaid
classDiagram
class CriticAgent {
+__init__(config : Optional[AgentConfig])
+_initialize_impl() None
+_process_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_fallback_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_health_check_impl() Dict[str, Any]
}
CriticAgent --> UltraBaseAgent : "inherits"
```

**Section sources**
- [mahoun/agents/critic_agent.py](file://mahoun/agents/critic_agent.py)

### Input/Output Schema
**Input Schema:**
```json
{
  "query": "string",
  "answer": "string",
  "context": "array"
}
```

**Output Schema:**
```json
{
  "faithfulness_score": "number",
  "integrity_report": "object",
  "warnings": "array"
}
```

### Core System Interactions
- **Knowledge Graph**: Integrity reports and verification results are stored in the knowledge graph.
- **RAG System**: The agent uses the RAG system to retrieve supporting evidence for verification.
- **LLM Router**: The agent uses the LLM router for NLI (Natural Language Inference) verification.

### Example Usage
```python
from mahoun.agents import AgentFactory

# Create and initialize the agent
agent = await AgentFactory.create_agent("critic")

# Verify an answer
result = await agent.process({
    "query": "Is the delay penalty applicable?",
    "answer": "Yes, the delay penalty is applicable according to clause 15.2.",
    "context": ["clause 15.2 text", "related correspondence"]
})
```

## Ultra Agent Variants

The MAHOUN system includes "Ultra" variants of several agents that provide enhanced capabilities with advanced features such as probabilistic modeling, graph analysis, and enterprise-grade patterns.

### Ultra Delay Agent
The Ultra Delay Agent extends the basic Delay Agent with automated delay identification, excusability analysis, concurrent delay detection, and critical path impact analysis.

```mermaid
classDiagram
class DelayType {
<<enumeration>>
EXCUSABLE_COMPENSABLE
EXCUSABLE_NON_COMPENSABLE
NON_EXCUSABLE
CONCURRENT
}
class DelayEvent {
+str id
+str description
+str start_date
+str end_date
+int duration_days
+DelayType delay_type
+str responsible_party
+bool impact_on_critical_path
+List[str] evidence_doc_ids
+float confidence
}
class DelayAnalysisResult {
+int total_delay_days
+int excusable_days
+int non_excusable_days
+int concurrent_days
+int compensable_days
+List[DelayEvent] critical_path_delays
+List[DelayEvent] all_delays
+str recommendation
}
class DelayConfig {
+int min_delay_days
+bool strict_mode
+str default_calendar
}
class UltraDelayAgent {
+__init__(config : Optional[DelayConfig])
+_initialize_impl() None
+_process_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_identify_delays(events : List[Dict]) List[DelayEvent]
+_classify_delays(delays : List[DelayEvent]) List[DelayEvent]
+_aggregate_analysis(delays : List[DelayEvent]) Dict
}
UltraDelayAgent --> DelayConfig : "uses"
UltraDelayAgent --> UltraBaseAgent : "inherits"
UltraDelayAgent --> DelayEvent : "produces"
UltraDelayAgent --> DelayAnalysisResult : "produces"
```

**Diagram sources**
- [mahoun/agents/ultra_delay_agent.py](file://mahoun/agents/ultra_delay_agent.py#L1-L217)

**Section sources**
- [mahoun/agents/ultra_delay_agent.py](file://mahoun/agents/ultra_delay_agent.py#L1-L217)

### Ultra Risk Assessment Agent
The Ultra Risk Assessment Agent extends the basic Risk Assessment Agent with probabilistic success estimation using Gaussian Process, uncertainty quantification, topological risk analysis using graph RAG, and Monte Carlo cost-benefit analysis.

```mermaid
classDiagram
class RiskLevel {
<<enumeration>>
CRITICAL
HIGH
MEDIUM
LOW
MINIMAL
}
class RiskAgentConfig {
+int mc_simulations
+float confidence_threshold
+int max_precedents
+bool enable_gp
+bool enable_graph
}
class StrengthWeakness {
+str content
+float impact
+str source
+float confidence
}
class FinancialRisk {
+float estimated_cost
+float potential_gain
+float roi_ratio
+float worst_case_loss
+float best_case_gain
+float break_even_probability
}
class RiskAssessmentResult {
+RiskLevel overall_risk
+float success_probability
+float uncertainty_score
+List[StrengthWeakness] strengths
+List[StrengthWeakness] weaknesses
+FinancialRisk financial_analysis
+List[str] recommendations
+int similar_cases_count
+float legal_complexity_score
}
class UltraRiskAssessmentAgent {
+__init__(config : Optional[RiskAgentConfig])
+_initialize_impl() None
+_process_impl(input_data : Dict, correlation_id : Optional[str]) Dict[str, Any]
+_analyze_precedents(query : str, claim_type : str) List[Dict]
+_estimate_success_probability(case_desc : str, precedents : List[Dict]) Tuple[float, float]
+_extract_factors(text : str, precedents : List[Dict]) Tuple[List[StrengthWeakness], List[StrengthWeakness]]
+_perform_financial_analysis(fin_data : Dict, prob : float, uncertainty : float) FinancialRisk
+_determine_risk_level(prob : float, unc : float, fin : FinancialRisk) RiskLevel
+_generate_recommendations(risk : RiskLevel, prob : float, weaknesses : List[StrengthWeakness]) List[str]
+_result_to_dict(res : RiskAssessmentResult) Dict
}
UltraRiskAssessmentAgent --> RiskAgentConfig : "uses"
UltraRiskAssessmentAgent --> UltraBaseAgent : "inherits"
UltraRiskAssessmentAgent --> RiskAssessmentResult : "produces"
```

**Diagram sources**
- [mahoun/agents/ultra_risk_assessment_agent.py](file://mahoun/agents/ultra_risk_assessment_agent.py#L1-L344)

**Section sources**
- [mahoun/agents/ultra_risk_assessment_agent.py](file://mahoun/agents/ultra_risk_assessment_agent.py#L1-L344)

## Agent Orchestration

The MAHOUN system uses an orchestrator to manage complex workflows involving multiple agents. The orchestrator executes workflows as Directed Acyclic Graphs (DAGs), enabling parallel execution with dependency resolution.

### Workflow Execution
The orchestrator allows defining workflows as DAGs where nodes represent agent executions and edges represent dependencies.

```mermaid
classDiagram
class NodeStatus {
<<enumeration>>
PENDING
READY
RUNNING
COMPLETED
FAILED
SKIPPED
CANCELLED
}
class WorkflowStatus {
<<enumeration>>
CREATED
RUNNING
PAUSED
COMPLETED
FAILED
CANCELLED
}
class WorkflowNode {
+str id
+str agent_name
+Dict[str, Any] config
+List[str] dependencies
+bool required
+float timeout
+int retries
+NodeStatus status
+Optional[AgentResult] result
+Optional[datetime] start_time
+Optional[datetime] end_time
+Optional[str] error
}
class WorkflowDAG {
+str name
+Dict[str, WorkflowNode] nodes
+Dict[str, Any] metadata
+add_node(node : WorkflowNode) None
+validate() List[str]
+get_execution_order() List[List[str]]
}
class ExecutionContext {
+str workflow_id
+Dict[str, Any] initial_data
+Dict[str, Any] node_results
+Dict[str, Any] variables
+get_input_for_node(node : WorkflowNode) Dict[str, Any]
}
class WorkflowCheckpoint {
+str workflow_id
+str dag_name
+datetime timestamp
+List[str] completed_nodes
+Dict[str, Any] node_results
+Dict[str, Any] context_variables
}
class UltraOrchestrator {
+__init__()
+register_agent(name : str, agent : UltraBaseAgent) None
+unregister_agent(name : str) None
+get_agent(name : str) Optional[UltraBaseAgent]
+execute_workflow(dag : WorkflowDAG, initial_data : Dict, checkpoint : Optional[WorkflowCheckpoint], max_parallel : int) Dict[str, Any]
+_execute_node(node : WorkflowNode, context : ExecutionContext) AgentResult
+_validate_integrity(node : WorkflowNode, result : AgentResult, context : ExecutionContext) None
+_build_final_data(dag : WorkflowDAG, context : ExecutionContext) Dict[str, Any]
+_create_checkpoint(workflow_id : str, dag : WorkflowDAG, context : ExecutionContext) None
+get_checkpoint(workflow_id : str) Optional[WorkflowCheckpoint]
+on_progress(callback : Callable[[str, str, float], Awaitable[None]]) None
+_report_progress(workflow_id : str, node_id : str, progress : float) None
+get_workflow_status(workflow_id : str) Optional[Dict[str, Any]]
+get_all_agent_status() Dict[str, Any]
+visualize_dag(dag : WorkflowDAG, format : str) str
+_visualize_ascii(dag : WorkflowDAG) str
+_visualize_mermaid(dag : WorkflowDAG) str
+_visualize_dot(dag : WorkflowDAG) str
+_visualize_json(dag : WorkflowDAG) str
}
UltraOrchestrator --> WorkflowDAG : "executes"
UltraOrchestrator --> WorkflowNode : "manages"
UltraOrchestrator --> ExecutionContext : "uses"
UltraOrchestrator --> WorkflowCheckpoint : "uses"
UltraOrchestrator --> UltraBaseAgent : "orchestrates"
```

**Diagram sources**
- [mahoun/agents/orchestrator.py](file://mahoun/agents/orchestrator.py#L1-L800)

**Section sources**
- [mahoun/agents/orchestrator.py](file://mahoun/agents/orchestrator.py#L1-L800)

### Example Workflow
```python
from mahoun.agents import UltraOrchestrator, WorkflowDAG, WorkflowNode

# Create orchestrator and register agents
orchestrator = UltraOrchestrator()
orchestrator.register_agent("doc_parser", doc_parser_agent)
orchestrator.register_agent("contract", contract_agent)
orchestrator.register_agent("narrative", narrative_agent)

# Define workflow DAG
dag = WorkflowDAG(name="contract_analysis")
dag.add_node(WorkflowNode(id="parse", agent_name="doc_parser"))
dag.add_node(WorkflowNode(id="analyze", agent_name="contract", dependencies=["parse"]))
dag.add_node(WorkflowNode(id="report", agent_name="narrative", dependencies=["analyze"]))

# Execute workflow
result = await orchestrator.execute_workflow(dag, {"text": "..."})
```

## Error Handling and Performance

The MAHOUN agent system implements comprehensive error handling and performance optimization strategies to ensure reliability and efficiency.

### Error Handling
All agents inherit robust error handling from the `UltraBaseAgent` class, which includes:
- **Circuit Breaker Pattern**: Prevents cascade failures by temporarily rejecting requests when failure thresholds are exceeded.
- **Retry with Exponential Backoff**: Handles transient failures by retrying with increasing delays.
- **Graceful Degradation**: Provides fallback implementations when primary processing fails.
- **Structured Logging**: Includes correlation IDs for tracing requests across services.
- **Health Checks**: Monitors agent health and dependencies.

### Timeout Management
Each agent implements timeout management at multiple levels:
- **Operation Timeout**: Maximum time for a single processing operation.
- **Initialization Timeout**: Maximum time for agent initialization.
- **Node Timeout**: In orchestrator workflows, maximum time for individual node execution.

### Performance Optimization
Key performance optimizations include:
- **Lazy Loading**: Components are initialized only when needed.
- **Singleton Management**: Agents are reused to avoid repeated initialization.
- **Parallel Execution**: The orchestrator executes independent nodes in parallel.
- **Caching**: Results are cached where appropriate to avoid redundant processing.
- **Efficient Chunking**: Documents are intelligently chunked to balance context and processing efficiency.

### Monitoring and Metrics
All agents provide comprehensive metrics through the `get_metrics()` and `get_status()` methods, including:
- Total calls and success rate
- Processing time and throughput
- Retry and failure counts
- Fallback usage
- Custom agent-specific metrics

## Conclusion
The MAHOUN system's specialized AI agents form a comprehensive ecosystem for legal document analysis and decision support. Each agent is designed with a specific domain responsibility, from document parsing and contract analysis to delay assessment and risk evaluation. The agents are built on a robust foundation that ensures reliability, resilience, and scalability. They interact seamlessly with core systems like the knowledge graph, RAG system, and LLM router, leveraging their capabilities to provide sophisticated analysis. The use of enterprise patterns such as circuit breakers, retry mechanisms, and graceful degradation ensures high availability and fault tolerance. The orchestrator enables complex multi-agent workflows, allowing for sophisticated analysis pipelines. This documentation provides a thorough understanding of the agent types, their implementation details, and their interactions, making the system accessible to both beginners and experienced developers.