# LangGraphワークフロー移行要件草案

## 背景
- 現行: MCPサーバーで UniversalLLMUseCase を呼び出し、品質チェック結果を `.noveler/checks/{session_id}` 配下へファイル保存。
- 課題: 品質チェック→修正→再チェックの反復時に、状態遷移や部分成功の追跡が難しく、例外時のロールバックや再開ポイントの把握も手作業になりがち。
- 要件: 各ステップの状態と品質記録を確実に保持し、LLM チェックの再実行や指摘修正サイクルを安全に回せる仕組みを整備する。

## ゴール定義
- セッション内で発生した全指摘について、修正履歴と再チェック結果を時間軸で復元できる。
- 未解消指摘が自動的に抽出され、LLM および利用者が再対応の必要性を判断できる。
- LLM が提示した修正タスクと実際の修正内容がマッピングされ、再実行時に参照できる。

## 目的・スコープ
- MCP サーバーを API 境界として維持しつつ、ワークフロー制御層を LangGraph へ段階的に移行する。
- ProgressiveCheckManager を先行対象とした PoC で、状態保持・再実行・エラー通知の要件適合性を検証する。
- 既存 QC-00x エラー体系、テンプレート資産、テスト運用（TDD / `make validate-templates` 等）との整合を担保する。

## 要件概要
### 1. 状態管理抽象化
- `WorkflowStateStore` を設計し、ファイル保存（`.noveler/checks/...`）と将来の DB 永続化に対応可能なインターフェースを提供する。
- 保存単位と必須フィールド:

  | エンティティ | 主キー | 必須フィールド（例） | 保存タイミング |
  | --- | --- | --- | --- |
  | `session` | `session_id` | `episode_number`, `initiator`, `created_at`, `current_status`, `iteration_policy`, `lock_status`, `state_version` | セッション開始時 |
  | `step_execution` | `session_id+step_id+attempt` | `input_snapshot_hash`, `output_snapshot_hash`, `issues_detected`, `duration_ms`, `fallback_reason`, `available_tools`, `tool_selection_status`, `manuscript_hash_refs` | 各ステップ完了時 |
  | `issue` | `issue_id` | `session_id`, `step_id`, `manuscript_version_id`, `manuscript_hash`, `category`, `severity`, `text_range`, `range_checksum`, `description`, `suggested_fixes`, `related_issue_ids`, `adjustment_method`, `confidence_score`, `adjustment_attempts` | チェック完了時 |
  | `issue_resolution` | `issue_id+resolution_attempt` | `applied_fix_description`, `applied_by`, `applied_at`, `tool_used`, `diff_ref`, `verification_status`, `verification_snapshot_id`, `recurrence_score`, `recurrence_flag` | 修正適用・再チェック完了時 |
  | `manuscript_fetch_log` | `fetch_id` | `session_id`, `manuscript_hash`, `tool_id`, `result`, `latency_ms`, `attempt_index` | 本文取得試行ごと |
- 原稿本文は原則ハッシュ値のみ保持し、テキストそのものは保存しない。必要時は `.noveler/artifacts/` 等の参照キー（`manuscript_hash`, `manuscript_version_id`）を記録する。
- `WorkflowStateStore` は `begin_transaction()`, `commit()`, `rollback()` を提供し、ファイル運用時はテンポラリ→原子リネーム、DB 運用時はトランザクションで実装する。

### 2. 指摘 ID とトレーサビリティ
- `issue_id` は `ISSUE-{epoch_ms}-{random_suffix}` 形式で採番し、全履歴を通じて一意。LangGraph ノードが新規検出時に生成し、保存後は変更禁止。
- 同箇所の再発指摘は新規 `issue_id` を採番し、元 ID を `related_issue_ids` に列挙して履歴を可視化する。
- 指摘ライフサイクル: `New` → `InProgress` → `Resolved` / `Recurrence` / `Partial` / `Deferred`。
  - `New`: チェック完了時に自動設定。
  - `InProgress`: LLM または利用者がツールを選択し修正計画を登録した時点。
  - `Resolved`: 再チェックで `recurrence_score < 0.3` かつ `range_checksum` 不一致。
  - `Recurrence`: `recurrence_score >= 0.7` または `range_checksum`・`category` が一致。
  - `Partial`: `0.3 <= recurrence_score < 0.7`。追加修正が必要。
  - `Deferred`: 利用者が対応延期を明示し、`defer_reason` を設定。
