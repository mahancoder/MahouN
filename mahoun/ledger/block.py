"""
Blockchain Block for Immutable Ledger
======================================

Provides tamper-evident blocks for audit trail.

Properties:
- Immutable once created
- Cryptographically linked to previous block
- Contains hash of own data
- Enables chain integrity verification
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from mahoun.ledger.models import LedgerEntry


# HARDENING PATCH P12: Frozen dataclass to prevent Block mutability
@dataclass(frozen=True)
class Block:
    """
    Immutable block in ledger blockchain

    Structure:
    - index: Position in chain (0 = genesis)
    - timestamp: When block was created
    - data: LedgerEntry (None for genesis)
    - prev_hash: Hash of previous block
    - hash: Hash of this block

    Guarantees:
    - Tamper-evident: Changing data invalidates hash
    - Chain-linked: Changing prev_hash breaks chain
    - Timestamped: Proves temporal ordering
    - Deterministic: Same input = same hash
    """

    index: int
    timestamp: datetime
    data: LedgerEntry | None
    prev_hash: str
    hash: str = field(default="", init=False)

    def __post_init__(self):
        """Compute hash after initialization"""
        if not self.hash:
            # Bypass frozen status to set the initial hash
            object.__setattr__(self, "hash", self.compute_hash())

    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of block

        Returns:
            Hex-encoded SHA-256 hash

        Note:
            Hash includes: index, timestamp, data, prev_hash
            Uses sorted JSON for determinism
        """
        # Prepare block data
        block_data: dict[str, Any] = {
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "prev_hash": self.prev_hash,
        }

        # Add ledger entry data (if not genesis)
        if self.data is not None:
            # HARDENING PATCH P11: Canonical serialization
            from mahoun.ledger.models import canonical_serialize

            block_data["data"] = canonical_serialize(self.data)
        else:
            block_data["data"] = None

        # Convert to deterministic JSON
        block_string = json.dumps(block_data, sort_keys=True, ensure_ascii=False)

        # Hash
        return hashlib.sha256(block_string.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> bool:
        """
        Verify block integrity

        Returns:
            True if block hash is valid, False otherwise

        Checks:
        - Stored hash matches computed hash
        """
        return self.hash == self.compute_hash()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert block to dictionary for serialization

        Returns:
            Dictionary representation
        """
        data_dict = None
        if self.data is not None:
            # HARDENING PATCH P11: Canonical serialization
            from mahoun.ledger.models import canonical_serialize

            data_dict = canonical_serialize(self.data)

        return {
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "data": data_dict,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Block":
        """
        Create block from dictionary

        Args:
            data: Dictionary representation

        Returns:
            Block instance
        """
        # Parse timestamp
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

        # Parse ledger entry (if present)
        ledger_data = None
        if data["data"] is not None:
            ledger_dict = dict(data["data"])
            if isinstance(ledger_dict.get("created_at"), str):
                ledger_dict["created_at"] = datetime.fromisoformat(ledger_dict["created_at"].replace("Z", "+00:00"))
            ledger_data = LedgerEntry(**ledger_dict)

        # Create block
        block = cls(index=data["index"], timestamp=timestamp, data=ledger_data, prev_hash=data["prev_hash"])

        # Verify hash matches
        if "hash" in data and data["hash"] != block.hash:
            raise ValueError(f"Block hash mismatch: stored={data['hash'][:16]}..., computed={block.hash[:16]}...")

        return block

    def __repr__(self) -> str:
        """String representation"""
        data_str = "genesis" if self.data is None else f"verdict={self.data.verdict_id[:8]}..."
        return f"Block(index={self.index}, data={data_str}, hash={self.hash[:16]}...)"

    def __eq__(self, other: object) -> bool:
        """Equality comparison"""
        if not isinstance(other, Block):
            return False
        return self.hash == other.hash

    def __hash__(self) -> int:
        """Hash for use in sets/dicts"""
        return int(self.hash[:16], 16)


def create_genesis_block() -> Block:
    """
    Create genesis block (first block in chain)

    HARDENING PATCH P13: Deterministic genesis block.
    Uses fixed timestamp so identical empty chains produce identical genesis hashes.

    Returns:
        Genesis block with index=0, no data, prev_hash="0"
    """
    # Fixed MAHOUN epoch for deterministic genesis hashing
    mahoun_epoch = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    return Block(
        index=0,
        timestamp=mahoun_epoch,
        data=None,
        prev_hash="0" * 64,  # 64 hex chars = 256 bits
    )


# Example usage
if __name__ == "__main__":
    from datetime import datetime

    from mahoun.ledger.models import LedgerEntry

    print("🔗 Blockchain Block Test")
    print("=" * 60)

    # Create genesis block
    genesis = create_genesis_block()
    print(f"✓ Genesis block: {genesis}")
    print(f"  Hash: {genesis.hash[:32]}...")
    print(f"  Integrity: {genesis.verify_integrity()}")

    # Create first data block
    entry = LedgerEntry(
        verdict_id="verdict_123",
        case_id="case_456",
        referenced_ltm_nodes=["rule_219"],
        referenced_facts=["fact_0"],
        confidence=0.92,
        invariant_version="v2.1.0",
        guard_mode="STRICT",
        created_at=datetime.now(UTC),
    )

    block1 = Block(index=1, timestamp=datetime.now(UTC), data=entry, prev_hash=genesis.hash)

    print(f"\n✓ Block 1: {block1}")
    print(f"  Hash: {block1.hash[:32]}...")
    print(f"  Prev hash: {block1.prev_hash[:32]}...")
    print(f"  Integrity: {block1.verify_integrity()}")

    # Verify chain link
    chain_valid = block1.prev_hash == genesis.hash
    print(f"  Chain link valid: {chain_valid}")

    # Try tampering
    print("\n🔒 Tamper Detection Test")
    original_hash = block1.hash
    block1.data.confidence = 0.99  # Tamper with data
    block1.hash = ""  # Force recompute
    block1.hash = block1.compute_hash()
    tampered_hash = block1.hash

    print(f"  Original hash: {original_hash[:32]}...")
    print(f"  Tampered hash: {tampered_hash[:32]}...")
    print(f"  Hashes match: {original_hash == tampered_hash}")

    # Serialization test
    print("\n💾 Serialization Test")
    block_dict = block1.to_dict()
    block1_restored = Block.from_dict(block_dict)
    print(f"  Serialization successful: {block1_restored.hash == block1.hash}")
