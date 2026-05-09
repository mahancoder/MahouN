# 🔒 MAHOUN Heavy Lock – Platform Gate

**Version:** 1.0.0  
**Date:** December 26, 2025  
**Status:** 🟢 ACTIVE

---

## 🎯 Mission

Lock the repository to ensure **zero placeholder code reaches main**.

Every PR must pass **6 mandatory gates** before merge. No exceptions.

---

## 📊 Gate Overview

| Gate | Name | Duration | Mandatory | Laptop-Safe |
|------|------|----------|-----------|-------------|
| 0 | Repo Integrity | ~2s | ✅ | ✅ |
| 1 | Format/Lint | ~5s | ✅ | ✅ |
| 2 | Type Safety | ~10s | ✅ | ✅ |
| 3 | Phase-1 Reality Tests | ~30s | ✅ | ✅ |
| 4 | Anti-Mock Proof | ~5s | ✅ | ✅ |
| 5 | Determinism Proof | ~60s | ✅ | ✅ |
| 6 | Artifact + Traceability | ~5s | ✅ | ✅ |
| 7 | Integration Tests | ~5min | ❌ | ❌ |
| 8 | E2E Tests | ~15min | ❌ | ❌ |

**Total for PR:** ~2 minutes (Gates 0-6 only)

---

## 🚪 Gate Descriptions

### Gate 0: Repo Integrity ⚡
**Purpose:** Block placeholder patterns and secrets

**Checks:**
- ❌ `pass` as sole function body in non-test code
- ❌ `TODO` / `FIXME` in core runtime paths
- ❌ `raise NotImplementedError` in non-abstract code
- ❌ `return {}` or `return None` as sole body
- ❌ Secrets patterns (AWS keys, tokens, passwords)

**Paths Checked:**
- `mahoun/` (all Python files)
- `output/` (all Python files)
- `api/` (all Python files)

**Excluded:**
- `tests/`
- `docs/`
- `*.md` files

**Run Locally:**
```bash
./ci/first_step/gate_0_integrity.sh
```

---

### Gate 1: Format/Lint 🎨
**Purpose:** Enforce code style consistency

**Tools:**
- `ruff check` (E, F, I, UP rules minimum)
- `ruff format` (deterministic formatting)

**Configuration:** `pyproject.toml` or `ruff.toml`

**Run Locally:**
```bash
./ci/first_step/gate_1_lint.sh
```

**Auto-fix:**
```bash
ruff check --fix .
ruff format .
```

---

### Gate 2: Type Safety 🔒
**Purpose:** Prevent new type errors

**Tool:** `basedpyright` (strict mode)

**Strategy:**
- Baseline file: `pyright_baseline.json`
- New errors block PR
- Reducing errors is encouraged

**Run Locally:**
```bash
./ci/first_step/gate_2_types.sh
```

---

### Gate 3: Phase-1 Reality Tests 🧪
**Purpose:** Verify real implementation (laptop-safe)

**What Runs:**
```bash
pytest first_step_ci_cd/ -q --tb=short
```

**Constraints:**
- Single worker (no xdist)
- No external services
- < 100 MB memory
- < 60 seconds timeout

**137 Tests:**
- 18 Import tests
- 33 Structure tests
- 29 Contract tests
- 27 Light logic tests
- 30 Anti-mock tests

**Run Locally:**
```bash
./ci/first_step/gate_3_reality.sh
```

---

### Gate 4: Anti-Mock Proof 🔍
**Purpose:** Prove implementations are not stubs

**Checks:**
- Run `first_step_ci_cd/test_5_anti_mock.py`
- Verify critical modules meet minimum line counts
- Fail if modules shrink without approval

**Thresholds:**
- `mahoun/agents/base_agent.py`: min 500 lines
- `mahoun/agents/claim_agent.py`: min 400 lines
- `mahoun/reasoning/ultra_reasoning_service.py`: min 300 lines
- (configurable in `ci/first_step/complexity_thresholds.json`)

**Run Locally:**
```bash
./ci/first_step/gate_4_antimock.sh
```

---

### Gate 5: Determinism Proof 🎲
**Purpose:** Ensure tests are deterministic

**Method:**
1. Run Gate 3 tests → capture hash of results
2. Run Gate 3 tests again → capture hash
3. Compare hashes
4. **Fail if different**

**Why:** Non-deterministic tests are unreliable

**Run Locally:**
```bash
./ci/first_step/gate_5_determinism.sh
```

---

### Gate 6: Artifact + Traceability 📦
**Purpose:** Track every CI run

**Artifacts Generated:**
- `junit.xml` - Test results
- `ci_summary.md` - Human-readable summary
- `reality_report.json` - Machine-readable metadata

**reality_report.json Structure:**
```json
{
  "commit_sha": "abc123...",
  "branch": "feature/xyz",
  "python_version": "3.12.3",
  "timestamp": "2025-12-26T18:00:00Z",
  "gates": {
    "gate_0": {"passed": true, "duration_s": 2.1},
    "gate_1": {"passed": true, "duration_s": 4.8},
    "gate_2": {"passed": true, "duration_s": 9.2},
    "gate_3": {"passed": true, "duration_s": 27.3, "tests": 137},
    "gate_4": {"passed": true, "duration_s": 3.1},
    "gate_5": {"passed": true, "duration_s": 54.6},
    "gate_6": {"passed": true, "duration_s": 1.2}
  },
  "total_duration_s": 102.3,
  "status": "PASS"
}
```

**Run Locally:**
```bash
./ci/first_step/gate_6_artifacts.sh
```

---

## 🚀 Running Locally

### Quick Check (All Gates 0-6)
```bash
make ci-first-step
```
or
```bash
./scripts/ci_run_first_step.sh
```

**Expected Duration:** ~2 minutes

