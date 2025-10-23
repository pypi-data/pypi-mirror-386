#!/usr/bin/env bash
# Safely remove .github directory after migrating to local CI
# File: scripts/local-ci/remove_github_directory.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🗑️ Removing .github directory (GitHub Actions no longer needed)..."

# Safety check - ensure we're in the right directory
if [ ! -d ".github" ]; then
    echo "❌ .github directory not found in current directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Backup before removal
BACKUP_DIR="archive/github_workflows_backup_$(date +%Y%m%d_%H%M%S)"
echo "📥 Creating backup: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
cp -r .github/* "$BACKUP_DIR/"

# List what we're removing
echo "📋 Contents being removed:"
find .github -type f | head -20

# Remove the directory
echo "🗑️ Removing .github directory..."
rm -rf .github

echo "✅ .github directory removed successfully!"
echo
echo "📁 Backup location: $BACKUP_DIR"
echo "🔧 Local CI implementation:"
echo "  • Git hooks: ~/.git-noveler/hooks/"
echo "  • Cron jobs: Use 'crontab -l' to view"
echo "  • Make targets: 'make quality-full', 'make daily-checks', etc."
echo
echo "💡 To verify local CI setup:"
echo "  make quality-full"
echo "  make daily-checks"