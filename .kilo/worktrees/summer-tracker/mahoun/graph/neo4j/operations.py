"""
Neo4j Graph Operations
=======================

High-level operations for graph manipulation.
"""


from typing import Any, Dict, List, Optional, Tuple

from mahoun.graph.neo4j.connection import Neo4jConnection, get_connection
from mahoun.graph.neo4j.monitoring import Neo4jMetrics


class GraphOperations:
    """High-level graph operations"""
    
    def __init__(
        self,
        connection: Optional[Neo4jConnection] = None,
        metrics: Optional[Neo4jMetrics] = None
    ):
        """
        Initialize graph operations
        
        Args:
            connection: Neo4j connection (uses global if None)
            metrics: Metrics tracker
        """
        self.conn = connection or get_connection()
        self.metrics = metrics or Neo4jMetrics()
    
    def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
        merge: bool = True
    ) -> Dict[str, Any]:
        """
        Create or merge a node
        
        Args:
            label: Node label
            properties: Node properties
            merge: Use MERGE instead of CREATE
            
        Returns:
            Created node properties
        """
        import time
        start = time.time()
        
        # Build property string
        prop_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        
        if merge:
            query = f"""
            MERGE (n:{label} {{{prop_str}}})
            ON CREATE SET n.created_at = datetime()
            ON MATCH SET n.updated_at = datetime()
            RETURN n
            """
        else:
            query = f"""
            CREATE (n:{label} {{{prop_str}}})
            SET n.created_at = datetime()
            RETURN n
            """
        
        result = self.conn.execute_query(query, properties)
        
        self.metrics.record_query(time.time() - start)
        
        return dict(result[0]["n"]) if result else {}
    
    def create_relationship(
        self,
        from_label: str,
        from_id: str,
        to_label: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
        merge: bool = True
    ) -> bool:
        """
        Create relationship between nodes
        
        Args:
            from_label: Source node label
            from_id: Source node ID
            to_label: Target node label
            to_id: Target node ID
            rel_type: Relationship type
            properties: Relationship properties
            merge: Use MERGE instead of CREATE
            
        Returns:
            Success status
        """
        import time
        start = time.time()
        
        props = properties or {}
        prop_str = ", ".join([f"{k}: ${k}" for k in props.keys()])
        
        if merge:
            query = f"""
            MATCH (a:{from_label} {{id: $from_id}})
            MATCH (b:{to_label} {{id: $to_id}})
            MERGE (a)-[r:{rel_type}]->(b)
            SET r += ${{{prop_str}}}
            SET r.updated_at = datetime()
            RETURN r
            """
        else:
            query = f"""
            MATCH (a:{from_label} {{id: $from_id}})
            MATCH (b:{to_label} {{id: $to_id}})
            CREATE (a)-[r:{rel_type} {{{prop_str}}}]->(b)
            SET r.created_at = datetime()
            RETURN r
            """
        
        params = {
            "from_id": from_id,
            "to_id": to_id,
            **props
        }
        
        try:
            self.conn.execute_query(query, params)
            self.metrics.record_query(time.time() - start)
            return True
        except Exception as e:
            self.metrics.record_error()
            print(f"❌ Failed to create relationship: {e}")
            return False
    
    def batch_create_nodes(
        self,
        label: str,
        nodes: List[Dict[str, Any]],
        batch_size: int = 1000,
        merge: bool = True
    ) -> int:
        """
        Batch create nodes
        
        Args:
            label: Node label
            nodes: List of node properties
            batch_size: Batch size
            merge: Use MERGE instead of CREATE
            
        Returns:
            Number of nodes created
        """
        import time
        
        total_created = 0
        
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i + batch_size]
            start = time.time()
            
            if merge:
                query = f"""
                UNWIND $rows AS row
                MERGE (n:{label} {{id: row.id}})
                SET n += row
                SET n.updated_at = datetime()
                ON CREATE SET n.created_at = datetime()
                """
            else:
                query = f"""
                UNWIND $rows AS row
                CREATE (n:{label})
                SET n = row
                SET n.created_at = datetime()
                """
            
            try:
                self.conn.execute_query(query, {"rows": batch})
                total_created += len(batch)
                self.metrics.record_query(time.time() - start)
            except Exception as e:
                self.metrics.record_error()
                print(f"❌ Batch {i//batch_size + 1} failed: {e}")
        
        return total_created
    
    def batch_create_relationships(
        self,
        relationships: List[Tuple[str, str, str, Dict[str, Any]]],
        from_label: str = "Document",
        to_label: str = "Document",
        batch_size: int = 1000,
        merge: bool = True
    ) -> int:
        """
        Batch create relationships
        
        Args:
            relationships: List of (from_id, to_id, rel_type, properties)
            from_label: Source node label
            to_label: Target node label
            batch_size: Batch size
            merge: Use MERGE instead of CREATE
            
        Returns:
            Number of relationships created
        """
        import time
        
        total_created = 0
        
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i + batch_size]
            start = time.time()
            
            # Convert to dict format
            rows = [
                {
                    "from_id": from_id,
                    "to_id": to_id,
                    "rel_type": rel_type,
                    "props": props
                }
                for from_id, to_id, rel_type, props in batch
            ]
            
            if merge:
                query = f"""
                UNWIND $rows AS row
                MATCH (a:{from_label} {{id: row.from_id}})
                MATCH (b:{to_label} {{id: row.to_id}})
                MERGE (a)-[r:RELATES]->(b)
                SET r += row.props
                SET r.updated_at = datetime()
                """
            else:
                query = f"""
                UNWIND $rows AS row
                MATCH (a:{from_label} {{id: row.from_id}})
                MATCH (b:{to_label} {{id: row.to_id}})
                CREATE (a)-[r:RELATES]->(b)
                SET r = row.props
                SET r.created_at = datetime()
                """
            
            try:
                self.conn.execute_query(query, {"rows": rows})
                total_created += len(batch)
                self.metrics.record_query(time.time() - start)
            except Exception as e:
                self.metrics.record_error()
                print(f"❌ Batch {i//batch_size + 1} failed: {e}")
        
        return total_created
    
    def batch_create_typed_relationships(
        self,
        relationships: List[Tuple[str, str, str, str, str, Dict[str, Any]]],
        batch_size: int = 1000,
        merge: bool = True
    ) -> int:
        """
        Batch create relationships with different types
        
        Supports creating relationships with different types in one batch.
        Uses transaction for consistency and rollback on error.
        
        Args:
            relationships: List of (from_label, from_id, to_label, to_id, rel_type, properties)
            batch_size: Batch size (default 1000)
            merge: Use MERGE instead of CREATE
            
        Returns:
            Number of relationships created
        """
        import time
        
        total_created = 0
        
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i + batch_size]
            start = time.time()
            
            # Group by relationship type for efficiency
            by_type: Dict[str, Any] = {}
            for from_label, from_id, to_label, to_id, rel_type, props in batch:
                key = (from_label, to_label, rel_type)
                if key not in by_type:
                    by_type[key] = []
                by_type[key].append({
                    "from_id": from_id,
                    "to_id": to_id,
                    "props": props or {}
                })
            
            # Execute in transaction
            try:
                with self.conn.driver.session() as session:
                    with session.begin_transaction() as tx:
                        for (from_label, to_label, rel_type), rows in by_type.items():
                            if merge:
                                query = f"""
                                UNWIND $rows AS row
                                MATCH (a:{from_label} {{id: row.from_id}})
                                MATCH (b:{to_label} {{id: row.to_id}})
                                MERGE (a)-[r:{rel_type}]->(b)
                                SET r += row.props
                                SET r.updated_at = datetime()
                                ON CREATE SET r.created_at = datetime()
                                """
                            else:
                                query = f"""
                                UNWIND $rows AS row
                                MATCH (a:{from_label} {{id: row.from_id}})
                                MATCH (b:{to_label} {{id: row.to_id}})
                                CREATE (a)-[r:{rel_type}]->(b)
                                SET r = row.props
                                SET r.created_at = datetime()
                                """
                            
                            tx.run(query, {"rows": rows})
                        
                        # Commit transaction
                        tx.commit()
                
                total_created += len(batch)
                self.metrics.record_query(time.time() - start)
                
            except Exception as e:
                self.metrics.record_error()
                print(f"❌ Batch {i//batch_size + 1} failed (rolled back): {e}")
                # Transaction automatically rolled back on exception
        
        return total_created
    
    def delete_node(self, label: str, node_id: str) -> bool:
        """Delete a node and its relationships"""
        query = f"""
        MATCH (n:{label} {{id: $id}})
        DETACH DELETE n
        """
        
        try:
            self.conn.execute_query(query, {"id": node_id})
            return True
        except Exception as e:
            print(f"❌ Failed to delete node: {e}")
            return False
    
    def get_node(self, label: str, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node by ID"""
        query = f"""
        MATCH (n:{label} {{id: $id}})
        RETURN n
        """
        
        result = self.conn.execute_query(query, {"id": node_id})
        return dict(result[0]["n"]) if result else None
    
    def update_node(
        self,
        label: str,
        node_id: str,
        properties: Dict[str, Any]
    ) -> bool:
        """Update node properties"""
        query = f"""
        MATCH (n:{label} {{id: $id}})
        SET n += $props
        SET n.updated_at = datetime()
        RETURN n
        """
        
        try:
            self.conn.execute_query(
                query,
                {"id": node_id, "props": properties}
            )
            return True
        except Exception as e:
            print(f"❌ Failed to update node: {e}")
            return False


# Convenience functions
def create_document(
    doc_id: str,
    title: str,
    content: str,
    **kwargs
) -> Dict[str, Any]:
    """Create a document node"""
    ops = GraphOperations()
    return ops.create_node(
        "Document",
        {"id": doc_id, "title": title, "content": content, **kwargs}
    )


def create_relationship(
    from_id: str,
    to_id: str,
    rel_type: str = "CITES",
    **properties
) -> bool:
    """Create relationship between documents"""
    ops = GraphOperations()
    return ops.create_relationship(
        "Document", from_id,
        "Document", to_id,
        rel_type, properties
    )


def batch_create_nodes(
    label: str,
    nodes: List[Dict[str, Any]],
    batch_size: int = 1000
) -> int:
    """Batch create nodes"""
    ops = GraphOperations()
    return ops.batch_create_nodes(label, nodes, batch_size)


def batch_create_relationships(
    relationships: List[Tuple[str, str, str, Dict[str, Any]]],
    batch_size: int = 1000
) -> int:
    """Batch create relationships"""
    ops = GraphOperations()
    return ops.batch_create_relationships(relationships, batch_size=batch_size)


# ============================================================================
# Bootstrap Verdict Ingestion Support (Scenario B)
# ============================================================================

import re
import hashlib
import logging

logger = logging.getLogger(__name__)


def _parse_law_article(article_str: str) -> Dict[str, str]:
    """
    Parse a law article string into components.
    
    Example:
        "ماده 339 قانون مدنی" -> {"article_no": "339", "code": "قانون مدنی", "label": "ماده 339 قانون مدنی"}
        "ماده 348 آیین دادرسی مدنی" -> {"article_no": "348", "code": "آیین دادرسی مدنی", ...}
    
    Args:
        article_str: Law article string in Persian
    
    Returns:
        Dict with article_no, code, label
    """
    # Try to extract article number and law code
    # Pattern: "ماده NUMBER (rest)"
    match = re.search(r'ماده\s+(\d+)\s+(.+)', article_str)
    
    if match:
        article_no = match.group(1)
        code = match.group(2).strip()
        
        return {
            "article_no": article_no,
            "code": code,
            "label": article_str
        }
    else:
        # Fallback: use entire string as label
        return {
            "article_no": "",
            "code": "",
            "label": article_str
        }


def _generate_verdict_id(verdict_struct: Dict[str, Any]) -> str:
    """
    Generate a unique ID for a verdict.
    
    Uses _source.filepath if available, otherwise generates a hash
    from case_meta properties.
    
    Args:
        verdict_struct: Parsed verdict dictionary
    
    Returns:
        Unique verdict ID string
    """
    # Try to use source filepath
    source = verdict_struct.get("_source", {})
    filepath = source.get("filepath")
    
    if filepath:
        # Use filename stem as ID
        import os
        filename = os.path.basename(filepath)
        verdict_id = os.path.splitext(filename)[0]
        return verdict_id
    
    # Fallback: generate hash from case_meta
    case_meta = verdict_struct.get("case_meta", {})
    court_level = case_meta.get("court_level", "")
    case_type = case_meta.get("case_type", "")
    procedure_stage = case_meta.get("procedure_stage", "")
    
    # Create a hash
    hash_input = f"{court_level}|{case_type}|{procedure_stage}"
    verdict_id = hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:16]
    
    return verdict_id


def upsert_verdict_struct(verdict_struct: Dict[str, Any]) -> str:
    """
    Upsert a parsed verdict structure into the Neo4j graph database.
    
    This is the main integration function for Bootstrap Verdict Ingestion (Scenario B).
    It is called by orchestrator.bootstrap_verdict_dataloader when --with-graph is used.
    
    Graph Schema:
    -------------
    Nodes:
        - :Verdict (properties: verdict_id, court_level, procedure_stage, case_type, is_final, finality_basis)
        - :LawArticle (properties: label, code, article_no)
        - :Person (properties: display_name, father_name, role)
        - :Tag (properties: name)
    
    Relationships:
        - (Verdict)-[:REFERS_TO]->(LawArticle)
        - (Verdict)-[:HAS_PARTY {role: "..."}]->(Person)
        - (Verdict)-[:HAS_TAG]->(Tag)
    
    Idempotency:
    -----------
    Uses MERGE operations to ensure that re-ingesting the same verdict
    updates existing nodes rather than creating duplicates.
    
    Args:
        verdict_struct: Parsed verdict dictionary (from minimal_verdict_parser.parse_verdict_file)
    
    Raises:
        Exception: If graph ingestion fails (caller should catch and log)
    
    Example Usage:
        >>> from mahoun.graph.neo4j.operations import upsert_verdict_struct
        >>> verdict_struct = parse_verdict_file("verdict.txt")
        >>> upsert_verdict_struct(verdict_struct)
        [INFO] Upserted verdict verdict_001 into graph
    """
    logger.info(f"[GRAPH] Upserting verdict into Neo4j")
    
    # Generate unique verdict ID
    verdict_id = _generate_verdict_id(verdict_struct)
    logger.debug(f"[GRAPH] Verdict ID: {verdict_id}")
    
    # Get connection
    try:
        conn = get_connection()
    except Exception as e:
        logger.error(f"[GRAPH] Failed to get Neo4j connection: {e}")
        raise
    
    # ========================================================================
    # Step 1: Create/Update Verdict node
    # ========================================================================
    case_meta = verdict_struct.get("case_meta", {})
    
    verdict_props = {
        "verdict_id": verdict_id,
        "court_level": case_meta.get("court_level", "نامشخص"),
        "procedure_stage": case_meta.get("procedure_stage", "نامشخص"),
        "case_type": case_meta.get("case_type", "نامشخص"),
        "is_final": case_meta.get("is_final", False),
        "finality_basis": case_meta.get("finality_basis", "") or ""
    }
    
    try:
        query_verdict = """
        MERGE (v:Verdict {verdict_id: $verdict_id})
        SET v.court_level = $court_level,
            v.procedure_stage = $procedure_stage,
            v.case_type = $case_type,
            v.is_final = $is_final,
            v.finality_basis = $finality_basis,
            v.updated_at = datetime()
        ON CREATE SET v.created_at = datetime()
        RETURN v.verdict_id as verdict_id
        """
        
        result = conn.execute_query(query_verdict, verdict_props)
        logger.debug(f"[GRAPH] Created/updated Verdict node: {verdict_id}")
    
    except Exception as e:
        logger.error(f"[GRAPH] Failed to create Verdict node: {e}")
        raise
    
    # ========================================================================
    # Step 2: Create LawArticle nodes and REFERS_TO relationships
    # ========================================================================
    legal_refs = verdict_struct.get("legal_references", {})
    all_articles: List[Any] = []
    # Collect all law articles
    all_articles.extend(legal_refs.get("substantive_law", []))
    all_articles.extend(legal_refs.get("procedural_law", []))
    # Note: fiqh_principles could also be treated as a separate node type
    # For now, we'll skip them or treat them as tags
    
    for article_str in all_articles[:50]:  # Limit to 50 to avoid too many nodes
        try:
            parsed = _parse_law_article(article_str)
            
            query_article = """
            MERGE (a:LawArticle {label: $label})
            SET a.code = $code,
                a.article_no = $article_no,
                a.updated_at = datetime()
            ON CREATE SET a.created_at = datetime()
            WITH a
            MATCH (v:Verdict {verdict_id: $verdict_id})
            MERGE (v)-[r:REFERS_TO]->(a)
            ON CREATE SET r.created_at = datetime()
            """
            
            params = {
                "label": parsed["label"],
                "code": parsed["code"],
                "article_no": parsed["article_no"],
                "verdict_id": verdict_id
            }
            
            conn.execute_query(query_article, params)
        
        except Exception as e:
            logger.warning(f"[GRAPH] Failed to create LawArticle for '{article_str}': {e}")
            # Continue with other articles
    
    logger.debug(f"[GRAPH] Created {len(all_articles)} LawArticle relationships")
    
    # ========================================================================
    # Step 3: Create Tag nodes and HAS_TAG relationships
    # ========================================================================
    system_tags = verdict_struct.get("system_tags", [])
    
    for tag in system_tags[:30]:  # Limit to 30 tags
        try:
            query_tag = """
            MERGE (t:Tag {name: $name})
            ON CREATE SET t.created_at = datetime()
            WITH t
            MATCH (v:Verdict {verdict_id: $verdict_id})
            MERGE (v)-[r:HAS_TAG]->(t)
            ON CREATE SET r.created_at = datetime()
            """
            
            params = {
                "name": tag,
                "verdict_id": verdict_id
            }
            
            conn.execute_query(query_tag, params)
        
        except Exception as e:
            logger.warning(f"[GRAPH] Failed to create Tag for '{tag}': {e}")
            # Continue with other tags
    
    logger.debug(f"[GRAPH] Created {len(system_tags)} Tag relationships")
    
    # ========================================================================
    # Step 4: Create Person nodes and HAS_PARTY relationships
    # ========================================================================
    parties = verdict_struct.get("parties", {})
    
    # Third party objector
    objector = parties.get("third_party_objector")
    if objector and objector.get("name"):
        try:
            display_name = f"{objector.get('title', '')} {objector.get('name', '')}".strip()
            father_name = objector.get("father_name", "")
            
            query_person = """
            MERGE (p:Person {display_name: $display_name, father_name: $father_name})
            ON CREATE SET p.created_at = datetime()
            WITH p
            MATCH (v:Verdict {verdict_id: $verdict_id})
            MERGE (v)-[r:HAS_PARTY {role: $role}]->(p)
            ON CREATE SET r.created_at = datetime()
            """
            
            params = {
                "display_name": display_name,
                "father_name": father_name,
                "verdict_id": verdict_id,
                "role": "third_party_objector"
            }
            
            conn.execute_query(query_person, params)
            logger.debug(f"[GRAPH] Created Person node: {display_name}")
        
        except Exception as e:
            logger.warning(f"[GRAPH] Failed to create Person (objector): {e}")
    
    # Third party objector attorney
    attorney = parties.get("third_party_objector_attorney")
    if attorney and attorney.get("name"):
        try:
            display_name = f"{attorney.get('title', '')} {attorney.get('name', '')}".strip()
            father_name = attorney.get("father_name", "")
            
            query_person = """
            MERGE (p:Person {display_name: $display_name, father_name: $father_name})
            ON CREATE SET p.created_at = datetime()
            WITH p
            MATCH (v:Verdict {verdict_id: $verdict_id})
            MERGE (v)-[r:HAS_PARTY {role: $role}]->(p)
            ON CREATE SET r.created_at = datetime()
            """
            
            params = {
                "display_name": display_name,
                "father_name": father_name,
                "verdict_id": verdict_id,
                "role": "third_party_objector_attorney"
            }
            
            conn.execute_query(query_person, params)
            logger.debug(f"[GRAPH] Created Person node: {display_name}")
        
        except Exception as e:
            logger.warning(f"[GRAPH] Failed to create Person (attorney): {e}")
    
    # Respondents
    respondents = parties.get("respondents", [])
    for resp in respondents[:10]:  # Limit to 10 respondents
        if resp and resp.get("name"):
            try:
                display_name = f"{resp.get('title', '')} {resp.get('name', '')}".strip()
                father_name = resp.get("father_name", "")
                
                query_person = """
                MERGE (p:Person {display_name: $display_name, father_name: $father_name})
                ON CREATE SET p.created_at = datetime()
                WITH p
                MATCH (v:Verdict {verdict_id: $verdict_id})
                MERGE (v)-[r:HAS_PARTY {role: $role}]->(p)
                ON CREATE SET r.created_at = datetime()
                """
                
                params = {
                    "display_name": display_name,
                    "father_name": father_name,
                    "verdict_id": verdict_id,
                    "role": "respondent"
                }
                
                conn.execute_query(query_person, params)
            
            except Exception as e:
                logger.warning(f"[GRAPH] Failed to create Person (respondent): {e}")
    
    # Respondents attorneys
    resp_attorneys = parties.get("respondents_attorneys", [])
    for att in resp_attorneys[:10]:
        if att and att.get("name"):
            try:
                display_name = f"{att.get('title', '')} {att.get('name', '')}".strip()
                father_name = att.get("father_name", "")
                
                query_person = """
                MERGE (p:Person {display_name: $display_name, father_name: $father_name})
                ON CREATE SET p.created_at = datetime()
                WITH p
                MATCH (v:Verdict {verdict_id: $verdict_id})
                MERGE (v)-[r:HAS_PARTY {role: $role}]->(p)
                ON CREATE SET r.created_at = datetime()
                """
                
                params = {
                    "display_name": display_name,
                    "father_name": father_name,
                    "verdict_id": verdict_id,
                    "role": "respondent_attorney"
                }
                
                conn.execute_query(query_person, params)
            
            except Exception as e:
                logger.warning(f"[GRAPH] Failed to create Person (respondent attorney): {e}")
    
    logger.debug(f"[GRAPH] Created Person nodes and HAS_PARTY relationships")
    
    # ========================================================================
    # Done!
    # ========================================================================
    logger.info(f"[GRAPH] ✓ Upserted verdict {verdict_id} into graph with all relationships")
    
    return verdict_id


# ============================================================================
# Read Helpers for Verdict Search Enrichment (added to GraphOperations class)
# ============================================================================

def _graph_get_law_articles_for_verdict(self, verdict_id: str) -> List[str]:
    """
    Get all law articles referenced by a verdict.
    
    Args:
        verdict_id: Unique identifier of the verdict
    
    Returns:
        List of law article labels, e.g., ["ماده 348 قانون آیین دادرسی مدنی", ...]
    """
    query = """
    MATCH (v:Verdict {verdict_id: $verdict_id})-[:REFERS_TO]->(a:LawArticle)
    RETURN a.label AS label
    """
    
    try:
        results = self.conn.execute_query(query, {"verdict_id": verdict_id})
        articles = [r["label"] for r in results if r.get("label")]
        logger.debug(f"[GRAPH] Found {len(articles)} law articles for verdict {verdict_id}")
        return articles
    except Exception as e:
        logger.warning(f"[GRAPH] Failed to get law articles for {verdict_id}: {e}")
        return []


def _graph_get_tags_for_verdict(self, verdict_id: str) -> List[str]:
    """
    Get all tags associated with a verdict.
    
    Args:
        verdict_id: Unique identifier of the verdict
    
    Returns:
        List of tag names, e.g., ["اعتراض ثالث اجرایی", "رفع توقیف", ...]
    """
    query = """
    MATCH (v:Verdict {verdict_id: $verdict_id})-[:HAS_TAG]->(t:Tag)
    RETURN t.name AS name
    """
    
    try:
        results = self.conn.execute_query(query, {"verdict_id": verdict_id})
        tags = [r["name"] for r in results if r.get("name")]
        logger.debug(f"[GRAPH] Found {len(tags)} tags for verdict {verdict_id}")
        return tags
    except Exception as e:
        logger.warning(f"[GRAPH] Failed to get tags for {verdict_id}: {e}")
        return []


def _graph_get_parties_for_verdict(self, verdict_id: str) -> List[Dict[str, str]]:
    """
    Get all parties involved in a verdict.
    
    Args:
        verdict_id: Unique identifier of the verdict
    
    Returns:
        List of party dicts with display_name, father_name, and role
    """
    query = """
    MATCH (v:Verdict {verdict_id: $verdict_id})-[r:HAS_PARTY]->(p:Person)
    RETURN p.display_name AS display_name, 
           p.father_name AS father_name, 
           r.role AS role
    """
    
    try:
        results = self.conn.execute_query(query, {"verdict_id": verdict_id})
        parties = [
            {
                "display_name": r.get("display_name", ""),
                "father_name": r.get("father_name", ""),
                "role": r.get("role", "")
            }
            for r in results
        ]
        logger.debug(f"[GRAPH] Found {len(parties)} parties for verdict {verdict_id}")
        return parties
    except Exception as e:
        logger.warning(f"[GRAPH] Failed to get parties for {verdict_id}: {e}")
        return []


def _graph_get_verdict_by_id(self, verdict_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a verdict node by its ID.
    
    Args:
        verdict_id: Unique identifier of the verdict
    
    Returns:
        Dict with verdict properties, or None if not found
    """
    query = """
    MATCH (v:Verdict {verdict_id: $verdict_id})
    RETURN v
    """
    
    try:
        results = self.conn.execute_query(query, {"verdict_id": verdict_id})
        if results:
            return dict(results[0]["v"])
        return None
    except Exception as e:
        logger.warning(f"[GRAPH] Failed to get verdict {verdict_id}: {e}")
        return None


# Attach read methods to GraphOperations class
GraphOperations.get_law_articles_for_verdict = _graph_get_law_articles_for_verdict
GraphOperations.get_tags_for_verdict = _graph_get_tags_for_verdict
GraphOperations.get_parties_for_verdict = _graph_get_parties_for_verdict
GraphOperations.get_verdict_by_id = _graph_get_verdict_by_id
