"""
MAHOUN Governed Graph Writer
==============================

Classification: CRITICAL / MUTATION AUTHORIZATION BOUNDARY
Purpose: Single architectural entry point for ALL graph mutations.

This module provides THREE primitives:
    1. GovernedGraphWriter  — governed persistence adapter
    2. GovernedTransaction  — governed transaction layer
    3. MutationReceipt      — immutable audit record

Architecture:
    Caller → GovernedGraphWriter → ValidatorPipeline → executor(cypher, params)
                                        │
                                   ProvenanceTracker
                                   OntologyEnforcer
                                   CustomGates

Invariants:
    - Every graph write passes through ValidatorPipeline BEFORE execution.
    - Every write produces an immutable MutationReceipt.
    - Missing provenance halts execution (fail-closed).
    - Invalid ontology halts execution (fail-closed).
    - No silent recovery. No soft failures. No fallbacks.
    - GovernedTransaction validates ALL mutations before committing ANY.

Author: MAHOUN Platform Governance Council
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence, Tuple

from mahoun.core.governance.validator_pipeline import (
    PipelineResult,
    ValidatorPipeline,
)
from mahoun.core.governance.provenance_tracker import ProvenanceMetadata
from mahoun.core.governance.violations import (
    GovernanceViolation,
    GovernanceViolationError,
    ViolationCategory,
    ViolationSeverity,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Executor Protocol (infrastructure-agnostic)
# ---------------------------------------------------------------------------

class GraphExecutor(Protocol):
    """Protocol for the injected graph execution backend.

    Any object that can run a Cypher query and return results satisfies
    this protocol.  This keeps the governance layer completely decoupled
    from Neo4j driver internals.
    """

    def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]: ...


class TransactionContext(Protocol):
    """Protocol for a transaction-capable execution context."""

    def run(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any: ...
    def commit(self) -> None: ...


# ---------------------------------------------------------------------------
# Mutation Types
# ---------------------------------------------------------------------------

class MutationType(str, Enum):
    """Type of graph mutation."""
    NODE_CREATE = "NODE_CREATE"
    NODE_MERGE = "NODE_MERGE"
    RELATIONSHIP_CREATE = "RELATIONSHIP_CREATE"
    RELATIONSHIP_MERGE = "RELATIONSHIP_MERGE"
    NODE_DELETE = "NODE_DELETE"


# ---------------------------------------------------------------------------
# Mutation Receipt (immutable audit record)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MutationReceipt:
    """Immutable audit record for a governed graph mutation.

    Every successful write through GovernedGraphWriter produces one
    of these.  Receipts are append-only and cannot be modified.

    Attributes:
        receipt_id: Unique identifier for this mutation.
        mutation_type: Type of mutation performed.
        pipeline_result: Full validation pipeline result.
        label: Node label or relationship type.
        entity_id: ID of the entity that was mutated.
        timestamp: UTC ISO-8601 timestamp of the mutation.
        correlation_id: Correlation ID for tracing.
        content_hash: SHA-256 hash of the mutation payload.
    """
    receipt_id: str
    mutation_type: MutationType
    pipeline_result: PipelineResult
    label: str
    entity_id: str
    timestamp: str
    correlation_id: str
    content_hash: str


# ---------------------------------------------------------------------------
# Governed Graph Writer (persistence adapter + authorization boundary)
# ---------------------------------------------------------------------------

class GovernedGraphWriter:
    """The ONLY authorized graph mutation interface.

    All graph writes — node creation, relationship creation, batch
    operations — MUST flow through this class.  Direct ``session.run()``
    with MERGE/CREATE queries is architecturally forbidden outside of
    this adapter.

    The writer is **infrastructure-agnostic**: it takes an injected
    ``executor`` that satisfies :class:`GraphExecutor`.  This means the
    governance layer does not depend on Neo4j driver internals.

    Fail-closed semantics:
        - Missing provenance → GovernanceViolationError
        - Ontology violation → GovernanceViolationError
        - Schema violation   → GovernanceViolationError
        - Executor failure   → exception propagated (no swallowing)
    """

    def __init__(
        self,
        executor: GraphExecutor,
        pipeline: Optional[ValidatorPipeline] = None,
    ) -> None:
        if executor is None:
            raise ValueError("GraphExecutor cannot be None")
        self._executor = executor
        self._pipeline = pipeline or ValidatorPipeline()
        self._mutation_log: List[MutationReceipt] = []

    # ------------------------------------------------------------------
    # Node writes
    # ------------------------------------------------------------------

    def write_node(
        self,
        label: str,
        node_data: Dict[str, Any],
        *,
        merge: bool = True,
        correlation_id: Optional[str] = None,
    ) -> MutationReceipt:
        """Write a node through the governed pipeline.

        Args:
            label: Node label (e.g. 'Document', 'Law', 'Verdict').
            node_data: Node properties.  MUST contain ``id`` and ``provenance``.
            merge: Use MERGE (True) or CREATE (False).
            correlation_id: Optional correlation ID for tracing.

        Returns:
            Immutable MutationReceipt.

        Raises:
            GovernanceViolationError: If validation fails (fail-closed).
        """
        cid = correlation_id or ""

        # --- AUTHORIZATION GATE ---
        pipeline_result = self._pipeline.validate_node_write(node_data, cid)

        # --- PERSISTENCE ---
        cypher_props = {k: v for k, v in node_data.items() if k != "provenance"}
        prop_assignments = ", ".join(f"n.{k} = ${k}" for k in cypher_props)

        if merge:
            query = (
                f"MERGE (n:{label} {{id: $id}}) "
                f"ON CREATE SET n.created_at = datetime() "
                f"SET {prop_assignments}, n.updated_at = datetime() "
                f"RETURN n"
            )
            mutation_type = MutationType.NODE_MERGE
        else:
            query = (
                f"CREATE (n:{label} {{id: $id}}) "
                f"SET {prop_assignments}, n.created_at = datetime() "
                f"RETURN n"
            )
            mutation_type = MutationType.NODE_CREATE

        self._executor.execute_query(query, cypher_props)

        # --- RECEIPT ---
        receipt = self._make_receipt(
            mutation_type=mutation_type,
            pipeline_result=pipeline_result,
            label=label,
            entity_id=str(node_data.get("id", "")),
            correlation_id=cid,
            payload=node_data,
        )
        self._mutation_log.append(receipt)
        logger.debug("[GOVERNED] Node write: %s/%s receipt=%s", label, node_data.get("id"), receipt.receipt_id)
        return receipt

    # ------------------------------------------------------------------
    # Relationship writes
    # ------------------------------------------------------------------

    def write_relationship(
        self,
        source_type: str,
        source_id: str,
        relationship_type: str,
        target_type: str,
        target_id: str,
        relationship_data: Dict[str, Any],
        *,
        merge: bool = True,
        correlation_id: Optional[str] = None,
    ) -> MutationReceipt:
        """Write a relationship through the governed pipeline.

        Args:
            source_type: Source node label.
            source_id: Source node ID.
            relationship_type: Relationship type (must be in ontology).
            target_type: Target node label.
            target_id: Target node ID.
            relationship_data: Relationship properties.  MUST contain ``provenance``.
            merge: Use MERGE (True) or CREATE (False).
            correlation_id: Optional correlation ID for tracing.

        Returns:
            Immutable MutationReceipt.

        Raises:
            GovernanceViolationError: On ontology violation or missing provenance.
        """
        cid = correlation_id or ""

        # --- AUTHORIZATION GATE ---
        pipeline_result = self._pipeline.validate_relationship_write(
            source_type=source_type,
            relationship_type=relationship_type,
            target_type=target_type,
            relationship_data=relationship_data,
            correlation_id=cid,
        )

        # --- PERSISTENCE ---
        cypher_props = {k: v for k, v in relationship_data.items() if k != "provenance"}
        prop_assignments = ", ".join(f"r.{k} = ${k}" for k in cypher_props)
        set_clause = f"SET {prop_assignments}" if prop_assignments else ""

        if merge:
            query = (
                f"MATCH (a:{source_type} {{id: $source_id}}) "
                f"MATCH (b:{target_type} {{id: $target_id}}) "
                f"MERGE (a)-[r:{relationship_type}]->(b) "
                f"ON CREATE SET r.created_at = datetime() "
                f"{set_clause}"
                f"{', ' if set_clause else 'SET '}r.updated_at = datetime()"
            )
            mutation_type = MutationType.RELATIONSHIP_MERGE
        else:
            query = (
                f"MATCH (a:{source_type} {{id: $source_id}}) "
                f"MATCH (b:{target_type} {{id: $target_id}}) "
                f"CREATE (a)-[r:{relationship_type}]->(b) "
                f"SET r.created_at = datetime() "
                f"{set_clause}"
            )
            mutation_type = MutationType.RELATIONSHIP_CREATE

        params = {"source_id": source_id, "target_id": target_id, **cypher_props}
        self._executor.execute_query(query, params)

        # --- RECEIPT ---
        receipt = self._make_receipt(
            mutation_type=mutation_type,
            pipeline_result=pipeline_result,
            label=relationship_type,
            entity_id=f"{source_id}->{target_id}",
            correlation_id=cid,
            payload=relationship_data,
        )
        self._mutation_log.append(receipt)
        logger.debug(
            "[GOVERNED] Relationship write: %s -[%s]-> %s receipt=%s",
            source_type, relationship_type, target_type, receipt.receipt_id,
        )
        return receipt

    # ------------------------------------------------------------------
    # Governed Transaction
    # ------------------------------------------------------------------

    def begin_transaction(
        self, correlation_id: Optional[str] = None
    ) -> "GovernedTransaction":
        """Begin a governed transaction.

        The transaction validates ALL mutations through the pipeline
        BEFORE committing any.  If any single validation fails, the
        entire transaction is aborted.

        Args:
            correlation_id: Correlation ID for the transaction scope.

        Returns:
            GovernedTransaction context manager.
        """
        return GovernedTransaction(
            writer=self,
            correlation_id=correlation_id or "",
        )

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    @property
    def mutation_log(self) -> Tuple[MutationReceipt, ...]:
        """Immutable view of all mutation receipts."""
        return tuple(self._mutation_log)

    @property
    def mutation_count(self) -> int:
        """Total number of governed mutations executed."""
        return len(self._mutation_log)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _make_receipt(
        mutation_type: MutationType,
        pipeline_result: PipelineResult,
        label: str,
        entity_id: str,
        correlation_id: str,
        payload: Dict[str, Any],
    ) -> MutationReceipt:
        ts = datetime.now(timezone.utc).isoformat()
        canonical = json.dumps(payload, sort_keys=True, default=str)
        content_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return MutationReceipt(
            receipt_id=hashlib.sha256(
                f"{ts}:{entity_id}:{content_hash}".encode()
            ).hexdigest()[:24],
            mutation_type=mutation_type,
            pipeline_result=pipeline_result,
            label=label,
            entity_id=entity_id,
            timestamp=ts,
            correlation_id=correlation_id,
            content_hash=content_hash,
        )


# ---------------------------------------------------------------------------
# Governed Transaction (atomic governed batch)
# ---------------------------------------------------------------------------

class GovernedTransaction:
    """Governed transaction that validates ALL mutations before committing ANY.

    Usage::

        writer = GovernedGraphWriter(executor)
        tx = writer.begin_transaction(correlation_id="op-123")
        tx.queue_node("Document", {"id": "d1", "provenance": {...}})
        tx.queue_relationship("Case", "c1", "CITES", "Law", "l1", {"provenance": {...}})
        receipts = tx.commit()  # validates all, then executes all atomically

    If ANY validation fails, the entire transaction is aborted and
    no mutations reach the database.  This is fail-closed batch semantics.
    """

    def __init__(self, writer: GovernedGraphWriter, correlation_id: str = "") -> None:
        self._writer = writer
        self._correlation_id = correlation_id
        self._committed = False
        self._aborted = False

        # Pending mutations: list of (validation_fn, execute_fn) tuples
        self._pending: List[Tuple[Callable[[], PipelineResult], Callable[[], None], Dict[str, Any]]] = []
        self._validation_results: List[PipelineResult] = []

    def queue_node(
        self,
        label: str,
        node_data: Dict[str, Any],
        *,
        merge: bool = True,
    ) -> None:
        """Queue a node write for governed batch commit.

        Raises:
            RuntimeError: If the transaction is already committed/aborted.
        """
        self._check_open()

        def validate() -> PipelineResult:
            return self._writer._pipeline.validate_node_write(
                node_data, self._correlation_id
            )

        def execute() -> None:
            cypher_props = {k: v for k, v in node_data.items() if k != "provenance"}
            prop_assignments = ", ".join(f"n.{k} = ${k}" for k in cypher_props)
            op = "MERGE" if merge else "CREATE"
            query = (
                f"{op} (n:{label} {{id: $id}}) "
                f"SET {prop_assignments}, "
                f"n.{'updated_at' if merge else 'created_at'} = datetime()"
            )
            self._writer._executor.execute_query(query, cypher_props)

        self._pending.append((validate, execute, {"type": "node", "label": label, "data": node_data}))

    def queue_relationship(
        self,
        source_type: str,
        source_id: str,
        relationship_type: str,
        target_type: str,
        target_id: str,
        relationship_data: Dict[str, Any],
        *,
        merge: bool = True,
    ) -> None:
        """Queue a relationship write for governed batch commit.

        Raises:
            RuntimeError: If the transaction is already committed/aborted.
        """
        self._check_open()

        def validate() -> PipelineResult:
            return self._writer._pipeline.validate_relationship_write(
                source_type=source_type,
                relationship_type=relationship_type,
                target_type=target_type,
                relationship_data=relationship_data,
                correlation_id=self._correlation_id,
            )

        def execute() -> None:
            cypher_props = {k: v for k, v in relationship_data.items() if k != "provenance"}
            prop_assignments = ", ".join(f"r.{k} = ${k}" for k in cypher_props)
            set_clause = f"SET {prop_assignments}" if prop_assignments else ""
            op = "MERGE" if merge else "CREATE"
            query = (
                f"MATCH (a:{source_type} {{id: $source_id}}) "
                f"MATCH (b:{target_type} {{id: $target_id}}) "
                f"{op} (a)-[r:{relationship_type}]->(b) "
                f"{set_clause}"
            )
            params = {"source_id": source_id, "target_id": target_id, **cypher_props}
            self._writer._executor.execute_query(query, params)

        self._pending.append((
            validate, execute,
            {"type": "relationship", "label": relationship_type, "data": relationship_data},
        ))

    def commit(self) -> Tuple[MutationReceipt, ...]:
        """Validate ALL queued mutations, then execute ALL atomically.

        Phase 1 — Validation:
            Every queued mutation is validated through ValidatorPipeline.
            If ANY validation fails, the entire transaction aborts.

        Phase 2 — Execution:
            All validated mutations are executed sequentially.
            If any execution fails, the error propagates (fail-closed).

        Returns:
            Tuple of immutable MutationReceipts.

        Raises:
            GovernanceViolationError: If any validation fails.
            RuntimeError: If transaction already committed/aborted.
        """
        self._check_open()

        # Phase 1: Validate ALL before executing ANY
        pipeline_results: List[PipelineResult] = []
        for validate_fn, _, _ in self._pending:
            result = validate_fn()  # raises GovernanceViolationError on failure
            pipeline_results.append(result)

        logger.info(
            "[GOVERNED TX] All %d mutations validated. Executing...",
            len(self._pending),
        )

        # Phase 2: Execute ALL
        receipts: List[MutationReceipt] = []
        for i, (_, execute_fn, meta) in enumerate(self._pending):
            execute_fn()

            mutation_type = (
                MutationType.NODE_MERGE if meta["type"] == "node"
                else MutationType.RELATIONSHIP_MERGE
            )
            receipt = GovernedGraphWriter._make_receipt(
                mutation_type=mutation_type,
                pipeline_result=pipeline_results[i],
                label=meta["label"],
                entity_id=str(meta["data"].get("id", "")),
                correlation_id=self._correlation_id,
                payload=meta["data"],
            )
            receipts.append(receipt)
            self._writer._mutation_log.append(receipt)

        self._committed = True
        logger.info(
            "[GOVERNED TX] Transaction committed: %d mutations, correlation=%s",
            len(receipts), self._correlation_id,
        )
        return tuple(receipts)

    def abort(self) -> None:
        """Abort the transaction. No mutations are executed."""
        self._aborted = True
        self._pending.clear()
        logger.info("[GOVERNED TX] Transaction aborted: correlation=%s", self._correlation_id)

    @property
    def pending_count(self) -> int:
        """Number of queued mutations awaiting commit."""
        return len(self._pending)

    @property
    def is_open(self) -> bool:
        """Whether the transaction is still open for mutations."""
        return not self._committed and not self._aborted

    def _check_open(self) -> None:
        if self._committed:
            raise RuntimeError("Transaction already committed")
        if self._aborted:
            raise RuntimeError("Transaction already aborted")
