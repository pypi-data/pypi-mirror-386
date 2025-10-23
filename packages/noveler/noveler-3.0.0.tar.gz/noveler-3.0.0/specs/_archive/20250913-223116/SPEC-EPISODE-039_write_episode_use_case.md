# エピソード執筆ユースケース仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、エピソード執筆のワークフロー全体を管理する統合的なユースケースを実装。執筆前準備から品質チェック、完成処理まで、一貫した執筆体験を提供。

### 1.2 スコープ
- 執筆前チェック（プロット確認・設定確認・前話確認）
- 執筆環境準備（テンプレート適用・ガイド表示）
- 執筆中サポート（リアルタイム品質チェック・自動保存）
- 執筆後処理（品質評価・改善提案・完成処理）
- AI執筆支援（プロンプト生成・文章補完）
- 統計追跡（執筆時間・文字数・品質推移）

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── WriteEpisodeUseCase                     ← Domain Layer
│   ├── WriteEpisodeRequest                 └── WritingSession (Entity)
│   ├── WriteEpisodeResponse                └── WritingContext (Value Object)
│   └── execute()                           └── WritingProgress (Value Object)
└── Helper Functions                         └── WritingSessionRepository (Interface)
    ├── prepare_writing_environment()
    └── finalize_episode_writing()
```

### 1.4 ビジネス価値
- **執筆品質向上**: 体系的な執筆プロセスによる品質確保
- **執筆効率化**: 自動化とAI支援による作業時間短縮
- **一貫性確保**: プロット・設定との整合性自動チェック
- **成長支援**: 執筆データ分析による継続的改善

## 2. 機能仕様

### 2.1 コアユースケース
```python
class WriteEpisodeUseCase:
    def __init__(
        self,
        episode_repository: EpisodeRepository,
        project_repository: ProjectRepository,
        quality_service: QualityCheckService,
        ai_service: AIWritingService,
        session_repository: WritingSessionRepository
    ) -> None:
        """依存性注入による初期化"""

    def execute(self, request: WriteEpisodeRequest) -> WriteEpisodeResponse:
        """エピソード執筆メイン処理"""
```

### 2.2 リクエスト・レスポンス
```python
@dataclass(frozen=True)
class WriteEpisodeRequest:
    """エピソード執筆リクエスト"""
    project_id: str
    episode_number: int | None = None  # Noneの場合は新規作成
    writing_mode: WritingMode = WritingMode.MANUAL
    ai_assistance_level: AIAssistanceLevel = AIAssistanceLevel.MEDIUM
    auto_save: bool = True
    real_time_check: bool = True

@dataclass(frozen=True)
class WriteEpisodeResponse:
    """エピソード執筆レスポンス"""
    success: bool
    session: WritingSession | None = None
    episode: Episode | None = None
    quality_report: QualityReport | None = None
    suggestions: list[WritingSuggestion] = field(default_factory=list)
    error_message: str | None = None

    @classmethod
    def success_response(
        cls,
        session: WritingSession,
        episode: Episode,
        quality_report: QualityReport
    ) -> WriteEpisodeResponse

    @classmethod
    def error_response(cls, error_message: str) -> WriteEpisodeResponse
```

### 2.3 執筆前処理
```python
def _prepare_writing_context(self, request: WriteEpisodeRequest) -> WritingContext:
    """執筆コンテキスト準備"""

def _check_prerequisites(self, project_id: str, episode_number: int) -> PrerequisiteCheckResult:
    """前提条件チェック（プロット・設定・前話）"""

def _load_writing_templates(self, project_id: str) -> list[WritingTemplate]:
    """執筆テンプレート読み込み"""

def _prepare_ai_context(self, context: WritingContext) -> AIContext:
    """AI支援用コンテキスト準備"""
```

### 2.4 執筆中処理
```python
def _start_writing_session(self, context: WritingContext) -> WritingSession:
    """執筆セッション開始"""

def _handle_auto_save(self, session: WritingSession, content: str) -> None:
    """自動保存処理"""

