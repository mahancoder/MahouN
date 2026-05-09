# mahoun/ledger/guards.py
"""
Ledger Entry Validation Guards
===============================
Enforces ledger entry integrity with deep validation.

Invariants enforced:
- EL-I1 (Evidence Required): At least one evidence reference exists
- EL-I2 (Graph Existence): Referenced nodes must exist in graph
- EL-I4 (Immutability): Guards checked before writing immutable entries
"""

from typing import TYPE_CHECKING, Optional

from mahoun.ledger.models import LedgerEntry

if TYPE_CHECKING:
    from mahoun.graph.ultra_graph_builder import UltraGraphBuilder


def validate_entry(
    entry: LedgerEntry,
    graph_builder: Optional['UltraGraphBuilder'] = None
) -> None:
    """
    Validate ledger entry with optional deep graph validation.
    
    Args:
        entry: LedgerEntry to validate
        graph_builder: Optional graph builder for deep validation
        
    Raises:
        ValueError: If validation fails
    """
    # Basic validation (always enforced)
    if not entry.referenced_ltm_nodes and not entry.referenced_facts:
        raise ValueError("LedgerEntry must have at least one referenced LTM node or fact")
    if not (0.0 <= entry.confidence <= 1.0):
        raise ValueError("Confidence must be between 0.0 and 1.0")
    if not entry.verdict_id or not entry.case_id:
        raise ValueError("Verdict ID and Case ID must not be empty")
    
    # Deep validation (if graph_builder provided)
    if graph_builder is not None:
        from mahoun.ledger.validators import DeepValidator
        validator = DeepValidator(graph_builder)
        validator.validate_entry_deep(entry)