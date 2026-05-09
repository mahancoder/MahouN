"""
Hallucination Detection Guardrail
==================================

Detects hallucinated facts in generated answers.
"""

from dataclasses import dataclass

from pipelines.guardrails.nli_verifier import NLIVerifier
from core.models import UncertaintyEstimate

log = setup_logger("hallucination_detector")


@dataclass
class HallucinationDetectionResult:
    """Result of hallucination detection"""
    has_hallucination: bool
    hallucination_score: float  # 0-1, higher = more likely hallucinated
    confidence: float
    detected_hallucinations: List[str]
    verification_method: str


class HallucinationDetector:
    """
    Hallucination detection using multiple signals
    
    Combines:
    - NLI verification (contradiction detection)
    - Uncertainty quantification
    - Fact checking against sources
    
    Example:
        >>> detector = HallucinationDetector()
        >>> result = detector.detect(
        ...     answer="دادگاه تجدیدنظر رأی صادر کرد",
        ...     context="دادگاه عالی کشور رأی صادر کرد",
        ...     uncertainty=0.8
        ... )
    """
    
    def __init__(
        self,
        nli_verifier: Optional[NLIVerifier] = None,
        hallucination_threshold: float = 0.6,
        uncertainty_threshold: float = 0.3
    ):
        """
        Initialize Hallucination Detector
        
        Args:
            nli_verifier: NLI verifier instance (creates if None)
            hallucination_threshold: Threshold for hallucination detection
            uncertainty_threshold: High uncertainty indicates possible hallucination
        """
        self.nli_verifier = nli_verifier or NLIVerifier()
        self.hallucination_threshold = hallucination_threshold
        self.uncertainty_threshold = uncertainty_threshold
        
        log.info("Hallucination Detector initialized")
    
    def detect(
        self,
        answer: str,
        context: str,
        uncertainty: Optional[float] = None,
        sources: Optional[List[str]] = None
    ) -> HallucinationDetectionResult:
        """
        Detect hallucinations in answer
        
        Args:
            answer: Generated answer
            context: Source context
            uncertainty: Uncertainty score (0-1)
            sources: Source documents
            
        Returns:
            HallucinationDetectionResult
        """
        try:
            hallucination_signals = []
            detected_hallucinations = []
            
            # Signal 1: NLI contradiction
            nli_result = self.nli_verifier.verify(context, answer)
            
            if not nli_result.is_supported:
                hallucination_signals.append(nli_result.contradiction_score)
                log.warning(
                    f"NLI detected contradiction: "
                    f"score={nli_result.contradiction_score:.3f}"
                )
            
            # Signal 2: High uncertainty
            if uncertainty is not None and uncertainty > self.uncertainty_threshold:
                hallucination_signals.append(uncertainty)
                log.warning(f"High uncertainty detected: {uncertainty:.3f}")
            
            # Signal 3: Sentence-level verification
            supported, filtered, retention = self.nli_verifier.verify_sentences(
                context, answer
            )
            
            if filtered:
                detected_hallucinations.extend(filtered)
                hallucination_signals.append(1.0 - retention)
            
            # Compute overall hallucination score
            if hallucination_signals:
                hallucination_score = sum(hallucination_signals) / len(hallucination_signals)
            else:
                hallucination_score = 0.0
            
            has_hallucination = hallucination_score >= self.hallucination_threshold
            
            result = HallucinationDetectionResult(
                has_hallucination=has_hallucination,
                hallucination_score=hallucination_score,
                confidence=1.0 - hallucination_score,
                detected_hallucinations=detected_hallucinations,
                verification_method="nli+uncertainty+sentence"
            )
            
            if has_hallucination:
                log.warning(
                    f"Hallucination detected! Score: {hallucination_score:.3f}, "
                    f"Filtered: {len(detected_hallucinations)} sentences"
                )
            else:
                log.info(f"No hallucination detected (score: {hallucination_score:.3f})")
            
            return result
            
        except Exception as e:
            log.error(f"Hallucination detection failed: {e}")
            return HallucinationDetectionResult(
                has_hallucination=False,  # Don't block on error
                hallucination_score=0.0,
                confidence=1.0,
                detected_hallucinations=[],
                verification_method="error_fallback"
            )
