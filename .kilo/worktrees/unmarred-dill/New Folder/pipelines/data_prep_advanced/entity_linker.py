"""
Entity Linker - Advanced Entity Recognition and Linking
=====================================================
Link entities to knowledge graph nodes
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import re
from enum import Enum


class EntityType(str, Enum):
    """Types of legal entities"""
    LAW = "law"
    ARTICLE = "article"
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    CASE = "case"
    COURT = "court"


@dataclass
class Entity:
    """Extracted entity"""
    text: str
    entity_type: EntityType
    start: int
    end: int
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)
    linked_id: Optional[str] = None


@dataclass
class EntityGraph:
    """Graph of linked entities"""
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Tuple[str, str, str]] = field(default_factory=list)  # (entity1, relation, entity2)
    
    def add_entity(self, entity: Entity):
        """Add entity to graph"""
        self.entities.append(entity)
    
    def add_relationship(self, entity1_id: str, relation: str, entity2_id: str):
        """Add relationship between entities"""
        self.relationships.append((entity1_id, relation, entity2_id))
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a specific type"""
        return [e for e in self.entities if e.entity_type == entity_type]


class EntityLinker:
    """
    Advanced entity linker for legal documents
    
    Features:
    - Named entity recognition
    - Entity disambiguation
    - Knowledge graph linking
    - Relationship extraction
    """
    
    def __init__(self, knowledge_base: Optional[Dict] = None):
        """
        Initialize entity linker
        
        Args:
            knowledge_base: Optional knowledge base for entity linking
        """
        self.knowledge_base = knowledge_base or {}
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for entity extraction"""
        self.patterns = {
            EntityType.LAW: [
                r'قانون\s+[\w\s]+',
                r'ماده\s+\d+',
            ],
            EntityType.ARTICLE: [
                r'ماده\s+\d+',
                r'بند\s+\d+',
            ],
            EntityType.DATE: [
                r'\d{4}/\d{1,2}/\d{1,2}',
                r'\d{1,2}\s+[\u0600-\u06FF]+\s+\d{4}',
            ],
        }
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from text
        
        Args:
            text: Input text
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    entity = Entity(
                        text=match.group(),
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.8
                    )
                    entities.append(entity)
        
        return entities
    
    def link_entities(self, entities: List[Entity]) -> EntityGraph:
        """
        Link entities to knowledge base
        
        Args:
            entities: List of entities to link
            
        Returns:
            Entity graph with linked entities
        """
        graph = EntityGraph()
        
        for entity in entities:
            # Try to link to knowledge base
            if entity.text in self.knowledge_base:
                entity.linked_id = self.knowledge_base[entity.text]
            
            graph.add_entity(entity)
        
        # Extract relationships
        self._extract_relationships(graph)
        
        return graph
    
    def _extract_relationships(self, graph: EntityGraph):
        """Extract relationships between entities"""
        entities = graph.entities
        
        # Simple relationship extraction
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # If entities are close, they might be related
                if abs(entity1.start - entity2.start) < 100:
                    relation = self._infer_relation(entity1, entity2)
                    if relation:
                        graph.add_relationship(
                            entity1.text,
                            relation,
                            entity2.text
                        )
    
    def _infer_relation(self, entity1: Entity, entity2: Entity) -> Optional[str]:
        """Infer relationship between two entities"""
        # Simple rule-based relation inference
        if entity1.entity_type == EntityType.LAW and entity2.entity_type == EntityType.ARTICLE:
            return "contains"
        elif entity1.entity_type == EntityType.ARTICLE and entity2.entity_type == EntityType.ARTICLE:
            return "related_to"
        
        return None
    
    def process(self, text: str) -> EntityGraph:
        """
        Full entity linking pipeline
        
        Args:
            text: Input text
            
        Returns:
            Entity graph
        """
        # Extract entities
        entities = self.extract_entities(text)
        
        # Link entities
        graph = self.link_entities(entities)
        
        return graph
