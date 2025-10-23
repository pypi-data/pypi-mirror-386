#!/usr/bin/env bash
# Setup local CI cron jobs (GitHub Actions replacement)
# File: scripts/setup/setup_local_ci_cron.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CRON_LOG_DIR="$PROJECT_ROOT/temp/cron"

echo "🔧 Setting up local CI cron jobs..."

# Create log directory
mkdir -p "$CRON_LOG_DIR"

# Get current user
USER=$(whoami)

# Current crontab backup
echo "📥 Backing up current crontab..."
crontab -l > "$CRON_LOG_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "No existing crontab"

# New cron entries
DAILY_CRON_ENTRY="0 2 * * * cd '$PROJECT_ROOT' && make daily-checks >> '$CRON_LOG_DIR/daily_checks.log' 2>&1"
WEEKLY_CRON_ENTRY="0 21 * * 0 cd '$PROJECT_ROOT' && make weekly-full-check >> '$CRON_LOG_DIR/weekly_full_check.log' 2>&1"

# Check if entries already exist
EXISTING_CRONTAB=$(crontab -l 2>/dev/null || true)

if echo "$EXISTING_CRONTAB" | grep -q "make daily-checks"; then
    echo "⚠️ Daily checks cron job already exists"
else
    echo "➕ Adding daily checks cron job..."
    (echo "$EXISTING_CRONTAB"; echo "$DAILY_CRON_ENTRY") | crontab -
    echo "  📅 Schedule: Every day at 2:00 AM"
fi

if echo "$EXISTING_CRONTAB" | grep -q "make weekly-full-check"; then
    echo "⚠️ Weekly full check cron job already exists"
else
    echo "➕ Adding weekly full check cron job..."
    UPDATED_CRONTAB=$(crontab -l 2>/dev/null || true)
    (echo "$UPDATED_CRONTAB"; echo "$WEEKLY_CRON_ENTRY") | crontab -
    echo "  📅 Schedule: Every Sunday at 9:00 PM"
fi

echo
echo "📋 Current cron jobs for local CI:"
crontab -l | grep -E "(daily-checks|weekly-full-check)" || echo "No local CI cron jobs found"

echo
echo "📁 Log files:"
echo "  Daily:  $CRON_LOG_DIR/daily_checks.log"
echo "  Weekly: $CRON_LOG_DIR/weekly_full_check.log"

echo
echo "✅ Local CI cron jobs setup completed!"
echo
echo "💡 To test manually:"
echo "  make daily-checks"
echo "  make weekly-full-check"
echo
echo "💡 To remove cron jobs:"
echo "  crontab -e  # Edit and remove the entries manually"