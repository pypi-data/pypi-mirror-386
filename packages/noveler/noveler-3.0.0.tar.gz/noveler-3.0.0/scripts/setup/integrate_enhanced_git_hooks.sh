#!/usr/bin/env bash
# Integrate enhanced Git hooks with existing hooks
# File: scripts/setup/integrate_enhanced_git_hooks.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOKS_DIR="$HOME/.git-noveler/hooks"

echo "🔗 Integrating enhanced Git hooks..."

# Backup existing hooks
BACKUP_DIR="$PROJECT_ROOT/temp/hooks_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📥 Backing up existing hooks to: $BACKUP_DIR"
cp -r "$HOOKS_DIR"/* "$BACKUP_DIR/" 2>/dev/null || true

# 1. Enhance pre-commit hook
echo "🔧 Enhancing pre-commit hook..."
PRE_COMMIT_HOOK="$HOOKS_DIR/pre-commit"

# Create enhanced pre-commit that calls both original and new checks
cat > "$PRE_COMMIT_HOOK.enhanced" << 'EOF'
#!/usr/bin/env bash
# Enhanced pre-commit hook (original + GitHub Actions functionality)

set -euo pipefail

# Get project root
REPO_ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd)"

# 1. Run original pre-commit hook
if [ -f "$0.original" ]; then
    echo "🔄 Running original pre-commit checks..."
    bash "$0.original" "$@" || exit 1
fi

# 2. Run enhanced checks
if [ -f "$REPO_ROOT/scripts/local-ci/enhanced_pre_commit.sh" ]; then
    echo "⚡ Running enhanced pre-commit checks..."
    bash "$REPO_ROOT/scripts/local-ci/enhanced_pre_commit.sh" "$@" || exit 1
fi

echo "✅ All pre-commit checks completed"
EOF

# Move original and replace
if [ -f "$PRE_COMMIT_HOOK" ]; then
    mv "$PRE_COMMIT_HOOK" "$PRE_COMMIT_HOOK.original"
fi
mv "$PRE_COMMIT_HOOK.enhanced" "$PRE_COMMIT_HOOK"
chmod +x "$PRE_COMMIT_HOOK"

# 2. Enhance commit-msg hook
echo "🔧 Enhancing commit-msg hook..."
COMMIT_MSG_HOOK="$HOOKS_DIR/commit-msg"

cat > "$COMMIT_MSG_HOOK.enhanced" << 'EOF'
#!/usr/bin/env bash
# Enhanced commit-msg hook (original + GitHub Actions functionality)

set -euo pipefail

# Get project root
REPO_ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd)"

# 1. Run original commit-msg hook
if [ -f "$0.original" ]; then
    echo "🔄 Running original commit-msg checks..."
    bash "$0.original" "$@" || exit 1
fi

# 2. Run enhanced checks
if [ -f "$REPO_ROOT/scripts/local-ci/enhanced_commit_msg.sh" ]; then
    echo "⚡ Running enhanced commit-msg checks..."
    bash "$REPO_ROOT/scripts/local-ci/enhanced_commit_msg.sh" "$@" || exit 1
fi

echo "✅ All commit-msg checks completed"
EOF

# Move original and replace
if [ -f "$COMMIT_MSG_HOOK" ]; then
    mv "$COMMIT_MSG_HOOK" "$COMMIT_MSG_HOOK.original"
fi
mv "$COMMIT_MSG_HOOK.enhanced" "$COMMIT_MSG_HOOK"
chmod +x "$COMMIT_MSG_HOOK"

# 3. Enhance post-commit hook
echo "🔧 Enhancing post-commit hook..."
POST_COMMIT_HOOK="$HOOKS_DIR/post-commit"

cat > "$POST_COMMIT_HOOK.enhanced" << 'EOF'
#!/usr/bin/env bash
# Enhanced post-commit hook (original + GitHub Actions functionality)

set -euo pipefail

# Get project root
REPO_ROOT="$(cd "$(git rev-parse --show-toplevel)" && pwd)"

# 1. Run original post-commit hook
if [ -f "$0.original" ]; then
    echo "🔄 Running original post-commit checks..."
    bash "$0.original" "$@" || true  # Non-blocking
fi

# 2. Run enhanced checks (background)
if [ -f "$REPO_ROOT/scripts/local-ci/enhanced_post_commit.sh" ]; then
    echo "⚡ Running enhanced post-commit checks (background)..."
    {
        bash "$REPO_ROOT/scripts/local-ci/enhanced_post_commit.sh" "$@" || true
    } &
fi

echo "✅ Post-commit processing started"
EOF

# Move original and replace
if [ -f "$POST_COMMIT_HOOK" ]; then
    mv "$POST_COMMIT_HOOK" "$POST_COMMIT_HOOK.original"
fi
mv "$POST_COMMIT_HOOK.enhanced" "$POST_COMMIT_HOOK"
chmod +x "$POST_COMMIT_HOOK"

echo
echo "✅ Enhanced Git hooks integration completed!"
echo
echo "📁 Backup location: $BACKUP_DIR"
echo "🔗 Enhanced hooks:"
echo "  pre-commit:  $PRE_COMMIT_HOOK"
echo "  commit-msg:  $COMMIT_MSG_HOOK"
echo "  post-commit: $POST_COMMIT_HOOK"
echo
echo "💡 To test the hooks:"
echo "  git add -A && git commit -m 'test: enhanced hooks integration'"