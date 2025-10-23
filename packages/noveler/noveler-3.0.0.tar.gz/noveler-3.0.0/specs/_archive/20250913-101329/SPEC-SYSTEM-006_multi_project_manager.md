# 複数プロジェクト管理ユースケース仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、複数の小説プロジェクトを統合的に管理するビジネスロジックを実装する。プロジェクト間の依存関係管理、リソース配分、優先順位付け、統合レポーティングを含む包括的な複数プロジェクト管理機能を提供。

### 1.2 スコープ
- 複数プロジェクトの一覧管理・検索・フィルタリング
- プロジェクト間の優先順位管理・スケジューリング
- リソース（時間・労力）の配分管理
- 統合進捗レポート・ダッシュボード
- プロジェクト間の共有リソース管理
- バッチ処理・一括操作

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── MultiProjectManager                    ← Domain Layer
│   ├── ProjectPortfolioRequest           └── ProjectPortfolio (Entity)
│   ├── BatchOperationRequest             └── Project (Entity)
│   ├── ResourceAllocationRequest         └── ResourceAllocation (Value Object)
│   ├── PortfolioResponse                 └── ProjectPriority (Value Object)
│   ├── execute_list_projects()           └── ProjectRepository (Interface)
│   ├── execute_allocate_resources()      └── PortfolioService (Service)
│   └── execute_batch_operation()
└── Helper Functions
    ├── calculate_project_priority()
    └── generate_portfolio_report()
```

### 1.4 ビジネス価値
- **効率的なマルチプロジェクト管理**: 複数作品の並行執筆を効率化
- **最適なリソース配分**: 限られた時間を最大限活用
- **戦略的な執筆計画**: データに基づく優先順位付け
- **統合的な進捗把握**: 全プロジェクトの状況を一元管理

## 2. クラス設計

### 2.1 メインユースケースクラス
```python
class MultiProjectManager:
    """複数プロジェクト管理ユースケース"""

    def __init__(
        self,
        project_repository: ProjectRepository,
        portfolio_service: PortfolioService,
        analytics_service: AnalyticsService,
        scheduler_service: SchedulerService
    ) -> None:
        """依存性注入による初期化"""
        self._project_repository = project_repository
        self._portfolio_service = portfolio_service
        self._analytics_service = analytics_service
        self._scheduler_service = scheduler_service
        self._cache = ProjectCache()
```

### 2.2 リクエスト・レスポンスクラス
```python
@dataclass(frozen=True)
class ProjectPortfolioRequest:
    """プロジェクトポートフォリオリクエスト"""
    filter_criteria: FilterCriteria
    sort_order: SortOrder = SortOrder.PRIORITY_DESC
    include_archived: bool = False
    page_size: int = 20
    page_number: int = 1

@dataclass(frozen=True)
class BatchOperationRequest:
    """バッチ操作リクエスト"""
    project_ids: list[str]
    operation_type: BatchOperationType
    parameters: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ResourceAllocationRequest:
    """リソース配分リクエスト"""
    total_hours_per_week: int
    allocation_strategy: AllocationStrategy
    project_constraints: dict[str, ProjectConstraint] = field(default_factory=dict)

@dataclass(frozen=True)
class PortfolioResponse:
    """ポートフォリオ操作レスポンス"""
    success: bool
    data: Any | None = None
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
```

## 3. データ構造

### 3.1 Enums
```python
from enum import Enum, auto

class SortOrder(Enum):
    """ソート順"""
    PRIORITY_DESC = "priority_desc"
    PRIORITY_ASC = "priority_asc"
    UPDATED_DESC = "updated_desc"
    UPDATED_ASC = "updated_asc"
    PROGRESS_DESC = "progress_desc"
    PROGRESS_ASC = "progress_asc"
    DEADLINE_ASC = "deadline_asc"

class BatchOperationType(Enum):
    """バッチ操作タイプ"""
    ARCHIVE = auto()
    UPDATE_STATUS = auto()
    QUALITY_CHECK = auto()
    BACKUP = auto()
    EXPORT = auto()
    ANALYZE = auto()

