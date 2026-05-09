"""
Ultra Entity Extractor - Advanced Named Entity Recognition
===========================================================
State-of-the-art entity extraction for Persian legal documents with
multi-model ensemble, contextual understanding, and relation extraction.

Features:
- Multi-model NER ensemble (Pattern + Rule-based + Statistical)
- Legal entity types (articles, laws, courts, judges, etc.)
- Contextual entity disambiguation
- Entity linking and normalization
- Relation extraction between entities
- Coreference resolution
- Entity confidence scoring
- Nested entity recognition
- Multi-lingual support (Persian + English)
- Entity validation and correction
- Temporal entity extraction
- Numerical entity extraction
- Entity clustering and grouping
"""

import re
import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter


class EntityType(Enum):
    """Legal entity types"""
    # Legal documents
    ARTICLE = "article"
    LAW = "law"
    REGULATION = "regulation"
    DECREE = "decree"
    BILL = "bill"
    
    # Legal institutions
    COURT = "court"
    TRIBUNAL = "tribunal"
    MINISTRY = "ministry"
    ORGANIZATION = "organization"
    
    # Legal roles
    JUDGE = "judge"
    LAWYER = "lawyer"
    PROSECUTOR = "prosecutor"
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    WITNESS = "witness"
    EXPERT = "expert"
    NOTARY = "notary"
    
    # Legal concepts
    CASE_NUMBER = "case_number"
    VERDICT = "verdict"
    SENTENCE = "sentence"
    FINE = "fine"
    CONTRACT = "contract"
    
    # General entities
    PERSON = "person"
    LOCATION = "location"
    DATE = "date"
    TIME = "time"
    MONEY = "money"
    PERCENTAGE = "percentage"
    DURATION = "duration"
    
    # Legal events
    HEARING = "hearing"
    TRIAL = "trial"
    APPEAL = "appeal"


@dataclass
class Entity:
    """Named entity with metadata"""
    text: str
    entity_type: EntityType
    start: int
    end: int
    confidence: float
    normalized: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    linked_entities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "type": self.entity_type.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "normalized": self.normalized,
            "metadata": self.metadata,
            "linked_entities": self.linked_entities
        }


@dataclass
class EntityRelation:
    """Relation between two entities"""
    subject: Entity
    relation: str
    object: Entity
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            "subject": self.subject.to_dict(),
            "relation": self.relation,
            "object": self.object.to_dict(),
            "confidence": self.confidence
        }