### Individual Gates
```bash
# Gate 0: Repo Integrity
./ci/first_step/gate_0_integrity.sh

# Gate 1: Format/Lint
./ci/first_step/gate_1_lint.sh

# Gate 2: Type Safety
./ci/first_step/gate_2_types.sh

# Gate 3: Reality Tests
./ci/first_step/gate_3_reality.sh

# Gate 4: Anti-Mock
./ci/first_step/gate_4_antimock.sh

# Gate 5: Determinism
./ci/first_step/gate_5_determinism.sh

# Gate 6: Artifacts
./ci/first_step/gate_6_artifacts.sh
```

### Auto-fix Issues
```bash
# Fix formatting
make lint-fix

# Fix imports
ruff check --fix --select I .
```

---

## 🔧 CI/CD Setup

### GitHub Actions

Located at: `.github/workflows/ci.yml`

**Triggers:**
- Every push to PR
- Every push to `main`
- Manual trigger (workflow_dispatch)

**Environment:**
- Ubuntu Latest
- Python 3.12
- 2 CPU cores, 7GB RAM (GitHub free tier)

**Status Checks:**
All 6 gates must pass before merge.

### GitLab CI (Alternative)

Located at: `.gitlab-ci.yml`

Same gate structure, different syntax.

---

## 🔐 Merge Policy

**Enforced in Repository Settings:**

✅ **Required Status Checks:**
- `gate-0-integrity`
- `gate-1-lint`
- `gate-2-types`
- `gate-3-reality`
- `gate-4-antimock`
- `gate-5-determinism`
- `gate-6-artifacts`

✅ **Required Reviews:** ≥ 1 approval

✅ **Restrictions:**
- No force-push to `main`
- No merge if "changes requested"
- Require branches to be up to date

❌ **Optional (Max Hardening):**
- Require signed commits
- Require linear history

---

## 📋 Pre-commit Hooks

**Installed via:** `.pre-commit-config.yaml`

**Hooks:**
1. Trailing whitespace removal
2. YAML validation
3. Ruff format + check
4. Type check (fast mode)

**Install:**
```bash
pip install pre-commit
pre-commit install
```

**Run Manually:**
```bash
pre-commit run --all-files
```

---

## 🎯 Optional Gates (Not Default)

### Gate 7: Integration Tests (Phase-2)
**Trigger:** Manual or nightly

**Requirements:**
- Docker Compose
- 8GB+ RAM
- Network access

**What Runs:**
```bash
pytest tests/ -m integration --timeout=300
```

**Enable:**
```bash
CI_ENABLE_INTEGRATION=1 ./scripts/ci_run_all.sh
```

---

### Gate 8: E2E Tests (Phase-3)
**Trigger:** Manual or nightly on powerful runner

**Requirements:**
- 16GB+ RAM
- 4+ CPU cores
- Real services (Neo4j, Redis, etc.)

**What Runs:**
```bash
pytest tests/ -m e2e --timeout=900
```

**Enable:**
```bash
CI_ENABLE_E2E=1 ./scripts/ci_run_all.sh
```

---

## 📊 Monitoring & Metrics

### CI Dashboard
- Average gate duration (per gate)
- Pass/fail rates
- Most common failures
- Flaky test detection

### Alerts
- Gate duration > 2x baseline → investigate
- Determinism failures → critical
- Repo integrity failures → block immediately

---

## 🚨 Troubleshooting

### "Gate 0 failed: placeholder detected"
**Fix:** Remove `pass`, `TODO`, or `raise NotImplementedError` from indicated file.

### "Gate 1 failed: formatting issues"
**Fix:** Run `ruff format .` and commit changes.

### "Gate 2 failed: new type errors"
**Fix:** Add type hints or fix type issues. Update baseline if intentional.

### "Gate 3 failed: tests failing"
**Fix:** Run `pytest first_step_ci_cd/ -v` locally to debug.

### "Gate 5 failed: non-deterministic tests"
**Fix:** Investigate test that uses randomness, time, or network. Mock properly.

### "CI too slow"
**Check:** Are you running optional gates by accident?

---

## 📚 Documentation

- `ci/first_step/README.md` - Gate implementation details
- `first_step_ci_cd/README.md` - Test suite documentation
- `.github/workflows/README.md` - CI workflow documentation

---

## 🎓 Philosophy

### Why So Strict?

1. **Placeholder code is a lie** - It claims features exist when they don't.
2. **Type safety prevents runtime errors** - Catch bugs at compile time.
3. **Deterministic tests are reliable** - Flaky tests waste time.
4. **Anti-mock proves reality** - Ensures implementations aren't stubs.

### Why Laptop-Safe?

- Developers should run full CI locally
- Fast feedback loop (< 2 minutes)
- No "works on CI but not locally" issues

### Why Mandatory?

- Every merged PR affects everyone
- One bad merge can break main for hours
- Prevention is cheaper than fixing

---

## 🔄 Maintenance

### Weekly
- Review gate durations
- Check for flaky tests
- Update baselines if needed

### Monthly
- Review complexity thresholds
- Update dependencies
- Audit secrets patterns

### Quarterly
- Review gate effectiveness
- Add new gates if needed
- Retire ineffective gates

---

## 📞 Support

**Issues with CI?**
1. Check this document first
2. Run gates locally to reproduce
3. Ask in #ci-cd channel
4. Tag @platform-team if urgent

**Want to add a gate?**
1. Propose in RFC
2. Implement in `ci/first_step/`
3. Test thoroughly
4. Update this document
5. Get approval from 2+ reviewers

---

## 📜 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-26 | Initial heavy lock implementation |

---

**🔒 Lock Status: ACTIVE**

**Last Updated:** December 26, 2025  
**Maintained By:** MAHOUN Platform Team

