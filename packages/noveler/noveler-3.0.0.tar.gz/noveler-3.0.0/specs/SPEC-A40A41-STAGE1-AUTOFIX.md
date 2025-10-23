---
spec_id: SPEC-A40A41-STAGE1-AUTOFIX
status: canonical
owner: bamboocity
last_reviewed: 2025-09-15
category: A40A41
sources: [REQ]
tags: [quality, stage1, autofix]
---
# SPEC-A40A41-STAGE1-AUTOFIX: A40/A41 準拠の技術的推敲(Stage1) 自動修正拡張

Status: Draft
Owner: noveler
Created: 2025-09-15

目的
- A40_推敲品質ガイドの Stage 1「技術的推敲」における自動修正項目のうち、現行実装で未カバーの安全領域を `fix_quality_issues` に追加する。
- `noveler check --auto-fix` 実行時、反復改善オーケストレーション（`improve_quality_until`）の利用を促進し、B20の自動改善→再評価サイクルに準拠させる。
 - Breaking change: 日本語文に対する強制改行と行幅警告は、全サブコマンドから撤廃する（`--auto-fix` による改行挿入は行わない）。

範囲
- 追加自動修正（安全・非意味変化）
  - 半角記号の全角統一: `! -> ！`, `? -> ？`
  - 会話文末の句点削除: 行末の `」。` を `」` に正規化
  - 閉じ括弧直前の空白削除: ` 」` ` 』` ` ）` ` 】` → `」` `』` `）` `】`
- 反復改善の導線: `noveler check --auto-fix` 経路で `improve_quality_until` を呼び出す
 - 行幅・改行ポリシー: 日本語文に対する自動改行は行わない。行幅超過に関する検出・警告・自動修正は提供しない。

非対象（将来検討）
- 段落頭の字下げ統一（運用差・嗜好差が大きく、安全自動化の合意形成後に対応）
- LLMによる内容/読者体験レベルの推敲（Stage 2/3 は別フローで実行）

受け入れ基準
1) `fix_quality_issues` を `dry_run: false` で実行時、追加3項目（記号統一/会話句点/閉じ括弧前空白）が必要行に無害適用され、`metadata.applied` が増加する。
2) `noveler check 1 --auto-fix` 実行時、`improve_quality_until` により合格点(>=80)へ到達するまで最大3回の反復を行い、最終的に再計測が行われる（フォールバックとして単回の`fix_quality_issues`を許容）。
3) いかなるサブコマンド・経路でも、行幅を理由に新たなハード改行を挿入しない。行幅超過の警告/エラー/修正は出力されない。再実行しても差分が出ない（冪等）。

備考
- 実装はB20 3コミットサイクルで反映（docs→feat→refactor）。

テストとの対応
- ユニット: `tests/unit/mcp_servers/tools/test_fix_quality_issues_stage1.py`
  - 約物(!/?)の全角統一、必要時の全角スペース挿入、行末『」。』の削除、閉じ括弧直前の空白削除、コードブロック無視
- E2E: `tests/e2e/test_stage1_autofix_e2e.py`
  - `execute_fix_quality_issues` 経由のエンドツーエンド検証（適用件数・書き戻し・内容の正規化）
- CLI: `tests/unit/presentation/test_cli_check_autofix.py`
  - `noveler check --auto-fix` が `improve_quality_until` を用いて目標スコア80/最大3反復で実行することを検証


設定
- 行幅/改行に関する設定キーは廃止（`.novelerrc` から `line_wrap.*` および `max_line_width*` 関連を削除）。