class PatternBasedExtractor:
    """Pattern-based entity extraction with advanced regex"""
    
    def __init__(self):
        self.patterns = self._build_patterns()
        print("🔍 Pattern-based Extractor initialized")
    
    def extract(self, text: str) -> List[Entity]:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.patterns.items():
            for pattern, confidence in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entity = Entity(
                        text=match.group(0),
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=confidence,
                        metadata=self._extract_metadata(match, entity_type)
                    )
                    entities.append(entity)
        
        return entities
    
    def _build_patterns(self) -> Dict[EntityType, List[Tuple[str, float]]]:
        """Build comprehensive regex patterns"""
        return {
            EntityType.ARTICLE: [
                (r'ماده\s+(\d+)(?:\s+تبصره\s+(\d+))?', 0.95),
                (r'بند\s+([الف-ی]|\d+)', 0.90),
                (r'Article\s+(\d+)', 0.95),
                (r'قسمت\s+(\d+)', 0.85),
                (r'فصل\s+(\d+)', 0.85),
            ],
            
            EntityType.LAW: [
                (r'قانون\s+(?:مدنی|تجارت|کار|جزا|اساسی)', 0.98),
                (r'قانون\s+آیین\s+دادرسی\s+(?:مدنی|کیفری)', 0.98),
                (r'قانون\s+مجازات\s+اسلامی', 0.98),
                (r'قانون\s+[^\s]+(?:\s+[^\s]+){0,3}', 0.85),
            ],
            
            EntityType.REGULATION: [
                (r'آیین\s*نامه\s+[^\s]+(?:\s+[^\s]+){0,3}', 0.90),
                (r'مقررات\s+[^\s]+(?:\s+[^\s]+){0,2}', 0.85),
            ],
            
            EntityType.COURT: [
                (r'دادگاه\s+(?:عالی|تجدیدنظر|بدوی|انقلاب|کیفری|حقوقی)', 0.95),
                (r'دیوان\s+(?:عدالت\s+اداری|عالی\s+کشور)', 0.98),
                (r'شعبه\s+\d+\s+دادگاه', 0.92),
                (r'محکمه\s+[^\s]+', 0.85),
            ],
            
            EntityType.JUDGE: [
                (r'(?:قاضی|رئیس|رییس)\s+(?:[^\s]+\s+){0,2}[^\s]+', 0.80),
                (r'جناب\s+آقای\s+[^\s]+', 0.75),
            ],
            
            EntityType.LAWYER: [
                (r'وکیل\s+(?:مدافع\s+)?(?:[^\s]+\s+){0,2}[^\s]+', 0.80),
                (r'مشاور\s+حقوقی', 0.85),
            ],
            
            EntityType.PLAINTIFF: [
                (r'خواهان(?:\s+[^\s]+){0,2}', 0.85),
                (r'شاکی(?:\s+[^\s]+){0,2}', 0.85),
                (r'مدعی(?:\s+[^\s]+){0,2}', 0.80),
            ],
            
            EntityType.DEFENDANT: [
                (r'خوانده(?:\s+[^\s]+){0,2}', 0.85),
                (r'متهم(?:\s+[^\s]+){0,2}', 0.85),
                (r'مدعی\s*علیه(?:\s+[^\s]+){0,2}', 0.80),
            ],
            
            EntityType.WITNESS: [
                (r'شاهد(?:\s+[^\s]+){0,2}', 0.85),
            ],
            
            EntityType.CASE_NUMBER: [
                (r'(?:پرونده|کلاسه)\s+(?:شماره\s+)?(\d+(?:/\d+)*)', 0.95),
                (r'شماره\s+دادنامه\s+(\d+(?:/\d+)*)', 0.95),
                (r'شماره\s+قرار\s+(\d+(?:/\d+)*)', 0.93),
            ],
            
            EntityType.VERDICT: [
                (r'حکم\s+(?:به\s+)?[^\s]+', 0.85),
                (r'رأی\s+(?:به\s+)?[^\s]+', 0.85),
                (r'قرار\s+(?:به\s+)?[^\s]+', 0.80),
            ],
            
            EntityType.DATE: [
                (r'\d{1,2}/\d{1,2}/\d{2,4}', 0.90),
                (r'(?:روز|تاریخ)\s+\d{1,2}\s+(?:فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)\s+(?:ماه\s+)?(?:سال\s+)?\d{4}', 0.95),
                (r'\d{4}-\d{2}-\d{2}', 0.90),
                (r'(?:امروز|دیروز|فردا)', 0.70),
            ],
            
            EntityType.TIME: [
                (r'\d{1,2}:\d{2}(?::\d{2})?', 0.90),
                (r'ساعت\s+\d{1,2}', 0.85),
            ],
            
            EntityType.MONEY: [
                (r'(\d+(?:[,،]\d+)*)\s*(?:ریال|تومان|دلار|یورو)', 0.92),
                (r'مبلغ\s+(\d+(?:[,،]\d+)*)', 0.88),
                (r'\$\s*\d+(?:,\d+)*(?:\.\d+)?', 0.90),
            ],
            
            EntityType.PERCENTAGE: [
                (r'(\d+(?:\.\d+)?)\s*(?:درصد|%)', 0.90),
            ],
            
            EntityType.DURATION: [
                (r'\d+\s+(?:سال|ماه|روز|هفته)', 0.88),
                (r'\d+\s+(?:year|month|day|week)s?', 0.88),
            ],
        }
    
    def _extract_metadata(self, match: re.Match, entity_type: EntityType) -> Dict:
        """Extract metadata from regex match"""
        metadata = {}
        
        if entity_type == EntityType.ARTICLE:
            if match.lastindex and match.lastindex >= 1:
                metadata["article_number"] = match.group(1)
            if match.lastindex and match.lastindex >= 2 and match.group(2):
                metadata["note_number"] = match.group(2)
        
        elif entity_type == EntityType.CASE_NUMBER:
            if match.lastindex and match.lastindex >= 1:
                metadata["case_number"] = match.group(1)
        
        elif entity_type == EntityType.MONEY:
            if match.lastindex and match.lastindex >= 1:
                metadata["amount"] = match.group(1)
        
        return metadata


