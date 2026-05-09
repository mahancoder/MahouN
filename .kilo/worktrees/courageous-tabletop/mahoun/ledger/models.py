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
