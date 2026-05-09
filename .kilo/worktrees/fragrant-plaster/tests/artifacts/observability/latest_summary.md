# Observability Summary - 20251221_060200

**Run ID:** `fea85d6d`
**Duration:** 3.51s

## Invariants Status
| Invariant | Status | Message |
|-----------|--------|---------|
| No Masking (Postgres) | ❌ FAIL | Postgres marked healthy despite being disabled! |
| Explicit Fallback | ✅ PASS | Fallback usage: False |

## Component Status Table
| Component | Healthy | Status |
|-----------|---------|--------|

## Output Preview
```json
{
  "success": true,
  "workflow_id": "563d28b6",
  "dag_name": "observability_test_workflow",
  "duration_seconds": 3.5056138038635254,
  "node_results": {
    "parsing": {
      "doc_id": "fallback_1766284324",
      "verdict_struct": {
        "case_meta": {
          "case_number": "fallback_1766284324"
        },
        "sections": {
          "verdict": "قرارداد شماره ۱۲۳: مبلغ ۵۰۰ میلیون تومان پرداخت نشده است."
        },
        "parties": {},
        "_fallback_mode": true,
        "_parsing_quality": {
          "completeness": 0.3
        }
      },
      "entities": {},
      "chunks": [
        {
          "text": "قرارداد شماره ۱۲۳: مبلغ ۵۰۰ میلیون تومان پرداخت نشده است.",
          "index": 0,
          "metadata": {
            "fallback": true
          }
        }
      ],
      "chunks_count": 1,
      "storage_result": null,
      "quality_metrics": {
        "fallback_used": true,
        "completeness": 0.3
      },
      "fallback_used": true
    },
    "dispute... [TRUNCATED]
```
