"""
Tests for GovernedGraphWriter — the mutation authorization boundary.

Proves:
    1. No write without provenance
    2. No relationship without ontology compliance
    3. Every write produces an immutable receipt
    4. GovernedTransaction validates ALL before committing ANY
    5. Aborted transactions produce zero mutations
    6. Fail-closed semantics on every violation
"""
import pytest
from unittest.mock import MagicMock
from mahoun.core.governance.governed_writer import (
    GovernedGraphWriter,
    GovernedTransaction,
    MutationReceipt,
    MutationType,
)
from mahoun.core.governance.violations import GovernanceViolationError
from mahoun.core.governance.provenance_tracker import ProvenanceMetadata


def _make_provenance() -> dict:
    return ProvenanceMetadata.create(
        source="test", correlation_id="corr-1", author="test-agent"
    ).to_dict()


def _mock_executor():
    executor = MagicMock()
    executor.execute_query = MagicMock(return_value=[])
    return executor


# ======================================================================
# GovernedGraphWriter — Node Writes
# ======================================================================

class TestGovernedNodeWrites:
    def test_valid_node_write_succeeds(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        receipt = writer.write_node(
            "Document",
            {"id": "doc-1", "title": "Test", "provenance": _make_provenance()},
        )
        assert isinstance(receipt, MutationReceipt)
        assert receipt.mutation_type == MutationType.NODE_MERGE
        assert receipt.label == "Document"
        assert receipt.entity_id == "doc-1"
        assert executor.execute_query.called

    def test_node_write_without_provenance_fails(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        with pytest.raises(GovernanceViolationError, match="provenance"):
            writer.write_node("Document", {"id": "doc-1", "title": "Test"})
        assert not executor.execute_query.called  # No DB call made

    def test_node_write_without_id_fails(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        with pytest.raises(GovernanceViolationError, match="required fields"):
            writer.write_node("Document", {"title": "Test", "provenance": _make_provenance()})
        assert not executor.execute_query.called

    def test_node_create_vs_merge(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        r1 = writer.write_node(
            "Law", {"id": "l1", "provenance": _make_provenance()}, merge=True
        )
        r2 = writer.write_node(
            "Law", {"id": "l2", "provenance": _make_provenance()}, merge=False
        )
        assert r1.mutation_type == MutationType.NODE_MERGE
        assert r2.mutation_type == MutationType.NODE_CREATE

    def test_receipt_is_frozen(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        receipt = writer.write_node(
            "Case", {"id": "c1", "provenance": _make_provenance()}
        )
        with pytest.raises(AttributeError):
            receipt.label = "tampered"

    def test_mutation_log_grows(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        assert writer.mutation_count == 0
        writer.write_node("Law", {"id": "l1", "provenance": _make_provenance()})
        writer.write_node("Law", {"id": "l2", "provenance": _make_provenance()})
        assert writer.mutation_count == 2
        assert len(writer.mutation_log) == 2

    def test_provenance_excluded_from_cypher(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        writer.write_node(
            "Document",
            {"id": "d1", "title": "X", "provenance": _make_provenance()},
        )
        call_args = executor.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params", {})
        assert "provenance" not in query
        assert "provenance" not in params


# ======================================================================
# GovernedGraphWriter — Relationship Writes
# ======================================================================

class TestGovernedRelationshipWrites:
    def test_valid_relationship_succeeds(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        receipt = writer.write_relationship(
            source_type="Case", source_id="c1",
            relationship_type="CITES",
            target_type="Law", target_id="l1",
            relationship_data={"provenance": _make_provenance()},
        )
        assert receipt.mutation_type == MutationType.RELATIONSHIP_MERGE
        assert receipt.label == "CITES"
        assert executor.execute_query.called

    def test_ontology_violation_fails(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        with pytest.raises(GovernanceViolationError, match="Ontology"):
            writer.write_relationship(
                source_type="Case", source_id="c1",
                relationship_type="INVENTED_REL",
                target_type="Law", target_id="l1",
                relationship_data={"provenance": _make_provenance()},
            )
        assert not executor.execute_query.called

    def test_relationship_without_provenance_fails(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        with pytest.raises(GovernanceViolationError, match="provenance"):
            writer.write_relationship(
                source_type="Case", source_id="c1",
                relationship_type="CITES",
                target_type="Law", target_id="l1",
                relationship_data={},
            )
        assert not executor.execute_query.called

    def test_new_ontology_rules_work(self):
        """Verify the new ontology rules (Verdict, Person, etc.) are enforced."""
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        prov = {"provenance": _make_provenance()}

        # Verdict -> REFERS_TO -> LawArticle (new rule)
        r1 = writer.write_relationship(
            "Verdict", "v1", "REFERS_TO", "LawArticle", "la1", prov
        )
        assert r1.mutation_type == MutationType.RELATIONSHIP_MERGE

        # Verdict -> HAS_PARTY -> Person (new rule)
        r2 = writer.write_relationship(
            "Verdict", "v1", "HAS_PARTY", "Person", "p1", prov
        )
        assert r2.label == "HAS_PARTY"

        # GraphNode -> RELATED -> GraphNode (new rule)
        r3 = writer.write_relationship(
            "GraphNode", "gn1", "RELATED", "GraphNode", "gn2", prov
        )
        assert r3.label == "RELATED"


# ======================================================================
# GovernedTransaction
# ======================================================================

class TestGovernedTransaction:
    def test_transaction_commit_validates_all_then_executes(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        prov = _make_provenance()

        tx = writer.begin_transaction(correlation_id="tx-001")
        tx.queue_node("Document", {"id": "d1", "provenance": prov})
        tx.queue_node("Law", {"id": "l1", "provenance": prov})
        tx.queue_relationship(
            "Case", "c1", "CITES", "Law", "l1", {"provenance": prov}
        )
        assert tx.pending_count == 3
        assert tx.is_open

        receipts = tx.commit()
        assert len(receipts) == 3
        assert not tx.is_open
        assert writer.mutation_count == 3
        assert executor.execute_query.call_count == 3

    def test_transaction_aborts_on_validation_failure(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)

        tx = writer.begin_transaction()
        tx.queue_node("Document", {"id": "d1", "provenance": _make_provenance()})
        tx.queue_node("Bad", {"id": "b1"})  # Missing provenance

        with pytest.raises(GovernanceViolationError):
            tx.commit()

        # ZERO mutations should have reached the database
        assert executor.execute_query.call_count == 0
        assert writer.mutation_count == 0

    def test_transaction_abort_explicit(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)

        tx = writer.begin_transaction()
        tx.queue_node("Law", {"id": "l1", "provenance": _make_provenance()})
        assert tx.pending_count == 1

        tx.abort()
        assert not tx.is_open
        assert tx.pending_count == 0

    def test_committed_transaction_rejects_more_writes(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)

        tx = writer.begin_transaction()
        tx.queue_node("Law", {"id": "l1", "provenance": _make_provenance()})
        tx.commit()

        with pytest.raises(RuntimeError, match="already committed"):
            tx.queue_node("Law", {"id": "l2", "provenance": _make_provenance()})

    def test_aborted_transaction_rejects_commit(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)

        tx = writer.begin_transaction()
        tx.abort()

        with pytest.raises(RuntimeError, match="already aborted"):
            tx.commit()

    def test_single_bad_mutation_blocks_entire_batch(self):
        """If mutation N fails validation, mutations 1..N-1 are NOT executed."""
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        prov = _make_provenance()

        tx = writer.begin_transaction()
        # 5 good mutations
        for i in range(5):
            tx.queue_node("Document", {"id": f"d{i}", "provenance": prov})
        # 1 bad mutation (ontology violation)
        tx.queue_relationship(
            "Document", "d0", "FAKE_REL", "Document", "d1", {"provenance": prov}
        )

        with pytest.raises(GovernanceViolationError):
            tx.commit()

        assert executor.execute_query.call_count == 0  # ZERO executed


# ======================================================================
# Constructor validation
# ======================================================================

class TestGovernedWriterInit:
    def test_none_executor_rejected(self):
        with pytest.raises(ValueError, match="cannot be None"):
            GovernedGraphWriter(executor=None)

    def test_mutation_log_is_immutable_view(self):
        executor = _mock_executor()
        writer = GovernedGraphWriter(executor)
        log = writer.mutation_log
        assert isinstance(log, tuple)
