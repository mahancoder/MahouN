"""
Ultra Dispute Agent - Enterprise-Grade Dispute Detection
=========================================================
Agent پیشرفته برای شناسایی اختلافات و نقض تعهدات

Features:
- Multi-query Search Strategy
- Dispute Classification (طبقه‌بندی اختلافات)
- Violation Severity Scoring
- Legal Clause Mapping
- Confidence Calibration
- Graceful Degradation
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .ultra_base_agent import UltraBaseAgent, AgentConfig

logger = logging.getLogger(__name__)


class DisputeType(str, Enum):
    """Types of disputes"""
    CONTRACTUAL = "contractual"      # نقض قرارداد
    PROCEDURAL = "procedural"        # نقض آیین‌نامه
    FINANCIAL = "financial"          # اختلاف مالی
    TIMELINE = "timeline"            # تأخیر
    QUALITY = "quality"              # کیفیت
    SCOPE = "scope"                  # محدوده کار
    OTHER = "other"


class ViolationSeverity(str, Enum):
    """Severity levels for violations"""
    CRITICAL = "critical"    # بحرانی
    HIGH = "high"           # بالا
    MEDIUM = "medium"       # متوسط
    LOW = "low"             # پایین


@dataclass
class DisputeAgentConfig(AgentConfig):
    """Configuration for dispute agent"""
    top_k: int = 15
    min_relevance_score: float = 0.3
    enable_classification: bool = True
    enable_severity_scoring: bool = True
    max_queries: int = 5


@dataclass
class DisputeItem:
    """A detected dispute"""
    description: str
    dispute_type: DisputeType
    source_doc: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    related_clauses: List[str] = field(default_factory=list)


@dataclass
class ViolationItem:
    """A detected violation"""
    description: str
    severity: ViolationSeverity
    source_doc: str
    confidence: float
    legal_basis: Optional[str] = None


class UltraDisputeAgent(UltraBaseAgent):
    """
    Enterprise-grade dispute detection agent.
    
    این agent اختلافات و نقض تعهدات را شناسایی می‌کند:
    1. جستجوی چندگانه با کلیدواژه‌های مختلف
    2. طبقه‌بندی نوع اختلاف
    3. امتیازدهی شدت نقض
    4. استخراج بندهای مرتبط
    """
    
    # Dispute detection keywords
    DISPUTE_KEYWORDS = {
        DisputeType.CONTRACTUAL: ["نقض قرارداد", "عدم اجرا", "تخلف از تعهد", "فسخ"],
        DisputeType.FINANCIAL: ["مطالبه", "خسارت", "جریمه", "پرداخت", "بدهی"],
        DisputeType.TIMELINE: ["تأخیر", "مهلت", "موعد", "سررسید"],
        DisputeType.QUALITY: ["کیفیت", "عیب", "نقص", "استاندارد"],
        DisputeType.SCOPE: ["محدوده", "تغییر کار", "کار اضافی"],
        DisputeType.PROCEDURAL: ["آیین‌نامه", "مقررات", "دستورالعمل"],
    }
    
    VIOLATION_KEYWORDS = ["نقض", "تخلف", "عدم رعایت", "مخالفت", "تجاوز"]
    
    def __init__(self, config: Optional[DisputeAgentConfig] = None):
        super().__init__(
            name="ultra_dispute",
            config=config or DisputeAgentConfig()
        )
        self._rag_service = None
        self._citation_engine = None
        self._reasoning_service = None
        
        self._dispute_metrics = {
            "queries_processed": 0,
            "disputes_found": 0,
            "violations_found": 0,
            "avg_confidence": 0.0,
        }
    
    async def _initialize_impl(self):
        """Initialize components"""
        self.logger.info("Initializing UltraDisputeAgent...")
        
        try:
            from mahoun.rag.hybrid_rag_service import create_hybrid_rag_service
            self._rag_service = await create_hybrid_rag_service()
            self.logger.info("✅ RAG Service initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ RAG Service not available: {e}")
        
        try:
            from mahoun.rag.citation_engine import CitationEngine
            self._citation_engine = CitationEngine()
            self.logger.info("✅ Citation Engine initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Citation Engine not available: {e}")
        
        try:
            from mahoun.reasoning.ultra_reasoning_service import UltraReasoningService
            self._reasoning_service = UltraReasoningService()
            self.logger.info("✅ Reasoning Service initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Reasoning Service not available: {e}")
    
    async def _process_impl(
        self,
        input_data: Dict[str, Any],
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Detect disputes and violations.
        
        Args:
            input_data: {
                "query": str,           # Main query/description
                "documents": list,      # Optional documents to analyze
                "focus_areas": list,    # Optional focus areas
                "case_context": str     # Optional case context
            }
        """
        query = input_data.get("query", "")
        focus_areas = input_data.get("focus_areas", [])
        case_context = input_data.get("case_context", "")
        
        if not query:
            raise ValueError("Query is required")
        
        # Build search queries
        search_queries = self._build_search_queries(query, focus_areas)
        
        # Execute searches
        all_results: List[Any] = []
        for sq in search_queries[:self.config.max_queries]:
            results = await self._search(sq, correlation_id)
            all_results.extend(results)
        
        # Deduplicate results
        unique_results = self._deduplicate_results(all_results)
        
        # Detect disputes
        disputes = self._detect_disputes(unique_results, query)
        
        # Detect violations
        violations = self._detect_violations(unique_results, query)
        
        # Extract related clauses
        related_clauses = await self._extract_clauses(unique_results, correlation_id)
        
        # Update metrics
        self._dispute_metrics["queries_processed"] += 1
        self._dispute_metrics["disputes_found"] += len(disputes)
        self._dispute_metrics["violations_found"] += len(violations)
        
        return {
            "disputes": [self._dispute_to_dict(d) for d in disputes],
            "violations": [self._violation_to_dict(v) for v in violations],
            "related_clauses": related_clauses,
            "summary": self._generate_summary(disputes, violations),
            "metadata": {
                "total_disputes": len(disputes),
                "total_violations": len(violations),
                "queries_executed": len(search_queries),
                "results_analyzed": len(unique_results)
            }
        }
    
    async def _fallback_impl(
        self,
        input_data: Dict[str, Any],
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Fallback: keyword-based detection only"""
        self.logger.warning(f"[{correlation_id}] Using FALLBACK mode")
        
        query = input_data.get("query", "")
        
        # Simple keyword detection
        disputes: List[Any] = []
        violations: List[Any] = []
        for dtype, keywords in self.DISPUTE_KEYWORDS.items():
            for kw in keywords:
                if kw in query:
                    disputes.append({
                        "description": f"احتمال اختلاف: {kw}",
                        "type": dtype.value,
                        "confidence": 0.5,
                        "fallback": True
                    })
                    break
        
        for kw in self.VIOLATION_KEYWORDS:
            if kw in query:
                violations.append({
                    "description": f"احتمال نقض: {kw}",
                    "severity": "medium",
                    "confidence": 0.5,
                    "fallback": True
                })
        
        return {
            "disputes": disputes,
            "violations": violations,
            "related_clauses": [],
            "summary": "تحلیل محدود (حالت fallback)",
            "metadata": {"fallback_used": True}
        }
    
    def _build_search_queries(self, base_query: str, focus_areas: List[str]) -> List[str]:
        """Build multiple search queries"""
        queries = [base_query]
        
        # Add focus areas
        for area in focus_areas[:3]:
            queries.append(f"{base_query} {area}")
        
        # Add dispute keywords
        for dtype, keywords in self.DISPUTE_KEYWORDS.items():
            if keywords[0] not in base_query:
                queries.append(f"{base_query} {keywords[0]}")
        
        return queries[:self.config.max_queries]
    
    async def _search(self, query: str, correlation_id: Optional[str]) -> List[Dict]:
        """Execute RAG search"""
        if not self._rag_service:
            return []
        
        try:
            from mahoun.rag.hybrid_rag_service import RAGMode
            result = await self._rag_service.retrieve(
                query=query,
                mode=RAGMode.AUTO,
                top_k=self.config.top_k
            )
            return [
                {
                    "content": r.content,
                    "doc_id": r.doc_id,
                    "score": r.score,
                    "source": r.source
                }
                for r in result.results
                if r.score >= self.config.min_relevance_score
            ]
        except Exception as e:
            self.logger.warning(f"[{correlation_id}] Search failed: {e}")
            return []
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results"""
        seen = set()
        unique: List[Any] = []
        for r in results:
            key = r["doc_id"]
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
    
    def _detect_disputes(self, results: List[Dict], query: str) -> List[DisputeItem]:
        """Detect disputes from results"""
        disputes: List[Any] = []
        for result in results:
            content = result["content"].lower()
            
            # Check each dispute type
            for dtype, keywords in self.DISPUTE_KEYWORDS.items():
                if any(kw in content for kw in keywords):
                    confidence = result["score"] * 0.9
                    
                    disputes.append(DisputeItem(
                        description=result["content"][:300],
                        dispute_type=dtype,
                        source_doc=result["doc_id"],
                        confidence=confidence,
                        evidence=[result["content"][:500]]
                    ))
                    break
        
        # Sort by confidence
        disputes.sort(key=lambda x: x.confidence, reverse=True)
        return disputes[:10]
    
    def _detect_violations(self, results: List[Dict], query: str) -> List[ViolationItem]:
        """Detect violations from results"""
        violations: List[Any] = []
        for result in results:
            content = result["content"].lower()
            
            if any(kw in content for kw in self.VIOLATION_KEYWORDS):
                # Determine severity
                severity = self._assess_severity(content)
                confidence = result["score"] * 0.85
                
                violations.append(ViolationItem(
                    description=result["content"][:300],
                    severity=severity,
                    source_doc=result["doc_id"],
                    confidence=confidence
                ))
        
        violations.sort(key=lambda x: x.confidence, reverse=True)
        return violations[:10]
    
    def _assess_severity(self, content: str) -> ViolationSeverity:
        """Assess violation severity"""
        critical_keywords = ["فسخ", "ابطال", "جبران خسارت کامل"]
        high_keywords = ["خسارت", "جریمه", "تعلیق"]
        medium_keywords = ["تأخیر", "نقص", "اصلاح"]
        
        if any(kw in content for kw in critical_keywords):
            return ViolationSeverity.CRITICAL
        elif any(kw in content for kw in high_keywords):
            return ViolationSeverity.HIGH
        elif any(kw in content for kw in medium_keywords):
            return ViolationSeverity.MEDIUM
        return ViolationSeverity.LOW
    
    async def _extract_clauses(self, results: List[Dict], correlation_id: Optional[str]) -> List[Dict]:
        """Extract related clauses"""
        clauses: List[Any] = []
        if self._citation_engine:
            try:
                # Simple clause extraction
                for result in results[:5]:
                    content = result["content"]
                    if "ماده" in content or "بند" in content:
                        clauses.append({
                            "text": content[:200],
                            "source": result["doc_id"]
                        })
            except Exception as e:
                self.logger.warning(f"[{correlation_id}] Clause extraction failed: {e}")
        
        return clauses[:10]
    
    def _generate_summary(self, disputes: List[DisputeItem], violations: List[ViolationItem]) -> str:
        """Generate summary of findings"""
        parts: List[Any] = []
        if disputes:
            types = set(d.dispute_type.value for d in disputes)
            parts.append(f"شناسایی {len(disputes)} اختلاف در حوزه‌های: {', '.join(types)}")
        
        if violations:
            critical = sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL)
            high = sum(1 for v in violations if v.severity == ViolationSeverity.HIGH)
            parts.append(f"شناسایی {len(violations)} نقض ({critical} بحرانی، {high} بالا)")
        
        if not parts:
            return "اختلاف یا نقض خاصی شناسایی نشد"
        
        return " | ".join(parts)
    
    def _dispute_to_dict(self, d: DisputeItem) -> Dict:
        return {
            "description": d.description,
            "type": d.dispute_type.value,
            "source": d.source_doc,
            "confidence": round(d.confidence, 3),
            "evidence": d.evidence[:2]
        }
    
    def _violation_to_dict(self, v: ViolationItem) -> Dict:
        return {
            "description": v.description,
            "severity": v.severity.value,
            "source": v.source_doc,
            "confidence": round(v.confidence, 3)
        }
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        return {
            "components": {
                "rag_service": self._rag_service is not None,
                "citation_engine": self._citation_engine is not None,
                "reasoning_service": self._reasoning_service is not None
            },
            "metrics": self._dispute_metrics.copy()
        }
