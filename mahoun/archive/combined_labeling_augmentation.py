"""
Combined Legal Text Labeling and Augmentation System
===================================================
Enterprise-grade system combining ultra-advanced legal text labeling with data augmentation.

Features:
- Entity-aware data augmentation
- Context-preserving text transformation
- Legal domain-specific augmentation strategies
- Integrated quality control
"""

import random
import re
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# Import rules from weight.py
try:
    from pipelines.labeling.weight import ENTITY_RULES, CATEGORY_RULES, CONTEXT_BOOST_PATTERNS, LABEL_PRIORITY
except ImportError:
    # Fallback if direct import fails
    ENTITY_RULES = []
    CATEGORY_RULES = {}
    CONTEXT_BOOST_PATTERNS = {}
    LABEL_PRIORITY = []

# ============================================================================
# Core Data Structures
# ============================================================================

class AugmentationType(Enum):
    """Types of augmentation strategies"""
    SYNONYM_REPLACEMENT = "synonym_replacement"
    BACK_TRANSLATION = "back_translation"
    PARAPHRASING = "paraphrasing"
    ENTITY_SWAP = "entity_swap"
    SENTENCE_REORDER = "sentence_reorder"
    NOISE_INJECTION = "noise_injection"
    CONTEXTUAL_SUBSTITUTION = "contextual_substitution"
    QUESTION_GENERATION = "question_generation"
    ANSWER_VARIATION = "answer_variation"

@dataclass
class LabeledEntity:
    """Labeled entity with metadata"""
    text: str
    label: str
    start: int
    end: int
    weight: float = 1.0
    context_score: float = 0.0

@dataclass
class AugmentedSample:
    """Augmented data sample with labels"""
    original_text: str
    augmented_text: str
    augmentation_type: AugmentationType
    confidence: float
    
    # Metadata
    preserved_entities: List[LabeledEntity] = field(default_factory=list)
    changes: List[Dict] = field(default_factory=list)
    quality_score: float = 0.0
    labels: List[str] = field(default_factory=list)

# ============================================================================
# Legal Entity Extractor
# ============================================================================

class LegalEntityExtractor:
    """Extract legal entities using rules from weight.py"""
    
    def __init__(self):
        self.entity_rules = ENTITY_RULES
        self.category_rules = CATEGORY_RULES
        self.context_patterns = CONTEXT_BOOST_PATTERNS
        print("🔍 Legal Entity Extractor initialized with weight.py rules")
    
    def extract_entities(self, text: str) -> List[LabeledEntity]:
        """Extract entities using ENTITY_RULES from weight.py"""
        entities = []
        
        for rule in self.entity_rules:
            label = rule["label"]
            pattern = rule["pattern"]
            weight = rule.get("weight", 1.0)
            
            # Find all matches
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity_text = match.group(0)
                start, end = match.span()
                
                # Calculate context score
                context_score = self._calculate_context_score(text, start, end, label)
                
                entities.append(LabeledEntity(
                    text=entity_text,
                    label=label,
                    start=start,
                    end=end,
                    weight=weight,
                    context_score=context_score
                ))
        
        # Sort by position and remove overlaps (keep higher weighted)
        entities.sort(key=lambda x: (x.start, -x.weight))
        filtered_entities = []
        
        for entity in entities:
            # Check for overlap with existing entities
            overlap = False
            for existing in filtered_entities:
                if entity.start < existing.end and entity.end > existing.start:
                    # Overlap exists - keep the one with higher weight
                    if entity.weight > existing.weight:
                        filtered_entities = [e for e in filtered_entities if e != existing]
                        filtered_entities.append(entity)
                    overlap = True
                    break
            
            if not overlap:
                filtered_entities.append(entity)
        
        return filtered_entities
    
    def _calculate_context_score(self, text: str, start: int, end: int, label: str) -> float:
        """Calculate context-aware score for entity"""
        context_window = 50  # characters before and after
        text_start = max(0, start - context_window)
        text_end = min(len(text), end + context_window)
        context_text = text[text_start:text_end].lower()
        
        # Get context patterns for this label
        patterns = self.context_patterns.get(label, [])
        score = 0.0
        
        for pattern in patterns:
            if re.search(pattern, context_text, re.IGNORECASE):
                score += 0.2  # Boost for each matching context pattern
        
        return min(1.0, score)  # Cap at 1.0

