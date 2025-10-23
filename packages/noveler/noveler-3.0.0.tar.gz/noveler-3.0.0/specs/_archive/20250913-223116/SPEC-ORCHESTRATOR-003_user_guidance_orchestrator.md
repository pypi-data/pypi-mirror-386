# ユーザーガイダンスオーケストレーター仕様書

## SPEC-WORKFLOW-003: ユーザーガイダンス調整


## 1. 概要

### 1.1 目的
DDD原則に基づき、インテリジェントなユーザーガイダンスとエラーハンドリングを統合的に管理するビジネスロジックを実装する。執筆者の状況に応じた文脈的な支援を提供。

### 1.2 スコープ
- コンテキストアウェアなガイダンス生成
- 多層的エラーハンドリングとリカバリー提案
- 学習に基づく予防的アドバイス
- ワークフロー最適化とナビゲーション
- プログレッシブディスクロージャー型支援

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── UserGuidanceOrchestrator                  ← Domain Layer
│   ├── GuidanceRequest                       └── GuidanceContext (Entity)
│   ├── GuidanceResponse                      └── UserProfile (Entity)
│   └── orchestrate()                         └── GuidanceStrategy (Value Object)
└── Specialized Handlers                       └── GuidanceRepository (Interface)
    ├── ErrorRecoveryHandler
    ├── WorkflowOptimizer
    └── LearningAdvisor
```

### 1.4 ビジネス価値
- **認知負荷の軽減**: 状況に応じた最適な情報提供
- **学習曲線の短縮**: 段階的な機能開示と学習支援
- **エラー回復の迅速化**: 具体的な解決策の即時提供
- **生産性の向上**: 最適化されたワークフロー提案

## 2. 機能仕様

### 2.1 コアオーケストレーター
```python
class UserGuidanceOrchestrator:
    def __init__(
        self,
        guidance_repository: GuidanceRepository,
        user_profile_service: UserProfileService,
        context_analyzer: ContextAnalyzer,
        strategy_selector: StrategySelector
    ) -> None:
        """依存性注入による初期化"""

    def orchestrate(self, request: GuidanceRequest) -> GuidanceResponse:
        """ガイダンス生成のメイン処理"""
```

### 2.2 リクエスト・レスポンス
```python
@dataclass(frozen=True)
class GuidanceRequest:
    """ガイダンスリクエスト"""
    user_id: str
    action_type: ActionType
    current_context: ExecutionContext
    error_info: ErrorInfo | None = None
    user_intent: UserIntent | None = None

@dataclass(frozen=True)
class ExecutionContext:
    """実行コンテキスト"""
    current_phase: WorkflowPhase
    project_state: ProjectState
    recent_actions: list[UserAction]
    environment: EnvironmentInfo

@dataclass(frozen=True)
class ErrorInfo:
    """エラー情報"""
    error_type: ErrorType
    error_message: str
    stack_trace: str | None = None
    occurred_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0

@dataclass(frozen=True)
class GuidanceResponse:
    """ガイダンスレスポンス"""
    success: bool
    primary_guidance: Guidance
    alternative_options: list[Guidance] = field(default_factory=list)
    learning_resources: list[LearningResource] = field(default_factory=list)
    workflow_suggestions: list[WorkflowSuggestion] = field(default_factory=list)
    error_recovery_plan: ErrorRecoveryPlan | None = None

    @classmethod
    def create_guidance(
        cls,
        primary_guidance: Guidance,
        alternatives: list[Guidance] | None = None
    ) -> GuidanceResponse

    @classmethod
    def create_error_guidance(
        cls,
        error_info: ErrorInfo,
        recovery_plan: ErrorRecoveryPlan
    ) -> GuidanceResponse
```

### 2.3 ガイダンス戦略
```python
@dataclass(frozen=True)
class Guidance:
    """ガイダンス"""
    guidance_type: GuidanceType
    title: str
    description: str
    steps: list[GuidanceStep]
    estimated_time: timedelta
    difficulty_level: DifficultyLevel
    prerequisites: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class GuidanceStep:
    """ガイダンスステップ"""
    order: int
    instruction: str
    command_example: str | None = None
    visual_aid: str | None = None
    validation_criteria: list[str] = field(default_factory=list)

class GuidanceType(Enum):
    """ガイダンスタイプ"""
    QUICK_FIX = "quick_fix"
    STEP_BY_STEP = "step_by_step"
    CONCEPTUAL = "conceptual"
    TROUBLESHOOTING = "troubleshooting"
    BEST_PRACTICE = "best_practice"
```

### 2.4 エラーリカバリー機能
```python
class ErrorRecoveryHandler:
    """エラーリカバリーハンドラー"""

    def analyze_error(self, error_info: ErrorInfo) -> ErrorAnalysis:
        """エラー分析"""

    def generate_recovery_plan(
        self,
        error_analysis: ErrorAnalysis,
        user_context: UserContext
    ) -> ErrorRecoveryPlan:
        """リカバリープラン生成"""

