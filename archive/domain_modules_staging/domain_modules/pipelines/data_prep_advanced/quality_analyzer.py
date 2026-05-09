"""
Advanced Quality Analyzer
==========================
Multi-dimensional quality assessment for legal documents
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from collections import Counter


class QualityDimension(Enum):
    """Quality dimensions for assessment"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    READABILITY = "readability"
    LEGAL_VALIDITY = "legal_validity"
    STRUCTURE = "structure"


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics"""
    
    # Overall
    overall_score: float  # 0-100
    quality_grade: str  # A+, A, B, C, D, F
    
    # Dimensions
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    readability_score: float
    legal_validity_score: float
    structure_score: float
    
    # Details
    issues: List[Dict]
    warnings: List[str]
    suggestions: List[str]
    
    # Statistics
    char_count: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    
    # Legal-specific
    article_count: int
    law_reference_count: int
    case_reference_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'overall_score': self.overall_score,
            'quality_grade': self.quality_grade,
            'dimensions': {
                'completeness': self.completeness_score,
                'accuracy': self.accuracy_score,
                'consistency': self.consistency_score,
                'readability': self.readability_score,
                'legal_validity': self.legal_validity_score,
                'structure': self.structure_score,
            },
            'issues': self.issues,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'statistics': {
                'char_count': self.char_count,
                'word_count': self.word_count,
                'sentence_count': self.sentence_count,
                'paragraph_count': self.paragraph_count,
                'article_count': self.article_count,
                'law_reference_count': self.law_reference_count,
                'case_reference_count': self.case_reference_count,
            }
        }


class QualityAnalyzer:
    """
    Advanced quality analyzer for legal documents
    
    Features:
    - Multi-dimensional quality assessment
    - Legal-specific validation
    - Readability analysis
    - Structure validation
    - Consistency checking
    - Anomaly detection
    """
    
    def __init__(
        self,
        min_quality_score: float = 70.0,
        strict_mode: bool = False
    ):
        self.min_quality_score = min_quality_score
        self.strict_mode = strict_mode
        
        # Legal patterns
        self.article_pattern = re.compile(
            r'ماده\s+[0-9۰-۹]{1,4}(?:\s+(?:تبصره|بند)\s+[آ-یa-z0-9۰-۹]{1,3})?'
        )
        self.law_pattern = re.compile(
            r'قانون\s+[^\s،\.؛]{3,50}'
        )
        self.case_pattern = re.compile(
            r'(?:پرونده|رأی)\s+(?:شماره|به\s+شماره)\s+[0-9۰-۹/-]+'
        )
    
    def analyze(self, text: str, metadata: Optional[Dict] = None) -> QualityMetrics:
        """
        Comprehensive quality analysis
        
        Args:
            text: Document text
            metadata: Optional metadata
            
        Returns:
            QualityMetrics with detailed assessment
        """
        # Basic statistics
        stats = self._compute_statistics(text)
        
        # Dimension scores
        completeness = self._assess_completeness(text, stats)
        accuracy = self._assess_accuracy(text, stats)
        consistency = self._assess_consistency(text, stats)
        readability = self._assess_readability(text, stats)
        legal_validity = self._assess_legal_validity(text, stats)
        structure = self._assess_structure(text, stats)
        
        # Overall score (weighted average)
        weights = {
            'completeness': 0.20,
            'accuracy': 0.20,
            'consistency': 0.15,
            'readability': 0.15,
            'legal_validity': 0.20,
            'structure': 0.10,
        }
        
        overall_score = (
            completeness * weights['completeness'] +
            accuracy * weights['accuracy'] +
            consistency * weights['consistency'] +
            readability * weights['readability'] +
            legal_validity * weights['legal_validity'] +
            structure * weights['structure']
        )
        
        # Quality grade
        quality_grade = self._compute_grade(overall_score)
        
        # Issues and suggestions
        issues = self._detect_issues(text, stats)
        warnings = self._generate_warnings(overall_score, issues)
        suggestions = self._generate_suggestions(issues, stats)
        
        return QualityMetrics(
            overall_score=overall_score,
            quality_grade=quality_grade,
            completeness_score=completeness,
            accuracy_score=accuracy,
            consistency_score=consistency,
            readability_score=readability,
            legal_validity_score=legal_validity,
            structure_score=structure,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions,
            **stats
        )
    
    def _compute_statistics(self, text: str) -> Dict:
        """Compute basic statistics"""
        # Character and word counts
        char_count = len(text)
        words = text.split()
        word_count = len(words)
        
        # Sentence count (approximate)
        sentence_endings = ['.', '!', '?', '؟', '۔']
        sentence_count = sum(text.count(end) for end in sentence_endings)
        sentence_count = max(1, sentence_count)
        
        # Paragraph count
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        paragraph_count = max(1, paragraph_count)
        
        # Legal elements
        article_count = len(self.article_pattern.findall(text))
        law_reference_count = len(self.law_pattern.findall(text))
        case_reference_count = len(self.case_pattern.findall(text))
        
        return {
            'char_count': char_count,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'article_count': article_count,
            'law_reference_count': law_reference_count,
            'case_reference_count': case_reference_count,
        }
    
    def _assess_completeness(self, text: str, stats: Dict) -> float:
        """Assess document completeness"""
        score = 100.0
        
        # Length check
        if stats['word_count'] < 50:
            score -= 40
        elif stats['word_count'] < 100:
            score -= 20
        
        # Structure check
        if stats['paragraph_count'] < 2:
            score -= 15
        
        # Legal elements check
        if stats['article_count'] == 0 and stats['law_reference_count'] == 0:
            score -= 25
        
        return max(0.0, score)
    
    def _assess_accuracy(self, text: str, stats: Dict) -> float:
        """Assess accuracy indicators"""
        score = 100.0
        
        # Check for common errors
        # Repeated words
        words = text.split()
        if len(words) > 1:
            repeated = sum(1 for i in range(len(words)-1) if words[i] == words[i+1])
            if repeated > 0:
                score -= min(20, repeated * 5)
        
        # Suspicious patterns
        if '???' in text or '...' * 3 in text:
            score -= 10
        
        # Encoding issues
        if '�' in text or '\ufffd' in text:
            score -= 30
        
        return max(0.0, score)
    
    def _assess_consistency(self, text: str, stats: Dict) -> float:
        """Assess internal consistency"""
        score = 100.0
        
        # Check for mixed languages inappropriately
        has_persian = any('\u0600' <= c <= '\u06ff' for c in text[:1000])
        has_english = any('a' <= c.lower() <= 'z' for c in text[:1000])
        
        if has_persian and has_english:
            # Check if it's appropriate mixing (e.g., citations)
            english_ratio = sum(1 for c in text if 'a' <= c.lower() <= 'z') / len(text)
            if english_ratio > 0.3:  # Too much English
                score -= 15
        
        # Check for consistent formatting
        # Article references should be consistent
        articles = self.article_pattern.findall(text)
        if len(articles) > 1:
            # Check consistency in formatting
            formats = set(articles)
            if len(formats) / len(articles) > 0.5:  # Too many different formats
                score -= 10
        
        return max(0.0, score)
    
    def _assess_readability(self, text: str, stats: Dict) -> float:
        """Assess readability"""
        score = 100.0
        
        # Average sentence length
        avg_sentence_length = stats['word_count'] / stats['sentence_count']
        if avg_sentence_length > 40:
            score -= 20
        elif avg_sentence_length > 30:
            score -= 10
        
        # Average word length
        words = text.split()
        if words:
            avg_word_length = sum(len(w) for w in words) / len(words)
            if avg_word_length > 8:
                score -= 10
        
        # Paragraph length
        avg_paragraph_length = stats['word_count'] / stats['paragraph_count']
        if avg_paragraph_length > 200:
            score -= 15
        
        return max(0.0, score)
    
    def _assess_legal_validity(self, text: str, stats: Dict) -> float:
        """Assess legal document validity"""
        score = 100.0
        
        # Must have legal references
        if stats['article_count'] == 0 and stats['law_reference_count'] == 0:
            score -= 40
        
        # Check for proper legal terminology
        legal_terms = [
            'قانون', 'ماده', 'تبصره', 'بند', 'رأی', 'دادگاه',
            'محکوم', 'مدعی', 'خوانده', 'دعوی', 'حکم'
        ]
        found_terms = sum(1 for term in legal_terms if term in text)
        if found_terms < 3:
            score -= 20
        
        # Check for proper structure
        if not any(marker in text for marker in ['ماده', 'بند', 'قسمت']):
            score -= 15
        
        return max(0.0, score)
    
    def _assess_structure(self, text: str, stats: Dict) -> float:
        """Assess document structure"""
        score = 100.0
        
        # Check for proper paragraphing
        if stats['paragraph_count'] < 2:
            score -= 30
        
        # Check for proper sentence structure
        if stats['sentence_count'] < 3:
            score -= 20
        
        # Check for headings/sections
        lines = text.split('\n')
        has_headings = any(
            len(line.strip()) < 50 and line.strip().endswith(':')
            for line in lines
        )
        if not has_headings and stats['word_count'] > 200:
            score -= 15
        
        return max(0.0, score)
    
    def _detect_issues(self, text: str, stats: Dict) -> List[Dict]:
        """Detect specific issues"""
        issues = []
        
        # Too short
        if stats['word_count'] < 50:
            issues.append({
                'type': 'length',
                'severity': 'high',
                'message': 'Document is too short',
                'location': 'global'
            })
        
        # No legal references
        if stats['article_count'] == 0 and stats['law_reference_count'] == 0:
            issues.append({
                'type': 'legal_validity',
                'severity': 'high',
                'message': 'No legal references found',
                'location': 'global'
            })
        
        # Encoding issues
        if '�' in text:
            issues.append({
                'type': 'encoding',
                'severity': 'critical',
                'message': 'Encoding errors detected',
                'location': 'multiple'
            })
        
        # Very long sentences
        sentences = re.split(r'[.!?؟۔]', text)
        for i, sent in enumerate(sentences):
            if len(sent.split()) > 50:
                issues.append({
                    'type': 'readability',
                    'severity': 'medium',
                    'message': 'Very long sentence detected',
                    'location': f'sentence_{i}'
                })
        
        return issues
    
    def _generate_warnings(self, overall_score: float, issues: List[Dict]) -> List[str]:
        """Generate warnings based on score and issues"""
        warnings = []
        
        if overall_score < 50:
            warnings.append("⚠️ Overall quality is very low - document may need reprocessing")
        elif overall_score < 70:
            warnings.append("⚠️ Quality is below acceptable threshold")
        
        critical_issues = [i for i in issues if i['severity'] == 'critical']
        if critical_issues:
            warnings.append(f"🚨 {len(critical_issues)} critical issues found")
        
        high_issues = [i for i in issues if i['severity'] == 'high']
        if high_issues:
            warnings.append(f"⚠️ {len(high_issues)} high-severity issues found")
        
        return warnings
    
    def _generate_suggestions(self, issues: List[Dict], stats: Dict) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Based on issues
        issue_types = Counter(i['type'] for i in issues)
        
        if 'length' in issue_types:
            suggestions.append("💡 Consider adding more content or context")
        
        if 'legal_validity' in issue_types:
            suggestions.append("💡 Add proper legal references (articles, laws)")
        
        if 'readability' in issue_types:
            suggestions.append("💡 Break down long sentences for better readability")
        
        if 'encoding' in issue_types:
            suggestions.append("💡 Fix encoding issues - re-extract or convert properly")
        
        # Based on statistics
        if stats['paragraph_count'] < 3 and stats['word_count'] > 200:
            suggestions.append("💡 Add paragraph breaks for better structure")
        
        if stats['article_count'] > 0 and stats['law_reference_count'] == 0:
            suggestions.append("💡 Add law name references for cited articles")
        
        return suggestions
    
    def _compute_grade(self, score: float) -> str:
        """Compute quality grade"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def batch_analyze(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None
    ) -> List[QualityMetrics]:
        """Analyze multiple documents"""
        if metadatas is None:
            metadatas = [None] * len(texts)
        
        return [
            self.analyze(text, metadata)
            for text, metadata in zip(texts, metadatas)
        ]
    
    def filter_by_quality(
        self,
        texts: List[str],
        min_score: Optional[float] = None
    ) -> Tuple[List[str], List[QualityMetrics]]:
        """Filter documents by quality score"""
        min_score = min_score or self.min_quality_score
        
        results = self.batch_analyze(texts)
        filtered = [
            (text, metrics)
            for text, metrics in zip(texts, results)
            if metrics.overall_score >= min_score
        ]
        
        if filtered:
            texts, metrics = zip(*filtered)
            return list(texts), list(metrics)
        return [], []