def _perform_realtime_check(self, content: str, check_type: CheckType) -> RealtimeCheckResult:
    """リアルタイム品質チェック"""

def _suggest_improvements(self, content: str, context: WritingContext) -> list[WritingSuggestion]:
    """改善提案生成"""
```

### 2.5 執筆後処理
```python
def _finalize_episode(self, session: WritingSession) -> Episode:
    """エピソード完成処理"""

def _generate_quality_report(self, episode: Episode) -> QualityReport:
    """品質レポート生成"""

def _update_statistics(self, session: WritingSession) -> None:
    """統計情報更新"""

def _create_improvement_plan(self, quality_report: QualityReport) -> ImprovementPlan:
    """改善計画作成"""
```

### 2.6 ヘルパー関数
```python
def prepare_writing_environment(
    project_id: str,
    episode_number: int | None = None,
    template_name: str | None = None
) -> WritingEnvironment:
    """執筆環境準備"""

def finalize_episode_writing(
    session_id: str,
    status: EpisodeStatus = EpisodeStatus.DRAFT,
    auto_publish: bool = False
) -> FinalizeResult:
    """エピソード執筆完了処理"""
```

## 3. データ構造仕様

### 3.1 列挙型定義
```python
from enum import Enum, auto

class WritingMode(Enum):
    """執筆モード"""
    MANUAL = "manual"          # 手動執筆
    AI_ASSISTED = "ai_assisted" # AI支援執筆
    AI_GENERATED = "ai_generated" # AI生成
    COLLABORATIVE = "collaborative" # 協同執筆

class AIAssistanceLevel(Enum):
    """AI支援レベル"""
    NONE = 0      # 支援なし
    LOW = 1       # 最小限の支援
    MEDIUM = 2    # 標準的な支援
    HIGH = 3      # 積極的な支援
    MAX = 4       # 最大限の支援

class CheckType(Enum):
    """チェックタイプ"""
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    STYLE = "style"
    CONSISTENCY = "consistency"
    PLOT = "plot"
    CHARACTER = "character"

class SuggestionType(Enum):
    """提案タイプ"""
    EXPRESSION = "expression"    # 表現改善
    STRUCTURE = "structure"      # 構成改善
    PACING = "pacing"           # ペース調整
    DESCRIPTION = "description"  # 描写追加
    DIALOGUE = "dialogue"       # 会話改善
    CONSISTENCY = "consistency" # 一貫性
```

### 3.2 データクラス定義
```python
@dataclass(frozen=True)
class WritingContext:
    """執筆コンテキスト"""
    project_id: str
    episode_number: int
    previous_episodes: list[EpisodeSummary]
    plot_summary: PlotSummary
    character_settings: list[CharacterSetting]
    world_settings: WorldSetting
    writing_guidelines: WritingGuidelines
    target_readers: TargetReaderProfile

@dataclass(frozen=True)
class WritingSession:
    """執筆セッション"""
    session_id: str
    project_id: str
    episode_number: int
    started_at: datetime
    writing_mode: WritingMode
    context: WritingContext
    progress: WritingProgress
    ai_interactions: list[AIInteraction] = field(default_factory=list)
    checkpoints: list[WritingCheckpoint] = field(default_factory=list)

@dataclass
class WritingProgress:
    """執筆進捗"""
    current_word_count: int = 0
    target_word_count: int = 3000
    completion_percentage: float = 0.0
    elapsed_time_seconds: int = 0
    active_writing_time_seconds: int = 0
    quality_score: float = 0.0
    last_saved_at: datetime | None = None

@dataclass(frozen=True)
class PrerequisiteCheckResult:
    """前提条件チェック結果"""
    all_clear: bool
    plot_exists: bool
    settings_complete: bool
    previous_episode_complete: bool
    warnings: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class WritingSuggestion:
    """執筆提案"""
    suggestion_id: str
    type: SuggestionType
    priority: Priority
    location: TextLocation
    current_text: str
    suggested_text: str
    explanation: str
    confidence: float  # 0.0-1.0
    impact_score: float  # 0.0-10.0