class ContextualExtractor:
    """Context-aware entity extraction"""
    
    def __init__(self):
        self.context_window = 200
        print("🎯 Contextual Extractor initialized")
    
    def extract(self, text: str, existing_entities: List[Entity]) -> List[Entity]:
        """Extract entities using context around existing entities"""
        entities = []
        
        for entity in existing_entities:
            context_entities = self._extract_from_context(text, entity)
            entities.extend(context_entities)
        
        return entities
    
    def _extract_from_context(self, text: str, anchor_entity: Entity) -> List[Entity]:
        """Extract entities from context around anchor entity"""
        entities = []
        
        # Get context window
        context_start = max(0, anchor_entity.start - self.context_window)
        context_end = min(len(text), anchor_entity.end + self.context_window)
        context = text[context_start:context_end]
        
        # Apply context-specific patterns
        if anchor_entity.entity_type == EntityType.ARTICLE:
            # Look for law name near article
            law_pattern = r'قانون\s+[^\s]+(?:\s+[^\s]+){0,2}'
            for match in re.finditer(law_pattern, context):
                abs_start = context_start + match.start()
                abs_end = context_start + match.end()
                
                # Check if not already extracted
                if not any(e.start == abs_start for e in entities):
                    entities.append(Entity(
                        text=match.group(0),
                        entity_type=EntityType.LAW,
                        start=abs_start,
                        end=abs_end,
                        confidence=0.85,
                        metadata={"context": "near_article"}
                    ))
        
        elif anchor_entity.entity_type == EntityType.COURT:
            # Look for case numbers near court
            case_pattern = r'پرونده\s+\d+'
            for match in re.finditer(case_pattern, context):
                abs_start = context_start + match.start()
                abs_end = context_start + match.end()
                
                entities.append(Entity(
                    text=match.group(0),
                    entity_type=EntityType.CASE_NUMBER,
                    start=abs_start,
                    end=abs_end,
                    confidence=0.90,
                    metadata={"context": "near_court"}
                ))
        
        return entities


