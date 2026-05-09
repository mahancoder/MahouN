# Citation and Provenance Engine

<cite>
**Referenced Files in This Document**   
- [citation_engine.py](file://mahoun/rag/citation_engine.py)
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py)
- [evidence_enrichment.py](file://mahoun/rag/evidence_enrichment.py)
- [ultra_evaluation_system.py](file://mahoun/rag/ultra_evaluation_system.py)
- [contract_agent.py](file://mahoun/agents/contract_agent.py)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Citation Engine Implementation](#citation-engine-implementation)
3. [Citation Extraction and Relevance Scoring](#citation-extraction-and-relevance-scoring)
4. [Citation Formatting and Legal Standards](#citation-formatting-and-legal-standards)
5. [Citation Integrity Verification](#citation-integrity-verification)
6. [Evidence Enrichment Integration](#evidence-enrichment-integration)
7. [Citation Generation in Legal Q&A](#citation-generation-in-legal-qa)
8. [Citation Accuracy and Completeness](#citation-accuracy-and-completeness)
9. [Configuration and Formatting Options](#configuration-and-formatting-options)
10. [Conclusion](#conclusion)

## Introduction
The Citation and Provenance Engine is a comprehensive system designed to provide verifiable source attribution for all generated responses within the MAHOUN platform. This engine ensures that every answer is backed by precise document excerpts, properly formatted citations, and rigorous validation against legal standards. The system integrates multiple components to extract, verify, and enrich citations, creating a robust framework for legal and contractual analysis. By leveraging advanced retrieval techniques, citation auditing, and evidence enrichment, the engine delivers accurate, reliable, and legally compliant responses. This documentation details the implementation of the citation_engine.py, its integration with guardrails/ultra_citation_auditor.py for integrity verification, and examples from contract_agent.py demonstrating citation generation in legal Q&A scenarios.

**Section sources**
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L1-L335)

## Citation Engine Implementation
The Citation Engine is implemented in citation_engine.py and serves as the core component for extracting and formatting citations from retrieval results. The engine processes results from the HybridRAGService, extracting precise citation information such as document title, page number, section, and clause number. It uses regular expression patterns to identify citation details within the content and metadata of retrieved documents. The engine constructs Citation objects containing the extracted information and formats them according to specified standards. The implementation includes methods for building individual citations, extracting citation details from content, and formatting citations in both plain text and Markdown formats. The engine is designed to handle multiple citation formats and provides flexibility in citation presentation.

```mermaid
classDiagram
class Citation {
+str doc_id
+Optional[str] doc_title
+Optional[int] page_number
+Optional[str] section
+Optional[str] clause_number
+str content
+float score
+Dict[str, Any] metadata
+str citation_text
}
class CitationResult {
+str query
+List[Citation] citations
+str formatted_citations
+Dict[str, Any] metadata
}
class CitationEngine {
+Dict[str, List[str]] patterns
+async extract_citations(rag_result : Any, query : str, max_citations : int) CitationResult
+_build_citation(retrieval_result : Any, query : str) Optional[Citation]
+_extract_clause_number(content : str) Optional[str]
+_extract_page_number(content : str, metadata : Dict[str, Any]) Optional[int]
+_extract_section(content : str, metadata : Dict[str, Any]) Optional[str]
+_build_citation_text(doc_title : str, clause_number : Optional[str], page_number : Optional[int], section : Optional[str], content : str) str
+_format_citations(citations : List[Citation]) str
+format_citation_markdown(citation : Citation) str
+format_citations_markdown(citations : List[Citation]) str
}
CitationEngine --> Citation : "creates"
CitationEngine --> CitationResult : "returns"
```

**Diagram sources**
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L26-L37)
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L40-L45)
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L48-L335)

**Section sources**
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L1-L335)

## Citation Extraction and Relevance Scoring
The citation extraction process begins with the retrieval of relevant documents using the HybridRAGService, which combines graph and text-based retrieval methods. The Citation Engine then processes these results to extract citation details using predefined patterns for clauses, pages, and sections. The relevance scoring is derived from the retrieval results, with the engine preserving the original relevance scores from the HybridRAGService. The extraction process involves analyzing both the content and metadata of retrieved documents to identify citation information. For each retrieval result, the engine constructs a Citation object containing the document ID, title, page number, section, clause number, content, score, metadata, and formatted citation text. The engine supports multiple citation formats and can handle both explicit and implicit citations within the text.

```mermaid
sequenceDiagram
participant User as "User"
participant ContractAgent as "Contract Agent"
participant RAGService as "HybridRAGService"
participant CitationEngine as "Citation Engine"
User->>ContractAgent : Submit query
ContractAgent->>RAGService : Retrieve documents
RAGService-->>ContractAgent : Return results
ContractAgent->>CitationEngine : Extract citations
CitationEngine->>CitationEngine : Extract clause numbers
CitationEngine->>CitationEngine : Extract page numbers
CitationEngine->>CitationEngine : Extract sections
CitationEngine-->>ContractAgent : Return formatted citations
ContractAgent-->>User : Display answer with citations
```

**Diagram sources**
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L92-L127)
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L129-L177)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py#L134-L217)

**Section sources**
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L66-L251)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py#L134-L217)

## Citation Formatting and Legal Standards
The Citation Engine provides comprehensive formatting capabilities to ensure citations meet legal standards. The engine supports multiple formatting styles, including plain text and Markdown, allowing for flexible presentation in different contexts. The formatted citations include the document title, clause number, page number, section, and a content snippet, presented in a standardized format. The engine uses a hierarchical approach to citation formatting, prioritizing the most relevant information and ensuring consistency across all citations. The formatting process involves constructing a citation string that combines the extracted information in a readable and legally compliant manner. The engine also supports customization of citation formatting through configuration options, allowing for adaptation to different document types and legal requirements.

```mermaid
flowchart TD
Start([Start Formatting]) --> ExtractInfo["Extract citation information"]
ExtractInfo --> FormatParts["Format individual parts"]
FormatParts --> CombineParts["Combine parts into citation string"]
CombineParts --> AddSnippet["Add content snippet"]
AddSnippet --> ReturnResult["Return formatted citation"]
```

**Diagram sources**
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L221-L251)
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L253-L267)
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L269-L309)

