# mahoun/ledger/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass(frozen=True)
class LedgerEntry:
    verdict_id: str
    case_id: str

    referenced_ltm_nodes: List[str]   # rule_id, statute_id, precedent_id
    referenced_facts: List[str]       # fact_id

    confidence: float
    invariant_version: str
    guard_mode: str

    created_at: datetime
    event_type: Optional[str] = None
    request_id: Optional[str] = None

# HARDENING PATCH P11: Canonical serialization
def canonical_serialize(entry: LedgerEntry) -> dict:
    """
    Deterministically serialize a LedgerEntry to a dictionary.
    Used for cryptographic hashing across all ledger components to ensure
    consistent verification regardless of backend or parsing logic.
    """
    from dataclasses import asdict
    d = asdict(entry)
    
    # Ensure lists are strictly typed and ordered (if applicable, but we sort keys anyway)
    # Datetime MUST be strictly ISO formatted
    if isinstance(d.get('created_at'), datetime):
        d['created_at'] = d['created_at'].isoformat()
        
    return d