class AllocationStrategy(Enum):
    """リソース配分戦略"""
    EQUAL = "equal"                    # 均等配分
    PRIORITY_BASED = "priority_based"  # 優先度ベース
    DEADLINE_BASED = "deadline_based"  # 締切ベース
    PROGRESS_BASED = "progress_based"  # 進捗ベース
    CUSTOM = "custom"                  # カスタム配分

class ProjectHealthStatus(Enum):
    """プロジェクト健全性ステータス"""
    HEALTHY = "healthy"        # 健全
    AT_RISK = "at_risk"       # リスクあり
    DELAYED = "delayed"       # 遅延
    STALLED = "stalled"       # 停滞
    CRITICAL = "critical"     # 危機的
```

### 3.2 DataClasses
```python
@dataclass
class FilterCriteria:
    """フィルタ条件"""
    status: list[ProjectStatus] | None = None
    genres: list[str] | None = None
    tags: list[str] | None = None
    date_range: DateRange | None = None
    progress_range: tuple[int, int] | None = None
    health_status: list[ProjectHealthStatus] | None = None

@dataclass
class ProjectConstraint:
    """プロジェクト制約"""
    min_hours: int = 0
    max_hours: int = 168  # 週168時間
    fixed_hours: int | None = None
    priority_override: int | None = None

@dataclass
class ProjectSummary:
    """プロジェクトサマリー"""
    project_id: str
    name: str
    status: ProjectStatus
    progress: float
    last_updated: datetime
    health_status: ProjectHealthStatus
    priority_score: float
    metrics: ProjectMetrics

@dataclass
class ProjectMetrics:
    """プロジェクトメトリクス"""
    total_episodes: int
    completed_episodes: int
    total_words: int
    average_quality_score: float
    update_frequency: float  # 更新頻度（日/話）
    reader_engagement: float  # 読者エンゲージメント

@dataclass
class ResourceAllocation:
    """リソース配分"""
    project_id: str
    allocated_hours: int
    percentage: float
    rationale: str
    expected_output: ExpectedOutput

@dataclass
class ExpectedOutput:
    """期待アウトプット"""
    episodes: int
    words: int
    quality_improvement: float
```

## 4. パブリックメソッド

### 4.1 プロジェクト一覧取得
```python
def execute_list_projects(self, request: ProjectPortfolioRequest) -> PortfolioResponse:
    """プロジェクト一覧取得

    処理フロー:
    1. フィルタ条件の検証
    2. キャッシュチェック
    3. リポジトリからプロジェクト取得
    4. フィルタリング適用
    5. ソート実行
    6. ページネーション適用
    7. サマリー情報生成

    Args:
        request: ポートフォリオリクエスト

    Returns:
        PortfolioResponse: プロジェクト一覧
    """
```

### 4.2 リソース配分
```python
def execute_allocate_resources(self, request: ResourceAllocationRequest) -> PortfolioResponse:
    """リソース配分計算

    処理フロー:
    1. アクティブプロジェクト取得
    2. 優先度計算
    3. 制約条件適用
    4. 配分戦略実行
    5. 期待アウトプット計算
    6. 配分結果検証

    Args:
        request: リソース配分リクエスト

    Returns:
        PortfolioResponse: 配分結果
    """
```

### 4.3 バッチ操作実行
```python
def execute_batch_operation(self, request: BatchOperationRequest) -> PortfolioResponse:
    """バッチ操作実行

    処理フロー:
    1. 対象プロジェクト検証
    2. 操作権限確認
    3. トランザクション開始
    4. 操作実行
    5. 結果集計
    6. トランザクション完了

    Args:
        request: バッチ操作リクエスト

    Returns:
        PortfolioResponse: 操作結果
    """
```

### 4.4 ポートフォリオ分析
```python
def execute_analyze_portfolio(self) -> PortfolioResponse:
    """ポートフォリオ全体分析

    処理フロー:
    1. 全プロジェクトデータ収集
    2. 統計情報計算
    3. トレンド分析
    4. リスク評価
    5. 改善提案生成

    Returns:
        PortfolioResponse: 分析結果
    """
