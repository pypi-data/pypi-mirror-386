# 要件ドキュメント概要

小説執筆支援システム「Noveler」の最新実装に基づく要件・分析ドキュメントをまとめています。執筆ワークフロー、品質管理、データ連携、LangSmith連携、運用要件までAs-built情報を網羅しています。

## ディレクトリ構成

```
requirements/
├── requirements_definition.md              # As-built要件定義書（Version 5.1）
├── requirements_traceability_matrix.yaml   # 実装トレーサビリティ（Version 2.1）
├── analysis/
│   ├── analysis_summary.md
│   ├── extracted_requirements.yaml
│   ├── reverse_engineering_completion_report.md
│   └── specification_analysis_report.json
├── tools/
│   ├── specifications_analyzer.py
│   └── quality_assurance_verification_plan.md
└── README.md
```

## 主要ドキュメント

- **requirements_definition.md**
  執筆ワークフロー（15/18ステップ）、MCP段階API、TenStage、会話設計ツール、品質チェック、LangSmith連携、データ/運用要件を要件ID付きで整理したAs-built版要件定義書です。対応する実装・仕様・試験を節ごとに参照できます。

- **requirements_traceability_matrix.yaml**
  執筆ワークフロー、品質管理、データ連携、運用カテゴリに分類した要件IDと、実装モジュール・仕様書・試験ケースをマッピングしたトレーサビリティマトリクスです。

- **specs/SPEC-MCP-002_mcp-tools-specification.md**
  MCPサーバーが提供するツール一覧と入出力仕様を定義した公式仕様書です（`specs/` ディレクトリを参照）。

## 補助資料

- `analysis/` ディレクトリでは自動抽出された要件データと分析レポートを保持しています。
- `tools/` ディレクトリには要件検証に用いるスクリプトおよび品質検証計画がまとまっています。

## 利用ガイド

1. **要件の把握:** `requirements_definition.md` で各要件（REQ-…）の概要・実装・テストを確認します。
2. **整合性確認:** `requirements_traceability_matrix.yaml` で要件IDと実装/試験の対応、カテゴリ別の網羅状況を確認します。
3. **仕様裏付け:** 関連する `specs/` ドキュメントを参照し、ツール入出力やAPI制約を確認します。
4. **品質検証:** `tools/quality_assurance_verification_plan.md` を基に品質検証プロセスを準備し、必要に応じてトレーサビリティのテスト列を参照します。
5. **差分レビュー:** 更新時は下記「整合性チェックリスト」に沿って要件～実装～テストの整合性を検証します。

## 実運用・テスト依存（2025-09-27 更新）

- LangGraph: Progressive Check ワークフローの実行に必須（`NOVELER_LG_PROGRESSIVE_CHECK=1`）。
- pytest-xdist: テスト並列実行に使用（推奨: `bin/test --xdist-auto`）。
- pytest-timeout: ハング防止のためのタイムアウト制御（例: `--timeout=300`）。

## 整合性チェックリスト

- 要件定義書とトレーサビリティマトリクスに同一 `REQ-*` が存在し、タイトル・要約・参照先が一致しているか。
- `src/mcp_servers/noveler/main.py` で登録されているすべてのMCPツールが、いずれかの要件（REQ）に紐づいているか。
- 各要件が指す実装・仕様・試験ファイルが最新のAs-builtコードと一致しているか（例: `tests/integration/mcp/test_progressive_check_mcp_tools.py` など）。
- LangSmith連携、TenStage、設計支援、段階的品質チェック、MCP書き込みツールがテスト/仕様とリンクされているか。
- YAML/Markdown整形が正しく、`yamllint` や `markdownlint` を通過するか。
- 主要テスト（執筆/品質/データ/運用）を必要に応じて実行し、要件更新後も合格することを確認したか。

## 更新情報

- 2025-09-18: 要件IDを明示し、TenStage・設計支援・LangSmith・段階的品質・MCP書き込みツールを文書/マトリクスに反映。整合性チェックリストを追加。
- 2025-09-17: As-built要件定義書（v5.0）とトレーサビリティマトリクス（v2.0）に合わせてREADMEを更新し、MCPツール仕様書を `specs/SPEC-MCP-002_mcp-tools-specification.md` に移管。
- 2025-09-04: MCPツール要件を `requirements_definition_master.md` へ統合（旧構成）。
- 2025-09-03: マスター要件定義書と分析レポートを作成。
