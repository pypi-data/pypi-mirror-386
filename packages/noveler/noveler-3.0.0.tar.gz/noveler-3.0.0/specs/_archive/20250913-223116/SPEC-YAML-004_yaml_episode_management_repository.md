# YAMLエピソード管理リポジトリ仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、エピソード管理アグリゲートのYAMLファイルベース永続化を提供する。エピソードライフサイクル管理、ワークフロー制御、進捗追跡を統合的に行う。

### 1.2 スコープ
- エピソード管理アグリゲートの完全な永続化・復元
- ワークフロー状態管理と遷移制御
- 進捗追跡・統計データの管理
- 依存関係管理（前話・次話・章構成）
- プロジェクト横断的なエピソード分析
- バッチ操作・一括処理機能

### 1.3 アーキテクチャ位置
```
Domain Layer
├── EpisodeManagementAggregate (Aggregate Root) ← Infrastructure Layer
├── EpisodeWorkflow (Entity)                   └── YamlEpisodeManagementRepository
├── EpisodeProgress (Entity)                   └── EpisodeWorkflowManager
├── EpisodeDependency (Entity)                 └── ProgressCalculator
├── WorkflowState (Value Object)               └── DependencyResolver
└── ProgressMetrics (Value Object)             └── BatchOperationManager
```

### 1.4 ビジネス価値
- **統合管理**: エピソード関連の全ての管理データを一元化
- **ワークフロー制御**: 柔軟なエピソード状態遷移とビジネスルール適用
- **進捗可視化**: リアルタイムな進捗追跡と統計分析
- **依存関係管理**: エピソード間の関連性と整合性保証

## 2. 機能仕様

### 2.1 基本管理操作
```python
# アグリゲート管理
def save_episode_management(management: EpisodeManagementAggregate) -> None
def load_episode_management(project_id: str) -> EpisodeManagementAggregate | None
def delete_episode_management(project_id: str) -> bool

# エピソード管理
def add_episode_to_management(project_id: str, episode_info: EpisodeInfo) -> None
def remove_episode_from_management(project_id: str, episode_number: int) -> bool
def update_episode_info(project_id: str, episode_number: int, info: EpisodeInfo) -> None
```

### 2.2 ワークフロー管理
```python
# ワークフロー操作
def transition_episode_state(
    project_id: str,
    episode_number: int,
    to_state: WorkflowState,
    context: TransitionContext
) -> bool

def get_available_transitions(project_id: str, episode_number: int) -> list[WorkflowState]
def validate_workflow_transition(
    current_state: WorkflowState,
    to_state: WorkflowState,
    context: TransitionContext
) -> ValidationResult

# ワークフロー設定
def set_custom_workflow(project_id: str, workflow_config: WorkflowConfiguration) -> None
def get_workflow_history(project_id: str, episode_number: int) -> list[WorkflowTransition]
```

### 2.3 進捗管理
```python
# 進捗追跡
def update_episode_progress(project_id: str, episode_number: int, progress: ProgressUpdate) -> None
def calculate_project_progress(project_id: str) -> ProjectProgressMetrics
def get_episode_progress_details(project_id: str, episode_number: int) -> EpisodeProgress

# 統計・分析
def get_completion_statistics(project_id: str) -> CompletionStats
def analyze_productivity_trends(project_id: str, period: TimePeriod) -> ProductivityAnalysis
def generate_progress_report(project_id: str, report_type: str) -> ProgressReport
```

### 2.4 依存関係管理
```python
# 依存関係設定
def add_episode_dependency(
    project_id: str,
    episode_number: int,
    depends_on: list[int],
    dependency_type: DependencyType
) -> None

def remove_episode_dependency(project_id: str, episode_number: int, dependency_id: str) -> bool
def validate_dependencies(project_id: str) -> list[DependencyConflict]

# 順序・構成管理
def reorder_episodes(project_id: str, new_order: list[int]) -> bool
def organize_by_chapters(project_id: str, chapter_structure: ChapterStructure) -> None
def validate_episode_sequence(project_id: str) -> SequenceValidationResult
```

