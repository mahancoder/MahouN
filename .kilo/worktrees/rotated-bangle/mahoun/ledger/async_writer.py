"""
Async Ledger Writer
===================

High-throughput async ledger writer with:
- Async I/O for non-blocking writes
- Batch processing for efficiency
- Connection pooling for databases
- Backpressure handling
- Dead letter queue (DLQ) for failed writes

CRITICAL: Maintains audit trail integrity under high load.
"""

import asyncio
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass

from mahoun.core.logging import setup_logger
from mahoun.ledger.models import LedgerEntry
from mahoun.ledger.writer import JSONLLedgerBackend

log = setup_logger("async_ledger_writer")


@dataclass
class WriteResult:
    """Result of async write operation"""
    success: bool
    entry_hash: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


class AsyncLedgerWriter:
    """
    Async ledger writer for high-throughput scenarios.
    
    Features:
    - Async I/O (non-blocking)
    - Batch writes (configurable batch size)
    - Automatic retry with exponential backoff
    - Dead letter queue for failed writes
    - Backpressure handling (queue size limits)
    - Connection pooling (for database backends)
    
    Performance:
    - Target: 1000+ writes/sec
    - Latency: <10ms per write (batched)
    - Memory: O(batch_size)
    
    Audit Integrity:
    - Hash chain maintained across batches
    - Failed writes moved to DLQ (not lost)
    - Retry with exponential backoff
    """
    
    def __init__(
        self,
        backend: JSONLLedgerBackend,
        batch_size: int = 100,
        max_queue_size: int = 10000,
        flush_interval_sec: float = 1.0,
        max_retries: int = 3,
        dlq_path: Optional[Path] = None
    ):
        """
        Initialize async ledger writer.
        
        Args:
            backend: Ledger storage backend (JSONLLedgerBackend from mahoun.ledger.writer)
            batch_size: Number of entries per batch
            max_queue_size: Maximum queue size (backpressure)
            flush_interval_sec: Auto-flush interval
            max_retries: Maximum retry attempts
            dlq_path: Path for dead letter queue
        """
        self.backend = backend
        self.batch_size = batch_size
        self.max_queue_size = max_queue_size
        self.flush_interval_sec = flush_interval_sec
        self.max_retries = max_retries
        
        # Write queue (bounded for backpressure)
        self._write_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        
        # Batch writer task
        self._batch_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Dead letter queue
        self.dlq_path = dlq_path or Path("./data/dlq")
        self.dlq_path.mkdir(parents=True, exist_ok=True)
        
        # Metrics
        self._total_writes = 0
        self._successful_writes = 0
        self._failed_writes = 0
        self._dlq_writes = 0
        self._total_batches = 0
        
        # Hash chain state
        self._last_hash = "genesis"
        self._hash_lock = asyncio.Lock()
        
        log.info(
            f"Initialized AsyncLedgerWriter "
            f"(batch_size={batch_size}, max_queue={max_queue_size})"
        )
    
    async def start(self) -> None:
        """Start async batch writer"""
        if self._running:
            log.warning("AsyncLedgerWriter already running")
            return
        
        self._running = True
        self._batch_task = asyncio.create_task(self._batch_writer_loop())
        log.info("AsyncLedgerWriter started")
    
    async def stop(self, timeout: float = 30.0) -> None:
        """
        Stop async batch writer and flush remaining entries.
        
        Args:
            timeout: Maximum time to wait for flush
        """
        if not self._running:
            return
        
        log.info("Stopping AsyncLedgerWriter...")
        self._running = False
        
        # Cancel batch task
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await asyncio.wait_for(self._batch_task, timeout=timeout)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        
        # Flush remaining entries
        await self._flush_queue(timeout=timeout)
        
        log.info("AsyncLedgerWriter stopped")
    
    async def write(self, entry: LedgerEntry) -> WriteResult:
        """
        Queue entry for async writing.
        
        Args:
            entry: Ledger entry to write
            
        Returns:
            WriteResult with success status
            
        Raises:
            asyncio.QueueFull: If queue is full (backpressure)
        """
        if not self._running:
            raise RuntimeError("AsyncLedgerWriter not started")
        
        # Create future for result
        future: asyncio.Future = asyncio.Future()
        
        try:
            # Put in queue (with timeout for backpressure)
            await asyncio.wait_for(
                self._write_queue.put((entry, future)),
                timeout=5.0
            )
            
            self._total_writes += 1
            
            # Wait for result
            result = await future
            return result
            
        except asyncio.TimeoutError:
            log.error("Write queue full (backpressure)")
            return WriteResult(
                success=False,
                error="Queue full (backpressure)"
            )
    
    async def _batch_writer_loop(self) -> None:
        """Background task for batch writing"""
        batch: List[Tuple[LedgerEntry, asyncio.Future]] = []
        last_flush = asyncio.get_event_loop().time()
        
        while self._running:
            try:
                # Wait for entry with timeout
                try:
                    entry, future = await asyncio.wait_for(
                        self._write_queue.get(),
                        timeout=self.flush_interval_sec
                    )
                    batch.append((entry, future))
                except asyncio.TimeoutError:
                    pass  # Timeout - check if should flush
                
                current_time = asyncio.get_event_loop().time()
                time_since_flush = current_time - last_flush
                
                # Flush if batch full or interval elapsed
                should_flush = (
                    len(batch) >= self.batch_size or
                    (batch and time_since_flush >= self.flush_interval_sec)
                )
                
                if should_flush:
                    await self._write_batch(batch)
                    batch = []
                    last_flush = current_time
                    
            except asyncio.CancelledError:
                log.info("Batch writer cancelled")
                break
            except Exception as e:
                log.error(f"Batch writer error: {e}", exc_info=True)
        
        # Flush remaining batch
        if batch:
            await self._write_batch(batch)
    
    async def _write_batch(
        self,
        batch: List[Tuple[LedgerEntry, asyncio.Future]]
    ) -> None:
        """
        Write batch of entries.
        
        CRITICAL: Maintains hash chain integrity across batch.
        """
        if not batch:
            return
        
        log.debug(f"Writing batch of {len(batch)} entries")
        
        # Acquire hash lock for atomic batch write
        async with self._hash_lock:
            prev_hash = self._last_hash
            
            for entry, future in batch:
                try:
                    # Compute hash
                    entry_dict = self._entry_to_dict(entry)
                    entry_hash = self._compute_hash(entry_dict, prev_hash)
                    
                    # Write to backend (in thread pool to avoid blocking)
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None,
                        self._sync_write,
                        entry_dict,
                        entry_hash
                    )
                    
                    # Update hash chain
                    prev_hash = entry_hash
                    
                    # Set result
                    result = WriteResult(success=True, entry_hash=entry_hash)
                    future.set_result(result)
                    
                    self._successful_writes += 1
                    
                except Exception as e:
                    log.error(f"Write failed: {e}")
                    
                    # Retry logic
                    retry_count = getattr(entry, "_retry_count", 0)
                    
                    if retry_count < self.max_retries:
                        # Retry with exponential backoff
                        entry._retry_count = retry_count + 1  # type: ignore
                        await asyncio.sleep(2 ** retry_count)
                        
                        # Re-queue
                        await self._write_queue.put((entry, future))
                        log.info(f"Retrying write (attempt {retry_count + 1})")
                    else:
                        # Move to DLQ
                        await self._write_to_dlq(entry, str(e))
                        
                        result = WriteResult(
                            success=False,
                            error=str(e),
                            retry_count=retry_count
                        )
                        future.set_result(result)
                        
                        self._failed_writes += 1
            
            # Update last hash
            self._last_hash = prev_hash
            self._total_batches += 1
        
        log.debug(f"Batch write complete (hash={prev_hash[:8]}...)")
    
    def _sync_write(self, entry_dict: Dict[str, Any], entry_hash: str) -> None:
        """Synchronous write wrapper for thread pool"""
        # Convert dict back to LedgerEntry for modern backend API
        from mahoun.ledger.models import LedgerEntry
        from datetime import datetime, timezone
        
        entry = LedgerEntry(
            verdict_id=entry_dict.get("verdict_id", ""),
            case_id=entry_dict.get("case_id", ""),
            referenced_ltm_nodes=entry_dict.get("referenced_ltm_nodes", []),
            referenced_facts=entry_dict.get("referenced_facts", []),
            confidence=entry_dict.get("confidence", 1.0),
            invariant_version=entry_dict.get("invariant_version", "1.0"),
            guard_mode=entry_dict.get("guard_mode", "OFF"),
            created_at=datetime.fromisoformat(entry_dict["created_at"]) if isinstance(entry_dict.get("created_at"), str) else entry_dict.get("created_at", datetime.now(timezone.utc)),
            request_id=entry_dict.get("request_id", "")
        )
        
        # Modern backend API: write(entry, entry_hash, prev_hash)
        prev_hash = self.backend.get_last_hash()
        self.backend.write(entry, entry_hash, prev_hash)
    
    def _entry_to_dict(self, entry: LedgerEntry) -> Dict[str, Any]:
        """Convert entry to dict"""
        return {
            "verdict_id": entry.verdict_id,
            "case_id": entry.case_id,
            "referenced_ltm_nodes": entry.referenced_ltm_nodes,
            "referenced_facts": entry.referenced_facts,
            "confidence": entry.confidence,
            "invariant_version": entry.invariant_version,
            "guard_mode": entry.guard_mode,
            "created_at": entry.created_at.isoformat() if isinstance(entry.created_at, datetime) else entry.created_at,
            "request_id": entry.request_id
        }
    
    def _compute_hash(self, entry_dict: Dict[str, Any], prev_hash: str) -> str:
        """Compute hash for entry"""
        content = json.dumps(entry_dict, default=str, sort_keys=True)
        return hashlib.sha256(f"{prev_hash}:{content}".encode()).hexdigest()
    
    async def _write_to_dlq(self, entry: LedgerEntry, error: str) -> None:
        """Write failed entry to dead letter queue"""
        try:
            dlq_file = self.dlq_path / f"dlq_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{entry.verdict_id}.json"
            
            dlq_entry = {
                "entry": self._entry_to_dict(entry),
                "error": error,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "retry_count": getattr(entry, "_retry_count", 0)
            }
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._write_dlq_file,
                dlq_file,
                dlq_entry
            )
            
            self._dlq_writes += 1
            log.warning(f"Entry moved to DLQ: {dlq_file}")
            
        except Exception as e:
            log.error(f"Failed to write to DLQ: {e}")
    
    def _write_dlq_file(self, path: Path, data: Dict[str, Any]) -> None:
        """Write DLQ file (sync)"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _flush_queue(self, timeout: float = 30.0) -> None:
        """Flush remaining entries in queue"""
        log.info("Flushing remaining entries...")
        
        batch: List[Tuple[LedgerEntry, asyncio.Future]] = []
        
        try:
            while not self._write_queue.empty():
                try:
                    entry, future = await asyncio.wait_for(
                        self._write_queue.get(),
                        timeout=0.1
                    )
                    batch.append((entry, future))
                    
                    if len(batch) >= self.batch_size:
                        await self._write_batch(batch)
                        batch = []
                        
                except asyncio.TimeoutError:
                    break
            
            # Write remaining
            if batch:
                await self._write_batch(batch)
                
        except Exception as e:
            log.error(f"Flush error: {e}")
        
        log.info(f"Flush complete ({len(batch)} entries)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get writer statistics"""
        return {
            "total_writes": self._total_writes,
            "successful_writes": self._successful_writes,
            "failed_writes": self._failed_writes,
            "dlq_writes": self._dlq_writes,
            "total_batches": self._total_batches,
            "queue_size": self._write_queue.qsize(),
            "success_rate": (
                self._successful_writes / self._total_writes
                if self._total_writes > 0 else 0.0
            )
        }
