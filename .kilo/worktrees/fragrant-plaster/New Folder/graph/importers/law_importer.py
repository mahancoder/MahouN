"""
Law Importer for Legal Knowledge Graph
======================================

This module imports laws and their articles into the Neo4j graph.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, date

from graph.neo4j.connection import Neo4jConnection
from graph.neo4j.models import LawNode, ArticleNode, NoteNode, ClauseNode

logger = logging.getLogger(__name__)


class LawImporter:
    """
    Law Importer
    
    Imports laws and their articles into the Neo4j graph.
    Creates Law nodes, Article nodes, and relationships between them.
    """

    def __init__(self, connection: Neo4jConnection):
        """
        Initialize LawImporter
        
        Args:
            connection: Neo4j connection instance
        """
        self.connection = connection
        logger.info("LawImporter initialized")

    def import_law(
        self,
        name: str,
        full_name: str,
        year: int,
        category: str,
        articles: List[Dict],
        approval_date: Optional[date] = None,
        source_url: Optional[str] = None,
        full_text: Optional[str] = None,
    ) -> str:
        """
        Import a law with its articles
        
        Creates:
        - Law node
        - Article nodes for all articles
        - CONTAINS relationships from Law to Articles
        - Note nodes if articles have notes
        - Clause nodes if articles have clauses
        
        Args:
            name: Law name (e.g., "قانون مدنی")
            full_name: Full official name
            year: Approval year
            category: Law category (مدنی، کیفری، etc.)
            articles: List of article dictionaries
            approval_date: Approval date
            source_url: Source URL
            full_text: Full text of law
        
        Returns:
            Law ID
        """
        # Generate law ID
        law_id = self._generate_law_id(name, year)

        # Create Law node
        law_node = LawNode(
            id=law_id,
            name=name,
            full_name=full_name,
            year=year,
            approval_date=approval_date,
            category=category,
            source_url=source_url,
            full_text=full_text,
            article_count=len(articles),
            citation_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Create law in graph
        self._create_law_node(law_node)

        # Import articles
        article_ids = []
        for i, article_data in enumerate(articles):
            article_id = self._import_article(law_id, name, article_data, order=i + 1)
            article_ids.append(article_id)

        logger.info(
            f"Imported law '{name}' with {len(article_ids)} articles (ID: {law_id})"
        )

        return law_id

    def _import_article(
        self, law_id: str, law_name: str, article_data: Dict, order: int
    ) -> str:
        """
        Import a single article
        
        Args:
            law_id: Parent law ID
            law_name: Parent law name
            article_data: Article data dictionary
            order: Article order in law
        
        Returns:
            Article ID
        """
        # Generate article ID
        article_number = article_data.get("number")
        article_id = f"{law_id}_article_{article_number}"

        # Create Article node
        article_node = ArticleNode(
            id=article_id,
            number=article_number,
            law_id=law_id,
            law_name=law_name,
            content=article_data.get("content", ""),
            has_note=article_data.get("has_note", False),
            note_count=len(article_data.get("notes", [])),
            has_clause=article_data.get("has_clause", False),
            clause_count=len(article_data.get("clauses", [])),
            category=article_data.get("category"),
            citation_count=0,
            pagerank_score=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Create article in graph
        self._create_article_node(article_node)

        # Create CONTAINS relationship
        self._create_contains_relationship(law_id, article_id, order)

        # Import notes if any
        if article_data.get("notes"):
            for note_data in article_data["notes"]:
                self._import_note(article_id, note_data)

        # Import clauses if any
        if article_data.get("clauses"):
            for clause_data in article_data["clauses"]:
                self._import_clause(article_id, clause_data)

        return article_id

    def _import_note(self, article_id: str, note_data: Dict) -> str:
        """
        Import a note (تبصره)
        
        Args:
            article_id: Parent article ID
            note_data: Note data dictionary
        
        Returns:
            Note ID
        """
        note_id = f"{article_id}_note_{note_data.get('number', 1)}"

        note_node = NoteNode(
            id=note_id,
            article_id=article_id,
            number=note_data.get("number", 1),
            content=note_data.get("content", ""),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Create note in graph
        self._create_note_node(note_node)

        # Create HAS_NOTE relationship
        self._create_has_note_relationship(article_id, note_id)

        return note_id

    def _import_clause(self, article_id: str, clause_data: Dict) -> str:
        """
        Import a clause (بند)
        
        Args:
            article_id: Parent article ID
            clause_data: Clause data dictionary
        
        Returns:
            Clause ID
        """
        clause_id = f"{article_id}_clause_{clause_data.get('number', 1)}"

        clause_node = ClauseNode(
            id=clause_id,
            article_id=article_id,
            number=clause_data.get("number", 1),
            content=clause_data.get("content", ""),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Create clause in graph
        self._create_clause_node(clause_node)

        # Create HAS_CLAUSE relationship
        self._create_has_clause_relationship(article_id, clause_id)

        return clause_id

    def _generate_law_id(self, name: str, year: int) -> str:
        """Generate unique law ID"""
        # Normalize name for ID
        normalized = name.replace(" ", "_").replace("‌", "_")
        return f"law_{normalized}_{year}"

    def _create_law_node(self, law_node: LawNode):
        """Create Law node in Neo4j"""
        query = """
        MERGE (l:Law {id: $id})
        SET l.name = $name,
            l.full_name = $full_name,
            l.year = $year,
            l.approval_date = $approval_date,
            l.category = $category,
            l.status = $status,
            l.source_url = $source_url,
            l.full_text = $full_text,
            l.article_count = $article_count,
            l.citation_count = $citation_count,
            l.created_at = $created_at,
            l.updated_at = $updated_at
        RETURN l.id as id
        """

        params = {
            "id": law_node.id,
            "name": law_node.name,
            "full_name": law_node.full_name,
            "year": law_node.year,
            "approval_date": (
                law_node.approval_date.isoformat() if law_node.approval_date else None
            ),
            "category": law_node.category,
            "status": law_node.status,
            "source_url": law_node.source_url,
            "full_text": law_node.full_text,
            "article_count": law_node.article_count,
            "citation_count": law_node.citation_count,
            "created_at": law_node.created_at.isoformat(),
            "updated_at": law_node.updated_at.isoformat(),
        }

        result = self.connection.execute_query(query, params)
        logger.debug(f"Created Law node: {law_node.id}")

    def _create_article_node(self, article_node: ArticleNode):
        """Create Article node in Neo4j"""
        query = """
        MERGE (a:Article {id: $id})
        SET a.number = $number,
            a.law_id = $law_id,
            a.law_name = $law_name,
            a.content = $content,
            a.has_note = $has_note,
            a.note_count = $note_count,
            a.has_clause = $has_clause,
            a.clause_count = $clause_count,
            a.category = $category,
            a.citation_count = $citation_count,
            a.pagerank_score = $pagerank_score,
            a.created_at = $created_at,
            a.updated_at = $updated_at
        RETURN a.id as id
        """

        params = {
            "id": article_node.id,
            "number": article_node.number,
            "law_id": article_node.law_id,
            "law_name": article_node.law_name,
            "content": article_node.content,
            "has_note": article_node.has_note,
            "note_count": article_node.note_count,
            "has_clause": article_node.has_clause,
            "clause_count": article_node.clause_count,
            "category": article_node.category,
            "citation_count": article_node.citation_count,
            "pagerank_score": article_node.pagerank_score,
            "created_at": article_node.created_at.isoformat(),
            "updated_at": article_node.updated_at.isoformat(),
        }

        result = self.connection.execute_query(query, params)
        logger.debug(f"Created Article node: {article_node.id}")

    def _create_note_node(self, note_node: NoteNode):
        """Create Note node in Neo4j"""
        query = """
        MERGE (n:Note {id: $id})
        SET n.article_id = $article_id,
            n.number = $number,
            n.content = $content,
            n.created_at = $created_at,
            n.updated_at = $updated_at
        RETURN n.id as id
        """

        params = {
            "id": note_node.id,
            "article_id": note_node.article_id,
            "number": note_node.number,
            "content": note_node.content,
            "created_at": note_node.created_at.isoformat(),
            "updated_at": note_node.updated_at.isoformat(),
        }

        result = self.connection.execute_query(query, params)
        logger.debug(f"Created Note node: {note_node.id}")

    def _create_clause_node(self, clause_node: ClauseNode):
        """Create Clause node in Neo4j"""
        query = """
        MERGE (c:Clause {id: $id})
        SET c.article_id = $article_id,
            c.number = $number,
            c.content = $content,
            c.created_at = $created_at,
            c.updated_at = $updated_at
        RETURN c.id as id
        """

        params = {
            "id": clause_node.id,
            "article_id": clause_node.article_id,
            "number": clause_node.number,
            "content": clause_node.content,
            "created_at": clause_node.created_at.isoformat(),
            "updated_at": clause_node.updated_at.isoformat(),
        }

        result = self.connection.execute_query(query, params)
        logger.debug(f"Created Clause node: {clause_node.id}")

    def _create_contains_relationship(self, law_id: str, article_id: str, order: int):
        """Create CONTAINS relationship from Law to Article"""
        query = """
        MATCH (l:Law {id: $law_id})
        MATCH (a:Article {id: $article_id})
        MERGE (l)-[r:CONTAINS {order: $order}]->(a)
        RETURN r
        """

        params = {"law_id": law_id, "article_id": article_id, "order": order}

        result = self.connection.execute_query(query, params)
        logger.debug(f"Created CONTAINS relationship: {law_id} -> {article_id}")

    def _create_has_note_relationship(self, article_id: str, note_id: str):
        """Create HAS_NOTE relationship from Article to Note"""
        query = """
        MATCH (a:Article {id: $article_id})
        MATCH (n:Note {id: $note_id})
        MERGE (a)-[r:HAS_NOTE]->(n)
        RETURN r
        """

        params = {"article_id": article_id, "note_id": note_id}

        result = self.connection.execute_query(query, params)
        logger.debug(f"Created HAS_NOTE relationship: {article_id} -> {note_id}")

    def _create_has_clause_relationship(self, article_id: str, clause_id: str):
        """Create HAS_CLAUSE relationship from Article to Clause"""
        query = """
        MATCH (a:Article {id: $article_id})
        MATCH (c:Clause {id: $clause_id})
        MERGE (a)-[r:HAS_CLAUSE]->(c)
        RETURN r
        """

        params = {"article_id": article_id, "clause_id": clause_id}

        result = self.connection.execute_query(query, params)
        logger.debug(f"Created HAS_CLAUSE relationship: {article_id} -> {clause_id}")

    def get_law_statistics(self, law_id: str) -> Dict:
        """
        Get statistics for a law
        
        Args:
            law_id: Law ID
        
        Returns:
            Dictionary with statistics
        """
        query = """
        MATCH (l:Law {id: $law_id})
        OPTIONAL MATCH (l)-[:CONTAINS]->(a:Article)
        OPTIONAL MATCH (a)-[:HAS_NOTE]->(n:Note)
        OPTIONAL MATCH (a)-[:HAS_CLAUSE]->(c:Clause)
        RETURN 
            l.name as name,
            l.year as year,
            count(DISTINCT a) as article_count,
            count(DISTINCT n) as note_count,
            count(DISTINCT c) as clause_count
        """

        params = {"law_id": law_id}

        result = self.connection.execute_query(query, params)

        if result:
            return result[0]
        else:
            return {}

    def delete_law(self, law_id: str):
        """
        Delete a law and all its articles
        
        Args:
            law_id: Law ID
        """
        query = """
        MATCH (l:Law {id: $law_id})
        OPTIONAL MATCH (l)-[:CONTAINS]->(a:Article)
        OPTIONAL MATCH (a)-[:HAS_NOTE]->(n:Note)
        OPTIONAL MATCH (a)-[:HAS_CLAUSE]->(c:Clause)
        DETACH DELETE l, a, n, c
        """

        params = {"law_id": law_id}

        self.connection.execute_query(query, params)
        logger.info(f"Deleted law: {law_id}")
