# Neural-Link Audit Report: Hardened OCR ↔ Reasoning/Inference Engine Integration

## 1. Ingestion Gateway
- **File**: `/home/haji/Desktop/Platform/mahoun/pipelines/ingestion/hardened_paddle_ocr.py`
- **Function**: `_create_truth_trace_segment()` (lines 403‑453)
- **Signature**: `def _create_truth_trace_segment(..., is_handwritten: bool = False, table_json_structure: Optional[str] = None, semantic_weight: float = 1.0)`

## 2. Semantic Weight Utilization
- **File**: same as above
- **Logic**: `semantic_weight` is set per-element type:
  - Handwritten: `1.5` (lines 721‑722)
  - Table: `2.0` (lines 709‑710)
  - Stamp/Signature: `1.8` (lines 738‑739)
  - Default: `1.0` (line 741)
- **Usage**: Passed to `TruthTraceSegment` and propagated to UI/reasoning layers for priority/score calculations.

## 3. Handwritten Logic Branching
- **File**: `hardened_paddle_ocr.py`
- **Method**: `_process_with_paddlex()` (lines 610‑797)
- **Condition**: `elem_type == 'handwritten'` → `is_handwritten=True`, `semantic_weight=1.5` (lines 717‑728)
- **UI Flag**: `is_handwritten` field in each `TruthTraceSegment` for downstream legal‑priority handling.

## 4. Table Determinism in Prompting
- **File**: `hardened_paddle_ocr.py`
- **Method**: `_process_with_paddlex()` (lines 610‑797)
- **Output**: `table_json_structure` populated with deterministic Markdown from `TableMaster` (lines 701‑707)
- **Merkle Assurance**: Table Markdown objects are independently hashed and added to the Merkle tree (lines 890‑898) preserving source‑of‑truth integrity during reasoning.

## 5. Feedback Loop (Rescan on Ambiguity)
- **Detection**: Legal‑keyword confidence check in `ocr_image_hardened()` (lines 934‑941)
- **Action**: If critical keyword confidence < `legal_keyword_threshold`, a `SecurityConstraintError` is raised, triggering upstream retry logic (not shown) that can request a re‑scan with adjusted OCR thresholds.
- **Upstream Hook**: The raised exception can be caught by calling code to invoke a rescan with modified parameters.

## 6. Invariants Preventing Hallucination
- **Merkle Anchoring**: Each `TruthTraceSegment` includes `merkle_leaf_link` (line 430) that is added to the document‑wide Merkle tree, making any post‑generation alteration detectable.
- **Legal‑Keyword Validation**: Confidence boosting only increases weighted confidence for known legal terms; low confidence on these terms triggers failures (lines 935‑941).
- **Atomic Checkpointing**: Checkpoints store Merkle leaves and truth‑trace segments atomically (lines 455‑490), ensuring the reasoning engine always works from a verified state.

*All identified bridge locations are within `hardened_paddle_ocr.py`; no additional files were required.*