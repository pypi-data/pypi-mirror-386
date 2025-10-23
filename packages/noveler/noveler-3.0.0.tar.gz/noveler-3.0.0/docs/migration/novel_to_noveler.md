# MIGRATION: `bin/novel` から `bin/noveler` への移行手順

最終更新: 2025-09-21

## 1. 背景

- 旧レガシーCLI `bin/novel` は 2025-09-21 をもって廃止されました。
- すべてのCLI操作は `bin/noveler`（本番想定）と MCP ツール (`noveler mcp call ...`) に統合されています。
- 既存のスクリプト／Gitフック／ドキュメントには「novel」表記が残っている場合があります。本ドキュメントはそれらを `noveler` ベースに差し替えるためのチェックリストです。

## 2. 置換サマリ

| 旧コマンド | 代替手段 |
| --- | --- |
| `./bin/novel --help` | `./bin/noveler --help` + `./bin/noveler mcp-server --help` |
| `./bin/novel write 1` | `./bin/noveler write 1` |
| `./bin/novel check 1 --auto-fix` | `./bin/noveler check 1 --auto-fix` |
| `./bin/novel complete-episode 1` | `./bin/noveler mcp call noveler_complete '{"episode_number":1}'` |
| `./bin/novel plot episode 1` | `./bin/noveler mcp call noveler_plot '{"episode_number":1}'` |
| `./bin/novel health check` | `./bin/noveler mcp call status '{}'` |
| `./bin/novel backup ...` | MCPツール `noveler mcp call backup_management '{...}'` |

> 🔁 **ポイント**: 旧CLIで提供されていた詳細オプションは MCP ツールで公開されています。`docs/mcp/tools_usage_best_practices.md` と `src/mcp_servers/noveler/server/noveler_tool_registry.py` を参照すると、利用可能な引数と戻り値を確認できます。

## 3. スクリプト／フックの更新

1. Gitフック (`src/noveler/infrastructure/repositories/git_hook_repository.py`) を `noveler` ベースのコマンドに置き換えます。
   - 品質チェック: `"$GUIDE_ROOT/bin/noveler" check "$file" --auto-fix`
   - プロットバージョン: `"$PYTHON_EXEC" -m noveler.infrastructure.git.hooks.plot_version_post_commit`
   - システム診断: `"$GUIDE_ROOT/bin/noveler" mcp call status '{}'`
2. 独自のスクリプトや CI ジョブに `bin/novel` が残っていないか `rg -n "bin/novel"` で確認します。
3. 互換スクリプトや長期保守ブランチでは、このドキュメントへのリンクを残した上で補足注記を追加してください。

## 4. ドキュメント更新の手順

1. `rg -n "\\bnovel\\b" docs` でヒットする使用例を確認し、現行手順では `noveler` へ差し替えます。
2. 歴史資料 (`docs/archive/**`, `specs/_archive/**`) は直接改変せず、冒頭に「旧CLI表記が残っている」旨の注記を追加する方針です。
3. README や Quick Start では `noveler` の例と `noveler mcp call ...` の呼び出しパターンを掲載し、旧コマンドを参照しないようにします。

## 5. テストと検証

- `pytest tests/integration/test_nih_prevention_integration.py` … Phase2 境界ケースを含むテストを追加し、MCPベースのフローでも最低1件の提案が返ることを確認します。
- `pytest tests/unit/domain/services/test_automatic_recommendation_generator.py` … `extract_common` 戦略と NullLogger フォールバックの挙動をカバーするユニットテストを追加します。
- CLI 動作確認: `./bin/noveler check 1`、`./bin/noveler mcp call status '{}'`、`./bin/noveler mcp call noveler_plot '{"episode_number":1,"regenerate":false}'`

## 6. 開発／配布フロー

1. `make dist` または該当ビルドスクリプトで `src` → `dist` を同期します。
2. `./bin/noveler --version` を実行し、新しい dist が利用されていることを確認します。
3. CI では `NOVELER_TEST_CLEANUP_MODE`・`NOVELER_TEST_CLEANUP_TIMEOUT` を必要に応じて設定し、テスト後にスタブファイルが残らないようにします。

## 7. トラブルシューティング

| 症状 | 対応 |
| --- | --- |
| `noveler: command not found` | `chmod +x bin/noveler` を実行し、シェルのPATHに `bin` を追加する |
| MCPツール呼び出しで JSON エラー | `noveler mcp call <tool> '{"episode_number":1}'` のように単一クォーテーションでJSONをラップする |
| フックから `plot_version_post_commit` が失敗する | `python -m noveler.infrastructure.git.hooks.plot_version_post_commit` を手動実行し、エラー内容を確認 |
| 旧ドキュメントを参照する必要がある | `docs/archive/ARCHIVE_NOTICE.md` を参照し、歴史資料であることを明示 |

---

移行中に不明点があれば `B50_システム運用基礎.md` の「現行CLIチェックリスト」またはこのドキュメントを参照し、必要に応じて TODO.md に追記してください。
