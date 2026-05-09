"""
Document Importer for Legal Knowledge Graph
===========================================

This module imports legal documents and their entities/relationships into Neo4j.
"""

import logging
import hashlib
from typing import List, Dict, Optional
from datetime import datetime

from graph.neo4j.connection import Neo4jConnection
from graph.builders.entity_extractor import EntityExtractor, Entity
from graph.builders.relationship_builder import RelationshipBuilder, Relationship

logger = logging.getLogger(__name__)


class DocumentImporter:
    """
    Document Importer
    
    Imports legal documents by:
    1. Extracting entities using EntityExtractor
    2. Building relationships using RelationshipBuilder
    3. Creating nodes and relationships in Neo4j
    """

    def __init__(
        self,
        connection: Neo4jConnection,
        entity_extractor: Optional[EntityExtractor] = None,
        relationship_builder: Optional[RelationshipBuilder] = None,
    ):
        """
        Initialize DocumentImporter
        
        Args:
            connection: Neo4j connection instance
            entity_extractor: EntityExtractor instance (creates new if None)
            relationship_builder: RelationshipBuilder instance (creates new if None)
        """
        self.connection = connection
        self.entity_extractor = entity_extractor or EntityExtractor(
            use_ner=False, min_score=0.7
        )
        self.relationship_builder = relationship_builder or RelationshipBuilder(
            max_distance=200
        )

        logger.info("DocumentImporter initialized")

    def import_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict] = None,
        create_relationships: bool = True,
    ) -> Dict:
        """
        Import a legal document
        
        Process:
        1. Extract entities from text
        2. Create entity nodes in graph
        3. Build relationships between entities
        4. Create relationship edges in graph
        
        Args:
            document_id: Unique document ID
            text: Document text
            metadata: Document metadata
            create_relationships: Whether to create relationships
        
        Returns:
            Dictionary with import statistics
        """
        logger.info(f"Importing document: {document_id}")

        # Extract entities
        entities = self.entity_extractor.extract_and_validate(text)
        logger.debug(f"Extracted {len(entities)} entities")

        # Create entity nodes
        entity_node_ids = []
        for entity in entities:
            node_id = self._create_entity_node(entity, document_id, metadata)
            if node_id:
                entity_node_ids.append(node_id)

        # Build and create relationships
        relationship_count = 0
        if create_relationships and len(entities) > 1:
            relationships = self.relationship_builder.build_relationships(
                entities, text
            )
            logger.debug(f"Built {len(relationships)} relationships")

            # Create relationship edges
            for relationship in relationships:
                success = self._create_relationship_edge(relationship, document_id)
                if success:
                    relationship_count += 1

        stats = {
            "document_id": document_id,
            "entity_count": len(entity_node_ids),
            "relationship_count": relationship_count,
            "entities_by_type": self._count_by_type(entities),
            "relationships_by_type": (
                self._count_relationships_by_type(relationships)
                if create_relationships
                else {}
            ),
        }

        logger.info(
            f"Imported document {document_id}: "
            f"{stats['entity_count']} entities, "
            f"{stats['relationship_count']} relationships"
        )

        return stats

    def _create_entity_node(
        self, entity: Entity, document_id: str, metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Create entity node in Neo4j
        
        Args:
            entity: Entity to create
            document_id: Source document ID
            metadata: Document metadata
        
        Returns:
            Node ID if created, None otherwise
        """
        # Generate node ID based on entity
        node_id = self._generate_entity_node_id(entity)

        # Map entity label to node label
        node_label = self._map_entity_to_node_label(entity.label)

        if not node_label:
            logger.warning(f"Unknown entity label: {entity.label}")
            return None

        # Create node based on type
        if node_label == "Court":
            return self._create_court_node(node_id, entity, document_id, metadata)
        elif node_label == "Verdict":
            return self._create_verdict_node(node_id, entity, document_id, metadata)
        elif node_label == "Case":
            return self._create_case_node(node_id, entity, document_id, metadata)
        elif node_label == "Person":
            return self._create_person_node(node_id, entity, document_id, metadata)
        elif node_label == "Party":
            return self._create_party_node(node_id, entity, document_id, metadata)
        else:
            # Generic entity node
            return self._create_generic_entity_node(
                node_id, entity, node_label, document_id, metadata
            )

    def _create_court_node(
        self, node_id: str, entity: Entity, document_id: str, metadata: Optional[Dict]
    ) -> str:
        """Create Court node"""
        query = """
        MERGE (c:Court {id: $id})
        SET c.name = $name,
            c.type = $type,
            c.source_document = $document_id,
            c.created_at = $created_at,
            c.updated_at = $updated_at
        RETURN c.id as id
        """

        params = {
            "id": node_id,
            "name": entity.text,
            "type": "عمومی",  # Default type
            "document_id": document_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        result = self.connection.execute_query(query, params)
        return node_id

    def _create_verdict_node(
        self, node_id: str, entity: Entity, document_id: str, metadata: Optional[Dict]
    ) -> str:
        """Create Verdict node"""
        query = """
        MERGE (v:Verdict {id: $id})
        SET v.verdict_number = $verdict_number,
            v.case_number = $case_number,
            v.content = $content,
            v.source_document = $document_id,
            v.created_at = $created_at,
            v.updated_at = $updated_at
        RETURN v.id as id
        """

        params = {
            "id": node_id,
            "verdict_number": entity.text,
            "case_number": metadata.get("case_number", "") if metadata else "",
            "content": entity.text,
            "document_id": document_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        result = self.connection.execute_query(query, params)
        return node_id

    def _create_case_node(
        self, node_id: str, entity: Entity, document_id: str, metadata: Optional[Dict]
    ) -> str:
        """Create Case node"""
        query = """
        MERGE (c:Case {id: $id})
        SET c.case_number = $case_number,
            c.type = $type,
            c.source_document = $document_id,
            c.created_at = $created_at,
            c.updated_at = $updated_at
        RETURN c.id as id
        """

        params = {
            "id": node_id,
            "case_number": entity.text,
            "type": "حقوقی",  # Default type
            "document_id": document_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        result = self.connection.execute_query(query, params)
        return node_id

    def _create_person_node(
        self, node_id: str, entity: Entity, document_id: str, metadata: Optional[Dict]
    ) -> str:
        """Create Person node (with hashed name for privacy)"""
        # Hash name for privacy
        name_hash = hashlib.sha256(entity.text.encode()).hexdigest()[:16]

        query = """
        MERGE (p:Person {id: $id})
        SET p.name_hash = $name_hash,
            p.role = $role,
            p.source_document = $document_id,
            p.created_at = $created_at,
            p.updated_at = $updated_at
        RETURN p.id as id
        """

        params = {
            "id": node_id,
            "name_hash": name_hash,
            "role": entity.metadata.get("role"),
            "document_id": document_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        result = self.connection.execute_query(query, params)
        return node_id

    def _create_party_node(
        self, node_id: str, entity: Entity, document_id: str, metadata: Optional[Dict]
    ) -> str:
        """Create Party node"""
        # Hash name for privacy
        name_hash = hashlib.sha256(entity.text.encode()).hexdigest()[:16]

        query = """
        MERGE (p:Party {id: $id})
        SET p.party_type = $party_type,
            p.name_hash = $name_hash,
            p.source_document = $document_id,
            p.created_at = $created_at,
            p.updated_at = $updated_at
        RETURN p.id as id
        """

        # Determine party type from entity text
        party_type = "خواهان" if "خواهان" in entity.text else "خوانده"

        params = {
            "id": node_id,
            "party_type": party_type,
            "name_hash": name_hash,
            "document_id": document_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        result = self.connection.execute_query(query, params)
        return node_id

    def _create_generic_entity_node(
        self,
        node_id: str,
        entity: Entity,
        node_label: str,
        document_id: str,
        metadata: Optional[Dict],
    ) -> str:
        """Create generic entity node"""
        query = f"""
        MERGE (e:{node_label} {{id: $id}})
        SET e.text = $text,
            e.label = $label,
            e.score = $score,
            e.source = $source,
            e.source_document = $document_id,
            e.created_at = $created_at,
            e.updated_at = $updated_at
        RETURN e.id as id
        """

        params = {
            "id": node_id,
            "text": entity.text,
            "label": entity.label,
            "score": entity.score,
            "source": entity.source,
            "document_id": document_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        result = self.connection.execute_query(query, params)
        return node_id

    def _create_relationship_edge(
        self, relationship: Relationship, document_id: str
    ) -> bool:
        """
        Create relationship edge in Neo4j
        
        Args:
            relationship: Relationship to create
            document_id: Source document ID
        
        Returns:
            True if created successfully
        """
        try:
            # Generate node IDs
            source_id = self._generate_entity_node_id(relationship.source_entity)
            target_id = self._generate_entity_node_id(relationship.target_entity)

            # Get node labels
            source_label = self._map_entity_to_node_label(
                relationship.source_entity.label
            )
            target_label = self._map_entity_to_node_label(
                relationship.target_entity.label
            )

            if not source_label or not target_label:
                return False

            # Create relationship
            query = f"""
            MATCH (s:{source_label} {{id: $source_id}})
            MATCH (t:{target_label} {{id: $target_id}})
            MERGE (s)-[r:{relationship.rel_type}]->(t)
            SET r.strength = $strength,
                r.confidence = $confidence,
                r.source_document = $document_id,
                r.context = $context,
                r.created_at = $created_at
            RETURN r
            """

            params = {
                "source_id": source_id,
                "target_id": target_id,
                "strength": relationship.strength,
                "confidence": relationship.confidence,
                "document_id": document_id,
                "context": relationship.properties.get("context", ""),
                "created_at": datetime.now().isoformat(),
            }

            result = self.connection.execute_query(query, params)
            return True

        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            return False

    def _generate_entity_node_id(self, entity: Entity) -> str:
        """Generate unique node ID for entity"""
        # Use normalized text + label for ID
        text_hash = hashlib.sha256(entity.normalized_text.encode()).hexdigest()[:12]
        return f"{entity.label.lower()}_{text_hash}"

    def _map_entity_to_node_label(self, entity_label: str) -> Optional[str]:
        """Map entity label to Neo4j node label"""
        mapping = {
            "COURT": "Court",
            "VERDICT": "Verdict",
            "CASE_NO": "Case",
            "PARTY": "Party",
            "JUDGE": "Person",
            "LAWYER": "Person",
            "ARTICLE": "Article",
            "LAW_NAME": "Law",
            "LOCATION": "Location",
            "DATE": "Date",
        }
        return mapping.get(entity_label)

    def _count_by_type(self, entities: List[Entity]) -> Dict[str, int]:
        """Count entities by type"""
        counts = {}
        for entity in entities:
            counts[entity.label] = counts.get(entity.label, 0) + 1
        return counts

    def _count_relationships_by_type(
        self, relationships: List[Relationship]
    ) -> Dict[str, int]:
        """Count relationships by type"""
        counts = {}
        for rel in relationships:
            counts[rel.rel_type] = counts.get(rel.rel_type, 0) + 1
        return counts

    def get_document_statistics(self, document_id: str) -> Dict:
        """
        Get statistics for imported document
        
        Args:
            document_id: Document ID
        
        Returns:
            Dictionary with statistics
        """
        query = """
        MATCH (n)
        WHERE n.source_document = $document_id
        WITH labels(n)[0] as label, count(n) as count
        RETURN label, count
        """

        params = {"document_id": document_id}

        result = self.connection.execute_query(query, params)

        stats = {"document_id": document_id, "nodes_by_type": {}}

        for row in result:
            stats["nodes_by_type"][row["label"]] = row["count"]

        return stats