### 2.5 バッチ操作
```python
# 一括状態更新
def bulk_update_status(
    project_id: str,
    episode_numbers: list[int],
    new_status: WorkflowState
) -> BatchOperationResult

def bulk_apply_workflow_action(
    project_id: str,
    episode_numbers: list[int],
    action: WorkflowAction
) -> BatchOperationResult

# 一括分析
def bulk_analyze_episodes(project_id: str, analysis_type: str) -> BulkAnalysisResult
def batch_progress_update(project_id: str, updates: list[ProgressUpdate]) -> BatchUpdateResult
```

## 3. データ構造仕様

### 3.1 ファイル配置
```
プロジェクトルート/
├── 50_管理資料/                    # 管理データ（YAML）
│   ├── エピソード管理.yaml          # メインエピソード管理ファイル
│   ├── ワークフロー履歴.yaml        # ワークフロー履歴
│   ├── 進捗データ.yaml              # 進捗追跡データ
│   ├── 依存関係.yaml                # エピソード依存関係
│   └── .management_backup/          # 管理データバックアップ
│       ├── エピソード管理_20250721_143022.yaml
│       ├── ワークフロー履歴_20250721_143022.yaml
│       └── 進捗データ_20250721_143022.yaml
└── 管理統計/                        # 統計・分析結果（オプション）
    ├── 進捗レポート_202507.yaml
    ├── 生産性分析_202507.yaml
    └── 完成度分析_202507.yaml
```

