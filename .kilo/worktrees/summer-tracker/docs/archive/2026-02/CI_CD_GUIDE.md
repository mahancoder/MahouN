# CI/CD Pipeline Guide

## Overview

Mahoun Platform uses a comprehensive CI/CD pipeline with multiple workflows for quality assurance, security, and deployment.

## Workflows

### 1. Main CI Pipeline (`.github/workflows/ci.yml`)

**Trigger**: Push/PR to `main`, `develop`, `linking` branches

**Gates (0-8)**:
- **Gate 0**: Repo Integrity - Verifies core paths and no stub code
- **Gate 1**: Format/Lint - Code style with ruff
- **Gate 2**: Type Safety - Type checking with basedpyright/mypy
- **Gate 3**: Phase-1 Reality Tests - Basic functionality tests
- **Gate 4**: Anti-Mock Proof - Ensures real implementations
- **Gate 5**: Determinism Proof - Verifies deterministic behavior
- **Gate 6**: Artifact + Traceability - Proper artifact generation
- **Gate 7**: Architecture Boundaries - Module boundary enforcement
- **Gate 8**: Contract Validation - Interface contract verification

**Duration**: ~15 minutes

**Fail Fast**: Pipeline stops at first failure

### 2. Enterprise Hardening Tests (`.github/workflows/enterprise-tests.yml`)

**Trigger**: 
- Push/PR to main branches
- Nightly at 2 AM UTC
- Manual dispatch

**Test Suites**:
- **Security Module**: Encryption, signing, auth, API keys, prompt defense
- **Concurrency Module**: Deadlock detection, distributed locks
- **Monitoring Module**: Alerting, metrics, health checks
- **Execution Module**: Replay, seed management, execution control
- **Graph Enhancements**: Concurrent builder, semantic search, vector index
- **Async Ledger**: Asynchronous ledger operations
- **LLM Migration**: Router, local driver, import verification
- **OCR Pipeline**: Post-processing, integration tests
- **Frontend Build**: TypeScript compilation, build verification
- **Docker Build**: Image building and smoke tests

**Duration**: ~30 minutes

**Coverage**: Generates HTML coverage reports

### 3. Security Scanning (`.github/workflows/security.yml`)

**Trigger**:
- Push/PR to main branches
- Weekly on Monday at 3 AM UTC
- Manual dispatch

**Scans**:
- **Dependency Scan**: Safety + pip-audit for vulnerabilities
- **Secret Scan**: Gitleaks for exposed secrets
- **Code Scan**: Bandit for security issues
- **Docker Scan**: Trivy for container vulnerabilities
- **License Check**: pip-licenses for compliance

**Duration**: ~20 minutes

**Reports**: Uploaded as artifacts

### 4. Deployment (`.github/workflows/deploy.yml`)

**Trigger**:
- Git tags matching `v*.*.*`
- Manual dispatch with environment selection

**Stages**:
1. **Build & Push**: Docker images to registry
2. **Deploy Staging**: Automatic for all tags
3. **Deploy Production**: Manual approval required

**Environments**:
- Staging: `https://staging.mahoun.ai`
- Production: `https://mahoun.ai`

## Local Development

### Run All Gates Locally

```bash
# Bash version
bash scripts/ci_run_first_step.sh

# Python version (recommended)
python scripts/ci_run_gates.py

# Make command
make ci-first-step
```

### Run Individual Gates

```bash
# Gate 0: Repo Integrity
bash ci/first_step/gate_0_integrity.sh

# Gate 1: Format/Lint
bash ci/first_step/gate_1_lint.sh

# Gate 2: Type Safety
bash ci/first_step/gate_2_types.sh

# Gate 3: Reality Tests
bash ci/first_step/gate_3_reality.sh

# Gate 4: Anti-Mock
bash ci/first_step/gate_4_antimock.sh

# Gate 5: Determinism
bash ci/first_step/gate_5_determinism.sh

# Gate 6: Artifacts
bash ci/first_step/gate_6_artifacts.sh

# Gate 7: Architecture
bash ci/first_step/gate_7_architecture.sh

# Gate 8: Contracts
bash ci/first_step/gate_8_contracts.sh
```

### Run Enterprise Tests

