#!/bin/bash
# 各プロジェクトフォルダに配置するnovelコマンドのショートカット
# 使用方法: このファイルをプロジェクトフォルダにコピーして使用

# 現在のスクリプトのディレクトリを取得（プロジェクトフォルダ）
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# プロジェクト設定.yamlの存在確認
if [ ! -f "$PROJECT_DIR/プロジェクト設定.yaml" ]; then
    echo "❌ エラー: プロジェクト設定.yamlが見つかりません。"
    echo "   パス: $PROJECT_DIR"
    echo "   このスクリプトはプロジェクトのルートディレクトリに配置してください。"
    exit 1
fi

# 00_ガイドディレクトリを探す（親ディレクトリから）
GUIDE_DIR=""
CURRENT_DIR="$PROJECT_DIR"
while [ "$CURRENT_DIR" != "/" ]; do
    PARENT_DIR="$(dirname "$CURRENT_DIR")"
    if [ -d "$PARENT_DIR/00_ガイド" ]; then
        GUIDE_DIR="$PARENT_DIR/00_ガイド"
        break
    fi
    CURRENT_DIR="$PARENT_DIR"
done

if [ -z "$GUIDE_DIR" ]; then
    echo "❌ エラー: 00_ガイドディレクトリが見つかりません。"
    echo "   このプロジェクトは小説執筆支援システムの配下に配置してください。"
    exit 1
fi

# novelコマンドのパス確認（binディレクトリ）
NOVEL_SCRIPT="$GUIDE_DIR/bin/noveler"

if [ ! -f "$NOVEL_SCRIPT" ]; then
    echo "❌ エラー: novelコマンドが見つかりません。"
    echo "   期待されるパス: $NOVEL_SCRIPT"
    echo "   システムが正しくセットアップされていない可能性があります。"
    exit 1
fi

# プロジェクト名を表示
PROJECT_NAME=$(grep -E "^\s*name:\s*" "$PROJECT_DIR/プロジェクト設定.yaml" | head -1 | sed 's/.*name:[[:space:]]*"\?\([^"]*\)"\?.*/\1/')
echo "📖 プロジェクト: $PROJECT_NAME"
echo "🔧 実行パス: $GUIDE_DIR"

# プロジェクトルートを設定してnovelコマンドを実行
cd "$PROJECT_DIR"
export PROJECT_ROOT="$PROJECT_DIR"
"$NOVEL_SCRIPT" "$@"