@dataclass(frozen=True)
class ErrorRecoveryPlan:
    """エラーリカバリープラン"""
    immediate_actions: list[RecoveryAction]
    preventive_measures: list[PreventiveMeasure]
    root_cause_explanation: str
    learning_opportunity: LearningOpportunity | None = None

@dataclass(frozen=True)
class RecoveryAction:
    """リカバリーアクション"""
    action_type: RecoveryActionType
    description: str
    command: str
    expected_outcome: str
    risk_level: RiskLevel
```

### 2.5 ワークフロー最適化機能
```python
class WorkflowOptimizer:
    """ワークフロー最適化"""

    def analyze_workflow(
        self,
        recent_actions: list[UserAction],
        project_state: ProjectState
    ) -> WorkflowAnalysis:
        """ワークフロー分析"""

    def suggest_optimizations(
        self,
        workflow_analysis: WorkflowAnalysis,
        user_preferences: UserPreferences
    ) -> list[WorkflowSuggestion]:
        """最適化提案生成"""

@dataclass(frozen=True)
class WorkflowSuggestion:
    """ワークフロー提案"""
    suggestion_type: SuggestionType
    description: str
    automation_script: str | None = None
    time_saved: timedelta
    implementation_steps: list[str]
    benefits: list[str]
```

## 3. ビジネスルール仕様

### 3.1 コンテキスト判定ルール
```python
CONTEXT_RULES = {
    "beginner_threshold": 5,  # 初心者判定のエピソード数
    "error_frequency_threshold": 3,  # 頻繁なエラーの閾値
    "guidance_detail_levels": {
        "beginner": "detailed",
        "intermediate": "balanced",
        "advanced": "concise"
    },
    "progressive_disclosure_pace": "adaptive"  # 適応的な情報開示
}
```

### 3.2 エラーハンドリング優先度
- **クリティカルエラー**: データ損失リスクのあるエラーを最優先
- **ワークフローブロッカー**: 作業継続を妨げるエラーを優先
- **品質改善提案**: 非ブロッキングな改善提案は低優先度

### 3.3 学習支援ルール
```python
LEARNING_RULES = {
    "repetitive_error_threshold": 3,  # 同一エラーの学習介入閾値
    "skill_progression_model": "mastery_based",  # 習熟度ベースの進行
    "feedback_timing": "just_in_time",  # ジャストインタイムフィードバック
    "cognitive_load_limit": 3  # 同時提示する新概念の最大数
}
```

## 4. データ構造仕様

### 4.1 ユーザープロファイル
```python
# ユーザープロファイル例
user_profile_example = UserProfile(
    user_id="user-123",
    experience_level=ExperienceLevel.INTERMEDIATE,
    preferred_guidance_style=GuidanceStyle.VISUAL,
    learning_history=LearningHistory(
        completed_tutorials=["basic_writing", "plot_design"],
        mastered_features=["episode_creation", "quality_check"],
        common_errors=[
            ErrorPattern(
                error_type=ErrorType.FILE_NOT_FOUND,
                frequency=5,
                last_occurred=datetime.now() - timedelta(days=2)
            )
        ]
    ),
    workflow_preferences=WorkflowPreferences(
        preferred_tools=["cli", "vscode"],
        automation_level=AutomationLevel.MODERATE,
        notification_preferences=NotificationPreferences(
            error_alerts=True,
            improvement_suggestions=True,
            achievement_notifications=False
        )
    )
)
```

### 4.2 ガイダンス例
```python
# エラーリカバリーガイダンス
error_guidance_example = Guidance(
    guidance_type=GuidanceType.TROUBLESHOOTING,
    title="ファイルが見つからないエラーの解決",
    description="指定されたエピソードファイルが見つかりません。以下の手順で解決できます。",
    steps=[
        GuidanceStep(
            order=1,
            instruction="現在のディレクトリを確認します",
            command_example="pwd",
            validation_criteria=["プロジェクトのルートディレクトリにいること"]
        ),
        GuidanceStep(
            order=2,
            instruction="エピソードファイルの一覧を確認します",
            command_example="novel list episodes",
            validation_criteria=["エピソード一覧が表示されること"]
        ),
        GuidanceStep(
            order=3,
            instruction="正しいファイル名でコマンドを再実行します",
            command_example="novel edit '第001話_タイトル.md'",
            visual_aid="![file_structure](/images/file_structure.png)"
        )
    ],
    estimated_time=timedelta(minutes=5),
    difficulty_level=DifficultyLevel.EASY,
    prerequisites=[]
)

