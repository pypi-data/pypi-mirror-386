#!/usr/bin/env bash
# Enhanced post-commit hook - GitHub Actions functionality integrated
# File: scripts/local-ci/enhanced_post_commit.sh

set -euo pipefail

# Get repository root
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "🚀 Enhanced post-commit checks starting..."

# 1. Quick unit tests (non-blocking)
echo "🧪 Running quick unit tests..."
export LLM_SILENT_PROGRESS=1
export LLM_FAST_CLEANUP=1
if python3 scripts/run_pytest.py --json-only -q tests/unit -m "not slow" --maxfail=3 >/dev/null 2>&1; then
    echo "✅ Quick unit tests passed"
else
    echo "⚠️ Some unit tests failed (check reports/llm_summary.jsonl)"
fi

# 2. Generate LLM summary
echo "📊 Generating test summary..."
if [ -f "reports/llm_summary.jsonl" ]; then
    echo "📁 Test summary available: reports/llm_summary.jsonl"
fi

# 3. Update CODEMAP (if available)
echo "🗺️ Updating CODEMAP..."
if [ -f "scripts/tools/update_codemap_foundation.py" ]; then
    python3 scripts/tools/update_codemap_foundation.py --quiet || true
fi

# 4. Coverage report (background)
echo "📈 Generating coverage report (background)..."
{
    python3 scripts/run_pytest.py --cov --cov-report=html --cov-report=term-missing -q tests/unit >/dev/null 2>&1 || true
} &

echo "✅ Post-commit checks completed"