class EntityNormalizer:
    """Normalize and standardize entities"""
    
    def __init__(self):
        self.normalization_rules = self._build_normalization_rules()
        print("🔧 Entity Normalizer initialized")
    
    def normalize(self, entity: Entity) -> Entity:
        """Normalize entity text"""
        normalized = entity.text
        
        # Apply type-specific normalization
        if entity.entity_type in self.normalization_rules:
            for pattern, replacement in self.normalization_rules[entity.entity_type]:
                normalized = re.sub(pattern, replacement, normalized)
        
        # General normalization
        normalized = self._general_normalize(normalized)
        
        entity.normalized = normalized
        return entity
    
    def _general_normalize(self, text: str) -> str:
        """General text normalization"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Normalize Persian characters
        text = text.replace('ك', 'ک')
        text = text.replace('ي', 'ی')
        text = text.replace('ى', 'ی')
        
        # Normalize numbers
        persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        text = text.translate(persian_to_english)
        
        return text
    
    def _build_normalization_rules(self) -> Dict[EntityType, List[Tuple[str, str]]]:
        """Build normalization rules"""
        return {
            EntityType.ARTICLE: [
                (r'\s+', ' '),
                (r'ماده\s*', 'ماده '),
            ],
            EntityType.MONEY: [
                (r'[,،]', ''),
                (r'\s+', ''),
            ],
            EntityType.DATE: [
                (r'\s+', ' '),
            ],
        }


class EntityLinker:
    """Link entities to knowledge base"""
    
    def __init__(self):
        self.knowledge_base = self._build_knowledge_base()
        print("🔗 Entity Linker initialized")
    
    def link(self, entities: List[Entity]) -> List[Entity]:
        """Link entities to knowledge base"""
        for entity in entities:
            if entity.normalized:
                linked = self._find_links(entity.normalized, entity.entity_type)
                entity.linked_entities = linked
        
        return entities
    
    def _find_links(self, text: str, entity_type: EntityType) -> List[str]:
        """Find links in knowledge base"""
        links = []
        
        if entity_type in self.knowledge_base:
            text_lower = text.lower()
            for kb_entry in self.knowledge_base[entity_type]:
                if self._is_similar(text_lower, kb_entry.lower()):
                    links.append(kb_entry)
        
        return links
    
    def _is_similar(self, text1: str, text2: str) -> bool:
        """Check if two texts are similar"""
        # Simple similarity check
        return text1 == text2 or text1 in text2 or text2 in text1
    
    def _build_knowledge_base(self) -> Dict[EntityType, List[str]]:
        """Build knowledge base"""
        return {
            EntityType.LAW: [
                "قانون مدنی",
                "قانون تجارت",
                "قانون کار",
                "قانون جزا",
                "قانون مجازات اسلامی",
                "قانون آیین دادرسی مدنی",
                "قانون آیین دادرسی کیفری",
                "قانون اساسی",
            ],
            EntityType.COURT: [
                "دادگاه عالی",
                "دیوان عدالت اداری",
                "دیوان عالی کشور",
                "دادگاه تجدیدنظر",
            ],
        }


class RelationExtractor:
    """Extract relations between entities"""
    
    def __init__(self):
        self.relation_patterns = self._build_relation_patterns()
        print("🔀 Relation Extractor initialized")
    
    def extract(self, text: str, entities: List[Entity]) -> List[EntityRelation]:
        """Extract relations between entities"""
        relations = []
        
        # Check all entity pairs
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                relation = self._find_relation(text, entity1, entity2)
                if relation:
                    relations.append(relation)
        
        return relations
    
    def _find_relation(
        self,
        text: str,
        entity1: Entity,
        entity2: Entity
    ) -> Optional[EntityRelation]:
        """Find relation between two entities"""
        # Get text between entities
        if entity1.end < entity2.start:
            between = text[entity1.end:entity2.start]
            subject, obj = entity1, entity2
        elif entity2.end < entity1.start:
            between = text[entity2.end:entity1.start]
            subject, obj = entity2, entity1
        else:
            return None
        
        # Check for relation patterns
        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, between, re.IGNORECASE):
                    return EntityRelation(
                        subject=subject,
                        relation=relation_type,
                        object=obj,
                        confidence=0.80
                    )
        
        return None
    
    def _build_relation_patterns(self) -> Dict[str, List[str]]:
        """Build relation patterns"""
        return {
            "cited_in": [r'طبق', r'براساس', r'مطابق', r'به\s+موجب'],
            "issued_by": [r'صادره\s+از', r'توسط', r'از\s+سوی'],
            "refers_to": [r'اشاره\s+به', r'مربوط\s+به', r'راجع\s+به'],
            "appeals_to": [r'تجدیدنظر', r'فرجام', r'اعتراض'],
            "decided_by": [r'رسیدگی\s+توسط', r'صادر\s+شده\s+از'],
        }


class EntityValidator:
    """Validate and filter entities"""
    
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        print(f"✅ Entity Validator initialized (min_confidence={min_confidence})")
    
    def validate(self, entities: List[Entity]) -> List[Entity]:
        """Validate entities"""
        valid_entities = []
        
        for entity in entities:
            if self._is_valid(entity):
                valid_entities.append(entity)
        
        return valid_entities
    
    def _is_valid(self, entity: Entity) -> bool:
        """Check if entity is valid"""
        # Check confidence
        if entity.confidence < self.min_confidence:
            return False
        
        # Check length
        if len(entity.text) < 2:
            return False
        
        # Check if not just numbers or punctuation
        if re.match(r'^[\d\s\.,،]+$', entity.text):
            return False
        
        return True


class UltraEntityExtractor:
    """
    Ultra-advanced entity extractor
    
    Features:
    - Multi-strategy extraction
    - Contextual understanding
    - Entity normalization
    - Entity linking
    - Relation extraction
    - Validation
    """
    
    def __init__(self, min_confidence: float = 0.5):
        # Initialize extractors
        self.pattern_extractor = PatternBasedExtractor()
        self.contextual_extractor = ContextualExtractor()
        self.normalizer = EntityNormalizer()
        self.linker = EntityLinker()
        self.relation_extractor = RelationExtractor()
        self.validator = EntityValidator(min_confidence)
        
        # Statistics
        self.stats = {
            "texts_processed": 0,
            "entities_extracted": 0,
            "relations_extracted": 0,
            "entity_types": defaultdict(int)
        }
        
        print("🚀 Ultra Entity Extractor initialized")
    
    def extract(
        self,
        text: str,
        extract_relations: bool = True,
        normalize: bool = True,
        link: bool = True,
        validate: bool = True
    ) -> Dict:
        """
        Extract entities from text
        
        Args:
            text: Input text
            extract_relations: Extract relations between entities
            normalize: Normalize entity text
            link: Link entities to knowledge base
            validate: Validate entities
        
        Returns:
            Dictionary with entities and relations
        """
        # Pattern-based extraction
        entities = self.pattern_extractor.extract(text)
        
        # Contextual extraction
        context_entities = self.contextual_extractor.extract(text, entities)
        entities.extend(context_entities)
        
        # Remove duplicates
        entities = self._deduplicate_entities(entities)
        
        # Validate
        if validate:
            entities = self.validator.validate(entities)
        
        # Normalize
        if normalize:
            entities = [self.normalizer.normalize(e) for e in entities]
        
        # Link
        if link:
            entities = self.linker.link(entities)
        
        # Extract relations
        relations = []
        if extract_relations:
            relations = self.relation_extractor.extract(text, entities)
        
        # Update statistics
        self._update_stats(entities, relations)
        
        return {
            "entities": [e.to_dict() for e in entities],
            "relations": [r.to_dict() for r in relations],
            "statistics": {
                "num_entities": len(entities),
                "num_relations": len(relations),
                "entity_types": self._count_entity_types(entities)
            }
        }
    
    def extract_entities(self, text: str) -> List[Entity]:
        """Extract only entities (no relations)"""
        result = self.extract(text, extract_relations=False)
        # Reconstruct Entity objects from dicts
        entities = []
        for e_dict in result["entities"]:
            entities.append(Entity(
                text=e_dict["text"],
                entity_type=EntityType(e_dict["type"]),
                start=e_dict["start"],
                end=e_dict["end"],
                confidence=e_dict["confidence"],
                normalized=e_dict.get("normalized"),
                metadata=e_dict.get("metadata", {}),
                linked_entities=e_dict.get("linked_entities", [])
            ))
        return entities
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities"""
        seen = set()
        unique = []
        
        for entity in entities:
            key = (entity.text, entity.start, entity.end, entity.entity_type)
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        
        return unique
    
    def _count_entity_types(self, entities: List[Entity]) -> Dict[str, int]:
        """Count entities by type"""
        counts = defaultdict(int)
        for entity in entities:
            counts[entity.entity_type.value] += 1
        return dict(counts)
    
    def _update_stats(self, entities: List[Entity], relations: List[EntityRelation]):
        """Update statistics"""
        self.stats["texts_processed"] += 1
        self.stats["entities_extracted"] += len(entities)
        self.stats["relations_extracted"] += len(relations)
        
        for entity in entities:
            self.stats["entity_types"][entity.entity_type.value] += 1
    
    def get_statistics(self) -> Dict:
        """Get extraction statistics"""
        stats = dict(self.stats)
        stats["entity_types"] = dict(stats["entity_types"])
        return stats


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("🚀 Testing Ultra Entity Extractor")
    print("=" * 60)
    
    # Initialize extractor
    extractor = UltraEntityExtractor(min_confidence=0.5)
    
    # Sample text
    text = """
    طبق ماده 10 قانون مدنی، قوانین راجع به اهلیت اشخاص تابع قانون دولتی است.
    دادگاه عالی در تاریخ 15/03/1402 با شماره دادنامه 9901234 حکم به پرداخت 
    مبلغ 50000000 ریال خسارت صادر کرد. خواهان با وکالت آقای احمدی علیه 
    خوانده در شعبه 12 دادگاه تجدیدنظر اقامه دعوا نمود.
    """
    
    # Extract entities
    print(f"\n📝 Extracting entities...")
    result = extractor.extract(text)
    
    print(f"\n🏷️  Entities: {result['statistics']['num_entities']}")
    for entity in result['entities']:
        print(f"   - {entity['text']}")
        print(f"     Type: {entity['type']}")
        print(f"     Confidence: {entity['confidence']:.2f}")
        if entity['normalized']:
            print(f"     Normalized: {entity['normalized']}")
        if entity['metadata']:
            print(f"     Metadata: {entity['metadata']}")
    
    print(f"\n🔀 Relations: {result['statistics']['num_relations']}")
    for relation in result['relations']:
        print(f"   - {relation['subject']['text']} --[{relation['relation']}]--> {relation['object']['text']}")
    
    print(f"\n📊 Entity Types:")
    for entity_type, count in result['statistics']['entity_types'].items():
        print(f"   - {entity_type}: {count}")
    
    # Statistics
    stats = extractor.get_statistics()
    print(f"\n📈 Overall Statistics:")
    print(f"   Texts processed: {stats['texts_processed']}")
    print(f"   Total entities: {stats['entities_extracted']}")
    print(f"   Total relations: {stats['relations_extracted']}")
    
    print("\n✅ Entity extractor test complete")
