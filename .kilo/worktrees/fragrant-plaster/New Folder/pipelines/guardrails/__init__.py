"""
MAHOUN Guardrails Module
========================

NLI verification and safety checks for generated content.

Components:
- NLI Verifier: Natural language inference validation
- Hallucination Detector: Factual consistency checking
- Safety Checker: Content safety validation
- Bias Detector: Bias and fairness checking

Features:
- Entailment verification
- Contradiction detection
- Factual consistency scoring
- Content filtering
- Bias mitigation
"""

__version__ = "2.0.0"

from .nli_verifier import NLIVerifier, NLIResult
from .citation_auditor import CitationAuditor, CitationAuditResult
from .hallucination_detector import HallucinationDetector, HallucinationDetectionResult

__all__ = [
    "NLIVerifier",
    "NLIResult",
    "CitationAuditor",
    "CitationAuditResult",
    "HallucinationDetector",
    "HallucinationDetectionResult"
]
