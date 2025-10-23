---
spec_id: SPEC-PLOT-005
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: PLOT
sources: [REQ]
tags: [plot]
---
# SPEC-PLOT-005: PlotCreationTask エンティティ仕様書

## 要件トレーサビリティ

**要件ID**: REQ-PLOT-005 (プロットバージョン管理)
**実装状況**: 🔄実装中
**テストカバレッジ**: tests/unit/test_plot_creation_entity.py (予定)
**関連仕様書**: SPEC-PLOT-001_claude-code-integration-plot-generation.md

**作成日**: 2025-01-22
**バージョン**: 1.1
**カテゴリ**: Domain Entity
**依存関係**: MergeStrategy, WorkflowStageType

## 概要

プロット作成タスクの状態とビジネスルールを管理するエンティティ。プロット作成ワークフローの各段階（マスタープロット、章別プロット、話数別プロット）でのタスク実行を統制し、適切な状態遷移と出力ファイル管理を行う。

## ドメインコンテキスト

**問題領域**: プロット作成ワークフローの複雑な状態管理
- マルチステージワークフロー（マスター→章別→話数別）の統制
- タスクの状態遷移とエラーハンドリング
- 出力ファイルのパス生成とマージ戦略適用
- タスクの実行時間とライフサイクル追跡

**解決アプローチ**: 状態機械パターンによるタスク制御
- WorkflowStageTypeによる段階的処理定義
- MergeStrategyによる安全なファイル操作制御
- 時刻記録による実行トレーサビリティ確保
- 例外安全な状態遷移の実装

## エンティティ設計

### 1. PlotCreationTask（集約ルート）

プロット作成タスクの完全なライフサイクルを管理。

**責務**:
- タスク状態の管理と遷移制御
- ワークフロー段階に応じた出力パス生成
- マージ戦略の適用と安全性確保
- 実行時間の追跡とエラー情報の記録
- 作成ファイルリストの管理

**ビジネス不変条件**:
1. **状態遷移制約**: pending → in_progress → (completed|failed) の一方向遷移
2. **時刻整合性**: started_at ≤ (completed_at|failed_at)
3. **エラー情報**: failed状態の場合、error_messageが必須
4. **ファイルリスト**: completed状態の場合、created_filesが設定済み
5. **パラメータ検証**: ワークフロー段階に必要なパラメータが存在

### 2. ビジネスルール

#### 2.1 タスク実行制御
```python
# BR-1: pending状態のタスクのみ実行開始可能
def start_execution(self) -> None:
    if self.status != "pending":
        raise ValueError("タスクは既に実行中または完了しています")

    self.status = "in_progress"
    self.started_at = datetime.now()

# BR-2: in_progress状態のタスクのみ完了可能
def complete_execution(self, created_files: list[str]) -> None:
    if self.status != "in_progress":
        raise ValueError("タスクは実行中ではありません")

    self.status = "completed"
    self.completed_at = datetime.now()
    self.created_files = created_files.copy()

# BR-3: pending/in_progress状態のタスクのみ失敗可能
def fail_execution(self, error_message: str) -> None:
    if self.status not in ["pending", "in_progress"]:
        raise ValueError("タスクは既に完了または失敗しています")

    self.status = "failed"
    self.failed_at = datetime.now()
    self.error_message = error_message
```

#### 2.2 出力パス生成
```python
# BR-4: ワークフロー段階に応じた適切なパス生成
def generate_output_path(self) -> str:
    match self.stage_type:
        case WorkflowStageType.MASTER_PLOT:
            return f"{self.project_root}/20_プロット/全体構成.yaml"
        case WorkflowStageType.CHAPTER_PLOT:
            chapter = self.parameters["chapter"]  # 必須パラメータ
            return f"{self.project_root}/20_プロット/章別プロット/第{chapter}章.yaml"
        case WorkflowStageType.EPISODE_PLOT:
            episode = self.parameters["episode"]  # 必須パラメータ
            return f"{self.project_root}/20_プロット/話数別プロット/第{episode:03d}話_プロット.yaml"
        case _:
            raise ValueError(f"不明なワークフロー段階: {self.stage_type}")
```

#### 2.3 状態判定
```python
# BR-5: 状態判定メソッド
def is_completed(self) -> bool:
    return self.status == "completed"

def is_failed(self) -> bool:
    return self.status == "failed"

def is_in_progress(self) -> bool:
    return self.status == "in_progress"
```

## テスト要求仕様

### 1. 状態遷移テスト

#### 1.1 正常な状態遷移
- **TEST-1**: `test_task_normal_execution_flow`
  - pending → in_progress → completed の正常遷移
  - 各段階で適切な時刻が記録される
  - created_filesが正しく保存される

