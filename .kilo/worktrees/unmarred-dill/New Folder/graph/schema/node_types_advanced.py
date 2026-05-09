"""
Advanced Graph Node Types and Schema Definition
===============================================

Enterprise-grade Neo4j schema with:
- Comprehensive node types and relationships
- Property constraints and validation
- Index definitions
- Relationship types with semantics
- Query patterns and templates
"""

from enum import Enum
from dataclasses import dataclass, field


class NodeType(str, Enum):
    """
    Comprehensive node types in the legal knowledge graph
    
    Organized by domain for better maintainability
    """
    
    # ========== Legal Documents ==========
    LAW = "Law"                          # قانون
    ARTICLE = "Article"                  # ماده قانونی
    CLAUSE = "Clause"                    # بند
    NOTE = "Note"                        # تبصره
    CHAPTER = "Chapter"                  # فصل
    SECTION = "Section"                  # بخش
    AMENDMENT = "Amendment"              # اصلاحیه
    REGULATION = "Regulation"            # آیین‌نامه
    DECREE = "Decree"                    # مصوبه
    CIRCULAR = "Circular"                # بخشنامه
    
    # ========== Court System ==========
    VERDICT = "Verdict"                  # رأی/حکم
    COURT = "Court"                      # دادگاه
    CASE = "Case"                        # پرونده
    BRANCH = "Branch"                    # شعبه دادگاه
    HEARING = "Hearing"                  # جلسه دادرسی
    APPEAL = "Appeal"                    # تجدیدنظر
    CASSATION = "Cassation"              # فرجام
    
    # ========== People & Roles ==========
    PERSON = "Person"                    # شخص (عمومی)
    JUDGE = "Judge"                      # قاضی/مستشار
    LAWYER = "Lawyer"                    # وکیل دادگستری
    PLAINTIFF = "Plaintiff"              # شاکی/خواهان
    DEFENDANT = "Defendant"              # متهم/خوانده
    WITNESS = "Witness"                  # شاهد
    EXPERT = "Expert"                    # کارشناس
    PROSECUTOR = "Prosecutor"            # دادستان
    NOTARY = "Notary"                    # سردفتر
    
    # ========== Organizations ==========
    ORGANIZATION = "Organization"        # سازمان
    GOVERNMENT_BODY = "GovernmentBody"   # نهاد دولتی
    MINISTRY = "Ministry"                # وزارتخانه
    PARLIAMENT = "Parliament"            # مجلس
    JUDICIARY = "Judiciary"              # قوه قضائیه
    LAW_FIRM = "LawFirm"                # دفتر وکالت
    
    # ========== Legal Concepts ==========
    LEGAL_CONCEPT = "LegalConcept"       # مفهوم حقوقی
    LEGAL_PRINCIPLE = "LegalPrinciple"   # اصل حقوقی
    LEGAL_DOCTRINE = "LegalDoctrine"     # نظریه حقوقی
    PRECEDENT = "Precedent"              # رویه قضایی
    LEGAL_TERM = "LegalTerm"             # اصطلاح حقوقی
    
    # ========== Metadata & Context ==========
    LOCATION = "Location"                # مکان
    DATE = "Date"                        # تاریخ
    TIME_PERIOD = "TimePeriod"           # دوره زمانی
    EVENT = "Event"                      # رویداد
    TOPIC = "Topic"                      # موضوع
    CATEGORY = "Category"                # دسته‌بندی
    TAG = "Tag"                          # برچسب
    
    # ========== References ==========
    CITATION = "Citation"                # استناد
    REFERENCE = "Reference"              # ارجاع
    FOOTNOTE = "Footnote"                # پانویس
    BIBLIOGRAPHY = "Bibliography"        # منابع


