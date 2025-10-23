---
spec_id: SPEC-WRITE-015
status: draft
owner: bamboocity
last_reviewed: 2025-09-17
category: WRITE
sources: [REQ]
tags: [writing, stepwise]
requirements:
  - REQ-WRITE-STEPWISE-002
  - REQ-DATA-001
---
# SPEC-WRITE-015: Stepwise Writing Use Case 仕様書

## 1. 概要

### 1.1 目的
A38 準拠15ステップ執筆プロセスを実装する `StepwiseWritingUseCase` の仕様を定義する。テンプレート駆動の段階的ワークフローにより、プロット構築から品質ゲートまでを半自動化し、柔軟なスキップ・再開に対応する。

### 1.2 対象コンポーネント
- `StepwiseWritingUseCase` (`src/noveler/application/use_cases/stepwise_writing_use_case.py`)
- ドメインサービス (`src/noveler/domain/services/writing_steps/*.py`)
- `WorkFileManager`, `StepOutputManager`, `StepSelectorService`
- `StepwiseWritingRequest` / `StepwiseWritingResponse`

### 1.3 要件紐付け
| 要件ID | 概要 | 対応章 |
| --- | --- | --- |
| REQ-WRITE-STEPWISE-002 | A38準拠15ステップ執筆ユースケース | §2, §3 |
| REQ-DATA-001 | ステップ結果のJSON/ファイル出力 | §4 |

## 2. ステップ構成

| Step | 名称 | サービス | 主な目的 |
| --- | --- | --- | --- |
| 0 | scope_definer | `ScopeDefinerService` | エピソードスコープ/目標設定 |
| 1 | story_structure | `StoryStructureDesignerService` | 章構成の骨格設計 |
| 2 | phase_structure | `PhaseStructureDesignerService` | 段階構造の詳細化 |
| 3 | theme_uniqueness | `ThemeUniquenessValidatorService` | テーマ独自性検証 |
| 4 | section_balance | `SectionBalanceOptimizerService` | セクション比率最適化 |
| 5 | scene_designer | `SceneDesignerService` | シーン/ビート設計 |
| 6 | logic_validator | `LogicValidatorService` | 因果/論理整合性チェック |
| 7 | character_consistency | `CharacterConsistencyService` | キャラ一貫性維持 |
| 8 | dialogue_designer | `DialogueDesignerService` | 会話構造設計 |
| 9 | emotion_curve | `EmotionCurveDesignerService` | 感情曲線・緊張制御 |
| 10 | scene_setting | `SceneSettingService` | 世界観・場面設定具体化 |
| 11 | manuscript_generator | `ManuscriptGeneratorService` | テンプレートから初稿生成 |
| 12 | props_world_building | `PropsWorldBuildingService` | 小道具・設定整備 |
| 13 | manuscript_generator (revision) | `ManuscriptGeneratorService` | 中間稿再生成と統合 |
| 14 | text_length_optimizer | `TextLengthOptimizerService` | 文字数最適化 |
| 15 | readability_optimizer | `ReadabilityOptimizerService` | 可読性最適化 |
| 16 | quality_gate | `QualityGateService` | 最低品質ゲート判定 |
| 17 | quality_certification | `QualityCertificationService` | 品質証明と承認 |
| 18 | publishing_preparation | `PublishingPreparationService` | 公開準備・スケジュール確定 |

## 3. ユースケース仕様

### 3.1 リクエスト (StepwiseWritingRequest)
- `project_root: Path`
- `episode_number: int`
- `step_pattern: str` — 例: `"all"`, `"0-5"`, `"structure"`, 正規表現パターン
- `resume_from_cache: bool`
- `parallel_execution: bool`
- `max_retry_count: int`
- `timeout_seconds: int`
- `generate_reports: bool`
- `custom_parameters: dict[str, Any]`

### 3.2 設定とDI
- ロガー: `ILoggerService` (任意)
- UnitOfWork: `IUnitOfWork` (永続化が必要な場合)
- パスサービス: `IPathService` (テンプレート/成果物パス解決)
- `StepSelectorService` が `step_pattern` を解釈し実行順序を決定
- `WorkFileManager` がテンプレート/一時ファイル操作を統合
- `StepOutputManager` がステップごとの成果物をキャッシュ保存

### 3.3 実行フロー
1. リクエスト検証 (`validate_request`)
2. 実行ステップの決定 (`StepSelectorService.parse_step_pattern`)
3. 既存キャッシュ利用 (`resume_from_cache=True` の場合)
4. 各ステップを順次/並列実行 (`parallel_execution` が True なら依存のないステップを並列)
5. ステップ結果を `StepExecutionResult` に格納
6. レポート生成 (`generate_reports=True` の場合)
7. 成果物（中間結果/最終原稿）の保存

### 3.4 リトライとタイムアウト
- 各ステップは `max_retry_count` 回まで再試行可
- `timeout_seconds` 超過でステップを失敗として記録し、後続ステップへ進むか停止するかは設定で制御

### 3.5 レスポンス (StepwiseWritingResponse)
- `success`: bool
- `episode_number`, `project_root`
- `executed_steps`: 実行したステップ番号一覧
- `step_results`: ステップ番号→`StepExecutionResult`
- `final_manuscript_path`: 最終原稿ファイル (存在する場合)
- 統計: `total_execution_time_ms`, `successful_steps`, `failed_steps`, `cached_steps`
- ログ: `execution_log`, `error_summary`, `report_path`

## 4. データ・ファイル管理
- ステップ成果物は `StepOutputManager` が `temp/step_outputs/` などに保存
- 最終原稿は `WorkFileManager` が `40_原稿/` へ保存し、バックアップを自動生成
- レポートは `50_管理資料/stepwise_reports/` に Markdown or JSON 形式で出力

## 5. テスト
| テスト | 目的 |
| --- | --- |
| `tests/test_stepwise_writing_system.py` | ステップパターン/並列実行/キャッシュ復元の統合検証 |
| `tests/unit/application/use_cases/test_stepwise_a30_loading_use_case.py` | A30ガイド読み込み補助ユースケースとの連携 |
| `tests/unit/domain/services/test_step_selector_service.py` | ステップ選択ロジック |
| `tests/unit/domain/services/test_progressive_write_manager_template_loading.py` | テンプレート管理との統合 |

## 6. 非機能要件
- `parallel_execution=True` の場合でもスレッドセーフなステップサービス
- 冪等性: 同一ステップを再実行しても副作用が残らない設計
- キャッシュサイズ管理: 古いステップ出力を自動再圧縮/削除

## 7. 更新履歴
| Version | Date | Summary |
| --- | --- | --- |
| 1.0.0 | 2025-09-17 | StepwiseWritingUseCase の As-built 仕様を再構築 |
