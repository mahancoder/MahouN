"""
MAHOUN Core Models
==================

Central data models used across the MAHOUN Enterprise system.
These models provide type-safe data structures for reasoning,
uncertainty estimation, and legal document processing.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# Legal Document Models
# ============================================================================

class LegalDocType(str, Enum):
    """Legal document types"""
    LAW = "law"
    VERDICT = "verdict"
    REGULATION = "regulation"
    ARTICLE = "article"
    CONTRACT = "contract"
    OPINION = "opinion"
    OTHER = "other"


class LegalDocument(BaseModel):
    """Core legal document model"""
    id: str = Field(..., description="Unique document identifier")
    text: str = Field(..., description="Full document text content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    doc_type: Optional[LegalDocType] = None
    title: Optional[str] = None
    source_file: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None


class LegalEntity(BaseModel):
    """Legal entity (person, organization, court, etc.)"""
    name: str
    entity_type: str  # person, organization, court, law
    role: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Reasoning Models
# ============================================================================

@dataclass
class ReasoningStep:
    """Single step in chain of thought reasoning"""
    step: str
    reasoning: str
    confidence: float = 0.5
    evidence: List[str] = field(default_factory=list)


@dataclass
class CausalRelation:
    """Causal relationship between facts"""
    cause: str
    effect: str
    strength: float
    explanation: str


@dataclass
class ReasoningResult:
    """Complete reasoning result"""
    question: str
    context: str
    facts: List[str]
    reasoning_chain: List[ReasoningStep]
    causal_chain: List[CausalRelation]
    primary_cause: Optional[CausalRelation]
    final_answer: str
    confidence: float
    supporting_evidence: List[str]
    evidence_strength: str
    visited_nodes: List[str] = field(default_factory=list)
    graph_edges_used: List[Tuple[str, str]] = field(default_factory=list)
    used_rule_ids: List[str] = field(default_factory=list)
    limitations: Optional[str] = None
    graph_dependency_proof: bool = False
    reasoning_depth: str = "deep"
    
    def to_trace_json(self) -> Dict[str, Any]:
        """Structured trace for auditing."""
        return {
            "final_answer": self.final_answer,
            "confidence": self.confidence,
            "visited_nodes": self.visited_nodes,
            "graph_edges_used": [list(edge) for edge in self.graph_edges_used],
            "used_rule_ids": self.used_rule_ids,
            "supporting_evidence": self.supporting_evidence,
            "causal_chain": [asdict(rel) for rel in self.causal_chain],
            "graph_dependency_proof": self.graph_dependency_proof,
            "limitations": self.limitations,
            "evidence_strength": self.evidence_strength,
            "reasoning_depth": self.reasoning_depth,
        }


# ============================================================================
# Uncertainty Models
# ============================================================================

@dataclass
class UncertaintyEstimate:
    """Uncertainty estimation result"""
    epistemic: float = 0.0  # Model uncertainty (reducible)
    aleatoric: float = 0.0  # Data uncertainty (irreducible)
    total: float = 0.0
    confidence: float = 1.0
    method: str = "ensemble"
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.total == 0.0:
            self.total = self.epistemic + self.aleatoric


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Legal Documents
    "LegalDocType",
    "LegalDocument",
    "LegalEntity",
    # Reasoning
    "ReasoningStep",
    "CausalRelation",
    "ReasoningResult",
    # Uncertainty
    "UncertaintyEstimate",
]