- 再マッピング戦略（`range_adjustment_strategy`）は優先順位付き配列 `["exact_match", "diff3", "semantic_search", "manual_confirmation"]` を採用。
  - `exact_match`: 最新原稿から `range_checksum` と同一のテキスト片を検索。ヒット時は開始/終了オフセットを更新し `adjustment_method=exact_match`。
  - `diff3`: 旧/新スナップショットで `diff-match-patch` 互換アルゴリズムを使用。補正量と一致率を `adjustment_delta` / `confidence_score` に記録。
  - `semantic_search`: 指摘周辺 ±100 文字を埋め込み比較し、類似度 0.8 以上の最長一致候補を採用。
  - `manual_confirmation`: 上記手順が失敗した場合、QC-013（REQUIRES_USER_ALIGNMENT）を発行し、ユーザー確認後に位置を確定。`confidence_score` < 0.6 の場合は自動で `Partial` 状態へ戻す。
  - 全ての試行順序と結果（成功/失敗）を `adjustment_attempts` に配列で保存。

### 3. 本文アクセス制御とトークン削減
- 原稿本文はハッシュ値で受け渡し、LLM プロンプトへ直接埋め込むのは必要最小限の抜粋のみ。
- 本文取得のツール優先順位: `fetch_artifact` → `read_snapshot` → `request_manual_upload`。
  - 成功時は SHA256 を再計算し `manuscript_hash` と一致することを検証。
  - 失敗時の QC コード: キャッシュ未ヒットは `QC-015`、ストレージ取得失敗は `QC-016`、手動アップロード待ちは `QC-017`、ハッシュ不一致は `QC-018`。
  - LangGraph ノードは `manuscript_fetch_log` を更新し、IterationPolicy に従って最大 3 回再試行（指数バックオフ: 1s, 2s, 4s）。成功したツールは次回優先。
- LLM へ渡す抜粋は、抽出範囲・ハッシュ・取得元キーをメタデータとして残し、監査ログへ記録。

### 4. LLM ツール提示
- `category_tool_map` に `tool_id`, `min_severity`, `requires_user_confirmation`, `fallback_tool_id`, `notes` を定義。
- LangGraph ノード `PlanFixStep` が `available_tools`（JSON 配列）を生成し、LLM プロンプトへ埋め込む。
- 提示失敗時は `ToolUnavailableError` を発行し、`fallback_tool_id` を適用。ユーザーが拒否した場合は `issue.state=Deferred`、`defer_reason=USER_REJECTED_TOOL` を記録。

### 5. LangGraph PoC 成功指標
- 測定根拠（2025-08-01〜2025-08-20 の運用ログより）:

  | 指標 | 現行中央値 / 平均 | サンプル数 (n) | 目標値 |
  | --- | --- | --- | --- |
  | セッション再開時間 | 45秒 (中央値) | 42 | ≤ 30秒 |
  | 再チェック判定一致率 | 91% | 20 | ≥ 95% |
  | 状態ストア応答 | 750ms | 15 | ≤ 500ms |
  | QC-00x マッピングテスト成功率 | 80% | 20 (正常10/異常10) | 100% |

- PoC 完了条件: 上記指標が目標を満たさない場合は次フェーズ移行を保留し、改善計画を作成する。

