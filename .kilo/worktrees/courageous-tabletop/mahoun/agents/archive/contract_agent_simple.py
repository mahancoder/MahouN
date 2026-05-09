"""
Contract Agent
==============

Agent برای پاسخ به سؤالات پیمانی
از کامپوننت‌های موجود استفاده می‌کند:
- HybridRAGService برای retrieval
- UltraReasoningService برای reasoning
- UltraNLIVerifier برای verification
"""

from typing import Any, Dict, Optional
import logging

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ContractAgent(BaseAgent):
    """
    Agent برای تحلیل و پاسخ به سؤالات مرتبط با قراردادها
    
    این agent از کامپوننت‌های موجود استفاده می‌کند:
    - HybridRAGService: برای جستجو و retrieval
    - UltraReasoningService: برای reasoning و تحلیل
    - UltraNLIVerifier: برای verification پاسخ‌ها
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("contract_agent", config)
        self.rag_service = None
        self.reasoning_service = None
        self.verifier = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize dependencies from existing components"""
        if self._initialized:
            return
        
        try:
            # Import existing components
            from mahoun.rag.hybrid_rag_service import create_hybrid_rag_service, RAGMode
            from mahoun.reasoning.ultra_reasoning_service import UltraReasoningService
            
            # Initialize RAG service
            self.rag_service = await create_hybrid_rag_service()
            self.logger.info("✅ HybridRAGService initialized")
            
            # Initialize reasoning service
            try:
                self.reasoning_service = UltraReasoningService()
                self.logger.info("✅ UltraReasoningService initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize UltraReasoningService: {e}")
                self.reasoning_service = None
            
            # Initialize verifier (optional)
            try:
                from mahoun.guardrails.ultra_nli_verifier import UltraNLIVerifier
                self.verifier = UltraNLIVerifier()
                self.logger.info("✅ UltraNLIVerifier initialized")
            except Exception as e:
                self.logger.warning(f"Could not initialize UltraNLIVerifier: {e}")
                self.verifier = None
            
            self._initialized = True
            self.logger.info("ContractAgent fully initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ContractAgent: {e}", exc_info=True)
            raise
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        پردازش سؤال پیمانی
        
        Args:
            input_data: شامل:
                - query: سؤال کاربر
                - top_k: تعداد نتایج (default: 10)
                - mode: RAG mode (default: AUTO)
        
        Returns:
            نتیجه شامل:
                - answer: پاسخ به سؤال
                - confidence: سطح اطمینان
                - citations: ارجاعات به مدارک
                - verified: آیا پاسخ verify شده است
        """
        if not self._initialized:
            await self.initialize()
        
        query = input_data.get("query")
        if not query:
            return await self.handle_error(
                ValueError("Query is required"),
                input_data
            )
        
        top_k = input_data.get("top_k", 10)
        mode = input_data.get("mode", "auto")
        
        try:
            # Step 1: RAG retrieval using existing HybridRAGService
            from mahoun.rag.hybrid_rag_service import RAGMode as RAGModeEnum
            
            rag_mode = RAGModeEnum.AUTO if mode == "auto" else RAGModeEnum.TEXT_ONLY
            rag_result = await self.rag_service.retrieve(
                query=query,
                mode=rag_mode,
                top_k=top_k
            )
            
            if not rag_result.results:
                return {
                    "success": False,
                    "answer": "هیچ مدرکی مرتبط با این سؤال یافت نشد.",
                    "confidence": 0.0,
                    "citations": []
                }
            
            # Step 2: Reasoning using existing UltraReasoningService
            context = [r.content for r in rag_result.results[:5]]  # Top 5 for reasoning
            
            answer: Optional[Any] = None
            confidence = 0.0
            
            if self.reasoning_service:
                try:
                    reasoning_result = await self.reasoning_service.reason(
                        context=context,
                        question=query
                    )
                    answer = reasoning_result.get("answer", "")
                    confidence = reasoning_result.get("confidence", 0.0)
                except Exception as e:
                    self.logger.warning(f"Reasoning failed: {e}, using simple answer")
            
            # Fallback: simple answer from top result
            if not answer:
                answer = rag_result.results[0].content[:500]  # First 500 chars
                confidence = rag_result.results[0].score
            
            # Step 3: Verification using existing UltraNLIVerifier (optional)
            verified = False
            if self.verifier and answer:
                try:
                    verification = await self.verifier.verify(
                        claim=answer,
                        evidence=context
                    )
                    verified = verification.get("is_valid", False) if isinstance(verification, dict) else False
                except Exception as e:
                    self.logger.warning(f"Verification failed: {e}")
            
            # Prepare citations
            citations = [
                {
                    "doc_id": r.doc_id,
                    "content": r.content[:200],  # First 200 chars
                    "score": r.score,
                    "source": r.source
                }
                for r in rag_result.results
            ]
            
            return {
                "success": True,
                "answer": answer,
                "confidence": confidence,
                "verified": verified,
                "citations": citations,
                "metadata": {
                    "rag_mode": rag_result.mode_used,
                    "retrieval_time_ms": rag_result.retrieval_time_ms,
                    "results_count": len(rag_result.results)
                }
            }
            
        except Exception as e:
            return await self.handle_error(e, input_data)
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        status = super().get_status()
        status.update({
            "initialized": self._initialized,
            "rag_service_available": self.rag_service is not None,
            "reasoning_service_available": self.reasoning_service is not None,
            "verifier_available": self.verifier is not None
        })
        return status

