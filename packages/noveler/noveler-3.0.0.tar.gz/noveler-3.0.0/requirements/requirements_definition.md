# 小説執筆支援システム「Noveler」要件定義書（As-built）

**Version**: 5.2 (As-built)
**Last Updated**: 2025-09-18
**Type**: 実装追従版要件定義書

## 📋 目次

1. [システム概要](#1-システム概要)
2. [実装済み機能サマリー](#2-実装済み機能サマリー)
3. [執筆ワークフロー要件](#3-執筆ワークフロー要件)
4. [品質管理要件](#4-品質管理要件)
5. [データ管理・連携要件](#5-データ管理連携要件)
6. [関連文書・テスト](#6-関連文書テスト)
7. [更新履歴](#7-更新履歴)

---

## 1. システム概要

### 1.1 目的
Web小説投稿向けの段階的プロット作成・原稿生成・品質確認・成果物管理を自動化し、執筆作業とレビュー作業を一貫して支援する。

### 1.2 提供面
- `bin/noveler` と `src/noveler/presentation/cli/cli_adapter.py` を中心としたローカルCLI。
- `src/mcp_servers/noveler/main.py` が提供するFastMCPサーバー（執筆・品質・ファイル操作ツール群）。
- `src/noveler/infrastructure/json/mcp/servers/json_conversion_server.py` によるJSON変換/キャッシュ/パフォーマンス最適化サーバー。
- `src/noveler/application`・`src/noveler/domain` 層に実装されたユースケース・ドメインサービス群。

### 1.3 想定利用者
- 小説連載者・投稿者（執筆/推敲の自動化）。
- 品質チェック担当者・レビュアー。
- CI・自動試験環境（FastMCP経由でのセッション制御と結果収集）。

---

## 2. 実装済み機能サマリー

| 領域 | 主な実装 | 主な試験 |
|------|----------|---------|
| CLIエントリ | `bin/noveler`, `src/noveler/presentation/cli/cli_adapter.py` | `tests/unit/presentation/cli/test_cli_adapter.py` |
| 統合執筆ユースケース（18ステップ） | `src/noveler/application/use_cases/integrated_writing_use_case.py`, `src/noveler/application/use_cases/enhanced_integrated_writing_use_case.py` | `tests/integration/test_integrated_writing_workflow.py` |
| 15ステップ段階執筆 | `src/noveler/application/use_cases/stepwise_writing_use_case.py`, `src/noveler/domain/services/writing_steps/` | `tests/test_stepwise_writing_system.py` |
| 段階制御／テンプレート | `src/noveler/domain/services/progressive_task_manager.py`, `templates/` | `tests/test_progressive_execution_control.py` |
| MCPツールハブ | `src/mcp_servers/noveler/main.py`, `src/mcp_servers/noveler/tools/` | `tests/e2e/test_quality_workflow_e2e.py`, `tests/integration/mcp/test_mcp_server_integration.py` |
| JSON変換・ファイル管理 | `src/noveler/infrastructure/json/mcp/servers/json_conversion_server.py`, `src/noveler/infrastructure/json/converters/cli_response_converter.py` | `tests/test_json_server_performance.py` |

---

## 3. 執筆ワークフロー要件

### 3.1 15ステップ段階執筆（StepwiseWritingUseCase） *(REQ-WRITE-STEPWISE-002)*
**Requirement Summary:** A38準拠15ステップ構造をユースケースとして提供し、キャッシュや並列実行制御を備えた段階執筆を実現する。

`src/noveler/application/use_cases/stepwise_writing_use_case.py` は 15ステップを順次または依存関係を保った並列で実行する。主なステップは以下。

| Step | 実装クラス | 主な目的 |
|------|-----------|---------|
| 0 scope_definer | `src/noveler/domain/services/writing_steps/scope_definer_service.py` | エピソードスコープと目標設定 |
| 1 story_structure | `src/noveler/domain/services/writing_steps/story_structure_designer_service.py` | 骨格・章構成の定義 |
| 2 phase_structure | `src/noveler/domain/services/writing_steps/phase_structure_designer_service.py` | 段階構造の詳細化 |
| 3 theme_uniqueness | `src/noveler/domain/services/writing_steps/theme_uniqueness_validator_service.py` | テーマ独自性と整合性検証 |
| 4 section_balance | `src/noveler/domain/services/writing_steps/section_balance_optimizer_service.py` | 導入/展開/解決バランス最適化 |
| 5 scene_designer | `src/noveler/domain/services/writing_steps/scene_designer_service.py` | シーン構成とビート配置 |
| 6 logic_validator | `src/noveler/domain/services/writing_steps/logic_validator_service.py` | 因果・論理整合性チェック |
| 7 character_consistency | `src/noveler/domain/services/writing_steps/character_consistency_service.py` | キャラクターの一貫性維持 |
| 8 dialogue_designer | `src/noveler/domain/services/writing_steps/dialogue_designer_service.py` | 会話構造・目的設計 |
| 9 emotion_curve | `src/noveler/domain/services/writing_steps/emotion_curve_designer_service.py` | 感情曲線・緊張緩和制御 |
| 10 scene_setting | `src/noveler/domain/services/writing_steps/scene_setting_service.py` | 世界観・場面設定の具体化 |
| 11 manuscript_generator | `src/noveler/domain/services/writing_steps/manuscript_generator_service.py` | YAMLテンプレートから原稿下書き生成 |
| 12 props_world_building | `src/noveler/domain/services/writing_steps/props_world_building_service.py` | 小道具・設定の整備 |
| 13 manuscript_generator (revision) | `src/noveler/domain/services/writing_steps/manuscript_generator_service.py` | 中間稿の再生成と統合 |
| 14 text_length_optimizer | `src/noveler/domain/services/writing_steps/text_length_optimizer_service.py` | 文字数・ボリューム調整 |
| 15 readability_optimizer | `src/noveler/domain/services/writing_steps/readability_optimizer_service.py` | 可読性最適化 |
| 16 quality_gate | `src/noveler/domain/services/writing_steps/quality_gate_service.py` | 最低品質ゲートの通過判定 |
| 17 quality_certification | `src/noveler/domain/services/writing_steps/quality_certification_service.py` | 品質証明と承認 |
| 18 publishing_preparation | `src/noveler/domain/services/writing_steps/publishing_preparation_service.py` | 公開準備・スケジュール確定 |

補足要件:
- `StepwiseWritingRequest` が `step_pattern`（例: `"all"`, `"0-5"`, `"structure"`）、`resume_from_cache`、`parallel_execution`、`generate_reports` 等の制御を提供。
- `WorkFileManager` と `StepOutputManager` が各ステップ結果をキャッシュし、再実行時の復元とレポート生成をサポート。
- 検証済み試験: `tests/test_stepwise_writing_system.py`。

### 3.2 18ステップ統合執筆（CLI `noveler write`） *(REQ-WRITE-CLI-001)*
**Requirement Summary:** 18ステップ統合ワークフローをCLIとMCP経由で提供し、失敗時にはフォールバック原稿とログを自動生成する。

`src/noveler/presentation/cli/cli_adapter.py` 内の `execute_18_step_writing` は以下のステップを所定フェーズで実行する（0〜18）。Step11で `UniversalClaudeCodeService` を介したClaude連携を行い、`EnhancedFileManager` と `LLMIOLogger` が成果物・IOログを保存する。

0. スコープ定義（構造設計）
1. 大骨（章の目的線）
2. 中骨（段階目標）
3. テーマ性・独自性検証
4. セクションバランス設計
5. 小骨（シーン／ビート）
6. 論理検証
7. キャラクター一貫性検証
8. 会話設計
9. 感情曲線
10. 世界観設計
11. 初稿生成（執筆実装、Claude呼び出し）
12. 文字数最適化
13. 文体・可読性パス
14. 必須品質ゲート
15. 最終品質認定
16. 公開準備
17. 仕上げ
18. 最終確認

エラー時はフォールバック原稿を生成し、全結果を `temp/json_output/` にJSON形式で保存。CLIからの起動は `noveler write <episode>`、MCP経由の直接操作は `noveler mcp call enhanced_execute_writing_step {...}` で検証済み（`tests/integration/test_integrated_writing_workflow.py`, `tests/unit/presentation/cli/test_cli_adapter.py`）。

### 3.3 MCP段階実行API *(REQ-WRITE-MCP-003)*
**Requirement Summary:** MCP経由で段階タスクの一覧取得・実行・復旧を制御し、LLM向けプロンプトテンプレートと進捗管理を統合する。

`src/mcp_servers/noveler/main.py` は段階制御用ツールを提供する。

- `get_writing_tasks` / `execute_writing_step` / `get_task_status` が `ProgressiveTaskManager`（`src/noveler/domain/services/progressive_task_manager.py`）と連携し、プロンプトテンプレート（`templates/`）からLLM向け指示を生成。
- エラー復旧と非同期制御を備えた `enhanced_get_writing_tasks` / `enhanced_execute_writing_step` / `enhanced_resume_from_partial_failure` が同一ユースケースを拡張し、診断ログと再試行ポイントを返却。
- `noveler_write`, `noveler_plot`, `status` などの互換ツールでCLI互換操作をMCP経由に公開。
- 検証済み試験: `tests/test_progressive_execution_control.py`, `tests/integration/mcp/test_progressive_check_mcp_tools.py`（復旧シナリオの検証を含む）。

### 3.4 10段階MCPツール（TenStageWriting） *(REQ-WRITE-TEN-004)*
**Requirement Summary:** TenStage構成の書き分けツールをMCPで提供し、セッション管理・段階別タイムアウト・JSON成果物保存を保証する。

- `src/mcp_servers/noveler/json_conversion_server.py` が `write_step_1`〜`write_step_10` を登録し、各ステップを300秒タイムアウトで個別実行。
- `TenStageSessionManager`（`noveler.infrastructure.services.ten_stage_session_manager`）がセッションファイルを `90_管理/writing_sessions/` に保存し、`write_resume` コマンドから復旧可能。
- 実行結果は `CLIResponseConverter` 経由でファイル参照付きJSONとして保存され、MCPツール `get_file_reference_info` や `list_files_with_hashes` から取得可能。
- 仕様参照: `specs/SPEC-MCP-001_mcp-tool-integration-system.md`, `specs/SPEC-MCP-002_mcp-tools-specification.md`。
- 検証済み試験: `tests/integration/mcp/test_mcp_server_integration.py`（ツール登録/セッション管理）、`tests/integration/mcp/test_progressive_check_mcp_tools.py`（段階実行シナリオ）。

### 3.5 執筆設計支援ツール（会話/感情/情景/小道具） *(REQ-WRITE-DESIGN-005)*
**Requirement Summary:** A38ガイドSTEP7-11に対応した設計支援ツールを提供し、会話ID体系を通じて情緒・舞台・小道具を整合させる。

- `ConversationDesignTool`（`src/mcp_servers/noveler/tools/conversation_design_tool.py`）が `design_conversations`, `track_emotions`, `design_scenes`, `design_senses`, `manage_props`, `get_conversation_context`, `export_design_data` を提供。
- 会話ID (`EP{episode}_SC{scene}_DL{dialogue}`) をキーに感情・情景・小道具を関連付け、`export_design_data` で統合JSONを出力。
- 実装は `ConversationDesignService`（`src/noveler/domain/services/conversation_design_service.py`）と `create_path_service` を利用し、成果物は `.noveler/design/` 系ディレクトリへ保存。
- 検証済み試験: `tests/unit/domain/services/test_conversation_design_service.py`（ドメインロジック）、`tests/integration/mcp/test_mcp_server_integration.py`（ツール登録）。
- 仕様参照: `specs/SPEC-MCP-002_mcp-tools-specification.md`（会話設計ツール群セクション）。

---

## 4. 品質管理要件

### 4.1 統合品質チェック *(REQ-QUALITY-001)*
**Requirement Summary:** リズム・可読性・文法・スタイルの各アスペクトを統合し、安定識別子付きの結果とスコアを返却する品質チェックを提供する。

- `run_quality_checks`（`src/mcp_servers/noveler/tools/run_quality_checks_tool.py`）が複数アスペクトを統合し、問題一覧・スコア・推奨修正を返却。
- `aspects`/`preset`/`thresholds`/`weights`/`page`/`page_size` 等のパラメータで抽出範囲と重みを制御。
- 各アスペクトは `CheckRhythmTool` / `CheckReadabilityTool` / `CheckGrammarTool` / `CheckStyleTool`（`src/mcp_servers/noveler/tools/`）に委譲。
- 検証済み試験: `tests/e2e/test_quality_workflow_e2e.py`、`tests/integration/mcp/test_progressive_check_mcp_tools.py`（品質アスペクトの整合性確認）。

### 4.2 段階的品質チェックMCPフロー *(REQ-QUALITY-STAGED-004)*
**Requirement Summary:** MCP経由で品質チェックの段階タスクを案内し、実行履歴と復旧ポイントを管理する段階的フローを提供する。

- `get_check_tasks` / `execute_check_step` / `get_check_status` / `get_check_history` が `ProgressiveCheckManager`（`src/noveler/domain/services/progressive_check_manager.py`）へ委譲し、LangGraph ワークフロー上で 12 段階のチェックを段階的に実行。`get_check_tasks` はセッション初期化と `session_id` 付与を兼ねる。
- `check_basic` ツールが CLI `noveler check --basic` をMCP互換で呼び出し、チェックガイダンスとの互換性を担保。未実装の `progressive_check.*` が呼ばれた場合は `get_tasks` 利用を案内するガイダンスメッセージを返却する。
- 仕様参照: `specs/SPEC-QUALITY-110_progressive_check_flow.md`, `specs/SPEC-QUALITY-120_langgraph_workflow_state_management.md`。
- 検証範囲: `tests/integration/mcp/test_progressive_check_mcp_tools.py`, `tests/unit/domain/services/test_progressive_check_manager_compliance.py` に加え、`.noveler/checks/<session_id>/` ログ生成を検証する新規ユニットテスト（temp dir 利用）を追加しCIへ組み込む。

### 4.3 品質改善とレポーティング *(REQ-QUALITY-002)*
**Requirement Summary:** 品質改善の反復実行・安全修正・品質データのエクスポート/参照を提供する。

- `improve_quality_until` が目標スコア到達までの反復改善を実行、`fix_quality_issues` が安全フィックス（約物統一・スペース/括弧の微修正等）を適用。
- 日本語文に対する自動改行および行幅警告は全サブコマンドから撤廃されており、`--auto-fix` 実行で新規ハード改行は一切挿入されない（冪等性保証）。
- `export_quality_report`, `list_quality_presets`, `get_quality_schema`, `test_result_analysis` が品質結果の保存、プリセット参照、テスト結果解析を提供。
- CLI `noveler check`（`cli_adapter.py`）は `execute_run_quality_checks` → `execute_improve_quality_until`（失敗時は `execute_fix_quality_issues`）→再測定の順に呼び出す。
- 検証済み試験: `tests/e2e/test_quality_workflow_e2e.py`, `tests/unit/presentation/cli/test_cli_adapter.py`。

### 4.4 LangSmith連携／バグ修正フロー *(REQ-QUALITY-LANG-005)*
**Requirement Summary:** LangSmithの run.json から成果物生成・パッチ適用・検証コマンド実行までの自動化フローを提供する。

- `langsmith_generate_artifacts`, `langsmith_apply_patch`, `langsmith_run_verification` が LangSmith成果物を `reports/langsmith/` に生成し、パッチ適用と検証結果を集約。
- `LangSmithBugfixWorkflowService`（`noveler.application.services.langsmith_bugfix_workflow_service`）と `LangsmithArtifactManager` がアーティファクト管理を担当。
- 仕様参照: `specs/SPEC-MCP-002_mcp-tools-specification.md`（LangSmithセクション）。
- 検証済み試験: `tests/unit/application/services/test_langsmith_bugfix_workflow_service.py`, `tests/unit/infrastructure/services/test_langsmith_artifact_manager.py`, `tests/unit/tools/test_langsmith_bugfix_helper_cli.py`。

### 4.5 適応的品質評価 *(REQ-QUALITY-003)*
**Requirement Summary:** ジャンル別基準と執筆進捗に基づく適応的品質評価をDDD準拠で実装し、結果をMCP/CLI双方で提供する。

- `AdaptiveQualityEvaluator`（`src/noveler/application/use_cases/adaptive_quality_evaluation_use_case.py`）がジャンル別基準と執筆進捗を元に評価結果を算出。
- DDD準拠での設計が `tests/test_ddd_compliance_adaptive_quality.py` で検証済み。
- 仕様参照: `specs/SPEC-QUALITY-019_adaptive_quality_evaluation.md`。

---

## 5. データ管理・連携要件

### 5.1 JSON変換とパフォーマンス最適化 *(REQ-DATA-001)*
**Requirement Summary:** CLI/MCP実行結果をファイル参照付きJSONとして保存し、キャッシュや最適化を適用する。

- `JSONConversionServer`（`src/noveler/infrastructure/json/mcp/servers/json_conversion_server.py`）が `FileIOCache`, `ComprehensivePerformanceOptimizer` を備え、CLI結果を `StandardResponseModel` / `ErrorResponseModel` へ変換。
- `CLIResponseConverter`（`src/noveler/infrastructure/json/converters/cli_response_converter.py`）がMarkdown/YAML/JSONをファイル参照化し、メタデータとともに `temp/json_output/` に保存。
- 検証済み試験: `tests/test_json_server_performance.py`、`tests/integration/mcp/test_mcp_server_integration.py`。

### 5.2 ファイル参照とハッシュ *(REQ-DATA-002)*
**Requirement Summary:** SHA256によるファイル追跡・変更検知を提供し、MCPツール群から参照可能にする。

- `get_file_reference_info`, `get_file_by_hash`, `check_file_changes`, `list_files_with_hashes` が `src/mcp_servers/noveler/json_conversion_adapter.py` および `src/noveler/infrastructure/json/file_managers/file_reference_manager.py` を通じて提供。
- ハッシュ管理は `src/noveler/infrastructure/json/utils/hash_utils.py` で実装され、CLI/MCPから統一的に利用。
- 検証済み試験: `tests/test_hash_functionality.py`, `tests/unit/infrastructure/json/test_hash_file_manager.py`。

### 5.3 アーティファクト・バックアップ *(REQ-DATA-003)*
**Requirement Summary:** `.noveler/artifacts/` へのアーティファクト保管とバックアップ作成/復元機能を提供する。

- `fetch_artifact`, `list_artifacts`, `backup_management` が `src/mcp_servers/noveler/main.py` と `src/noveler/domain/services/artifact_store_service.py` で実装。
- バックアップは日付・ハッシュ付きディレクトリ構造で保存し、`backup_management` が作成・一覧・削除・復元を制御。
- 検証済み試験: `tests/e2e/test_quality_workflow_e2e.py`, `tests/integration/mcp/test_mcp_server_integration.py`。

### 5.4 直接ファイル操作（MCP書き込みツール） *(REQ-OPS-WRITE-001)*
**Requirement Summary:** MCPクライアントからのファイル書き込みを、安全なルート解決とディレクトリ作成を伴って提供する。

- `write` ツール (`src/mcp_servers/noveler/main.py`) が `execute_write_file` を通じてプロジェクトルート相対パスへ書き込みを実行。`create_path_service` により正規化されたルートを採用し、存在しないディレクトリは安全に作成。
- 書き込み結果は absolute/relative path、内容サイズ、使用ルートを返却し、MCPクライアントでの差分適用に用いる。
- 仕様参照: `specs/SPEC-MCP-001_mcp-tool-integration-system.md`（mcp__noveler__noveler_write セクション）。
- 検証済み試験: `tests/integration/mcp/test_mcp_server_integration.py`（ツール登録）、`tests/integration/mcp/test_mcp_server_compliance.py`（セッション制御・安全ガード確認）。

---

## 6. 関連文書・テスト

| 領域 | 仕様・補足 | 試験 |
|------|-----------|------|
| 段階執筆（15/18ステップ） | `specs/SPEC-WRITE-015_stepwise_writing_use_case.md`, `specs/SPEC-WRITE-018_integrated_writing_flow.md` | `tests/test_stepwise_writing_system.py`, `tests/integration/test_integrated_writing_workflow.py` |
| MCP段階制御 | `specs/SPEC-MCP-001_mcp-tool-integration-system.md` | `tests/test_progressive_execution_control.py`, `tests/integration/mcp/test_progressive_check_mcp_tools.py` |
| TenStage & 設計支援ツール | `specs/SPEC-MCP-002_mcp-tools-specification.md` | `tests/integration/mcp/test_mcp_server_integration.py`, `tests/unit/domain/services/test_conversation_design_service.py` |
| 品質チェック & 段階的フロー | `specs/SPEC-MCP-PROGRESSIVE-CHECK-001`, `specs/SPEC-A40A41-STAGE1-AUTOFIX.md`, `specs/SPEC-A40A41-STAGE23-POLISH.md` | `tests/e2e/test_quality_workflow_e2e.py`, `tests/integration/mcp/test_progressive_check_mcp_tools.py` |
| LangSmith連携 | `specs/SPEC-MCP-002_mcp-tools-specification.md`（LangSmithセクション） | `tests/unit/application/services/test_langsmith_bugfix_workflow_service.py`, `tests/unit/infrastructure/services/test_langsmith_artifact_manager.py` |
| JSON変換／ファイル参照 | `specs/SPEC-DATA-001_json_conversion_pipeline.md` | `tests/test_json_server_performance.py` |
| アーティファクト／バックアップ | `specs/SPEC-ARTIFACT-001-artifact-reference-system.md` | `tests/e2e/test_quality_workflow_e2e.py` |

---

## 7. 更新履歴

| Version | Date | Changes |
|---------|------|---------|
| 5.2 | 2025-09-18 | 仕様更新: 日本語文に対する強制改行・行幅警告を全サブコマンドから撤廃（`--auto-fix`で改行を挿入しない方針を明文化） |
| 5.1 | 2025-09-18 | 要件ID明示化、TenStage/設計支援/段階的品質/ LangSmith/書き込みツール要件を追加し、トレーサビリティ整合を確立 |
| 5.0 | 2025-09-17 | As-built更新: 段階執筆フローを実装内容に合わせて再整理、MCPツールと品質/データ要件を現行コードに同期 |
| 4.0 | 2025-09-05 | 統合版ドラフト（旧10段階構成ベース） |
| 3.0 | 2025-09-05 | ワークフロー中心構成に改訂 |
| 2.0 | 2025-09-05 | LLM最適化版（旧仕様） |
| 1.0 | 2025-09-04 | 初版作成 |