### 3.2 エピソード管理YAML構造
```yaml
# エピソード管理.yaml
metadata:
  project_id: "project-001"
  project_name: "転生したら最強の魔法使いだった件"
  aggregate_id: "episode-management-001"
  version: "2.1.0"
  created_at: "2025-07-15T10:30:00"
  last_updated: "2025-07-21T14:30:22"
  total_episodes: 15
  schema_version: "2.1.0"

episodes:
  - episode_number: 1
    episode_id: "episode-001"
    title: "異世界転生"
    current_state: "PUBLISHED"
    workflow_config: "standard_workflow"

    # 基本情報
    basic_info:
      created_at: "2025-07-15T10:30:00"
      updated_at: "2025-07-21T14:30:22"
      author: "山田太郎"
      word_count: 3247
      target_word_count: 3000
      character_count: 9874
      page_count: 13

    # ワークフロー状態
    workflow_state:
      current_state: "PUBLISHED"
      previous_state: "REVIEWED"
      state_changed_at: "2025-07-21T12:00:00"
      available_transitions: ["ARCHIVE", "REVISION_REQUIRED"]
      workflow_locked: false
      locked_reason: null
      auto_transition_enabled: true

    # 進捗情報
    progress:
      completion_percentage: 100.0
      writing_progress: 100.0
      review_progress: 100.0
      editing_progress: 100.0
      quality_check_progress: 100.0

      # 段階別タイムスタンプ
      milestones:
        draft_started: "2025-07-15T10:30:00"
        draft_completed: "2025-07-16T15:45:00"
        review_started: "2025-07-17T09:00:00"
        review_completed: "2025-07-17T14:30:00"
        editing_started: "2025-07-18T10:00:00"
        editing_completed: "2025-07-18T16:45:00"
        published: "2025-07-21T12:00:00"

      # 実働時間
      time_tracking:
        total_writing_minutes: 180
        total_editing_minutes: 45
        total_review_minutes: 30
        break_time_minutes: 15

    # 品質情報
    quality_metrics:
      current_score: 89.2
      target_score: 85.0
      quality_gate_passed: true
      last_quality_check: "2025-07-18T16:30:00"
      quality_trend: "improving"
      issues_count: 2

    # メタデータ
    metadata:
      tags: ["転生", "魔法", "学校"]
      genre: ["ファンタジー"]
      priority: "high"
      difficulty: "medium"
      estimated_hours: 4.0
      actual_hours: 4.25

    # 依存関係
    dependencies:
      depends_on: []  # 第1話なので依存なし
      blocks: [2]     # 第2話の前提となる
      related_episodes: [2, 3]
      chapter_assignment: 1

  - episode_number: 2
    episode_id: "episode-002"
    title: "魔法学校"
    current_state: "IN_EDITING"
    workflow_config: "standard_workflow"

    basic_info:
      created_at: "2025-07-17T09:15:00"
      updated_at: "2025-07-21T14:30:22"
      author: "山田太郎"
      word_count: 2850
      target_word_count: 3000
      character_count: 8745
      page_count: 12

    workflow_state:
      current_state: "IN_EDITING"
      previous_state: "IN_REVIEW"
      state_changed_at: "2025-07-21T10:15:00"
      available_transitions: ["EDITING_COMPLETED", "REVISION_REQUIRED"]
      workflow_locked: false

    progress:
      completion_percentage: 75.0
      writing_progress: 100.0
      review_progress: 100.0
      editing_progress: 60.0
      quality_check_progress: 0.0

    # 以下同様の構造...

project_settings:
  default_workflow: "standard_workflow"
  auto_numbering: true
  chapter_based_organization: true
  progress_tracking_enabled: true
  quality_gates_enabled: true

  # ワークフロー設定
  workflow_configurations:
    standard_workflow:
      name: "標準ワークフロー"
      states: ["DRAFT", "IN_REVIEW", "IN_EDITING", "QUALITY_CHECK", "COMPLETED", "PUBLISHED"]
      transitions:
        DRAFT:
          - to: "IN_REVIEW"
            conditions: ["word_count >= target_word_count * 0.8"]
            auto_transition: false
        IN_REVIEW:
          - to: "IN_EDITING"
            conditions: ["review_completed"]
            auto_transition: true
          - to: "REVISION_REQUIRED"
            conditions: ["major_issues_found"]
            auto_transition: false

  # 自動化設定
  automation:
    auto_progress_update: true
    auto_quality_check: true
    auto_dependency_validation: true
    auto_backup_on_state_change: true

statistics:
  total_episodes: 15
  by_state:
    PUBLISHED: 8
    IN_EDITING: 3
    IN_REVIEW: 2
    DRAFT: 2
  completion_rate: 0.53
  average_episode_length: 3150
  total_word_count: 47250
  estimated_completion_date: "2025-09-15"
  current_velocity: 2.5  # episodes per week
```

### 3.3 ワークフロー履歴YAML構造
```yaml
# ワークフロー履歴.yaml
metadata:
  project_id: "project-001"
  created_at: "2025-07-15T10:30:00"
  last_updated: "2025-07-21T14:30:22"
  total_transitions: 87

workflow_history:
  - transition_id: "wf-trans-001"
    episode_number: 1
    timestamp: "2025-07-15T10:30:00"
    from_state: null
    to_state: "DRAFT"
    trigger: "episode_created"
    user_id: "user-123"
    automated: false
    context:
      reason: "新規エピソード作成"
      additional_data: {}

  - transition_id: "wf-trans-002"
    episode_number: 1
    timestamp: "2025-07-16T15:45:00"
    from_state: "DRAFT"
    to_state: "IN_REVIEW"
    trigger: "manual_transition"
    user_id: "user-123"
    automated: false
    context:
      reason: "執筆完了、レビュー開始"
      word_count_at_transition: 3247

  - transition_id: "wf-trans-003"
    episode_number: 1
    timestamp: "2025-07-17T14:30:00"
    from_state: "IN_REVIEW"
    to_state: "IN_EDITING"
    trigger: "review_completed"
    user_id: "system"
    automated: true
    context:
      reason: "レビュー完了、自動遷移"
      review_score: 88.5
      issues_found: 3

workflow_statistics:
  average_time_in_states:
    DRAFT: 1890  # minutes
    IN_REVIEW: 570
    IN_EDITING: 405
    QUALITY_CHECK: 45

  transition_success_rate: 0.96
  most_common_transitions:
    - from: "DRAFT"
      to: "IN_REVIEW"
      count: 15
    - from: "IN_REVIEW"
      to: "IN_EDITING"
      count: 13

  bottleneck_analysis:
    slowest_state: "DRAFT"
    most_revisions: "IN_EDITING"
    success_rate_by_state:
      DRAFT: 0.93
      IN_REVIEW: 0.98
      IN_EDITING: 0.89
```