@dataclass(frozen=True)
class QualityReport:
    """品質レポート"""
    episode_id: str
    overall_score: float
    category_scores: dict[str, float]
    strengths: list[str]
    weaknesses: list[str]
    improvement_areas: list[ImprovementArea]
    comparison_with_previous: ComparisonResult | None
    generated_at: datetime

@dataclass(frozen=True)
class AIInteraction:
    """AI対話記録"""
    timestamp: datetime
    user_prompt: str
    ai_response: str
    applied: bool
    feedback: str | None = None
```

### 3.3 執筆支援データ構造
```python
@dataclass(frozen=True)
class WritingTemplate:
    """執筆テンプレート"""
    template_id: str
    name: str
    category: TemplateCategory
    structure: list[TemplateSection]
    variables: dict[str, str]
    example_usage: str

@dataclass(frozen=True)
class WritingGuidelines:
    """執筆ガイドライン"""
    style_guide: StyleGuide
    prohibited_expressions: list[str]
    recommended_expressions: list[str]
    tone_guidelines: ToneGuidelines
    pacing_guidelines: PacingGuidelines

@dataclass(frozen=True)
class WritingCheckpoint:
    """執筆チェックポイント"""
    checkpoint_id: str
    timestamp: datetime
    word_count: int
    content_snapshot: str
    quality_score: float
    auto_saved: bool

@dataclass(frozen=True)
class ImprovementPlan:
    """改善計画"""
    plan_id: str
    episode_id: str
    priority_areas: list[ImprovementArea]
    specific_actions: list[ImprovementAction]
    estimated_impact: float
    recommended_resources: list[Resource]
```

## 4. ビジネスルール仕様

### 4.1 執筆前チェックルール
```python
PREREQUISITE_RULES = {
    "plot_required": {
        "check": lambda ctx: ctx.plot_exists,
        "message": "プロットが未作成です。先にプロットを作成してください。",
        "severity": Severity.ERROR
    },
    "previous_episode_complete": {
        "check": lambda ctx: ctx.episode_number == 1 or ctx.previous_complete,
        "message": "前話が未完成です。順番に執筆することを推奨します。",
        "severity": Severity.WARNING
    },
    "character_settings": {
        "check": lambda ctx: len(ctx.character_settings) > 0,
        "message": "キャラクター設定が不足しています。",
        "severity": Severity.WARNING
    }
}
```

### 4.2 品質基準ルール
```python
def calculate_episode_quality_score(metrics: QualityMetrics) -> float:
    """エピソード品質スコア計算

    重み付け:
    - 文章品質: 30%
    - ストーリー構成: 25%
    - キャラクター描写: 20%
    - 読みやすさ: 15%
    - 独創性: 10%

    ボーナス:
    - プロット準拠: +5点
    - 設定一貫性: +5点
    - 前話との連続性: +5点
    """

    base_score = (
        metrics.writing_quality * 0.3 +
        metrics.story_structure * 0.25 +
        metrics.character_portrayal * 0.2 +
        metrics.readability * 0.15 +
        metrics.originality * 0.1
    ) * 100

    bonus = 0
    if metrics.plot_adherence > 0.8:
        bonus += 5
    if metrics.setting_consistency > 0.9:
        bonus += 5
    if metrics.continuity_score > 0.85:
        bonus += 5

    return min(100, base_score + bonus)
