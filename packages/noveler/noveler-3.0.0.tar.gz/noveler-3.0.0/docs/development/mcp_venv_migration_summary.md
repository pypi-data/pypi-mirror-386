# MCP & Venv Migration Summary

**Date**: 2025-10-03
**Task**: Windows/WSL クロスプラットフォームvenv対応 + MCP設定更新

---

## 完了した作業

### 1. ✅ クロスプラットフォームvenv管理スクリプト作成
**ファイル**: `scripts/setup_venv.py`

**機能**:
- Windows/WSL自動検出
- プラットフォーム別venv作成（`.venv.win` / `.venv.wsl`）
- UTF-8エンコーディング自動設定（Windows cp932対応）
- pyproject.toml依存関係の自動インストール
- 検証機能（`--verify-only`）

**使用方法**:
```bash
# Windows
py scripts/setup_venv.py

# WSL/Linux
python3 scripts/setup_venv.py
```

---

### 2. ✅ .gitignore更新
プラットフォーム別venvエントリを追加:
```gitignore
.venv.win     # Windows-specific venv
.venv.wsl     # WSL/Linux-specific venv
```

---

### 3. ✅ pyproject.toml依存関係修正
`pytest-timeout>=2.2.0`を`dev`グループに追加（テスト実行に必要）

---

### 4. ✅ ドキュメント作成

#### venv関連
- **docs/development/venv_setup_guide.md** - Venvセットアップガイド
  - クイックスタート（Windows/WSL）
  - コマンドリファレンス
  - トラブルシューティング
  - FAQ

#### MCP設定関連
- **docs/development/mcp_config_updates_needed.md** - MCP設定更新ガイド
  - 更新が必要な全ファイルのリスト
  - プラットフォーム別パス対応表
  - 更新手順（手動/自動）
  - 検証手順
  - ロールバック手順

---

## 特定されたMCP設定ファイル

### 更新が必要なファイル

| ファイル | 優先度 | 現在のパス | 新しいパス |
|---------|--------|-----------|-----------|
| **codex.mcp.json** | 🔴 High | `wsl python` | WSL: `.venv.wsl/bin/python`<br>Win: `.venv.win/Scripts/python.exe` |
| **.mcp/config.json** | 🟡 Medium | `.venv/bin/python` | `.venv.wsl/bin/python` |
| **.codex/mcp.json** | 🟡 Medium | `.venv/bin/python` | `.venv.wsl/bin/python` |
| **.mcp.production.json** | 🟢 Low | 確認が必要 | 確認が必要 |

### 確認が必要なスクリプト

| スクリプト | 役割 | 確認内容 |
|-----------|------|---------|
| **bin/setup_mcp_configs** | MCP設定更新ラッパー | プラットフォーム検出対応 |
| **scripts/setup/update_mcp_configs.py** | MCP設定更新ロジック | venvパス自動検出 |
| **bin/claude_code_mcp_setup.py** | Claude Code固有設定 | ハードコードパスチェック |

---

## 動作確認済み

### Windows環境

✅ **Venv作成**: `.venv.win/` 正常作成
```
[CREATE] Creating virtual environment: .venv.win
         Platform: Windows
         Python: py
[OK] Virtual environment created successfully
```

✅ **依存関係インストール**: 全パッケージインストール成功
```
Successfully installed noveler-3.0.0 pytest-8.4.2 ruff-0.13.3 ...
[OK] Dependencies installed successfully
```

✅ **UTF-8エンコーディング**: 日本語パス正常表示
```
Project: C:\Users\bamboocity\OneDrive\Documents\9_小説\00_ガイド
```

✅ **パッケージ検証**: novelerモジュールインポート成功
```
[VERIFY] Checking installation...
  [OK] Venv directory exists: .venv.win
  [OK] Python executable exists
  [OK] Pip executable exists
  [OK] Noveler package installed and importable
```

✅ **テスト実行**: A24 protagonist_nameテスト成功
```
tests/.../test_initialization_services.py::TestProjectSetupService::test_generate_character_settings_with_protagonist_name PASSED
============================== 1 passed in 0.22s ==============================
```

---

## 未完了タスク（次のステップ）

### Phase 1: MCP設定の手動更新（推奨: 即時対応）

1. **codex.mcp.json更新**
   ```bash
   # Backup
   cp codex.mcp.json codex.mcp.json.backup

   # Edit to use platform-specific venv
   # Windows: .venv.win/Scripts/python.exe
   # WSL: .venv.wsl/bin/python
   ```

2. **MCP server再起動**
   - Claude Code: Command Palette → "Claude Code: Restart MCP Servers"
   - 動作確認: noveler MCPツールをテスト

