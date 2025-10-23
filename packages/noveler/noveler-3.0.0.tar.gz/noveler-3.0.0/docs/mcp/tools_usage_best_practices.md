# MCPツール統合システム使用例・ベストプラクティスガイド

**ガイドID**: BPG-MCP-001
**対象仕様**: SPEC-MCP-001 v2.4.0準拠
**対象ユーザー**: 小説執筆者、システム開発者
**最終更新**: 2025-09-05

---

## 1. 概要

このガイドは、小説執筆支援システム「Noveler」のMCP（Model Context Protocol）ツール群を効果的に活用するための実用的な使用例とベストプラクティスを提供します。

### 1.1 MCPツール統合の利点
- **95%トークン削減**: JSON変換による効率化
- **独立タイムアウト**: 段階別5分実行で高い可用性
- **シームレス統合**: Claude Code内での直接実行
- **品質自動化**: A31評価68項目による自動品質チェック

---

## 2. 基本的な使用パターン

### 2.1 新規エピソード執筆（フル実行）

#### 2.1.1 基本的な流れ
```
1. プロット生成 → noveler_plot
2. 19ステップ執筆実行 → noveler_write
3. 品質チェック → noveler_check
4. 修正実行 → check_fix
5. （任意）最終化・公開準備 → noveler_complete
```

> **補足**: 2025-09-18 時点で `init` ツールは廃止済みです。プロジェクト雛形はテンプレートをコピーするか、`noveler` CLI の初期化コマンドをご利用ください。

#### 2.1.2 実際のコマンド例
```bash
# Step 1: プロット生成
mcp__noveler__noveler_plot episode=1

# Step 2: 19ステップ執筆実行
mcp__noveler__noveler_write episode=1

# Step 3: 品質チェック
mcp__noveler__noveler_check episode=1

# Step 4: 問題修正
mcp__noveler__check_fix episode=1 fix_level="standard"

# Step 5 (任意): 完了処理・公開準備メタの取得
mcp__noveler__noveler_complete episode=1 auto_publish=false
```

> **LLM実行の有効化**: `config/novel_config.yaml` 内の `defaults.writing_steps.use_llm` を `true` に設定すると、STEP 0-18 の各実行時にテンプレート指示が LLM へ送信されます（既定値 `false` はオフライン検証用）。

### 2.2 段階的執筆（ステップ実行）

- `write_stage` と `write_resume` は旧 TenStage API のステージ名（例: `plot_data_preparation`, `refine_manuscript_quality`）を現在も使用します。Schema v2 テンプレートの各STEPを全面的にカバーした個別ツールは順次公開予定です。それまでは `noveler_write` で 19 ステップを逐次実行し、必要に応じてアーティファクトを個別参照してください。

### 2.3 中断・再開パターン

#### 2.3.1 セッション管理による継続実行
```bash
# 実行開始
mcp__noveler__noveler_write episode=1
# → session_id="session_abc123" が返される

# 中断後の再開
mcp__noveler__write_resume episode=1 session_id="session_abc123"
```

---

## 3. シナリオ別ベストプラクティス

### 3.1 初心者向け: 一気通貫執筆

**推奨フロー**:
```
noveler_plot → noveler_write → noveler_check → check_fix → noveler_complete
```

**ポイント**:
- `noveler_write`ツールで19ステップを一括実行（構造設計〜最終確認まで）
- `noveler_check`で基本品質を確認
- 問題があれば`check_fix`で自動修正

**実行例**:
```bash
# 1. 第1話のプロット生成
mcp__noveler__noveler_plot episode=1

# 2. 第1話の執筆（約20-25分で完了）
mcp__noveler__noveler_write episode=1

# 3. 品質チェック（3段階チェック）
mcp__noveler__noveler_check episode=1

# 4. 自動修正（必要に応じて）
mcp__noveler__check_fix episode=1 fix_level="safe"

# 5 (任意). 完了処理・原稿出力パッケージ化
mcp__noveler__noveler_complete episode=1 auto_publish=false
```

