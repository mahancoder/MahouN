"""
Data Augmentation Module
=========================

Advanced data augmentation techniques for legal documents.
"""

from dataclasses import dataclass, field
from enum import Enum
import random
from typing import List, Optional

# Import the new combined system
from pipelines.labeling.combined_labeling_augmentation import EnhancedIntegratedSystem, AugmentedSample


class AugmentationStrategy(str, Enum):
    """Data augmentation strategies"""
    SYNONYM_REPLACEMENT = "synonym_replacement"
    BACK_TRANSLATION = "back_translation"
    PARAPHRASE = "paraphrase"
    NOISE_INJECTION = "noise_injection"
    ENTITY_REPLACEMENT = "entity_replacement"
    LEGAL_ENTITY_PRESERVING = "legal_entity_preserving"  # New strategy
    CONTEXT_AWARE_PARAPHRASING = "context_aware_paraphrasing"  # New strategy
    CATEGORY_BASED_AUGMENTATION = "category_based_augmentation"  # New strategy


@dataclass
class AugmentedData:
    """Augmented data result"""
    original: str
    augmented: str
    strategy: AugmentationStrategy
    confidence: float = 1.0
    # Additional metadata from the combined system
    quality_score: float = 1.0
    preserved_entities: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)


class DataAugmenter:
    """
    Advanced data augmentation for legal documents
    
    Features:
    - Synonym replacement
    - Back translation
    - Paraphrasing
    - Noise injection
    - Entity replacement
    - Legal entity preserving augmentation (NEW)
    - Context-aware paraphrasing (NEW)
    - Category-based augmentation (NEW)
    """
    
    def __init__(self, strategies: Optional[List[AugmentationStrategy]] = None):
        """
        Initialize data augmenter
        
        Args:
            strategies: List of augmentation strategies to use
        """
        self.strategies = strategies or [
            AugmentationStrategy.SYNONYM_REPLACEMENT,
            AugmentationStrategy.PARAPHRASE,
        ]
        self._init_resources()
        
        # Initialize the new combined system
        self.combined_system = EnhancedIntegratedSystem()
    
    def _init_resources(self):
        """Initialize augmentation resources"""
        # Persian legal synonyms
        self.synonyms = {
            'قانون': ['مقررات', 'آیین‌نامه'],
            'ماده': ['بند', 'تبصره'],
            'محکوم': ['مجرم', 'متهم'],
        }
    
    def augment(self, text: str, num_augmentations: int = 1) -> List[AugmentedData]:
        """
        Augment text data
        
        Args:
            text: Input text
            num_augmentations: Number of augmented versions to generate
            
        Returns:
            List of augmented data
        """
        results = []
        
        for _ in range(num_augmentations):
            strategy = random.choice(self.strategies)
            
            # Use the new combined system for advanced strategies
            if strategy in [AugmentationStrategy.LEGAL_ENTITY_PRESERVING, 
                           AugmentationStrategy.CONTEXT_AWARE_PARAPHRASING,
                           AugmentationStrategy.CATEGORY_BASED_AUGMENTATION]:
                augmented_data = self._use_combined_system(text, strategy)
                results.append(augmented_data)
            else:
                # Use existing strategies
                if strategy == AugmentationStrategy.SYNONYM_REPLACEMENT:
                    augmented = self._synonym_replacement(text)
                elif strategy == AugmentationStrategy.PARAPHRASE:
                    augmented = self._paraphrase(text)
                elif strategy == AugmentationStrategy.NOISE_INJECTION:
                    augmented = self._noise_injection(text)
                else:
                    augmented = text
                
                results.append(AugmentedData(
                    original=text,
                    augmented=augmented,
                    strategy=strategy,
                    confidence=0.8
                ))
        
        return results
    
    def _use_combined_system(self, text: str, strategy: AugmentationStrategy) -> AugmentedData:
        """
        Use the combined system for advanced augmentation strategies
        
        Args:
            text: Input text
            strategy: Augmentation strategy to use
            
        Returns:
            AugmentedData with results from the combined system
        """
        try:
            # Process text with the combined system
            result = self.combined_system.process_text_with_quality_control(text)
            
            # Select an augmentation based on the strategy
            if strategy == AugmentationStrategy.LEGAL_ENTITY_PRESERVING:
                # Use the first augmentation (which preserves entities)
                if result["augmentations"]:
                    aug_sample: AugmentedSample = result["augmentations"][0]
                    augmented_text = aug_sample.augmented_text
                    quality_score = aug_sample.quality_score
                    preserved_entities = [e.text for e in aug_sample.preserved_entities]
                    labels = aug_sample.labels
                else:
                    augmented_text = text
                    quality_score = 0.0
                    preserved_entities = []
                    labels = []
            elif strategy == AugmentationStrategy.CONTEXT_AWARE_PARAPHRASING:
                # Use the paraphrasing augmentation
                paraphrase_aug = None
                for aug in result["augmentations"]:
                    if aug.augmentation_type.name == "PARAPHRASING":
                        paraphrase_aug = aug
                        break
                
                if paraphrase_aug:
                    augmented_text = paraphrase_aug.augmented_text
                    quality_score = paraphrase_aug.quality_score
                    preserved_entities = [e.text for e in paraphrase_aug.preserved_entities]
                    labels = paraphrase_aug.labels
                else:
                    augmented_text = text
                    quality_score = 0.0
                    preserved_entities = []
                    labels = []
            elif strategy == AugmentationStrategy.CATEGORY_BASED_AUGMENTATION:
                # Use the category-based augmentation
                category_aug = None
                for aug in result["augmentations"]:
                    if aug.augmentation_type.name == "CONTEXTUAL_SUBSTITUTION":
                        category_aug = aug
                        break
                
                if category_aug:
                    augmented_text = category_aug.augmented_text
                    quality_score = category_aug.quality_score
                    preserved_entities = [e.text for e in category_aug.preserved_entities]
                    labels = category_aug.labels
                else:
                    augmented_text = text
                    quality_score = 0.0
                    preserved_entities = []
                    labels = []
            else:
                # Fallback
                augmented_text = text
                quality_score = 0.0
                preserved_entities = []
                labels = []
            
            return AugmentedData(
                original=text,
                augmented=augmented_text,
                strategy=strategy,
                confidence=quality_score,
                quality_score=quality_score,
                preserved_entities=preserved_entities,
                labels=labels
            )
        except Exception as e:
            # Fallback in case of error
            return AugmentedData(
                original=text,
                augmented=text,
                strategy=strategy,
                confidence=0.0,
                quality_score=0.0,
                preserved_entities=[],
                labels=[]
            )
    
    def _synonym_replacement(self, text: str) -> str:
        """Replace words with synonyms"""
        words = text.split()
        
        for i, word in enumerate(words):
            if word in self.synonyms and random.random() > 0.5:
                words[i] = random.choice(self.synonyms[word])
        
        return ' '.join(words)
    
    def _paraphrase(self, text: str) -> str:
        """Paraphrase text (simplified version)"""
        # In production, use a paraphrasing model
        return text
    
    def _noise_injection(self, text: str) -> str:
        """Inject noise into text"""
        words = text.split()
        
        # Randomly swap adjacent words
        if len(words) > 2 and random.random() > 0.7:
            i = random.randint(0, len(words) - 2)
            words[i], words[i+1] = words[i+1], words[i]
        
        return ' '.join(words)
    
    def batch_augment(self, texts: List[str], num_augmentations: int = 1) -> List[List[AugmentedData]]:
        """
        Augment multiple texts
        
        Args:
            texts: List of input texts
            num_augmentations: Number of augmentations per text
            
        Returns:
            List of augmented data for each input
        """
        return [self.augment(text, num_augmentations) for text in texts]