#!/bin/bash
# Run metrics integration tests with proper environment

export MAHOUN_INTEGRATION=1

echo "=================================="
echo "Running Metrics Integration Tests"
echo "=================================="

python -m pytest tests/integration/test_metrics_full_lifecycle.py -v --tb=short -x

echo ""
echo "=================================="
echo "Test run complete"
echo "=================================="