### 3.4 進捗データYAML構造
```yaml
# 進捗データ.yaml
metadata:
  project_id: "project-001"
  tracking_started: "2025-07-15T10:30:00"
  last_updated: "2025-07-21T14:30:22"
  tracking_resolution: "daily"  # daily, hourly, minute

progress_tracking:
  daily_progress:
    - date: "2025-07-15"
      episodes_created: 1
      episodes_completed: 0
      words_written: 1500
      writing_time_minutes: 120
      editing_time_minutes: 0
      total_active_time: 135  # break time excluded

    - date: "2025-07-16"
      episodes_created: 1
      episodes_completed: 1
      words_written: 3200
      writing_time_minutes: 180
      editing_time_minutes: 45
      total_active_time: 240

  weekly_summaries:
    - week: "2025-W29"
      episodes_created: 3
      episodes_completed: 2
      total_words: 9450
      average_daily_words: 1350
      productivity_score: 8.5

  monthly_summaries:
    - month: "2025-07"
      episodes_created: 15
      episodes_completed: 8
      total_words: 47250
      writing_velocity: 2.5  # episodes per week
      quality_trend: "improving"

productivity_metrics:
  current_streak: 12  # days
  longest_streak: 18  # days
  average_words_per_hour: 750
  peak_productivity_time: "14:00-17:00"
  most_productive_day: "Tuesday"

  writing_patterns:
    morning_productivity: 0.7
    afternoon_productivity: 0.9
    evening_productivity: 0.6
    weekend_productivity: 0.4

  quality_correlation:
    words_vs_quality: 0.23  # correlation coefficient
    time_vs_quality: 0.67
    revision_vs_quality: 0.81

goals_and_targets:
  current_goals:
    - type: "daily_words"
      target: 1000
      current: 850
      deadline: "2025-07-21"

    - type: "weekly_episodes"
      target: 2
      current: 1.5
      deadline: "2025-07-27"

    - type: "project_completion"
      target: "2025-09-15"
      estimated: "2025-09-22"
      confidence: 0.75

  goal_history:
    - goal_id: "goal-001"
      type: "daily_words"
      target: 800
      achieved: true
      completion_date: "2025-07-10"
      success_rate: 0.85
```

### 3.5 依存関係YAML構造
```yaml
# 依存関係.yaml
metadata:
  project_id: "project-001"
  created_at: "2025-07-15T10:30:00"
  last_updated: "2025-07-21T14:30:22"
  dependency_model_version: "1.2.0"

episode_dependencies:
  - episode_number: 1
    dependencies: []  # No dependencies
    blocks: [2, 3]    # Required for episodes 2 and 3
    dependency_type: "prerequisite"
    strength: "strong"

  - episode_number: 2
    dependencies: [1]
    blocks: [4, 5]
    dependency_type: "sequential"
    strength: "medium"

  - episode_number: 3
    dependencies: [1, 2]
    blocks: [6]
    dependency_type: "character_development"
    strength: "strong"

chapter_structure:
  - chapter_number: 1
    chapter_title: "異世界への扉"
    episodes: [1, 2, 3]
    chapter_dependencies: []
    estimated_word_count: 9000

  - chapter_number: 2
    chapter_title: "魔法学校生活"
    episodes: [4, 5, 6, 7]
    chapter_dependencies: [1]
    estimated_word_count: 12000

dependency_validation:
  circular_dependencies: []
  missing_prerequisites: []
  orphaned_episodes: []
  validation_status: "valid"
  last_validation: "2025-07-21T14:30:22"

dependency_analysis:
  critical_path: [1, 2, 4, 7, 10, 13, 15]  # Episodes on critical path
  bottleneck_episodes: [4, 10]  # Episodes that block many others
  parallelizable_episodes: [[3, 5], [6, 8], [9, 11]]  # Episodes that can be worked on in parallel
```