### 3.2 中級者向け: 段階的品質向上

**推奨フロー**:
```
noveler_plot → write_stage(1-7) → write_manuscript_draft →
check_story_elements → check_writing_expression → check_fix
```

**ポイント**:
- 段階別実行で細かい制御
- 専門的な品質チェックツールを活用
- 修正レベルを調整

**実行例**:
```bash
# プロット生成
mcp__noveler__noveler_plot episode=2

# 段階1-7: 設計フェーズ
mcp__noveler__write_stage episode=2 stage="plot_data_preparation"
mcp__noveler__write_stage episode=2 stage="design_emotional_flow" session_id="session_002"

# STEP8: 原稿執筆（目標4000字）
mcp__noveler__write_manuscript_draft episode=2 word_count_target=4000

# 専門品質チェック
mcp__noveler__check_story_elements episode=2
mcp__noveler__check_writing_expression episode=2

# 標準レベル修正
mcp__noveler__check_fix episode=2 fix_level="standard"
```

### 3.3 上級者向け: カスタム品質管理

**推奨フロー**:
```
noveler_plot（事前設計）→ check_story_structure → write_with_claude → 個別品質チェック →
積極修正 → 最終検証
```

**ポイント**:
- プロット事前検証
- Claude直接執筆機能活用
- 積極的修正レベル使用

**実行例**:
```bash
# プロット生成と構造確認
mcp__noveler__noveler_plot episode=3
mcp__noveler__check_story_structure episode=3

# Claude直接執筆（外部API不使用）
mcp__noveler__write_with_claude episode=3 word_count_target=5000

# 個別品質分析
mcp__noveler__check_rhythm episode=3

# 積極修正適用
mcp__noveler__check_fix episode=3 fix_level="aggressive"

# 最終品質確認
mcp__noveler__noveler_check episode=3
```

---

## 4. 品質チェック活用法

### 4.1 段階的品質チェック戦略

#### 4.1.1 基本チェック（初稿完成時）
```bash
# 基本的な問題のみチェック
mcp__noveler__check_basic episode=1
```

**チェック内容**:
- 文字数チェック
- 禁止表現検出
- 基本文章構造
- 誤字脱字の可能性

#### 4.1.2 要素別チェック（推敲時）
```bash
# A31評価68項目による詳細チェック
mcp__noveler__check_story_elements episode=1

# 文章表現力の専門チェック
mcp__noveler__check_writing_expression episode=1

# リズム・読みやすさチェック
mcp__noveler__check_rhythm episode=1
```

#### 4.1.3 構造チェック（完成前）
```bash
# ストーリー全体構成の最終チェック
mcp__noveler__check_story_structure episode=1
```

### 4.2 修正レベルの使い分け

#### 4.2.1 修正レベル別特徴
```bash
# 安全修正: 明確な誤りのみ修正
mcp__noveler__check_fix episode=1 fix_level="safe"

# 標準修正: 一般的な改善提案を適用
mcp__noveler__check_fix episode=1 fix_level="standard"

# 積極修正: 品質向上のための大幅修正
mcp__noveler__check_fix episode=1 fix_level="aggressive"
```

#### 4.2.2 修正レベル選択指針
- **safe**: 初稿・締切直前・保守的修正
- **standard**: 通常の推敲・バランス重視
- **aggressive**: 品質最優先・時間に余裕がある場合

### 4.3 テスト結果解析（Codex/Claude 共通）

pytest などの JSON レポートをそのまま渡すと、失敗・エラー・統計情報を整理した Issue 一覧を返します。

```bash
# pytest-json-report の出力を渡す例
noveler mcp call test_result_analysis '{
  "test_result_json": $(cat reports/pytest-report.json),
  "focus_on_failures": true,
  "include_suggestions": true,
  "max_issues": 20
}'

# Codex CLI の call-tool でも同じ形式で実行可能
call-tool mcp__noveler__test_result_analysis test_result_json=@reports/pytest-report.json include_suggestions=true
```

