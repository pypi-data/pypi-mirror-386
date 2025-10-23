#!/usr/bin/env bash
# Enhanced pre-commit hook - GitHub Actions functionality integrated
# File: scripts/local-ci/enhanced_pre_commit.sh

set -euo pipefail

# Get repository root
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "🔍 Enhanced pre-commit checks starting..."

# 1. Standard pre-commit (existing)
if command -v pre-commit >/dev/null 2>&1; then
    echo "📝 Running standard pre-commit checks..."
    pre-commit run --files "$@" || {
        echo "❌ Standard pre-commit checks failed"
        exit 1
    }
else
    echo "⚠️ pre-commit not installed, skipping standard checks"
fi

# 2. Fast quality checks (GitHub Actions replacement)
echo "🧪 Running fast quality checks..."

# Lint check
echo "🔎 Ruff linting..."
if command -v ruff >/dev/null 2>&1; then
    ruff check --quiet || {
        echo "❌ Ruff linting failed"
        exit 1
    }
else
    echo "⚠️ Ruff not available"
fi

# Type check (only on changed files)
echo "🔍 MyPy type checking..."
if command -v mypy >/dev/null 2>&1; then
    # Only run mypy on Python files being committed
    git diff --cached --name-only --diff-filter=AM | grep '\.py$' | head -10 | xargs -r mypy --quiet || {
        echo "❌ Type checking failed"
        exit 1
    }
else
    echo "⚠️ MyPy not available"
fi

# 3. Import validation
echo "📦 Import validation..."
if [ -f "scripts/tools/import_validator.py" ]; then
    python3 scripts/tools/import_validator.py --quick-check || {
        echo "❌ Import validation failed"
        exit 1
    }
else
    echo "⚠️ Import validator not found"
fi

# 4. DDD compliance (quick check)
echo "🏗️ DDD compliance (quick)..."
if [ -f "scripts/tools/check_tdd_ddd_compliance.py" ]; then
    python3 scripts/tools/check_tdd_ddd_compliance.py --quick --project-root=. || {
        echo "❌ DDD compliance check failed"
        exit 1
    }
else
    echo "⚠️ DDD compliance checker not found"
fi

echo "✅ All pre-commit checks passed!"