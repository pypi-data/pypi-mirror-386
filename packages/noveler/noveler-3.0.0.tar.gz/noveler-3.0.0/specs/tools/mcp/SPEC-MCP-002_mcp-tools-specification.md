---
spec_id: SPEC-MCP-002
status: canonical
owner: bamboocity
last_reviewed: 2025-09-27
category: MCP
tags: [mcp, tools]
requirements:
  - REQ-WRITE-MCP-003
  - REQ-WRITE-TEN-004
  - REQ-WRITE-DESIGN-005
  - REQ-QUALITY-001
  - REQ-QUALITY-002
  - REQ-QUALITY-STAGED-004
  - REQ-QUALITY-LANG-005
  - REQ-DATA-001
  - REQ-DATA-002
  - REQ-DATA-003
  - REQ-OPS-WRITE-001
---
# SPEC-MCP-002: MCPツール仕様書

**Version**: 2.2.0
**Last Updated**: 2025-09-18
**Status**: 実装完了・運用中

## 1. 概要

### 1.1 目的
小説執筆支援システム「Noveler」の FastMCP サーバーが公開するツール群の仕様を定義する。段階執筆（TenStage/18ステップ）、品質評価・改善、設計支援、LangSmith連携、データ・運用ツールまでを網羅し、要件定義書 v5.1 および REQ-WRITE/QUALITY/DATA/OPS 系要件に対する準拠を保証する。

### 1.2 システム位置付け
- MCPサーバー実装: `src/mcp_servers/noveler/main.py`
- JSON変換サーバー: `src/noveler/infrastructure/json/mcp/servers/json_conversion_server.py`
- TenStageセッション管理: `noveler.infrastructure.services.ten_stage_session_manager`
- 設計支援サービス: `noveler.domain.services.conversation_design_service`
- LangSmithワークフロー: `noveler.application.services.langsmith_bugfix_workflow_service`

### 1.3 共通仕様
- **タイムアウト**: 各ツールは既定で 300 秒。長時間処理はステップ分割または再開 API を提供。
- **入出力形式**: JSON Schema 互換の辞書構造。ファイル参照は SHA256 ハッシュと相対パスを併記。
- **セッション管理**: TenStage/品質段階ツールは session_id による継続実行と中断復旧をサポート。
- **ログ/監査**: すべてのツールは UnifiedLogger を使用し、`temp/json_output/` や `.noveler/` 以下に成果物を保存。
  
（新）**サービス層契約**:
1. FastMCP ツール登録クラスは、すべて専用 `ToolService` 経由で実行する（直接 UseCase を呼ばない）。
2. 入力/出力は DTO として定義し、必要に応じて JSON Schema にエクスポートする。
3. 例外は `ToolServiceError`（`message`, `reason`, `hint`, `error_type`, `details?`）に正規化し、標準レスポンスへ変換する。

### 1.4 CLI 役割分離（チェック vs 改稿）
- `noveler check`: 品質評価専用。`run_quality_checks`/`improve_quality_until` 等のラッパーとして動作し、原稿書き換えは行わない。
- `noveler polish`: Stage2/Stage3 改稿導線。`polish_manuscript`/`polish_manuscript_apply` をラップし、`dry_run` で適用制御する。
- 両導線とも ProgressiveCheckManager をハブとし、テンプレロード順（`templates/quality/checks/` → `backup/` → `templates/writing/`）と I/O ログ方針（`.noveler/checks/` 保存）を共有する。

## 2. 執筆実行ツール (REQ-WRITE-MCP-003 / REQ-WRITE-TEN-004)

