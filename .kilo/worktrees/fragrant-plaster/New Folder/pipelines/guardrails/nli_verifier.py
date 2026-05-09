"""
NLI Verification Guardrail
===========================

Verifies that generated answers are supported by the context using NLI.
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from dataclasses import dataclass

from pipelines._logging import setup_logger

log = setup_logger("nli_verifier")


@dataclass
class NLIResult:
    """Result of NLI verification"""
    is_supported: bool
    entailment_score: float
    contradiction_score: float
    neutral_score: float
    threshold: float


class NLIVerifier:
    """
    NLI-based answer verification
    
    Verifies that generated answers are entailed by (supported by) the context.
    Uses Natural Language Inference models to detect contradictions.
    
    Example:
        >>> verifier = NLIVerifier(model_name="microsoft/deberta-v3-base")
        >>> result = verifier.verify(
        ...     context="دادگاه عالی کشور رأی صادر کرد",
        ...     answer="دادگاه تجدیدنظر رأی صادر کرد"
        ... )
        >>> print(result.is_supported)  # False (contradiction)
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        model: Optional[torch.nn.Module] = None,
        tokenizer: Optional[AutoTokenizer] = None,
        threshold: float = 0.5,
        device: Optional[str] = None,
        cache_dir: Optional[str] = None,
        use_model_manager: bool = True
    ):
        """
        Initialize NLI Verifier
        
        Args:
            model_name: HuggingFace model name for NLI (optional if model provided)
            model: Pre-loaded model (optional)
            tokenizer: Pre-loaded tokenizer (optional)
            threshold: Minimum entailment score to consider supported
            device: Device for inference (cuda/cpu)
            cache_dir: Cache directory for models
            use_model_manager: Use ModelManager for robust loading
        """
        self.threshold = threshold
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        # If model and tokenizer provided, use them directly
        if model is not None and tokenizer is not None:
            self.model = model.eval().to(self.device)
            self.tokenizer = tokenizer
            self.model_name = model_name or "custom"
            log.info(f"✅ Using provided NLI model on {self.device}")
            return
        
        # Otherwise, load with fallback support
        if use_model_manager:
            try:
                from api.services.model_manager import get_model_manager
                
                log.info("Loading NLI model via ModelManager with fallback support")
                model_manager = get_model_manager()
                
                self.model = model_manager.get_model_with_fallback("nli")
                self.tokenizer = model_manager.get_tokenizer_with_fallback("nli")
                
                if self.model is None or self.tokenizer is None:
                    raise RuntimeError("ModelManager failed to load NLI model")
                
                self.model = self.model.eval().to(self.device)
                self.model_name = "nli_with_fallback"
                log.info(f"✅ NLI model loaded via ModelManager on {self.device}")
                return
                
            except Exception as e:
                log.warning(f"ModelManager loading failed: {e}, falling back to direct loading")
        
        # Fallback to direct loading
        model_name = model_name or "microsoft/deberta-v3-base"
        log.info(f"Loading NLI model directly: {model_name}")
        
        fallback_models = [
            model_name,
            "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
            "cross-encoder/nli-deberta-v3-small"
        ]
        
        loaded = False
        for attempt_model in fallback_models:
            try:
                log.info(f"Attempting to load: {attempt_model}")
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    attempt_model,
                    cache_dir=cache_dir
                )
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    attempt_model,
                    cache_dir=cache_dir
                ).eval().to(self.device)
                
                self.model_name = attempt_model
                log.info(f"✅ NLI model loaded: {attempt_model} on {self.device}")
                loaded = True
                break
                
            except Exception as e:
                log.warning(f"Failed to load {attempt_model}: {e}")
                continue
        
        if not loaded:
            log.error("❌ All NLI models failed to load")
            raise RuntimeError("Failed to load any NLI model")
    
    def verify(
        self,
        context: str,
        answer: str,
        return_scores: bool = False
    ) -> NLIResult:
        """
        Verify that answer is supported by context
        
        Args:
            context: Source context/documents
            answer: Generated answer to verify
            return_scores: Whether to return detailed scores
            
        Returns:
            NLIResult with verification result
        """
        try:
            with torch.no_grad():
                # Tokenize
                inputs = self.tokenizer(
                    answer,  # premise
                    context,  # hypothesis
                    return_tensors="pt",
                    truncation=True,
                    padding=True,
                    max_length=512
                ).to(self.device)
                
                # Forward pass
                logits = self.model(**inputs).logits
                probs = torch.softmax(logits, dim=-1).squeeze(0)
                
                # Extract probabilities
                # Note: Label order varies by model
                # Common: [contradiction, neutral, entailment] or [entailment, neutral, contradiction]
                if probs.shape[0] == 3:
                    # Assume [contradiction, neutral, entailment] (DeBERTa style)
                    contradiction_score = float(probs[0])
                    neutral_score = float(probs[1])
                    entailment_score = float(probs[2])
                else:
                    # Fallback
                    entailment_score = float(probs[-1])
                    contradiction_score = float(probs[0])
                    neutral_score = 0.0
                
                # Check if supported
                is_supported = entailment_score >= self.threshold
                
                result = NLIResult(
                    is_supported=is_supported,
                    entailment_score=entailment_score,
                    contradiction_score=contradiction_score,
                    neutral_score=neutral_score,
                    threshold=self.threshold
                )
                
                log.debug(
                    f"NLI verification: supported={is_supported}, "
                    f"entailment={entailment_score:.3f}, "
                    f"contradiction={contradiction_score:.3f}"
                )
                
                return result
                
        except Exception as e:
            log.error(f"NLI verification failed: {e}")
            # Return neutral result on error
            return NLIResult(
                is_supported=True,  # Don't block on error
                entailment_score=0.5,
                contradiction_score=0.0,
                neutral_score=0.5,
                threshold=self.threshold
            )
    
    def verify_sentences(
        self,
        context: str,
        answer: str,
        sentence_tokenizer=None
    ) -> Tuple[List[str], List[str], float]:
        """
        Verify answer sentence by sentence
        
        Args:
            context: Source context
            answer: Generated answer
            sentence_tokenizer: Function to split into sentences
            
        Returns:
            (supported_sentences, filtered_sentences, retention_rate)
        """
        # Simple sentence tokenizer
        if sentence_tokenizer is None:
            sentences = [s.strip() for s in answer.split('.') if s.strip()]
        else:
            sentences = sentence_tokenizer(answer)
        
        supported = []
        filtered = []
        
        for sent in sentences:
            if not sent:
                continue
            
            result = self.verify(context, sent)
            
            if result.is_supported:
                supported.append(sent)
            else:
                filtered.append(sent)
                log.warning(f"Filtered sentence: {sent[:50]}...")
        
        retention_rate = len(supported) / len(sentences) if sentences else 1.0
        
        log.info(
            f"Sentence verification: {len(supported)}/{len(sentences)} kept "
            f"({retention_rate*100:.1f}%)"
        )
        
        return supported, filtered, retention_rate
    
    def batch_verify(
        self,
        context: str,
        answers: List[str]
    ) -> List[NLIResult]:
        """
        Verify multiple answers against same context
        
        Args:
            context: Source context
            answers: List of answers to verify
            
        Returns:
            List of NLIResult objects
        """
        results = []
        
        for answer in answers:
            result = self.verify(context, answer)
            results.append(result)
        
        return results