class RelationshipType(str, Enum):
    """
    Comprehensive relationship types with semantic meaning
    """
    
    # ========== Document Relationships ==========
    CONTAINS = "CONTAINS"                # Law CONTAINS Article
    PART_OF = "PART_OF"                  # Article PART_OF Law
    AMENDS = "AMENDS"                    # Amendment AMENDS Law
    REPEALS = "REPEALS"                  # Law REPEALS Law
    SUPERSEDES = "SUPERSEDES"            # Law SUPERSEDES Law
    IMPLEMENTS = "IMPLEMENTS"            # Regulation IMPLEMENTS Law
    REFERENCES = "REFERENCES"            # Article REFERENCES Article
    
    # ========== Citation Relationships ==========
    CITES = "CITES"                      # Verdict CITES Article
    CITED_BY = "CITED_BY"                # Article CITED_BY Verdict
    SUPPORTS = "SUPPORTS"                # Verdict SUPPORTS Verdict
    CONTRADICTS = "CONTRADICTS"          # Verdict CONTRADICTS Verdict
    DISTINGUISHES = "DISTINGUISHES"      # Verdict DISTINGUISHES Verdict
    FOLLOWS = "FOLLOWS"                  # Verdict FOLLOWS Precedent
    
    # ========== Court Relationships ==========
    ISSUED_BY = "ISSUED_BY"              # Verdict ISSUED_BY Court
    HEARD_IN = "HEARD_IN"                # Case HEARD_IN Court
    PRESIDED_BY = "PRESIDED_BY"          # Case PRESIDED_BY Judge
    REPRESENTED_BY = "REPRESENTED_BY"    # Party REPRESENTED_BY Lawyer
    APPEALED_TO = "APPEALED_TO"          # Verdict APPEALED_TO Court
    OVERTURNS = "OVERTURNS"              # Verdict OVERTURNS Verdict
    CONFIRMS = "CONFIRMS"                # Verdict CONFIRMS Verdict
    
    # ========== Party Relationships ==========
    PLAINTIFF_IN = "PLAINTIFF_IN"        # Person PLAINTIFF_IN Case
    DEFENDANT_IN = "DEFENDANT_IN"        # Person DEFENDANT_IN Case
    WITNESS_IN = "WITNESS_IN"            # Person WITNESS_IN Case
    EXPERT_IN = "EXPERT_IN"              # Person EXPERT_IN Case
    
    # ========== Organizational Relationships ==========
    WORKS_FOR = "WORKS_FOR"              # Person WORKS_FOR Organization
    MEMBER_OF = "MEMBER_OF"              # Person MEMBER_OF Organization
    AFFILIATED_WITH = "AFFILIATED_WITH"  # Organization AFFILIATED_WITH Organization
    REGULATES = "REGULATES"              # Organization REGULATES Domain
    
    # ========== Conceptual Relationships ==========
    RELATED_TO = "RELATED_TO"            # Concept RELATED_TO Concept
    DEFINES = "DEFINES"                  # Article DEFINES Concept
    APPLIES_TO = "APPLIES_TO"            # Law APPLIES_TO Domain
    BASED_ON = "BASED_ON"                # Concept BASED_ON Principle
    DERIVED_FROM = "DERIVED_FROM"        # Concept DERIVED_FROM Concept
    
    # ========== Temporal Relationships ==========
    OCCURRED_ON = "OCCURRED_ON"          # Event OCCURRED_ON Date
    VALID_FROM = "VALID_FROM"            # Law VALID_FROM Date
    VALID_UNTIL = "VALID_UNTIL"          # Law VALID_UNTIL Date
    PRECEDED_BY = "PRECEDED_BY"          # Event PRECEDED_BY Event
    FOLLOWED_BY = "FOLLOWED_BY"          # Event FOLLOWED_BY Event
    
    # ========== Spatial Relationships ==========
    LOCATED_IN = "LOCATED_IN"            # Court LOCATED_IN Location
    JURISDICTION_OVER = "JURISDICTION_OVER"  # Court JURISDICTION_OVER Location
    
    # ========== Semantic Relationships ==========
    SIMILAR_TO = "SIMILAR_TO"            # Document SIMILAR_TO Document
    CO_OCCURS_WITH = "CO_OCCURS_WITH"    # Term CO_OCCURS_WITH Term
    MENTIONS = "MENTIONS"                # Document MENTIONS Entity