`include_suggestions=false` を指定すると、失敗箇所の抽出だけに絞り込めます。CI と連携する場合は `max_issues` を小さくして要点のみ確認する運用が推奨です。

---

## 5. 設定と実行ベストプラクティス（Codex/Claude）

### 5.1 MCPクライアント設定の自動更新

既存設定ファイルを壊さないように、バックアップ付きで安全にマージ更新します。

```bash
# 一括更新（codex/.mcp/Claude）
./bin/setup_mcp_configs

# 個別更新
./bin/setup_mcp_configs --codex     # codex.mcp.json
./bin/setup_mcp_configs --project   # .mcp/config.json
./bin/setup_mcp_configs --claude    # Claude Code 設定

# ドライラン（書き込み無し）
./bin/setup_mcp_configs --dry-run

# 表示名/説明のカスタム
./bin/setup_mcp_configs --name "Noveler MCP" --description "Writing/quality tools"
```

**SSOT管理**: 詳細は `docs/mcp/config_management.md` を参照
**最小サンプル**: `docs/.examples/codex.mcp.json`

### 5.2 エンハンスト執筆ユースケース（診断/復旧対応）

標準の `get_writing_tasks` / `execute_writing_step` と併存し、エラーハンドリング強化版として以下を提供します。

```bash
noveler mcp call enhanced_get_writing_tasks '{"episode_number":1}'
noveler mcp call enhanced_execute_writing_step '{"episode_number":1,"step_id":1,"dry_run":false}'
noveler mcp call enhanced_resume_from_partial_failure '{"episode_number":1,"recovery_point":5}'
```

戻り値には `execution_method: enhanced_use_case` が含まれ、復旧が適用された場合は `recovery_applied: true` を返します。

## 5. エラー対処・トラブルシューティング

### 5.1 よくあるエラーパターン

#### 5.1.1 セッションタイムアウト
```
エラー: Session timeout after 5 minutes
対処法: write_resume で再開
```

```bash
# タイムアウト後の再開
mcp__noveler__write_resume episode=1 session_id="timeout_session_id"
```

#### 5.1.2 プロジェクトルート未指定
```
エラー: Project root not found
対処法: project_root パラメータを明示指定
```

```bash
# プロジェクトルート明示指定
mcp__noveler__noveler_write episode=1 project_root="/path/to/novel/project"
```

#### 5.1.3 エピソード番号エラー
```
エラー: Invalid episode number
対処法: 正の整数でエピソード番号指定
```

```bash
# 正しいエピソード番号指定
mcp__noveler__noveler_write episode=1  # ✅ 正しい
mcp__noveler__noveler_write episode=-1 # ❌ エラー
```

### 5.2 パフォーマンス最適化

#### 5.2.1 並列実行パターン
```bash
# 複数エピソードの並列品質チェック（推奨）
mcp__noveler__check_basic episode=1 &
mcp__noveler__check_basic episode=2 &
mcp__noveler__check_basic episode=3 &
wait
```

#### 5.2.2 段階実行による負荷分散
```bash
# 重い処理を段階分割
mcp__noveler__write_stage episode=1 stage="plot_data_preparation"
# 5分休憩
mcp__noveler__write_stage episode=1 stage="write_manuscript_draft" session_id="prev_session"
```

---

## 6. プロジェクト管理ベストプラクティス

### 6.1 プロジェクト状態の継続監視

#### 6.1.1 定期ステータス確認
```bash
# プロジェクト全体状況の確認
mcp__noveler__status

# 出力例:
# - 執筆済み話数: 5話
# - 平均品質スコア: 82点
# - 総文字数: 18,500文字
# - 最終更新: 2025-09-05 14:30
```