| ツール名 | 主用途 | 主な入力 | 出力/副作用 | 備考 |
| --- | --- | --- | --- | --- |
| `get_writing_tasks` | 18ステップ進行タスク一覧 | `episode_number`, `project_root?` | タスクリスト（step_id, 指示, 依存） | ProgressiveTaskManager 連携 |
| `execute_writing_step` | 18ステップ個別実行 | `episode_number`, `step_id`, `project_root?`, `dry_run?` | 実行結果、次ステップ | 失敗時はステータスを保持 |
| `get_task_status` | 進捗照会 | `episode_number` | 完了/残タスク、診断情報 | |
| `enhanced_get_writing_tasks` | エラーハンドリング強化版 | 上記+ `diagnostics` | 状態/リカバリ推奨 | 非同期情報を含む |
| `enhanced_execute_writing_step` | 非同期/再試行版実行 | 上記+ `async` オプション | 実行結果、fallback 情報 | Path fallback events を返却 |
| `enhanced_resume_from_partial_failure` | 中断復旧 | `episode_number`, `recovery_point`, `project_root?` | 再開結果、残タスク | 失敗ステップから再実行 |
| `write_stage` | TenStage 特定段階実行 | `episode_number`, `stage`(1-10), `session_id?` | ステージ結果、次候補 | |
| `write_resume` | TenStage セッション再開 | `episode_number`, `session_id` | 再開成否、次ステージ | |
| `write_step_1`〜`write_step_10` | TenStage 個別実行 | `episode`, `session_id?`, パラメータ | 各段階の成果物（プロット/会話/原稿等） | 300秒タイムアウト、結果は `temp/json_output/`|
| `write` | 10段階フル実行 | `episode`, `project_root?` | 最終原稿、品質レポート | CLI向けエイリアス |

（付記）サービス実装責務:
- `get_writing_tasks`/`execute_writing_step`/`get_task_status` は `WritingWorkflowToolService` が担当。
- `write`/`write_stage`/`write_resume` は `TenStageToolService` が担当。

*セッションファイル構造* (`90_管理/writing_sessions/session_{id}.json`):
```json
{
  "session_id": "EP001_20250918_120001",
  "episode": 1,
  "stages": {
    "plot_data_preparation": {"output_path": "...", "completed_at": "..."},
    "emotional_relationship": {...}
  },
  "status": "in-progress",
  "last_updated": "2025-09-18T03:21:00Z"
}
```

## 3. 設計支援ツール (REQ-WRITE-DESIGN-005)

| ツール名 | 主用途 | 主な入力 | 出力 |
| --- | --- | --- | --- |
| `design_conversations` | 会話構造設計 (STEP7) | `episode_number`, `scene_number`, `dialogues[]`(speaker, text, trigger_id, purpose 等) | シーンID, 会話IDレンジ, 正規化済みダイアログ |
| `track_emotions` | 感情曲線追跡 | `emotions[]`(trigger_id, viewpoint, before_level 等) | 感情ポイント集計、追跡数 |
| `design_scenes` | 情景・時間管理 | `scenes[]`(scene_id, location, dialogue_range 等) | 登録シーン数、位置情報 |
| `design_senses` | 五感描写設計 | `triggers[]`(sense_type, description, timing 等) | 感覚トリガー出力 |
| `manage_props` | 小道具ライフサイクル管理 | `props[]`(prop_id, introduced, used, stored 等) | 小道具配列、出現履歴 |
| `get_conversation_context` | 会話IDから周辺情報取得 | `conversation_id` | 直近の会話・感情・情景トレース |
| `export_design_data` | 設計データ一括エクスポート | `episode_number` | `.noveler/design/{episode}/design.json` 等のパス |

- 全ツールは ConversationID (`EP{episode:03d}_SC{scene:02d}_DL{dialogue:03d}`) をキーに整理。
- 出力は `.noveler/design/` 配下に保存し、`FileIOCache` で再利用可能。

## 4. 品質チェック・改善ツール (REQ-QUALITY-001/002)

