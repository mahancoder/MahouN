"""
Enhanced RAG Pipeline with GAT Reranking
=========================================

Integrates Graph Attention Networks, Uncertainty Quantification,
and Chain-of-Thought reasoning into the RAG pipeline.

Flow:
1. Hybrid Retrieval (BM25 + Dense)
2. Cross-Encoder Reranking (optional)
3. GAT Reranking (NEW)
4. Uncertainty Filtering (NEW)
5. Response Generation
"""


import asyncio
from typing import List, Dict, Any, Optional, Protocol, runtime_checkable
import json
import os
from pathlib import Path

from core.models import RetrievalResult, LegalDocument, UncertaintyEstimate
from core import rag_pipeline
from pipelines.gnn.graph_builder import LegalGraphBuilder
from pipelines.guardrails import NLIVerifier, CitationAuditor, HallucinationDetector
from pipelines._logging import setup_logger

log = setup_logger("enhanced_rag")

# NEW: Import smart cache and query enhancement
try:
    from pipelines.smart_cache import SmartCache, CacheLevel
    HAS_SMART_CACHE = True
except ImportError:
    HAS_SMART_CACHE = False

try:
    from pipelines.advanced_query_enhancement import (
        AdvancedQueryEnhancer,
        QueryIntent,
        QueryComplexity,
    )
    HAS_QUERY_ENHANCEMENT = True
except ImportError:
    HAS_QUERY_ENHANCEMENT = False
    log.warning("Query enhancement not available")

# NEW: Import reasoning services
try:
    from reasoning.generation import AnswerComposerService, ComposerConfig
    from reasoning.uncertainty import UncertaintyService, UncertaintyConfig
    from reasoning.policy import PolicyGuardrailsService, PolicyConfig
    HAS_REASONING_SERVICES = True
except ImportError:
    HAS_REASONING_SERVICES = False

# Import model manager with fallback to avoid circular dependency
try:
    from api.services.model_manager import get_model_manager
    HAS_MODEL_MANAGER = True
except ImportError:
    HAS_MODEL_MANAGER = False
    get_model_manager = None

log = setup_logger("enhanced_rag")


