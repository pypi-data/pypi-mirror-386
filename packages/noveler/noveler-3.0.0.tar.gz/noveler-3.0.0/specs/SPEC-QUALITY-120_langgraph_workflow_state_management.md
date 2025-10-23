# SPEC-QUALITY-120: LangGraph Workflow State Management

## メタデータ

| 項目 | 内容 |
|------|------|
| 仕様ID | SPEC-QUALITY-120 |
| E2EテストID | E2E-QUALITY-120 |
| test_type | e2e / integration / unit |
| バージョン | v1.0.0 |
| 作成日 | 2025-09-26 |
| 最終更新 | 2025-09-26 |
| ステータス | draft |
| 関連仕様 | SPEC-QUALITY-110, SPEC-MCP-002, SPEC-LLM-001, SPEC-A40A41-STAGE23-POLISH |

## 1. 概要

LangGraph を用いて品質チェック→修正→再チェックのループを制御し、指摘履歴・本文参照・LLM ツール選定を一貫して管理するためのワークフロー基盤を規定する。`WorkflowStateStore` を軸に全ステップの状態をハッシュベースで記録し、MCP 経由の既存クライアントとの互換性を維持したまま状態再開・フォールバック・再実行を信頼性高く運用可能にする。

## 2. ビジネス要件

### 2.1 目的
- 品質チェックサイクルにおける指摘の取りこぼしを防ぎ、修正履歴を追跡可能にする。
- LLM の再実行や手動修正を円滑にし、編集者の確認工数を削減する。
- 原稿本文をハッシュ参照で扱い、トークンコストと情報漏洩リスクを低減する。

### 2.2 成功基準
- セッション再開時間中央値 ≤ 30 秒（現行 45 秒）。
- 再チェック判定一致率 ≥ 95%（現行 91%）。
- 状態ストア応答 ≤ 500 ms（現行 750 ms）。
- QC-00x マッピングテスト成功率 100%（正常10件・異常10件）。

### 2.3 測定根拠

| 指標 | 現行値 (期間: 2025-08-01〜2025-08-20) | サンプル数 | 改善目標 |
|------|---------------------------------|------------|-----------|
| セッション再開時間 | 45 秒（中央値） | n=42 | ≤ 30 秒 |
| 再チェック判定一致率 | 91% | n=20 | ≥ 95% |
| 状態ストア応答 | 750 ms（平均） | n=15 | ≤ 500 ms |
| QC-00x マッピング成功率 | 80% | n=20（正常10/異常10） | 100% |

目標未達の場合は PoC フェーズを維持し、改善策を追加してからフェーズ移行する。

## 3. 機能仕様

### 3.1 スコープ
- **含まれるもの**: WorkflowStateStore の設計、指摘 ID とライフサイクル、本文ハッシュ取得フロー、LangGraph PoC、LLM ツール提示、QC エラー変換、PoC 評価指標。
- **含まれないもの**: UniversalLLMUseCase 自体の改修、MCP クライアント/UI の大幅変更、DB 実装の具体的なマイグレーション手順。

### 3.2 ユースケース

#### UC-120-001: 品質チェックセッションの開始
```yaml
前提条件: episode 原稿が artifacts に保存済み、MCP サーバー稼働中
アクター: noveler CLI (ユーザー)
入力: episode_number=1, iteration_policy={"count":2, "until_pass":true}
処理手順:
  1. WorkflowStateStore.begin_session() を呼び出しロック取得。
  2. LangGraph ノードが templates/quality/checks を読み取り Step1 プロンプト生成。
  3. LLM 応答から issues と metrics を抽出し state_store に保存。
期待出力: session_id, 初回 issues, manifest ログ。
事後条件: session 状態が active、lock_status=held。
```

#### UC-120-002: 指摘修正と再チェック
```yaml
前提条件: UC-120-001 が完了し、issue が New 状態で存在
アクター: LangGraph (システム)
入力: issue_id, category_tool_map, manuscript_hash
処理手順:
  1. PlanFixStep が available_tools を生成し LLM へ提示。
  2. 修正提案を適用し issue_resolution を登録。
  3. 再チェックを実行し recurrence_score を算出、issue state を更新。
期待出力: issue 状態=Resolved/Partial/Recurrence、resolution ログ。
事後条件: step_execution が追記され、必要に応じ manifest に IterationPolicy 履歴を追加。
```

#### UC-120-003: 本文抜粋の取得
```yaml
前提条件: session 内に manuscript_hash が存在
アクター: LangGraph ノード
入力: manuscript_hash, range_checksum
処理手順:
  1. fetch_artifact を試行。失敗時は read_snapshot, 次に request_manual_upload。
  2. 取得した本文の SHA256 を検証。
  3. 抜粋を生成し LLM へ送付。メタデータを manuscript_fetch_log に保存。
期待出力: 抜粋テキスト, メタデータ。
事後条件: fetch_log に結果が残り、再利用時は成功ツールを優先。
```