| ツール名 | 主用途 | 主な入力 | 主な出力 |
| --- | --- | --- | --- |
| `run_quality_checks` | 複合品質チェック | `episode_number`, `aspects?`, `preset?`, `thresholds?` | 問題リスト（安定ID付き）、総合スコア |
| `check_rhythm` / `check_readability` / `check_grammar` / `check_style` | 個別アスペクト評価 | 原稿パス/テキスト、`preset?` | 各アスペクトのスコア、指摘一覧 |
| `improve_quality_until` | スコア目標まで改善 | `episode_number`, `target_score`, `max_iterations?` | 改善ログ、到達スコア |
| `fix_quality_issues` | 安全な修正適用 | `episode_number`, `operations?` | 修正結果、適用概要 |
| `fix_style_extended` | style拡張修正（opt-in） | `episode_number`, `fullwidth_space_mode?`, `brackets_fix_mode?`, `dry_run?` | 修正差分、変更件数、ファイル更新状況 |
| `export_quality_report` | 品質レポート生成 | `episode_number`, `format?` | `reports/quality/{episode}/report.json|md` |
| `list_quality_presets` / `get_quality_schema` | プリセット/スキーマ参照 | `preset?` | プリセット一覧 / JSON Schema |
| `test_result_analysis` | テスト結果要約 | `run_path?`, `gist?` | エラー分類、再現用コマンド |
| `get_issue_context` | 指摘箇所の上下文取得 | `issue_id`, `episode_number` | 原稿抜粋、提案改善ポイント |
| `polish_manuscript` / `polish_manuscript_apply` / `polish` / `restore_manuscript_from_artifact` | 仕上げ・ロールバック操作 | 原稿ID、artifact_id、 `dry_run?`, `save_report?`, `stages?` | 改稿結果、復元結果 |

品質関連成果物は `50_管理資料/品質記録/` および `.noveler/quality/` に格納。LangSmith連携と連動する場合は #5 を参照。

### 4.1 LLM統合パターン（SPEC-LLM-001準拠）

**対象ツール**: `polish_manuscript_apply`, `polish_manuscript`等のLLM実行ツール

**統合仕様**:
- **プロンプト外部化**: LLM入力は `templates/quality/checks/` 直下のテンプレートを読み込んで生成（A40 Stage2/3 は MD ファイル）。
- **LLM実行**: UniversalLLMUseCase経由の統一実行パターン
- **MCP対応**: 自動フォールバック機能による確実な環境対応。フォールバックが発生した場合、ツールは改稿適用をスキップし、元原稿を保持する。
- **廃止済みパラメータ**: `force_llm` は v3.0.0 で完全削除済み。外部LLM強制は `.novelerrc.yaml` や環境変数で制御する。

### 4.2 ProgressiveCheck 反復API（追加）

12ステップ品質チェックを段階実行・反復制御する MCP API。役割はライトウェイト系（`run_quality_checks`/`improve_quality_until`）と分離する。

| ツール名 | 入力 | 出力 | 備考 |
| --- | --- | --- | --- |
| `progressive_check.start_session` *(deprecated)* | `-` | `-` | 呼び出された場合は 400 系レスポンスで `"use progressive_check.get_tasks"` を案内する |
| `progressive_check.get_tasks` | `{episode_number, session_id?}` | `{session_id, episode_number, current_step, current_task, executable_tasks, progress, llm_instruction, next_action, phase_info}` | セッション初期化兼タスク一覧取得（LangGraph ワークフロー起動） |
| `progressive_check.execute_step` | `{session_id, step_id, input_data?, iteration_policy?, llm_overrides?}` | `{success, execution_result, artifacts, passed?, next_step?, manuscript_fetch_log?}` | 単一ステップ実行（available_tools/ハッシュ参照対応） |
| `progressive_check.repeat_step` | `{session_id, step_id, iteration_policy}` | `{success, final_result, attempts, stopped_reason}` | 反復ポリシーに従って再実行 |
| `progressive_check.get_status` | `{episode_number, session_id?}` | `{session_id, current_step, completed_steps, failed_steps, progress, manifest?, locks?}` | 進捗・状態 |
| `progressive_check.list_artifacts` | `{session_id}` | `{artifacts}` | アーティファクト参照 |
| `progressive_check.end_session` | `{session_id, finalize?}` | `{success, closed}` | セッション終了 |

IterationPolicy/manifest/エラーコード（QC-006～008）は `SPEC-QUALITY-110` を参照。