## 4. 技術仕様

### 4.1 依存関係
```python
# 外部ライブラリ
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

# ドメイン層
from domain.entities.episode_management_aggregate import EpisodeManagementAggregate
from domain.entities.episode_workflow import EpisodeWorkflow, WorkflowState, WorkflowTransition
from domain.entities.episode_progress import EpisodeProgress, ProgressMetrics
from domain.entities.episode_dependency import EpisodeDependency, DependencyType
from domain.repositories.episode_management_repository import EpisodeManagementRepository
from domain.services.workflow_service import WorkflowService
from domain.services.progress_calculator import ProgressCalculator

# インフラ層
from infrastructure.utils.yaml_utils import YAMLHandler
from infrastructure.workflow.workflow_engine import WorkflowEngine
```

### 4.2 ワークフロー状態定義
```python
class WorkflowState(Enum):
    """エピソードワークフロー状態"""
    PLANNED = "PLANNED"                    # 企画済み
    DRAFT = "DRAFT"                        # 執筆中
    IN_REVIEW = "IN_REVIEW"                # レビュー中
    REVISION_REQUIRED = "REVISION_REQUIRED" # 修正要求
    IN_EDITING = "IN_EDITING"              # 編集中
    QUALITY_CHECK = "QUALITY_CHECK"        # 品質チェック中
    COMPLETED = "COMPLETED"                # 完成
    REVIEWED = "REVIEWED"                  # レビュー済み
    PUBLISHED = "PUBLISHED"                # 公開済み
    ARCHIVED = "ARCHIVED"                  # アーカイブ済み

class DependencyType(Enum):
    """依存関係タイプ"""
    PREREQUISITE = "prerequisite"          # 前提条件
    SEQUENTIAL = "sequential"              # 順次実行
    CHARACTER_DEVELOPMENT = "character_development"  # キャラクター開発
    PLOT_CONTINUITY = "plot_continuity"    # プロット継続性
    WORLD_BUILDING = "world_building"      # 世界観構築
    THEMATIC = "thematic"                  # テーマ的関連
```

### 4.3 エラーハンドリング
```python
# カスタム例外
class EpisodeManagementRepositoryError(Exception):
    """エピソード管理リポジトリエラー"""
    pass

class WorkflowTransitionError(EpisodeManagementRepositoryError):
    """ワークフロー遷移エラー"""
    pass

class DependencyValidationError(EpisodeManagementRepositoryError):
    """依存関係検証エラー"""
    pass

class ProgressCalculationError(EpisodeManagementRepositoryError):
    """進捗計算エラー"""
    pass

class BatchOperationError(EpisodeManagementRepositoryError):
    """バッチ操作エラー"""
    pass
```

### 4.4 進捗計算機能
```python
class ProgressCalculator:
    def calculate_episode_progress(self, episode_info: EpisodeInfo) -> ProgressMetrics:
        """個別エピソード進捗計算"""

    def calculate_project_progress(self, episodes: list[EpisodeInfo]) -> ProjectProgressMetrics:
        """プロジェクト全体進捗計算"""

    def calculate_velocity(self, completed_episodes: list[EpisodeInfo], period: timedelta) -> float:
        """執筆速度計算"""

    def estimate_completion_date(self, current_progress: float, velocity: float, remaining_work: int) -> datetime:
        """完成予定日推定"""
```

## 5. パフォーマンス要件

### 5.1 応答時間
- アグリゲート保存: 300ms以内
- アグリゲート読み込み: 200ms以内
- ワークフロー遷移: 100ms以内
- 進捗計算: 150ms以内
- 依存関係検証: 200ms以内
- バッチ操作: 2秒以内（100エピソード）