### 3.3 再マッピング戦略
- 再マッピング順序: `range_adjustment_strategy = ["exact_match", "diff3", "semantic_search", "manual_confirmation"]`。
  - `exact_match`: 最新原稿から `range_checksum` と一致するテキスト片を探索。ヒット時は開始/終了オフセットを更新し `adjustment_method=exact_match`、`confidence_score=1.0`。
  - `diff3`: 旧旧/新差分を `diff-match-patch` 互換アルゴリズムで補正し `adjustment_delta` を保存。成功時は `adjustment_method=diff3`、`confidence_score=0.7~0.9`。
  - `semantic_search`: 指摘周辺±100文字を埋め込み比較し類似度 ≥ 0.8 の最長一致候補を採用。`confidence_score` は類似度を記録。
  - `manual_confirmation`: 上記が失敗、または `confidence_score < 0.6` の場合に QC-013（ManualAlignmentRequired）を発行し、ユーザー入力で範囲を確定。結果を `adjustment_method=manual_confirmation`, `confidence_score=<user_confirmed>` として保存。
- すべての試行結果は `adjustment_attempts` 配列へ `{strategy, result, confidence}` 形式で記録する。
- 再チェック時に `confidence_score < 0.6` の指摘は自動で `Partial` 状態へ戻す。

### 3.4 本文取得フロー
- ツール優先順位: `fetch_artifact` → `read_snapshot` → `request_manual_upload`。
- 失敗時 QC コード:
  - キャッシュ未ヒット: `QC-015`（ManuscriptCacheMiss）。
  - ストレージ取得失敗: `QC-016`（ManuscriptStorageFailure）。
  - 手動アップロード待ち: `QC-017`（ManualUploadPending）。
  - ハッシュ不一致: `QC-018`（ManuscriptHashMismatch）。
- 再試行: 最大 3 回、指数バックオフ（1s→2s→4s）。成功したツールは次回優先順位の先頭へ移動。
- `manuscript_fetch_log` には `tool_id`, `result`, `latency_ms`, `attempt_index`, `qc_code` を記録し、成功時には `excerpt_hash`, `excerpt_length`, `source_key`（artifact_id 等）も保存。
- LLM へ渡す抜粋は最小必要範囲に限定し、メタデータ（`excerpt_hash`, `range_checksum`, `manuscript_hash`）をプロンプトに添付する。

## 4. 技術仕様

### 4.0 既存実装調査（必須）
1. `grep -i "ProgressiveCheck" CODEMAP.yaml` で既存関連モジュールを確認。
2. 共有コンポーネント: `PathService`, `StructuredLogger`, `UniversalLLMUseCase`, `ProgressiveCheckManager`。
3. 類似実装: `find src -name "*progressive_check*"` でテンプレート取得処理と比較。
4. 再利用可否: 既存 `ProgressiveCheckManager` を LangGraph 対応へ拡張、状態保存処理は新規ラッパー実装が必要。

### 4.1 インターフェース定義

```python
# File: src/noveler/domain/services/workflow_state_store.py
class WorkflowStateStore(Protocol):
    """Persists session/step/issue state for LangGraph-driven workflows."""

    def begin_session(self, episode_number: int, iteration_policy: IterationPolicy) -> SessionContext:
        """Create session record and acquire episode-level lock."""

    def record_step_execution(self, payload: StepExecutionPayload) -> None:
        """Persist step inputs/outputs including manuscript_hash references."""

    def record_issue(self, issue: IssuePayload) -> None:
        """Store new or recurring issue with lifecycle metadata."""

    def record_issue_resolution(self, resolution: IssueResolutionPayload) -> None:
        """Attach resolution attempt and verification snapshot."""

    def append_fetch_log(self, log: ManuscriptFetchLog) -> None:
        """Track manuscript retrieval attempts and results."""

    def commit(self) -> None:
        """Commit pending changes atomically."""

    def rollback(self) -> None:
        """Rollback pending changes and release locks."""
```

### 4.2 データモデル

```yaml
Session:
  properties:
    session_id: string (required, UUID)
    episode_number: int (required)
    iteration_policy:
      count: int
      until_pass: bool
      time_budget_sec: int
      min_improvement: float
    lock_status: enum [held, released]
    created_at: datetime
    current_status: enum [active, completed, failed]
    state_version: int

Issue:
  properties:
    issue_id: string (required, pattern: ISSUE-*)
    session_id: string (required)
    step_id: int (required)
    manuscript_hash: string (required)
    text_range:
      start_char: int
      end_char: int
      start_line: int
      end_line: int
    range_checksum: string
    category: string
    severity: enum [low, medium, high, critical]
    state: enum [New, InProgress, Resolved, Recurrence, Partial, Deferred]
    adjustment_method: string
    confidence_score: float
    adjustment_attempts: list

IssueResolution:
  properties:
    issue_id: string (required)
    resolution_attempt: int
    applied_fix_description: string
    tool_used: string
    diff_ref: string
    verification_status: enum [passed, recurrence, partial]
    verification_snapshot_id: string
    recurrence_score: float

ManuscriptFetchLog:
  properties:
    fetch_id: string (UUID)
    session_id: string
    manuscript_hash: string
    tool_id: string
    result: enum [success, failure]
    latency_ms: int
    attempt_index: int
    qc_code: string
    excerpt_hash: string?
    excerpt_length: int?
    source_key: string?
```

