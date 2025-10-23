#!/bin/bash
# 統合キャッシュ管理システム環境変数設定スクリプト
#
# このスクリプトは新しいシェルセッションで読み込んで使用します:
# source scripts/tools/setup_cache_env.sh

# ガイドルートを取得
GUIDE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# temp/cache/python ディレクトリを作成
CACHE_DIR="$GUIDE_ROOT/temp/cache/python"
mkdir -p "$CACHE_DIR"

# PYTHONPYCACHEPREFIX環境変数を設定
export PYTHONPYCACHEPREFIX="$CACHE_DIR"

echo "🎯 統合キャッシュ管理システム環境変数設定完了"
echo "📁 PYTHONPYCACHEPREFIX = $PYTHONPYCACHEPREFIX"
echo ""
echo "💡 使用方法:"
echo "   source scripts/tools/setup_cache_env.sh"
echo "   python <your_script.py>"
echo ""
echo "✅ 今後のPythonキャッシュは temp/cache/python に統一されます"