# ワークフロー最適化提案
workflow_suggestion_example = WorkflowSuggestion(
    suggestion_type=SuggestionType.AUTOMATION,
    description="毎回の品質チェックを自動化して時間を節約",
    automation_script="""
#!/bin/bash
# 自動品質チェックスクリプト
novel write new && novel check --auto-fix && novel commit
""",
    time_saved=timedelta(minutes=10),
    implementation_steps=[
        "スクリプトファイルを作成: create_and_check.sh",
        "実行権限を付与: chmod +x create_and_check.sh",
        "エイリアスを設定: alias nwrite='./create_and_check.sh'"
    ],
    benefits=[
        "品質チェックの忘れ防止",
        "一貫した品質維持",
        "作業時間の短縮"
    ]
)
```

### 4.3 エラーリカバリープラン例
```python
# 複雑なエラーのリカバリープラン
recovery_plan_example = ErrorRecoveryPlan(
    immediate_actions=[
        RecoveryAction(
            action_type=RecoveryActionType.DIAGNOSTIC,
            description="プロジェクト状態の診断",
            command="novel doctor --verbose",
            expected_outcome="問題のある設定ファイルを特定",
            risk_level=RiskLevel.NONE
        ),
        RecoveryAction(
            action_type=RecoveryActionType.BACKUP,
            description="現在の状態をバックアップ",
            command="novel backup create 'before_fix'",
            expected_outcome="復元可能なバックアップを作成",
            risk_level=RiskLevel.LOW
        ),
        RecoveryAction(
            action_type=RecoveryActionType.FIX,
            description="破損した設定ファイルを修復",
            command="novel repair config --auto",
            expected_outcome="設定ファイルが正常化",
            risk_level=RiskLevel.MEDIUM
        )
    ],
    preventive_measures=[
        PreventiveMeasure(
            measure_type=MeasureType.VALIDATION,
            description="定期的な設定ファイル検証",
            implementation="cron: 0 0 * * * novel validate config"
        ),
        PreventiveMeasure(
            measure_type=MeasureType.BACKUP,
            description="自動バックアップの設定",
            implementation="novel config set auto_backup=true"
        )
    ],
    root_cause_explanation="設定ファイルのYAML構文エラーが原因です。おそらく手動編集時にインデントが崩れた可能性があります。",
    learning_opportunity=LearningOpportunity(
        topic="YAML構文の基礎",
        resources=[
            "https://yaml.org/spec/",
            "novel help yaml-syntax"
        ],
        estimated_learning_time=timedelta(minutes=30)
    )
)
```

## 5. エラーハンドリング仕様

### 5.1 エラー分類
```python
class GuidanceError(Exception):
    """ガイダンスエラー基底クラス"""

class ContextAnalysisError(GuidanceError):
    """コンテキスト分析エラー"""

class StrategySelectionError(GuidanceError):
    """戦略選択エラー"""

class ResourceNotFoundError(GuidanceError):
    """リソース不在エラー"""
```

### 5.2 エラーメッセージング戦略
```python
ERROR_MESSAGE_STRATEGIES = {
    "beginner": {
        "style": "friendly",
        "detail_level": "high",
        "include_examples": True,
        "suggest_learning": True
    },
    "intermediate": {
        "style": "professional",
        "detail_level": "medium",
        "include_examples": False,
        "suggest_alternatives": True
    },
    "advanced": {
        "style": "concise",
        "detail_level": "low",
        "include_technical": True,
        "suggest_automation": True
    }
}
```

## 6. 使用例

### 6.1 基本的なガイダンス生成
```python
# オーケストレーター初期化
orchestrator = UserGuidanceOrchestrator(
    guidance_repository=guidance_repo,
    user_profile_service=profile_service,
    context_analyzer=context_analyzer,
    strategy_selector=strategy_selector
)

# エラー発生時のガイダンス要求
request = GuidanceRequest(
    user_id="user-123",
    action_type=ActionType.EPISODE_CREATION,
    current_context=ExecutionContext(
        current_phase=WorkflowPhase.WRITING,
        project_state=ProjectState(
            project_id="novel-001",
            episode_count=5,
            last_activity=datetime.now()
        ),
        recent_actions=[
            UserAction(ActionType.QUALITY_CHECK, datetime.now() - timedelta(minutes=5)),
            UserAction(ActionType.EPISODE_EDIT, datetime.now() - timedelta(minutes=2))
        ],
        environment=EnvironmentInfo(
            os="Windows",
            cli_version="1.2.0",
            editor="vscode"
        )
    ),
    error_info=ErrorInfo(
        error_type=ErrorType.PERMISSION_DENIED,
        error_message="ファイルへの書き込み権限がありません",
        retry_count=2
    )
)

# ガイダンス生成
response = orchestrator.orchestrate(request)

