#!/usr/bin/env bash
# Enhanced commit-msg hook - GitHub Actions functionality integrated
# File: scripts/local-ci/enhanced_commit_msg.sh

set -euo pipefail

COMMIT_MSG_FILE="$1"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "📝 Enhanced commit-msg validation starting..."

# 1. Standard commit message validation (existing behavior)
# This should be called first to maintain compatibility

# 2. Three-commit cycle validation
echo "🔄 Three-commit cycle validation..."
if [ -f "scripts/tools/three_commit_validator.py" ]; then
    python3 scripts/tools/three_commit_validator.py --commit-msg-file="$COMMIT_MSG_FILE" || {
        echo "❌ Three-commit cycle validation failed"
        echo "💡 Ensure commits follow RED → GREEN → REFACTOR pattern"
        exit 1
    }
else
    echo "⚠️ Three-commit validator not found"
fi

# 3. Commit message format validation
echo "📏 Commit message format validation..."
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Check for conventional commit format
if ! echo "$COMMIT_MSG" | grep -qE '^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+'; then
    echo "⚠️ Commit message doesn't follow conventional commit format"
    echo "💡 Recommended format: type(scope): description"
    echo "💡 Types: feat, fix, docs, style, refactor, test, chore"
fi

# Check minimum length
if [ ${#COMMIT_MSG} -lt 10 ]; then
    echo "❌ Commit message too short (minimum 10 characters)"
    exit 1
fi

echo "✅ Commit message validation passed"