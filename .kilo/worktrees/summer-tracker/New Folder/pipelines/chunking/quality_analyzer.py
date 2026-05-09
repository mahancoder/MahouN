#!/usr/bin/env python3
"""
Chunk Quality Analyzer
=======================
Advanced quality analysis for text chunks with:
- Coherence scoring
- Completeness analysis
- Boundary quality assessment
- Entity preservation checking
- Size consistency analysis
- Readability metrics
- Comprehensive reporting
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import numpy as np

from .service import Chunk

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for chunks"""
    overall_score: float
    coherence_score: float
    completeness_score: float
    boundary_quality_score: float
    entity_preservation_score: float
    size_consistency_score: float
    readability_score: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "overall_score": self.overall_score,
            "coherence_score": self.coherence_score,
            "completeness_score": self.completeness_score,
            "boundary_quality_score": self.boundary_quality_score,
            "entity_preservation_score": self.entity_preservation_score,
            "size_consistency_score": self.size_consistency_score,
            "readability_score": self.readability_score
        }


@dataclass
class QualityIssue:
    """Represents a quality issue"""
    severity: str  # "low", "medium", "high"
    type: str
    description: str
    affected_chunks: List[int]
    recommendation: str


@dataclass
class QualityReport:
    """Comprehensive quality report"""
    metrics: QualityMetrics
    issues: List[QualityIssue]
    recommendations: List[str]
    chunk_scores: List[Dict[str, float]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metrics": self.metrics.to_dict(),
            "issues": [
                {
                    "severity": issue.severity,
                    "type": issue.type,
                    "description": issue.description,
                    "affected_chunks": issue.affected_chunks,
                    "recommendation": issue.recommendation
                }
                for issue in self.issues
            ],
            "recommendations": self.recommendations,
            "chunk_scores": self.chunk_scores
        }


