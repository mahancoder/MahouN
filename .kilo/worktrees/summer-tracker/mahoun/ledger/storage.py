# mahoun/ledger/storage.py
"""
DEPRECATED: Legacy ledger storage API
======================================

⚠️ WARNING: This module is DEPRECATED and will be removed in v2.0.0

Use mahoun.ledger.writer instead:
    from mahoun.ledger.writer import (
        JSONLLedgerBackend,  # Instead of FileLedgerWriter
        NoOpLedgerBackend,   # Instead of NoOpLedgerWriter
        EvidenceLedgerWriter,
    )

This compatibility shim exists only for backward compatibility.
All new code should use mahoun.ledger.writer.

Migration Timeline:
- v1.1.0 (current): Deprecation warnings added
- v1.2.0 (next month): Warnings become errors in tests
- v2.0.0 (3 months): This module removed completely
"""

import warnings
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import os

# Import from modern API
from mahoun.ledger.writer import (
    EvidenceLedgerWriter,
    JSONLLedgerBackend,
    NoOpLedgerBackend as _NoOpLedgerBackend,
)
from mahoun.ledger.models import LedgerEntry


# Emit deprecation warning on module import
warnings.warn(
    "mahoun.ledger.storage is deprecated. Use mahoun.ledger.writer instead. "
    "See migration guide: docs/LEDGER_MIGRATION.md",
    DeprecationWarning,
    stacklevel=2
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

class FileLedgerWriter(EvidenceLedgerWriter):
    """
    DEPRECATED: Use JSONLLedgerBackend from mahoun.ledger.writer instead.
    
    This is a legacy compatibility wrapper that will be removed in v2.0.0.
    """
    
    def __init__(self, base_dir: str, fsync: bool = True):
        warnings.warn(
            "FileLedgerWriter is deprecated. Use JSONLLedgerBackend from mahoun.ledger.writer",
            DeprecationWarning,
            stacklevel=2
        )
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.fsync = fsync
        self._head_path = self.base_dir / "ledger.head"
        if not self._head_path.exists():
            self._head_path.write_text("0" * 64, encoding="utf-8")

    def _get_prev(self) -> str:
        return self._head_path.read_text(encoding="utf-8").strip() or ("0" * 64)

    def _set_prev(self, value: str) -> None:
        self._head_path.write_text(value, encoding="utf-8")

    def write(
        self,
        event_type_or_entry: Any,
        request_id: str | None = None,
        payload: dict[str, Any] | None = None
    ) -> str:
        if isinstance(event_type_or_entry, LedgerEntry):
            entry = event_type_or_entry
            event_type = entry.event_type or "verdict"
            request_id = entry.request_id or entry.verdict_id
            timestamp = entry.created_at or datetime.now(timezone.utc)
            payload = {
                "verdict_id": entry.verdict_id,
                "case_id": entry.case_id,
                "referenced_ltm_nodes": entry.referenced_ltm_nodes,
                "referenced_facts": entry.referenced_facts,
                "confidence": entry.confidence,
                "invariant_version": entry.invariant_version,
                "guard_mode": entry.guard_mode,
                "created_at": timestamp.isoformat(),
            }
        else:
            event_type = str(event_type_or_entry)
            timestamp = datetime.now(timezone.utc)
            if request_id is None or payload is None:
                raise ValueError("request_id and payload are required")

        prev_hash = self._get_prev()
        record = {
            "ts": timestamp.isoformat(),
            "event_type": event_type,
            "request_id": request_id,
            "payload": payload,
            "prev_hash": prev_hash,
        }
        record_hash = _sha256(prev_hash + _canon(record))
        record["hash"] = record_hash

        day = record["ts"][:10]
        out = self.base_dir / f"{day}.jsonl"
        line = _canon(record) + "\n"

        with out.open("a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            if self.fsync:
                os.fsync(f.fileno())

        self._set_prev(record_hash)
        return record_hash


# Compatibility alias for tests expecting FileLedgerBackend
FileLedgerBackend = JSONLLedgerBackend

class NoOpLedgerWriter(EvidenceLedgerWriter):
    """
    DEPRECATED: Use NoOpLedgerBackend from mahoun.ledger.writer instead.
    
    This is a legacy compatibility wrapper that will be removed in v2.0.0.
    """
    
    def __init__(self):
        warnings.warn(
            "NoOpLedgerWriter is deprecated. Use NoOpLedgerBackend from mahoun.ledger.writer",
            DeprecationWarning,
            stacklevel=2
        )
        env = os.getenv("MAHOUN_ENV", "dev").lower()
        if env in ("staging", "prod", "production"):
            raise RuntimeError(
                "NoOpLedgerWriter is not allowed in staging/prod. "
                "Configure JSONLLedgerBackend instead."
            )

    def write(
        self,
        event_type_or_entry: Any,
        request_id: str | None = None,
        payload: dict[str, Any] | None = None
    ) -> str:
        return "0" * 64
