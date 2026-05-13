#!/bin/bash
# ============================================================================
# MAHOUN Platform - Pre-Commit Security Audit
# ============================================================================
# PURPOSE: Detect sensitive data before it reaches the repository
# CLASSIFICATION: CRITICAL SECURITY CONTROL
# ============================================================================

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🔒 MAHOUN Security Audit - Pre-Commit Check"
echo "============================================"

VIOLATIONS=0

# ============================================================================
# 1. CHECK FOR ENVIRONMENT FILES
# ============================================================================
echo -e "\n📋 Checking for environment files..."
if git diff --cached --name-only | grep -E '\.env$|\.env\..*' | grep -v '\.env\.example' | grep -v '\.env\.backend\.example'; then
    echo -e "${RED}❌ VIOLATION: Environment files detected${NC}"
    echo "   These files may contain secrets and should never be committed."
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo -e "${GREEN}✓ No environment files detected${NC}"
fi

# ============================================================================
# 2. CHECK FOR API KEYS & TOKENS
# ============================================================================
echo -e "\n🔑 Checking for API keys and tokens..."
if git diff --cached --name-only | grep -iE 'api_key|token|secret|password|credential'; then
    echo -e "${YELLOW}⚠️  WARNING: Files with sensitive names detected${NC}"
    echo "   Please verify these files don't contain actual secrets."
    git diff --cached --name-only | grep -iE 'api_key|token|secret|password|credential'
fi

# ============================================================================
# 3. CHECK FOR PRIVATE KEYS
# ============================================================================
echo -e "\n🔐 Checking for private keys..."
if git diff --cached --name-only | grep -E '\.key$|\.pem$|\.p12$|\.pfx$|id_rsa|id_dsa|id_ecdsa'; then
    echo -e "${RED}❌ VIOLATION: Private key files detected${NC}"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo -e "${GREEN}✓ No private keys detected${NC}"
fi

# ============================================================================
# 4. CHECK FOR DATABASE FILES
# ============================================================================
echo -e "\n💾 Checking for database files..."
if git diff --cached --name-only | grep -E '\.sqlite$|\.sqlite3$|\.db$'; then
    echo -e "${YELLOW}⚠️  WARNING: Database files detected${NC}"
    echo "   Database files should typically not be committed."
fi

# ============================================================================
# 5. SCAN FILE CONTENTS FOR SECRETS
# ============================================================================
echo -e "\n🔍 Scanning file contents for potential secrets..."

# Patterns that might indicate secrets
SECRET_PATTERNS=(
    "api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}"
    "secret[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}"
    "password['\"]?\s*[:=]\s*['\"][^'\"]{8,}"
    "token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}"
    "-----BEGIN (RSA |DSA )?PRIVATE KEY-----"
    "aws_access_key_id"
    "aws_secret_access_key"
    "AKIA[0-9A-Z]{16}"
    "sk-[a-zA-Z0-9]{20,}"
    "ghp_[a-zA-Z0-9]{36}"
    "glpat-[a-zA-Z0-9_-]{20,}"
)

for pattern in "${SECRET_PATTERNS[@]}"; do
    if git diff --cached | grep -iE "$pattern" > /dev/null; then
        echo -e "${RED}❌ VIOLATION: Potential secret detected matching pattern: $pattern${NC}"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [ $VIOLATIONS -eq 0 ]; then
    echo -e "${GREEN}✓ No secrets detected in file contents${NC}"
fi

# ============================================================================
# 6. CHECK FOR LARGE FILES
# ============================================================================
echo -e "\n📦 Checking for large files..."
LARGE_FILES=$(git diff --cached --name-only | while read file; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
        if [ "$size" -gt 10485760 ]; then  # 10MB
            echo "$file ($((size / 1048576))MB)"
        fi
    fi
done)

if [ -n "$LARGE_FILES" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Large files detected (>10MB):${NC}"
    echo "$LARGE_FILES"
    echo "   Consider using Git LFS or excluding these files."
fi

# ============================================================================
# 7. CHECK FOR PROPRIETARY MARKERS
# ============================================================================
echo -e "\n🏢 Checking for proprietary/confidential markers..."
if git diff --cached | grep -iE 'PROPRIETARY|CONFIDENTIAL|INTERNAL ONLY|DO NOT DISTRIBUTE'; then
    echo -e "${RED}❌ VIOLATION: Proprietary/confidential markers detected${NC}"
    echo "   Files marked as proprietary should not be in public repository."
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo -e "${GREEN}✓ No proprietary markers detected${NC}"
fi

# ============================================================================
# FINAL VERDICT
# ============================================================================
echo -e "\n============================================"
if [ $VIOLATIONS -gt 0 ]; then
    echo -e "${RED}❌ SECURITY AUDIT FAILED${NC}"
    echo -e "${RED}   $VIOLATIONS critical violation(s) detected${NC}"
    echo -e "\n${YELLOW}To bypass this check (NOT RECOMMENDED):${NC}"
    echo -e "   git commit --no-verify"
    exit 1
else
    echo -e "${GREEN}✅ SECURITY AUDIT PASSED${NC}"
    echo -e "${GREEN}   No critical violations detected${NC}"
    exit 0
fi
