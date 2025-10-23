# テンプレートファイル

このディレクトリには、novelerシステムで使用する各種テンプレートが格納されています。

## 🎯 実際に使用中のテンプレート

### 段階実行用プロンプトテンプレート（19ステップ執筆システム / Schema v2）
- `write_step00_scope_definition.yaml` – STEP0: スコープ定義
- `write_step01_chapter_purpose.yaml` – STEP1: 章の目的線
- `write_step02_section_goals.yaml` – STEP2: セクション目標
- `write_step03_theme_uniqueness.yaml` – STEP3: テーマ独自性検証
- `write_step04_section_balance.yaml` – STEP4: セクションバランス設計
- `write_step05_scene_beats.yaml` – STEP5: シーン/ビート設計
- `write_step06_logic_verification.yaml` – STEP6: 論理検証
- `write_step07_character_detail.yaml` – STEP7: キャラクター詳細化
- `write_step08_dialogue_design.yaml` – STEP8: 対話設計
- `write_step09_emotion_curve.yaml` – STEP9: 感情カーブ設計
- `write_step10_atmosphere_worldview.yaml` – STEP10: 雰囲気・世界観演出
- `write_step11_foreshadow_placement.yaml` – STEP11: 伏線配置
- `write_step12_first_draft.yaml` – STEP12: 初稿執筆
- `write_step13_style_adjustment.yaml` – STEP13: 文体調整
- `write_step14_description_enhancement.yaml` – STEP14: 描写強化
- `write_step15_readability_optimization.yaml` – STEP15: 読みやすさ最適化
- `write_step16_quality_check.yaml` – STEP16: 品質チェック
- `write_step17_reader_experience.yaml` – STEP17: 読者体験最適化
- `write_step18_final_preparation.yaml` – STEP18: 最終確認・公開準備

**使用システム:** ProgressiveWriteManager / ProgressiveTaskManager（段階実行制御）

### プロット生成用テンプレート
- `章別プロットテンプレート.yaml` - 章別詳細プロット作成用
- `話別プロットテンプレート.yaml` - 話別詳細プロット作成用
- `chapter_plot.yaml` - 章プロット生成用（簡易版）

**使用システム:** YamlTemplateRepository, PlotCreationOrchestrator

### 品質チェック用テンプレート
- `check_step01_typo_check.yaml` 〜 `check_step12_final_quality_approval.yaml`
  - 12段階品質チェック（Schema v2 / ProgressiveCheckManager 専用）
  - ルート必須キー: `metadata`, `llm_config`, `prompt`, `inputs`, `constraints`, `tasks`, `artifacts`, `acceptance_criteria`, `next`, `variables`, `control_settings`, `check_criteria`
- `comprehensive.yaml` - 総合品質チェック
  - LangGraph 版では `control_settings` に加えて `available_tools` ブロックを定義し、各ツールの `tool_id`, `min_severity`, `requires_user_confirmation`, `fallback_tool_id` を記述する。
  - 抜粋を LLM に渡す場合は `manuscript_excerpt` セクションを追加し、`excerpt_hash` / `source_key` / `range_checksum` を変数として宣言する。
- `consistency_analysis.yaml` - 一貫性分析
- `creative_focus.yaml` - 創作性重視チェック
- `debug.yaml` - デバッグ用チェック
- `emotional_depth_analyzer.yaml` - 感情深度分析
- `quick.yaml` - クイックチェック
- `reader_experience.yaml` - 読者体験チェック
- `structural.yaml` - 構造チェック
- その他の品質関連テンプレート

**使用システム:** 品質チェックコマンド

## 📋 テンプレートの役割
- **段階実行制御**: LLMによる一括実行を防ぎ、ステップ単位で実行
- **プロット生成**: 構造化されたプロット作成支援
- **品質管理**: 執筆品質の自動チェック・改善提案

## 📝 命名規則
- **writeコマンド用**: `write_step*_*.yaml` - `/noveler write` および MCP 経由の段階実行テンプレート
  - Schema v2 構造化仕様（A38準拠）: `docs/technical/prompt_template_schema_v2.md`
  - ルート必須キー: `metadata`, `llm_config`, `prompt`, `inputs`, `constraints`, `tasks`, `artifacts`, `acceptance_criteria`, `next`, `variables`, `control_settings`
  - `control_settings` は全STEPで `strict_single_step` など安全ガードを `true` 指定。実装側がこれらの制御フラグを尊重する前提です。
- **plotコマンド用**: `*プロット*.yaml` - プロット生成で使用されるテンプレート
- **品質チェック用**: `check_step*_*.yaml` / `*.yaml` - 品質チェックコマンド用テンプレート
  - Schema v2 構造化仕様（A38準拠）: ProgressiveCheckManager が `check_step*_*.yaml` を優先ロード
  - ルート必須キー: `metadata`, `llm_config`, `prompt`, `inputs`, `constraints`, `tasks`, `artifacts`, `acceptance_criteria`, `next`, `variables`, `control_settings`, `check_criteria`

## 📝 更新履歴
- 2025-09-24: check_step*_*.yaml を Schema v2 仕様へ更新（ProgressiveCheckManager対応）
- 2025-09-09: テンプレート整理、シンプル構造に変更
- 2025-09-09: 実用性重視でtemplates直下に配置統一
- 2025-09-09: 用途明示のためwrite_step*形式に命名規則変更


## 🔎 テンプレート探索順（品質/推敲）
1. `templates/quality/checks/`（正本）
2. `templates/quality/checks/backup/`（退避・参照専用）
3. 旧互換: `templates/writing/`（存在時のみ）
検証失敗時は内蔵フォールバックし、WARN ログに `template_source=embedded` を記録します。


### ProgressiveCheck 固有の補足
- LangGraph WorkflowStateStore に合わせ、`variables` に `manuscript_hash`, `session_id`, `state_version` を含める。
- 変数セット: `{step_id, step_name, episode_number, completed_steps, total_steps, phase, project_root, session_id}` を前提。
- バージョン管理: `metadata.version` とテンプレート本文のハッシュ（content_hash）をセッション manifest に記録して追跡（SPEC-QUALITY-110）。
- 検収: `acceptance_criteria.by_task` は `issues.<category>` を指すフィールド指定とし、`artifacts.required_fields`（summary/issues/recommendations/metrics）を満たすこと。