```

### 4.5 スケジュール最適化
```python
def execute_optimize_schedule(self, constraints: ScheduleConstraints) -> PortfolioResponse:
    """執筆スケジュール最適化

    処理フロー:
    1. 現在のスケジュール取得
    2. 制約条件適用
    3. 最適化アルゴリズム実行
    4. 競合解決
    5. スケジュール生成

    Args:
        constraints: スケジュール制約

    Returns:
        PortfolioResponse: 最適化されたスケジュール
    """
```

## 5. プライベートメソッド

### 5.1 計算メソッド
```python
def _calculate_priority_score(self, project: Project) -> float:
    """優先度スコア計算"""

def _calculate_health_status(self, project: Project) -> ProjectHealthStatus:
    """プロジェクト健全性計算"""

def _calculate_expected_output(self, project: Project, hours: int) -> ExpectedOutput:
    """期待アウトプット計算"""
```

### 5.2 フィルタリングメソッド
```python
def _apply_filters(self, projects: list[Project], criteria: FilterCriteria) -> list[Project]:
    """フィルタ適用"""

def _apply_sorting(self, projects: list[Project], sort_order: SortOrder) -> list[Project]:
    """ソート適用"""

def _apply_pagination(self, projects: list[Project], page_size: int, page_number: int) -> list[Project]:
    """ページネーション適用"""
```

### 5.3 バッチ処理メソッド
```python
def _execute_archive_batch(self, project_ids: list[str]) -> BatchResult:
    """アーカイブバッチ実行"""

def _execute_quality_check_batch(self, project_ids: list[str]) -> BatchResult:
    """品質チェックバッチ実行"""

def _aggregate_batch_results(self, results: list[BatchResult]) -> dict[str, Any]:
    """バッチ結果集計"""
```

## 6. 依存関係

### 6.1 ドメイン層依存
- `ProjectPortfolio`: プロジェクトポートフォリオエンティティ
- `Project`: プロジェクトエンティティ
- `ResourceAllocation`: リソース配分値オブジェクト
- `ProjectPriority`: プロジェクト優先度値オブジェクト
- `ProjectRepository`: プロジェクトリポジトリインターフェース
- `PortfolioService`: ポートフォリオドメインサービス

### 6.2 インフラ層依存
- `AnalyticsService`: 分析サービス
- `SchedulerService`: スケジューラーサービス
- `ProjectCache`: プロジェクトキャッシュ

## 7. 設計原則遵守

### 7.1 DDD原則
- **集約の境界**: ProjectPortfolioを集約ルートとして設計
- **値オブジェクトの不変性**: ResourceAllocation等の不変性保証
- **ドメインサービス**: 複雑な計算ロジックをPortfolioServiceに集約
- **リポジトリパターン**: データアクセスの抽象化

### 7.2 TDD原則
- **テストシナリオ網羅**: 全ての配分戦略に対するテスト
- **境界値テスト**: リソース配分の上限・下限テスト
- **統合テスト**: 複数プロジェクトの相互作用テスト
- **パフォーマンステスト**: 大量プロジェクト処理のテスト

## 8. 使用例

### 8.1 プロジェクト一覧取得
```python
# ユースケース初期化
manager = MultiProjectManager(
    project_repository,
    portfolio_service,
    analytics_service,
    scheduler_service
)

# フィルタ条件設定
filter_criteria = FilterCriteria(
    status=[ProjectStatus.WRITING, ProjectStatus.PLANNING],
    genres=["ファンタジー", "SF"],
    health_status=[ProjectHealthStatus.HEALTHY, ProjectHealthStatus.AT_RISK]
)

# リクエスト作成
request = ProjectPortfolioRequest(
    filter_criteria=filter_criteria,
    sort_order=SortOrder.PRIORITY_DESC,
    include_archived=False,
    page_size=10,
    page_number=1
)

# 実行
response = manager.execute_list_projects(request)

if response.success:
    projects = response.data['projects']
    for project in projects:
        print(f"{project.name}: 優先度 {project.priority_score:.2f}")
```

### 8.2 リソース配分
```python
# 制約条件設定
constraints = {
    "project-001": ProjectConstraint(min_hours=10, max_hours=20),
    "project-002": ProjectConstraint(fixed_hours=15),
    "project-003": ProjectConstraint(priority_override=100)
}

