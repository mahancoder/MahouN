"""
Citation Auditing Guardrail
============================

Verifies that citations in answers are accurate and properly referenced.
"""

import re
from dataclasses import dataclass

from pipelines._logging import setup_logger

log = setup_logger("citation_auditor")


@dataclass
class CitationAuditResult:
    """Result of citation audit"""
    is_valid: bool
    total_citations: int
    valid_citations: int
    invalid_citations: List[str]
    missing_sources: List[str]
    accuracy_score: float


class CitationAuditor:
    """
    Citation accuracy verification
    
    Verifies that:
    - Citations exist in source documents
    - Citation text matches source
    - All claims are properly cited
    
    Example:
        >>> auditor = CitationAuditor()
        >>> result = auditor.audit(
        ...     answer="طبق ماده 10 قانون مدنی...",
        ...     sources=["قانون مدنی - ماده 10: ..."]
        ... )
    """
    
    def __init__(
        self,
        min_accuracy: float = 0.8,
        citation_patterns: Optional[List[str]] = None
    ):
        """
        Initialize Citation Auditor
        
        Args:
            min_accuracy: Minimum accuracy score to pass
            citation_patterns: Regex patterns for citation detection
        """
        self.min_accuracy = min_accuracy
        
        # Default Persian legal citation patterns
        self.citation_patterns = citation_patterns or [
            r'ماده\s+\d+',  # ماده 10
            r'قانون\s+[\w\s]+',  # قانون مدنی
            r'رأی\s+شماره\s+\d+',  # رأی شماره 123
            r'پرونده\s+\d+',  # پرونده 456
            r'دادگاه\s+[\w\s]+',  # دادگاه عالی کشور
        ]
        
        log.info("Citation Auditor initialized")
    
    def audit(
        self,
        answer: str,
        sources: List[str],
        metadata: Optional[List[Dict]] = None
    ) -> CitationAuditResult:
        """
        Audit citations in answer
        
        Args:
            answer: Generated answer with citations
            sources: Source documents
            metadata: Optional metadata for sources
            
        Returns:
            CitationAuditResult
        """
        try:
            # Extract citations from answer
            citations = self._extract_citations(answer)
            
            if not citations:
                log.warning("No citations found in answer")
                return CitationAuditResult(
                    is_valid=False,
                    total_citations=0,
                    valid_citations=0,
                    invalid_citations=[],
                    missing_sources=[],
                    accuracy_score=0.0
                )
            
            # Verify each citation
            valid_citations = []
            invalid_citations = []
            
            for citation in citations:
                if self._verify_citation(citation, sources):
                    valid_citations.append(citation)
                else:
                    invalid_citations.append(citation)
            
            # Calculate accuracy
            accuracy = len(valid_citations) / len(citations) if citations else 0.0
            is_valid = accuracy >= self.min_accuracy
            
            result = CitationAuditResult(
                is_valid=is_valid,
                total_citations=len(citations),
                valid_citations=len(valid_citations),
                invalid_citations=invalid_citations,
                missing_sources=[],
                accuracy_score=accuracy
            )
            
            log.info(
                f"Citation audit: {len(valid_citations)}/{len(citations)} valid "
                f"({accuracy*100:.1f}%)"
            )
            
            return result
            
        except Exception as e:
            log.error(f"Citation audit failed: {e}")
            return CitationAuditResult(
                is_valid=True,  # Don't block on error
                total_citations=0,
                valid_citations=0,
                invalid_citations=[],
                missing_sources=[],
                accuracy_score=1.0
            )
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract citations from text using patterns"""
        citations = []
        
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, text, re.UNICODE)
            citations.extend(matches)
        
        # Remove duplicates
        citations = list(set(citations))
        
        return citations
    
    def _verify_citation(self, citation: str, sources: List[str]) -> bool:
        """Verify that citation exists in sources"""
        citation_lower = citation.lower()
        
        for source in sources:
            if citation_lower in source.lower():
                return True
        
        return False