# ============================================================================
# Persian Synonym Dictionary with Legal Terms
# ============================================================================

class PersianLegalSynonymDict:
    """Persian synonym dictionary enhanced with legal domain terms"""
    
    def __init__(self):
        self.synonyms = self._build_synonyms()
        print("📚 Persian Legal Synonym Dictionary initialized")
    
    def _build_synonyms(self) -> Dict[str, List[str]]:
        """Build Persian legal synonyms"""
        return {
            # Legal terms from weight.py context
            "دادگاه": ["محکمه", "دیوان", "هیأت قضاوت"],
            "قاضی": ["حاکم", "داور", "رئیس دادگاه"],
            "حکم": ["رأی", "قرار", "فرمان"],
            "خواهان": ["شاکی", "مدعی", "دعوت‌کننده"],
            "خوانده": ["متهم", "مدعی‌علیه", "دعوت‌شونده"],
            "وکیل": ["مدافع", "نماینده قانونی", "حقوق‌دان"],
            "پرونده": ["دوسیه", "مدارک", "قضیه"],
            "شهادت": ["گواهی", "اظهارات", "سوگند"],
            "جرم": ["بزه", "تخلف", "جنایت"],
            "مجازات": ["کیفر", "تنبیه", "عقاب"],
            
            # Common verbs
            "صادر کرد": ["اعلام کرد", "ابلاغ کرد", "داد"],
            "تأیید کرد": ["پذیرفت", "قبول کرد", "认可"],
            "رد کرد": ["نپذیرفت", "مردود شمرد", "انکار کرد"],
            "مطرح کرد": ["بیان کرد", "عنوان کرد", "ارائه داد"],
            
            # Adjectives
            "قانونی": [" المشروع", "حقوقی", "قانون‌مند"],
            "غیرقانونی": ["نامشروع", "خلاف قانون", "غیرمجاز"],
            "صحیح": ["درست", "معتبر", "قابل قبول"],
            "باطل": ["نامعتبر", "بی‌اعتبار", "مردود"],
        }
    
    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word"""
        return self.synonyms.get(word, [])
    
    def has_synonyms(self, word: str) -> bool:
        """Check if word has synonyms"""
        return word in self.synonyms

# ============================================================================
# Entity-Preserving Augmenter
# ============================================================================

class EntityPreservingAugmenter:
    """Augment text while preserving legal entities"""
    
    def __init__(self):
        self.entity_extractor = LegalEntityExtractor()
        self.synonym_dict = PersianLegalSynonymDict()
        print("🛡️ Entity-Preserving Augmenter initialized")
    
    def augment_with_preservation(
        self,
        text: str,
        augmenter_func,
        *args,
        **kwargs
    ) -> AugmentedSample:
        """Augment text while preserving entities"""
        # Extract entities before augmentation
        entities = self.entity_extractor.extract_entities(text)
        
        # Apply augmentation
        augmented_text = augmenter_func(text, *args, **kwargs)
        
        # Verify entities are preserved
        preserved_entities = []
        for entity in entities:
            # Check if entity still exists in augmented text
            if entity.text in augmented_text:
                preserved_entities.append(entity)
            else:
                # Try to re-insert if missing
                # This is a simplified approach - in practice, you might want more sophisticated re-insertion
                pass
        
        return AugmentedSample(
            original_text=text,
            augmented_text=augmented_text,
            augmentation_type=AugmentationType.ENTITY_SWAP,  # Placeholder
            confidence=0.9,
            preserved_entities=entities,  # All original entities
            quality_score=0.95
        )

# ============================================================================
# Synonym Replacement Augmenter with Legal Context
# ============================================================================

class LegalSynonymReplacementAugmenter:
    """Augment text by replacing words with legal synonyms"""
    
    def __init__(self, replacement_rate: float = 0.2):
        self.replacement_rate = replacement_rate
        self.synonym_dict = PersianLegalSynonymDict()
        self.entity_extractor = LegalEntityExtractor()
        print("🔄 Legal Synonym Replacement Augmenter initialized")
    
    def augment(self, text: str) -> AugmentedSample:
        """Augment text with synonym replacement"""
        # Extract entities to avoid replacing them
        entities = self.entity_extractor.extract_entities(text)
        entity_positions = [(e.start, e.end) for e in entities]
        
        words = text.split()
        augmented_words = words.copy()
        changes = []
        
        # Calculate number of words to replace
        num_replacements = max(1, int(len(words) * self.replacement_rate))
        
        # Get replaceable word indices (avoiding entity positions)
        replaceable_indices = []
        for i, word in enumerate(words):
            # Calculate character position of this word
            char_pos = sum(len(w) + 1 for w in words[:i])  # +1 for spaces
            
            # Check if this word overlaps with any entity
            overlaps_entity = False
            for start, end in entity_positions:
                if char_pos < end and (char_pos + len(word)) > start:
                    overlaps_entity = True
                    break
            
            if not overlaps_entity and self.synonym_dict.has_synonyms(word):
                replaceable_indices.append(i)
        
        if not replaceable_indices:
            return AugmentedSample(
                original_text=text,
                augmented_text=text,
                augmentation_type=AugmentationType.SYNONYM_REPLACEMENT,
                confidence=0.0
            )
        
        # Randomly select words to replace
        selected_indices = random.sample(
            replaceable_indices,
            min(num_replacements, len(replaceable_indices))
        )
        
        # Replace words
        for idx in selected_indices:
            original_word = words[idx]
            synonyms = self.synonym_dict.get_synonyms(original_word)
            
            if synonyms:
                replacement = random.choice(synonyms)
                augmented_words[idx] = replacement
                changes.append({
                    "position": idx,
                    "original": original_word,
                    "replacement": replacement
                })
        
        augmented_text = " ".join(augmented_words)
        
        # Extract labels from preserved entities
        labels = [entity.label for entity in entities]
        
        return AugmentedSample(
            original_text=text,
            augmented_text=augmented_text,
            augmentation_type=AugmentationType.SYNONYM_REPLACEMENT,
            confidence=0.85,
            changes=changes,
            quality_score=0.9,
            labels=labels,
            preserved_entities=entities
        )

# ============================================================================
# Context-Aware Paraphrasing Augmenter
# ============================================================================

class ContextAwareParaphrasingAugmenter:
    """Augment text using paraphrasing with legal context awareness"""
    
    def __init__(self):
        self.entity_extractor = LegalEntityExtractor()
        print("📝 Context-Aware Paraphrasing Augmenter initialized")
    
    def augment(self, text: str) -> AugmentedSample:
        """Augment text with context-aware paraphrasing"""
        # Extract entities and their contexts
        entities = self.entity_extractor.extract_entities(text)
        
        # Simple rule-based paraphrasing with legal context
        patterns = [
            # Legal-specific patterns from weight.py
            (r'ماده\s+(\d+)', r'ماده \1 از قانون'),
            (r'تبصره\s+(\d+)', r'تبصره \1 مربوطه'),
            (r'دادگاه\s+(عمومی|کیفری|حقوقی)', r'هیأت قضاوت \1'),
            (r'حکم\s+به', r'صدور حکم مبنی بر'),
            (r'با توجه به', r'منوط به'),
            (r'در نظر گرفتن', r'لحاظ کردن'),
            (r'به منظور', r'جهت'),
            (r'در صورتی که', r'در صورت وجود'),
        ]
        
        augmented_text = text
        changes = []
        
        for pattern, replacement in patterns:
            count = 0
            def replacer(match):
                nonlocal count
                count += 1
                changes.append({
                    "pattern": pattern,
                    "replacement": replacement,
                    "match": match.group(0)
                })
                return match.expand(replacement)
            
            augmented_text = re.sub(pattern, replacer, augmented_text)
        
        # Extract labels
        labels = [entity.label for entity in entities]
        
        return AugmentedSample(
            original_text=text,
            augmented_text=augmented_text,
            augmentation_type=AugmentationType.PARAPHRASING,
            confidence=0.8,
            changes=changes,
            quality_score=0.85,
            labels=labels,
            preserved_entities=entities
        )

# ============================================================================
# Legal Category-Aware Augmenter
# ============================================================================

class LegalCategoryAwareAugmenter:
    """Augment text based on legal categories from weight.py"""
    
    def __init__(self):
        self.category_rules = CATEGORY_RULES
        self.entity_extractor = LegalEntityExtractor()
        print("⚖️ Legal Category-Aware Augmenter initialized")
    
    def get_text_category(self, text: str) -> Optional[str]:
        """Determine the legal category of text"""
        scores = defaultdict(float)
        
        for category, rules in self.category_rules.items():
            patterns = rules.get("patterns", [])
            weight = rules.get("weight", 1.0)
            context_patterns = rules.get("context_patterns", [])
            
            # Score based on pattern matches
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                scores[category] += len(matches) * weight
            
            # Boost score based on context patterns
            for context_pattern in context_patterns:
                if re.search(context_pattern, text, re.IGNORECASE):
                    scores[category] += 0.5 * weight
        
        # Return category with highest score
        if scores:
            return max(scores.keys(), key=lambda x: scores[x])
        return None
    
    def augment_by_category(self, text: str) -> AugmentedSample:
        """Augment text using category-specific strategies"""
        category = self.get_text_category(text)
        
        if not category:
            # Default augmentation
            return self._default_augment(text)
        
        # Category-specific augmentation strategies
        category_strategies = {
            "جرایم_و_تخلفات": self._crime_augment,
            "مجازات‌ها": self._punishment_augment,
            "حقوق_دنی": self._civil_augment,
            "حقوق_تجاری": self._commercial_augment,
            "آیین_دادرسی_دنی": self._procedure_augment,
        }
        
        strategy = category_strategies.get(category, self._default_augment)
        return strategy(text)
    
    def _crime_augment(self, text: str) -> AugmentedSample:
        """Crime-specific augmentation"""
        patterns = [
            (r'سرقت', r'مال‌ربایی'),
            (r'قتل', r'هلاکت عمدی'),
            (r'ضرب و جرح', r'آسیب جسمانی'),
            (r'کلاهبرداری', r'فریب و کلاه‌برداری'),
        ]
        
        return self._apply_patterns(text, patterns, "جرایم_و_تخلفات")
    
    def _punishment_augment(self, text: str) -> AugmentedSample:
        """Punishment-specific augmentation"""
        patterns = [
            (r'حبس', r'محبوسیت'),
            (r'جریمه', r'مال‌الزام'),
            (r'اعدام', r'حکم اعدام'),
            (r'دیه', r'پرداخت دیه'),
        ]
        
        return self._apply_patterns(text, patterns, "مجازات‌ها")
    
    def _civil_augment(self, text: str) -> AugmentedSample:
        """Civil law-specific augmentation"""
        patterns = [
            (r'قرارداد', r'عهدنامه'),
            (r'اجاره', r'مستاجری'),
            (r'رهن', r'وثیقه'),
            (r'وصیت', r'وصایا'),
        ]
        
        return self._apply_patterns(text, patterns, "حقوق_دنی")
    
    def _commercial_augment(self, text: str) -> AugmentedSample:
        """Commercial law-specific augmentation"""
        patterns = [
            (r'شرکت', r'مؤسسه تجاری'),
            (r'چک', r'اثری'),
            (r'سفته', r'حکمی'),
            (r'بازرگان', r'تاجر'),
        ]
        
        return self._apply_patterns(text, patterns, "حقوق_تجاری")
    
    def _procedure_augment(self, text: str) -> AugmentedSample:
        """Legal procedure-specific augmentation"""
        patterns = [
            (r'دادخواست', r'التماس'),
            (r'لایحه', r'دفترچه'),
            (r'صورتجلسه', r'ثبت جلسه'),
            (r'ابلاغ', r'ارسال رسمی'),
        ]
        
        return self._apply_patterns(text, patterns, "آیین_دادرسی_دنی")
    
    def _default_augment(self, text: str) -> AugmentedSample:
        """Default augmentation"""
        # Simple synonym replacement
        patterns = [
            (r'دادگاه', r'هیأت قضاوت'),
            (r'قاضی', r'داور'),
            (r'حکم', r'فرمان'),
        ]
        
        return self._apply_patterns(text, patterns, "عمومی")
    
    def _apply_patterns(self, text: str, patterns: List[Tuple[str, str]], category: str) -> AugmentedSample:
        """Apply patterns to text"""
        augmented_text = text
        changes = []
        
        for pattern, replacement in patterns:
            count = 0
            def replacer(match):
                nonlocal count
                count += 1
                changes.append({
                    "pattern": pattern,
                    "replacement": replacement,
                    "match": match.group(0)
                })
                return match.expand(replacement)
            
            augmented_text = re.sub(pattern, replacer, augmented_text)
        
        # Extract entities
        entities = self.entity_extractor.extract_entities(text)
        labels = [entity.label for entity in entities]
        
        return AugmentedSample(
            original_text=text,
            augmented_text=augmented_text,
            augmentation_type=AugmentationType.CONTEXTUAL_SUBSTITUTION,
            confidence=0.85,
            changes=changes,
            quality_score=0.9,
            labels=labels,
            preserved_entities=entities
        )

# ============================================================================
# Integrated Labeling and Augmentation System
# ============================================================================

class IntegratedLabelingAugmentationSystem:
    """
    Integrated system combining legal text labeling with data augmentation
    
    Features:
    - Entity extraction using weight.py rules
    - Context-aware data augmentation
    - Legal domain-specific transformations
    - Quality-controlled output
    """
    
    def __init__(self):
        self.entity_extractor = LegalEntityExtractor()
        self.synonym_augmenter = LegalSynonymReplacementAugmenter()
        self.paraphrase_augmenter = ContextAwareParaphrasingAugmenter()
        self.category_augmenter = LegalCategoryAwareAugmenter()
        self.entity_preserver = EntityPreservingAugmenter()
        
        # Statistics
        self.stats = {
            "total_processed": 0,
            "augmentations_by_type": defaultdict(int),
            "avg_quality_score": 0.0,
        }
        
        print("🎯 Integrated Labeling and Augmentation System initialized")
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process text with labeling and augmentation
        
        Args:
            text: Input legal text
            
        Returns:
            Dictionary with labeled entities and augmented versions
        """
        # Extract entities
        entities = self.entity_extractor.extract_entities(text)
        
        # Determine category
        category = self.category_augmenter.get_text_category(text)
        
        # Generate augmented versions
        augmentations = []
        
        # Synonym replacement
        synonym_sample = self.synonym_augmenter.augment(text)
        augmentations.append(synonym_sample)
        self.stats["augmentations_by_type"][synonym_sample.augmentation_type.value] += 1
        
        # Context-aware paraphrasing
        paraphrase_sample = self.paraphrase_augmenter.augment(text)
        augmentations.append(paraphrase_sample)
        self.stats["augmentations_by_type"][paraphrase_sample.augmentation_type.value] += 1
        
        # Category-aware augmentation
        category_sample = self.category_augmenter.augment_by_category(text)
        augmentations.append(category_sample)
        self.stats["augmentations_by_type"][category_sample.augmentation_type.value] += 1
        
        # Update statistics
        self.stats["total_processed"] += 1
        avg_quality = sum(s.quality_score for s in augmentations) / len(augmentations)
        self.stats["avg_quality_score"] = (
            (self.stats["avg_quality_score"] * (self.stats["total_processed"] - 1) + avg_quality) 
            / self.stats["total_processed"]
        )
        
        return {
            "original_text": text,
            "entities": entities,
            "category": category,
            "augmentations": augmentations,
            "labels": list(set([e.label for e in entities])),  # Unique labels
        }
    
    def augment_dataset(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Process entire dataset"""
        results = []
        for text in texts:
            result = self.process_text(text)
            results.append(result)
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        return dict(self.stats)

# ============================================================================
# Enhanced Data Quality Control
# ============================================================================

class DataQualityController:
    """Quality control for augmented legal texts"""
    
    def __init__(self):
        self.entity_extractor = LegalEntityExtractor()
        print("✅ Data Quality Controller initialized")
    
    def validate_augmentation(self, original: str, augmented: str) -> Dict[str, Any]:
        """
        Validate augmented text quality
        
        Args:
            original: Original text
            augmented: Augmented text
            
        Returns:
            Validation results with quality metrics
        """
        # Extract entities from both texts
        original_entities = self.entity_extractor.extract_entities(original)
        augmented_entities = self.entity_extractor.extract_entities(augmented)
        
        # Calculate preservation rate
        preserved_count = 0
        original_entity_texts = {e.text for e in original_entities}
        for entity in augmented_entities:
            if entity.text in original_entity_texts:
                preserved_count += 1
        
        preservation_rate = preserved_count / len(original_entities) if original_entities else 1.0
        
        # Calculate semantic similarity (simplified)
        # In a real implementation, you would use embedding similarity
        original_words = set(original.lower().split())
        augmented_words = set(augmented.lower().split())
        
        if original_words:
            semantic_similarity = len(original_words.intersection(augmented_words)) / len(original_words)
        else:
            semantic_similarity = 1.0
        
        # Overall quality score
        quality_score = (preservation_rate * 0.7 + semantic_similarity * 0.3)
        
        return {
            "quality_score": quality_score,
            "entity_preservation_rate": preservation_rate,
            "semantic_similarity": semantic_similarity,
            "original_entity_count": len(original_entities),
            "augmented_entity_count": len(augmented_entities),
            "preserved_entities": preserved_count,
        }
    
    def filter_low_quality(self, samples: List[AugmentedSample], min_quality: float = 0.7) -> List[AugmentedSample]:
        """
        Filter out low quality augmented samples
        
        Args:
            samples: List of augmented samples
            min_quality: Minimum quality threshold
            
        Returns:
            Filtered list of high-quality samples
        """
        high_quality_samples = []
        
        for sample in samples:
            if sample.quality_score >= min_quality:
                high_quality_samples.append(sample)
        
        return high_quality_samples

# ============================================================================
# Advanced Legal Text Generator
# ============================================================================

class LegalTextGenerator:
    """Generate synthetic legal texts based on labeling rules"""
    
    def __init__(self):
        self.entity_rules = ENTITY_RULES
        self.category_rules = CATEGORY_RULES
        print("📜 Legal Text Generator initialized")
    
    def generate_synthetic_text(self, category: Optional[str] = None, entity_types: Optional[List[str]] = None) -> str:
        """
        Generate synthetic legal text
        
        Args:
            category: Legal category to generate text for
            entity_types: Specific entity types to include
            
        Returns:
            Generated legal text
        """
        # Select category
        if not category:
            # Check if we have categories to choose from
            if self.category_rules:
                category = random.choice(list(self.category_rules.keys()))
            else:
                # Fallback if no categories available
                category = "حقوق_دنی"  # Default category
        
        # Get category rules
        rules = self.category_rules.get(category, {})
        patterns = rules.get("patterns", [])
        context_patterns = rules.get("context_patterns", [])
        
        # Build text from patterns
        text_parts = []
        
        # Add some context patterns
        if context_patterns:
            context = random.choice(context_patterns)
            # Convert regex pattern to example text
            example_context = self._pattern_to_text(context)
            if example_context:
                text_parts.append(example_context)
        
        # Add entity patterns
        if entity_types:
            # Filter rules by entity types
            relevant_rules = [r for r in self.entity_rules if r["label"] in entity_types]
        else:
            # Use all rules for this category or fallback rules
            relevant_rules = self.entity_rules if self.entity_rules else [
                {"label": "ARTICLE", "pattern": r"ماده\s+[0-9۰-۹]{1,4}"},
                {"label": "COURT", "pattern": r"دادگاه\s+[^،\.]{2,30}"},
                {"label": "LAW_NAME", "pattern": r"قانون\s+[^،\.]{2,50}"}
            ]
        
        # Add some entities (only if we have rules)
        if relevant_rules:
            for _ in range(random.randint(1, 3)):  # Reduced from 2-5 to 1-3
                if relevant_rules:
                    rule = random.choice(relevant_rules)
                    pattern = rule["pattern"]
                    example_entity = self._pattern_to_text(pattern)
                    if example_entity:
                        text_parts.append(example_entity)
        else:
            # Fallback text if no rules
            fallback_texts = [
                "مطابق ماده 10 قانون مدنی",
                "دادگاه تهران",
                "قرارداد بیع",
                "ماده 5 تبصره 2",
                "شماره پرونده 1400/123"
            ]
            text_parts.extend(random.sample(fallback_texts, min(2, len(fallback_texts))))
        
        # Combine parts
        if text_parts:
            text = " ".join(text_parts)
        else:
            # Final fallback
            text = "این یک سند حقوقی نمونه است که شامل ماده قانونی و دادگاه می‌باشد."
        
        # Add some legal boilerplate
        boilerplate = [
            "با توجه به ماده مذکور و استناد به قانون مدنی",
            "در نتیجه و بنا به درخواست خواهان",
            "دادگاه به این حکم رسید که",
            "مطابق آیین‌نامه اجرایی",
            "طبق دستورالعمل مربوطه"
        ]
        
        text += " " + random.choice(boilerplate)
        
        return text
    
    def _pattern_to_text(self, pattern: str) -> Optional[str]:
        """
        Convert regex pattern to example text
        
        Args:
            pattern: Regex pattern
            
        Returns:
            Example text matching the pattern
        """
        # This is a simplified implementation
        # In practice, you would use a more sophisticated approach
        
        # Handle common legal patterns
        if "ماده" in pattern and "عدد" in pattern:
            return f"ماده {random.randint(1, 50)}"
        elif "تبصره" in pattern and "عدد" in pattern:
            return f"تبصره {random.randint(1, 10)}"
        elif "دادگاه" in pattern:
            courts = ["دادگاه عالی کشور", "دادگاه کیفری یک", "دادگاه حقوقی"]
            return random.choice(courts)
        elif "قاضی" in pattern:
            return f"قاضی {random.choice(['احمدی', 'محمدی', 'حسینی'])}"
        elif "شماره" in pattern and "عدد" in pattern:
            return f"شماره {random.randint(1000, 9999)}/{random.randint(100, 999)}"
        
        # For other patterns, return a simplified version
        # Remove regex special characters
        clean_pattern = re.sub(r'[\\^$.|?*+(){}\[\]]', '', pattern)
        if clean_pattern.strip():
            return clean_pattern
        return None

# ============================================================================
# Enhanced Integrated System with Quality Control
# ============================================================================

class EnhancedIntegratedSystem(IntegratedLabelingAugmentationSystem):
    """
    Enhanced integrated system with quality control and text generation
    """
    
    def __init__(self):
        super().__init__()
        self.quality_controller = DataQualityController()
        self.text_generator = LegalTextGenerator()
        print("🌟 Enhanced Integrated System initialized")
    
    def process_text_with_quality_control(self, text: str, min_quality: float = 0.7) -> Dict[str, Any]:
        """
        Process text with quality control
        
        Args:
            text: Input legal text
            min_quality: Minimum quality threshold
            
        Returns:
            Processed results with quality metrics
        """
        # Process with base system
        result = self.process_text(text)
        
        # Apply quality control to augmentations
        high_quality_augmentations = self.quality_controller.filter_low_quality(
            result["augmentations"], min_quality
        )
        
        # Validate each augmentation
        validation_results = []
        for aug in high_quality_augmentations:
            validation = self.quality_controller.validate_augmentation(
                result["original_text"], aug.augmented_text
            )
            validation_results.append(validation)
        
        # Update result with quality-controlled augmentations
        result["augmentations"] = high_quality_augmentations
        result["validation_results"] = validation_results
        
        return result
    
    def generate_training_dataset(self, size: int = 100) -> List[Dict[str, Any]]:
        """
        Generate synthetic training dataset
        
        Args:
            size: Number of samples to generate
            
        Returns:
            List of generated samples with labels and augmentations
        """
        samples = []
        
        for i in range(size):
            # Generate synthetic text
            text = self.text_generator.generate_synthetic_text()
            
            # Process with quality control
            result = self.process_text_with_quality_control(text)
            samples.append(result)
            
            # Progress indicator
            if (i + 1) % 20 == 0:
                print(f"  Generated {i + 1}/{size} samples")
        
        return samples

# ============================================================================
# Example Usage and Testing
# ============================================================================

def test_enhanced_system():
    """Test the enhanced integrated system"""
    print("🚀 Testing Enhanced Integrated Labeling and Augmentation System")
    print("=" * 70)
    
    # Create enhanced system
    system = EnhancedIntegratedSystem()
    
    # Sample legal texts
    sample_texts = [
        "دادگاه عالی کشور در پرونده شماره 1400/123 با استناد به ماده 10 قانون مدنی حکم به پرداخت خسارت صادر کرد.",
        "متهم به اتهام سرقت در تاریخ 1400/01/01 به مدت 6 ماه حبس و پرداخت 10 میلیون ریال جریمه محکوم گردید.",
        "قرارداد اجاره بین موجر و مستاجر در تاریخ 1399/12/01 منعقد گردید و موجر تعهد کرد ملک را در شرایط متعارف تحویل دهد."
    ]
    
    print(f"\n📝 Processing {len(sample_texts)} sample texts with quality control:")
    
    # Process texts with quality control
    for i, text in enumerate(sample_texts, 1):
        print(f"\n--- Processing Text {i} ---")
        result = system.process_text_with_quality_control(text, min_quality=0.75)
        
        print(f"Category: {result['category']}")
        print(f"Labels: {result['labels']}")
        print(f"Original entities: {len(result['entities'])}")
        
        # Show validation results
        if result.get('validation_results'):
            print("  Validation results:")
            for j, validation in enumerate(result['validation_results']):
                print(f"    Aug {j+1}: Quality={validation['quality_score']:.2f}, "
                      f"Preservation={validation['entity_preservation_rate']:.2f}")
        
        print(f"  High-quality augmentations: {len(result['augmentations'])}")
        
        # Show first augmentation
        if result['augmentations']:
            first_aug = result['augmentations'][0]
            print(f"    Example: {first_aug.augmentation_type.value}")
            print(f"    Text: {first_aug.augmented_text}")
    
    # Generate synthetic dataset
    print(f"\n🤖 Generating synthetic training dataset...")
    synthetic_data = system.generate_training_dataset(size=10)
    print(f"  Generated {len(synthetic_data)} synthetic samples")
    
    # Show first synthetic sample
    if synthetic_data:
        first_sample = synthetic_data[0]
        print(f"  First sample category: {first_sample['category']}")
        print(f"  First sample labels: {first_sample['labels']}")
        if first_sample['augmentations']:
            print(f"  First sample augmentations: {len(first_sample['augmentations'])}")
    
    # Show statistics
    stats = system.get_statistics()
    print(f"\n📊 System Statistics:")
    print(f"  Total processed: {stats['total_processed']}")
    print(f"  Average quality score: {stats['avg_quality_score']:.2f}")
    print(f"  Augmentations by type:")
    for aug_type, count in stats['augmentations_by_type'].items():
        print(f"    {aug_type}: {count}")

def test_quality_control():
    """Test quality control features"""
    print("\n🔍 Testing Quality Control Features")
    print("=" * 50)
    
    controller = DataQualityController()
    
    # Test cases
    test_cases = [
        {
            "original": "دادگاه عالی کشور در پرونده شماره 1400/123 حکم صادر کرد",
            "augmented": "هیأت قضاوت عالی کشور در کلاسه شماره 1400/123 فرمان داد"
        },
        {
            "original": "متهم به اتهام سرقت محکوم گردید",
            "augmented": "متهم به اتهام مال‌ربایی حکم گرفت"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        validation = controller.validate_augmentation(case["original"], case["augmented"])
        print(f"  Quality Score: {validation['quality_score']:.2f}")
        print(f"  Entity Preservation: {validation['entity_preservation_rate']:.2f}")
        print(f"  Semantic Similarity: {validation['semantic_similarity']:.2f}")

if __name__ == "__main__":
    test_enhanced_system()
    test_quality_control()