#### 6.1.2 品質トレンドの追跡
```bash
# 品質チェック履歴の確認
mcp__noveler__noveler_check episode=1  # 各話の品質スコア記録
mcp__noveler__noveler_check episode=2
mcp__noveler__noveler_check episode=3
```

### 6.2 バックアップ・バージョン管理

#### 6.2.1 重要段階でのスナップショット
```bash
# 初稿完成時のバックアップ
cp -r projects/default/ backup/episode_1_draft_$(date +%Y%m%d)

# 品質チェック完了時
cp -r projects/default/ backup/episode_1_quality_$(date +%Y%m%d)
```

---

## 7. 高度な活用テクニック

### 7.1 カスタムワークフロー構築

#### 7.1.1 ジャンル特化パターン
```bash
# ファンタジー小説特化フロー
mcp__noveler__noveler_plot episode=1
mcp__noveler__write_stage episode=1 stage="design_emotional_flow"  # 感情重視
mcp__noveler__write_stage episode=1 stage="design_scene_atmosphere" # 雰囲気重視
mcp__noveler__write_manuscript_draft episode=1 word_count_target=4500
mcp__noveler__check_story_elements episode=1  # 世界観チェック重視

# 恋愛小説特化フロー
mcp__noveler__write_stage episode=1 stage="design_character_dialogue" # 対話重視
mcp__noveler__write_stage episode=1 stage="design_emotional_flow"     # 感情重視
mcp__noveler__check_writing_expression episode=1  # 表現力重視
```

#### 7.1.2 スケジュール連動パターン
```bash
# 毎日投稿スケジュール
# 曜日別タスク分散
# 月: プロット / 火: 執筆 / 水: 品質チェック / 木: 修正 / 金: 投稿準備
```

### 7.2 AI協創最適化

#### 7.2.1 トークン効率化パターン
```bash
# 95%トークン削減を活用した大量処理
for episode in {1..10}; do
    mcp__noveler__write_with_claude episode=$episode word_count_target=4000
done
```

#### 7.2.2 品質向上循環パターン
```bash
# 品質向上のPDCAサイクル
mcp__noveler__noveler_write episode=1                    # Plan & Do
mcp__noveler__noveler_check episode=1                    # Check
mcp__noveler__check_fix episode=1 fix_level="standard" # Action
mcp__noveler__noveler_check episode=1                    # 再Check
```

---

## 8. 運用上の注意事項

### 8.1 制限事項・留意点

#### 8.1.1 技術的制限
- **タイムアウト**: 各段階最大5分
- **同時実行**: 同一エピソードの並列実行非推奨
- **セッション管理**: セッションIDの適切な管理が必要

#### 8.1.2 品質管理上の留意点
- **自動修正の限界**: fix_levelに関わらず100%完璧にはならない
- **人間の最終チェック**: AIチェック後の人間による確認推奨
- **ジャンル特性**: ジャンルによって品質基準が異なる

### 8.2 セキュリティ・プライバシー

#### 8.2.1 データ保護
- プロジェクトファイルの適切なバックアップ
- 機密情報（実名等）の除去確認
- バージョン管理での履歴保護

---

## 9. FAQ

### 9.1 よくある質問

**Q1: エピソードの執筆に時間がかかりすぎる**
A1: `write_stage`を使って段階分割実行を試してください。各段階5分以内で完了します。

**Q2: 品質スコアが低い**
A2: `check_story_elements`で詳細分析後、`check_fix`の`fix_level="aggressive"`を試してください。

**Q3: セッションが失われた**
A3: セッションIDが不明な場合は、`noveler_write`で全体を再実行することをお勧めします。

**Q4: プロジェクトファイルが見つからない**
A4: `project_root`パラメータでパスを明示指定するか、`status`で現在の状態を確認してください。

### 9.2 パフォーマンス最適化FAQ