### 5.2 メモリ使用量
- アグリゲートインスタンス: 20MB以内（500エピソード）
- ワークフロー履歴: 10MB以内
- 進捗データ: 15MB以内
- 依存関係グラフ: 5MB以内

### 5.3 スケーラビリティ
- サポートエピソード数: 1000エピソード/プロジェクト
- 同時管理プロジェクト数: 100プロジェクト
- ワークフロー履歴保持: 10000レコード

## 6. 品質保証

### 6.1 データ整合性
```python
def validate_episode_management_integrity(self) -> list[str]:
    """エピソード管理の整合性検証"""

def validate_workflow_consistency(self, project_id: str) -> ValidationResult:
    """ワークフロー一貫性検証"""

def validate_dependency_graph(self, project_id: str) -> DependencyValidationResult:
    """依存関係グラフ検証"""

def validate_progress_data_consistency(self, project_id: str) -> ProgressValidationResult:
    """進捗データ整合性検証"""
```

### 6.2 エラー回復
```python
def repair_corrupted_workflow_state(self, project_id: str, episode_number: int) -> bool:
    """破損ワークフロー状態の修復"""

def reconstruct_progress_from_history(self, project_id: str) -> bool:
    """履歴からの進捗データ再構築"""

def resolve_dependency_conflicts(self, project_id: str) -> ConflictResolutionResult:
    """依存関係競合の解決"""
```

### 6.3 バックアップ・復元
```python
def create_management_backup(self, project_id: str) -> Path:
    """管理データのバックアップ作成"""

def restore_from_backup(self, project_id: str, backup_path: Path) -> bool:
    """バックアップからの復元"""

def validate_backup_integrity(self, backup_path: Path) -> bool:
    """バックアップ整合性確認"""
```

## 7. セキュリティ

### 7.1 アクセス制御
```python
class EpisodeManagementAccessControl:
    def can_modify_workflow(self, user: User, episode_number: int) -> bool:
        """ワークフロー変更権限確認"""

    def can_view_progress_data(self, user: User, project_id: str) -> bool:
        """進捗データ閲覧権限確認"""

    def can_manage_dependencies(self, user: User, project_id: str) -> bool:
        """依存関係管理権限確認"""
```

### 7.2 監査ログ
```python
def log_workflow_transition(self, transition: WorkflowTransition, user: User) -> None:
    """ワークフロー遷移の監査ログ記録"""

def log_progress_update(self, update: ProgressUpdate, user: User) -> None:
    """進捗更新の監査ログ記録"""

def log_dependency_change(self, change: DependencyChange, user: User) -> None:
    """依存関係変更の監査ログ記録"""
```

## 8. 拡張性・統合性

### 8.1 プラグインインターフェース
```python
class EpisodeManagementPlugin:
    @abstractmethod
    def on_episode_state_changed(self, episode_number: int, from_state: WorkflowState, to_state: WorkflowState) -> None:
        """状態変更時のプラグイン処理"""

    @abstractmethod
    def on_progress_updated(self, episode_number: int, progress: ProgressMetrics) -> None:
        """進捗更新時のプラグイン処理"""

    @abstractmethod
    def validate_custom_transition(self, transition: WorkflowTransition) -> ValidationResult:
        """カスタム遷移検証"""
```

### 8.2 外部システム連携
```python
def export_progress_to_external_system(self, project_id: str, system_config: dict) -> bool:
    """外部システムへの進捗エクスポート"""

def import_workflow_configuration(self, config_source: str) -> WorkflowConfiguration:
    """外部からのワークフロー設定インポート"""

def sync_with_project_management_tool(self, tool_config: dict) -> SyncResult:
    """プロジェクト管理ツールとの同期"""
```

## 9. 使用例