3. **検証**
   ```bash
   # Windows
   .\.venv.win\Scripts\python.exe -c "import noveler; print('OK')"
   ```

### ✅ Phase 2: スクリプト更新（完了: 2025-10-03）

1. **✅ scripts/setup/update_mcp_configs.py 更新**
   - プラットフォーム検出ロジック追加（`detect_wsl()` / `get_platform_venv_python()`）
   - `.venv.win` / `.venv.wsl` パス自動選択実装
   - UTF-8エンコーディング対応（Windows cp932対策）
   - venv存在確認と警告メッセージ追加

2. **✅ テスト実行**
   ```bash
   $ py -3 scripts/setup/update_mcp_configs.py --dry-run
   🔧 Updating MCP configs (server=noveler) in project: C:\Users\...\00_ガイド

   # Generated config correctly uses platform-specific path:
   "command": "C:\\Users\\...\\00_ガイド\\.venv.win\\Scripts\\python.exe"
   ```

3. **✅ 検証完了**
   - codex.mcp.json: `.venv.win` パス生成成功
   - .mcp/config.json: `.venv.win` パス生成成功
   - Claude desktop config: `.venv.win` パス生成成功

**Next**: 実際のMCP設定更新を実行（`--dry-run`なしで）

### Phase 3: 旧venvクリーンアップ（オプション）

```bash
# 既存の.venvを.venv.backupにリネーム
mv .venv .venv.backup

# 確認: 新venvのみ存在
ls -la .venv*
# Expected: .venv.win (Windows) または .venv.wsl (WSL)
```

---

## トラブルシューティング

### MCP Server起動失敗

**症状**: Claude CodeでMCPサーバーが起動しない

**原因**: 古い`.venv`パスを参照している

**解決策**:
1. `codex.mcp.json`のPythonパスを確認
2. プラットフォームに応じたvenvパスに更新
3. MCP serverを再起動

### Python Import Error

**症状**: `ModuleNotFoundError: No module named 'noveler'`

**原因**: venvが正しくインストールされていない

**解決策**:
```bash
# Venv再作成
py scripts/setup_venv.py --force

# 検証
py scripts/setup_venv.py --verify-only
```

### 文字化け（Windows）

**症状**: パスや出力が文字化けする

**原因**: Windows cp932エンコーディング

**解決策**: スクリプト内で自動対応済み（UTF-8強制設定）

---

## 参考ドキュメント

- [venv_setup_guide.md](./venv_setup_guide.md) - 詳細なvenvセットアップガイド
- [mcp_config_updates_needed.md](./mcp_config_updates_needed.md) - MCP設定更新の詳細手順
- [CLAUDE.md](../../CLAUDE.md) § MCP Operations - プロジェクト固有のMCP運用ルール
- [docs/mcp/config_management.md](../../docs/mcp/config_management.md) - SSOT管理ガイドライン

---

## 技術的な背景

### なぜプラットフォーム別venvが必要か？

1. **バイナリ互換性**: Linux ELF ≠ Windows PE
2. **パス形式の違い**: `/home/user/...` vs `C:\Users\...`
3. **シンボリックリンク**: WSLのシンボリックリンクはWindowsで動作しない
4. **ネイティブパフォーマンス**: 各プラットフォームのネイティブPython使用

### 既存の`.venv`の問題

```
.venv/pyvenv.cfg:
  home = /home/bamboocity/.local/share/uv/python/cpython-3.13.5-linux-x86_64-gnu/bin
```

- **Linux用Python**: Windows環境で実行不可
- **壊れたシンボリックリンク**: `.venv/bin/python3 -> python` (broken)
- **アーキテクチャ不一致**: x86_64-linux-gnu (ELF) ≠ Windows (PE)

---

## 次回セッションのチェックリスト

- [ ] MCP設定を自動更新: `python scripts/setup/update_mcp_configs.py`
- [ ] Claude CodeでMCPサーバー再起動
- [ ] noveler MCPツールの動作確認
- [x] ~~scripts/setup/update_mcp_configs.pyのレビュー~~ (完了)
- [x] ~~bin/setup_mcp_configs --dry-runテスト~~ (完了)
- [ ] 旧.venvディレクトリのバックアップ/削除（オプション）

---

## Contact & Support

問題が発生した場合:
1. [mcp_config_updates_needed.md](./mcp_config_updates_needed.md)のトラブルシューティングセクションを確認
2. [venv_setup_guide.md](./venv_setup_guide.md)のFAQを参照
3. ロールバック手順（バックアップから復元）を実行
