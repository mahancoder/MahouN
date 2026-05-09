"""
Immutable Blockchain Ledger
============================

Provides tamper-evident audit trail for verdicts.

Architecture:
- Blockchain-based (linked blocks)
- Append-only (no modifications)
- Cryptographically secured (hash chains)
- Integrity verifiable (full chain validation)

Guarantees:
- Immutability: Cannot modify past entries
- Auditability: Complete history preserved
- Tamper-evidence: Any change detected
- Temporal ordering: Chronological sequence
"""

import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

from mahoun.ledger.block import Block, create_genesis_block
from mahoun.ledger.models import LedgerEntry
from mahoun.core.logging import setup_logger

log = setup_logger("blockchain_ledger")


class ImmutableLedger:
    """
    Blockchain-based immutable ledger
    
    Properties:
    - Append-only: Can only add, never modify
    - Tamper-evident: Changes invalidate chain
    - Persistent: Survives restarts
    - Verifiable: Full integrity check
    
    Thread-safety:
    - Not thread-safe by default
    - Use external locking for concurrent access
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize immutable ledger
        
        Args:
            storage_path: Path to persist blockchain (optional)
        """
        self.chain: List[Block] = []
        self.storage_path = storage_path
        
        # Load existing chain or create genesis
        if storage_path and os.path.exists(storage_path):
            self._load_from_disk()
        else:
            self._create_genesis_block()
        
        log.info(f"Immutable ledger initialized with {len(self.chain)} blocks")
    
    def _create_genesis_block(self) -> None:
        """Create genesis block (first block in chain)"""
        genesis = create_genesis_block()
        self.chain.append(genesis)
        log.debug("Genesis block created")
    
    def append(self, entry: LedgerEntry) -> Block:
        """
        Append entry to ledger (immutable operation)
        
        Args:
            entry: LedgerEntry to append
        
        Returns:
            Block containing the entry
        
        Raises:
            ValueError: If entry is invalid
            RuntimeError: If chain integrity check fails
        
        Note:
            This is the ONLY way to add data to ledger.
            No modification or deletion operations exist.
        """
        # Validate entry
        if not entry.verdict_id or not entry.case_id:
            raise ValueError("verdict_id and case_id must not be empty")
        
        # Get previous block
        prev_block = self.chain[-1]
        
        # Create new block
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now(timezone.utc),
            data=entry,
            prev_hash=prev_block.hash
        )
        
        # Append to chain
        self.chain.append(new_block)
        
        # Verify integrity after append
        if not self.verify_integrity():
            # Rollback
            self.chain.pop()
            raise RuntimeError("Chain integrity check failed after append")
        
        # Persist to disk
        if self.storage_path:
            self._persist_to_disk()
        
        log.debug(f"Appended block {new_block.index}: verdict={entry.verdict_id[:8]}...")
        
        return new_block
    
    def verify_integrity(self) -> bool:
        """
        Verify entire chain integrity
        
        Returns:
            True if chain is valid, False otherwise
        
        Checks:
        1. Each block's hash is valid
        2. Each block links to previous block
        3. Genesis block is valid
        """
        if not self.chain:
            return False
        
        # Check genesis block
        genesis = self.chain[0]
        if genesis.index != 0:
            log.error("Genesis block has invalid index")
            return False
        if genesis.prev_hash != "0" * 64:
            log.error("Genesis block has invalid prev_hash")
            return False
        if not genesis.verify_integrity():
            log.error("Genesis block integrity check failed")
            return False
        
        # Check each subsequent block
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]
            
            # Verify block hash
            if not current.verify_integrity():
                log.error(f"Block {i} integrity check failed")
                return False
            
            # Verify chain link
            if current.prev_hash != prev.hash:
                log.error(f"Block {i} chain link broken")
                return False
            
            # Verify index
            if current.index != i:
                log.error(f"Block {i} has invalid index: {current.index}")
                return False
        
        return True
    
    def get_entry(self, verdict_id: str) -> Optional[LedgerEntry]:
        """
        Get entry by verdict ID
        
        Args:
            verdict_id: Verdict identifier
        
        Returns:
            LedgerEntry if found, None otherwise
        """
        for block in self.chain[1:]:  # Skip genesis
            if block.data and block.data.verdict_id == verdict_id:
                return block.data
        return None
    
    def find_entries_using_node(self, node_id: str) -> List[LedgerEntry]:
        """
        Find all entries referencing a node
        
        Args:
            node_id: Node identifier
        
        Returns:
            List of LedgerEntry objects
        
        Use case:
            When a rule/precedent is updated, find all verdicts
            that used it and mark them for review.
        """
        results = []
        for block in self.chain[1:]:  # Skip genesis
            if block.data:
                if node_id in block.data.referenced_ltm_nodes:
                    results.append(block.data)
                elif node_id in block.data.referenced_facts:
                    results.append(block.data)
        return results
    
    def get_entries_by_case(self, case_id: str) -> List[LedgerEntry]:
        """
        Get all entries for a case
        
        Args:
            case_id: Case identifier
        
        Returns:
            List of LedgerEntry objects in chronological order
        """
        results = []
        for block in self.chain[1:]:  # Skip genesis
            if block.data and block.data.case_id == case_id:
                results.append(block.data)
        return results
    
    def get_entries_in_range(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[LedgerEntry]:
        """
        Get entries in time range
        
        Args:
            start_time: Start of range (inclusive)
            end_time: End of range (inclusive)
        
        Returns:
            List of LedgerEntry objects
        """
        results = []
        for block in self.chain[1:]:  # Skip genesis
            if block.data:
                if start_time <= block.data.created_at <= end_time:
                    results.append(block.data)
        return results
    
    def _persist_to_disk(self) -> None:
        """
        Persist blockchain to disk
        
        Format: JSON array of blocks
        
        Note:
            Atomic write using temp file + rename
        """
        if not self.storage_path:
            return
        
        # Ensure directory exists
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize chain
        chain_data = [block.to_dict() for block in self.chain]
        
        # Atomic write
        temp_path = f"{self.storage_path}.tmp"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(chain_data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            os.replace(temp_path, self.storage_path)
            
        except Exception as e:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(f"Failed to persist ledger: {e}") from e
    
    def _load_from_disk(self) -> None:
        """
        Load blockchain from disk
        
        Raises:
            RuntimeError: If chain is invalid
        """
        if not self.storage_path or not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                chain_data = json.load(f)
            
            # Reconstruct blocks
            self.chain = [Block.from_dict(block_dict) for block_dict in chain_data]
            
            # Verify integrity
            if not self.verify_integrity():
                raise RuntimeError("Loaded chain failed integrity check")
            
            log.info(f"Loaded {len(self.chain)} blocks from disk")
        
        except Exception as e:
            raise RuntimeError(f"Failed to load ledger: {e}") from e
    
    def export_audit_report(
        self,
        output_path: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> None:
        """
        Export audit report
        
        Args:
            output_path: Path to write report
            start_time: Start of range (optional)
            end_time: End of range (optional)
        
        Format:
            JSON with chain metadata + entries
        """
        # Get entries in range
        if start_time and end_time:
            entries = self.get_entries_in_range(start_time, end_time)
        else:
            entries = [block.data for block in self.chain[1:] if block.data]
        
        # Build report
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "chain_length": len(self.chain),
            "entries_count": len(entries),
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "chain_integrity": self.verify_integrity(),
            "entries": [entry.model_dump() for entry in entries]
        }
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        log.info(f"Exported audit report to {output_path}")
    
    def __len__(self) -> int:
        """Return number of blocks (including genesis)"""
        return len(self.chain)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ImmutableLedger(blocks={len(self.chain)}, integrity={self.verify_integrity()})"


# Example usage
if __name__ == "__main__":
    import tempfile
    
    print("⛓️  Immutable Blockchain Ledger Test")
    print("=" * 60)
    
    # Create ledger with temp storage
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        storage_path = f.name
    
    ledger = ImmutableLedger(storage_path=storage_path)
    print(f"✓ Created ledger: {ledger}")
    
    # Add entries
    for i in range(3):
        entry = LedgerEntry(
            verdict_id=f"verdict_{i}",
            case_id=f"case_{i}",
            referenced_ltm_nodes=[f"rule_{i}"],
            referenced_facts=[f"fact_{i}"],
            confidence=0.9 + i * 0.02,
            invariant_version="v2.1.0",
            guard_mode="STRICT",
            created_at=datetime.now(timezone.utc)
        )
        block = ledger.append(entry)
        print(f"✓ Appended block {block.index}")
    
    # Verify integrity
    print(f"\n✓ Chain integrity: {ledger.verify_integrity()}")
    
    # Query
    entry = ledger.get_entry("verdict_1")
    print(f"✓ Retrieved entry: {entry.verdict_id if entry else None}")
    
    # Find by node
    entries = ledger.find_entries_using_node("rule_1")
    print(f"✓ Found {len(entries)} entries using rule_1")
    
    # Reload from disk
    ledger2 = ImmutableLedger(storage_path=storage_path)
    print(f"✓ Reloaded ledger: {ledger2}")
    print(f"✓ Chains match: {len(ledger.chain) == len(ledger2.chain)}")
    
    # Cleanup
    os.remove(storage_path)
