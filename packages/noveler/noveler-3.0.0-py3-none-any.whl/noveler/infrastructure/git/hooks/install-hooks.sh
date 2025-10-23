#!/bin/bash
#
# Git hooksのインストールスクリプト
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🔧 Installing Git hooks..."

# pre-commitフックのインストール
if [ -f "$SCRIPT_DIR/pre-commit-ddd" ]; then
    echo "📋 Installing DDD pre-commit hook..."

    # 既存のpre-commitがある場合はバックアップ
    if [ -f "$GIT_HOOKS_DIR/pre-commit" ]; then
        echo "   Backing up existing pre-commit hook..."
        mv "$GIT_HOOKS_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # フックをコピー
    cp "$SCRIPT_DIR/pre-commit-ddd" "$GIT_HOOKS_DIR/pre-commit"
    chmod +x "$GIT_HOOKS_DIR/pre-commit"

    echo "✅ DDD pre-commit hook installed successfully!"
else
    echo "❌ pre-commit-ddd not found!"
    exit 1
fi

# post-commitフックのインストール
if [ -f "$SCRIPT_DIR/post-commit-auto-deploy" ]; then
    echo "🚀 Installing auto-deploy post-commit hook..."

    # 既存のpost-commitがある場合はバックアップ
    if [ -f "$GIT_HOOKS_DIR/post-commit" ]; then
        echo "   Backing up existing post-commit hook..."
        mv "$GIT_HOOKS_DIR/post-commit" "$GIT_HOOKS_DIR/post-commit.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # フックをコピー
    cp "$SCRIPT_DIR/post-commit-auto-deploy" "$GIT_HOOKS_DIR/post-commit"
    chmod +x "$GIT_HOOKS_DIR/post-commit"

    echo "✅ Auto-deploy post-commit hook installed successfully!"
else
    echo "⚠️  post-commit-auto-deploy not found - skipping auto-deploy setup"
fi

echo ""
echo "🎉 Git hooks installation complete!"
echo ""
echo "The following will run automatically:"
echo ""
echo "📋 Before each commit (pre-commit):"
echo "  - DDD compliance validation (85% threshold)"
echo "  - Test coverage check (60% minimum)"
echo "  - Layer dependency validation"
echo "  - TDD cycle reminders"
echo ""
echo "🚀 After each commit (post-commit):"
echo "  - Automatic deployment to all projects"
echo "  - Git archive-based script synchronization"
echo "  - Production-ready version distribution"
echo ""
echo "💡 Notes:"
echo "  - Pre-commit bypass: git commit --no-verify (emergency only!)"
echo "  - Auto-deploy logs: /tmp/auto-deploy.log"
echo "  - Manual deploy: python3 scripts/tools/deploy_scripts_cli.py"
echo ""
