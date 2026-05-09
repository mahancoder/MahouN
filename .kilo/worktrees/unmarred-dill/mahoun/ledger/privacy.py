# mahoun/ledger/privacy.py
"""
Privacy Filtering for Evidence Ledger
=====================================

Ensures sensitive fact values are never stored in the Evidence Ledger.
Only opaque identifiers are allowed for auditability without data leakage.
"""

from typing import Any, List

# Sensitive fact types that must never have their values stored
SENSITIVE_FACT_TYPES = {
    "PERSONAL_ID",
    "MEDICAL",
    "BIOMETRIC",
    "ADDRESS",
}


def filter_facts_for_ledger(facts: List[Any]) -> List[str]:
    """
    Filter facts for safe storage in Evidence Ledger.
    
    Args:
        facts: List of fact objects or dicts with 'id' and 'type' fields
        
    Returns:
        List of fact IDs only (no values)
        
    Raises:
        ValueError: If any fact lacks an ID
    """
    filtered_ids: List[Any] = []
    for fact in facts:
        # Extract ID - support both object and dict formats
        if hasattr(fact, 'id'):
            fact_id = fact.id
        elif isinstance(fact, dict) and 'id' in fact:
            fact_id = fact['id']
        else:
            raise ValueError(f"Fact must have an 'id' field: {fact}")
        
        # Extract type for validation (but don't use it for filtering)
        if isinstance(fact, dict):
            fact_type = fact.get('type', None)
        elif hasattr(fact, 'type'):
            fact_type = fact.type
        else:
            fact_type: Optional[Any] = None
        # Validate that sensitive types don't leak values
        # Note: We don't branch on sensitivity - we always return only IDs
        if fact_type in SENSITIVE_FACT_TYPES:
            # Additional validation: ensure no value field is present
            if hasattr(fact, 'value') or (isinstance(fact, dict) and 'value' in fact):
                raise ValueError(f"Sensitive fact {fact_id} must not contain value field")
        
        # Always return only the ID
        filtered_ids.append(fact_id)
    
    return filtered_ids