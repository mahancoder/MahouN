#!/bin/bash
set -e

echo "=== Metrics Fixes Commit Script ==="
echo ""

# Check if files exist and have changes
echo "Checking file status..."
git status --short | grep -E "(snapshot|metrics\.py|metrics_migration|test_metrics_full_lifecycle)" || echo "No matching files in git status"

echo ""
echo "Checking if files are tracked..."
git ls-files mahoun/metrics/snapshot.py mahoun/metrics/metrics.py mahoun/infrastructure/observability/metrics_migration.py tests/integration/test_metrics_full_lifecycle.py

echo ""
echo "Checking for uncommitted changes in these files..."
git diff --name-only | grep -E "(snapshot|metrics\.py|metrics_migration|test_metrics_full_lifecycle)" || echo "No uncommitted changes"

echo ""
echo "Checking staged files..."
git diff --cached --name-only

echo ""
echo "=== Attempting to stage files ==="
git add mahoun/metrics/snapshot.py mahoun/metrics/metrics.py mahoun/infrastructure/observability/metrics_migration.py tests/integration/test_metrics_full_lifecycle.py

echo ""
echo "=== Staged files ==="
git diff --cached --name-only

echo ""
echo "=== Committing ==="
git commit -F commit_message.txt

echo ""
echo "=== Done! ==="
git log --oneline -1
