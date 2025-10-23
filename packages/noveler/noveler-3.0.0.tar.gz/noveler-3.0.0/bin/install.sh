#!/bin/bash

# 小説執筆支援システム インストールスクリプト
# 使用方法: ./install.sh

set -e  # エラー時に停止

echo "📚 小説執筆支援システムをインストールしています..."
echo ""

# 現在のディレクトリを取得
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# scripts ディレクトリは 00_ガイド の直下にある
GUIDE_DIR="$(dirname "$INSTALL_DIR")"
SCRIPTS_DIR="$GUIDE_DIR/scripts"
BIN_DIR="$INSTALL_DIR"

# 基本的な要件チェック
echo "🔍 システム要件をチェックしています..."

# Python 3.8+ チェック
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3が見つかりません"
    echo "   Python 3.8以上をインストールしてください"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Python 3.8以上が必要です（現在: $PYTHON_VERSION）"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION が利用可能です"

# pip チェック
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip が見つかりません"
    echo "   pip をインストールしてください"
    exit 1
fi

# PIP_CMD を決定
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

echo "✅ pip が利用可能です"

# Git チェック（オプション）
if command -v git &> /dev/null; then
    echo "✅ Git が利用可能です"
else
    echo "⚠️  Git が見つかりません（オプション機能で使用）"
fi

echo ""

# 依存関係のインストール
echo "📦 依存関係をインストールしています..."
cd "$SCRIPTS_DIR"

if [ -f "requirements.txt" ]; then
    $PIP_CMD install -r requirements.txt
    echo "✅ Python パッケージをインストールしました"
else
    echo "❌ requirements.txt が見つかりません"
    exit 1
fi

echo ""

# PATH設定
echo "🔧 PATH設定を構成しています..."

# シェルの種類を検出
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
    SHELL_NAME="bash"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
    SHELL_NAME="zsh"
else
    SHELL_RC="$HOME/.profile"
    SHELL_NAME="shell"
fi

# PATH設定行
PATH_LINE="export PATH=\"$BIN_DIR:\$PATH\""

# 既存の設定をチェック
if [ -f "$SHELL_RC" ]; then
    if grep -q "$BIN_DIR" "$SHELL_RC"; then
        echo "✅ PATH設定は既に存在します"
    else
        echo "$PATH_LINE" >> "$SHELL_RC"
        echo "✅ PATH設定を $SHELL_RC に追加しました"
    fi
else
    echo "$PATH_LINE" >> "$SHELL_RC"
    echo "✅ PATH設定を $SHELL_RC に作成しました"
fi

# 現在のセッションでPATHを設定
export PATH="$BIN_DIR:$PATH"

echo ""

# 権限設定
echo "🔐 実行権限を設定しています..."
chmod +x "$BIN_DIR"/*
echo "✅ 実行権限を設定しました"

echo ""

# グローバル設定の初期化
echo "⚙️  グローバル設定を初期化しています..."
cd "$SCRIPTS_DIR"

if [ -f "setup/novel_config.py" ]; then
    if python3 setup/novel_config.py init --auto 2>/dev/null; then
        echo "✅ グローバル設定を初期化しました"
    else
        echo "⚠️  グローバル設定の初期化をスキップしました（既に存在または手動設定が必要）"
    fi
else
    echo "⚠️  設定スクリプトが見つかりません。手動設定が必要です"
fi

echo ""

# 動作確認
echo "🧪 動作確認を実行しています..."

# novelerコマンドの確認
if command -v noveler &> /dev/null; then
    echo "✅ noveler コマンドが利用可能です"

    # システム診断
    if noveler status &> /dev/null; then
        echo "✅ システム診断が正常に動作します"
    else
        echo "⚠️  システム診断で軽微な問題があります（動作には影響しません）"
    fi
else
    echo "❌ noveler コマンドが見つかりません"
    echo "   新しいターミナルを開くか、以下を実行してください:"
    echo "   source $SHELL_RC"
    echo "   または"
    echo "   export PATH=\"$BIN_DIR:\$PATH\""
fi

echo ""

# インストール完了
echo "🎉 インストールが完了しました！"
echo ""
echo "📝 次のステップ:"
echo "  1. 新しいターミナルを開くか、以下を実行:"
echo "     source $SHELL_RC"
echo ""
echo "  2. 動作確認:"
echo "     noveler --help"
echo "     noveler status"
echo ""
echo "  3. 新規プロジェクト作成:"
echo "     noveler create \"あなたの作品名\""
echo ""
echo "  4. 執筆開始:"
echo "     cd 01_あなたの作品名"
echo "     noveler write 1"
echo ""
echo "📚 詳細な使い方は以下を参照してください:"
echo "  - README_SIMPLE.md (5分で始めるガイド)"
echo "  - README.md (完全な技術仕様)"
echo "  - 00_統合マスターガイド.md (全体概要)"
echo ""
echo "🆘 問題が発生した場合:"
echo "  - noveler status で状態確認"
echo "  - noveler health check で詳細診断"
echo "  - scripts/setup/SETUP_GUIDE.md でトラブルシューティング"
echo ""
echo "✨ 素晴らしい小説執筆体験をお楽しみください！"
