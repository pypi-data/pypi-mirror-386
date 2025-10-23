# B20 開発サイクル — 標準ワークフロー（簡易版）

## 3-Commit Cycle
1) RED — 仕様/失敗テストの追加（最小）
2) GREEN — 最小実装でテストを緑にする
3) REFACTOR — 命名/重複/構造の整理（挙動不変）

## 実務チェックリスト
- 影響調査: `scripts/tools/impact_audit.py --pattern "<keyword>" --output temp/impact_audit/<name>.md`
- STDIO方針: MCP_STDIO_SAFE=1（stdoutはMCP専用）
- import方針: importlib 遅延 or 意図コメント（PLC0415 keep with reason）
- テンプレ: `.novelerrc.yaml file_templates` を尊重（Path/Loader経路）
- ドキュメント: README/CHANGELOG/ガイド更新

## PR テンプレ
`.github/PULL_REQUEST_TEMPLATE.md` を利用してください。