if response.success:
    # プライマリガイダンスの表示
    guidance = response.primary_guidance
    print(f"\n{guidance.title}")
    print(f"{guidance.description}\n")

    for step in guidance.steps:
        print(f"{step.order}. {step.instruction}")
        if step.command_example:
            print(f"   コマンド例: {step.command_example}")

    # リカバリープランの実行
    if response.error_recovery_plan:
        plan = response.error_recovery_plan
        print(f"\n根本原因: {plan.root_cause_explanation}")

        for action in plan.immediate_actions:
            print(f"\n[{action.risk_level}] {action.description}")
            print(f"実行: {action.command}")
```

### 6.2 プロアクティブなワークフロー最適化
```python
# ワークフロー分析リクエスト
workflow_request = GuidanceRequest(
    user_id="user-123",
    action_type=ActionType.WORKFLOW_OPTIMIZATION,
    current_context=current_context,
    user_intent=UserIntent(
        goal="執筆効率を向上させたい",
        constraints=["自動化は最小限に", "既存ツールを活用"]
    )
)

response = orchestrator.orchestrate(workflow_request)

# ワークフロー提案の表示
for suggestion in response.workflow_suggestions:
    print(f"\n提案: {suggestion.description}")
    print(f"節約時間: {suggestion.time_saved}")
    print(f"実装手順:")
    for i, step in enumerate(suggestion.implementation_steps, 1):
        print(f"  {i}. {step}")
```

### 6.3 学習パス提供
```python
# 学習支援リクエスト
learning_request = GuidanceRequest(
    user_id="user-123",
    action_type=ActionType.LEARNING_SUPPORT,
    current_context=current_context,
    user_intent=UserIntent(
        goal="品質チェック機能をマスターしたい",
        current_knowledge_level="基礎的な使い方は理解"
    )
)

response = orchestrator.orchestrate(learning_request)

# 学習リソースの表示
print("\n推奨学習パス:")
for resource in response.learning_resources:
    print(f"\n📚 {resource.title}")
    print(f"   種類: {resource.resource_type}")
    print(f"   所要時間: {resource.estimated_time}")
    print(f"   URL: {resource.url}")
```

## 7. テスト仕様

### 7.1 単体テスト
```python
class TestUserGuidanceOrchestrator:
    def test_context_aware_guidance_generation(self):
        """コンテキスト認識ガイダンス生成テスト"""

    def test_error_recovery_plan_generation(self):
        """エラーリカバリープラン生成テスト"""

    def test_workflow_optimization_suggestions(self):
        """ワークフロー最適化提案テスト"""

    def test_user_level_appropriate_guidance(self):
        """ユーザーレベル適応ガイダンステスト"""

    def test_progressive_disclosure(self):
        """プログレッシブディスクロージャーテスト"""
```

### 7.2 統合テスト
```python
class TestGuidanceIntegration:
    def test_full_guidance_workflow(self):
        """完全ガイダンスワークフローテスト"""

    def test_multi_error_handling(self):
        """複数エラー同時処理テスト"""

    def test_learning_path_effectiveness(self):
        """学習パス効果測定テスト"""
```

## 8. 設計原則遵守

### 8.1 DDD原則
- **戦略的設計**: ガイダンスコンテキストの明確な境界定義
- **戦術的設計**: GuidanceStrategy値オブジェクトによる戦略パターン
- **ドメイン駆動**: ユーザー支援ドメインの深い理解に基づく設計

### 8.2 TDD原則
- **ビヘイビア駆動**: ユーザー行動シナリオベースのテスト設計
- **モックファースト**: 外部依存のモック化による独立テスト
- **継続的リファクタリング**: ガイダンス品質の継続的改善

## 9. 品質基準

### 9.1 ユーザビリティ基準
- **ガイダンス理解度**: 90%以上のユーザーが初回で理解
- **問題解決率**: 85%以上のエラーが提案により解決
- **学習効果**: 同一エラーの再発率50%削減

### 9.2 パフォーマンス基準
- **ガイダンス生成時間**: 500ms以内
- **コンテキスト分析時間**: 200ms以内
- **リソース使用量**: メモリ50MB以下

## 10. 実装メモ

### 10.1 実装ファイル
- **メインクラス**: `scripts/application/use_cases/user_guidance_orchestrator.py`
- **テストファイル**: `tests/unit/application/use_cases/test_user_guidance_orchestrator.py`
- **統合テスト**: `tests/integration/test_guidance_workflow.py`

### 10.2 今後の改善点
- [ ] AI駆動のコンテキスト理解（自然言語処理統合）
- [ ] マルチモーダルガイダンス（動画・音声ガイド）
- [ ] コミュニティ駆動の解決策データベース
- [ ] 予測的エラー防止（プロアクティブアラート）
- [ ] パーソナライズされた学習カリキュラム生成