# 配分リクエスト
allocation_request = ResourceAllocationRequest(
    total_hours_per_week=40,
    allocation_strategy=AllocationStrategy.PRIORITY_BASED,
    project_constraints=constraints
)

# 実行
response = manager.execute_allocate_resources(allocation_request)

if response.success:
    allocations = response.data['allocations']
    for allocation in allocations:
        print(f"{allocation.project_id}: {allocation.allocated_hours}時間 ({allocation.percentage:.1f}%)")
        print(f"  期待アウトプット: {allocation.expected_output.episodes}話")
```

### 8.3 バッチ品質チェック
```python
# バッチ操作リクエスト
batch_request = BatchOperationRequest(
    project_ids=["project-001", "project-002", "project-003"],
    operation_type=BatchOperationType.QUALITY_CHECK,
    parameters={
        "check_types": ["basic_style", "story_structure"],
        "auto_fix": True
    }
)

# 実行
response = manager.execute_batch_operation(batch_request)

if response.success:
    results = response.data['results']
    print(f"成功: {results['success_count']}")
    print(f"失敗: {results['failure_count']}")
    for detail in results['details']:
        print(f"  {detail['project_id']}: {detail['status']}")
```

## 9. エラーハンドリング

### 9.1 エラー分類
```python
class MultiProjectError(Exception):
    """マルチプロジェクト管理基底例外"""

class ResourceAllocationError(MultiProjectError):
    """リソース配分エラー"""

class BatchOperationError(MultiProjectError):
    """バッチ操作エラー"""

class ScheduleConflictError(MultiProjectError):
    """スケジュール競合エラー"""

class PortfolioAnalysisError(MultiProjectError):
    """ポートフォリオ分析エラー"""
```

### 9.2 エラーメッセージ定義
```python
ERROR_MESSAGES = {
    "INSUFFICIENT_RESOURCES": "割り当て可能なリソースが不足しています: 必要 {required}時間, 利用可能 {available}時間",
    "CONFLICTING_CONSTRAINTS": "プロジェクト制約が競合しています: {conflicts}",
    "BATCH_OPERATION_FAILED": "バッチ操作が失敗しました: {operation_type} - {reason}",
    "PROJECT_NOT_FOUND": "プロジェクトが見つかりません: {project_ids}",
    "INVALID_FILTER": "無効なフィルタ条件です: {criteria}",
    "SCHEDULE_CONFLICT": "スケジュール競合が発生しました: {conflicts}",
    "ANALYSIS_FAILED": "ポートフォリオ分析に失敗しました: {reason}"
}
```

## 10. テスト観点

### 10.1 単体テスト
```python
class TestMultiProjectManager:
    def test_list_projects_with_filters(self):
        """フィルタ付きプロジェクト一覧取得"""

    def test_resource_allocation_strategies(self):
        """各種リソース配分戦略"""

    def test_batch_operations(self):
        """バッチ操作の実行"""

    def test_priority_calculation(self):
        """優先度計算ロジック"""

    def test_health_status_evaluation(self):
        """健全性評価ロジック"""

    def test_pagination(self):
        """ページネーション処理"""
```

### 10.2 統合テスト
```python
class TestMultiProjectIntegration:
    def test_portfolio_lifecycle(self):
        """ポートフォリオライフサイクル"""

    def test_concurrent_batch_operations(self):
        """並行バッチ操作"""

    def test_resource_optimization(self):
        """リソース最適化統合"""

    def test_large_portfolio_performance(self):
        """大規模ポートフォリオ性能"""
```

## 11. 品質基準

### 11.1 パフォーマンス基準
- プロジェクト一覧取得: 500ms以内（100プロジェクト）
- リソース配分計算: 1秒以内（50プロジェクト）
- バッチ操作: 30秒以内（100プロジェクト）

### 11.2 信頼性基準
- 配分精度: 合計時間の誤差1%以内
- バッチ成功率: 99%以上
- データ一貫性: 100%保証

### 11.3 保守性基準
- 新規戦略追加: 既存コード変更なし
- テストカバレッジ: 95%以上
- 循環的複雑度: 8以下
