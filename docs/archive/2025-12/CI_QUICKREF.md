# 🔒 MAHOUN Heavy Lock - Quick Reference

> **5-Second Version:** Run `make ci-first-step` before every commit

---

## ⚡ Common Commands

```bash
# Run all gates (Python, recommended)
make ci-first-step

# Run all gates (Bash)
make ci-first-step-bash

# Run just tests
make test

# Fix code style
make lint-fix

# Quick sanity check (Gates 0-1 only)
make sanity
```

---

## 🐍 Python Scripts

```bash
# Check for placeholders
python3 scripts/ci_scan_placeholders.py

# Check for secrets
python3 scripts/ci_scan_secrets.py

# Generate report
python3 scripts/ci_make_reality_report.py

# Run all gates
python3 scripts/ci_run_gates.py
```

---

## 🚪 Individual Gates (Bash)

```bash
./ci/first_step/gate_0_integrity.sh    # Repo integrity
./ci/first_step/gate_1_lint.sh         # Format/lint
./ci/first_step/gate_2_types.sh        # Type safety
./ci/first_step/gate_3_reality.sh      # Reality tests
./ci/first_step/gate_4_antimock.sh     # Anti-mock
./ci/first_step/gate_5_determinism.sh  # Determinism
./ci/first_step/gate_6_artifacts.sh    # Artifacts
```

---

## 📋 Manual Pipeline

```bash
# Gate 0
python3 scripts/ci_scan_placeholders.py
python3 scripts/ci_scan_secrets.py

# Gate 1
ruff check .
ruff format --check .

# Gate 2
basedpyright

# Gate 3-5
pytest first_step_ci_cd/ -q --junit-xml=artifacts/junit.xml
pytest first_step_ci_cd/ -q --junit-xml=artifacts/junit_rerun.xml

# Gate 6
python3 scripts/ci_make_reality_report.py
```

---

## 🛠️ Development

```bash
# First time setup
make install-dev
pre-commit install

# Before committing
make ci-first-step

# Auto-fix issues
ruff check --fix .
ruff format .
```

---

## 📖 Documentation

- **CI_COMPLETE_GUIDE.md** ← Start here (complete overview)
- **CI_LOCK.md** ← Detailed policies
- **CI_PYTHON_GATES.md** ← Python scripts guide
- **CI_QUICKREF.md** ← This file (quick commands)

---

## 🎯 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All gates passed |
| 1 | Gate failure |
| 2 | Critical issue (e.g., secrets detected) |

---

## ⚠️ Current Known Issues

```bash
# See placeholders (48+ in legacy code)
python3 scripts/ci_scan_placeholders.py
```

**Action:** Fix these before gates will pass

---

## 🚀 Quick Fixes

```bash
# Code style issues
ruff check --fix .
ruff format .

# Run tests to see what's failing
pytest first_step_ci_cd/ -v

# See what's blocking you
make ci-first-step 2>&1 | grep "FAILED"
```

---

## 💡 Tips

- Use `make ci-first-step` (fast, Python-based)
- Use `-v` flag on pytest for verbose test output
- Check `artifacts/` folder for generated reports
- Pre-commit hooks run automatically after installation

---

**Version:** 2.0  
**Last Updated:** December 26, 2025

