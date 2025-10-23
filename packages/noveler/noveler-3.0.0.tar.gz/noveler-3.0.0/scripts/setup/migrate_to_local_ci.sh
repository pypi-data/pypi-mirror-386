#!/usr/bin/env bash
# Complete migration from GitHub Actions to Local CI
# File: scripts/setup/migrate_to_local_ci.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Migrating from GitHub Actions to Local CI..."
echo "📁 Project: $PROJECT_ROOT"
echo

# Step 1: Test current setup
echo "1️⃣ Testing current Makefile targets..."
if make quality-full; then
    echo "✅ Makefile targets working"
else
    echo "❌ Makefile targets failed - please fix before continuing"
    exit 1
fi

# Step 2: Setup cron jobs
echo
echo "2️⃣ Setting up cron jobs..."
bash scripts/setup/setup_local_ci_cron.sh

# Step 3: Integrate Git hooks
echo
echo "3️⃣ Integrating enhanced Git hooks..."
bash scripts/setup/integrate_enhanced_git_hooks.sh

# Step 4: Test Git hooks
echo
echo "4️⃣ Testing Git hooks (dry run)..."
echo "test: local CI migration" > temp/test_commit_msg.txt
if bash ~/.git-noveler/hooks/commit-msg temp/test_commit_msg.txt; then
    echo "✅ Git hooks working"
    rm -f temp/test_commit_msg.txt
else
    echo "❌ Git hooks failed"
    rm -f temp/test_commit_msg.txt
    exit 1
fi

# Step 5: Remove .github directory
echo
echo "5️⃣ Removing .github directory..."
bash scripts/local-ci/remove_github_directory.sh

echo
echo "🎉 Migration to Local CI completed successfully!"
echo
echo "📋 Summary of changes:"
echo "  ✅ Makefile targets added (quality-full, daily-checks, weekly-full-check)"
echo "  ✅ Enhanced Git hooks integrated"
echo "  ✅ Cron jobs configured for daily/weekly checks"
echo "  ✅ .github directory removed"
echo
echo "🔧 Local CI Features:"
echo "  • Pre-commit: Lint, type check, DDD compliance"
echo "  • Post-commit: Unit tests, coverage, CODEMAP update"
echo "  • Commit-msg: Three-commit cycle, message format validation"
echo "  • Daily (2:00 AM): Full quality checks"
echo "  • Weekly (Sun 9:00 PM): Archive cleanup + quality checks"
echo
echo "💡 Manual commands:"
echo "  make quality-full      # Run all quality checks"
echo "  make daily-checks      # Run daily quality checks"
echo "  make weekly-full-check # Run weekly comprehensive check"
echo "  crontab -l             # View scheduled cron jobs"
echo
echo "🎯 Next steps:"
echo "  1. Test: git add -A && git commit -m 'test: local CI integration'"
echo "  2. Monitor: tail -f temp/cron/daily_checks.log"