### 9.1 基本的な使用パターン
```python
# リポジトリ初期化
mgmt_repo = YamlEpisodeManagementRepository(base_path=Path("/projects"))

# 新規プロジェクト管理作成
management = EpisodeManagementAggregate(
    project_id="project-001",
    project_name="転生したら最強の魔法使いだった件"
)

# エピソード追加
episode_info = EpisodeInfo(
    episode_number=1,
    title="異世界転生",
    target_word_count=3000,
    workflow_config="standard_workflow"
)
management.add_episode(episode_info)

# アグリゲート保存
mgmt_repo.save_episode_management(management)
```

### 9.2 ワークフロー管理例
```python
# ワークフロー遷移
transition_result = mgmt_repo.transition_episode_state(
    project_id="project-001",
    episode_number=1,
    to_state=WorkflowState.IN_REVIEW,
    context=TransitionContext(
        user_id="user-123",
        reason="執筆完了",
        metadata={"word_count": 3247}
    )
)

if transition_result.success:
    print(f"状態遷移成功: {transition_result.from_state} → {transition_result.to_state}")

# 利用可能な遷移確認
available_transitions = mgmt_repo.get_available_transitions("project-001", 1)
print(f"利用可能な遷移: {available_transitions}")

# ワークフロー履歴確認
history = mgmt_repo.get_workflow_history("project-001", 1)
for transition in history[-5:]:
    print(f"{transition.timestamp}: {transition.from_state} → {transition.to_state}")
```

### 9.3 進捗管理例
```python
# 進捗更新
progress_update = ProgressUpdate(
    episode_number=1,
    writing_progress=100.0,
    review_progress=75.0,
    editing_progress=0.0,
    time_spent_minutes=180
)

mgmt_repo.update_episode_progress("project-001", 1, progress_update)

# プロジェクト全体の進捗確認
project_progress = mgmt_repo.calculate_project_progress("project-001")
print(f"全体進捗: {project_progress.completion_percentage:.1f}%")
print(f"完成予定: {project_progress.estimated_completion_date}")

# 進捗レポート生成
report = mgmt_repo.generate_progress_report("project-001", "monthly")
print(report.summary)
```

### 9.4 依存関係管理例
```python
# エピソード依存関係追加
mgmt_repo.add_episode_dependency(
    project_id="project-001",
    episode_number=3,
    depends_on=[1, 2],
    dependency_type=DependencyType.CHARACTER_DEVELOPMENT
)

# 依存関係検証
validation_result = mgmt_repo.validate_dependencies("project-001")
if validation_result.has_conflicts:
    for conflict in validation_result.conflicts:
        print(f"競合: {conflict.description}")

# 章構成設定
chapter_structure = ChapterStructure(
    chapters=[
        Chapter(number=1, title="異世界への扉", episodes=[1, 2, 3]),
        Chapter(number=2, title="魔法学校生活", episodes=[4, 5, 6, 7])
    ]
)
mgmt_repo.organize_by_chapters("project-001", chapter_structure)
```

### 9.5 バッチ操作例
```python
# 複数エピソードの一括状態更新
batch_result = mgmt_repo.bulk_update_status(
    project_id="project-001",
    episode_numbers=[1, 2, 3],
    new_status=WorkflowState.PUBLISHED
)

print(f"更新成功: {batch_result.success_count}件")
print(f"更新失敗: {batch_result.failure_count}件")

# 一括進捗更新
updates = [
    ProgressUpdate(episode_number=4, writing_progress=50.0),
    ProgressUpdate(episode_number=5, writing_progress=25.0)
]

bulk_update_result = mgmt_repo.batch_progress_update("project-001", updates)
```

## 10. テスト仕様

