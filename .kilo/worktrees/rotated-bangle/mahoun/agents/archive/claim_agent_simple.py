"""
Claim Agent
===========

Agent برای تولید محتوای دعوی
از کامپوننت‌های موجود استفاده می‌کند:
- HybridRAGService برای جستجو
- UltraReasoningService برای استدلال
- CitationEngine برای ارجاع
"""

from typing import Any, Dict, List, Optional
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ClaimAgent(BaseAgent):
    """
    Agent برای تولید محتوای دعوی
    
    این agent از کامپوننت‌های موجود استفاده می‌کند:
    - HybridRAGService: برای جستجو در مدارک
    - UltraReasoningService: برای استدلال و تحلیل
    - CitationEngine: برای ارجاع به مدارک
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("claim_agent", config)
        self.rag_service = None
        self.reasoning_service = None
        self.citation_engine = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize dependencies from existing components"""
        if self._initialized:
            return
        
        try:
            from mahoun.rag.hybrid_rag_service import create_hybrid_rag_service
            from mahoun.rag.citation_engine import CitationEngine
            
            self.rag_service = await create_hybrid_rag_service()
            self.citation_engine = CitationEngine()
            
            try:
                from mahoun.reasoning.ultra_reasoning_service import UltraReasoningService
                self.reasoning_service = UltraReasoningService()
            except Exception as e:
                self.logger.warning(f"Could not initialize UltraReasoningService: {e}")
                self.reasoning_service = None
            
            self._initialized = True
            self.logger.info("✅ ClaimAgent fully initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ClaimAgent: {e}", exc_info=True)
            raise
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تولید محتوای دعوی
        
        Args:
            input_data: شامل:
                - claim_type: نوع دعوی
                - facts: حقایق و اطلاعات
                - legal_basis: مبانی حقوقی (optional)
                - documents: مدارک مرتبط (optional)
        
        Returns:
            نتیجه شامل:
                - claim_content: محتوای دعوی
                - arguments: استدلال‌ها
                - citations: ارجاعات
                - legal_basis: مبانی حقوقی
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            claim_type = input_data.get("claim_type", "general")
            facts = input_data.get("facts", "")
            legal_basis = input_data.get("legal_basis", "")
            documents = input_data.get("documents", [])
            
            # Build query for retrieval
            query = f"{claim_type} {facts}"
            
            # Retrieve relevant documents
            rag_result = await self.rag_service.retrieve(
                query=query,
                top_k=10
            )
            
            # Extract citations
            citation_result = await self.citation_engine.extract_citations(
                rag_result=rag_result,
                query=query
            )
            
            # Build context for reasoning
            context = [r.content for r in rag_result.results[:5]]
            if facts:
                context.insert(0, f"حقایق: {facts}")
            
            # Generate claim content using reasoning
            claim_content = ""
            arguments: List[Any] = []
            if self.reasoning_service:
                reasoning_result = await self.reasoning_service.reason(
                    query=f"تولید دعوی برای {claim_type}",
                    context=context
                )
                claim_content = reasoning_result.answer if hasattr(reasoning_result, 'answer') else str(reasoning_result)
            else:
                # Fallback: simple claim generation
                claim_content = self._generate_simple_claim(claim_type, facts, rag_result.results)
            
            # Extract arguments from results
            arguments = self._extract_arguments(rag_result.results, citation_result.citations)
            
            return {
                "success": True,
                "claim_content": claim_content,
                "arguments": arguments,
                "citations": [
                    {
                        "doc_id": c.doc_id,
                        "clause": c.clause_number,
                        "citation_text": c.citation_text
                    }
                    for c in citation_result.citations
                ],
                "legal_basis": legal_basis or self._extract_legal_basis(rag_result.results),
                "metadata": {
                    "claim_type": claim_type,
                    "total_citations": len(citation_result.citations),
                    "total_arguments": len(arguments)
                }
            }
            
        except Exception as e:
            return await self.handle_error(e, input_data)
    
    def _generate_simple_claim(self, claim_type: str, facts: str, results: list) -> str:
        """Generate simple claim content"""
        claim_parts = [
            f"دعوی مربوط به: {claim_type}",
            f"\nحقایق: {facts}",
            "\nمستندات:"
        ]
        
        for i, result in enumerate(results[:3], 1):
            claim_parts.append(f"\n{i}. {result.content[:200]}...")
        
        return "\n".join(claim_parts)
    
    def _extract_arguments(self, results: list, citations: list) -> list:
        """Extract arguments from results"""
        arguments: List[Any] = []
        for result in results[:5]:
            arguments.append({
                "content": result.content[:300],
                "source": result.doc_id,
                "score": result.score
            })
        
        return arguments
    
    def _extract_legal_basis(self, results: list) -> str:
        """Extract legal basis from results"""
        legal_keywords = ["قانون", "مقررات", "آیین‌نامه", "بند", "ماده"]
        legal_basis_parts: List[Any] = []
        for result in results:
            content = result.content
            if any(kw in content for kw in legal_keywords):
                legal_basis_parts.append(content[:200])
        
        return "\n".join(legal_basis_parts[:3]) if legal_basis_parts else ""

