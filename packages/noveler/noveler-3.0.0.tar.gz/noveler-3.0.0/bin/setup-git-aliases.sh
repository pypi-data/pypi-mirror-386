#!/bin/bash
# Git aliasの設定スクリプト
# 品質チェック統合git-commitコマンドを使いやすくする

echo "🔧 Git aliasを設定しています..."

# 現在のディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_COMMIT_PATH="$SCRIPT_DIR/git-commit"

# Gitエイリアスを設定（!を追加してexternal commandとして実行）
git config alias.ci "!$GIT_COMMIT_PATH"
git config alias.commit-safe "!$GIT_COMMIT_PATH"
git config alias.commit-check "!$GIT_COMMIT_PATH"

# 設定確認
echo ""
echo "✅ 以下のGitエイリアスが設定されました:"
echo ""
echo "  git ci              # 品質チェック付きコミット（短縮形）"
echo "  git commit-safe     # 品質チェック付きコミット（明示的）"
echo "  git commit-check    # 品質チェック付きコミット（説明的）"
echo ""

# 使用例を表示
echo "📚 使用例:"
echo ""
echo "  # 対話形式でコミット（推奨）"
echo "  git ci"
echo ""
echo "  # メッセージ指定でコミット"
echo "  git ci -m \"feat: 新機能追加\""
echo ""
echo "  # 品質チェックをスキップ（緊急時のみ）"
echo "  git ci --no-verify -m \"hotfix: 緊急修正\""
echo ""

# パスの設定確認
if [ -f "$GIT_COMMIT_PATH" ] && [ -x "$GIT_COMMIT_PATH" ]; then
    echo "✅ git-commitスクリプトが正常に設定されています"
else
    echo "❌ git-commitスクリプトが見つからないか実行権限がありません"
    echo "   パス: $GIT_COMMIT_PATH"
    exit 1
fi

echo ""
echo "🎉 設定完了！今後は 'git ci' でコミットしてください"
