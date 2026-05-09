# Evidence Ledger Failure Modes
================================

This document describes what happens if Evidence Ledger invariants are violated.
These are NOT hypothetical scenarios - they are real risks that must be prevented.

## EL-I3 Violation: Ledger Write Does Not Block Verdict

**What happens:** Verdicts are published even when ledger write fails.

**Consequence:** The system produces legal decisions without audit trail. There is no way to verify what evidence supported a verdict. Removing evidence does not invalidate verdicts. The system becomes a black box that cannot be trusted for legal accountability.

**Detection:** Look for verdicts generated despite ledger exceptions. Check logs for "Ledger write failed" messages that do not prevent verdict return.

**Recovery:** Immediate system shutdown. All verdicts since violation must be invalidated.

## EL-I1 Violation: Verdicts Without Evidence References

**What happens:** Ledger entries are created with empty referenced_ltm_nodes and referenced_facts.

**Consequence:** Verdicts appear to have evidence but actually have none. The audit trail shows references that don't exist. Future evidence removal cannot invalidate these verdicts, creating persistent false conclusions.

**Detection:** Query ledger for entries where both reference lists are empty. Check validate_entry() bypass attempts.

**Recovery:** Delete all affected verdicts. Re-run cases with proper evidence collection.

## EL-I2 Violation: Reasoning Artifacts in Ledger

**What happens:** Ledger stores reasoning steps, graph edges, or inference paths.

**Consequence:** The ledger becomes a reasoning trace, violating separation of concerns. Internal inference details are exposed. The system can be reverse-engineered to manipulate verdicts.

**Detection:** Inspect ledger entries for non-reference data. Check storage implementations for additional fields.

**Recovery:** Wipe ledger. Implement new storage that strictly validates entry structure.

## EL-I4 Violation: Mutable Ledger Entries

**What happens:** Ledger entries can be modified after writing.

**Consequence:** Audit trail becomes unreliable. Evidence can be added/removed post-verdict. Verdicts can be retroactively "supported" by fake evidence.

**Detection:** Attempt to modify frozen dataclass fields. Check storage for update operations.

**Recovery:** Immediate audit of all entries. Re-implement with immutable storage.

## EL-I5 Violation: Excluded Nodes in References

**What happens:** Defeated or excluded nodes appear in ledger references.

**Consequence:** Contradiction resolution is bypassed. Invalid evidence supports verdicts. Logically inconsistent legal conclusions are possible.

**Detection:** Cross-reference ledger entries with guardrails exclusion lists. Check for nodes marked as excluded.

**Recovery:** Invalidate verdicts containing excluded references. Fix evidence collection logic.

## EL-I6 Violation: Insufficient References for Audit

**What happens:** Ledger lacks enough references to invalidate verdicts when evidence is removed.

**Consequence:** Evidence removal does not trigger verdict invalidation. Stale verdicts persist despite lost foundation. The audit becomes incomplete.

**Detection:** Remove evidence nodes and check if dependent verdicts are invalidated. Verify reference completeness.

**Recovery:** Enhance reference collection. Implement dependency tracking.

## Complete Ledger Removal

**What happens:** Evidence Ledger is disabled or removed entirely.

**Consequence:** The system becomes non-auditable. All verdicts are published without evidence trail. There is no way to verify decision validity. The system cannot be used for legal purposes requiring accountability.

**Detection:** Absence of ledger writes in logs. Verdicts generated without ledger integration.

**Recovery:** Restore ledger immediately. All verdicts since removal are invalid.

---

**WARNING TO FUTURE ENGINEERS:**

If you are considering modifying or removing any part of the Evidence Ledger:

STOP. This is not a performance optimization. This is not "unnecessary complexity."

The Evidence Ledger is the only thing preventing this system from producing unauditable, unaccountable legal hallucinations.

Violating these invariants turns MAHOUN into a dangerous toy, not a legal AI.