# VSCode開発環境セットアップガイド

## 概要

このガイドでは、小説執筆支援システム（Noveler）の開発環境をVSCodeで構築する手順を説明します。

## デバッグ設定（launch.json）

### 現在の設定構成

プロジェクトルートの `.vscode/launch.json` には以下のデバッグ設定が含まれています：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Noveler MCP Server",
      "type": "python",
      "request": "launch",
      "module": "mcp_servers.noveler",
      "args": [],
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src:${workspaceFolder}"
      },
      "python": "${workspaceFolder}/.venv/bin/python"
    },
    {
      "name": "Noveler CLI (bin/noveler)",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/bin/noveler",
      "args": ["--help"],
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env",
      "python": "${workspaceFolder}/.venv/bin/python"
    },
    {
      "name": "Test Current File",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

### 各設定の説明

#### 1. Noveler MCP Server
- **用途**: MCPサーバーのデバッグ
- **起動方法**: F5キー、または「実行とデバッグ」パネルから選択
- **特徴**: Claude Codeとの統合デバッグが可能

#### 2. Noveler CLI (bin/noveler)
- **用途**: 統合CLIのデバッグ
- **起動方法**: デバッグ構成を選択してF5
- **引数変更**: `args` 配列に任意のコマンドライン引数を追加

例：
```json
"args": ["mcp", "call", "list_available_tools"]
```

#### 3. Test Current File
- **用途**: 現在開いているテストファイルの実行
- **起動方法**: テストファイルを開いた状態でF5
- **特徴**: 個別テストの詳細なデバッグが可能

## 推奨拡張機能

### 必須
- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)

### 推奨
- **Python Test Explorer** (littlefoxteam.vscode-python-test-adapter)
- **YAML** (redhat.vscode-yaml)
- **Markdown All in One** (yzhang.markdown-all-in-one)
- **GitLens** (eamodio.gitlens)

## 環境設定

### Python仮想環境

1. 仮想環境の作成と有効化：
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# または
.venv\Scripts\activate  # Windows
```

2. 依存関係のインストール：
```bash
pip install -e ".[dev]"
```

### VSCode設定（settings.json）

プロジェクトルートの `.vscode/settings.json` に推奨設定：

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    ".mypy_cache": true,
    ".ruff_cache": true
  }
}
```

## デバッグのヒント

### ブレークポイントの設定
- 行番号の左側をクリック
- または `F9` キーで現在行にブレークポイントを設定

### 条件付きブレークポイント
- ブレークポイントを右クリック → 「条件の編集」
- 特定の条件でのみ停止させることが可能

### デバッグコンソール
- デバッグ中に変数の値を確認
- 式の評価が可能
- `Ctrl+Shift+Y` でコンソールパネルを表示

## トラブルシューティング

### よくある問題と解決方法

#### 1. ModuleNotFoundError
**原因**: PYTHONPATHが正しく設定されていない
**解決**: launch.jsonの `env` セクションを確認：
```json
"env": {
  "PYTHONPATH": "${workspaceFolder}/src:${workspaceFolder}"
}
```

#### 2. デバッガが起動しない
**原因**: Python仮想環境が有効でない
**解決**:
- VSCodeの左下のPythonインタープリタを確認
- `.venv/bin/python` が選択されていることを確認

#### 3. MCPサーバーが起動しない
**原因**: MCPサーバーのモジュールパスが変更された
**解決**: `module` の値が `mcp_servers.noveler` であることを確認

## 更新履歴

### 2025-09-27
- Typer CLIからMCPサーバーアーキテクチャへの移行に伴う設定更新
- `novel_cli.py` デバッグ設定を削除
- MCPサーバーとbin/novelerのデバッグ設定を追加

## 関連ドキュメント

- [開発者ガイド](developer_guide.md)
- [クイックスタート](quick_start.md)
- [MCP設定ガイド](../mcp/config_management.md)