**Section sources**
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L221-L309)

## Citation Integrity Verification
The integrity of citations is verified using the ultra_citation_auditor.py component, which performs comprehensive citation auditing. The auditor extracts citations from the generated answer and verifies them against the provided sources using fuzzy matching and pattern recognition. The verification process includes checking the accuracy, completeness, and style compliance of citations. The auditor assigns a validity score to each citation based on its similarity to the source material and adherence to citation standards. The system also detects potential plagiarism by comparing the generated answer to the source documents. The verification results include recommendations for improving citation accuracy and completeness, as well as automated corrections for invalid citations. This multi-layered verification process ensures that all citations are accurate, complete, and compliant with legal standards.

```mermaid
classDiagram
class CitationType {
+str EXPLICIT
+str IMPLICIT
+str LEGAL_ARTICLE
+str CASE_REFERENCE
+str STATUTE
}
class CitationStyle {
+str PERSIAN_LEGAL
+str BLUEBOOK
+str APA
}
class Citation {
+str text
+CitationType citation_type
+int start
+int end
+Optional[str] source_reference
+Optional[str] article_number
+Optional[str] law_name
+Optional[str] case_number
+bool is_valid
+float confidence
+Optional[str] matched_source
+float similarity_score
+float completeness_score
+bool style_compliance
+str extraction_method
}
class UltraCitationAuditResult {
+bool is_valid
+float overall_score
+int total_citations
+int valid_citations
+int invalid_citations
+int missing_citations
+List[Citation] citations
+List[Dict] invalid_citation_details
+float accuracy_score
+float completeness_score
+float style_compliance_score
+List[str] recommendations
+Dict[str, str] corrections
+float processing_time_ms
}
class CitationExtractor {
+Dict[str, List[str]] patterns
+extract_citations(text : str) List[Citation]
+_build_patterns() Dict[str, List[str]]
+_extract_explicit_citations(text : str) List[Citation]
+_extract_legal_articles(text : str) List[Citation]
+_extract_case_references(text : str) List[Citation]
+_extract_implicit_citations(text : str) List[Citation]
+_remove_duplicates(citations : List[Citation]) List[Citation]
}
class CitationVerifier {
+float fuzzy_threshold
+verify_citations(citations : List[Citation], sources : List[str]) List[Citation]
+_extract_citation_text(text : str) str
+_fuzzy_match(text1 : str, text2 : str) float
+_compute_completeness(citation : Citation) float
}
class PlagiarismDetector {
+float threshold
+detect_plagiarism(text : str, sources : List[str], window_size : int) PlagiarismResult
+_compute_similarity(text1 : str, text2 : str) float
}
class CitationStyleValidator {
+CitationStyle style
+validate_style(citation : Citation) bool
}
class UltraCitationAuditor {
+float min_accuracy
+float fuzzy_threshold
+CitationStyle citation_style
+bool enable_plagiarism_detection
+CitationExtractor extractor
+CitationVerifier verifier
+CitationStyleValidator style_validator
+Optional[PlagiarismDetector] plagiarism_detector
+Dict[str, int] stats
+audit(answer : str, sources : List[str], metadata : Optional[List[Dict]]) UltraCitationAuditResult
+_generate_recommendations(citations : List[Citation], accuracy : float, completeness : float, style_compliance : float) List[str]
+_generate_corrections(citations : List[Citation]) Dict[str, str]
+get_statistics() Dict
}
CitationExtractor --> Citation : "creates"
CitationVerifier --> Citation : "updates"
PlagiarismDetector --> PlagiarismResult : "creates"
CitationStyleValidator --> Citation : "validates"
UltraCitationAuditor --> CitationExtractor : "uses"
UltraCitationAuditor --> CitationVerifier : "uses"
UltraCitationAuditor --> CitationStyleValidator : "uses"
UltraCitationAuditor --> PlagiarismDetector : "uses"
UltraCitationAuditor --> UltraCitationAuditResult : "creates"
```

