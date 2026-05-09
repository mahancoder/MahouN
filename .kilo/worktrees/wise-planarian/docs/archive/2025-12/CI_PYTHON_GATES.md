# Python-Based CI Gates

## Overview

The MAHOUN Heavy Lock now has **Python-based gate scripts** for better portability and sophistication.

## 🐍 Python Scripts

### Individual Scanners

```bash
# Gate 0a: Placeholder scanner
python3 scripts/ci_scan_placeholders.py

# Gate 0b: Secrets scanner
python3 scripts/ci_scan_secrets.py

# Gate 6: Reality report generator
python3 scripts/ci_make_reality_report.py
```

### Unified Runner

```bash
# Run all gates (Python-based)
python3 scripts/ci_run_gates.py
```

## 📋 Complete Gate Pipeline

```bash
# Gate 0: Repo integrity
python scripts/ci_scan_placeholders.py
python scripts/ci_scan_secrets.py

# Gate 1: Lint/format
ruff check .
ruff format --check .

# Gate 2: Type safety
basedpyright
# or: pyright
# or: mypy mahoun/ output/ api/ --config-file=mypy.ini

# Gate 3+4+5: Tests (run twice for determinism)
pytest first_step_ci_cd/ -q --junitxml=artifacts/junit.xml
pytest first_step_ci_cd/ -q --junitxml=artifacts/junit_rerun.xml

# Gate 6: Generate artifacts
python scripts/ci_make_reality_report.py
```

## ✨ Features

### ci_scan_placeholders.py
- Detects `pass` statements
- Finds `TODO`/`FIXME` comments
- Identifies `NotImplementedError` stubs
- Checks for empty returns
- Supports `--verbose` flag
- Exit codes: 0 (pass), 1 (fail)

**Example:**
```bash
python3 scripts/ci_scan_placeholders.py --verbose
```

### ci_scan_secrets.py
- AWS keys (AKIA...)
- Private keys (-----BEGIN...)
- Hardcoded passwords
- API keys and tokens
- Stripe/GitHub/GitLab tokens
- Google API keys
- Slack webhooks
- Redacts secrets in output
- Exit codes: 0 (pass), 1 (warning), 2 (critical)

**Example:**
```bash
python3 scripts/ci_scan_secrets.py --fail-on-medium
```

### ci_make_reality_report.py
- Generates `reality_report.json`
- Creates `ci_summary.md`
- Parses JUnit XML
- Git metadata
- Environment info
- Dependency hash
- Determinism check

**Output:**
- `artifacts/reality_report.json` - Machine-readable
- `artifacts/ci_summary.md` - Human-readable

### ci_run_gates.py
- Runs all gates in sequence
- Stops on first failure
- Colored output
- Duration tracking
- Final summary
- Exit code: 0 (all pass), 1 (any fail)

## 🚀 Quick Start

### Option 1: Python Runner (Recommended)
```bash
python3 scripts/ci_run_gates.py
```

### Option 2: Bash Runner
```bash
./scripts/ci_run_first_step.sh
```

### Option 3: Make Target
```bash
make ci-first-step
```

### Option 4: Individual Gates
```bash
# Just check for placeholders
python3 scripts/ci_scan_placeholders.py

# Just check for secrets
python3 scripts/ci_scan_secrets.py

# Just generate report
python3 scripts/ci_make_reality_report.py
```

## 📊 Output Examples

### Placeholder Scanner
```
============================================================
🔍 Gate 0a: Placeholder Pattern Scanner
============================================================

mahoun/agents/base_agent.py:
  ERROR Line 311: Standalone pass statement (likely placeholder)
    pass

============================================================
📊 Summary
============================================================
Files scanned: 45
Total issues: 52
  Critical: 0
  Errors: 52
  Warnings: 0

❌ FAILED: Found placeholder patterns
```

### Secrets Scanner
```
============================================================
🔐 Gate 0b: Secrets Scanner
============================================================

🔍 Scanning for secrets and sensitive data...

✅ PASSED: No secrets detected
```

### Reality Report
```
============================================================
📦 Gate 6: Reality Report Generator
============================================================

📊 Generating reality report...
✓ Generated: artifacts/reality_report.json
✓ Generated: artifacts/ci_summary.md

📦 Artifacts created:
  - ci_summary.md (1,234 bytes)
  - junit.xml (45,678 bytes)
  - junit_rerun.xml (45,680 bytes)
  - reality_report.json (2,345 bytes)

✅ Gate 6: PASSED
```

## 🔧 Configuration

### Placeholder Patterns
Edit `scripts/ci_scan_placeholders.py`:
```python
PLACEHOLDER_PATTERNS = [
    (r'^\s+pass\s*$', 'Standalone pass statement', 2),
    # Add more patterns...
]
```

### Secret Patterns
Edit `scripts/ci_scan_secrets.py`:
```python
SECRET_PATTERNS = [
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID', 3),
    # Add more patterns...
]
```

## 🎯 Integration

### GitHub Actions
```yaml
- name: Gate 0: Repo Integrity
  run: |
    python3 scripts/ci_scan_placeholders.py
    python3 scripts/ci_scan_secrets.py

- name: Gate 3-5: Reality Tests
  run: |
    pytest first_step_ci_cd/ -q --junitxml=artifacts/junit.xml
    pytest first_step_ci_cd/ -q --junitxml=artifacts/junit_rerun.xml

- name: Gate 6: Artifacts
  run: python3 scripts/ci_make_reality_report.py
```

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python3 scripts/ci_scan_placeholders.py || exit 1
python3 scripts/ci_scan_secrets.py || exit 1
```

## 📚 See Also

- `CI_LOCK.md` - Complete CI/CD documentation
- `scripts/ci_run_gates.py` - Unified Python runner
- `scripts/ci_run_first_step.sh` - Bash runner (still available)
- `Makefile` - Make targets

## 🎉 Benefits

### Why Python Scripts?

1. **Portable** - Works on any OS with Python 3
2. **Sophisticated** - Better pattern matching and analysis
3. **Readable** - Easier to understand and maintain
4. **Extensible** - Easy to add new checks
5. **Structured** - JSON output for CI integration
6. **Colored Output** - Better UX in terminal

### Both Approaches Available

You can use either:
- **Python scripts** (`scripts/ci_*.py`) - Modern, portable
- **Bash scripts** (`ci/first_step/*.sh`) - Traditional, fast

Both work! Choose what fits your workflow.

