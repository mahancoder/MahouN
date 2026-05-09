#!/bin/bash
echo "Running monitoring tests..."
python -m pytest tests/test_ultra_legal_monitoring.py tests/test_monitoring_unification_strict.py -v --tb=short 2>&1 | tee test_results.txt
echo ""
echo "Test summary:"
grep -E "(PASSED|FAILED|ERROR)" test_results.txt | tail -20
