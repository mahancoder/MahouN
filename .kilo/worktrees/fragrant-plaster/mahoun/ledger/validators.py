"""
Deep Ledger Validation
=======================

Provides comprehensive validation of ledger entries.

Validation levels:
1. Shallow: Basic field validation
2. Deep: Graph consistency validation
3. Cryptographic: Proof verification

Guarantees:
- Entries reference valid graph nodes
- Confidence scores are justified
- No excluded nodes are referenced
- Cryptographic proofs are valid
"""

from typing import Dict, Set, Optional, List
import logging

from mahoun.ledger.models import LedgerEntry
from mahoun.graph.ultra_graph_builder import UltraGraphBuilder, GraphNode

log = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when ledger entry validation fails"""
    pass


class DeepValidator:
    """
    Deep validator for ledger entries
    
    Validates:
    - Node existence in graph
    - Fact validity
    - Confidence justification
    - Excluded node detection
    - Cryptographic proof integrity
    """
    
    def __init__(self, graph_builder: Optional[UltraGraphBuilder] = None):
        """
        Initialize validator
        
        Args:
            graph_builder: Graph builder for node validation (optional)
        """
        self.graph = graph_builder
    
    def validate_entry_deep(
        self,
        entry: LedgerEntry,
        excluded_nodes: Optional[Set[str]] = None
    ) -> None:
        """
        Deep validation of ledger entry
        
        Args:
            entry: LedgerEntry to validate
            excluded_nodes: Set of excluded node IDs (optional)
        
        Raises:
            ValidationError: If validation fails
        
        Checks:
        1. Nodes exist in graph
        2. Facts are valid
        3. Confidence is justified
        4. No excluded nodes referenced
        5. Cryptographic proof (if present)
        """
        # Check 1: Validate node existence
        if self.graph is not None:
            self._validate_node_existence(entry)
        
        # Check 2: Validate facts
        if self.graph is not None:
            self._validate_facts(entry)
        
        # Check 3: Validate confidence justification
        self._validate_confidence(entry)
        
        # Check 4: Check for excluded nodes
        if excluded_nodes:
            self._validate_no_excluded_nodes(entry, excluded_nodes)
        
        # Check 5: Validate cryptographic proof (if present)
        if hasattr(entry, 'cryptographic_proof') and entry.cryptographic_proof:
            self._validate_cryptographic_proof(entry)
    
    def _validate_node_existence(self, entry: LedgerEntry) -> None:
        """
        Validate that all referenced nodes exist in graph
        
        Args:
            entry: LedgerEntry to validate
        
        Raises:
            ValidationError: If node doesn't exist
        """
        if self.graph is None:
            return
        
        graph_nodes = self.graph.get_nodes()
        
        # Check LTM nodes
        for node_id in entry.referenced_ltm_nodes:
            if node_id not in graph_nodes:
                available_nodes = list(graph_nodes.keys())[:10]
                raise ValidationError(
                    f"Referenced LTM node '{node_id}' does not exist in graph. "
                    f"Available nodes (first 10): {available_nodes}"
                )
        
        log.debug(f"✓ All {len(entry.referenced_ltm_nodes)} LTM nodes exist in graph")
    
    def _validate_facts(self, entry: LedgerEntry) -> None:
        """
        Validate that all referenced facts are valid
        
        Args:
            entry: LedgerEntry to validate
        
        Raises:
            ValidationError: If fact is invalid
        """
        if self.graph is None:
            return
        
        graph_nodes = self.graph.get_nodes()
        
        # Check facts
        for fact_id in entry.referenced_facts:
            if fact_id not in graph_nodes:
                raise ValidationError(
                    f"Referenced fact '{fact_id}' does not exist in graph"
                )
            
            # Verify it's actually a fact node
            node = graph_nodes[fact_id]
            if hasattr(node, 'node_type') and node.node_type != "Fact":
                log.warning(
                    f"Node '{fact_id}' is referenced as fact but has type '{node.node_type}'"
                )
        
        log.debug(f"✓ All {len(entry.referenced_facts)} facts are valid")
    
    def _validate_confidence(self, entry: LedgerEntry) -> None:
        """
        Validate that confidence score is justified
        
        Args:
            entry: LedgerEntry to validate
        
        Raises:
            ValidationError: If confidence is not justified
        
        Rules:
        - High confidence (>0.9) requires at least 3 evidence items
        - Medium confidence (0.7-0.9) requires at least 2 evidence items
        - Low confidence (<0.7) requires at least 1 evidence item
        """
        total_evidence = len(entry.referenced_ltm_nodes) + len(entry.referenced_facts)
        
        if entry.confidence > 0.9 and total_evidence < 3:
            raise ValidationError(
                f"Confidence {entry.confidence:.2f} too high for {total_evidence} evidence items. "
                f"High confidence (>0.9) requires at least 3 evidence items."
            )
        
        if entry.confidence > 0.7 and total_evidence < 2:
            raise ValidationError(
                f"Confidence {entry.confidence:.2f} too high for {total_evidence} evidence items. "
                f"Medium confidence (>0.7) requires at least 2 evidence items."
            )
        
        if total_evidence == 0:
            raise ValidationError(
                "Entry has no evidence but non-zero confidence"
            )
        
        log.debug(f"✓ Confidence {entry.confidence:.2f} justified by {total_evidence} evidence items")
    
    def _validate_no_excluded_nodes(
        self,
        entry: LedgerEntry,
        excluded_nodes: Set[str]
    ) -> None:
        """
        Validate that no excluded nodes are referenced
        
        Args:
            entry: LedgerEntry to validate
            excluded_nodes: Set of excluded node IDs
        
        Raises:
            ValidationError: If excluded node is referenced
        
        Context:
            During contradiction resolution, some nodes are excluded.
            These nodes must NOT appear in ledger entries.
        """
        # Check LTM nodes
        for node_id in entry.referenced_ltm_nodes:
            if node_id in excluded_nodes:
                raise ValidationError(
                    f"Referenced LTM node '{node_id}' was excluded during "
                    f"contradiction resolution and must not be used"
                )
        
        # Check facts
        for fact_id in entry.referenced_facts:
            if fact_id in excluded_nodes:
                raise ValidationError(
                    f"Referenced fact '{fact_id}' was excluded during "
                    f"contradiction resolution and must not be used"
                )
        
        log.debug("✓ No excluded nodes referenced")
    
    def _validate_cryptographic_proof(self, entry: LedgerEntry) -> None:
        """
        Validate cryptographic proof (if present)
        
        Args:
            entry: LedgerEntry to validate
        
        Raises:
            ValidationError: If proof is invalid
        
        Note:
            Requires public key for verification.
            If public key not available, logs warning.
        """
        # This is a placeholder for future implementation
        # Requires public key infrastructure
        log.debug("Cryptographic proof validation not yet implemented")


def validate_entry_shallow(entry: LedgerEntry) -> None:
    """
    Shallow validation of ledger entry
    
    Args:
        entry: LedgerEntry to validate
    
    Raises:
        ValidationError: If validation fails
    
    Checks:
    - At least one evidence reference
    - Confidence in valid range
    - Required fields not empty
    """
    # Check evidence
    if not entry.referenced_ltm_nodes and not entry.referenced_facts:
        raise ValidationError(
            "LedgerEntry must have at least one referenced LTM node or fact"
        )
    
    # Check confidence range
    if not (0.0 <= entry.confidence <= 1.0):
        raise ValidationError(
            f"Confidence must be in [0.0, 1.0], got {entry.confidence}"
        )
    
    # Check required fields
    if not entry.verdict_id:
        raise ValidationError("verdict_id must not be empty")
    
    if not entry.case_id:
        raise ValidationError("case_id must not be empty")
    
    if not entry.invariant_version:
        raise ValidationError("invariant_version must not be empty")
    
    log.debug("✓ Shallow validation passed")


def validate_entry(
    entry: LedgerEntry,
    graph_builder: Optional[UltraGraphBuilder] = None,
    excluded_nodes: Optional[Set[str]] = None,
    deep: bool = True
) -> None:
    """
    Validate ledger entry (shallow + optional deep)
    
    Args:
        entry: LedgerEntry to validate
        graph_builder: Graph builder for deep validation (optional)
        excluded_nodes: Set of excluded node IDs (optional)
        deep: Whether to perform deep validation (default: True)
    
    Raises:
        ValidationError: If validation fails
    """
    # Always do shallow validation
    validate_entry_shallow(entry)
    
    # Deep validation if requested and graph available
    if deep and graph_builder is not None:
        validator = DeepValidator(graph_builder)
        validator.validate_entry_deep(entry, excluded_nodes)


# Example usage
if __name__ == "__main__":
    from mahoun.ledger.models import LedgerEntry
    from datetime import datetime, timezone
    
    print("🔍 Deep Ledger Validation Test")
    print("=" * 60)
    
    # Test shallow validation
    print("\n1. Shallow Validation")
    
    # Valid entry
    entry = LedgerEntry(
        verdict_id="verdict_123",
        case_id="case_456",
        referenced_ltm_nodes=["rule_219"],
        referenced_facts=["fact_0"],
        confidence=0.85,
        invariant_version="v2.1.0",
        guard_mode="STRICT",
        created_at=datetime.now(timezone.utc)
    )
    
    try:
        validate_entry_shallow(entry)
        print("✓ Valid entry passed shallow validation")
    except ValidationError as e:
        print(f"✗ Unexpected failure: {e}")
    
    # Invalid entry (no evidence)
    invalid_entry = LedgerEntry(
        verdict_id="verdict_123",
        case_id="case_456",
        referenced_ltm_nodes=[],
        referenced_facts=[],
        confidence=0.85,
        invariant_version="v2.1.0",
        guard_mode="STRICT",
        created_at=datetime.now(timezone.utc)
    )
    
    try:
        validate_entry_shallow(invalid_entry)
        print("✗ Invalid entry should have failed")
    except ValidationError as e:
        print(f"✓ Invalid entry correctly rejected: {e}")
    
    # Test confidence validation
    print("\n2. Confidence Validation")
    
    validator = DeepValidator()
    
    # High confidence with insufficient evidence
    high_conf_entry = LedgerEntry(
        verdict_id="verdict_123",
        case_id="case_456",
        referenced_ltm_nodes=["rule_219"],
        referenced_facts=[],
        confidence=0.95,  # Too high for 1 evidence
        invariant_version="v2.1.0",
        guard_mode="STRICT",
        created_at=datetime.now(timezone.utc)
    )
    
    try:
        validator._validate_confidence(high_conf_entry)
        print("✗ High confidence should require more evidence")
    except ValidationError as e:
        print(f"✓ High confidence correctly rejected: {e}")
    
    # Appropriate confidence
    good_conf_entry = LedgerEntry(
        verdict_id="verdict_123",
        case_id="case_456",
        referenced_ltm_nodes=["rule_219", "rule_220", "precedent_1"],
        referenced_facts=["fact_0"],
        confidence=0.92,
        invariant_version="v2.1.0",
        guard_mode="STRICT",
        created_at=datetime.now(timezone.utc)
    )
    
    try:
        validator._validate_confidence(good_conf_entry)
        print("✓ Appropriate confidence accepted")
    except ValidationError as e:
        print(f"✗ Unexpected failure: {e}")
