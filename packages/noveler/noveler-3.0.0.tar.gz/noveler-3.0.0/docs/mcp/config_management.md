# MCP設定管理ガイド（SSOT）

## 設定ファイルの役割と管理方針

### アクティブ設定ファイル

1. **`codex.mcp.json`** (リポジトリルート)
   - **用途**: Codex CLI用のNoveler MCPサーバー設定
   - **管理**: `./bin/setup_mcp_configs --codex`で自動更新
   - **含まれるサーバー**: noveler, noveler-dev

2. **`.mcp/config.json`**
   - **用途**: Claude Code用のNoveler MCPサーバー設定
   - **管理**: `./bin/setup_mcp_configs --project`で自動更新
   - **含まれるサーバー**: noveler, noveler-dev

3. **`.codex/mcp.json`**
   - **用途**: Codex用マルチサーバー設定（Serena, Local Context等含む）
   - **管理**: 手動管理（Noveler以外のサーバーを含むため）
   - **含まれるサーバー**: noveler, noveler-dev, serena, serena-uvx, local-context

4. **`docs/.examples/codex.mcp.json`**
   - **用途**: ドキュメント・テンプレート用
   - **管理**: 手動管理（例示目的）
   - **含まれるサーバー**: noveler

### 自動更新ツール

- **`./bin/setup_mcp_configs`**: 1と2の設定を統一的に更新
- **オプション**:
  - `--codex`: codex.mcp.jsonのみ更新
  - `--project`: .mcp/config.jsonのみ更新
  - `--claude`: Claude Code用設定のみ更新
  - `--dry-run`: 変更プレビューのみ

### 削除済み不要ファイル（2025-09-22）

以下のファイルは重複のため削除されました：
- `claude_code_mcp_config.json`
- `test_mcp_minimal.json`
- `.mcp.production.json`
- `config/claude_code_mcp_config.json`
- `config/claude_code_mcp_config_enhanced.json`
- `scripts/.mcp.production.json`

### ベストプラクティス

1. **Noveler MCPサーバーの設定変更**: `./bin/setup_mcp_configs`を使用
2. **複数サーバー環境**: `.codex/mcp.json`を直接編集
3. **新規環境セットアップ**: `./bin/setup_mcp_configs`で基本設定を生成後、必要に応じて手動調整

### よくあるトラブル（dist不在・接続断）

設定が反映されない、接続できない場合は以下を確認します。

1. `dist/mcp_servers/noveler/main.py` の存在を確認。存在しない場合は `python scripts/ci/ensure_dist_wrapper.py` を実行し、必要なら `STRICT_DIST_WRAPPER=1 python scripts/ci/check_dist_wrapper.py` で検証します。
2. `cwd` が対象リポジトリのルート（例: `…/00_ガイド`）になっているかを確認します。
3. `PYTHONPATH` に `…/00_ガイド` および `…/00_ガイド/dist` が含まれているか確認します。
4. ログに `Connection closed` が出力されている場合、`/mcp restart noveler` を実行し、設定の保存後に再接続します。

### SSOT原則

- Noveler MCPサーバー設定は`scripts/setup/update_mcp_configs.py`の`ensure_mcp_server_entry()`が唯一の真の定義
- この関数は**環境を自動検出**し、開発環境・本番環境（dist-only）の両方に対応
- 他のMCPサーバー（Serena等）は各自のドキュメントに従い手動管理
- 設定変更時は必ず`setup_mcp_configs`を優先使用し、手動編集は最小限に留める

#### 環境自動検出の仕組み

`ensure_mcp_server_entry()` は以下のロジックで環境を判定します：

```python
def _detect_environment(project_root: Path) -> str:
    """
    開発環境か本番環境かを判定
    - src/ が存在 → 開発環境
    - src/ が存在しない & dist/ が存在 → 本番環境（dist-only）
    - その他 → 開発環境（デフォルト）
    """
```

| 環境 | src/ | dist/ | 参照先 | PYTHONPATH |
|-----|------|-------|------|-----------|
| 開発（クローン） | ✅ | ❌ | `src/mcp_servers/noveler/main.py` | `[project_root, src]` |
| 開発（ビルド後） | ✅ | ✅ | `src/mcp_servers/noveler/main.py` | `[project_root, src]` |
| 本番（dist-only） | ❌ | ✅ | `dist/mcp_servers/noveler/main.py` | `[dist, project_root]` |

#### ビルドと設定の一貫性

- `make build` は `scripts/build.py:create_production_mcp_config()` を実行
- この関数は同じ `ensure_mcp_server_entry()` を呼び出し（`env="production"` 指定）
- 結果として `.mcp.production.json` が生成される
- `setup_mcp_configs` を実行しても、同じ関数が使用されるため、矛盾が発生しない
- **SSOT の一貫性が保証される**