**Diagram sources**
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py#L32-L65)
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py#L48-L65)
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py#L68-L84)
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py#L100-L213)
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py#L220-L252)
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py#L283-L315)
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py#L330-L344)
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py#L351-L474)

**Section sources**
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py#L1-L569)

## Evidence Enrichment Integration
The evidence_enrichment.py component enhances citations by adding contextual metadata and computing various scores to assess the quality and relevance of evidence. The enrichment process involves normalizing text, extracting entities such as articles, clauses, and judgments, and inferring the evidence type based on content analysis. The system computes authority scores based on the evidence type, with higher scores assigned to more authoritative sources such as laws and unification rulings. Recency scores are calculated based on the publication year of the evidence, with more recent documents receiving higher scores. The system also detects potential conflicts, such as waiver clauses, and assigns a conflict risk score. The overall weight of evidence is computed as a weighted combination of relevance, authority, and recency scores, providing a comprehensive assessment of evidence quality.

```mermaid
classDiagram
class Entity {
+str entity_type
+str text
+int start
+int end
+Dict[str, str] identity
}
class EnrichedEvidence {
+str doc_id
+str chunk_hash
+str locator
+str text
+str normalized_text
+List[Entity] entities
+str evidence_type
+float authority_score
+float relevance_score
+float semantic_score
+float recency_score
+float conflict_risk
+float overall_weight
+Dict[str, Any] metadata
}
class evidence_enrichment {
+Tuple[("رأی", "رای"), ("آيين", "آیین"), ...] _SYNONYMS
+str _DIGIT_MAP
+str _ARABIC_DIGIT_MAP
+re.Pattern _ARTICLE_RE
+re.Pattern _CLAUSE_RE
+re.Pattern _UNIFICATION_RE
+re.Pattern _CIRCULAR_RE
+re.Pattern _JUDGMENT_RE
+re.Pattern _DATE_RE
+re.Pattern _YEAR_RE
+normalize_text(text : str) str
+_extract_entities(text : str) List[Entity]
+_is_year_valid(year : str) bool
+_normalize_year(year : int) int
+_compute_recency(entities : List[Entity]) float
+_infer_evidence_type(normalized_text : str) str
+_authority_score(evidence_type : str) float
+_detect_conflict(normalized_text : str) float
+_clamp(value : float) float
+enrich_evidence(text : str, doc_id : str, relevance_score : float, semantic_score : float, metadata : Optional[Dict[str, Any]]) EnrichedEvidence
}
evidence_enrichment --> Entity : "creates"
evidence_enrichment --> EnrichedEvidence : "creates"
```