@dataclass
class NodeSchema:
    """Schema definition for a node type"""
    node_type: NodeType
    required_properties: List[str]
    optional_properties: List[str] = field(default_factory=list)
    unique_properties: List[str] = field(default_factory=list)
    indexed_properties: List[str] = field(default_factory=list)
    fulltext_properties: List[str] = field(default_factory=list)
    vector_properties: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class RelationshipSchema:
    """Schema definition for a relationship type"""
    relationship_type: RelationshipType
    from_node: NodeType
    to_node: NodeType
    required_properties: List[str] = field(default_factory=list)
    optional_properties: List[str] = field(default_factory=list)
    description: str = ""
    cardinality: str = "many-to-many"  # one-to-one, one-to-many, many-to-many



# ============================================================================
# Comprehensive Node Schemas
# ============================================================================

NODE_SCHEMAS: Dict[NodeType, NodeSchema] = {
    NodeType.LAW: NodeSchema(
        node_type=NodeType.LAW,
        required_properties=["id", "name", "law_number"],
        optional_properties=[
            "name_en", "approval_date", "publication_date", "effective_date",
            "category", "subcategory", "status", "summary", "full_text",
            "keywords", "version", "metadata"
        ],
        unique_properties=["id", "law_number"],
        indexed_properties=["name", "category", "status", "approval_date"],
        fulltext_properties=["name", "summary", "full_text"],
        vector_properties=["embedding"],
        constraints=[
            "CONSTRAINT ON (n:Law) ASSERT n.id IS UNIQUE",
            "CONSTRAINT ON (n:Law) ASSERT n.law_number IS UNIQUE",
            "CONSTRAINT ON (n:Law) ASSERT EXISTS(n.name)",
        ],
        description="Legal law document"
    ),
    
    NodeType.ARTICLE: NodeSchema(
        node_type=NodeType.ARTICLE,
        required_properties=["id", "article_number", "content"],
        optional_properties=[
            "title", "law_id", "chapter", "section", "notes",
            "order_index", "metadata"
        ],
        unique_properties=["id"],
        indexed_properties=["article_number", "law_id", "chapter"],
        fulltext_properties=["title", "content", "notes"],
        vector_properties=["embedding"],
        constraints=[
            "CONSTRAINT ON (n:Article) ASSERT n.id IS UNIQUE",
            "CONSTRAINT ON (n:Article) ASSERT EXISTS(n.content)",
        ],
        description="Article within a law"
    ),
    
    NodeType.VERDICT: NodeSchema(
        node_type=NodeType.VERDICT,
        required_properties=["id", "verdict_number", "case_number", "verdict_date"],
        optional_properties=[
            "court_name", "court_type", "branch_number", "case_type",
            "subject", "summary", "full_text", "result", "judges",
            "parties", "cited_articles", "cited_laws", "is_precedent",
            "confidence_score", "metadata"
        ],
        unique_properties=["id", "verdict_number"],
        indexed_properties=[
            "verdict_number", "case_number", "court_name", "verdict_date",
            "case_type", "result", "is_precedent"
        ],
        fulltext_properties=["subject", "summary", "full_text"],
        vector_properties=["embedding"],
        constraints=[
            "CONSTRAINT ON (n:Verdict) ASSERT n.id IS UNIQUE",
            "CONSTRAINT ON (n:Verdict) ASSERT n.verdict_number IS UNIQUE",
            "CONSTRAINT ON (n:Verdict) ASSERT EXISTS(n.verdict_date)",
        ],
        description="Court verdict/judgment"
    ),
    
    NodeType.COURT: NodeSchema(
        node_type=NodeType.COURT,
        required_properties=["id", "name"],
        optional_properties=[
            "court_type", "level", "jurisdiction", "location",
            "established_date", "metadata"
        ],
        unique_properties=["id"],
        indexed_properties=["name", "court_type", "level"],
        fulltext_properties=["name"],
        constraints=[
            "CONSTRAINT ON (n:Court) ASSERT n.id IS UNIQUE",
            "CONSTRAINT ON (n:Court) ASSERT EXISTS(n.name)",
        ],
        description="Court institution"
    ),
    
    NodeType.PERSON: NodeSchema(
        node_type=NodeType.PERSON,
        required_properties=["id", "name"],
        optional_properties=[
            "name_en", "role", "title", "organization", "specialization",
            "license_number", "metadata"
        ],
        unique_properties=["id"],
        indexed_properties=["name", "role"],
        fulltext_properties=["name"],
        constraints=[
            "CONSTRAINT ON (n:Person) ASSERT n.id IS UNIQUE",
            "CONSTRAINT ON (n:Person) ASSERT EXISTS(n.name)",
        ],
        description="Person entity"
    ),
    
    NodeType.LEGAL_CONCEPT: NodeSchema(
        node_type=NodeType.LEGAL_CONCEPT,
        required_properties=["id", "name"],
        optional_properties=[
            "name_en", "definition", "category", "related_concepts",
            "examples", "metadata"
        ],
        unique_properties=["id"],
        indexed_properties=["name", "category"],
        fulltext_properties=["name", "definition"],
        vector_properties=["embedding"],
        constraints=[
            "CONSTRAINT ON (n:LegalConcept) ASSERT n.id IS UNIQUE",
            "CONSTRAINT ON (n:LegalConcept) ASSERT EXISTS(n.name)",
        ],
        description="Legal concept or term"
    ),
}