```

### 4.3 AI支援ルール
```python
AI_ASSISTANCE_RULES = {
    AIAssistanceLevel.LOW: {
        "spell_check": True,
        "grammar_check": True,
        "style_suggestions": False,
        "content_generation": False,
        "plot_suggestions": False
    },
    AIAssistanceLevel.MEDIUM: {
        "spell_check": True,
        "grammar_check": True,
        "style_suggestions": True,
        "content_generation": False,
        "plot_suggestions": True
    },
    AIAssistanceLevel.HIGH: {
        "spell_check": True,
        "grammar_check": True,
        "style_suggestions": True,
        "content_generation": True,
        "plot_suggestions": True,
        "auto_complete": True
    }
}
```

### 4.4 自動保存ルール
```python
AUTO_SAVE_TRIGGERS = {
    "time_interval": {
        "interval_seconds": 300,  # 5分ごと
        "condition": lambda s: s.last_saved_delta() > 300
    },
    "word_count": {
        "word_increment": 100,  # 100文字ごと
        "condition": lambda s: s.words_since_save() >= 100
    },
    "pause_detection": {
        "pause_seconds": 30,  # 30秒無操作
        "condition": lambda s: s.idle_time() > 30
    },
    "quality_check": {
        "after_check": True,  # 品質チェック後
        "condition": lambda s: s.quality_check_performed
    }
}
```

## 5. エラーハンドリング仕様

### 5.1 エラー分類
```python
class WritingError(Exception):
    """執筆エラー基底クラス"""

class PrerequisiteError(WritingError):
    """前提条件エラー"""

class SessionError(WritingError):
    """セッションエラー"""

class AutoSaveError(WritingError):
    """自動保存エラー"""

class AIServiceError(WritingError):
    """AIサービスエラー"""

class QualityCheckError(WritingError):
    """品質チェックエラー"""
```

### 5.2 エラーハンドリング実装
```python
def execute(self, request: WriteEpisodeRequest) -> WriteEpisodeResponse:
    """エラーハンドリング付き実行"""
    try:
        # 前提条件チェック
        prerequisite_result = self._check_prerequisites(
            request.project_id,
            request.episode_number
        )
        if not prerequisite_result.all_clear:
            return WriteEpisodeResponse.error_response(
                f"前提条件を満たしていません: {prerequisite_result.warnings}"
            )

        # 執筆処理
        context = self._prepare_writing_context(request)
        session = self._start_writing_session(context)

        # 執筆完了待機（実際の実装では非同期処理）
        episode = self._finalize_episode(session)
        quality_report = self._generate_quality_report(episode)

        return WriteEpisodeResponse.success_response(
            session, episode, quality_report
        )

    except PrerequisiteError as e:
        return WriteEpisodeResponse.error_response(
            f"前提条件エラー: {e}"
        )
    except AIServiceError as e:
        logger.warning(f"AI サービスエラー: {e}")
        # AI なしで継続
        return self._execute_without_ai(request)
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        return WriteEpisodeResponse.error_response(
            "執筆中にエラーが発生しました"
        )
```

## 6. 使用例

### 6.1 基本的な執筆フロー
```python
# サービス準備
episode_repo = YamlEpisodeRepository(project_path)
project_repo = YamlProjectRepository(base_path)
quality_service = IntegratedQualityCheckService()
ai_service = GPTWritingService(api_key)
session_repo = YamlWritingSessionRepository()

# ユースケース初期化
use_case = WriteEpisodeUseCase(
    episode_repo,
    project_repo,
    quality_service,
    ai_service,
    session_repo
)

# 新規エピソード執筆
request = WriteEpisodeRequest(
    project_id="novel-project-001",
    episode_number=None,  # 自動採番
    writing_mode=WritingMode.AI_ASSISTED,
    ai_assistance_level=AIAssistanceLevel.MEDIUM,
    auto_save=True,
    real_time_check=True
)

response = use_case.execute(request)

if response.success:
    print(f"執筆セッション開始: {response.session.session_id}")
    print(f"エピソード番号: {response.episode.number}")
    print(f"品質スコア: {response.quality_report.overall_score:.1f}")

    # 改善提案表示
    for suggestion in response.suggestions[:3]:
        print(f"- [{suggestion.type.value}] {suggestion.explanation}")
else:
    print(f"エラー: {response.error_message}")
```

### 6.2 AI支援執筆
```python
# 執筆環境準備
environment = prepare_writing_environment(
    project_id="novel-project-001",
    template_name="アクションシーン"
)