**Diagram sources**
- [evidence_enrichment.py](file://mahoun/rag/evidence_enrichment.py#L41-L47)
- [evidence_enrichment.py](file://mahoun/rag/evidence_enrichment.py#L50-L65)
- [evidence_enrichment.py](file://mahoun/rag/evidence_enrichment.py#L68-L249)

**Section sources**
- [evidence_enrichment.py](file://mahoun/rag/evidence_enrichment.py#L1-L250)

## Citation Generation in Legal Q&A
The contract_agent.py demonstrates the application of the Citation and Provenance Engine in legal Q&A scenarios. The UltraContractAgent processes user queries by retrieving relevant documents, generating answers with chain-of-thought reasoning, and including citations in the response. The agent uses the HybridRAGService for document retrieval and the CitationEngine for citation extraction and formatting. The generated responses include the answer, confidence score, verification status, reasoning chain, and citations. The agent supports different reasoning modes, including simple answers and chain-of-thought reasoning, automatically selecting the appropriate mode based on the complexity of the query. The system also performs NLI verification to ensure the answer is supported by the retrieved evidence. This integration enables the agent to provide accurate, well-supported answers to complex legal questions.

```mermaid
sequenceDiagram
participant User as "User"
participant ContractAgent as "Contract Agent"
participant RAGService as "HybridRAGService"
participant ReasoningService as "Reasoning Service"
participant CitationEngine as "Citation Engine"
participant NLIVerifier as "NLI Verifier"
User->>ContractAgent : Submit legal query
ContractAgent->>RAGService : Retrieve documents
RAGService-->>ContractAgent : Return results
ContractAgent->>ReasoningService : Generate answer
ReasoningService-->>ContractAgent : Return answer
ContractAgent->>NLIVerifier : Verify answer
NLIVerifier-->>ContractAgent : Return verification result
ContractAgent->>CitationEngine : Extract citations
CitationEngine-->>ContractAgent : Return citations
ContractAgent-->>User : Display answer with citations and verification status
```

**Diagram sources**
- [contract_agent.py](file://mahoun/agents/contract_agent.py#L262-L497)
- [contract_agent.py](file://mahoun/agents/contract_agent.py#L378-L389)
- [contract_agent.py](file://mahoun/agents/contract_agent.py#L396-L411)
- [contract_agent.py](file://mahoun/agents/contract_agent.py#L413-L424)
- [contract_agent.py](file://mahoun/agents/contract_agent.py#L426-L427)

**Section sources**
- [contract_agent.py](file://mahoun/agents/contract_agent.py#L1-L1599)

## Citation Accuracy and Completeness
The ultra_evaluation_system.py provides a comprehensive framework for evaluating citation accuracy and completeness. The system includes metrics for assessing retrieval quality, generation quality, and end-to-end performance. The evaluation engine computes scores for recall, precision, F1, MAP, MRR, and NDCG to assess retrieval effectiveness. For generation quality, the system uses metrics such as BLEU, ROUGE, METEOR, BERTSCORE, and BLEURT. The framework also includes semantic metrics like semantic similarity, answer relevance, faithfulness, and context relevance. The citation accuracy metric specifically evaluates the correctness and completeness of citations, identifying hallucinations and unsupported claims. The system performs statistical analysis of evaluation results, providing confidence intervals and significance testing. This comprehensive evaluation framework enables continuous improvement of the citation system through data-driven insights.

```mermaid
classDiagram
class MetricType {
+str RECALL
+str PRECISION
+str F1
+str MAP
+str MRR
+str NDCG
+str HIT_RATE
+str BLEU
+str ROUGE
+str METEOR
+str BERTSCORE
+str BLEURT
+str SEMANTIC_SIMILARITY
+str ANSWER_RELEVANCE
+str FAITHFULNESS
+str CONTEXT_RELEVANCE
+str ANSWER_CORRECTNESS
+str ANSWER_COMPLETENESS
+str HALLUCINATION_RATE
+str CITATION_ACCURACY
+str LATENCY
+str THROUGHPUT
+str COST
+str COHERENCE
+str FLUENCY
+str CONSISTENCY
+str DEMOGRAPHIC_PARITY
+str EQUAL_OPPORTUNITY
+str BIAS_SCORE
}
class EvaluationMode {
+str OFFLINE
+str ONLINE
+str AB_TEST
+str ADVERSARIAL
+str HUMAN
}
class EvaluationSample {
+str id
+str query
+Optional[str] ground_truth
+List[Dict[str, Any]] retrieved_docs
+Optional[str] generated_answer
+Optional[str] reference_answer
+Dict[str, Any] metadata
+List[str] relevant_doc_ids
+Optional[float] retrieval_time_ms
+Optional[float] generation_time_ms
+Optional[float] total_time_ms
}
class EvaluationResult {
+str sample_id
+Dict[str, float] metrics
+bool passed
+List[str] errors
+List[str] warnings
+Optional[Dict[str, Any]] retrieval_results
+Optional[Dict[str, Any]] generation_results
+Dict[str, str] explanations
}
class BenchmarkReport {
+str name
+str timestamp
+Dict[str, float] metrics
+List[EvaluationResult] sample_results
+Dict[str, Tuple[float, float]] confidence_intervals
+Dict[str, Dict[str, Any]] statistical_tests
+int total_samples
+int passed_samples
+int failed_samples
+float total_cost
+float cost_per_query
+List[str] recommendations
}
class MetricCalculator {
+calculate(sample : EvaluationSample) float
+aggregate(scores : List[float]) float
}
class RecallCalculator {
+int k
+calculate(sample : EvaluationSample) float
+aggregate(scores : List[float]) float
}
class PrecisionCalculator {
+int k
+calculate(sample : EvaluationSample) float
+aggregate(scores : List[float]) float
}
class NDCGCalculator {
+int k
+calculate(sample : EvaluationSample) float
+aggregate(scores : List[float]) float
}
class MRRCalculator {
+calculate(sample : EvaluationSample) float
+aggregate(scores : List[float]) float
}
class SemanticSimilarityCalculator {
+str model_name
+calculate(sample : EvaluationSample) float
+aggregate(scores : List[float]) float
}
class FaithfulnessCalculator {
+bool use_llm
+calculate(sample : EvaluationSample) float
+aggregate(scores : List[float]) float
}
class HallucinationDetector {
+calculate(sample : EvaluationSample) float
+aggregate(scores : List[float]) float
}
class EvaluationEngine {
+List[MetricType] metrics
+EvaluationMode mode
+Dict[MetricType, MetricCalculator] calculators
+List[EvaluationResult] results
+_init_calculators() void
+evaluate_sample(sample : EvaluationSample) EvaluationResult
+evaluate_batch(samples : List[EvaluationSample], show_progress : bool) BenchmarkReport
+_generate_report(results : List[EvaluationResult]) BenchmarkReport
+_generate_recommendations(report : BenchmarkReport) List[str]
+compare_systems(system_a_results : List[EvaluationResult], system_b_results : List[EvaluationResult], metric : MetricType) Dict[str, Any]
+_interpret_effect_size(cohens_d : float) str
}
class ABTestFramework {
+str variant_a_name
+str variant_b_name
+List[EvaluationResult] variant_a_results
+List[EvaluationResult] variant_b_results
+add_result(result : EvaluationResult, variant : str) void
+analyze(metrics : List[MetricType]) Dict[str, Any]
}
MetricCalculator <|-- RecallCalculator
MetricCalculator <|-- PrecisionCalculator
MetricCalculator <|-- NDCGCalculator
MetricCalculator <|-- MRRCalculator
MetricCalculator <|-- SemanticSimilarityCalculator
MetricCalculator <|-- FaithfulnessCalculator
MetricCalculator <|-- HallucinationDetector
EvaluationEngine --> MetricCalculator : "uses"
EvaluationEngine --> BenchmarkReport : "creates"
ABTestFramework --> EvaluationEngine : "uses"
```

**Diagram sources**
- [ultra_evaluation_system.py](file://mahoun/rag/ultra_evaluation_system.py#L39-L83)
- [ultra_evaluation_system.py](file://mahoun/rag/ultra_evaluation_system.py#L85-L92)
- [ultra_evaluation_system.py](file://mahoun/rag/ultra_evaluation_system.py#L98-L115)
- [ultra_evaluation_system.py](file://mahoun/rag/ultra_evaluation_system.py#L117-L131)
- [ultra_evaluation_system.py](file://mahoun/rag/ultra_evaluation_system.py#L133-L159)
- [ultra_evaluation_system.py](file://mahoun/rag/ultra_evaluation_system.py#L165-L362)
- [ultra_evaluation_system.py](file://mahoun/rag/ultra_evaluation_system.py#L368-L586)
- [ultra_evaluation_system.py](file://mahoun/rag/ultra_evaluation_system.py#L604-L661)

**Section sources**
- [ultra_evaluation_system.py](file://mahoun/rag/ultra_evaluation_system.py#L1-L721)

## Configuration and Formatting Options
The Citation and Provenance Engine provides extensive configuration options for citation verbosity and formatting styles. The system supports different document types through configurable citation styles, including Persian legal, Bluebook, and APA formats. The verbosity of citations can be adjusted through configuration parameters, allowing for concise or detailed citation presentation. The engine supports multiple output formats, including plain text and Markdown, with customizable formatting options for each format. The configuration also includes settings for citation extraction patterns, relevance score thresholds, and citation validation rules. These configuration options enable the system to adapt to different use cases and user preferences, ensuring that citations are presented in the most appropriate format for the context.

**Section sources**
- [citation_engine.py](file://mahoun/rag/citation_engine.py#L66-L90)
- [ultra_citation_auditor.py](file://mahoun/guardrails/ultra_citation_auditor.py#L333-L344)

## Conclusion
The Citation and Provenance Engine represents a comprehensive solution for verifiable source attribution in the MAHOUN platform. By integrating advanced retrieval, citation extraction, integrity verification, and evidence enrichment components, the system ensures that all generated responses are backed by accurate, complete, and legally compliant citations. The engine's modular architecture allows for flexible configuration and adaptation to different document types and legal standards. The integration with the contract_agent.py demonstrates the system's effectiveness in legal Q&A scenarios, providing users with well-supported answers to complex legal questions. The comprehensive evaluation framework enables continuous improvement of the citation system through data-driven insights. Overall, the Citation and Provenance Engine establishes a robust foundation for trustworthy and reliable information retrieval and generation in legal and contractual contexts.