# ============================================================================
# Comprehensive Relationship Schemas
# ============================================================================

RELATIONSHIP_SCHEMAS: List[RelationshipSchema] = [
    # Document relationships
    RelationshipSchema(
        relationship_type=RelationshipType.CONTAINS,
        from_node=NodeType.LAW,
        to_node=NodeType.ARTICLE,
        required_properties=["order_index"],
        optional_properties=["chapter", "section"],
        description="Law contains articles",
        cardinality="one-to-many"
    ),
    
    RelationshipSchema(
        relationship_type=RelationshipType.CITES,
        from_node=NodeType.VERDICT,
        to_node=NodeType.ARTICLE,
        required_properties=["confidence"],
        optional_properties=[
            "context", "citation_type", "relevance_score",
            "extracted_by", "verified"
        ],
        description="Verdict cites article",
        cardinality="many-to-many"
    ),
    
    RelationshipSchema(
        relationship_type=RelationshipType.AMENDS,
        from_node=NodeType.AMENDMENT,
        to_node=NodeType.LAW,
        required_properties=["amendment_date"],
        optional_properties=["description", "articles_affected"],
        description="Amendment modifies law",
        cardinality="many-to-one"
    ),
    
    RelationshipSchema(
        relationship_type=RelationshipType.OVERTURNS,
        from_node=NodeType.VERDICT,
        to_node=NodeType.VERDICT,
        required_properties=["overturn_date"],
        optional_properties=["reason", "court_level"],
        description="Verdict overturns another verdict",
        cardinality="one-to-one"
    ),
    
    RelationshipSchema(
        relationship_type=RelationshipType.ISSUED_BY,
        from_node=NodeType.VERDICT,
        to_node=NodeType.COURT,
        required_properties=["issue_date"],
        optional_properties=["branch_number", "judges"],
        description="Verdict issued by court",
        cardinality="many-to-one"
    ),
    
    RelationshipSchema(
        relationship_type=RelationshipType.PRESIDED_BY,
        from_node=NodeType.CASE,
        to_node=NodeType.JUDGE,
        required_properties=[],
        optional_properties=["role", "panel_position"],
        description="Case presided by judge",
        cardinality="many-to-many"
    ),
    
    RelationshipSchema(
        relationship_type=RelationshipType.SIMILAR_TO,
        from_node=NodeType.VERDICT,
        to_node=NodeType.VERDICT,
        required_properties=["similarity_score"],
        optional_properties=["similarity_type", "computed_at"],
        description="Semantic similarity between verdicts",
        cardinality="many-to-many"
    ),
]


