#!/bin/bash
# File: scripts/setup/rebuild_wsl_venv.sh
# Purpose: WSL Ubuntu環境でLinux版Python仮想環境を再構築

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Working directory: $PROJECT_ROOT"

echo "=== WSL環境確認 ==="
uname -a
which python3
python3 --version

echo ""
echo "=== 既存.venv削除 ==="
if [ -d .venv ]; then
    rm -rf .venv
    echo "✓ .venv削除完了"
fi

echo ""
echo "=== uv確認 ==="
if ! command -v uv &> /dev/null; then
    echo "uvをインストール中..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
uv --version

echo ""
echo "=== Linux版仮想環境構築 ==="
uv venv .venv --python 3.13

echo ""
echo "=== 仮想環境確認 ==="
ls -la .venv/bin/python*
file .venv/bin/python

echo ""
echo "=== 依存パッケージインストール ==="
uv pip install -e .

echo ""
echo "=== 完了 ==="
echo ".venv/bin/python が Linux ELF形式であることを確認してください"
