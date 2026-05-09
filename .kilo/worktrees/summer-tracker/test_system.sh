#!/bin/bash
# Quick System Test Wrapper
# Runs the system test with proper environment setup

set -e

echo "🔧 Setting up environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -e ."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Run test
echo ""
echo "🚀 Running system test..."
python3 scripts/quick_system_test.py "$@"
