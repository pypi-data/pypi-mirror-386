# Release v2.1.0 (2025-09-21)

- MCP: JSON-RPC入出力の整備（initialize / tools/list / tools/call）とテスト安定化
- B20: 軽量出力原則の既定化（MCP_LIGHTWEIGHT_DEFAULT=1）
  - テスト（pytest 全体）: tests/conftest.py で既定ON
  - 本番CLI: bin/noveler で既定ON
  - CI（CLIスモーク）: cli-smoke.yml の各MCP/CLI呼び出しにenv追加
- Presentationハンドラの軽量整形
  - run_quality_checks / improve_quality_until / fix_quality_issues / export_quality_report
  - format: summary|ndjson|full, page/page_size, metadata.total_issues/returned_issues/pagination/truncated
- Docs: docs/mcp/stdout_safety.md にJSONインタラクション形式（initialize / tools/list / tools/call）を追記
- Tests: 軽量整形・Tool辞書化のユニットテストを追加（最小）

Migration Notes
- 詳細出力が必要な呼び出しは、リクエストに `{"format":"full"}` を明示してください。
- 既定を無効化したい場合は環境変数 `MCP_LIGHTWEIGHT_DEFAULT=0` を指定してください。

Known Notes
- 他のワークフローへの一括env付与は、YAMLの厳格検証に配慮して段階適用予定（テストはconftestで既定ONのため影響なし）。