# AI最大支援で執筆
request = WriteEpisodeRequest(
    project_id="novel-project-001",
    episode_number=5,
    writing_mode=WritingMode.AI_ASSISTED,
    ai_assistance_level=AIAssistanceLevel.MAX
)

response = use_case.execute(request)

# AI対話履歴確認
for interaction in response.session.ai_interactions:
    print(f"User: {interaction.user_prompt}")
    print(f"AI: {interaction.ai_response[:100]}...")
    print(f"適用: {'Yes' if interaction.applied else 'No'}")
    print("---")
```

### 6.3 執筆完了処理
```python
# セッション完了
result = finalize_episode_writing(
    session_id=response.session.session_id,
    status=EpisodeStatus.COMPLETED,
    auto_publish=False
)

if result.success:
    print(f"エピソード完成！")
    print(f"総執筆時間: {result.total_time_minutes}分")
    print(f"実質執筆時間: {result.active_time_minutes}分")
    print(f"最終文字数: {result.final_word_count}文字")
    print(f"改訂回数: {result.revision_count}回")

    # 改善計画
    if result.improvement_plan:
        print("\n次回の改善ポイント:")
        for action in result.improvement_plan.specific_actions:
            print(f"- {action.description}")
```

## 7. テスト仕様

### 7.1 単体テスト
```python
class TestWriteEpisodeUseCase:
    def test_successful_writing_session(self):
        """正常な執筆セッションテスト"""

    def test_prerequisite_validation(self):
        """前提条件検証テスト"""

    def test_auto_save_functionality(self):
        """自動保存機能テスト"""

    def test_realtime_quality_check(self):
        """リアルタイム品質チェックテスト"""

    def test_ai_assistance_integration(self):
        """AI支援統合テスト"""

    def test_error_recovery(self):
        """エラー復旧テスト"""
```

### 7.2 統合テスト
```python
class TestWriteEpisodeIntegration:
    def test_full_writing_workflow(self):
        """完全執筆ワークフローテスト"""

    def test_concurrent_writing_sessions(self):
        """並行執筆セッションテスト"""

    def test_long_writing_session(self):
        """長時間執筆セッションテスト"""

    def test_cross_episode_consistency(self):
        """エピソード間一貫性テスト"""
```

## 8. 設計原則遵守

### 8.1 DDD原則
- **集約ルート**: WritingSessionを中心とした集約設計
- **値オブジェクト**: WritingContext、WritingProgressの不変性
- **ドメインサービス**: QualityCheckService、AIWritingServiceの活用
- **リポジトリパターン**: セッションデータの永続化分離

### 8.2 TDD原則
- **振る舞い駆動**: 執筆ワークフローをテストで定義
- **モックサービス**: AI・品質チェックサービスのモック化
- **境界値テスト**: 文字数制限、時間制限のテスト
- **統合シナリオ**: E2Eでの執筆フロー検証

## 9. 品質基準

### 9.1 パフォーマンス基準
- **レスポンス時間**: 執筆開始を3秒以内
- **自動保存**: 500ms以内で完了
- **品質チェック**: 1000文字を1秒以内で分析
- **AI応答**: 2秒以内で提案生成

### 9.2 ユーザビリティ基準
- **中断回復**: 95%以上のセッション復旧率
- **データ保全**: 99.9%以上の自動保存成功率
- **提案精度**: 70%以上の提案採用率
- **満足度**: 80%以上のユーザー満足度

## 10. 実装メモ

### 10.1 実装ファイル
- **メインクラス**: `scripts/application/use_cases/write_episode_use_case.py`
- **テストファイル**: `tests/unit/application/use_cases/test_write_episode_use_case.py`
- **統合テスト**: `tests/integration/test_write_episode_workflow.py`

### 10.2 今後の改善点
- [ ] 音声入力対応（ハンズフリー執筆）
- [ ] マルチモーダルAI（画像からの描写生成）
- [ ] 協同執筆機能（リアルタイム共同編集）
- [ ] 執筆分析AI（個人の執筆スタイル学習）
- [ ] VR執筆環境（没入型執筆体験）