### 6. エラー変換・リトライ整合
- 例外→QC コード変換: `PromptExecutionError`→`QC-004`, `StatePersistenceError`→`QC-009`, `ToolUnavailableError`→`QC-012`, `TemplateMismatchError`→`QC-006`, `ManualAlignmentRequired`→`QC-013`, `ManuscriptHashMismatchError`→`QC-018`。
- IterationPolicy フィールド: `count`, `until_pass`, `time_budget_sec`, `min_improvement`。CLI 引数で上書き可能。`session.iteration_policy` に保存。
- `WorkflowStateStore.begin_session` 時に `episode_number` 単位のロックを取得。例外発生時は `rollback()`→ロック解放。ロック情報はメモリ/ファイル/DB 実装に合わせた `locks` テーブルで追跡。

### 7. 検証・テスト要件
- ユニット: ID 採番、`WorkflowStateStore` トランザクション、ライフサイクル遷移、再マッピング戦略、ツール提示ロジック、本文ハッシュ参照。
- 統合: LangGraph ノード（スタブ LLM）で状態保存→QC コード変換→ロック解放→本文取得を検証。
- E2E: `noveler check` / `noveler polish` から PoC フローを実行し、履歴再現・未解消指摘抽出・ハッシュ参照を確認。テストケース表に入力原稿、指摘内容、期待値を明記。

### 8. ドキュメント更新
- SPEC-QUALITY-110: 指摘データモデル、再発判定アルゴリズム、IterationPolicy、監査ログ、本文ハッシュ運用を追加。
- SPEC-MCP-002: `iteration_policy` パラメータ、ロック取得レスポンス、`issue` の新フィールド例、本文取得 API 利用手順を追記。
- B20_Claude_Code 開発作業指示書: LangGraph ノード TDD 手順、`available_tools` 書式、トランザクション検証、ハッシュ参照実装ルールを更新。
- templates/README: `available_tools` JSON 例、`tool_selection_status` 更新ルール、本文抜粋テンプレートを追加。

## 非機能要件
- 同時セッション数: 10（現行 5）まで性能劣化無し。閾値超過時は待機キューへ格納。
- 応答時間: 状態保存 ≤300ms、セッション再開 ≤30秒、ハッシュ照会による本文取得 ≤1秒。
- 可用性: 失敗時は直前コミットポイントから復元。ファイル保存は原子リネーム、DB 保存はトランザクションでアトミック性を保証。
- セキュリティ: 指摘履歴アクセスはセッション開始者/管理者に制限。監査ログを `.noveler/audit/{YYYYMM}/` に保存し 90 日後アーカイブ。アクセス権限・削除ポリシーを SPEC に記載。

## 移行計画とロールバック
- フェーズ:
  1. `WorkflowStateStore` 導入（既存実装ラップ、ID 採番共通化）。
  2. 指摘ライフサイクル/ツール提示/本文ハッシュ参照の記録拡張。
  3. LangGraph PoC 導入（feature flag 制御、指標計測）。
  4. 静的解析・テストカバレッジ拡張（mutation test 20 ケース、E2E 5 ケース追加）。
  5. 本運用リリースと監査ログ運用開始。
- ロールバック:
  - フェーズ 3 以降で障害発生時は feature flag で旧実装へ切り戻し。
  - 新フィールドは互換維持（未使用時 NULL）とし、切戻し後の処理を検証。
  - `state_version` でバージョン整合性を確認し、整合性チェックツールで差分を検証。

## リスクと留意点
- 状態永続化の二重管理期間は専用差分ツールで整合性確認を行う。
- LangGraph のアップデートに備え、CI にテンプレート整合・バージョン検査を追加。
- MCP API 互換維持のため、変換レイヤーの E2E テストと回帰テストを整備。

## 次のアクション
1. 現行ワークフローの失敗ログと再実行コストを詳細分析し、PoC 指標の測定方法をドキュメント化する。
2. `WorkflowStateStore` の API 定義・ロック/トランザクション実装方式を設計し、プロトタイプを作成する。
3. LangGraph PoC を実装し、QC-00x マッピング・再チェック挙動・ツール提示・本文ハッシュ参照をテストする。
4. PoC 評価後、移行ロードマップとドキュメント改訂計画（SPEC/TODO/README 更新）を確定する。