### 10.1 単体テスト
```python
class TestYamlEpisodeManagementRepository:
    def test_save_and_load_management_aggregate(self):
        """管理アグリゲートの保存・読み込みテスト"""

    def test_workflow_state_transitions(self):
        """ワークフロー状態遷移テスト"""

    def test_progress_calculation(self):
        """進捗計算テスト"""

    def test_dependency_management(self):
        """依存関係管理テスト"""

    def test_batch_operations(self):
        """バッチ操作テスト"""

    def test_data_validation(self):
        """データ検証テスト"""

class TestWorkflowEngine:
    def test_state_transition_validation(self):
        """状態遷移検証テスト"""

    def test_custom_workflow_configuration(self):
        """カスタムワークフロー設定テスト"""

    def test_automated_transitions(self):
        """自動遷移テスト"""
```

### 10.2 統合テスト
```python
class TestEpisodeManagementIntegration:
    def test_complete_episode_lifecycle(self):
        """エピソード完全ライフサイクルテスト"""

    def test_multi_project_management(self):
        """マルチプロジェクト管理テスト"""

    def test_large_scale_operations(self):
        """大規模データ操作テスト"""

    def test_concurrent_workflow_operations(self):
        """並行ワークフロー操作テスト"""
```

### 10.3 パフォーマンステスト
```python
def test_large_project_performance(self):
    """大規模プロジェクトのパフォーマンステスト（1000エピソード）"""

def test_batch_operation_performance(self):
    """バッチ操作パフォーマンステスト"""

def test_dependency_resolution_performance(self):
    """依存関係解決パフォーマンステスト"""
```

## 11. 監視・運用

### 11.1 メトリクス収集
```python
# エピソード管理メトリクス
metrics = {
    'management_operations': {
        'workflow_transitions_per_hour': 25,
        'progress_updates_per_hour': 45,
        'batch_operations_per_day': 8,
        'dependency_validations_per_hour': 12
    },
    'workflow_metrics': {
        'average_episode_completion_days': 5.2,
        'workflow_success_rate': 0.94,
        'most_time_consuming_state': 'DRAFT',
        'transition_failure_rate': 0.06
    },
    'progress_metrics': {
        'average_daily_progress': 15.3,
        'velocity_episodes_per_week': 2.8,
        'productivity_trend': 'increasing',
        'goal_achievement_rate': 0.78
    }
}
```

### 11.2 アラート条件
- ワークフロー遷移失敗率 > 10%
- エピソードが同一状態に7日以上滞在
- 依存関係競合検出
- 進捗データ整合性エラー
- バッチ操作失敗率 > 5%

### 11.3 ダッシュボード表示
```python
def generate_management_dashboard(self, project_id: str) -> dict:
    """管理ダッシュボード用データ生成"""
    return {
        'project_overview': self.get_project_summary(project_id),
        'workflow_status': self.get_workflow_distribution(project_id),
        'progress_trends': self.get_progress_trends(project_id, days=30),
        'bottlenecks': self.identify_workflow_bottlenecks(project_id),
        'upcoming_deadlines': self.get_upcoming_deadlines(project_id),
        'productivity_metrics': self.get_productivity_summary(project_id)
    }
```

## 12. 実装メモ

### 12.1 実装ファイル
- **メインクラス**: `src/noveler/infrastructure/repositories/yaml_episode_management_repository.py`
- **ワークフローエンジン**: `scripts/infrastructure/workflow/workflow_engine.py`
- **進捗計算機**: `scripts/domain/services/progress_calculator.py`
- **テストファイル**: `tests/unit/infrastructure/repositories/test_yaml_episode_management_repository.py`

### 12.2 設計方針
- **アグリゲートの完全性**: エピソード管理に関する全データの一貫性保証
- **ワークフローの柔軟性**: 設定可能なワークフロー定義と自動遷移機能
- **進捗の可視性**: リアルタイム進捗追跡と予測機能
- **依存関係の明確性**: 複雑なエピソード関係の可視化と管理

### 12.3 今後の改善点
- [ ] 機械学習による執筆時間予測
- [ ] ワークフロー最適化提案機能
- [ ] リアルタイム進捗共有機能
- [ ] 自動依存関係検出機能
- [ ] 進捗ガント チャート生成
- [ ] モバイルアプリ対応API
- [ ] チーム協業機能
- [ ] 執筆パターン分析機能
