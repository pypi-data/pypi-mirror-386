#!/bin/bash
# 重複実装防止Git Hooks設定スクリプト
#
# 新規ファイル作成時に重複実装チェックを自動実行するpre-commitフックを設定
#
# 使用例:
#   ./scripts/tools/setup_duplicate_prevention_hooks.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🔧 重複実装防止Hooks設定開始..."

# 1. pre-commitフック作成
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# 重複実装防止 pre-commit hook

PROJECT_ROOT="$(git rev-parse --show-toplevel)"

echo "🔍 重複実装検出チェック実行中..."

# 重複実装検出ツール実行
if [[ -f "$PROJECT_ROOT/scripts/tools/duplicate_implementation_detector.py" ]]; then
    cd "$PROJECT_ROOT"

    # 重複検出実行
    python scripts/tools/duplicate_implementation_detector.py
    EXIT_CODE=$?

    if [[ $EXIT_CODE -ne 0 ]]; then
        echo
        echo "❌ コミットブロック: 重複実装違反が検出されました"
        echo "修正してから再度コミットしてください"
        echo
        echo "自動修正を試す場合:"
        echo "  python scripts/tools/duplicate_implementation_detector.py --fix"
        echo
        exit 1
    fi

    echo "✅ 重複実装チェック: 問題なし"
else
    echo "⚠️ 重複実装検出ツールが見つかりません"
fi

# 影響調査サマリー生成（情報提供のみ）
if [[ -f "$PROJECT_ROOT/scripts/tools/impact_audit.py" ]]; then
    cd "$PROJECT_ROOT"
    echo "🗂️ 影響調査サマリーを生成中..."
    python scripts/tools/impact_audit.py --output temp/impact_audit/latest.md || true
fi

# 統一ロギング品質ゲート（警告のみ）
if [[ -f "$PROJECT_ROOT/src/noveler/infrastructure/quality_gates/unified_logging_gate.py" ]]; then
    cd "$PROJECT_ROOT"
    echo "🧭 統一ロギング品質ゲート（警告モード）を実行中..."
    python src/noveler/infrastructure/quality_gates/unified_logging_gate.py --warn-only || true
fi

# 新規Pythonファイルの特別チェック
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=A | grep -E '\.py$' || true)

if [[ -n "$STAGED_PY_FILES" ]]; then
    echo
    echo "📝 新規Pythonファイル検出: $STAGED_PY_FILES"

    for file in $STAGED_PY_FILES; do
        if [[ -f "$file" ]]; then
            echo "  チェック中: $file"

            # Console直接インスタンス化チェック
            if grep -q "Console()" "$file"; then
                echo "❌ Console()の直接インスタンス化が検出されました: $file"
                echo "   修正: from noveler.presentation.shared.shared_utilities import console"
                exit 1
            fi

            # import loggingチェック
            if grep -q "^import logging" "$file"; then
                echo "❌ 直接logging使用が検出されました: $file"
                echo "   修正: from noveler.infrastructure.logging.unified_logger import get_logger"
                exit 1
            fi

            # パスハードコーディングチェック
            if grep -qE '["\'][0-9][0-9]_' "$file"; then
                echo "❌ パスハードコーディングが検出されました: $file"
                echo "   修正: CommonPathServiceを使用してください"
                exit 1
            fi

            echo "  ✅ $file: チェック完了"
        fi
    done
fi

echo "✅ pre-commit チェック完了"
EOF

# 実行権限付与
chmod +x "$HOOKS_DIR/pre-commit"

# 2. pre-push フック作成（オプション）
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
# 重複実装防止 pre-push hook

PROJECT_ROOT="$(git rev-parse --show-toplevel)"

echo "🚀 Push前の最終品質チェック..."

# 統合品質チェック実行
if [[ -f "$PROJECT_ROOT/check_tdd_ddd_compliance.py" ]]; then
    cd "$PROJECT_ROOT"

    echo "DDD準拠性チェック実行中..."
    python check_tdd_ddd_compliance.py --quick

    if [[ $? -ne 0 ]]; then
        echo "❌ Push中断: 品質チェックに失敗しました"
        exit 1
    fi
else
    echo "⚠️ 品質チェックツールが見つかりません"
fi

echo "✅ 品質チェック完了"
EOF

chmod +x "$HOOKS_DIR/pre-push"

# 3. 設定完了メッセージ
echo
echo "✅ 重複実装防止Hooks設定完了!"
echo "------------------------------------------"
echo "設定されたフック:"
echo "  • pre-commit: 重複実装検出 + 新規ファイルチェック"
echo "  • pre-push: 統合品質チェック"
echo
echo "📋 動作確認:"
echo "  git add . && git commit -m \"test\""
echo
echo "🔧 無効化 (必要時):"
echo "  git config core.hooksPath /dev/null  # 一時無効"
echo "  git config --unset core.hooksPath    # 有効化"
echo

# 4. テスト実行
echo "🧪 フック動作テスト..."

# 現在の変更状況確認
if git diff --staged --quiet; then
    echo "ステージング領域が空のため、テスト用の軽微な変更を作成します"

    # テスト用ファイル作成
    TEST_FILE="$PROJECT_ROOT/test_hooks.tmp"
    echo "# Hooks test file" > "$TEST_FILE"
    git add "$TEST_FILE"

    echo "テスト実行中..."
    if "$HOOKS_DIR/pre-commit"; then
        echo "✅ pre-commitフック: 正常動作"
    else
        echo "❌ pre-commitフック: エラー"
    fi

    # クリーンアップ
    git reset HEAD "$TEST_FILE" >/dev/null 2>&1 || true
    rm -f "$TEST_FILE"
else
    echo "既存のステージング変更があります。手動でテストしてください:"
    echo "  git commit -m \"test\""
fi

echo
echo "🎉 セットアップ完了!"
echo "既存実装を無視した新規開発が自動的に防止されます。"