class EnhancedRAGPipeline(core.rag_pipeline.RAGPipeline):
    """
    Enhanced RAG pipeline with GAT-based reranking

    Features:
    - Hybrid retrieval (existing)
    - GAT reranking with graph structure
    - Uncertainty quantification
    - Chain-of-thought explanations
    - Backward compatible

    Example:
        >>> pipeline = EnhancedRAGPipeline(
        ...     enable_gat_reranking=True,
        ...     gat_model_path="models/gat_best.pt"
        ... )
        >>> results = await pipeline.retrieve_and_rerank(
        ...     query="رأی دادگاه عالی",
        ...     top_k=10
        ... )
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        enable_gat_reranking: bool = True,
        gat_model_path: Optional[str] = None,
        graph_path: Optional[str] = None,
        uncertainty_threshold: float = 0.2,
        min_results: int = 3,
        score_weights: Optional[Dict[str, float]] = None,
        enable_smart_cache: bool = True,
        enable_query_enhancement: bool = True,
    ):
        """
        Initialize Enhanced RAG Pipeline

        Args:
            config: Configuration dict (for AdvancedRetriever)
            enable_gat_reranking: Enable GAT reranking
            gat_model_path: Path to trained GAT model
            graph_path: Path to pre-built graph
            uncertainty_threshold: Filter results with uncertainty > threshold
            min_results: Minimum results to return (fallback)
            score_weights: Weights for score fusion
        """
        log.info("Initializing Enhanced RAG Pipeline")

        # Load config
        if config is None:
            from pipelines._config import load_config

            config_obj = load_config()
            # Convert AppConfig to dict
            config = config_obj.__dict__ if hasattr(config_obj, '__dict__') else {}
        else:
            # Ensure config is a dict
            config = config if isinstance(config, dict) else (config.__dict__ if hasattr(config, '__dict__') else {})

        self.config = config
        self.enable_gat_reranking = enable_gat_reranking
        self.uncertainty_threshold = uncertainty_threshold
        self.min_results = min_results
        
        # NEW: Initialize Smart Cache
        self.smart_cache: Optional[SmartCache] = None
        if enable_smart_cache and HAS_SMART_CACHE:
            try:
                log.info("Initializing Smart Cache...")
                self.smart_cache = SmartCache(
                    max_l1_size=config.get("cache_l1_size", 1000),
                    max_l2_size=config.get("cache_l2_size", 10000),
                    similarity_threshold=config.get("cache_similarity_threshold", 0.92),
                    enable_redis=config.get("cache_enable_redis", False),
                    redis_host=config.get("redis_host", "localhost"),
                    redis_port=config.get("redis_port", 6379),
                )
                log.info("✅ Smart Cache initialized")
            except Exception as e:
                log.warning(f"⚠️ Failed to initialize Smart Cache: {e}")
                self.smart_cache = None
        
        # NEW: Initialize Query Enhancer
        self.query_enhancer: Optional[AdvancedQueryEnhancer] = None
        if enable_query_enhancement and HAS_QUERY_ENHANCEMENT:
            try:
                log.info("Initializing Query Enhancer...")
                self.query_enhancer = AdvancedQueryEnhancer()
                log.info("✅ Query Enhancer initialized")
            except Exception as e:
                log.warning(f"⚠️ Failed to initialize Query Enhancer: {e}")
                self.query_enhancer = None

        # Score fusion weights
        self.score_weights = score_weights or {
            "retrieval": 0.4,
            "gat": 0.3,
            "pagerank": 0.2,
            "cross_encoder": 0.1,
        }

        # Policy manager hot-reload
        self._policy_manager = get_global_policy_manager()
        self._apply_runtime_policy()

        # Apply adaptive runtime policy if available
        self._apply_runtime_policy()

        # Initialize base retriever
        log.info("Initializing base retriever...")
        # Allow DI-friendly custom retriever via config (optional)
        custom_retriever: Optional[RetrieverProtocol] = (
            getattr(config, "custom_retriever", None)
            if hasattr(config, "custom_retriever")
            else None
        )
        self.retriever = custom_retriever or AdvancedRetriever(config)

        # Initialize GAT reranker (if enabled)
        self.gat_reranker: Optional[GATRerankerService] = None
        if enable_gat_reranking:
            try:
                log.info("Initializing GAT reranker...")
                self.gat_reranker = GATRerankerService(
                    model_path=gat_model_path,
                    graph_path=graph_path,
                    enable_uncertainty=True,
                    fallback_to_pagerank=True,
                )
                log.info("GAT reranking enabled")
            except Exception as e:
                log.warning(f"Failed to initialize GAT reranker: {e}")
                log.warning("Continuing without GAT reranking")
                self.enable_gat_reranking = False
        else:
            log.info("GAT reranking disabled")
        
        # NEW: Initialize Guardrails with ModelManager
        log.info("Initializing guardrails with ModelManager...")
        try:
            # Use ModelManager for robust NLI loading
            model_manager = get_model_manager()
            nli_model = model_manager.get_model_with_fallback("nli")
            nli_tokenizer = model_manager.get_tokenizer_with_fallback("nli")
            
            if nli_model is not None and nli_tokenizer is not None:
                self.nli_verifier = NLIVerifier(
                    model=nli_model,
                    tokenizer=nli_tokenizer,
                    threshold=config.get("nli_threshold", 0.5),
                    use_model_manager=False  # Already loaded
                )
                log.info("✅ NLI verifier initialized via ModelManager")
            else:
                log.warning("⚠️ NLI model unavailable, trying direct loading...")
                self.nli_verifier = NLIVerifier(
                    model_name=config.get("nli_model", "microsoft/deberta-v3-base"),
                    threshold=config.get("nli_threshold", 0.5),
                    use_model_manager=False
                )
            
            self.citation_auditor = CitationAuditor(
                min_accuracy=config.get("citation_min_accuracy", 0.8)
            )
            self.hallucination_detector = HallucinationDetector(
                nli_verifier=self.nli_verifier,
                hallucination_threshold=config.get("hallucination_threshold", 0.6)
            )
            log.info("✅ Guardrails initialized successfully")
        except Exception as e:
            log.warning(f"⚠️ Failed to initialize guardrails: {e}")
            self.nli_verifier = None
            self.citation_auditor = None
            self.hallucination_detector = None
        
        # NEW: Initialize Answer Composer
        self.answer_composer = None
        if HAS_REASONING_SERVICES:
            try:
                log.info("Initializing Answer Composer...")
                composer_config = ComposerConfig(
                    max_tokens=config.get("answer_max_tokens", 512),
                    temperature=config.get("answer_temperature", 0.3),
                    default_style=config.get("answer_style", "formal"),
                    enable_cot=config.get("enable_cot", False)
                )
                self.answer_composer = AnswerComposerService(config=composer_config)
                log.info("✅ Answer Composer initialized")
            except Exception as e:
                log.warning(f"⚠️ Failed to initialize Answer Composer: {e}")
        
        # NEW: Initialize Uncertainty Service (Req 6.1, 6.2, 6.3, 6.4)
        self.uncertainty_service = None
        if HAS_REASONING_SERVICES:
            try:
                log.info("Initializing Uncertainty Service...")
                # Get uncertainty method from config (default: ensemble)
                uncertainty_method = config.get("uncertainty_method", "ensemble")
                
                uncertainty_config = UncertaintyConfig(
                    default_method=uncertainty_method,
                    enable_calibration=config.get("enable_uncertainty_calibration", True),
                    enable_ensemble=config.get("enable_uncertainty_ensemble", True)
                )
                self.uncertainty_service = UncertaintyService(config=uncertainty_config)
                log.info(f"✅ Uncertainty Service initialized (method={uncertainty_method})")
            except Exception as e:
                log.warning(f"⚠️ Failed to initialize Uncertainty Service: {e}")
        
        # NEW: Initialize Policy Guardrails
        self.policy_service = None
        if HAS_REASONING_SERVICES:
            try:
                log.info("Initializing Policy Guardrails...")
                policy_config = PolicyConfig(
                    enable_pii_redaction=config.get("enable_pii_redaction", True),
                    enable_content_filtering=config.get("enable_content_filtering", True),
                    enable_audit_logging=False,  # No pool in pipeline init
                    block_on_pii=False,
                    block_on_filter_violations=False  # Warning only
                )
                self.policy_service = PolicyGuardrailsService(config=policy_config)
                log.info("✅ Policy Guardrails initialized")
            except Exception as e:
                log.warning(f"⚠️ Failed to initialize Policy Guardrails: {e}")

        log.info(
            f"Enhanced RAG Pipeline initialized: "
            f"GAT={'enabled' if self.enable_gat_reranking else 'disabled'}, "
            f"uncertainty_threshold={uncertainty_threshold}, "
            f"reasoning_services={'enabled' if HAS_REASONING_SERVICES else 'disabled'}"
        )

    def _apply_runtime_policy(self) -> None:
        try:
            self._policy_manager.apply_to_pipeline(self)
        except Exception as exc:
            log.warning(f"Could not apply runtime policy: {exc}")

    def _apply_runtime_policy(self) -> None:
        """Apply runtime policy from feedback scheduler if present."""
        policy_path = os.getenv(
            "FEEDBACK_POLICY_PATH",
            os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "feedback", "runtime_policy.json")),
        )
        try:
            if os.path.exists(policy_path):
                with open(policy_path, "r", encoding="utf-8") as f:
                    pol = json.load(f)
                if isinstance(pol, dict):
                    thr = pol.get("uncertainty_threshold")
                    if isinstance(thr, (int, float)):
                        self.uncertainty_threshold = float(thr)
                    sw = pol.get("score_weights")
                    if isinstance(sw, dict):
                        merged = {**self.score_weights, **sw}
                        s = sum(merged.values())
                        if s > 0:
                            merged = {k: float(v) / s for k, v in merged.items()}
                        self.score_weights = merged
                log.info(f"Applied runtime policy from {policy_path}")
        except Exception as e:
            log.warning(f"Could not apply runtime policy from {policy_path}: {e}")

    async def query(
        self,
        query: str,
        top_k: int = 10,
        llm_generate_fn: Optional[callable] = None,
        use_expansion: bool = True,
        return_explanations: bool = False,
        verify_answer: bool = True
    ) -> Dict[str, Any]:
        """
        Complete RAG query with retrieval, reranking, generation, and verification
        
        NEW: End-to-end RAG pipeline with guardrails
        
        Args:
            query: User query
            top_k: Number of results to retrieve
            llm_generate_fn: Custom LLM generation function
            use_expansion: Use query expansion
            return_explanations: Return explanations
            verify_answer: Enable answer verification
            
        Returns:
            Complete RAG result with answer and verification
        """
        log.info(f"🔍 Processing query: {query[:100]}...")
        
        # Step 1: Retrieve and rerank
        retrieved_results = await self.retrieve_and_rerank(
            query=query,
            top_k=top_k,
            use_expansion=use_expansion,
            return_explanations=return_explanations
        )
        
        if not retrieved_results:
            return {
                "query": query,
                "answer": "متأسفانه هیچ نتیجه‌ای برای این سوال یافت نشد.",
                "retrieved_results": [],
                "success": False,
                "error": "No results found"
            }
        
        # Step 2: Generate and verify answer
        if verify_answer and (self.nli_verifier or self.citation_auditor or self.hallucination_detector):
            result = await self.generate_and_verify_answer(
                query=query,
                retrieved_results=retrieved_results,
                llm_generate_fn=llm_generate_fn
            )
        else:
            # Generate without verification
            context = "\n\n".join([r.text for r in retrieved_results[:5]])
            if llm_generate_fn:
                answer = await llm_generate_fn(context, query)
            else:
                answer = self._generate_extractive_answer(query, retrieved_results)
            
            result = {
                "query": query,
                "answer": answer,
                "retrieved_results": retrieved_results,
                "context": context,
                "success": True,
                "verification": {"is_valid": True, "warnings": []}
            }
        
        log.info(f"✅ Query processed successfully")
        return result

    async def retrieve_and_rerank(
        self,
        query: str,
        top_k: int = 10,
        use_expansion: bool = True,
        use_diversification: bool = False,
        return_explanations: bool = False,
    ) -> List[RetrievalResult]:
        """
        Retrieve and rerank documents with GAT

        Args:
            query: Search query
            top_k: Number of results to return
            use_expansion: Enable query expansion
            use_diversification: Enable result diversification
            return_explanations: Include chain-of-thought explanations

        Returns:
            List of RetrievalResult with scores, uncertainty, and reasoning
        """
        log.info(f"Processing query: {query}")

        try:
            # NEW: Step 0: Check Smart Cache
            if self.smart_cache:
                cached_results, cache_level = self.smart_cache.get(query, use_semantic=True)
                if cached_results:
                    log.info(f"✅ Cache HIT from {cache_level.value}")
                    # Convert cached results back to RetrievalResult objects
                    return [
                        RetrievalResult(
                            doc_id=r["doc_id"],
                            score=r["score"],
                            text=r["text"],
                            metadata=r.get("metadata", {}),
                        )
                        for r in cached_results[:top_k]
                    ]
                log.debug("Cache MISS, proceeding with retrieval")
            
            # NEW: Step 0.5: Query Enhancement
            enhanced_query = None
            query_variants = [query]
            
            if self.query_enhancer:
                log.debug("Enhancing query...")
                enhanced_query = self.query_enhancer.enhance(query)
                
                log.info(
                    f"Query enhanced: intent={enhanced_query.intent.value}, "
                    f"complexity={enhanced_query.complexity.value}, "
                    f"variants={len(enhanced_query.get_all_variants())}"
                )
                
                # Adjust top_k based on complexity
                if enhanced_query.complexity == QueryComplexity.MULTI_HOP:
                    top_k_adjusted = top_k * 2
                    log.debug(f"Complex query detected, increasing top_k to {top_k_adjusted}")
                elif enhanced_query.complexity == QueryComplexity.SIMPLE:
                    top_k_adjusted = max(top_k // 2, 5)
                    log.debug(f"Simple query detected, reducing top_k to {top_k_adjusted}")
                else:
                    top_k_adjusted = top_k
                
                # Use query variants for retrieval
                query_variants = enhanced_query.get_all_variants()[:3]  # Limit to 3
            else:
                top_k_adjusted = top_k
            
            # Step 1: Hybrid Retrieval (with variants)
            log.debug(f"Step 1: Hybrid retrieval with {len(query_variants)} variants...")
            
            all_retrieval_results = []
            for variant in query_variants:
                variant_results = await self._hybrid_retrieve(
                    variant,
                    top_k=top_k_adjusted * 2,  # Get more candidates
                    use_expansion=use_expansion,
                    use_diversification=use_diversification,
                )
                all_retrieval_results.extend(variant_results)
            
            # Deduplicate by doc_id
            seen_ids = set()
            retrieval_results = []
            for result in all_retrieval_results:
                if result.doc_id not in seen_ids:
                    seen_ids.add(result.doc_id)
                    retrieval_results.append(result)

            if not retrieval_results:
                log.warning("No results from hybrid retrieval")
                return []

            log.info(f"Retrieved {len(retrieval_results)} unique candidates")

            # Step 2: GAT Reranking (if enabled)
            if self.enable_gat_reranking and self.gat_reranker:
                log.debug("Step 2: GAT reranking...")
                retrieval_results = await self._gat_rerank(
                    query,
                    retrieval_results,
                    top_k=top_k * 2,
                    return_explanations=return_explanations,
                )
                log.info(f"After GAT reranking: {len(retrieval_results)} results")

            # Step 3: Uncertainty Filtering
            if self.uncertainty_threshold > 0:
                log.debug("Step 3: Uncertainty filtering...")
                retrieval_results = self._filter_by_uncertainty(
                    retrieval_results,
                    threshold=self.uncertainty_threshold,
                    min_results=self.min_results,
                )
                log.info(f"After uncertainty filtering: {len(retrieval_results)} results")

            # Step 4: Final ranking and truncation
            final_results = retrieval_results[:top_k]

            log.info(f"Returning {len(final_results)} final results")
            
            # NEW: Cache results
            if self.smart_cache:
                # Convert to cacheable format
                cacheable_results = [
                    {
                        "doc_id": r.doc_id,
                        "score": r.score,
                        "text": r.text,
                        "metadata": r.metadata,
                    }
                    for r in final_results
                ]
                
                # Add metadata
                cache_metadata = {}
                if enhanced_query:
                    cache_metadata = {
                        "intent": enhanced_query.intent.value,
                        "complexity": enhanced_query.complexity.value,
                    }
                
                self.smart_cache.put(query, cacheable_results, metadata=cache_metadata)
                log.debug("Results cached")

            return final_results

        except Exception as e:
            log.error(f"Error in retrieve_and_rerank: {e}", exc_info=True)
            # Fallback: return basic retrieval results
            return await self._hybrid_retrieve(query, top_k=top_k)

    async def _hybrid_retrieve(
        self,
        query: str,
        top_k: int = 50,
        use_expansion: bool = True,
        use_diversification: bool = False,
    ) -> List[RetrievalResult]:
        """
        Perform hybrid retrieval (existing pipeline)

        Args:
            query: Search query
            top_k: Number of results
            use_expansion: Query expansion
            use_diversification: Result diversification

        Returns:
            List of RetrievalResult
        """
        # Run retrieval in executor (blocking operation)
        loop = asyncio.get_event_loop()
        result_dict = await loop.run_in_executor(
            None,
            lambda: self.retriever.retrieve(
                query,
                top_k=top_k,
                use_expansion=use_expansion,
                use_diversification=use_diversification,
            ),
        )

        # Convert to RetrievalResult objects
        results = []
        for r in result_dict.get("results", []):
            results.append(
                RetrievalResult(
                    doc_id=r["id"],
                    score=r["score"],
                    text=r["text"],
                    metadata=r.get("metadata", {}),
                    # Store original method
                    **{"method": r.get("method", "hybrid")},
                )
            )

        return results

    async def _gat_rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = 20,
        return_explanations: bool = False,
    ) -> List[RetrievalResult]:
        """
        Apply GAT reranking with uncertainty

        Args:
            query: Search query
            results: Candidate results
            top_k: Number to keep
            return_explanations: Include explanations

        Returns:
            Reranked results with uncertainty
        """
        if not results:
            return results

        try:
            # Convert to dict format for GAT reranker
            candidates = [
                {"id": r.doc_id, "text": r.text, "score": r.score, "metadata": r.metadata}
                for r in results
            ]

            # Apply GAT reranking
            reranked = await self.gat_reranker.rerank_async(
                query=query,
                results=candidates,
                top_k=top_k,
                alpha=self.score_weights["retrieval"],
                beta=self.score_weights["gat"],
                gamma=self.score_weights["pagerank"],
                return_explanation=return_explanations,
                return_uncertainty=True,
            )

            # Convert back to RetrievalResult
            # (rerank_async already returns RetrievalResult objects)
            return reranked

        except Exception as e:
            log.error(f"GAT reranking failed: {e}")
            log.warning("Falling back to original retrieval scores")
            return results[:top_k]

    def _filter_by_uncertainty(
        self, results: List[RetrievalResult], threshold: float = 0.2, min_results: int = 3
    ) -> List[RetrievalResult]:
        """
        Filter results by uncertainty threshold
        
        NEW: Uses UncertaintyService for advanced filtering with ensemble methods

        Args:
            results: Results with uncertainty estimates
            threshold: Max uncertainty to keep
            min_results: Minimum results to return

        Returns:
            Filtered results
        """
        if not results:
            return results
        
        # NEW: Use UncertaintyService if available (Req 6.1, 6.2, 6.3, 6.4)
        if self.uncertainty_service:
            log.debug(f"Using UncertaintyService for filtering (method={self.config.get('uncertainty_method', 'ensemble')})")
            return self.uncertainty_service.filter_by_uncertainty(
                results,
                threshold=threshold,
                min_results=min_results
            )

        # Fallback: Original implementation (backward compatibility)
        log.debug("Using fallback uncertainty filtering")
        # Separate results with and without uncertainty
        with_uncertainty = [r for r in results if r.uncertainty is not None]
        without_uncertainty = [r for r in results if r.uncertainty is None]

        # Filter by threshold
        high_confidence = [
            r for r in with_uncertainty if r.uncertainty.is_high_confidence(threshold)
        ]

        log.debug(
            f"Uncertainty filtering: {len(high_confidence)}/{len(with_uncertainty)} "
            f"high confidence (threshold={threshold})"
        )

        # Combine: high confidence + no uncertainty
        filtered = high_confidence + without_uncertainty

        # Ensure minimum results
        if len(filtered) < min_results:
            log.warning(
                f"Only {len(filtered)} high-confidence results, "
                f"adding {min_results - len(filtered)} more"
            )
            # Add low-confidence results to meet minimum
            low_confidence = [
                r for r in with_uncertainty if not r.uncertainty.is_high_confidence(threshold)
            ]
            filtered.extend(low_confidence[: min_results - len(filtered)])

        return filtered

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get pipeline statistics

        Returns:
            Statistics dict
        """
        stats = {
            "gat_reranking_enabled": self.enable_gat_reranking,
            "uncertainty_threshold": self.uncertainty_threshold,
            "score_weights": self.score_weights,
            "min_results": self.min_results,
        }

        if self.gat_reranker:
            stats["gat_mode"] = self.gat_reranker.mode
            stats["gat_device"] = getattr(self.gat_reranker, "device", "cpu")
        
        # NEW: Add cache statistics
        if self.smart_cache:
            stats["cache"] = self.smart_cache.get_stats()
            stats["cache_enabled"] = True
        else:
            stats["cache_enabled"] = False
        
        # NEW: Add query enhancement status
        stats["query_enhancement_enabled"] = self.query_enhancer is not None

        return stats

    # Synchronous wrapper for backward compatibility
    def retrieve_and_rerank_sync(
        self, query: str, top_k: int = 10, **kwargs
    ) -> List[RetrievalResult]:
        """
        Synchronous version of retrieve_and_rerank

        For backward compatibility with non-async code.

        Args:
            query: Search query
            top_k: Number of results
            **kwargs: Additional arguments

        Returns:
            List of RetrievalResult
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.retrieve_and_rerank(query, top_k, **kwargs))


# Convenience function
async def enhanced_rag_search(
    query: str, top_k: int = 10, config: Optional[Dict[str, Any]] = None, **kwargs
) -> List[RetrievalResult]:
    """
    Convenience function for enhanced RAG search

    Args:
        query: Search query
        top_k: Number of results
        config: Configuration dict
        **kwargs: Additional arguments for EnhancedRAGPipeline

    Returns:
        List of RetrievalResult
    """
    pipeline = EnhancedRAGPipeline(config=config, **kwargs)
    return await pipeline.retrieve_and_rerank(query, top_k=top_k)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="Search query")
    ap.add_argument("--top_k", type=int, default=10, help="Number of results")
    ap.add_argument("--gat_model", help="Path to GAT model")
    ap.add_argument("--no_gat", action="store_true", help="Disable GAT reranking")
    ap.add_argument("--uncertainty_threshold", type=float, default=0.2)
    ap.add_argument("--explanations", action="store_true", help="Include explanations")
    args = ap.parse_args()

    # Create pipeline
    pipeline = EnhancedRAGPipeline(
        enable_gat_reranking=not args.no_gat,
        gat_model_path=args.gat_model,
        uncertainty_threshold=args.uncertainty_threshold,
    )

    # Run search
    results = asyncio.run(
        pipeline.retrieve_and_rerank(
            query=args.query, top_k=args.top_k, return_explanations=args.explanations
        )
    )

    # Display results
    print("\n" + "=" * 80)
    print(f"Query: {args.query}")
    print(f"Results: {len(results)}")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        print(f"\n[{i}] Score: {result.score:.4f}")
        print(f"ID: {result.doc_id}")

        if result.gnn_score is not None:
            print(f"GNN Score: {result.gnn_score:.4f}")

        if result.uncertainty:
            print(
                f"Uncertainty: {result.uncertainty.uncertainty:.4f} "
                f"({'high' if result.uncertainty.is_high_confidence() else 'low'} confidence)"
            )

        print(f"Text: {result.text[:200]}...")
        print("-" * 80)

    # Statistics
    print("\nPipeline Statistics:")
    stats = pipeline.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")


@runtime_checkable
class RetrieverProtocol(Protocol):
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_expansion: bool = True,
        use_diversification: bool = False,
    ) -> Dict: ...


@runtime_checkable
class RerankerProtocol(Protocol):
    async def rerank_async(
        self, query: str, results: List[Dict[str, Any]], top_k: int = 50, **kwargs
    ) -> List[RetrievalResult]: ...


    async def generate_and_verify_answer(
        self,
        query: str,
        retrieved_results: List[RetrievalResult],
        llm_generate_fn: Optional[callable] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Generate answer with guardrail verification
        
        NEW: Complete generation + verification pipeline
        
        Args:
            query: User query
            retrieved_results: Retrieved and reranked results
            llm_generate_fn: Custom LLM generation function (context, query) -> answer
            max_retries: Maximum retries if verification fails
            
        Returns:
            Dict with answer, verification results, and metadata
        """
        # Extract context and sources
        context = "\n\n".join([r.text for r in retrieved_results[:5]])
        sources = [r.text for r in retrieved_results[:10]]
        
        # Get uncertainty if available
        uncertainty = None
        if retrieved_results and hasattr(retrieved_results[0], 'uncertainty'):
            uncertainties = [r.uncertainty.total_uncertainty 
                           for r in retrieved_results 
                           if hasattr(r, 'uncertainty') and r.uncertainty]
            if uncertainties:
                uncertainty = sum(uncertainties) / len(uncertainties)
        
        best_answer = None
        best_verification = None
        
        for attempt in range(max_retries + 1):
            try:
                # Generate answer
                if llm_generate_fn:
                    answer = await llm_generate_fn(context, query)
                elif self.answer_composer:
                    # NEW: Use Answer Composer Service
                    log.info("Generating answer with Answer Composer...")
                    answer_response = await self.answer_composer.compose(
                        query=query,
                        context=context,
                        retrieved_results=retrieved_results,
                        style="formal"
                    )
                    answer = answer_response.answer
                    
                    # Add composer metadata
                    if "metadata" not in locals():
                        metadata = {}
                    metadata["composer"] = {
                        "method": answer_response.method,
                        "confidence": answer_response.confidence,
                        "latency": answer_response.latency,
                        "citations": answer_response.citations
                    }
                else:
                    # Fallback: extractive answer (first relevant chunk)
                    answer = self._generate_extractive_answer(query, retrieved_results)
                
                # Verify answer
                verification = await self.verify_answer(
                    answer=answer,
                    context=context,
                    sources=sources,
                    uncertainty=uncertainty
                )
                
                # NEW: Apply policy enforcement
                if self.policy_service:
                    log.info("Applying policy guardrails...")
                    policy_result = await self.policy_service.enforce(
                        content=answer,
                        context={
                            "query": query,
                            "user_id": config.get("user_id") if hasattr(config, "get") else None
                        }
                    )
                    
                    # Use filtered answer
                    answer = policy_result.filtered_content
                    
                    # Add policy metadata
                    if "metadata" not in locals():
                        metadata = {}
                    metadata["policy"] = {
                        "pii_redacted": policy_result.pii_redacted,
                        "content_filtered": policy_result.content_filtered,
                        "violations": len(policy_result.violations)
                    }
                
                # If valid, return immediately
                if verification["is_valid"]:
                    log.info(f"✅ Generated valid answer on attempt {attempt + 1}")
                    response = {
                        "query": query,
                        "answer": answer,
                        "verification": verification,
                        "retrieved_results": retrieved_results,
                        "context": context,
                        "attempt": attempt + 1,
                        "success": True
                    }
                    
                    # Add metadata if available
                    if "metadata" in locals():
                        response["metadata"] = metadata
                    
                    return response
                
                # Keep best attempt
                if best_answer is None or len(verification["warnings"]) < len(best_verification["warnings"]):
                    best_answer = answer
                    best_verification = verification
                
                log.warning(f"⚠️ Attempt {attempt + 1} failed verification: {verification['warnings']}")
                
            except Exception as e:
                log.error(f"Generation attempt {attempt + 1} failed: {e}")
                continue
        
        # All attempts failed, return best attempt with warnings
        log.warning(f"⚠️ All {max_retries + 1} attempts failed verification, returning best attempt")
        return {
            "query": query,
            "answer": best_verification["filtered_answer"] if best_verification else best_answer,
            "verification": best_verification,
            "retrieved_results": retrieved_results,
            "context": context,
            "attempt": max_retries + 1,
            "success": False,
            "fallback": True
        }
    
    def _generate_extractive_answer(
        self,
        query: str,
        results: List[RetrievalResult],
        max_length: int = 500
    ) -> str:
        """
        Generate extractive answer from top results (fallback)
        
        Args:
            query: User query
            results: Retrieved results
            max_length: Maximum answer length
            
        Returns:
            Extractive answer
        """
        if not results:
            return "متأسفانه اطلاعات کافی برای پاسخ به این سوال یافت نشد."
        
        # Take top result as answer
        answer_parts = []
        current_length = 0
        
        for result in results[:3]:
            text = result.text.strip()
            if current_length + len(text) <= max_length:
                answer_parts.append(text)
                current_length += len(text)
            else:
                # Add partial text
                remaining = max_length - current_length
                if remaining > 100:  # Only add if meaningful
                    answer_parts.append(text[:remaining] + "...")
                break
        
        return " ".join(answer_parts)

    async def verify_answer(
        self,
        answer: str,
        context: str,
        sources: Optional[List[str]] = None,
        uncertainty: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Verify answer using all guardrails
        
        NEW: Complete answer verification pipeline
        
        Args:
            answer: Generated answer
            context: Source context
            sources: Source documents
            uncertainty: Uncertainty score
            
        Returns:
            Verification result with all checks
        """
        verification_result = {
            "is_valid": True,
            "nli_check": None,
            "citation_check": None,
            "hallucination_check": None,
            "filtered_answer": answer,
            "warnings": []
        }
        
        try:
            # Check 1: NLI Verification
            if self.nli_verifier:
                log.debug("Running NLI verification...")
                nli_result = self.nli_verifier.verify(context, answer)
                verification_result["nli_check"] = {
                    "is_supported": nli_result.is_supported,
                    "entailment_score": nli_result.entailment_score,
                    "contradiction_score": nli_result.contradiction_score
                }
                
                if not nli_result.is_supported:
                    verification_result["is_valid"] = False
                    verification_result["warnings"].append(
                        f"NLI: Answer not supported by context "
                        f"(entailment={nli_result.entailment_score:.2f})"
                    )
                    log.warning("NLI verification failed")
            
            # Check 2: Citation Auditing
            if self.citation_auditor and sources:
                log.debug("Running citation audit...")
                citation_result = self.citation_auditor.audit(answer, sources)
                verification_result["citation_check"] = {
                    "is_valid": citation_result.is_valid,
                    "accuracy": citation_result.accuracy_score,
                    "total_citations": citation_result.total_citations,
                    "valid_citations": citation_result.valid_citations
                }
                
                if not citation_result.is_valid:
                    verification_result["warnings"].append(
                        f"Citations: {citation_result.valid_citations}/"
                        f"{citation_result.total_citations} valid "
                        f"({citation_result.accuracy_score*100:.1f}%)"
                    )
            
            # Check 3: Hallucination Detection
            if self.hallucination_detector:
                log.debug("Running hallucination detection...")
                halluc_result = self.hallucination_detector.detect(
                    answer, context, uncertainty, sources
                )
                verification_result["hallucination_check"] = {
                    "has_hallucination": halluc_result.has_hallucination,
                    "score": halluc_result.hallucination_score,
                    "confidence": halluc_result.confidence,
                    "detected_count": len(halluc_result.detected_hallucinations)
                }
                
                if halluc_result.has_hallucination:
                    verification_result["is_valid"] = False
                    verification_result["warnings"].append(
                        f"Hallucination detected "
                        f"(score={halluc_result.hallucination_score:.2f})"
                    )
                    log.warning("Hallucination detected")
                    
                    # Filter out hallucinated sentences
                    if halluc_result.detected_hallucinations:
                        # Keep only supported sentences
                        supported, _, _ = self.nli_verifier.verify_sentences(
                            context, answer
                        )
                        verification_result["filtered_answer"] = ". ".join(supported)
            
            # Log summary
            if verification_result["is_valid"]:
                log.info("✅ Answer passed all guardrail checks")
            else:
                log.warning(
                    f"⚠️ Answer failed verification: "
                    f"{len(verification_result['warnings'])} warnings"
                )
            
            return verification_result
            
        except Exception as e:
            log.error(f"Answer verification failed: {e}")
            # Return permissive result on error
            return {
                "is_valid": True,
                "error": str(e),
                "filtered_answer": answer,
                "warnings": ["Verification error - proceeding with caution"]
            }
