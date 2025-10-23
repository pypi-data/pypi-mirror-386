# MCP Configuration Templates

このディレクトリはMCP（Model Context Protocol）サーバーの設定テンプレートを管理します。

## ファイル構成

- `codex.template.json`: Claude Code/Codex用の基本テンプレート
- `*.example.json`: 各環境向けのサンプル設定（将来追加）

## 実運用ファイルの配置

実際に使用される設定ファイルは以下の場所に配置されます:

- **リポジトリルート**: `codex.mcp.json` (Claude Code用)
- **ユーザーホーム**: `C:\Users\bamboocity\.claude.json` (Claude Desktop用)
- **プロジェクト内**: `.mcp/config.json` (プロジェクト固有設定)

## テンプレートの使用方法

設定を更新する際は、既存のスクリプトを使用してください:

### MCP設定の一括更新（推奨）

```bash
# Claude Code/Codexの全MCP設定を一括更新
bin/setup_mcp_configs

# または直接Pythonスクリプトを実行
python scripts/setup/update_mcp_configs.py

# 対象別に更新（オプション）
bin/setup_mcp_configs --codex      # codex.mcp.json のみ
bin/setup_mcp_configs --project    # .mcp/config.json のみ
bin/setup_mcp_configs --claude     # Claude Desktop設定のみ
bin/setup_mcp_configs --dry-run    # 変更内容の確認（書き込みなし）
```

**更新対象**:
- `codex.mcp.json` (リポジトリルート - Codex CLI用)
- `.mcp/config.json` (プロジェクト内 - Noveler MCP専用)
- Claude Desktop設定ファイル (OS依存パス)

### Codex CLI専用設定の同期

Codex CLIの`~/.codex/config.toml`を同期する場合は、専用スクリプトを使用:

```bash
# Codex CLI設定を同期（~/.codex/config.toml）
python scripts/setup/sync_codex_config.py

# 変更確認のみ（dry-run）
python scripts/setup/sync_codex_config.py --dry-run

# バックアップなしで更新（非推奨）
python scripts/setup/sync_codex_config.py --no-backup
```

**用途**:
- Codex CLI（`codex`コマンド）の`mcp_servers`セクションをテンプレートと同期
- `config/mcp/codex.template.json`の内容を`~/.codex/config.toml`に反映
- 他のセクション（model設定など）は変更されません

## 注意事項

- このディレクトリ内のファイルはテンプレートです。直接編集しても動作には影響しません。
- 実運用ファイルを変更した場合は、このテンプレートも同期させてください。
- パス情報は環境依存のため、テンプレート内では絶対パスを使用しています。

### スクリプト統合について

**決定事項**: `sync_codex_config.py`は`bin/setup_mcp_configs`に統合**しない**

**理由**:
- 対象ファイル形式が異なる（JSON vs TOML）
- 設定ファイルの場所が異なる（プロジェクト内 vs ユーザーホーム）
- `sync_codex_config.py`はCodex CLI専用で、使用頻度が低い
- 各スクリプトを独立して実行することで、誤った設定上書きを防止

**推奨運用**:
- 通常は`bin/setup_mcp_configs`のみ使用（Claude Code/MCP設定）
- Codex CLIを使用する場合のみ`sync_codex_config.py`を手動実行
