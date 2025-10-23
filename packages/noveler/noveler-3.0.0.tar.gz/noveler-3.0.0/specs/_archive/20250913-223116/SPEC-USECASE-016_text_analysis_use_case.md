# テキスト分析ユースケース仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、小説テキストの詳細な分析機能を提供する。文字数・単語数・読みやすさ・感情分析・文体特徴など、多角的な分析を通じて執筆品質向上を支援。

### 1.2 スコープ
- テキストの基本統計（文字数・単語数・文数）
- 読みやすさ指標（漢字比率・平仮名比率・文長）
- 感情・雰囲気分析（感情スコア・トーン分析）
- 文体特徴抽出（語彙多様性・文体パターン）
- 比較分析（過去エピソード・目標値との比較）
- 分析結果の永続化・履歴管理

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── TextAnalysisUseCase                     ← Domain Layer
│   ├── TextAnalysisRequest                 └── TextMetrics (Entity)
│   ├── TextAnalysisResponse                └── ReadabilityScore (Value Object)
│   └── execute()                           └── EmotionScore (Value Object)
└── Helper Functions                         └── TextAnalysisRepository (Interface)
    ├── analyze_batch_episodes()
    └── generate_analysis_report()
```

### 1.4 ビジネス価値
- **客観的品質評価**: 数値化された指標による品質管理
- **執筆改善支援**: 具体的な改善ポイントの可視化
- **読者体験向上**: 読みやすさ・感情バランスの最適化
- **成長可視化**: 執筆スキルの定量的な成長追跡

## 2. 機能仕様

### 2.1 コアユースケース
```python
class TextAnalysisUseCase:
    def __init__(
        self,
        text_repository: TextAnalysisRepository,
        episode_repository: EpisodeRepository,
        nlp_service: NaturalLanguageService = None
    ) -> None:
        """依存性注入による初期化"""

    def execute(self, request: TextAnalysisRequest) -> TextAnalysisResponse:
        """テキスト分析メイン処理"""
```

### 2.2 リクエスト・レスポンス
```python
@dataclass(frozen=True)
class TextAnalysisRequest:
    """テキスト分析リクエスト"""
    text: str
    analysis_type: AnalysisType = AnalysisType.FULL
    episode_id: str | None = None
    project_id: str | None = None
    options: AnalysisOptions = field(default_factory=AnalysisOptions)

@dataclass(frozen=True)
class TextAnalysisResponse:
    """テキスト分析レスポンス"""
    success: bool
    metrics: TextMetrics | None = None
    suggestions: list[ImprovementSuggestion] = field(default_factory=list)
    error_message: str | None = None
    processing_time: float = 0.0

    @classmethod
    def success_response(cls, metrics: TextMetrics, suggestions: list[ImprovementSuggestion]) -> TextAnalysisResponse

    @classmethod
    def error_response(cls, error_message: str) -> TextAnalysisResponse
```

### 2.3 分析機能
```python
def _analyze_basic_statistics(self, text: str) -> BasicStatistics:
    """基本統計分析（文字数・単語数・文数）"""

def _analyze_readability(self, text: str) -> ReadabilityMetrics:
    """読みやすさ分析（漢字比率・文長・複雑度）"""

def _analyze_emotion(self, text: str) -> EmotionMetrics:
    """感情分析（感情スコア・トーン・雰囲気）"""

def _analyze_style(self, text: str) -> StyleMetrics:
    """文体分析（語彙多様性・文体パターン）"""

def _generate_suggestions(self, metrics: TextMetrics) -> list[ImprovementSuggestion]:
    """改善提案生成"""
```

### 2.4 ヘルパー関数
```python
def analyze_batch_episodes(
    project_id: str,
    episode_ids: list[str],
    analysis_type: AnalysisType,
    text_repository: TextAnalysisRepository,
    episode_repository: EpisodeRepository
) -> BatchAnalysisResponse:
    """複数エピソードの一括分析"""