#### 1.2 失敗時の状態遷移
- **TEST-2**: `test_task_failure_from_pending`
  - pending → failed の遷移
  - error_messageが正しく記録される
- **TEST-3**: `test_task_failure_from_in_progress`
  - in_progress → failed の遷移

#### 1.3 不正な状態遷移
- **TEST-4**: `test_start_execution_invalid_status`
  - in_progress/completed/failed状態からの開始試行でValueError
- **TEST-5**: `test_complete_execution_invalid_status`
  - pending/completed/failed状態からの完了試行でValueError
- **TEST-6**: `test_fail_execution_invalid_status`
  - completed/failed状態からの失敗試行でValueError

### 2. 出力パス生成テスト

#### 2.1 マスタープロット
- **TEST-7**: `test_generate_output_path_master_plot`
  - MASTER_PLOTでの正しいパス生成
  - パラメータ不要の確認

#### 2.2 章別プロット
- **TEST-8**: `test_generate_output_path_chapter_plot`
  - CHAPTER_PLOTでの正しいパス生成
  - chapterパラメータの使用確認
- **TEST-9**: `test_generate_output_path_chapter_plot_missing_parameter`
  - chapterパラメータ不足時のKeyError

#### 2.3 話数別プロット
- **TEST-10**: `test_generate_output_path_episode_plot`
  - EPISODE_PLOTでの正しいパス生成（3桁ゼロパディング）
  - episodeパラメータの使用確認
- **TEST-11**: `test_generate_output_path_episode_plot_missing_parameter`
  - episodeパラメータ不足時のKeyError

#### 2.4 不正な段階タイプ
- **TEST-12**: `test_generate_output_path_unknown_stage`
  - 未定義のWorkflowStageTypeでValueError

### 3. 初期化テスト

#### 3.1 正常な初期化
- **TEST-13**: `test_initialization_with_defaults`
  - デフォルトパラメータでの初期化確認
  - merge_strategy=MergeStrategy.MERGE
  - status="pending"
  - タイムスタンプの正確性
- **TEST-14**: `test_initialization_with_custom_merge_strategy`
  - カスタムマージ戦略での初期化

#### 3.2 初期状態検証
- **TEST-15**: `test_initial_state_verification`
  - 初期化直後の全属性確認
  - None値の属性確認
  - 空のcreated_filesリスト

### 4. 状態判定テスト

#### 4.1 状態判定メソッド
- **TEST-16**: `test_status_check_methods`
  - is_completed(), is_failed(), is_in_progress()の正確性
  - 各状態での真偽値確認

### 5. エラーハンドリングテスト

#### 5.1 パラメータ検証
- **TEST-17**: `test_parameter_validation_for_chapter_plot`
  - 章別プロットでchapterパラメータ必須検証
- **TEST-18**: `test_parameter_validation_for_episode_plot`
  - 話数別プロットでepisodeパラメータ必須検証

#### 5.2 マージ戦略検証
- **TEST-19**: `test_merge_strategy_properties`
  - MergeStrategy.is_safe プロパティ検証
  - MergeStrategy.requires_confirmation プロパティ検証

### 6. 時刻整合性テスト

#### 6.1 実行時刻記録
- **TEST-20**: `test_execution_timestamps_consistency`
  - created_at ≤ started_at ≤ completed_at の順序確認
- **TEST-21**: `test_failure_timestamps_consistency`
  - created_at ≤ started_at ≤ failed_at の順序確認

### 7. データ不変性テスト

#### 7.1 created_files保護
- **TEST-22**: `test_created_files_immutability`
  - complete_execution時のリストコピー確認
  - 外部変更からの保護確認

## 実装上の注意点

### 1. 型安全性
- すべてのメソッドで型ヒント必須
- datetime型の適切な使用
- Optional型の明示的指定

### 2. 例外安全性
- 状態変更の原子性確保
- エラー時の部分更新回避
- 適切な例外型の選択

### 3. テスト可能性
- 時刻依存性の抽出可能設計
- モック可能な外部依存性
- 状態の検証可能性

### 4. パフォーマンス
- 不必要なオブジェクト生成回避
- メモリ効率的なファイルリスト管理
- 計算量O(1)の状態判定

## 関連仕様書

- **MergeStrategy値オブジェクト**: `merge_strategy.spec.md`
- **WorkflowStageType値オブジェクト**: `workflow_stage_type.spec.md`
- **プロット作成ユースケース**: `plot_creation_use_case.spec.md`

---
**更新履歴**:
- 2025-01-22: 初版作成（TDD+DDD原則準拠）