**Q5: 処理速度を向上させたい**
A5: JSON変換による95%トークン削減が適用されているため、既に最適化されています。並列実行や段階分割をお試しください。

**Q6: メモリ使用量が気になる**
A6: 段階別実行（`write_stage`）により、メモリ使用量を分散できます。

---

## 10. まとめ

MCPツール統合システムを効果的に活用することで、小説執筆の効率と品質を大幅に向上させることができます。

**主要なポイント**:
1. **初心者**: `noveler_write` → `noveler_check` → `check_fix` の基本フロー
2. **中級者**: 段階的実行とカスタム品質チェック
3. **上級者**: プロット事前検証と積極的品質向上

**成功の鍵**:
- 自分の執筆スタイルに合わせたツール選択
- 段階的品質向上の継続実行
- セッション管理とエラー対処の習得

これらのベストプラクティスを参考に、効率的なAI協創執筆をお楽しみください。

---

## 11. 軽量出力オプションと反復オーケストレーション（B20準拠）

### 11.1 軽量出力オプション
- 本文は原則返さず、`issue_id`/`file_hash`/`line_hash`/`block_hash` などの識別子で参照。
- `run_quality_checks` 推奨設定:

- 追加オプション:
  - `exclude_dialogue_lines: boolean` — 会話行（「…」/『…』）を文長チェックから除外（readability）

  - `format: "summary"`（要約のみ）で速報把握。
  - 詳細は `page` / `page_size` で段階取得（既定で200件上限・超過時 `metadata.pagination`/`truncated: true`）。
  - `format: "ndjson"` はページ適用後の範囲のみを `metadata.ndjson` に同梱。
  - 付与メタ: `total_issues` / `returned_issues` / `aspect_scores` / `pagination` / `truncated`。
- `fix_quality_issues`:
  - 既定 `include_diff: false`。必要時のみ `true` + `max_diff_lines`（短縮diff）。
  - 自動修正は安全な `reason_codes` を明示（例: 三点リーダ/ダッシュ/短文連結・長文分割/句読点基本正規化 等）。
- 具体例:
  - `run_quality_checks({ episode_number: 1, file_path: "...", aspects: ["rhythm"], severity_threshold: "medium", format: "summary" })`
  - `run_quality_checks({ episode_number: 1, file_path: "...", aspects: ["rhythm"], page: 1, page_size: 100, format: "json" })`
  - `fix_quality_issues({ episode_number: 1, file_path: "...", reason_codes: ["ELLIPSIS_STYLE","DASH_STYLE"], dry_run: true, include_diff: false })`

### 11.2 反復オーケストレーション（improve_quality_until）
- 各評価項目ごとに「自動修正 → 再評価」を反復し、合格したら次項目へ進む段階ゲート方式。
- 既定値: `target_score: 80` / `max_iterations: 3` / `min_delta: 0.5` / `severity_threshold: "medium"`。
- 推奨順序: リズム → 可読性 → 文法（最終に総合確認）。
- サンプル:
  - `improve_quality_until({ episode_number: 1, file_path: "40_原稿/EP001_scene01.md", aspects: ["rhythm","readability","grammar"], target_score: 80, max_iterations: 3, include_diff: false })`
- 方針: 本文非同梱・ハッシュ/ID中心。必要時のみ `get_issue_context` で周辺数行を参照。

注意（reason_codesの指定形式）:
- `fix_quality_issues` は `reason_codes: string[]`（配列）。
- `improve_quality_until` は元々 `{ aspect: string[] }`（オブジェクト）ですが、後方互換で配列も受理します。
  - 配列で渡した場合は、指定した全アスペクトに同一セットを適用します。
  - 例（オブジェクト）: `reason_codes: { "rhythm": ["CONSECUTIVE_LONG_SENTENCES","ELLIPSIS_STYLE"] }`
  - 例（配列・後方互換）: `reason_codes: ["CONSECUTIVE_LONG_SENTENCES","ELLIPSIS_STYLE"]`
  - 不正/非対応コードは自動的に無視され、`metadata.ignored_reason_codes` に記録されます。

