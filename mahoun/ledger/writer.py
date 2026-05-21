"""
Evidence Ledger Writer
======================
Production-grade ledger writer with blockchain-based immutability.

Invariants enforced:
- EL-I1: Every entry has evidence references
- EL-I4: Entries are immutable (blockchain-based)
- EL-I6: Cryptographic proof enables tamper detection

CRITICAL: This module now uses ImmutableLedger (blockchain) instead of
simple hash chains for production-grade immutability guarantees.
"""

import hashlib
import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from mahoun.ledger.blockchain import ImmutableLedger
from mahoun.ledger.models import LedgerEntry

if TYPE_CHECKING:
    from mahoun.graph.ultra_graph_builder import UltraGraphBuilder

logger = logging.getLogger(__name__)


class LedgerBackend(ABC):
    """Abstract backend for ledger storage."""

    @abstractmethod
    def write(self, entry: LedgerEntry, entry_hash: str, prev_hash: str) -> None:
        """Write entry to storage."""
        pass

    @abstractmethod
    def get_last_hash(self) -> str:
        """Get hash of last entry (or 'genesis' if empty)."""
        pass

    @abstractmethod
    def read_all(self) -> list[dict[str, Any]]:
        """Read all entries (for verification)."""
        pass

    @abstractmethod
    def verify_chain(self) -> bool:
        """Verify hash chain integrity."""
        pass