# ============================================================================
# Node Type Groups and Categories
# ============================================================================

NODE_TYPE_GROUPS = {
    "legal_documents": [
        NodeType.LAW, NodeType.ARTICLE, NodeType.CLAUSE, NodeType.NOTE,
        NodeType.CHAPTER, NodeType.SECTION, NodeType.AMENDMENT,
        NodeType.REGULATION, NodeType.DECREE, NodeType.CIRCULAR,
    ],
    "court_system": [
        NodeType.VERDICT, NodeType.COURT, NodeType.CASE, NodeType.BRANCH,
        NodeType.HEARING, NodeType.APPEAL, NodeType.CASSATION,
    ],
    "people": [
        NodeType.PERSON, NodeType.JUDGE, NodeType.LAWYER,
        NodeType.PLAINTIFF, NodeType.DEFENDANT, NodeType.WITNESS,
        NodeType.EXPERT, NodeType.PROSECUTOR, NodeType.NOTARY,
    ],
    "organizations": [
        NodeType.ORGANIZATION, NodeType.GOVERNMENT_BODY, NodeType.MINISTRY,
        NodeType.PARLIAMENT, NodeType.JUDICIARY, NodeType.LAW_FIRM,
    ],
    "concepts": [
        NodeType.LEGAL_CONCEPT, NodeType.LEGAL_PRINCIPLE,
        NodeType.LEGAL_DOCTRINE, NodeType.PRECEDENT, NodeType.LEGAL_TERM,
    ],
    "metadata": [
        NodeType.LOCATION, NodeType.DATE, NodeType.TIME_PERIOD,
        NodeType.EVENT, NodeType.TOPIC, NodeType.CATEGORY, NodeType.TAG,
    ],
    "references": [
        NodeType.CITATION, NodeType.REFERENCE, NodeType.FOOTNOTE,
        NodeType.BIBLIOGRAPHY,
    ],
}


# ============================================================================
# Cypher Query Templates
# ============================================================================

CYPHER_TEMPLATES = {
    "create_law": """
        CREATE (l:Law {
            id: $id,
            name: $name,
            law_number: $law_number,
            approval_date: date($approval_date),
            category: $category,
            status: $status,
            created_at: datetime()
        })
        RETURN l
    """,
    
    "create_article": """
        MATCH (l:Law {id: $law_id})
        CREATE (a:Article {
            id: $id,
            article_number: $article_number,
            content: $content,
            order_index: $order_index,
            created_at: datetime()
        })
        CREATE (l)-[:CONTAINS {order_index: $order_index}]->(a)
        RETURN a
    """,
    
    "create_citation": """
        MATCH (v:Verdict {id: $verdict_id})
        MATCH (a:Article {id: $article_id})
        MERGE (v)-[c:CITES {
            confidence: $confidence,
            context: $context,
            citation_type: $citation_type,
            created_at: datetime()
        }]->(a)
        RETURN c
    """,
    
    "find_related_articles": """
        MATCH (a:Article {id: $article_id})
        MATCH (a)<-[:CITES]-(v:Verdict)-[:CITES]->(related:Article)
        WHERE related.id <> $article_id
        WITH related, count(v) as citation_count
        ORDER BY citation_count DESC
        LIMIT $limit
        RETURN related, citation_count
    """,
    
    "find_precedents": """
        MATCH (v:Verdict {id: $verdict_id})-[:CITES]->(a:Article)
        MATCH (precedent:Verdict {is_precedent: true})-[:CITES]->(a)
        WHERE precedent.id <> $verdict_id
        WITH precedent, count(a) as common_citations
        ORDER BY common_citations DESC, precedent.verdict_date DESC
        LIMIT $limit
        RETURN precedent, common_citations
    """,
    
    "citation_network": """
        MATCH (l:Law)-[:CONTAINS]->(a:Article)<-[c:CITES]-(v:Verdict)
        WITH l, count(DISTINCT v) as citation_count,
             avg(c.confidence) as avg_confidence
        ORDER BY citation_count DESC
        LIMIT $limit
        RETURN l.name, l.law_number, citation_count, avg_confidence
    """,
}


