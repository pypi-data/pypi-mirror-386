# Release v2.2.7 (2025-09-21)

## 主要変更
- MCPサーバー実装を `noveler.presentation.mcp.server_runtime` に移管し、`mcp_servers/noveler/main.py` は薄い互換ラッパーへ統一。Composition Root が明確化し、層境界の監視を importlinter 契約で自動化しました。
- `GRAMMAR_PUNCTUATION` オートフィクスの分割ロジックを改良。助動詞・接続詞を用いた境界スコアリングと語尾ベースのフォールバックを導入し、長文への句点挿入や会話行の安全性を高めました。
- SPEC-901 信頼性向上の第一段階として、MessageBus に Outbox / Idempotency のファイルベース実装を追加。イベントは `<project>/temp/outbox/` に保存され、冪等キーでコマンドの重複実行を抑止できます。
- `noveler check` 互換レイヤーを調整し、`--exclude-dialogue` フラグを安定動作させつつ軽量出力設定との連携を検証しました。
- `make ci-smoke` に polish/apply/restore/write/list_artifacts の最小経路を追加し、MCP ツール群の基本動作を自動確認できるようにしました。

## 影響範囲
- 既存の `mcp_servers.noveler.main` import は互換維持。CLI やテストコードの呼び出し方法は従来通り利用できます。
- `fix_quality_issues` の挙動は安全性向上のみで、既存の reason code や入力フォーマットに互換性があります。
- CI スモークで追加の MCP 呼び出しが実行されるため、テスト用データ (`temp/test_data/40_原稿/第001話_スモークテスト.md`) が必要です。

## テスト
- `pytest tests/unit/mcp_servers/tools/test_fix_quality_issues_grammar.py`
- `pytest tests/unit/presentation/cli/test_cli_adapter.py::test_check_command_success_exit_code`
- `pytest tests/e2e/test_stage1_autofix_e2e.py`
