"""
Graph Node Types Definition
============================

Defines all node types (entity labels) in the knowledge graph.
"""

from enum import Enum


class NodeType(str, Enum):
    """
    Node types in the legal knowledge graph
    
    Based on analysis of legal documents and court verdicts.
    """
    
    # Legal Documents
    LAW = "Law"                      # قانون
    ARTICLE = "Article"              # ماده قانونی
    CLAUSE = "Clause"                # بند
    NOTE = "Note"                    # تبصره
    
    # Court System
    VERDICT = "Verdict"              # رأی/حکم
    COURT = "Court"                  # دادگاه
    CASE = "Case"                    # پرونده
    BRANCH = "Branch"                # شعبه دادگاه
    
    # People
    PERSON = "Person"                # شخص (عمومی)
    JUDGE = "Judge"                  # قاضی/مستشار
    LAWYER = "Lawyer"                # وکیل دادگستری
    PLAINTIFF = "Plaintiff"          # شاکی/خواهان
    DEFENDANT = "Defendant"          # متهم/خوانده
    WITNESS = "Witness"              # شاهد
    
    # Organizations
    ORGANIZATION = "Organization"    # سازمان
    GOVERNMENT_BODY = "GovernmentBody"  # نهاد دولتی
    
    # Other
    LOCATION = "Location"            # مکان
    DATE = "Date"                    # تاریخ
    LEGAL_CONCEPT = "LegalConcept"   # مفهوم حقوقی


# Node type groups for easier querying
NODE_TYPE_GROUPS = {
    "legal_documents": [
        NodeType.LAW,
        NodeType.ARTICLE,
        NodeType.CLAUSE,
        NodeType.NOTE,
    ],
    "court_system": [
        NodeType.VERDICT,
        NodeType.COURT,
        NodeType.CASE,
        NodeType.BRANCH,
    ],
    "people": [
        NodeType.PERSON,
        NodeType.JUDGE,
        NodeType.LAWYER,
        NodeType.PLAINTIFF,
        NodeType.DEFENDANT,
        NodeType.WITNESS,
    ],
    "organizations": [
        NodeType.ORGANIZATION,
        NodeType.GOVERNMENT_BODY,
    ],
    "metadata": [
        NodeType.LOCATION,
        NodeType.DATE,
        NodeType.LEGAL_CONCEPT,
    ],
}


# Required properties for each node type
REQUIRED_PROPERTIES = {
    NodeType.LAW: ["id", "name"],
    NodeType.ARTICLE: ["id", "number", "content"],
    NodeType.VERDICT: ["id", "case_number", "date"],
    NodeType.COURT: ["id", "name"],
    NodeType.CASE: ["id", "case_number"],
    NodeType.JUDGE: ["id", "name"],
    NodeType.LAWYER: ["id", "name"],
    NodeType.PERSON: ["id", "name"],
    NodeType.ORGANIZATION: ["id", "name"],
    NodeType.LOCATION: ["id", "name"],
}


# Optional properties for each node type
OPTIONAL_PROPERTIES = {
    NodeType.LAW: ["description", "approval_date", "category"],
    NodeType.ARTICLE: ["law_id", "chapter", "section"],
    NodeType.VERDICT: [
        "decision",
        "verdict_type",  # بدوی, تجدیدنظر, فرجام
        "status",  # قطعی, غیرقطعی
        "content",
        "summary",
    ],
    NodeType.COURT: ["type", "level", "location"],
    NodeType.CASE: [
        "subject",
        "status",  # در جریان, خاتمه یافته
        "filing_date",
    ],
    NodeType.JUDGE: ["title", "specialization"],
    NodeType.LAWYER: ["bar_number", "specialization"],
    NodeType.PERSON: ["role", "father_name", "national_id"],
}


def get_all_node_types():
    """Get list of all node types"""
    return [nt.value for nt in NodeType]


def get_node_types_by_group(group: str):
    """Get node types by group"""
    return [nt.value for nt in NODE_TYPE_GROUPS.get(group, [])]


def get_required_properties(node_type: str):
    """Get required properties for a node type"""
    nt = NodeType(node_type)
    return REQUIRED_PROPERTIES.get(nt, ["id"])


def get_optional_properties(node_type: str):
    """Get optional properties for a node type"""
    nt = NodeType(node_type)
    return OPTIONAL_PROPERTIES.get(nt, [])