class ChunkQualityAnalyzer:
    """
    Advanced Chunk Quality Analyzer
    ================================
    
    Analyzes chunk quality across multiple dimensions:
    
    **Metrics:**
    - Coherence: Semantic consistency within chunks
    - Completeness: Proper start/end boundaries
    - Boundary Quality: Clean chunk boundaries
    - Entity Preservation: Named entities not split
    - Size Consistency: Uniform chunk sizes
    - Readability: Text readability scores
    
    **Features:**
    - Multi-dimensional scoring
    - Issue detection and reporting
    - Actionable recommendations
    - Per-chunk and aggregate analysis
    
    Example:
        ```python
        analyzer = ChunkQualityAnalyzer(
            min_coherence=0.7,
            min_completeness=0.8
        )
        
        # Analyze chunks
        report = analyzer.analyze(chunks)
        
        print(f"Overall score: {report.metrics.overall_score:.2f}")
        print(f"Issues found: {len(report.issues)}")
        
        for issue in report.issues:
            print(f"- {issue.severity}: {issue.description}")
        ```
    """
    
    def __init__(
        self,
        min_coherence: float = 0.7,
        min_completeness: float = 0.8,
        min_boundary_quality: float = 0.75,
        target_size_variance: float = 0.3,
        enable_entity_detection: bool = False
    ):
        """
        Initialize quality analyzer
        
        Args:
            min_coherence: Minimum acceptable coherence score
            min_completeness: Minimum acceptable completeness score
            min_boundary_quality: Minimum acceptable boundary quality
            target_size_variance: Maximum acceptable size variance
            enable_entity_detection: Enable entity detection
        """
        self.min_coherence = min_coherence
        self.min_completeness = min_completeness
        self.min_boundary_quality = min_boundary_quality
        self.target_size_variance = target_size_variance
        self.enable_entity_detection = enable_entity_detection
    
    def analyze(self, chunks: List[Chunk]) -> QualityReport:
        """
        Perform comprehensive quality analysis
        
        Args:
            chunks: List of chunks to analyze
            
        Returns:
            Quality report with metrics and recommendations
        """
        if not chunks:
            return self._empty_report()
        
        # Compute individual metrics
        coherence_scores = self._compute_coherence_scores(chunks)
        completeness_scores = self._compute_completeness_scores(chunks)
        boundary_scores = self._compute_boundary_quality_scores(chunks)
        entity_scores = self._compute_entity_preservation_scores(chunks)
        size_consistency = self._compute_size_consistency(chunks)
        readability_scores = self._compute_readability_scores(chunks)
        
        # Aggregate metrics
        metrics = QualityMetrics(
            overall_score=self._compute_overall_score(
                coherence_scores,
                completeness_scores,
                boundary_scores,
                entity_scores,
                size_consistency,
                readability_scores
            ),
            coherence_score=np.mean(coherence_scores),
            completeness_score=np.mean(completeness_scores),
            boundary_quality_score=np.mean(boundary_scores),
            entity_preservation_score=np.mean(entity_scores),
            size_consistency_score=size_consistency,
            readability_score=np.mean(readability_scores)
        )
        
        # Detect issues
        issues = self._detect_issues(
            chunks,
            coherence_scores,
            completeness_scores,
            boundary_scores,
            entity_scores,
            size_consistency
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, issues)
        
        # Per-chunk scores
        chunk_scores = [
            {
                "chunk_index": i,
                "coherence": coherence_scores[i],
                "completeness": completeness_scores[i],
                "boundary_quality": boundary_scores[i],
                "entity_preservation": entity_scores[i],
                "readability": readability_scores[i]
            }
            for i in range(len(chunks))
        ]
        
        return QualityReport(
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            chunk_scores=chunk_scores
        )
    
    def _compute_coherence_scores(self, chunks: List[Chunk]) -> List[float]:
        """
        Compute coherence scores for chunks
        
        Coherence measures semantic consistency within a chunk
        """
        scores = []
        
        for chunk in chunks:
            # Simple coherence based on sentence connectivity
            sentences = re.split(r'[.!?]+', chunk.text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) <= 1:
                scores.append(1.0)
                continue
            
            # Check for transition words and pronouns (simple heuristic)
            transition_words = {'however', 'therefore', 'moreover', 'furthermore', 'additionally'}
            pronouns = {'he', 'she', 'it', 'they', 'this', 'that', 'these', 'those'}
            
            coherence_indicators = 0
            for sentence in sentences[1:]:
                words = set(sentence.lower().split())
                if words & (transition_words | pronouns):
                    coherence_indicators += 1
            
            coherence = coherence_indicators / (len(sentences) - 1) if len(sentences) > 1 else 1.0
            # Normalize to 0.6-1.0 range (assume baseline coherence)
            coherence = 0.6 + (coherence * 0.4)
            scores.append(min(coherence, 1.0))
        
        return scores
    
    def _compute_completeness_scores(self, chunks: List[Chunk]) -> List[float]:
        """
        Compute completeness scores for chunks
        
        Completeness measures if chunks have proper start/end boundaries
        """
        scores = []
        
        for chunk in chunks:
            text = chunk.text.strip()
            if not text:
                scores.append(0.0)
                continue
            
            score = 0.0
            
            # Check start: Should start with capital letter
            if text[0].isupper():
                score += 0.5
            
            # Check end: Should end with sentence terminator
            if text[-1] in '.!?':
                score += 0.5
            
            scores.append(score)
        
        return scores
    
    def _compute_boundary_quality_scores(self, chunks: List[Chunk]) -> List[float]:
        """
        Compute boundary quality scores
        
        Boundary quality measures if chunk boundaries are at natural break points
        """
        scores = []
        
        for i, chunk in enumerate(chunks):
            text = chunk.text.strip()
            if not text:
                scores.append(0.0)
                continue
            
            score = 0.0
            
            # Check if starts at paragraph boundary
            if i == 0 or text.startswith('\n'):
                score += 0.3
            elif text[0].isupper():
                score += 0.2
            
            # Check if ends at sentence boundary
            if text[-1] in '.!?':
                score += 0.4
            
            # Check if ends at paragraph boundary
            if i == len(chunks) - 1 or text.endswith('\n'):
                score += 0.3
            
            scores.append(min(score, 1.0))
        
        return scores
    
    def _compute_entity_preservation_scores(self, chunks: List[Chunk]) -> List[float]:
        """
        Compute entity preservation scores
        
        Checks if named entities are preserved (not split across chunks)
        """
        if not self.enable_entity_detection:
            # Return perfect scores if entity detection is disabled
            return [1.0] * len(chunks)
        
        scores = []
        
        for chunk in chunks:
            # Simple entity detection using capitalization patterns
            text = chunk.text
            
            # Find potential entities (consecutive capitalized words)
            potential_entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            
            if not potential_entities:
                scores.append(1.0)
                continue
            
            # Check if entities are complete (not cut off at boundaries)
            complete_entities = 0
            for entity in potential_entities:
                # Check if entity appears complete in text
                if entity in text and not text.startswith(entity[:-1]):
                    complete_entities += 1
            
            score = complete_entities / len(potential_entities) if potential_entities else 1.0
            scores.append(score)
        
        return scores
    
    def _compute_size_consistency(self, chunks: List[Chunk]) -> float:
        """
        Compute size consistency score
        
        Measures how consistent chunk sizes are
        """
        if len(chunks) <= 1:
            return 1.0
        
        sizes = [chunk.token_count for chunk in chunks]
        mean_size = np.mean(sizes)
        std_size = np.std(sizes)
        
        # Coefficient of variation
        cv = std_size / mean_size if mean_size > 0 else 0
        
        # Convert to score (lower CV = higher score)
        # CV of 0.3 or less is considered good
        score = max(0, 1.0 - (cv / self.target_size_variance))
        
        return score
    
    def _compute_readability_scores(self, chunks: List[Chunk]) -> List[float]:
        """
        Compute readability scores using Flesch Reading Ease
        
        Higher scores indicate easier readability
        """
        scores = []
        
        for chunk in chunks:
            text = chunk.text
            
            # Count sentences, words, and syllables
            sentences = len(re.split(r'[.!?]+', text))
            words = len(text.split())
            
            if words == 0 or sentences == 0:
                scores.append(0.5)
                continue
            
            # Simple syllable count (approximation)
            syllables = sum(self._count_syllables(word) for word in text.split())
            
            # Flesch Reading Ease formula
            # Score = 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
            fre = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
            
            # Normalize to 0-1 range (FRE typically ranges from 0-100)
            normalized_score = max(0, min(1, fre / 100))
            scores.append(normalized_score)
        
        return scores
    
    def _count_syllables(self, word: str) -> int:
        """Simple syllable counter"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent 'e'
        if word.endswith('e'):
            syllable_count -= 1
        
        # Every word has at least one syllable
        return max(1, syllable_count)
    
    def _compute_overall_score(
        self,
        coherence_scores: List[float],
        completeness_scores: List[float],
        boundary_scores: List[float],
        entity_scores: List[float],
        size_consistency: float,
        readability_scores: List[float]
    ) -> float:
        """
        Compute overall quality score
        
        Weighted average of all metrics
        """
        weights = {
            "coherence": 0.25,
            "completeness": 0.20,
            "boundary": 0.20,
            "entity": 0.15,
            "size": 0.10,
            "readability": 0.10
        }
        
        overall = (
            weights["coherence"] * np.mean(coherence_scores) +
            weights["completeness"] * np.mean(completeness_scores) +
            weights["boundary"] * np.mean(boundary_scores) +
            weights["entity"] * np.mean(entity_scores) +
            weights["size"] * size_consistency +
            weights["readability"] * np.mean(readability_scores)
        )
        
        return overall
    
    def _detect_issues(
        self,
        chunks: List[Chunk],
        coherence_scores: List[float],
        completeness_scores: List[float],
        boundary_scores: List[float],
        entity_scores: List[float],
        size_consistency: float
    ) -> List[QualityIssue]:
        """Detect quality issues"""
        issues = []
        
        # Low coherence chunks
        low_coherence = [i for i, score in enumerate(coherence_scores) if score < self.min_coherence]
        if low_coherence:
            issues.append(QualityIssue(
                severity="medium",
                type="low_coherence",
                description=f"{len(low_coherence)} chunks have low semantic coherence",
                affected_chunks=low_coherence,
                recommendation="Consider using semantic chunking strategy or increasing chunk size"
            ))
        
        # Incomplete chunks
        incomplete = [i for i, score in enumerate(completeness_scores) if score < self.min_completeness]
        if incomplete:
            issues.append(QualityIssue(
                severity="low",
                type="incomplete_boundaries",
                description=f"{len(incomplete)} chunks have incomplete boundaries",
                affected_chunks=incomplete,
                recommendation="Enable sentence boundary preservation"
            ))
        
        # Poor boundary quality
        poor_boundaries = [i for i, score in enumerate(boundary_scores) if score < self.min_boundary_quality]
        if poor_boundaries:
            issues.append(QualityIssue(
                severity="medium",
                type="poor_boundaries",
                description=f"{len(poor_boundaries)} chunks have poor boundary quality",
                affected_chunks=poor_boundaries,
                recommendation="Use paragraph-aware or adaptive chunking"
            ))
        
        # Split entities
        split_entities = [i for i, score in enumerate(entity_scores) if score < 0.9]
        if split_entities and self.enable_entity_detection:
            issues.append(QualityIssue(
                severity="high",
                type="split_entities",
                description=f"{len(split_entities)} chunks may have split named entities",
                affected_chunks=split_entities,
                recommendation="Enable entity-aware chunking"
            ))
        
        # Inconsistent sizes
        if size_consistency < 0.7:
            issues.append(QualityIssue(
                severity="low",
                type="size_inconsistency",
                description="Chunk sizes vary significantly",
                affected_chunks=[],
                recommendation="Use fixed-size chunking for more consistent sizes"
            ))
        
        return issues
    
    def _generate_recommendations(
        self,
        metrics: QualityMetrics,
        issues: List[QualityIssue]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Overall quality
        if metrics.overall_score < 0.7:
            recommendations.append(
                "Overall quality is below threshold. Consider reviewing chunking strategy."
            )
        
        # Specific recommendations based on metrics
        if metrics.coherence_score < self.min_coherence:
            recommendations.append(
                "Low coherence detected. Try semantic or adaptive chunking strategies."
            )
        
        if metrics.completeness_score < self.min_completeness:
            recommendations.append(
                "Many chunks have incomplete boundaries. Enable sentence boundary preservation."
            )
        
        if metrics.size_consistency_score < 0.7:
            recommendations.append(
                "Chunk sizes are inconsistent. Consider fixed-size chunking or adjust parameters."
            )
        
        if metrics.entity_preservation_score < 0.9:
            recommendations.append(
                "Named entities may be split across chunks. Enable entity-aware chunking."
            )
        
        # Issue-based recommendations
        high_severity_issues = [i for i in issues if i.severity == "high"]
        if high_severity_issues:
            recommendations.append(
                f"Found {len(high_severity_issues)} high-severity issues requiring immediate attention."
            )
        
        return recommendations
    
    def _empty_report(self) -> QualityReport:
        """Return empty report for no chunks"""
        return QualityReport(
            metrics=QualityMetrics(
                overall_score=0.0,
                coherence_score=0.0,
                completeness_score=0.0,
                boundary_quality_score=0.0,
                entity_preservation_score=0.0,
                size_consistency_score=0.0,
                readability_score=0.0
            ),
            issues=[],
            recommendations=["No chunks to analyze"],
            chunk_scores=[]
        )
