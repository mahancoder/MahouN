#!/bin/bash
#
# Gate 1: Format/Lint
# ===================
# Enforces code style with ruff
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "🎨 Gate 1: Format/Lint Check"
echo "================================================"
echo ""

cd "$PROJECT_ROOT"

# Check if ruff is installed
if ! command -v ruff &> /dev/null; then
    echo -e "${RED}❌ ruff not found. Installing...${NC}"
    pip install ruff
fi

echo "📋 Running ruff check..."
echo ""

# Run ruff check
if ruff check . --select E,F,I,UP,N,W --output-format=github; then
    echo -e "${GREEN}✓ Lint check passed${NC}"
    LINT_PASSED=true
else
    echo -e "${RED}❌ Lint check failed${NC}"
    LINT_PASSED=false
fi

echo ""
echo "📝 Running ruff format check..."
echo ""

# Check formatting
if ruff format --check .; then
    echo -e "${GREEN}✓ Format check passed${NC}"
    FORMAT_PASSED=true
else
    echo -e "${RED}❌ Format check failed${NC}"
    echo ""
    echo "Run this to fix:"
    echo "  ruff format ."
    FORMAT_PASSED=false
fi

echo ""
echo "================================================"

if [ "$LINT_PASSED" = true ] && [ "$FORMAT_PASSED" = true ]; then
    echo -e "${GREEN}✅ Gate 1: PASSED${NC}"
    echo "Code style is compliant."
    exit 0
else
    echo -e "${RED}❌ Gate 1: FAILED${NC}"
    echo ""
    echo "To fix issues:"
    echo "  ruff check --fix ."
    echo "  ruff format ."
    exit 1
fi






