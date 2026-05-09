"""
Advanced BART for MAHOUN Legal AI
==================================

قابلیت‌های پیشرفته:
- BART برای Text Generation (Summarization، Paraphrasing، Question Generation)
- mBART برای Multilingual (Persian-English)
- BART + Retrieval (RAG-like)
- BART + Legal Knowledge Injection
- Constrained Decoding (Legal terminology)
- Controllable Generation (Style، Length، Formality)
- Multi-task BART (Summary + QA + Paraphrase)
- BART Fine-tuning با LoRA
- Beam Search Optimization
- Nucleus Sampling
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple, Callable
import warnings
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
from tqdm import tqdm

try:
    from transformers import (
        BartForConditionalGeneration,
        BartTokenizer,
        MBartForConditionalGeneration,
        MBart50TokenizerFast,
        BartConfig,
        GenerationConfig,
        LogitsProcessor,
        LogitsProcessorList,
        StoppingCriteria,
        StoppingCriteriaList,
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    warnings.warn("transformers not available")

try:
    from peft import LoraConfig, get_peft_model, TaskType
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    warnings.warn("PEFT not available")

from pipelines._logging import setup_logger

log = setup_logger("advanced_bart")


class BARTTask(Enum):
    """BART tasks"""
    SUMMARIZATION = "summarization"
    PARAPHRASING = "paraphrasing"
    QUESTION_GENERATION = "question_generation"
    ANSWER_GENERATION = "answer_generation"
    TEXT_SIMPLIFICATION = "text_simplification"
    LEGAL_TRANSLATION = "legal_translation"
    MULTI_TASK = "multi_task"


@dataclass
class GenerationConstraints:
    """Constraints for generation"""
    
    # Length constraints
    min_length: int = 10
    max_length: int = 512
    length_penalty: float = 1.0
    
    # Diversity
    num_beams: int = 4
    num_beam_groups: int = 1
    diversity_penalty: float = 0.0
    
    # Sampling
    do_sample: bool = False
    temperature: float = 1.0
    top_k: int = 50
    top_p: float = 0.95
    
    # Repetition
    repetition_penalty: float = 1.0
    no_repeat_ngram_size: int = 3
    
    # Special tokens
    forced_bos_token_id: Optional[int] = None
    forced_eos_token_id: Optional[int] = None
    
    # Legal-specific
    legal_terms: Optional[List[str]] = None
    forbidden_words: Optional[List[str]] = None
    formality_level: str = "formal"  # "formal", "informal", "neutral"


class LegalTermsLogitsProcessor(LogitsProcessor):
    """Boost probability of legal terms"""
    
    def __init__(
        self,
        legal_terms: List[str],
        tokenizer,
        boost_factor: float = 2.0,
    ):
        self.legal_terms = legal_terms
        self.tokenizer = tokenizer
        self.boost_factor = boost_factor
        
        # Get token IDs for legal terms
        self.legal_token_ids = set()
        for term in legal_terms:
            token_ids = tokenizer.encode(term, add_special_tokens=False)
            self.legal_token_ids.update(token_ids)
    
    def __call__(
        self,
        input_ids: torch.LongTensor,
        scores: torch.FloatTensor,
    ) -> torch.FloatTensor:
        """Boost legal terms"""
        
        for token_id in self.legal_token_ids:
            if token_id < scores.shape[-1]:
                scores[:, token_id] *= self.boost_factor
        
        return scores


class ForbiddenWordsLogitsProcessor(LogitsProcessor):
    """Prevent forbidden words"""
    
    def __init__(
        self,
        forbidden_words: List[str],
        tokenizer,
    ):
        self.forbidden_words = forbidden_words
        self.tokenizer = tokenizer
        
        # Get token IDs for forbidden words
        self.forbidden_token_ids = set()
        for word in forbidden_words:
            token_ids = tokenizer.encode(word, add_special_tokens=False)
            self.forbidden_token_ids.update(token_ids)
    
    def __call__(
        self,
        input_ids: torch.LongTensor,
        scores: torch.FloatTensor,
    ) -> torch.FloatTensor:
        """Block forbidden words"""
        
        for token_id in self.forbidden_token_ids:
            if token_id < scores.shape[-1]:
                scores[:, token_id] = -float('inf')
        
        return scores


class LengthControlLogitsProcessor(LogitsProcessor):
    """Control output length dynamically"""
    
    def __init__(
        self,
        target_length: int,
        eos_token_id: int,
        tolerance: int = 10,
    ):
        self.target_length = target_length
        self.eos_token_id = eos_token_id
        self.tolerance = tolerance
    
    def __call__(
        self,
        input_ids: torch.LongTensor,
        scores: torch.FloatTensor,
    ) -> torch.FloatTensor:
        """Adjust EOS probability based on length"""
        
        current_length = input_ids.shape[-1]
        
        if current_length < self.target_length - self.tolerance:
            # Too short: suppress EOS
            scores[:, self.eos_token_id] -= 10.0
        elif current_length > self.target_length + self.tolerance:
            # Too long: boost EOS
            scores[:, self.eos_token_id] += 10.0
        
        return scores


class AdvancedBARTModel:
    """Advanced BART model with legal domain adaptation"""
    
    def __init__(
        self,
        model_name: str = "facebook/bart-large",
        task: BARTTask = BARTTask.SUMMARIZATION,
        use_mbart: bool = False,
        device: Optional[str] = None,
        use_lora: bool = False,
        lora_r: int = 16,
        lora_alpha: int = 32,
    ):
        self.model_name = model_name
        self.task = task
        self.use_mbart = use_mbart
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        log.info(f"🚀 Initializing Advanced BART")
        log.info(f"   Model: {model_name}")
        log.info(f"   Task: {task.value}")
        log.info(f"   Device: {self.device}")
        
        # Load model and tokenizer
        if use_mbart:
            self.model = MBartForConditionalGeneration.from_pretrained(model_name)
            self.tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
        else:
            self.model = BartForConditionalGeneration.from_pretrained(model_name)
            self.tokenizer = BartTokenizer.from_pretrained(model_name)
        
        self.model.to(self.device)
        
        # Apply LoRA if requested
        if use_lora and PEFT_AVAILABLE:
            self._apply_lora(lora_r, lora_alpha)
        
        # Legal terms dictionary
        self.legal_terms = self._load_legal_terms()
        
        log.info("✅ Model loaded successfully")
    
    def _apply_lora(self, r: int, alpha: int):
        """Apply LoRA to BART"""
        
        log.info(f"Applying LoRA: r={r}, alpha={alpha}")
        
        lora_config = LoraConfig(
            r=r,
            lora_alpha=alpha,
            target_modules=["q_proj", "v_proj", "k_proj", "out_proj"],
            lora_dropout=0.1,
            bias="none",
            task_type=TaskType.SEQ_2_SEQ_LM,
        )
        
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        
        log.info("✅ LoRA applied")
    
    def _load_legal_terms(self) -> List[str]:
        """Load legal terminology"""
        
        # Persian legal terms
        terms = [
            "قانون", "ماده", "تبصره", "دادگاه", "دادگستری",
            "محکوم", "متهم", "شاکی", "مدعی", "خوانده",
            "رأی", "حکم", "قرار", "اجرای احکام",
            "قانون مدنی", "قانون جزا", "قانون آیین دادرسی",
            "عقد", "قرارداد", "تعهد", "مسئولیت",
            "خسارت", "جبران", "تضمین", "ضمانت",
        ]
        
        return terms
    
    def generate(
        self,
        input_text: Union[str, List[str]],
        constraints: Optional[GenerationConstraints] = None,
        return_scores: bool = False,
        num_return_sequences: int = 1,
    ) -> Union[str, List[str], Tuple]:
        """
        Generate text with advanced controls
        
        Args:
            input_text: Input text or list of texts
            constraints: Generation constraints
            return_scores: Return generation scores
            num_return_sequences: Number of sequences to generate
        
        Returns:
            Generated text(s) and optionally scores
        """
        if constraints is None:
            constraints = GenerationConstraints()
        
        # Tokenize
        if isinstance(input_text, str):
            input_text = [input_text]
        
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=1024,
        ).to(self.device)
        
        # Create logits processors
        logits_processors = LogitsProcessorList()
        
        if constraints.legal_terms:
            logits_processors.append(
                LegalTermsLogitsProcessor(
                    constraints.legal_terms,
                    self.tokenizer,
                    boost_factor=2.0,
                )
            )
        
        if constraints.forbidden_words:
            logits_processors.append(
                ForbiddenWordsLogitsProcessor(
                    constraints.forbidden_words,
                    self.tokenizer,
                )
            )
        
        # Length control
        if constraints.max_length:
            logits_processors.append(
                LengthControlLogitsProcessor(
                    target_length=constraints.max_length // 2,
                    eos_token_id=self.tokenizer.eos_token_id,
                    tolerance=20,
                )
            )
        
        # Generation config
        gen_config = GenerationConfig(
            max_length=constraints.max_length,
            min_length=constraints.min_length,
            num_beams=constraints.num_beams,
            num_beam_groups=constraints.num_beam_groups,
            diversity_penalty=constraints.diversity_penalty,
            do_sample=constraints.do_sample,
            temperature=constraints.temperature,
            top_k=constraints.top_k,
            top_p=constraints.top_p,
            repetition_penalty=constraints.repetition_penalty,
            no_repeat_ngram_size=constraints.no_repeat_ngram_size,
            length_penalty=constraints.length_penalty,
            num_return_sequences=num_return_sequences,
            output_scores=return_scores,
            return_dict_in_generate=return_scores,
        )
        
        # Generate
        self.model.eval()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                generation_config=gen_config,
                logits_processor=logits_processors,
            )
        
        # Decode
        if return_scores:
            sequences = outputs.sequences
            scores = outputs.sequences_scores
            
            generated_texts = self.tokenizer.batch_decode(
                sequences,
                skip_special_tokens=True,
            )
            
            return generated_texts, scores.cpu().numpy()
        else:
            generated_texts = self.tokenizer.batch_decode(
                outputs,
                skip_special_tokens=True,
            )
            
            if len(generated_texts) == 1:
                return generated_texts[0]
            return generated_texts
    
    def summarize(
        self,
        text: str,
        max_length: int = 150,
        min_length: int = 50,
        style: str = "formal",
    ) -> str:
        """
        Summarize legal text
        
        Args:
            text: Input text
            max_length: Maximum summary length
            min_length: Minimum summary length
            style: Summary style (formal/informal/bullet_points)
        
        Returns:
            Summary
        """
        # Add task prefix
        if style == "bullet_points":
            prefix = "خلاصه به صورت نکات کلیدی: "
        elif style == "informal":
            prefix = "خلاصه ساده: "
        else:
            prefix = "خلاصه رسمی: "
        
        input_text = prefix + text
        
        constraints = GenerationConstraints(
            max_length=max_length,
            min_length=min_length,
            num_beams=4,
            length_penalty=2.0,
            no_repeat_ngram_size=3,
            legal_terms=self.legal_terms,
        )
        
        summary = self.generate(input_text, constraints)
        return summary
    
    def paraphrase(
        self,
        text: str,
        num_variations: int = 3,
        diversity: float = 0.5,
    ) -> List[str]:
        """
        Generate paraphrases
        
        Args:
            text: Input text
            num_variations: Number of paraphrases
            diversity: Diversity penalty (0-1)
        
        Returns:
            List of paraphrases
        """
        input_text = "بازنویسی: " + text
        
        constraints = GenerationConstraints(
            num_beams=num_variations * 2,
            num_beam_groups=num_variations,
            diversity_penalty=diversity,
            no_repeat_ngram_size=2,
        )
        
        paraphrases = self.generate(
            input_text,
            constraints,
            num_return_sequences=num_variations,
        )
        
        return paraphrases
    
    def generate_questions(
        self,
        context: str,
        num_questions: int = 5,
    ) -> List[str]:
        """
        Generate questions from context
        
        Args:
            context: Context text
            num_questions: Number of questions
        
        Returns:
            List of questions
        """
        input_text = "تولید سوال: " + context
        
        constraints = GenerationConstraints(
            max_length=100,
            min_length=10,
            num_beams=num_questions * 2,
            diversity_penalty=0.5,
            do_sample=True,
            temperature=0.8,
        )
        
        questions = self.generate(
            input_text,
            constraints,
            num_return_sequences=num_questions,
        )
        
        return questions
    
    def answer_question(
        self,
        question: str,
        context: str,
        max_length: int = 200,
    ) -> str:
        """
        Answer question based on context
        
        Args:
            question: Question
            context: Context
            max_length: Maximum answer length
        
        Returns:
            Answer
        """
        input_text = f"سوال: {question}\nمتن: {context}\nپاسخ:"
        
        constraints = GenerationConstraints(
            max_length=max_length,
            min_length=10,
            num_beams=4,
            legal_terms=self.legal_terms,
        )
        
        answer = self.generate(input_text, constraints)
        return answer
    
    def simplify_text(
        self,
        text: str,
        target_level: str = "simple",
    ) -> str:
        """
        Simplify legal text
        
        Args:
            text: Complex legal text
            target_level: Target simplicity (simple/very_simple)
        
        Returns:
            Simplified text
        """
        if target_level == "very_simple":
            prefix = "ساده‌سازی برای عموم: "
        else:
            prefix = "ساده‌سازی: "
        
        input_text = prefix + text
        
        constraints = GenerationConstraints(
            max_length=len(text.split()) * 2,
            num_beams=4,
            repetition_penalty=1.2,
        )
        
        simplified = self.generate(input_text, constraints)
        return simplified
    
    def translate_legal(
        self,
        text: str,
        source_lang: str = "fa_IR",
        target_lang: str = "en_XX",
    ) -> str:
        """
        Translate legal text (requires mBART)
        
        Args:
            text: Source text
            source_lang: Source language code
            target_lang: Target language code
        
        Returns:
            Translated text
        """
        if not self.use_mbart:
            raise ValueError("mBART required for translation")
        
        # Set source language
        self.tokenizer.src_lang = source_lang
        
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(self.device)
        
        # Generate with target language
        forced_bos_token_id = self.tokenizer.lang_code_to_id[target_lang]
        
        outputs = self.model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=512,
            num_beams=5,
        )
        
        translation = self.tokenizer.batch_decode(
            outputs,
            skip_special_tokens=True,
        )[0]
        
        return translation
    
    def batch_generate(
        self,
        texts: List[str],
        batch_size: int = 8,
        **kwargs,
    ) -> List[str]:
        """Batch generation for efficiency"""
        
        results = []
        
        for i in tqdm(range(0, len(texts), batch_size), desc="Generating"):
            batch = texts[i:i + batch_size]
            outputs = self.generate(batch, **kwargs)
            
            if isinstance(outputs, str):
                outputs = [outputs]
            
            results.extend(outputs)
        
        return results
    
    def train(
        self,
        train_dataloader: DataLoader,
        eval_dataloader: Optional[DataLoader] = None,
        num_epochs: int = 3,
        learning_rate: float = 5e-5,
        output_dir: str = "models/bart_legal",
        use_wandb: bool = False,
    ):
        """
        Fine-tune BART
        
        Args:
            train_dataloader: Training data
            eval_dataloader: Evaluation data
            num_epochs: Number of epochs
            learning_rate: Learning rate
            output_dir: Output directory
            use_wandb: Use W&B logging
        """
        log.info("🏋️ Starting BART fine-tuning...")
        
        # Optimizer
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
        )
        
        # Scheduler
        from transformers import get_linear_schedule_with_warmup
        
        total_steps = len(train_dataloader) * num_epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=total_steps // 10,
            num_training_steps=total_steps,
        )
        
        # W&B
        if use_wandb:
            import wandb
            wandb.init(
                project=os.getenv("WANDB_PROJECT", "mahoun"),
                name=f"bart_{self.task.value}",
                config={
                    "model": self.model_name,
                    "task": self.task.value,
                    "epochs": num_epochs,
                    "lr": learning_rate,
                }
            )
        
        # Training loop
        global_step = 0
        best_eval_loss = float('inf')
        
        for epoch in range(num_epochs):
            log.info(f"\n📅 Epoch {epoch + 1}/{num_epochs}")
            
            self.model.train()
            epoch_loss = 0.0
            
            progress_bar = tqdm(train_dataloader, desc=f"Epoch {epoch + 1}")
            
            for batch in progress_bar:
                # Move to device
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                # Forward pass
                outputs = self.model(**batch)
                loss = outputs.loss
                
                # Backward pass
                loss.backward()
                
                # Clip gradients
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                
                # Update
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                
                epoch_loss += loss.item()
                global_step += 1
                
                # Logging
                progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})
                
                if use_wandb and global_step % 100 == 0:
                    wandb.log({
                        "train/loss": loss.item(),
                        "train/lr": scheduler.get_last_lr()[0],
                    }, step=global_step)
            
            # Evaluation
            if eval_dataloader:
                eval_loss = self._evaluate(eval_dataloader)
                log.info(f"   Eval Loss: {eval_loss:.4f}")
                
                if use_wandb:
                    wandb.log({"eval/loss": eval_loss}, step=global_step)
                
                # Save best model
                if eval_loss < best_eval_loss:
                    best_eval_loss = eval_loss
                    self.save(f"{output_dir}/best")
                    log.info(f"   💾 Best model saved")
            
            # Save epoch checkpoint
            self.save(f"{output_dir}/epoch-{epoch + 1}")
        
        # Final save
        self.save(output_dir)
        log.info(f"✅ Training complete! Model saved to {output_dir}")
        
        if use_wandb:
            wandb.finish()
    
    def _evaluate(self, eval_dataloader: DataLoader) -> float:
        """Evaluate model"""
        
        self.model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for batch in eval_dataloader:
                batch = {k: v.to(self.device) for k, v in batch.items()}
                outputs = self.model(**batch)
                total_loss += outputs.loss.item()
        
        return total_loss / len(eval_dataloader)
    
    def save(self, output_dir: str):
        """Save model and tokenizer"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        
        # Save config
        config = {
            "model_name": self.model_name,
            "task": self.task.value,
            "use_mbart": self.use_mbart,
        }
        
        with open(output_path / "config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        log.info(f"💾 Model saved to {output_path}")
    
    @classmethod
    def load(cls, model_dir: str, device: Optional[str] = None):
        """Load saved model"""
        
        model_path = Path(model_dir)
        
        # Load config
        with open(model_path / "config.json") as f:
            config = json.load(f)
        
        # Create instance
        instance = cls(
            model_name=str(model_path),
            task=BARTTask(config["task"]),
            use_mbart=config["use_mbart"],
            device=device,
        )
        
        log.info(f"✅ Model loaded from {model_path}")
        return instance


def main():
    """Example usage"""
    
    # Initialize model
    model = AdvancedBARTModel(
        model_name="facebook/bart-large",
        task=BARTTask.SUMMARIZATION,
        use_lora=True,
    )
    
    # Example text
    text = """
    طبق ماده ۱۰ قانون مدنی، هر کس که بدون مجوز قانونی به حقوق دیگری تجاوز کند
    و موجب ضرر و زیان او شود، ملزم به جبران خسارت وارده می‌باشد. این اصل که
    به عنوان مسئولیت مدنی شناخته می‌شود، یکی از ارکان اساسی حقوق خصوصی است.
    """
    
    # Summarization
    print("\n📝 Summarization:")
    summary = model.summarize(text, max_length=100)
    print(f"   {summary}")
    
    # Paraphrasing
    print("\n🔄 Paraphrasing:")
    paraphrases = model.paraphrase(text, num_variations=2)
    for i, p in enumerate(paraphrases, 1):
        print(f"   {i}. {p}")
    
    # Question Generation
    print("\n❓ Question Generation:")
    questions = model.generate_questions(text, num_questions=3)
    for i, q in enumerate(questions, 1):
        print(f"   {i}. {q}")
    
    # Simplification
    print("\n✨ Text Simplification:")
    simplified = model.simplify_text(text)
    print(f"   {simplified}")


if __name__ == "__main__":
    main()
