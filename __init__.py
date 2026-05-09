"""
HAJIX - MAHOUN Refactored Codebase
===================================

Safe, Clean, Non-Breaking Refactor of MAHOUN.

Modules:
    agents: Multi-agent system
    core: Core services (LLM, metrics, health)
    mahoun: MCP (Model Context Protocol) layer
    pipelines: Document ingestion and processing
    rag: Retrieval-Augmented Generation
    graph: Knowledge graph operations
    reasoning: Causal inference and chain-of-thought
    self_improve: Self-improvement system
    retrieval: Hybrid search
    orchestrator: Workflow management
"""

__version__ = "2.0.0-hajix"
__all__ = [
    "agents",
    "core", 
    "mahoun",
    "pipelines",
    "rag",
    "graph",
    "reasoning",
    "self_improve",
    "retrieval",
    "orchestrator",
]
