#!/bin/bash
# File: scripts/setup/setup_weekly_cleanup_cron.sh
# Purpose: Setup weekly cleanup cron job for local development environment
# Context: Alternative to GitHub Actions for local git repositories

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CRON_ENTRY="0 21 * * 0 cd '$PROJECT_ROOT' && make archive-cleanup >> '$PROJECT_ROOT/temp/weekly_cleanup.log' 2>&1"

echo "Setting up weekly cleanup cron job for local environment..."
echo "Project root: $PROJECT_ROOT"
echo

# Check if cron is available
if ! command -v crontab &> /dev/null; then
    echo "❌ crontab command not found. This setup requires cron to be installed."
    echo "   On WSL/Ubuntu: sudo apt install cron"
    echo "   On macOS: cron should be available by default"
    exit 1
fi

# Show current crontab
echo "Current crontab entries:"
crontab -l 2>/dev/null || echo "  (no crontab entries)"
echo

# Check if entry already exists
if crontab -l 2>/dev/null | grep -q "make archive-cleanup"; then
    echo "⚠️  Weekly cleanup cron job already exists. Skipping..."
    echo "   To remove: crontab -e (then delete the line manually)"
    exit 0
fi

# Add the entry
echo "Adding weekly cleanup cron job..."
echo "  Schedule: Every Sunday at 9:00 PM"
echo "  Command: cd '$PROJECT_ROOT' && make archive-cleanup"
echo "  Log: '$PROJECT_ROOT/temp/weekly_cleanup.log'"
echo

# Backup current crontab and add new entry
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Weekly cleanup cron job added successfully!"
echo
echo "Manual operations:"
echo "  Preview: make archive-cleanup-dry-run"
echo "  Run now: make archive-cleanup"
echo "  View log: tail -f temp/weekly_cleanup.log"
echo "  Remove cron: crontab -e (then delete the line)"
echo
echo "Note: Ensure temp/ directory exists for log output"
mkdir -p "$PROJECT_ROOT/temp"
echo "Created temp/ directory for logs"