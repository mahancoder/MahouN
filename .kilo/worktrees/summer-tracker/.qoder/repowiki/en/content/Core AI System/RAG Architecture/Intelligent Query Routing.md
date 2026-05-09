# Intelligent Query Routing

<cite>
**Referenced Files in This Document**   
- [query_router.py](file://mahoun/rag/query_router.py)
- [test_llm_router_properties.py](file://tests/test_llm_router_properties.py)
- [ultra_bandit_system.py](file://mahoun/self_improve/ultra_bandit_system.py)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py)
- [router.py](file://mahoun/core/llm/router.py)
- [runtime_config.py](file://mahoun/core/runtime_config.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Query Classification System](#query-classification-system)
3. [Routing Strategy and RAG Mode Selection](#routing-strategy-and-rag-mode-selection)
4. [Confidence Scoring and Fallback Mechanism](#confidence-scoring-and-fallback-mechanism)
5. [LLM Router Integration and Dynamic Model Selection](#llm-router-integration-and-dynamic-model-selection)
6. [Adaptive Learning with Ultra Bandit System](#adaptive-learning-with-ultra-bandit-system)
7. [Configuration Options and Custom Routing Rules](#configuration-options-and-custom-routing-rules)
8. [Performance Monitoring and Optimization](#performance-monitoring-and-optimization)
9. [Common Issues and Solutions](#common-issues-and-solutions)

## Introduction
The Intelligent Query Routing system in MAHOUN is designed to classify user queries and route them to the most appropriate retrieval strategy based on query intent. This system leverages pattern matching, keyword detection, and confidence scoring to determine query types such as contract-related, delay analysis, legal inquiry, or technical inquiry. The routing mechanism integrates with the LLM router for dynamic model selection and employs an adaptive learning system to continuously improve classification accuracy and routing efficiency. This document provides a comprehensive overview of the query routing architecture, implementation details, and optimization strategies.

## Query Classification System

The QueryClassification system identifies query intent through pattern matching and keyword detection. It supports multiple query types including contract, delay analysis, legal inquiry, and technical inquiry. The classification process involves analyzing the input query against predefined patterns and keywords associated with each query type. The system computes scores for each query type based on pattern matches and normalizes these scores to generate a confidence level between 0 and 1.

```mermaid
classDiagram
class QueryType {
+CONTRACT : str
+DELAY_ANALYSIS : str
+LEGAL_INQUIRY : str
+TECHNICAL_INQUIRY : str
+GENERAL : str
}
class QueryClassification {
+query : str
+query_type : QueryType
+confidence : float
+keywords_found : List[str]
+metadata : Dict[str, Any]
}
class QueryRouter {
+patterns : Dict[QueryType, List[Dict[str, Any]]]
+stats : Dict[str, Any]
+_build_patterns() : Dict[QueryType, List[Dict[str, Any]]]
+classify(query : str) : QueryClassification
+route(query : str, top_k : int, rag_mode : Optional[str]) : RoutedQueryResult
+_determine_rag_mode(query_type : QueryType) : str
+get_stats() : Dict[str, Any]
}
QueryRouter --> QueryClassification : "returns"
QueryRouter --> QueryType : "uses"
```

**Diagram sources**
- [query_router.py](file://mahoun/rag/query_router.py#L25-L32)
- [query_router.py](file://mahoun/rag/query_router.py#L34-L42)
- [query_router.py](file://mahoun/rag/query_router.py#L54-L323)

**Section sources**
- [query_router.py](file://mahoun/rag/query_router.py#L25-L228)

## Routing Strategy and RAG Mode Selection

The routing strategy determines the appropriate RAG mode based on the classified query type. Contract and legal inquiries are routed to hybrid_graph_first mode to leverage graph relationships, while delay analysis and technical inquiries use text_only mode for structured text retrieval. The system automatically selects the optimal retrieval strategy through the _determine_rag_mode method, which maps query types to specific RAG modes. The HybridRAGService supports multiple operational modes including graph_only, text_only, and hybrid_graph_first, with automatic fallback to text_only if graph retrieval is unavailable.

```mermaid
flowchart TD
A[User Query] --> B{Query Type}
B --> |CONTRACT| C[hybrid_graph_first]
B --> |DELAY_ANALYSIS| D[text_only]
B --> |LEGAL_INQUIRY| C[hybrid_graph_first]
B --> |TECHNICAL_INQUIRY| D[text_only]
B --> |GENERAL| E[auto]
C --> F[Graph + Text Fusion]
D --> G[BM25 + Dense Retrieval]
E --> H[Runtime Configuration]
H --> |graph_enabled| C
H --> |!graph_enabled| D
```

**Diagram sources**
- [query_router.py](file://mahoun/rag/query_router.py#L285-L313)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py#L29-L34)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py#L127-L132)

**Section sources**
- [query_router.py](file://mahoun/rag/query_router.py#L285-L313)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py#L127-L132)

## Confidence Scoring and Fallback Mechanism

The confidence scoring mechanism normalizes pattern match scores to produce a confidence level between 0 and 1. When the maximum score is zero, indicating no pattern matches, the system defaults to GENERAL query type with 0.5 confidence. The fallback routing logic ensures resilience by automatically switching to alternative retrieval strategies when primary methods fail. If graph-only retrieval is disabled or fails, the system falls back to text_only mode. The HybridRAGService implements error handling that catches exceptions during retrieval and automatically falls back to text_only mode, ensuring continuous service availability.

```mermaid
sequenceDiagram
participant User
participant QueryRouter
participant HybridRAGService
participant GraphRetriever
participant TextRetriever
User->>QueryRouter : Submit Query
QueryRouter->>QueryRouter : Classify Query Type
QueryRouter->>HybridRAGService : Route with Mode
alt Graph Retrieval Enabled
HybridRAGService->>GraphRetriever : Retrieve Graph Results
GraphRetriever-->>HybridRAGService : Return Results or Error
alt Graph Retrieval Success
HybridRAGService->>TextRetriever : Retrieve Text Results
TextRetriever-->>HybridRAGService : Return Results
HybridRAGService->>HybridRAGService : Merge and Re-rank
else Graph Retrieval Failure
HybridRAGService->>TextRetriever : Fallback to Text Retrieval
TextRetriever-->>HybridRAGService : Return Results
end
else Graph Retrieval Disabled
HybridRAGService->>TextRetriever : Direct Text Retrieval
TextRetriever-->>HybridRAGService : Return Results
end
HybridRAGService-->>QueryRouter : Return Hybrid Results
QueryRouter-->>User : Return Final Results
```

**Diagram sources**
- [query_router.py](file://mahoun/rag/query_router.py#L200-L212)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py#L159-L217)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py#L219-L376)

**Section sources**
- [query_router.py](file://mahoun/rag/query_router.py#L200-L212)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py#L159-L217)

## LLM Router Integration and Dynamic Model Selection

The LLM router integration enables dynamic model selection based on query complexity and capability requirements. The system uses a priority-based fallback chain with circuit breakers to ensure high availability. Model selection is deterministic, meaning identical inputs always produce the same output, ensuring reproducibility and auditability. The router supports multiple routing strategies including priority, round-robin, least latency, and least cost. Routing rules can be configured by capability, cost, or latency, allowing fine-grained control over model selection.

```mermaid
classDiagram
class LLMRouter {
+_models : Dict[str, ModelConfig]
+_routing_rules : Dict[str, List[RoutingRule]]
+_fallback_chain : List[str]
+_circuit_breakers : Dict[str, CircuitBreaker]
+_stats : Dict[str, ModelStats]
+select(prompt : str, capability : str, context : Dict) : str
+get_fallback(failed_model : str) : Optional[str]
+record_success(model_name : str, latency_ms : float)
+record_failure(model_name : str)
+add_routing_rule(capability : str, model_name : str)
}
class ModelConfig {
+name : str
+provider : LLMProvider
+capabilities : FrozenSet[str]
+priority : int
+cost_per_1k_input : float
+cost_per_1k_output : float
+avg_latency_ms : float
}
class RoutingRule {
+capability : str
+model_name : str
+priority : int
+conditions : Dict[str, Any]
}
class CircuitBreaker {
+model_name : str
+state : CircuitState
+failure_count : int
+success_count : int
+record_success()
+record_failure()
+is_available() : bool
}
class ModelStats {
+model_name : str
+total_requests : int
+successful_requests : int
+failed_requests : int
+total_latency_ms : float
+success_rate : float
+avg_latency_ms : float
}
LLMRouter --> ModelConfig : "contains"
LLMRouter --> RoutingRule : "contains"
LLMRouter --> CircuitBreaker : "contains"
LLMRouter --> ModelStats : "contains"
```

**Diagram sources**
- [router.py](file://mahoun/core/llm/router.py#L117-L150)
- [router.py](file://mahoun/core/llm/router.py#L171-L290)
- [router.py](file://mahoun/core/llm/router.py#L321-L800)

**Section sources**
- [router.py](file://mahoun/core/llm/router.py#L117-L150)
- [router.py](file://mahoun/core/llm/router.py#L171-L290)
- [router.py](file://mahoun/core/llm/router.py#L321-L800)

## Adaptive Learning with Ultra Bandit System

The ultra_bandit_system.py implements advanced multi-armed bandit algorithms for adaptive learning and optimization. This system supports Thompson Sampling, UCB (Upper Confidence Bound), LinUCB for contextual bandits, and Neural Thompson Sampling with ensemble networks. The UltraBanditSystem class provides a unified interface to multiple bandit algorithms, enabling exploration-exploitation trade-offs in model selection and routing decisions. The system maintains statistics on arm performance and computes cumulative regret to measure optimization effectiveness.

```mermaid
classDiagram
class UltraBanditSystem {
+n_arms : int
+context_dim : Optional[int]
+algorithm : str
+device : str
+bandit : Any
+total_pulls : int
+total_reward : float
+regret_history : List[float]
+select_arm(context : Optional[np.ndarray]) : int
+update(arm : int, reward : float, context : Optional[np.ndarray])
+get_statistics() : Dict[str, Any]
+compute_regret(optimal_reward : float) : float
}
class ThompsonSampling {
+n_arms : int
+alpha : np.ndarray
+beta : np.ndarray
+pulls : np.ndarray
+rewards : np.ndarray
+select_arm() : int
+update(arm : int, reward : float)
+get_statistics() : Dict[int, Dict[str, float]]
}
class UCB {
+n_arms : int
+c : float
+pulls : np.ndarray
+rewards : np.ndarray
+t : int
+select_arm() : int
+update(arm : int, reward : float)
+get_statistics() : Dict[int, Dict[str, float]]
}
class LinUCB {
+n_arms : int
+context_dim : int
+alpha : float
+A : List[np.ndarray]
+b : List[np.ndarray]
+pulls : np.ndarray
+select_arm(context : np.ndarray) : int
+update(arm : int, context : np.ndarray, reward : float)
+get_statistics() : Dict[int, Dict[str, float]]
}
class NeuralThompsonSampling {
+context_dim : int
+n_arms : int
+n_ensemble : int
+device : str
+ensemble : List[NeuralContextualBandit]
+optimizers : List[torch.optim.Optimizer]
+pulls : np.ndarray
+buffer : List[Tuple]
+select_arm(context : np.ndarray) : int
+update(context : np.ndarray, arm : int, reward : float)
+_train_ensemble()
+get_statistics() : Dict[int, Dict[str, float]]
}
UltraBanditSystem --> ThompsonSampling : "uses"
UltraBanditSystem --> UCB : "uses"
UltraBanditSystem --> LinUCB : "uses"
UltraBanditSystem --> NeuralThompsonSampling : "uses"
```

**Diagram sources**
- [ultra_bandit_system.py](file://mahoun/self_improve/ultra_bandit_system.py#L40-L75)
- [ultra_bandit_system.py](file://mahoun/self_improve/ultra_bandit_system.py#L78-L117)
- [ultra_bandit_system.py](file://mahoun/self_improve/ultra_bandit_system.py#L124-L167)
- [ultra_bandit_system.py](file://mahoun/self_improve/ultra_bandit_system.py#L206-L291)
- [ultra_bandit_system.py](file://mahoun/self_improve/ultra_bandit_system.py#L346-L416)

**Section sources**
- [ultra_bandit_system.py](file://mahoun/self_improve/ultra_bandit_system.py#L40-L416)

## Configuration Options and Custom Routing Rules

The system provides extensive configuration options for custom routing rules and performance monitoring. Runtime settings are controlled through environment variables and YAML configuration files, allowing mode-specific configurations for desktop_minimal and server_full deployments. The runtime_config.py module manages settings for graph operations, LoRA training, LLM backends, and embedding models. Custom routing rules can be defined by capability, with priority-based rule evaluation ensuring deterministic behavior. The system supports enterprise graph mode with hybrid retrieval and local full backends for maximum performance.

```mermaid
flowchart TD
A[Environment Variables] --> B[Runtime Settings]
C[YAML Configuration] --> B
B --> D{Mode}
D --> |desktop_minimal| E[Graph Disabled]
D --> |desktop_minimal| F[LLM: OpenAI API]
D --> |desktop_minimal| G[Embeddings: bge-small]
D --> |server_full| H[Graph Enabled]
D --> |server_full| I[LLM: Local GPU]
D --> |server_full| J[Embeddings: bge-default]
K[Custom Routing Rules] --> L[Capability-Based Routing]
M[Priority Settings] --> N[Model Selection]
O[Circuit Breakers] --> P[Failover Management]
Q[Performance Monitoring] --> R[SLA Compliance]
S[Adaptive Learning] --> T[Continuous Optimization]
style E fill:#f9f,stroke:#333
style F fill:#f9f,stroke:#333
style G fill:#f9f,stroke:#333
style H fill:#bbf,stroke:#333
style I fill:#bbf,stroke:#333
style J fill:#bbf,stroke:#333
```

**Diagram sources**
- [runtime_config.py](file://mahoun/core/runtime_config.py#L32-L64)
- [runtime_config.py](file://mahoun/core/runtime_config.py#L149-L238)
- [router.py](file://mahoun/core/llm/router.py#L469-L503)

**Section sources**
- [runtime_config.py](file://mahoun/core/runtime_config.py#L32-L278)
- [router.py](file://mahoun/core/llm/router.py#L469-L503)

## Performance Monitoring and Optimization

The system includes comprehensive performance monitoring through the UltraPerformanceMonitor class, which collects metrics on latency, throughput, error rates, and resource utilization. The monitoring system implements ML-based anomaly detection using statistical methods and isolation forests to identify performance issues. SLA monitoring tracks compliance with performance targets, while the performance profiler identifies bottlenecks in critical operations. The system generates detailed performance reports with recommendations for optimization, including cache hit rate improvements and latency reduction strategies.

```mermaid
classDiagram
class UltraPerformanceMonitor {
+aggregator : MetricAggregator
+anomaly_detector : AnomalyDetector
+alert_manager : AlertManager
+sla_monitor : SLAMonitor
+profiler : PerformanceProfiler
+stats : Dict[str, int]
+record_metric(name : str, value : float, component : str)
+record_latency(component : str, operation : str, latency_ms : float)
+set_sla_target(metric : str, target_value : float)
+generate_report(component : str) : PerformanceReport
+get_bottlenecks(component : str) : List[Dict]
}
class MetricAggregator {
+window_size : int
+metrics : Dict[str, deque]
+add(metric : PerformanceMetric)
+get_stats(component : str, metric_name : str) : Dict[str, float]
}
class AnomalyDetector {
+contamination : float
+models : Dict[str, Any]
+detect(component : str, metric_name : str, values : List[float]) : List[int]
+_detect_statistical(values : List[float]) : List[int]
}
class AlertManager {
+dedup_window : int
+alerts : List[Alert]
+create_alert(metric : str, severity : AlertSeverity, value : float) : Optional[Alert]
+register_callback(callback : Callable[[Alert], None])
}
class SLAMonitor {
+sla_targets : Dict[str, Dict]
+violations : List[Dict]
+set_target(metric : str, target_value : float)
+check_compliance(metric : str, value : float) : Tuple[bool, Optional[str]]
}
class PerformanceProfiler {
+profiles : Dict[str, List[Dict]]
+profile(component : str, operation : str, duration : float)
+get_bottlenecks(component : str) : List[Dict]
}
UltraPerformanceMonitor --> MetricAggregator : "contains"
UltraPerformanceMonitor --> AnomalyDetector : "contains"
UltraPerformanceMonitor --> AlertManager : "contains"
UltraPerformanceMonitor --> SLAMonitor : "contains"
UltraPerformanceMonitor --> PerformanceProfiler : "contains"
```

**Diagram sources**
- [ultra_performance_monitoring.py](file://mahoun/self_improve/ultra_performance_monitoring.py#L121-L162)
- [ultra_performance_monitoring.py](file://mahoun/self_improve/ultra_performance_monitoring.py#L164-L232)
- [ultra_performance_monitoring.py](file://mahoun/self_improve/ultra_performance_monitoring.py#L235-L304)
- [ultra_performance_monitoring.py](file://mahoun/self_improve/ultra_performance_monitoring.py#L306-L372)
- [ultra_performance_monitoring.py](file://mahoun/self_improve/ultra_performance_monitoring.py#L374-L423)
- [ultra_performance_monitoring.py](file://mahoun/self_improve/ultra_performance_monitoring.py#L425-L745)

**Section sources**
- [ultra_performance_monitoring.py](file://mahoun/self_improve/ultra_performance_monitoring.py#L121-L745)

## Common Issues and Solutions

Common issues in the query routing system include misclassification of queries, routing latency, and resource constraints in desktop_minimal mode. Misclassification can occur when queries contain keywords from multiple categories, leading to ambiguous pattern matches. This is addressed through confidence scoring and the default GENERAL classification for low-confidence matches. Routing latency issues are mitigated by the fallback mechanism and circuit breakers that prevent cascading failures. In desktop_minimal mode, graph operations are disabled by default to conserve resources, with automatic fallback to text-only retrieval. The adaptive learning system continuously improves classification accuracy through feedback loops and performance monitoring.

**Section sources**
- [query_router.py](file://mahoun/rag/query_router.py#L207-L212)
- [hybrid_rag_service.py](file://mahoun/rag/hybrid_rag_service.py#L159-L217)
- [runtime_config.py](file://mahoun/core/runtime_config.py#L186-L208)
- [ultra_performance_monitoring.py](file://mahoun/self_improve/ultra_performance_monitoring.py#L570-L600)