class JSONLLedgerBackend(LedgerBackend):
    """
    Append-only JSONL file backend.

    Each line is a JSON object with:
    - entry: The ledger entry data
    - hash: SHA-256 hash of entry + prev_hash
    - prev_hash: Hash of previous entry
    - written_at: Timestamp of write
    """

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"JSONL Ledger Backend initialized at {path}")

    def write(self, entry: LedgerEntry, entry_hash: str, prev_hash: str) -> None:
        """Append entry to JSONL file."""
        record = {
            "entry": self._entry_to_dict(entry),
            "hash": entry_hash,
            "prev_hash": prev_hash,
            "written_at": datetime.now(UTC).isoformat(),
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")
        logger.debug(f"Ledger entry written: {entry.verdict_id}")

    def get_last_hash(self) -> str:
        """Get hash of last entry."""
        if not self.path.exists():
            return "genesis"

        with open(self.path, encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return "genesis"
            last = json.loads(lines[-1])
            return last["hash"]

    def read_all(self) -> list[dict[str, Any]]:
        """Read all entries."""
        if not self.path.exists():
            return []

        entries = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return entries

    def verify_chain(self) -> bool:
        """Verify hash chain integrity."""
        entries = self.read_all()
        if not entries:
            return True

        prev_hash = "genesis"
        for record in entries:
            expected_hash = self._compute_hash(record["entry"], prev_hash)
            if record["hash"] != expected_hash:
                logger.error(f"Hash chain broken at {record['entry'].get('verdict_id')}")
                return False
            prev_hash = record["hash"]

        return True

    def _entry_to_dict(self, entry: LedgerEntry) -> dict[str, Any]:
        """Convert LedgerEntry to dict."""
        return {
            "verdict_id": entry.verdict_id,
            "case_id": entry.case_id,
            "referenced_ltm_nodes": list(entry.referenced_ltm_nodes),
            "referenced_facts": list(entry.referenced_facts),
            "confidence": entry.confidence,
            "invariant_version": entry.invariant_version,
            "guard_mode": entry.guard_mode,
            "created_at": entry.created_at.isoformat()
            if isinstance(entry.created_at, datetime)
            else str(entry.created_at),
            "event_type": entry.event_type,
            "request_id": entry.request_id,
        }

    def _compute_hash(self, entry_dict: dict[str, Any], prev_hash: str) -> str:
        """Compute hash for verification."""
        content = json.dumps(entry_dict, default=str, sort_keys=True)
        return hashlib.sha256(f"{prev_hash}:{content}".encode()).hexdigest()


class SQLiteLedgerBackend(LedgerBackend):
    """
    SQLite backend for ledger storage.

    Provides ACID guarantees and efficient querying.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
        logger.info(f"SQLite Ledger Backend initialized at {db_path}")

    def _init_db(self) -> None:
        """Initialize database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verdict_id TEXT NOT NULL,
                case_id TEXT NOT NULL,
                referenced_ltm_nodes TEXT NOT NULL,
                referenced_facts TEXT NOT NULL,
                confidence REAL NOT NULL,
                invariant_version TEXT NOT NULL,
                guard_mode TEXT NOT NULL,
                created_at TEXT NOT NULL,
                event_type TEXT,
                request_id TEXT,
                entry_hash TEXT NOT NULL UNIQUE,
                prev_hash TEXT NOT NULL,
                written_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_verdict_id ON ledger(verdict_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_case_id ON ledger(case_id)")
        conn.commit()
        conn.close()

    def write(self, entry: LedgerEntry, entry_hash: str, prev_hash: str) -> None:
        """Insert entry into database."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """INSERT INTO ledger 
                   (verdict_id, case_id, referenced_ltm_nodes, referenced_facts,
                    confidence, invariant_version, guard_mode, created_at,
                    event_type, request_id, entry_hash, prev_hash, written_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.verdict_id,
                    entry.case_id,
                    json.dumps(list(entry.referenced_ltm_nodes)),
                    json.dumps(list(entry.referenced_facts)),
                    entry.confidence,
                    entry.invariant_version,
                    entry.guard_mode,
                    entry.created_at.isoformat() if isinstance(entry.created_at, datetime) else str(entry.created_at),
                    entry.event_type,
                    entry.request_id,
                    entry_hash,
                    prev_hash,
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()
            logger.debug(f"Ledger entry written to SQLite: {entry.verdict_id}")
        finally:
            conn.close()

    def get_last_hash(self) -> str:
        """Get hash of last entry."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute("SELECT entry_hash FROM ledger ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else "genesis"
        finally:
            conn.close()

    def read_all(self) -> list[dict[str, Any]]:
        """Read all entries."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute(
                """SELECT verdict_id, case_id, referenced_ltm_nodes, referenced_facts,
                          confidence, invariant_version, guard_mode, created_at,
                          event_type, request_id, entry_hash, prev_hash, written_at
                   FROM ledger ORDER BY id ASC"""
            )
            entries = []
            for row in cursor:
                entries.append(
                    {
                        "entry": {
                            "verdict_id": row[0],
                            "case_id": row[1],
                            "referenced_ltm_nodes": json.loads(row[2]),
                            "referenced_facts": json.loads(row[3]),
                            "confidence": row[4],
                            "invariant_version": row[5],
                            "guard_mode": row[6],
                            "created_at": row[7],
                            "event_type": row[8],
                            "request_id": row[9],
                        },
                        "hash": row[10],
                        "prev_hash": row[11],
                        "written_at": row[12],
                    }
                )
            return entries
        finally:
            conn.close()

    def verify_chain(self) -> bool:
        """Verify hash chain integrity."""
        entries = self.read_all()
        if not entries:
            return True

        prev_hash = "genesis"
        for record in entries:
            content = json.dumps(record["entry"], default=str, sort_keys=True)
            expected_hash = hashlib.sha256(f"{prev_hash}:{content}".encode()).hexdigest()
            if record["hash"] != expected_hash:
                logger.error(f"Hash chain broken at {record['entry'].get('verdict_id')}")
                return False
            prev_hash = record["hash"]

        return True


class NoOpLedgerBackend(LedgerBackend):
    """
    No-op backend for testing/development only.

    WARNING: This backend does NOT persist data.
    Only use in test/dev environments.

    HARDENING PATCH P04: Raises RuntimeError if used in production.
    """

    def __init__(self):
        # HARDENING: Prevent use in production
        from mahoun.core.environment import get_environment_name

        _env = get_environment_name()
        if _env == "production":
            raise RuntimeError(
                "FATAL: NoOpLedgerBackend cannot be used in PRODUCTION mode. "
                "All ledger writes would be silently discarded, violating EL-I3 "
                "(Verdict Blocking) and EL-I6 (Audit Sufficiency). "
                "Use 'blockchain', 'jsonl', or 'sqlite' backend instead."
            )
        self._entries: list[dict[str, Any]] = []
        self._last_hash = "genesis"
        logger.warning("⚠️ NoOpLedgerBackend: Data will NOT be persisted!")

    def write(self, entry: LedgerEntry, entry_hash: str, prev_hash: str) -> None:
        self._entries.append({"entry": entry, "hash": entry_hash, "prev_hash": prev_hash})
        self._last_hash = entry_hash

    def get_last_hash(self) -> str:
        return self._last_hash

    def read_all(self) -> list[dict[str, Any]]:
        return self._entries

    def verify_chain(self) -> bool:
        # HARDENING PATCH P17: Implement actual in-memory chain verification
        if not self._entries:
            return True

        current_prev = "genesis"
        for i, record in enumerate(self._entries):
            if record["prev_hash"] != current_prev:
                logger.error(f"Chain broken at index {i}: expected prev {current_prev}, got {record['prev_hash']}")
                return False

            # Verify the hash matches content
            import hashlib
            import json

            from mahoun.ledger.models import canonical_serialize

            content = json.dumps(canonical_serialize(record["entry"]), default=str, sort_keys=True)
            expected_hash = hashlib.sha256(f"{current_prev}:{content}".encode()).hexdigest()

            if record["hash"] != expected_hash:
                logger.error(f"Hash mismatch at index {i}: expected {expected_hash}, got {record['hash']}")
                return False

            current_prev = record["hash"]

        return True


class EvidenceLedgerWriter:
    """
    Production-grade ledger writer with blockchain-based immutability.

    Invariants enforced:
    - EL-I1: Every entry has evidence references (validated by guards.py)
    - EL-I2: Referenced nodes exist in graph (deep validation)
    - EL-I4: Entries are immutable (blockchain-based)
    - EL-I6: Cryptographic proof enables tamper detection

    Usage:
        # Blockchain-based (RECOMMENDED for production)
        writer = EvidenceLedgerWriter.create_blockchain(
            storage_path=Path("data/ledger"),
            graph_builder=graph_builder
        )

        # Legacy backend (backward compatibility)
        backend = JSONLLedgerBackend(Path("data/ledger.jsonl"))
        writer = EvidenceLedgerWriter(backend=backend)

        # Write entry
        entry = LedgerEntry(...)
        entry_hash = writer.write(entry)
    """

    def __init__(
        self,
        backend: LedgerBackend | None = None,
        blockchain: ImmutableLedger | None = None,
        graph_builder: Optional["UltraGraphBuilder"] = None,
    ):
        """
        Initialize ledger writer.

        Args:
            backend: Legacy backend (deprecated, for backward compatibility)
            blockchain: ImmutableLedger instance (recommended)
            graph_builder: Optional graph builder for deep validation

        Note: Either backend OR blockchain must be provided, not both.
        """
        if backend is None and blockchain is None:
            raise ValueError("Either backend or blockchain must be provided")
        if backend is not None and blockchain is not None:
            raise ValueError("Cannot use both backend and blockchain")

        self.backend = backend
        self.blockchain = blockchain
        self.graph_builder = graph_builder

        if blockchain:
            logger.info("EvidenceLedgerWriter initialized with ImmutableLedger (blockchain)")
        else:
            logger.info(f"EvidenceLedgerWriter initialized with {type(backend).__name__} (legacy)")

    @classmethod
    def create_blockchain(
        cls, storage_path: Path, graph_builder: Optional["UltraGraphBuilder"] = None
    ) -> "EvidenceLedgerWriter":
        """
        Create writer with blockchain-based storage (RECOMMENDED).

        Args:
            storage_path: Directory for blockchain storage
            graph_builder: Optional graph builder for deep validation

        Returns:
            EvidenceLedgerWriter with blockchain backend
        """
        blockchain = ImmutableLedger(str(storage_path))
        return cls(blockchain=blockchain, graph_builder=graph_builder)

    def _compute_hash(self, entry: LedgerEntry, prev_hash: str) -> str:
        """
        Compute SHA-256 hash for entry including previous hash.

        This creates a hash chain where each entry's hash depends on
        all previous entries, enabling tamper detection.
        """
        # HARDENING PATCH P11: Canonical serialization
        from mahoun.ledger.models import canonical_serialize

        entry_dict = canonical_serialize(entry)
        content = json.dumps(entry_dict, default=str, sort_keys=True)
        return hashlib.sha256(f"{prev_hash}{content}".encode()).hexdigest()

    def write(self, entry: LedgerEntry) -> str:
        """
        Write ledger entry (either to blockchain or legacy backend).

        Args:
            entry: LedgerEntry to write

        Returns:
            Hex-encoded hash of the written entry
        """
        try:
            # EL-I1: Verify evidence references exist
            from mahoun.ledger.guards import validate_entry

            validate_entry(entry, self.graph_builder)

            # Write to blockchain or legacy backend
            if self.blockchain:
                # Blockchain-based write with cryptographic proof
                block = self.blockchain.append(entry)
                logger.info(
                    f"Ledger entry written to blockchain: verdict={entry.verdict_id}, block={block.index}, hash={block.hash[:16]}..."
                )
                return block.hash
            else:
                # Legacy backend write
                if self.backend is None:
                    raise RuntimeError("No ledger backend configured")
                prev_hash = self.backend.get_last_hash()
                entry_hash = self._compute_hash(entry, prev_hash)
                self.backend.write(entry, entry_hash, prev_hash)
                logger.info(f"Ledger entry written: verdict={entry.verdict_id}, hash={entry_hash[:16]}...")
                return entry_hash
        except ValueError as e:
            # Validation failure
            logger.error(f"Ledger validation failed: {e}")
            raise
        except Exception as e:
            # EL-I3: Verdict Blocking - failure here prevents verdict publication
            logger.error(f"Ledger write failed: {e}")
            raise RuntimeError(f"Ledger write failed: {e}") from e

    def verify_integrity(self) -> bool:
        """
        Verify ledger integrity (blockchain or hash chain).

        Returns:
            True if chain is valid, False if tampered
        """
        if self.blockchain:
            return self.blockchain.verify_integrity()
        else:
            if self.backend is None:
                return True
            return self.backend.verify_chain()


def create_ledger_writer(
    backend_type: str = "blockchain", path: Path | None = None, graph_builder: Optional["UltraGraphBuilder"] = None
) -> EvidenceLedgerWriter:
    """
    Factory function to create ledger writer.

    Args:
        backend_type: "blockchain" (recommended), "jsonl", "sqlite", or "noop"
        path: Path for storage (not needed for noop)
        graph_builder: Optional graph builder for deep validation

    Returns:
        Configured EvidenceLedgerWriter
    """
    if backend_type == "blockchain":
        path = path or Path("data/ledger")
        return EvidenceLedgerWriter.create_blockchain(path, graph_builder)

    backend: LedgerBackend
    if backend_type == "jsonl":
        path = path or Path("data/ledger/evidence.jsonl")
        backend = JSONLLedgerBackend(path)
    elif backend_type == "sqlite":
        path = path or Path("data/ledger/evidence.db")
        backend = SQLiteLedgerBackend(path)
    elif backend_type == "noop":
        backend = NoOpLedgerBackend()
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")

    return EvidenceLedgerWriter(backend=backend, graph_builder=graph_builder)