def generate_analysis_report(
    project_id: str,
    analysis_results: list[TextAnalysisResponse],
    format: ReportFormat = ReportFormat.MARKDOWN
) -> AnalysisReport:
    """分析レポート生成"""
```

## 3. データ構造仕様

### 3.1 列挙型定義
```python
from enum import Enum, auto

class AnalysisType(Enum):
    """分析タイプ"""
    BASIC = auto()      # 基本統計のみ
    READABILITY = auto() # 読みやすさ分析
    EMOTION = auto()    # 感情分析
    STYLE = auto()      # 文体分析
    FULL = auto()       # 全分析

class SentimentType(Enum):
    """感情タイプ"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class ToneType(Enum):
    """文章トーン"""
    FORMAL = "formal"
    CASUAL = "casual"
    DRAMATIC = "dramatic"
    HUMOROUS = "humorous"
    SERIOUS = "serious"
    ROMANTIC = "romantic"

class ReportFormat(Enum):
    """レポート形式"""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PDF = "pdf"
```

### 3.2 データクラス定義
```python
@dataclass(frozen=True)
class AnalysisOptions:
    """分析オプション"""
    include_suggestions: bool = True
    compare_with_previous: bool = False
    save_to_history: bool = True
    detail_level: DetailLevel = DetailLevel.NORMAL

@dataclass(frozen=True)
class BasicStatistics:
    """基本統計情報"""
    total_characters: int
    total_words: int
    total_sentences: int
    unique_words: int
    average_sentence_length: float
    max_sentence_length: int
    min_sentence_length: int

@dataclass(frozen=True)
class ReadabilityMetrics:
    """読みやすさ指標"""
    readability_score: float  # 0-100
    kanji_ratio: float
    hiragana_ratio: float
    katakana_ratio: float
    complexity_level: ComplexityLevel
    reading_time_minutes: float

@dataclass(frozen=True)
class EmotionMetrics:
    """感情分析結果"""
    sentiment: SentimentType
    sentiment_score: float  # -1.0 to 1.0
    tone: ToneType
    emotion_distribution: dict[str, float]
    mood_consistency: float  # 0-100

@dataclass(frozen=True)
class StyleMetrics:
    """文体分析結果"""
    vocabulary_diversity: float  # 0-1.0
    formality_score: float  # 0-100
    descriptiveness: float  # 0-100
    dialogue_ratio: float  # 0-1.0
    narrative_pace: NarrativePace

@dataclass(frozen=True)
class TextMetrics:
    """統合テキスト分析結果"""
    basic_stats: BasicStatistics
    readability: ReadabilityMetrics
    emotion: EmotionMetrics
    style: StyleMetrics
    overall_quality_score: float  # 0-100
    timestamp: datetime
    analysis_version: str = "1.0"

@dataclass(frozen=True)
class ImprovementSuggestion:
    """改善提案"""
    category: SuggestionCategory
    priority: Priority
    message: str
    specific_location: str | None = None
    example: str | None = None
    impact_score: float = 0.0  # 0-10
```

### 3.3 複雑なデータ構造
```python
@dataclass(frozen=True)
class BatchAnalysisResponse:
    """一括分析レスポンス"""
    success: bool
    total_episodes: int
    analyzed_episodes: int
    failed_episodes: int
    results: dict[str, TextAnalysisResponse]
    summary_statistics: SummaryStatistics
    processing_time: float

@dataclass(frozen=True)
class AnalysisReport:
    """分析レポート"""
    project_id: str
    report_id: str
    generated_at: datetime
    format: ReportFormat
    content: str
    metadata: dict[str, Any]
    file_path: str | None = None
```

## 4. ビジネスルール仕様

### 4.1 分析基準
```python
# 読みやすさスコア計算
def calculate_readability_score(metrics: ReadabilityMetrics) -> float:
    """読みやすさスコア計算

    基準:
    - 漢字比率: 20-30%が最適 (100点)
    - 文長: 40-60文字が最適 (100点)
    - 複雑度: 中程度が最適 (100点)

    重み付け:
    - 漢字比率: 40%
    - 文長: 40%
    - 複雑度: 20%
    """

# 感情バランス評価
def evaluate_emotion_balance(emotion_metrics: EmotionMetrics) -> float:
    """感情バランス評価

    基準:
    - 感情の一貫性: 80%以上で高評価
    - 感情の多様性: 適度な変化があると高評価
    - ジャンルとの整合性: ジャンルに応じた感情分布
    """

# 文体品質評価
def evaluate_style_quality(style_metrics: StyleMetrics) -> float:
    """文体品質評価

    基準:
    - 語彙多様性: 0.7以上で高評価
    - 描写性: 60-80%が最適
    - 対話比率: 30-50%が最適
    - ナラティブペース: ジャンルに応じた適正値
    """
```

### 4.2 改善提案生成ルール
```python
SUGGESTION_RULES = {
    "KANJI_RATIO_HIGH": {
        "condition": lambda m: m.readability.kanji_ratio > 0.4,
        "message": "漢字の使用率が{ratio:.1%}と高めです。読みやすさ向上のため、一部を平仮名に変更することを検討してください。",
        "priority": Priority.MEDIUM,
        "example": "「複雑」→「ふくざつ」、「理解」→「わかる」"
    },
    "SENTENCE_TOO_LONG": {
        "condition": lambda m: m.basic_stats.max_sentence_length > 100,
        "message": "最大{length}文字の長文があります。読点で区切るか、複数の文に分割することを推奨します。",
        "priority": Priority.HIGH
    },
    "LOW_VOCABULARY_DIVERSITY": {
        "condition": lambda m: m.style.vocabulary_diversity < 0.5,
        "message": "語彙の多様性が{diversity:.1%}と低めです。類語辞典を活用して表現のバリエーションを増やしましょう。",
        "priority": Priority.MEDIUM
    }
}
```

## 5. エラーハンドリング仕様

### 5.1 エラー分類
```python
class TextAnalysisError(Exception):
    """テキスト分析エラー基底クラス"""

class EmptyTextError(TextAnalysisError):
    """空テキストエラー"""

class TextTooLongError(TextAnalysisError):
    """テキスト長超過エラー"""

class LanguageNotSupportedError(TextAnalysisError):
    """非対応言語エラー"""

class AnalysisTimeoutError(TextAnalysisError):
    """分析タイムアウトエラー"""
```

### 5.2 エラーハンドリング実装
```python
try:
    # 分析処理
    metrics = self._perform_analysis(request.text)
except EmptyTextError:
    return TextAnalysisResponse.error_response("分析対象のテキストが空です")
except TextTooLongError as e:
    return TextAnalysisResponse.error_response(
        f"テキストが長すぎます（最大{e.max_length}文字）"
    )
except AnalysisTimeoutError:
    return TextAnalysisResponse.error_response(
        "分析処理がタイムアウトしました。テキストを分割して再試行してください"
    )
except Exception as e:
    logger.error(f"予期しないエラー: {e}")
    return TextAnalysisResponse.error_response(
        "分析中にエラーが発生しました"
    )
```

## 6. 使用例

### 6.1 基本的なテキスト分析
```python
# リポジトリとサービス準備
text_repository = YamlTextAnalysisRepository(analysis_path)
episode_repository = YamlEpisodeRepository(project_path)
nlp_service = JapaneseNLPService()

# ユースケース初期化
use_case = TextAnalysisUseCase(
    text_repository,
    episode_repository,
    nlp_service
)

# 分析リクエスト
request = TextAnalysisRequest(
    text="俺の名前は田中太郎。突然の光に包まれ、気がつくと見知らぬ世界にいた。",
    analysis_type=AnalysisType.FULL,
    episode_id="episode-001",
    project_id="novel-project-001"
)

# 分析実行
response = use_case.execute(request)

if response.success:
    print(f"品質スコア: {response.metrics.overall_quality_score:.1f}")
    print(f"読みやすさ: {response.metrics.readability.readability_score:.1f}")
    print(f"感情トーン: {response.metrics.emotion.tone.value}")

    # 改善提案表示
    for suggestion in response.suggestions:
        print(f"[{suggestion.priority.name}] {suggestion.message}")
else:
    print(f"分析失敗: {response.error_message}")
```

### 6.2 一括分析
```python
# 複数エピソードの一括分析
batch_response = analyze_batch_episodes(
    project_id="novel-project-001",
    episode_ids=["episode-001", "episode-002", "episode-003"],
    analysis_type=AnalysisType.READABILITY,
    text_repository=text_repository,
    episode_repository=episode_repository
)

print(f"分析完了: {batch_response.analyzed_episodes}/{batch_response.total_episodes}")
print(f"平均品質スコア: {batch_response.summary_statistics.average_quality_score:.1f}")
```

### 6.3 分析レポート生成
```python
# 分析結果からレポート生成
report = generate_analysis_report(
    project_id="novel-project-001",
    analysis_results=[response],
    format=ReportFormat.MARKDOWN
)

# レポート保存
with open(report.file_path, "w", encoding="utf-8") as f:
    f.write(report.content)

print(f"レポート生成完了: {report.file_path}")
```

## 7. テスト仕様

### 7.1 単体テスト
```python
class TestTextAnalysisUseCase:
    def test_basic_text_analysis(self):
        """基本的なテキスト分析テスト"""

    def test_empty_text_handling(self):
        """空テキストのハンドリングテスト"""

    def test_long_text_analysis(self):
        """長文テキスト分析テスト"""

    def test_readability_calculation(self):
        """読みやすさ計算テスト"""

    def test_emotion_analysis(self):
        """感情分析テスト"""

    def test_suggestion_generation(self):
        """改善提案生成テスト"""
```

### 7.2 統合テスト
```python
class TestTextAnalysisIntegration:
    def test_full_analysis_workflow(self):
        """完全分析ワークフローテスト"""

    def test_batch_analysis(self):
        """一括分析テスト"""

    def test_report_generation(self):
        """レポート生成テスト"""

    def test_history_tracking(self):
        """履歴追跡テスト"""
```

## 8. 設計原則遵守

### 8.1 DDD原則
- **ドメインロジックの集約**: TextMetricsエンティティに分析結果の振る舞いを集約
- **値オブジェクトの活用**: ReadabilityScore、EmotionScore等の不変性確保
- **リポジトリパターン**: 分析結果の永続化をインフラ層に分離
- **ドメインサービス**: 複雑な分析ロジックをNaturalLanguageServiceに委譲

### 8.2 TDD原則
- **テストファースト**: 分析仕様を先にテストで定義
- **RED-GREEN-REFACTOR**: 失敗テスト→実装→リファクタリングのサイクル
- **高カバレッジ**: 分析ロジックの90%以上をテストでカバー
- **モックの活用**: 外部NLPサービスのモック化でテスト独立性確保

## 9. 品質基準

### 9.1 パフォーマンス基準
- **分析速度**: 5000文字のテキストを3秒以内で分析完了
- **メモリ使用**: 最大100MBのメモリ使用量
- **並行処理**: 10エピソードの同時分析に対応
- **キャッシュ効率**: 同一テキストの再分析を90%高速化

### 9.2 精度基準
- **基本統計**: 100%正確な文字数・単語数カウント
- **読みやすさ**: 人間評価との相関係数0.8以上
- **感情分析**: 80%以上の感情分類精度
- **改善提案**: 70%以上の提案採用率

## 10. 実装メモ

### 10.1 実装ファイル
- **メインクラス**: `src/noveler/application/use_cases/text_analysis_use_case.py`
- **テストファイル**: `tests/unit/application/use_cases/test_text_analysis_use_case.py`
- **統合テスト**: `tests/integration/test_text_analysis_workflow.py`

### 10.2 今後の改善点
- [ ] AI による高度な文体分析（GPT連携）
- [ ] リアルタイム分析（執筆中の即時フィードバック）
- [ ] 比較分析の強化（他作品・ジャンル平均との比較）
- [ ] 多言語対応（英語・中国語対応）
- [ ] カスタム分析ルールの設定機能