**代替制御方法**:
```yaml
# .novelerrc.yaml
llm_execution:
  respect_mcp_environment: false  # MCP環境判定を無視
  fallback_enabled: true          # フォールバック有効

# 環境変数
NOVELER_FORCE_EXTERNAL_LLM=true  # 外部LLM強制使用
```

### 4.1 fix_style_extended 詳細仕様

**目的**: FULLWIDTH_SPACE正規化とBRACKETS_MISMATCH自動補正によるテキスト品質向上（opt-in機能）

**入力パラメータ**:
```json
{
  "episode_number": 1,
  "project_name": "string?",
  "file_path": "string?",
  "content": "string?",
  "fullwidth_space_mode": "disabled|normalize|remove|dialogue_only|narrative_only",
  "brackets_fix_mode": "disabled|auto|conservative",
  "dry_run": true
}
```

**機能詳細**:
1. **FULLWIDTH_SPACE正規化**:
   - `normalize`: 全角スペース（　）→半角スペース（ ）変換
   - `remove`: 全角スペース除去
   - `dialogue_only`: 台詞内（「」『』内）のみ処理
   - `narrative_only`: 地の文（台詞外）のみ処理

2. **BRACKETS_MISMATCH自動補正**:
   - 対象括弧: 「」『』（）【】〈〉《》〔〕
   - `conservative`: 3個以下の差異のみ修正（安全重視）
   - `auto`: より積極的な修正

**出力例**:
```json
{
  "success": true,
  "message": "style拡張処理が完了しました。2件の変更を実行しました。",
  "metadata": {
    "changes_made": 2,
    "changes_detail": ["行15: 全角スペース処理 (normalize)", "括弧補正: 」 を 1 個追加"],
    "diff": "--- original\n+++ modified\n@@ -15,1 +15,1 @@\n-「こんにちは　世界」\n+「こんにちは 世界」\n",
    "dry_run": true,
    "fullwidth_mode": "normalize",
    "brackets_mode": "conservative",
    "file_path": "/path/to/episode.md"
  }
}
```

**安全性設計**:
- デフォルト `dry_run=true` で差分表示のみ
- すべての機能がデフォルト無効（明示的指定必要）
- 詳細な変更ログと差分表示

## 5. 段階的品質チェック MCP フロー (REQ-QUALITY-STAGED-004)

---

## 付録A: Tool DTO Catalog（初版）

本付録はサービス層が扱う代表DTOと例外のスケッチであり、実装時は型定義モジュール（`noveler.application.mcp_services.dto` 等）に集約する。

### A.1 共通エラー型
```
class ToolServiceError(Exception):
    message: str
    reason: str  # e.g., "validation_error", "not_found", "io_error"
    hint: str | None
    error_type: str  # Python例外種別や自前コード
    details: dict | None
```

### A.2 入出力例（抜粋）
```
@dataclass
class WriteFileRequest:
    relative_path: str
    content: str
    project_root: str | None = None

@dataclass
class WriteFileResponse:
    success_path: str
    bytes_written: int
```

```
@dataclass
class ExecuteWritingStepRequest:
    episode_number: int
    step_id: float
    dry_run: bool = False
    project_root: str | None = None

@dataclass
class ExecuteWritingStepResult:
    step_id: float
    status: str  # "completed" | "skipped" | "error"
    artifacts: list[str]  # artifact:ID
```

> LangGraph ワークフローの状態管理・本文ハッシュ参照・QCコード詳細は SPEC-QUALITY-120 を参照。 `input_data.available_tools` / `tool_selection_status` / `manuscript_hash_refs` を必須フィールドとして扱い、fetch_artifact → read_snapshot → request_manual_upload の順で本文を取得する。失敗時は QC-015〜018 を返却し、`manuscript_fetch_log` に試行履歴を記録する。

