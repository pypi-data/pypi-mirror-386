#!/bin/bash
# 小説執筆支援システム 環境設定スクリプト
# 使用方法: source scripts/setup/setenv.sh

# スクリプトの場所を取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GUIDE_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SCRIPTS_ROOT="$GUIDE_ROOT/src"

# 環境変数の設定
export GUIDE_ROOT="$GUIDE_ROOT"
export SCRIPTS_ROOT="$SCRIPTS_ROOT"
export PYTHONPATH="$SCRIPTS_ROOT:$PYTHONPATH"

# PATH に bin ディレクトリを追加
export PATH="$GUIDE_ROOT/bin:$PATH"

# ログ出力
echo "🔧 小説執筆支援システム環境設定完了"
echo "   GUIDE_ROOT: $GUIDE_ROOT"
echo "   SRC_ROOT: $SCRIPTS_ROOT"
echo "   PATH に追加: $GUIDE_ROOT/bin"
echo ""
echo "✅ 使用可能コマンド:"
echo "   novel --help    # コマンド一覧"
echo "   novel status    # システム状況確認"
echo "   novel new       # 新規プロジェクト作成"
echo ""

# 便利なエイリアス
alias cdguide="cd '$GUIDE_ROOT'"
alias cdsrc="cd '$SCRIPTS_ROOT'"
alias novel-test="cd '$GUIDE_ROOT' && python -m pytest tests/"

echo "📁 便利なエイリアス:"
echo "   cdguide      # ガイドルートへ移動"
echo "   cdsrc        # srcルートへ移動"
echo "   novel-test   # テスト実行"