**更新履歴**:
- v1.0.0 (2025-09-05): 初版作成（SPEC-MCP-001 v2.4.0対応）

**関連ドキュメント**:
- SPEC-MCP-001_mcp-tool-integration-system.md
- requirements_definition_master.md
- SPEC-MCP-001_v240_implementation_completion_report.md

### 11.3 A40統合推敲プロンプト（polish_manuscript）

- 目的: A40ガイドのStage2（内容推敲）/Stage3（読者体験）に対応する統合プロンプトを段階別に生成し、LLM実行に渡す導線を提供。
- 実行例:
  ```bash
  noveler mcp call polish_manuscript '{
    "episode_number": 1,
    "file_path": "40_原稿/第001話_タイトル.md",
    "stages": ["stage2", "stage3"],
    "dry_run": true
  }'
  ```
- 出力:
  - issues: 各ステージの結果（details.promptにプロンプト）
  - metadata.prompts: { stage2: "...", stage3: "..." }
- 備考:
  - MCP内の非同期制約を避けるため、ツール内ではLLM実行を行わずプロンプト生成に特化。
  - 改稿の適用は、上位（CLI/エディタ）でLLMに渡し、原稿に反映してから `run_quality_checks` を再実行する。

### 11.4 A40統合推敲 一気通貫適用（polish_manuscript_apply）

- 目的: Stage2/3のプロンプト生成→LLM実行→差分作成→原稿適用→A41レポート作成まで自動化。
- 実行例:
  ```bash
  noveler mcp call polish_manuscript_apply '{
    "episode_number": 1,
    "file_path": "40_原稿/第001話_タイトル.md",
    "stages": ["stage2", "stage3"],
    "dry_run": false,
    "save_report": true
  }'
  ```
- 出力:
  - issues[0].details: { applied, score, passed, diff_artifact, report_artifact, prompts }
  - metadata: diff_artifact, report_artifact（.noveler/artifacts参照）
- 備考:
  - MCP内（LLM不可環境）ではプロンプト生成と差分/レポートのみを実施（原稿は未変更）。
  - UniversalLLMUseCase がフォールバックを返した場合は改稿適用をスキップし、差分とレポートのみ生成。
  - 非MCP環境ではUniversalClaudeCodeServiceによりLLM実行を行い、改稿を適用。

### 11.5 MessageBus / Outbox の運用確認
- すべての `noveler_*` MCP ツールは MessageBus 統合を通じて `<project>/temp/bus_outbox/` にイベント履歴を保存します。
- テスト後に初期状態へ戻したい場合は以下を実行してください。
  ```bash
  rm -rf temp/bus_outbox
  ```
- べき等性は InMemory で管理され、プロセス終了でリセットされます。
- **運用コマンド（完全実装済み）**:
  ```bash
  noveler bus health --detailed         # DLQ統計を含むヘルス状況
  noveler bus list --type dlq          # 失敗イベント一覧
  noveler bus flush --dry-run          # 手動フラッシュ（プレビュー）
  noveler bus replay <event_id>        # DLQエントリの再実行
  noveler bus metrics --reset          # パフォーマンス指標とリセット
  ```
- 背景フラッシュタスクは30秒間隔で自動実行され、`NOVELER_DISABLE_BACKGROUND_FLUSH=1` で無効化できます。


## 運用ベストプラクティス（更新）
- 軽量出力の既定化: `MCP_LIGHTWEIGHT_DEFAULT=1` を推奨（CI/本番）。
- MCP設定は可搬化: `.mcp/config.json` は相対パス・`cwd: '.'`・`PYTHONPATH=.:./dist` を基本とし、`args[0]` はスクリプトパス（`-u`は使わない）。`PYTHONUNBUFFERED=1` は env で付与。