```bash
# All enterprise tests
pytest tests/test_enterprise_hardening_comprehensive.py -v

# Specific modules
pytest tests/test_enterprise_hardening_comprehensive.py::TestSecurityModule -v
pytest tests/test_enterprise_hardening_comprehensive.py::TestConcurrencyModule -v

# Graph enhancements
pytest tests/test_concurrent_graph_comprehensive.py -v
pytest tests/test_semantic_search_comprehensive.py -v
pytest tests/test_vector_index_comprehensive.py -v

# With coverage
pytest tests/test_enterprise_hardening_comprehensive.py --cov=mahoun --cov-report=html
```

### Run Security Scans

```bash
# Dependency scan
pip install safety pip-audit
safety check
pip-audit

# Code scan
pip install bandit[toml]
bandit -r mahoun/ api/

# License check
pip install pip-licenses
pip-licenses --format=markdown
```

### Docker Testing

```bash
# Build and test
make docker-build
make docker-up
make docker-test

# Full stack
make docker-up-full

# Clean up
make docker-down
make docker-clean
```

## Pre-commit Hooks

Install pre-commit hooks to run checks before commits:

```bash
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## Branch Protection Rules

### Main Branch
- Require PR reviews (2 approvals)
- Require status checks to pass:
  - First Step Gates (0-8)
  - Enterprise Hardening Tests
  - Security Scanning
- Require branches to be up to date
- No force pushes
- No deletions

### Develop Branch
- Require PR reviews (1 approval)
- Require status checks to pass:
  - First Step Gates (0-8)
- Allow force pushes (with lease)

### Feature Branches
- No restrictions
- Recommended: Run `make ci-first-step` before pushing

## Deployment Process

### Staging Deployment

1. Merge to `develop` branch
2. Create release candidate tag: `git tag v1.2.3-rc.1`
3. Push tag: `git push origin v1.2.3-rc.1`
4. Automatic deployment to staging
5. Run smoke tests
6. Verify functionality

### Production Deployment

1. Merge `develop` to `main`
2. Create release tag: `git tag v1.2.3`
3. Push tag: `git push origin v1.2.3`
4. Automatic build and staging deployment
5. Manual approval required for production
6. Deployment to production
7. Smoke tests and monitoring

## Troubleshooting

### Gate Failures

See `ci/first_step/TROUBLESHOOTING.md` for common issues and fixes.

### Test Failures

```bash
# Run specific test with verbose output
pytest tests/test_name.py::test_function -vv

# Run with debugging
pytest tests/test_name.py --pdb

# Run with coverage
pytest tests/test_name.py --cov=mahoun --cov-report=term-missing
```

### Docker Issues

```bash
# Check logs
docker compose logs backend
docker compose logs frontend

# Restart services
docker compose restart

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

## Monitoring

### GitHub Actions

- View workflow runs: `https://github.com/hajmamali/Platform/actions`
- Download artifacts from completed runs
- Check job logs for detailed output

### Metrics

- Coverage reports uploaded as artifacts
- Test results in JUnit XML format
- Security scan reports (Bandit, Trivy)
- License compliance reports

## Best Practices

1. **Run CI locally before pushing**
   ```bash
   make ci-first-step
   ```

2. **Keep commits atomic and focused**
   - One logical change per commit
   - Clear commit messages

3. **Write tests for new features**
   - Unit tests for logic
   - Integration tests for workflows
   - Contract tests for interfaces

4. **Update documentation**
   - Code comments
   - API documentation
   - Architecture docs

5. **Security first**
   - No secrets in code
   - Use environment variables
   - Regular dependency updates

6. **Monitor CI performance**
   - Keep gates fast (<15 min total)
   - Parallelize independent tests
   - Cache dependencies

## CI/CD Metrics

### Current Performance

- **Gate 0-8**: ~15 minutes
- **Enterprise Tests**: ~30 minutes
- **Security Scans**: ~20 minutes
- **Docker Build**: ~10 minutes
- **Total CI Time**: ~45 minutes (parallel)

### Success Rates (Target)

- Main CI: >95%
- Enterprise Tests: >90%
- Security Scans: 100% (no critical issues)
- Deployment: >99%

## Future Enhancements

- [ ] Performance benchmarking workflow
- [ ] Automated changelog generation
- [ ] Slack/Discord notifications
- [ ] Deployment rollback automation
- [ ] Canary deployments
- [ ] A/B testing infrastructure
- [ ] Load testing in staging
- [ ] Automated security patching

## Support

For CI/CD issues:
1. Check workflow logs in GitHub Actions
2. Review `ci/first_step/TROUBLESHOOTING.md`
3. Run gates locally for debugging
4. Contact DevOps team

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
