---
spec_id: SPEC-A40A41-STAGE23-POLISH
status: canonical
owner: bamboocity
last_reviewed: 2025-09-23
category: A40A41
sources: [REQ, SPEC-LLM-001]
tags: [quality, stage2, stage3, polish, llm_integration]
dependencies:
  - SPEC-LLM-001
---
# SPEC-A40A41-STAGE23-POLISH: A40/A41 推敲 Stage2/3（内容・読者体験）

目的
- Stage2（内容推敲）/Stage3（読者体験）をMCPツールとして一気通貫実行し、改稿本文・差分・レポートをアーティファクト化して可逆に運用する。

ガイド/テンプレ導線
- Stage2 プロンプトは A38_執筆プロンプトガイドの表現テンプレを参照し、以下の誘導を含む。
  - 冒頭3行フック（3行固定: 異常値→具体→賭け金）
  - Scene→Sequel（Scene: goal→conflict→outcome / Sequel: reaction→dilemma→decision）
  - 会話ビート抽出（1ターン1情報・説明台詞禁止）
- Stage3 プロンプトは A38 の「章末クリフハンガー設計」テンプレを参照し、type/unresolved/stakes/promise を設計する誘導を含む。

対象ツール
- `polish_manuscript`（プロンプト生成のみ・dry_run前提）
- `polish_manuscript_apply`（プロンプト→実行→適用→レポートまで一気通貫・**SPEC-LLM-001準拠UniversalLLMUseCase統合**）
- `polish`（上位エイリアス: `mode: prompt|apply` で分岐）

実装アーキテクチャ（SPEC-LLM-001準拠）
- **プロンプト外部化**: LLM入力は `templates/quality/checks/` 直下の MD テンプレートから読み込み（Stage2/Stage3 別ファイル）。
- **LLM実行**: UniversalLLMUseCase経由の統一実行パターン
- **MCP対応**: 自動フォールバック機能による確実な環境対応
- **パラメータ**: `force_llm`は v3.0.0 で完全削除済み（外部LLM強制は設定で制御）

I/O仕様（要点）
- 入力: `episode_number`, `file_path`, `stages: ["stage2","stage3"]`, `dry_run: bool`, `save_report: bool`
- 出力: `metadata`に以下の参照IDを格納
  - `improved_artifact`（改稿本文）
  - `diff_artifact`（差分）
  - `report_artifact`（推敲レポート）
- 参照: `.noveler/artifacts/` に内容とメタ情報を保存

テンプレート仕様（A40専用）
- Stage2: `polish_stage2_content.yaml`（`templates/quality/checks/`。レガシー互換で `stage2_content_refiner.md` / `write_step26_polish_stage2.yaml` ）
- Stage3: `polish_stage3_reader.yaml`（`templates/quality/checks/`。レガシー互換で `stage3_reader_experience.md` / `write_step27_polish_stage3.yaml` ）
- 必須プレースホルダ: `{manuscript}`（原稿埋め込み）
- 任意プレースホルダ: `{episode_number}`, `{project_title}`, `{project_genre}`, `{target_word_count}`
- 検証・フォールバック: SPEC-LLM-001 の 3.0/3.3 に準拠（未解決プレースホルダ検知、内蔵デフォルトへフォールバック、WARN ログ）

パラメータ変更（SPEC-LLM-001）
- フォールバック対応: UniversalLLMUseCase がフォールバックを返した場合は改稿適用をスキップし、元原稿と差分のみ生成。外部LLM強制は `.novelerrc.yaml` または `NOVELER_FORCE_EXTERNAL_LLM` で制御。

受入基準
1) `polish_manuscript_apply` を `dry_run: true` で実行時、`metadata` に `improved_artifact`/`diff_artifact`/`report_artifact` が含まれる。
2) `restore_manuscript_from_artifact` を `dry_run: true` で実行すると、`diff_artifact` が作成されロールバック検証が可能。
3) `polish` ツールで `mode: apply` の場合、`polish_manuscript_apply` と同等の成果物が生成される。
 6) `final_quality_approval`（step12）の合否に `length_stats.in_range` を含める（必須）。
 4) `polish_manuscript` 実行時の `metadata.prompts.stage2` に「冒頭3行フック/Scene→Sequel/会話ビート」の誘導文言が含まれ、`stage3` に「クリフハンガー」誘導が含まれる。
 5) `templates/quality/checks/` のテンプレート更新が LLM 入力に反映されること（フォールバック時は埋め込み既定を使用し、ログに出自を記録）。

テストとの対応
- E2E: `tests/e2e/test_a40_polish_workflow_e2e.py`（dry_runアーティファクトの返却、復元の差分生成）
- CLI/Best practices: `docs/mcp/tools_usage_best_practices.md` のサンプルコマンドに準拠
- Unit: `tests/unit/mcp_servers/tools/test_polish_prompts_templates.py`（プロンプトにA38テンプレ誘導が含まれることを検証）

非機能要件（抜粋）
- アーティファクト参照でプロンプトを最小化（ARTIFACT仕様準拠）
- 実行時間: 1話あたり 30秒以内（dry_run）目標
- 可逆性: 改稿本文は常にアーティファクト経由で復元可能
- **パフォーマンス**: SPEC-LLM-001統合後もパフォーマンス劣化10%以内維持
- **MCP対応**: MCP環境での動作成功率100%保証（UniversalLLMUseCase統合効果）

品質保証（SPEC-LLM-001連携）
- テストカバレッジ: 95%以上維持
- アーキテクチャ境界違反: 0件
- CI/CDスモークテスト: 100%成功維持


補足（テンプレ変数）
- `{target_min_chars}` / `{target_max_chars}` は ConfigResolver から注入される。未設定時は 6000/10000。