## 5. 検証仕様

### 5.1 PoC 成功指標検証
- 指標ごとの検証テストを `tests/performance/test_progressive_check_metrics.py`（新設）で測定。
- 成功条件: 2.3 の目標値を全て満たす。未達の場合は CI を fail させず WARN とし、レポートを `reports/langgraph_poc_metrics.md` に出力。

### 5.2 E2Eテストシナリオ (test_type: e2e)

```gherkin
Feature: LangGraph workflow persists issues and supports restarts

  Scenario: Resume session after manual interruption
    Given episode 1 session is active with two issues recorded
    And WorkflowStateStore snapshots are committed
    When the user reruns "noveler check 1 --auto-fix"
    Then the session resumes within 30 seconds
    And unresolved issues remain flagged with state Partial
```

### 5.3 統合テスト項目 (test_type: integration)

| テストID | テスト内容 | 期待結果 |
|----------|------------|----------|
| INT-QUALITY-120-001 | LangGraph ノード→WorkflowStateStore 書き込み | step_execution が永続化される |
| INT-QUALITY-120-002 | 再マッピング diff3 手順 | adjustment_method=diff3, confidence_score>=0.7 |
| INT-QUALITY-120-003 | Manuscript fetch fallback | QC-015/016/017 が正しく発行される |
| INT-QUALITY-120-004 | QC-00x 変換 | 例外ごとに期待 QC コードが返る |
| INT-QUALITY-120-005 | IterationPolicy 強制終了 | count/time_budget 超過時に停止 |

### 5.4 単体テスト項目 (test_type: unit)

| テストID | テスト対象 | テスト内容 | 期待結果 |
|----------|------------|----------|----------|
| UNIT-QUALITY-120-001 | workflow_state_store.begin_session | ロック取得と state_version 初期化 |
| UNIT-QUALITY-120-002 | range_adjustment.exact_match | テキスト一致でオフセット更新 |
| UNIT-QUALITY-120-003 | range_adjustment.semantic_search | 類似度 < 0.8 で ManualAlignmentRequired 送出 |
| UNIT-QUALITY-120-004 | manuscript_fetch.retry_policy | 最大3回再試行し指数バックオフを記録 |
| UNIT-QUALITY-120-005 | iteration_policy.enforce | count/time_budget 超過時に停止 |

## 6. 非機能要件

### 6.1 パフォーマンス
- 状態保存 API レイテンシー ≤ 300 ms。
- セッション再開処理 ≤ 30 秒。
- ハッシュ参照本文取得 ≤ 1 秒。

### 6.2 セキュリティ
- 指摘履歴はセッション開始者と管理者のみ閲覧可。RBAC を施行。
- 監査ログ (`.noveler/audit/{YYYYMM}/audit.log`) を 90 日保存後にアーカイブ。

### 6.3 可用性
- ロック領域破損時は自動ロールバックし、管理者通知を行う。
- フェイルオーバー時は state_version を確認し二重書き込みを防止。

## 7. エラーハンドリング
- `PromptExecutionError` → `QC-004`（LLM 実行失敗）。
- `StatePersistenceError` → `QC-009`（状態保存失敗）。
- `ToolUnavailableError` → `QC-012`（推奨ツール未準備）。
- `ManualAlignmentRequired` → `QC-013`（手動位置調整が必要）。
- `ManuscriptCacheMissError` → `QC-015`、`ManuscriptStorageError` → `QC-016`、`ManualUploadPending` → `QC-017`、`ManuscriptHashMismatchError` → `QC-018`。

## 8. 監査・ログ
- 監査ログ項目: `timestamp`, `session_id`, `issue_id`, `action`, `performed_by`, `tool_used`, `qc_code`, `metadata`。
- LangGraph 実行ログに `adjustment_attempts`, `confidence_score`, `manuscript_fetch_log` を含め、LLM 入出力は `.noveler/checks/{session_id}/` に保存。

## 9. 移行計画
1. `WorkflowStateStore` ラッパーを実装し既存 ProgressiveCheckManager から呼び出し。
2. range_adjustment / manuscript_fetch モジュールを追加し単体テストを整備。
3. LangGraph 実装は既定経路であり、`NOVELER_LG_PROGRESSIVE_CHECK` を `0` に設定した場合は警告を発行し、`"LangGraph workflow is mandatory"` ガイダンスを返却して実行を継続する。
4. KPI 達成後、旧フォールバックは削除済み。`.noveler/checks/{session_id}/` への manifest / 入出力ログ生成は必須要件として CI テストで検証する。

## 10. 未決事項
- DB 永続化への移行時期と採用するストレージ（SQLite / PostgreSQL / DynamoDB 等）。
- semantic_search の埋め込みモデル管理（ローカル vs API）。
- request_manual_upload の UI/通知手段（CLI vs MCP GUI）。

## 11. 参考資料
- requirements/langgraph_workflow_state_management.md
- SPEC-QUALITY-110_progressive_check_flow.md
- SPEC-MCP-002_mcp-tools-specification.md
- SPEC-LLM-001_polish_manuscript_apply_integration.md