| ツール名 | 主用途 | 入出力概要 |
| --- | --- | --- |
| `get_check_tasks` | 段階タスクリスト取得 | **入力**: `episode_number` / **出力**: タスク配列 (`id`, `phase`, `llm_instruction`, SLA) |
| `execute_check_step` | 特定ステップ実行 | **入力**: `episode_number`, `step_id`, `parameters?` / **出力**: 成功可否、品質スコア、改善候補、成果物ファイル |
| `get_check_status` | 実行状況照会 | **入力**: `episode_number` / **出力**: 完了数、現在フェーズ、残時間見積もり |
| `get_check_history` | 実行履歴閲覧 | **入力**: `episode_number` / **出力**: 履歴配列（各ステップの終了時刻/結果） |
| `check_basic` | CLI互換の簡易チェック | **入力**: `episode_number`, `project_root?` / **出力**: 基本品質レポート | CLI `noveler check --basic` を呼び出す互換ツール |

すべて `ProgressiveCheckManager` に委譲し、`.noveler/checks/{session_id}/` にセッション JSON を出力する。新規仕様 `SPEC-QUALITY-110` で詳細定義予定。

## 6. LangSmith 連携ツール (REQ-QUALITY-LANG-005)

| ツール名 | 主用途 | 主な入力 | 出力/成果物 |
| --- | --- | --- | --- |
| `langsmith_generate_artifacts` | run.json から成果物生成 | `run_json_path?`, `run_json_content?`, `output_dir`, `dataset_name?`, `expected_behavior?`, `project_root?` | `reports/langsmith/*` 配下に summary/prompt/dataset を出力 |
| `langsmith_apply_patch` | パッチ適用 | `patch_text?`, `patch_file?`, `strip?`, `project_root?` | 適用可否、適用ログ |
| `langsmith_run_verification` | 検証コマンド実行 | `command?`, `project_root?`, `env?` | returncode, stdout/stderr, 実行ログ |

LangSmith成果物は `.noveler/artifacts/langsmith/{run_id}/` に保存され、品質報告や再現テストと連携する。

## 7. データ／アーティファクト管理ツール (REQ-DATA-001〜003)

| ツール名 | 主用途 | 入出力概要 |
| --- | --- | --- |
| `convert_cli_to_json` | CLIレスポンスをJSON化 | `cli_result` | `StandardResponseModel` を返却、`temp/json_output/` に保存 |
| `validate_json_response` | JSON検証 | `json_data` | スキーマ検証結果 |
| `get_file_reference_info` | ファイル参照メタ情報取得 | `file_path` | ハッシュ、バイト数、最終更新時刻 |
| `list_files_with_hashes` | プロジェクト全体のハッシュ一覧 | — | `[{path, hash}]` |
| `get_file_by_hash` | ハッシュから内容取得 | `hash` | Base64エンコード済み内容 |
| `check_file_changes` | 複数ファイルの変更検知 | `file_paths[]` | 変更有無、最新ハッシュ |
| `fetch_artifact` / `list_artifacts` | `.noveler/artifacts` 取得 | `artifact_id`, `project_root?`, `format?` | コンテンツ/一覧 |
| `backup_management` | バックアップ作成/復元/削除 | `operation`, `targets[]`, `project_root?` | 実行ステータス、保存先 |

## 8. 運用・ファイル操作ツール (REQ-OPS-WRITE-001)

| ツール名 | 主用途 | 入出力概要 | 安全策 |
| --- | --- | --- | --- |
| `write` | 任意ファイル書き込み | `relative_path`, `content`, `project_root?` | ファイル作成/更新結果、絶対パス | `create_path_service` によりルート正規化、親ディレクトリ自動生成 |
| `status` | プロジェクト状況表示 | `project_root?` | 執筆済み原稿、セッション、ログ一覧 | 読み取りのみ |
| `noveler` | CLI互換コマンド実行 | `command`, `options?`, `project_root?` | CLIレスポンス(JSON) | `convert_cli_to_json` 経由 |

## 9. エラー処理とフォールバック
- すべての FastMCP 呼び出しは例外発生時に `TextContent` で JSON 形式の `error` オブジェクトを返却。
- PathService フォールバック時は `path_fallback_used: true` とイベント配列をレスポンスに付加。
- `enhanced_*` 系ツールは再試行ガイダンス (`retry_hint`) とフェイルセーフ操作 (`resume_hint`) を含む。

## 10. 関連仕様＆テスト

