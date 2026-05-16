"""
MAHOUN Mutation Authorization Boundary
========================================

Classification: KERNEL / CONSTITUTIONAL / NON-BYPASSABLE

This module implements the hard governance boundary at the Neo4j write layer.

Architecture:
    ALL Cypher → MutationAuthorizationBoundary.inspect()
                        │
                  READ query?  ──YES──→ pass through
                        │NO
                  Called from GovernedNeo4jSession? ──YES──→ pass through
                        │NO
                        ▼
                GovernanceViolationError (fail-closed, unconditionally)

Invariants:
    1. No mutation Cypher (MERGE/CREATE/DELETE/SET) may execute without
       passing through GovernedNeo4jSession.
    2. GovernedNeo4jSession validates provenance and ontology via
       ValidatorPipeline BEFORE building Cypher.
    3. Every successful mutation produces an immutable MutationReceipt.
    4. No audit mode. No soft mode. No compatibility mode.
       Governance IS execution authority.

The system fails because governance BLOCKS it —
not because developers remembered to call validation.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import contextvars
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Tuple

from mahoun.core.governance.validator_pipeline import ValidatorPipeline, PipelineResult
from mahoun.core.governance.provenance_tracker import ProvenanceMetadata
from mahoun.core.governance.violations import GovernanceViolationError, GovernanceViolation, ViolationSeverity, ViolationCategory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cypher Mutation Intent Classifier
# ---------------------------------------------------------------------------

# Keywords that signal a state-mutation operation.
# Matches at word boundaries to avoid false positives (e.g. "created_at").
_MUTATION_PATTERN = re.compile(
    r"\b(MERGE|CREATE|DELETE|DETACH\s+DELETE|SET|REMOVE|DROP)\b",
    re.IGNORECASE,
)

# Queries that are always allowed regardless of caller
# (DDL health checks and schema reads only)
_WHITELIST_PATTERN = re.compile(
    r"^\s*RETURN\s+1|"
    r"^\s*CALL\s+db\.|"
    r"^\s*MATCH\b(?!.*\b(MERGE|CREATE|DELETE|SET|REMOVE)\b)",
    re.IGNORECASE | re.DOTALL,
)


def classify_cypher(query: str) -> bool:
    """Return True if the query contains mutation intent."""
    return bool(_MUTATION_PATTERN.search(query))


# ---------------------------------------------------------------------------
# Mutation Receipt
# ---------------------------------------------------------------------------

class MutationType(str, Enum):
    NODE_CREATE = "NODE_CREATE"
    NODE_MERGE = "NODE_MERGE"
    RELATIONSHIP_CREATE = "RELATIONSHIP_CREATE"
    RELATIONSHIP_MERGE = "RELATIONSHIP_MERGE"
    NODE_DELETE = "NODE_DELETE"


@dataclass(frozen=True)
class MutationReceipt:
    """Immutable forensic record for every governed graph mutation."""
    receipt_id: str
    mutation_type: MutationType
    label: str
    entity_id: str
    timestamp: str
    correlation_id: str
    content_hash: str
    pipeline_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "mutation_type": self.mutation_type.value,
            "label": self.label,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "content_hash": self.content_hash,
            "pipeline_hash": self.pipeline_hash,
        }


def _make_receipt(
    mutation_type: MutationType,
    label: str,
    entity_id: str,
    correlation_id: str,
    payload: Dict[str, Any],
    pipeline_hash: str,
) -> MutationReceipt:
    ts = datetime.now(timezone.utc).isoformat()
    canonical = json.dumps(payload, sort_keys=True, default=str)
    content_hash = hashlib.sha256(canonical.encode()).hexdigest()
    # Structural hash ONLY. Timestamp is recorded but NOT part of the execution identity.
    receipt_id = hashlib.sha256(
        f"{entity_id}:{content_hash}".encode()
    ).hexdigest()[:24]
    return MutationReceipt(
        receipt_id=receipt_id,
        mutation_type=mutation_type,
        label=label,
        entity_id=entity_id,
        timestamp=ts,
        correlation_id=correlation_id,
        content_hash=content_hash,
        pipeline_hash=pipeline_hash,
    )


# ---------------------------------------------------------------------------
# Mutation Authorization Boundary (constitutional checkpoint)
# ---------------------------------------------------------------------------

# ContextVar: safe for asyncio, completely isolates coroutines even on the same OS thread.
_authorized_write_ctx: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "_authorized_write_ctx", default=False
)


def _is_authorized() -> bool:
    """True only when executing inside GovernedNeo4jSession."""
    return _authorized_write_ctx.get()


class MutationAuthorizationBoundary:
    """
    Constitutional checkpoint for ALL Cypher execution.

    This is NOT a helper. This is the execution authority.

    Called by Neo4jConnection._raw_execute() on EVERY query.
    Raises GovernanceViolationError unconditionally if:
        - The query contains mutation intent (MERGE/CREATE/DELETE/SET/REMOVE)
        - AND the caller is not inside an active GovernedNeo4jSession context

    Read-only queries always pass through.
    """

    @staticmethod
    def inspect(query: str) -> None:
        """
        Inspect a Cypher query for mutation intent.

        Raises:
            GovernanceViolationError: If mutation detected outside governed context.
        """
        if not classify_cypher(query):
            return  # Read-only — pass through

        if _is_authorized():
            return  # Inside GovernedNeo4jSession — pass through

        # Mutation outside governed context — CONSTITUTIONAL VIOLATION
        raise GovernanceViolationError(
            GovernanceViolation(
                category=ViolationCategory.ARCHITECTURE_BOUNDARY,
                severity=ViolationSeverity.CRITICAL,
                message=(
                    "ARCHITECTURAL VIOLATION: Mutation Cypher detected outside "
                    "GovernedNeo4jSession. Direct execution of MERGE/CREATE/"
                    "DELETE/SET is constitutionally forbidden. "
                    "All mutations must flow through GovernedNeo4jSession."
                ),
                details={"query_preview": query[:120]},
                source="MutationAuthorizationBoundary",
            )
        )


# ---------------------------------------------------------------------------
# GovernedNeo4jSession — the ONLY authorized write surface
# ---------------------------------------------------------------------------

class GovernedNeo4jSession:
    """
    The ONLY surface through which mutation Cypher may reach Neo4j.

    Callers do NOT get raw session access.
    They call typed write methods (write_node, write_relationship).
    Each call:
        1. Validates provenance via ValidatorPipeline (fail-closed)
        2. Validates ontology via ValidatorPipeline (fail-closed)
        3. Sets the thread-local authorization flag
        4. Executes the pre-built Cypher
        5. Clears the authorization flag
        6. Appends an immutable MutationReceipt to the ledger

    There is no path to execute raw mutation Cypher from outside this class.
    """

    def __init__(
        self,
        raw_executor: Any,  # callable(query, params) -> list
        pipeline: Optional[ValidatorPipeline] = None,
        correlation_id: str = "",
    ) -> None:
        self._raw_executor = raw_executor
        self._pipeline = pipeline or ValidatorPipeline()
        self._correlation_id = correlation_id
        self._ledger: List[MutationReceipt] = []

    # ------------------------------------------------------------------
    # Public write API
    # ------------------------------------------------------------------

    def write_node(
        self,
        label: str,
        node_data: Dict[str, Any],
        merge: bool = True,
    ) -> MutationReceipt:
        """
        Write a node through the governed boundary.

        Requires:
            - node_data["id"] — unique identifier
            - node_data["provenance"] — provenance metadata dict

        Raises:
            GovernanceViolationError: fail-closed on any violation.
        """
        # Phase 1: Governance validation
        result = self._pipeline.validate_node_write(
            node_data, self._correlation_id
        )

        # Phase 2: Build Cypher (provenance stays out of graph properties)
        cypher_props = {k: v for k, v in node_data.items() if k != "provenance"}
        assignments = ", ".join(f"n.{k} = ${k}" for k in cypher_props)

        if merge:
            query = (
                f"MERGE (n:{label} {{id: $id}}) "
                f"ON CREATE SET n.created_at = datetime() "
                f"SET {assignments}, n.updated_at = datetime()"
            )
            m_type = MutationType.NODE_MERGE
        else:
            query = (
                f"CREATE (n:{label}) "
                f"SET {assignments}, n.created_at = datetime()"
            )
            m_type = MutationType.NODE_CREATE

        # Phase 3: Execute under authorization
        self._execute_authorized(query, cypher_props)

        # Phase 4: Receipt
        receipt = _make_receipt(
            mutation_type=m_type,
            label=label,
            entity_id=str(node_data.get("id", "")),
            correlation_id=self._correlation_id,
            payload=node_data,
            pipeline_hash=result.pipeline_hash,
        )
        self._ledger.append(receipt)
        logger.info(
            "[MAB] Node write authorized: %s/%s receipt=%s",
            label, node_data.get("id"), receipt.receipt_id,
        )
        return receipt

    def write_relationship(
        self,
        source_type: str,
        source_id: str,
        relationship_type: str,
        target_type: str,
        target_id: str,
        rel_data: Dict[str, Any],
        merge: bool = True,
    ) -> MutationReceipt:
        """
        Write a relationship through the governed boundary.

        Requires:
            - rel_data["provenance"] — provenance metadata dict
            - relationship_type must be in OntologyEnforcer ruleset

        Raises:
            GovernanceViolationError: fail-closed on any violation.
        """
        # Phase 1: Governance validation
        result = self._pipeline.validate_relationship_write(
            source_type=source_type,
            relationship_type=relationship_type,
            target_type=target_type,
            relationship_data=rel_data,
            correlation_id=self._correlation_id,
        )

        # Phase 2: Build Cypher
        cypher_props = {k: v for k, v in rel_data.items() if k != "provenance"}
        assignments = ", ".join(f"r.{k} = ${k}" for k in cypher_props)
        set_clause = f"SET {assignments}" if assignments else ""

        if merge:
            query = (
                f"MATCH (a:{source_type} {{id: $__src}}) "
                f"MATCH (b:{target_type} {{id: $__tgt}}) "
                f"MERGE (a)-[r:{relationship_type}]->(b) "
                f"ON CREATE SET r.created_at = datetime() "
                f"{set_clause}"
            )
            m_type = MutationType.RELATIONSHIP_MERGE
        else:
            query = (
                f"MATCH (a:{source_type} {{id: $__src}}) "
                f"MATCH (b:{target_type} {{id: $__tgt}}) "
                f"CREATE (a)-[r:{relationship_type}]->(b) "
                f"SET r.created_at = datetime() {set_clause}"
            )
            m_type = MutationType.RELATIONSHIP_CREATE

        params = {"__src": source_id, "__tgt": target_id, **cypher_props}

        # Phase 3: Execute under authorization
        self._execute_authorized(query, params)

        # Phase 4: Receipt
        receipt = _make_receipt(
            mutation_type=m_type,
            label=relationship_type,
            entity_id=f"{source_id}->{target_id}",
            correlation_id=self._correlation_id,
            payload=rel_data,
            pipeline_hash=result.pipeline_hash,
        )
        self._ledger.append(receipt)
        logger.info(
            "[MAB] Relationship write authorized: %s-[%s]->%s receipt=%s",
            source_type, relationship_type, target_type, receipt.receipt_id,
        )
        return receipt

    # ------------------------------------------------------------------
    # Batch / Transaction
    # ------------------------------------------------------------------

    def begin_transaction(self) -> "GovernedWriteTransaction":
        """Begin an atomic governed transaction.

        Validates ALL queued mutations before executing ANY.
        """
        return GovernedWriteTransaction(session=self)

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    @property
    def ledger(self) -> Tuple[MutationReceipt, ...]:
        """Immutable view of all mutation receipts."""
        return tuple(self._ledger)

    @property
    def mutation_count(self) -> int:
        return len(self._ledger)

    # ------------------------------------------------------------------
    # Internal — authorization token management
    # ------------------------------------------------------------------

    def _execute_authorized(self, query: str, params: Dict[str, Any]) -> List[Any]:
        """Execute mutation Cypher under the authorization token.

        Sets contextvar flag → executes → resets flag.
        The token is managed contextually — it cannot leak across async boundaries.
        """
        token = _authorized_write_ctx.set(True)
        try:
            return self._raw_executor(query, params)
        finally:
            _authorized_write_ctx.reset(token)


# ---------------------------------------------------------------------------
# GovernedWriteTransaction — validate-all-then-execute-all
# ---------------------------------------------------------------------------

class GovernedWriteTransaction:
    """Atomic governed transaction.

    Phase 1 — Validation: every queued mutation validated via pipeline.
               If ANY fails → abort entire transaction → zero DB writes.
    Phase 2 — Execution: all validated mutations executed sequentially.

    This is the only safe way to perform multi-mutation batch writes.
    """

    def __init__(self, session: GovernedNeo4jSession) -> None:
        self._session = session
        self._committed = False
        self._aborted = False
        # Each pending item: (validate_fn, execute_fn, meta)
        self._pending: List[Tuple[Any, Any, Dict[str, Any]]] = []

    def queue_node(
        self,
        label: str,
        node_data: Dict[str, Any],
        merge: bool = True,
    ) -> None:
        self._check_open()

        def validate():
            return self._session._pipeline.validate_node_write(
                node_data, self._session._correlation_id
            )

        def execute():
            cypher_props = {k: v for k, v in node_data.items() if k != "provenance"}
            assignments = ", ".join(f"n.{k} = ${k}" for k in cypher_props)
            op = "MERGE" if merge else "CREATE"
            if merge:
                query = (
                    f"{op} (n:{label} {{id: $id}}) "
                    f"ON CREATE SET n.created_at = datetime() "
                    f"SET {assignments}, n.updated_at = datetime()"
                )
            else:
                query = f"{op} (n:{label}) SET {assignments}, n.created_at = datetime()"
            self._session._execute_authorized(query, cypher_props)

        self._pending.append((
            validate, execute,
            {"type": "node", "label": label, "data": node_data,
             "m_type": MutationType.NODE_MERGE if merge else MutationType.NODE_CREATE},
        ))

    def queue_relationship(
        self,
        source_type: str,
        source_id: str,
        relationship_type: str,
        target_type: str,
        target_id: str,
        rel_data: Dict[str, Any],
        merge: bool = True,
    ) -> None:
        self._check_open()

        def validate():
            return self._session._pipeline.validate_relationship_write(
                source_type=source_type,
                relationship_type=relationship_type,
                target_type=target_type,
                relationship_data=rel_data,
                correlation_id=self._session._correlation_id,
            )

        def execute():
            cypher_props = {k: v for k, v in rel_data.items() if k != "provenance"}
            assignments = ", ".join(f"r.{k} = ${k}" for k in cypher_props)
            set_clause = f"SET {assignments}" if assignments else ""
            op = "MERGE" if merge else "CREATE"
            if merge:
                query = (
                    f"MATCH (a:{source_type} {{id: $__src}}) "
                    f"MATCH (b:{target_type} {{id: $__tgt}}) "
                    f"{op} (a)-[r:{relationship_type}]->(b) "
                    f"ON CREATE SET r.created_at = datetime() {set_clause}"
                )
            else:
                query = (
                    f"MATCH (a:{source_type} {{id: $__src}}) "
                    f"MATCH (b:{target_type} {{id: $__tgt}}) "
                    f"{op} (a)-[r:{relationship_type}]->(b) "
                    f"SET r.created_at = datetime() {set_clause}"
                )
            params = {"__src": source_id, "__tgt": target_id, **cypher_props}
            self._session._execute_authorized(query, params)

        self._pending.append((
            validate, execute,
            {
                "type": "relationship", "label": relationship_type,
                "data": rel_data,
                "m_type": MutationType.RELATIONSHIP_MERGE if merge else MutationType.RELATIONSHIP_CREATE,
                "entity_id": f"{source_id}->{target_id}",
            },
        ))

    def commit(self) -> Tuple[MutationReceipt, ...]:
        """Validate ALL, then execute ALL. Atomic fail-closed semantics."""
        self._check_open()

        # Phase 1: Validate every pending mutation
        pipeline_results = []
        for validate_fn, _, _ in self._pending:
            pipeline_results.append(validate_fn())  # raises on violation

        logger.info("[TX] %d mutations validated. Executing.", len(self._pending))

        # Phase 2: Execute and mint receipts
        receipts: List[MutationReceipt] = []
        for i, (_, execute_fn, meta) in enumerate(self._pending):
            execute_fn()
            receipt = _make_receipt(
                mutation_type=meta["m_type"],
                label=meta["label"],
                entity_id=meta.get("entity_id", str(meta["data"].get("id", ""))),
                correlation_id=self._session._correlation_id,
                payload=meta["data"],
                pipeline_hash=pipeline_results[i].pipeline_hash,
            )
            receipts.append(receipt)
            self._session._ledger.append(receipt)

        self._committed = True
        return tuple(receipts)

    def abort(self) -> None:
        self._aborted = True
        self._pending.clear()

    @property
    def is_open(self) -> bool:
        return not self._committed and not self._aborted

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def _check_open(self) -> None:
        if self._committed:
            raise RuntimeError("Transaction already committed")
        if self._aborted:
            raise RuntimeError("Transaction already aborted")
