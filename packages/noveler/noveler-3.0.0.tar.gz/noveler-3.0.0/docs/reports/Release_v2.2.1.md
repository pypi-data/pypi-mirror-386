# Release v2.2.1 (2025-09-21)

主要変更
- feat: 十段階ツール登録を共通化する `ten_stage_tool_bindings` モジュールを追加し、`register_ten_stage_tools` / `register_async_ten_stage_tools` を公開。
- refactor: `JSONConversionServer` / `AsyncJSONConversionServer` が新モジュール経由で十段階ツールを登録するよう統一し、サーバークラスの肥大化を抑制。
- test: `tests/integration/mcp/test_mcp_server_integration.py` のレジストリ検証に新モジュールの走査を追加し、登録漏れを検知可能に。
- docs: `TODO.md` の「MCPサーバー 実装分割」残件を完了済みとして整理し、進捗タグを更新。

背景
- 十段階ツールの登録ロジックが同期/非同期サーバー双方で重複しており、300行上限を超えかけていたため、共通ヘルパーに切り出す必要がありました。

実装ハイライト
- `src/mcp_servers/noveler/server/ten_stage_tool_bindings.py` に同期/非同期の登録ヘルパーを集約し、遅延インポートとログ出力を共通化。
- `src/mcp_servers/noveler/json_conversion_server.py` と `src/mcp_servers/noveler/async_json_conversion_server.py` は新ヘルパーを呼び出すだけで十段階ツールを登録できる構成に整理。
- 統合テストではレジストリ抽出後に新モジュール内の `__all__` を走査し、同期/非同期双方の登録漏れを検出するアサーションを追加。

品質確認
- `pytest tests/integration/mcp/test_mcp_server_integration.py::TestMCPServerIntegration::test_ten_stage_writing_system`（十段階ツール登録パターンの検証）

移行影響
- APIのシグネチャや公開ツール名は変更なし。統合テストを通過していれば追加作業は不要です。