| カテゴリ | 仕様書 | 主なテスト |
| --- | --- | --- |
| TenStage/18ステップ | `SPEC-WRITE-018_integrated_writing_flow.md` | `tests/integration/mcp/test_mcp_server_integration.py`, `tests/integration/test_integrated_writing_workflow.py` |
| 設計支援ツール | `SPEC-WRITE-020_conversation_design_suite.md` *(draft)* | `tests/unit/domain/services/test_conversation_design_service.py` |
| 品質チェック/改善 | `SPEC-QUALITY-001`, `SPEC-A40A41-STAGE1-AUTOFIX`, `SPEC-A40A41-STAGE23-POLISH`, `SPEC-LLM-001` | `tests/e2e/test_quality_workflow_e2e.py`, `tests/unit/presentation/cli/test_cli_adapter.py` |
| 段階的品質フロー | `SPEC-QUALITY-110_progressive_check_flow.md` *(draft)* | `tests/integration/mcp/test_progressive_check_mcp_tools.py` |
| LangSmith連携 | `SPEC-QUALITY-104_langsmith_bugfix_workflow.md` | `tests/unit/application/services/test_langsmith_bugfix_workflow_service.py` |
| データ/アーティファクト | `SPEC-ARTIFACT-001_artifact-reference-system.md` | `tests/test_json_server_performance.py`, `tests/test_hash_functionality.py` |
| ファイル操作・運用 | `SPEC-MCP-001_mcp-tool-integration-system.md` | `tests/integration/mcp/test_mcp_server_compliance.py` |

---

本仕様書は要件定義書 v5.1 の MCP ツール要件を基準としており、新規ツールやパラメータが追加された際は該当カテゴリの表に追記すること。新設予定の仕様書 (SPEC-WRITE-020 / SPEC-QUALITY-110) が完成次第、本書の `requirements` および参照表を更新する。


#### progressive_check.execute_step 追加仕様
- 入力 `input_data.available_tools[]`: `{tool_id, min_severity, requires_user_confirmation, fallback_tool_id}` を受け取り、LLM 提示に使用する。
- 入力 `input_data.manuscript_hash_refs[]`: `{hash, type}` 形式で原稿スナップショットを指定し、WorkflowStateStore に記録する。
- 出力 `execution_result.manuscript_fetch_log[]` 例:
```json
{
  "tool_id": "fetch_artifact",
  "result": "success",
  "latency_ms": 420,
  "qc_code": null,
  "excerpt_hash": "sha256:...",
  "attempt_index": 1
}
```
- 失敗時は QC-015（キャッシュ未ヒット）/QC-016（ストレージ失敗）/QC-017（手動アップロード待ち）/QC-018（ハッシュ不一致）を返却し、`metadata.recovery_hint` に再試行手順を格納する。
- 入力 `input_data` 追記:
```json
{
  "exclude_dialogue_lines": true,
  "rule_profile": "mixed_device_daily_6k_10k",
  "window_size": 5,
  "config_overrides": { "target_length": {"min":6000, "max":10000} }
}
```
- 出力 `execution_result.metadata` 追記:
```json
{
  "config_snapshot": {"target_length": {"min":6000, "max":10000, "source":"project_config"}},
  "rhythm_metrics": {"p25": 18, "p50": 32, "p75": 54, "window_in_range_ratio": 0.88},
  "dialogue_warnings": {"punctuation_runs": []},
  "hook_assessment": {"minor_peak_position_pct": 52, "mini_hook_position_pct": 86, "main_hook_strength": "avg"},
  "length_stats": {"body_chars": 8421, "in_range": true}
}
```
- エラーコード: `QC-009`（設定なし）/`QC-010`（設定不正）は `SPEC-QUALITY-110` を参照。


> 設定必須: `プロジェクト設定.yaml` が存在しない/不正な場合、`progressive_check.execute_step` は `QC-009`/`QC-010` を返して中断します。テスト/緊急用途に限り `input_data.config_overrides.target_length` を指定すると実行継続できます（`metadata.config_snapshot.source=override`）。