# ============================================================================
# Index and Constraint Creation Queries
# ============================================================================

def get_constraint_queries() -> List[str]:
    """Generate constraint creation queries"""
    queries = []
    
    for node_type, schema in NODE_SCHEMAS.items():
        # Unique constraints
        for prop in schema.unique_properties:
            queries.append(
                f"CREATE CONSTRAINT {node_type.value.lower()}_{prop}_unique "
                f"IF NOT EXISTS FOR (n:{node_type.value}) "
                f"REQUIRE n.{prop} IS UNIQUE"
            )
        
        # Existence constraints
        for prop in schema.required_properties:
            queries.append(
                f"CREATE CONSTRAINT {node_type.value.lower()}_{prop}_exists "
                f"IF NOT EXISTS FOR (n:{node_type.value}) "
                f"REQUIRE n.{prop} IS NOT NULL"
            )
    
    return queries


def get_index_queries() -> List[str]:
    """Generate index creation queries"""
    queries = []
    
    for node_type, schema in NODE_SCHEMAS.items():
        # Regular indexes
        for prop in schema.indexed_properties:
            queries.append(
                f"CREATE INDEX {node_type.value.lower()}_{prop}_index "
                f"IF NOT EXISTS FOR (n:{node_type.value}) ON (n.{prop})"
            )
        
        # Full-text indexes
        if schema.fulltext_properties:
            props_str = ", ".join([f"n.{p}" for p in schema.fulltext_properties])
            queries.append(
                f"CREATE FULLTEXT INDEX {node_type.value.lower()}_fulltext "
                f"IF NOT EXISTS FOR (n:{node_type.value}) ON EACH [{props_str}]"
            )
        
        # Vector indexes
        for prop in schema.vector_properties:
            queries.append(
                f"CREATE VECTOR INDEX {node_type.value.lower()}_{prop}_vector "
                f"IF NOT EXISTS FOR (n:{node_type.value}) ON (n.{prop}) "
                f"OPTIONS {{indexConfig: {{`vector.dimensions`: 1024, "
                f"`vector.similarity_function`: 'cosine'}}}}"
            )
    
    return queries


# ============================================================================
# Validation Functions
# ============================================================================

def validate_node_properties(node_type: NodeType, properties: Dict[str, Any]) -> List[str]:
    """Validate node properties against schema"""
    errors = []
    
    if node_type not in NODE_SCHEMAS:
        return [f"Unknown node type: {node_type}"]
    
    schema = NODE_SCHEMAS[node_type]
    
    # Check required properties
    for prop in schema.required_properties:
        if prop not in properties:
            errors.append(f"Missing required property: {prop}")
    
    # Check property types (basic validation)
    for prop, value in properties.items():
        if prop not in schema.required_properties + schema.optional_properties:
            errors.append(f"Unknown property: {prop}")
    
    return errors


def get_node_schema(node_type: NodeType) -> Optional[NodeSchema]:
    """Get schema for a node type"""
    return NODE_SCHEMAS.get(node_type)


def get_relationship_schemas_for_nodes(
    from_node: NodeType,
    to_node: NodeType
) -> List[RelationshipSchema]:
    """Get valid relationship schemas between two node types"""
    return [
        schema for schema in RELATIONSHIP_SCHEMAS
        if schema.from_node == from_node and schema.to_node == to_node
    ]
