# 物語深度評価ユースケース仕様書

## 概要
`NarrativeDepthEvaluation`は、物語の深度と表現力を総合的に評価するユースケースです。キャラクターの内面描写、情景描写の細かさ、感情の深み、メタファーや比喩の使用、テーマの一貫性、読者との情緒的結びつきなどを多層的に分析し、文学的価値と読み応えの向上を支援します。

## クラス設計

### NarrativeDepthEvaluation

**責務**
- 物語深度の多層的分析
- キャラクターの心理描写評価
- 情景と雰囲気の表現性分析
- 言語表現の豊かさと独創性評価
- テーマの一貫性と深みの測定
- 情緒的インパクトの定量化
- 読者エンゲージメントの予測
- 文学的改善提案の生成

## データ構造

### NarrativeDepthDimension (Enum)
```python
class NarrativeDepthDimension(Enum):
    CHARACTER_PSYCHOLOGY = "character_psychology"    # キャラクター心理
    EMOTIONAL_RESONANCE = "emotional_resonance"      # 感情的響鳴
    ATMOSPHERIC_DETAIL = "atmospheric_detail"        # 雰囲気詳細
    THEMATIC_DEPTH = "thematic_depth"                # テーマ深度
    LINGUISTIC_RICHNESS = "linguistic_richness"      # 言語豊かさ
    NARRATIVE_COMPLEXITY = "narrative_complexity"    # 物語複雑性
    SENSORY_ENGAGEMENT = "sensory_engagement"        # 五感への訴求
    SYMBOLIC_LAYERING = "symbolic_layering"          # 象徴的層化
```

### DepthEvaluationRequest (DataClass)
```python
@dataclass
class DepthEvaluationRequest:
    project_name: str                                # プロジェクト名
    target_episodes: list[int] = []                  # 評価対象エピソード
    dimensions: list[NarrativeDepthDimension] = []   # 評価次元（空=全て）
    analysis_depth: str = "comprehensive"            # 分析深度
    reference_genre: str | None = None               # 参照ジャンル
    target_audience: str = "general"                 # 想定読者層
    comparative_analysis: bool = True                # 比較分析有無
    generate_suggestions: bool = True                # 改善提案生成
    detailed_breakdown: bool = False                 # 詳細分解モード
```

### DepthEvaluationResponse (DataClass)
```python
@dataclass
class DepthEvaluationResponse:
    success: bool                                    # 評価成功フラグ
    message: str                                     # 結果メッセージ
    overall_depth_score: float = 0.0                # 総合深度スコア
    dimension_scores: dict[NarrativeDepthDimension, float] = {}  # 次元別スコア
    evaluated_episodes_count: int = 0               # 評価エピソード数
    literary_assessment: LiteraryAssessment = None  # 文学的評価
    improvement_suggestions: list[DepthImprovementSuggestion] = []  # 改善提案
    comparative_insights: dict[str, any] = {}        # 比較分析結果
    detailed_analysis: dict[str, any] = {}           # 詳細分析データ
    reader_engagement_prediction: float = 0.0       # 読者エンゲージメント予測
```

### LiteraryAssessment (DataClass)
```python
@dataclass
class LiteraryAssessment:
    prose_quality: float                             # 散文品質
    narrative_sophistication: float                 # 物語洗練度
    emotional_authenticity: float                   # 感情の真実味
    thematic_coherence: float                       # テーマの一貫性
    character_development_depth: float              # キャラ成長深度
    world_building_richness: float                  # 世界構築の豊かさ
    literary_device_usage: dict[str, float]         # 文学技法使用度
    reader_immersion_potential: float               # 読者沈没ポテンシャル
    cultural_relevance: float                       # 文化的関連性
    originality_index: float                        # 独創性指数
```

### DepthImprovementSuggestion (DataClass)
```python
@dataclass
class DepthImprovementSuggestion:
    dimension: NarrativeDepthDimension               # 対象次元
    priority: str                                    # 優先度（high/medium/low）
    current_score: float                            # 現在スコア
    target_score: float                             # 目標スコア
    suggestion_text: str                            # 改善提案文
    specific_examples: list[str]                    # 具体例
    literary_techniques: list[str]                  # 推奨文学技法
    expected_impact: str                            # 期待効果
    implementation_difficulty: str                  # 実装難易度
    episode_specific_advice: dict[int, str] = {}    # エピソード固有アドバイス
```

### NarrativeElement (DataClass)
```python
@dataclass
class NarrativeElement:
    element_type: str                                # 要素タイプ
    content: str                                     # 内容
    depth_score: float                              # 深度スコア
    literary_devices: list[str]                     # 使用文学技法
    emotional_impact: float                         # 感情インパクト
    thematic_connection: str                        # テーマとの関連
    position_in_narrative: tuple[int, int]          # 物語内位置
```

## パブリックメソッド

### evaluate_narrative_depth()

**シグネチャ**
```python
def evaluate_narrative_depth(self, request: DepthEvaluationRequest) -> DepthEvaluationResponse:
```

**目的**
指定されたエピソードの物語深度を多層的に評価する。

**引数**
- `request`: 深度評価リクエスト

**戻り値**
- `DepthEvaluationResponse`: 深度評価結果

**処理フロー**
1. **テキスト前処理**: エピソードテキストの清浄化と構造化
2. **次元別分析**: 各深度次元の個別評価
3. **統合スコア計算**: 次元スコアの重み付き統合
4. **文学的評価**: 散文品質と芸術性の分析
5. **比較分析**: ジャンル平均や過去作品との比較
6. **改善提案生成**: 具体的で実用的な提案作成
7. **エンゲージメント予測**: 読者反応の予測モデル適用
8. **結果統合**: 包括的なレスポンス構築

### analyze_character_depth()

**シグネチャ**
```python
def analyze_character_depth(
    self,
    project_name: str,
    episode_numbers: list[int],
    character_focus: str | None = None
) -> CharacterDepthAnalysis:
```

**目的**
キャラクターの心理描写と成長を詳細分析する。

### evaluate_atmospheric_richness()

**シグネチャ**
```python
def evaluate_atmospheric_richness(
    self,
    project_name: str,
    episode_numbers: list[int]
) -> AtmosphericAnalysis:
```

**目的**
情景描写と雰囲気作りの豊かさを評価する。

### assess_thematic_coherence()

**シグネチャ**
```python
def assess_thematic_coherence(
    self,
    project_name: str,
    episode_numbers: list[int]
) -> ThematicAnalysis:
```

**目的**
テーマの一貫性と深みを分析する。

## プライベートメソッド

### _analyze_character_psychology()

**シグネチャ**
```python
def _analyze_character_psychology(
    self,
    text: str,
    character_profiles: dict[str, any]
) -> float:
```

**目的**
キャラクターの心理描写の深さを評価する。

**評価項目**
```python
psychological_elements = {
    "internal_monologue_depth": float,      # 内面的独白の深さ
    "emotional_complexity": float,          # 感情の複雑さ
    "motivation_clarity": float,            # 動機の明確さ
    "psychological_growth": float,          # 心理的成長
    "inner_conflict_depth": float,          # 内的葡藤の深さ
    "empathy_evocation": float,             # 共感喚起度
    "character_uniqueness": float,          # キャラ独自性
    "behavioral_consistency": float         # 行動一貫性
}
```

### _evaluate_emotional_resonance()

**シグネチャ**
```python
def _evaluate_emotional_resonance(
    self,
    text: str,
    target_audience: str
) -> float:
```

**目的**
読者との感情的結びつきの強さを測定する。

**評価指標**
- 感情語彙の使用頻度と適切性
- 情景と感情のマッチング
- 感情の漸強とクライマックスの効果
- 読者の感情移入を促す表現

### _assess_atmospheric_detail()

**シグネチャ**
```python
def _assess_atmospheric_detail(self, text: str) -> float:
```

**目的**
情景描写と雰囲気作りの細かさを評価する。

**分析要素**
```python
atmospheric_aspects = {
    "sensory_description_richness": float,  # 五感描写の豊かさ
    "environmental_detail_density": float,  # 環境詳細の密度
    "mood_establishment": float,            # ムード確立度
    "immersive_quality": float,             # 沈没感品質
    "symbolic_landscape": float,            # 象徴的風景
    "temporal_atmosphere": float,           # 時間的雰囲気
    "cultural_texture": float,              # 文化的質感
    "weather_mood_alignment": float         # 天候と気分の連動
}
```

### _evaluate_thematic_depth()

**シグネチャ**
```python
def _evaluate_thematic_depth(
    self,
    text: str,
    project_themes: list[str]
) -> float:
```

**目的**
テーマの一貫性と哲学的深みを分析する。

### _analyze_linguistic_richness()

**シグネチャ**
```python
def _analyze_linguistic_richness(self, text: str) -> float:
```

**目的**
言語表現の豊かさと芸術性を評価する。

**評価要素**
```python
linguistic_features = {
    "vocabulary_sophistication": float,     # 語彙の洗練度
    "metaphor_usage": float,                # メタファー使用度
    "simile_effectiveness": float,          # 直喩の効果性
    "rhetorical_device_variety": float,     # 修连技法の多様性
    "sentence_rhythm_variation": float,     # 文リズムの変化
    "dialogue_authenticity": float,         # 対話の真実味
    "prose_flow_quality": float,            # 散文の流れの品質
    "literary_allusion_depth": float        # 文学的暗示の深さ
}
```

### _calculate_narrative_complexity()

**シグネチャ**
```python
def _calculate_narrative_complexity(
    self,
    text: str,
    plot_structure: dict[str, any]
) -> float:
```

**目的**
物語構造の複雑さと技巧さを分析する。

### _assess_sensory_engagement()

**シグネチャ**
```python
def _assess_sensory_engagement(self, text: str) -> float:
```

**目的**
五感への訴求度と体験的描写を評価する。

### _evaluate_symbolic_layering()

**シグネチャ**
```python
def _evaluate_symbolic_layering(self, text: str) -> float:
```

**目的**
象徴的表現と深層意味の重ねを分析する。

### _generate_improvement_suggestions()

**シグネチャ**
```python
def _generate_improvement_suggestions(
    self,
    dimension_scores: dict[NarrativeDepthDimension, float],
    text_analysis: dict[str, any],
    target_audience: str
) -> list[DepthImprovementSuggestion]:
```

**目的**
分析結果に基づいて具体的な改善提案を生成する。

### _predict_reader_engagement()

**シグネチャ**
```python
def _predict_reader_engagement(
    self,
    depth_scores: dict[str, float],
    target_audience: str,
    genre: str
) -> float:
```

**目的**
深度スコアから読者エンゲージメントを予測する。

## 依存関係

### ドメインサービス
- `TextAnalysisService`: テキストの基本分析
- `LiteraryDeviceDetector`: 文学技法の検出
- `EmotionalToneAnalyzer`: 感情トーンの分析
- `ThematicAnalyzer`: テーマ的分析
- `CharacterAnalyzer`: キャラクター分析
- `EngagementPredictor`: 読者エンゲージメント予測

### リポジトリ
- `ProjectRepository`: プロジェクト情報の取得
- `EpisodeRepository`: エピソードテキストの取得
- `GenreBenchmarkRepository`: ジャンル別ベンチマークデータ
- `LiteraryStandardRepository`: 文学的標準データ

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`NarrativeElement`, `LiteraryAssessment`）の適切な使用
- ✅ 値オブジェクト（列挙型）の活用
- ✅ ドメインサービス（各種Analyzer）の適切な活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
project_repo = YamlProjectRepository()
episode_repo = YamlEpisodeRepository()
genre_benchmark_repo = GenreBenchmarkRepository()
literary_standard_repo = LiteraryStandardRepository()
text_analysis_service = TextAnalysisService()
literary_device_detector = LiteraryDeviceDetector()
emotional_tone_analyzer = EmotionalToneAnalyzer()
thematic_analyzer = ThematicAnalyzer()
character_analyzer = CharacterAnalyzer()
engagement_predictor = EngagementPredictor()

# ユースケース作成
use_case = NarrativeDepthEvaluation(
    project_repository=project_repo,
    episode_repository=episode_repo,
    genre_benchmark_repository=genre_benchmark_repo,
    literary_standard_repository=literary_standard_repo,
    text_analysis_service=text_analysis_service,
    literary_device_detector=literary_device_detector,
    emotional_tone_analyzer=emotional_tone_analyzer,
    thematic_analyzer=thematic_analyzer,
    character_analyzer=character_analyzer,
    engagement_predictor=engagement_predictor
)

# 包括的な物語深度評価
request = DepthEvaluationRequest(
    project_name="fantasy_adventure",
    target_episodes=[1, 2, 3, 4, 5],  # 第1-5話を評価
    dimensions=[
        NarrativeDepthDimension.CHARACTER_PSYCHOLOGY,
        NarrativeDepthDimension.EMOTIONAL_RESONANCE,
        NarrativeDepthDimension.ATMOSPHERIC_DETAIL,
        NarrativeDepthDimension.THEMATIC_DEPTH,
        NarrativeDepthDimension.LINGUISTIC_RICHNESS
    ],
    analysis_depth="comprehensive",
    reference_genre="fantasy",
    target_audience="young_adult",
    comparative_analysis=True,
    generate_suggestions=True,
    detailed_breakdown=True
)

response = use_case.evaluate_narrative_depth(request)

if response.success:
    print(f"物語深度評価完了: {response.message}")
    print(f"総合深度スコア: {response.overall_depth_score:.2f}/100")
    print(f"評価対象エピソード: {response.evaluated_episodes_count}件")

    # 次元別スコア表示
    print("\n=== 次元別評価 ===")
    for dimension, score in response.dimension_scores.items():
        print(f"{dimension.value}: {score:.1f}/100")

    # 文学的評価表示
    if response.literary_assessment:
        assessment = response.literary_assessment
        print("\n=== 文学的評価 ===")
        print(f"散文品質: {assessment.prose_quality:.1f}")
        print(f"物語洗練度: {assessment.narrative_sophistication:.1f}")
        print(f"感情の真実味: {assessment.emotional_authenticity:.1f}")
        print(f"テーマ一貫性: {assessment.thematic_coherence:.1f}")
        print(f"キャラ成長深度: {assessment.character_development_depth:.1f}")
        print(f"世界構築豊かさ: {assessment.world_building_richness:.1f}")
        print(f"独創性指数: {assessment.originality_index:.1f}")

    # 読者エンゲージメント予測
    print(f"\n📊 読者エンゲージメント予測: {response.reader_engagement_prediction:.1f}%")

    # 改善提案表示
    if response.improvement_suggestions:
        print("\n=== 改善提案 ===")
        for suggestion in response.improvement_suggestions:
            priority_emoji = "🔴" if suggestion.priority == "high" else "🟡" if suggestion.priority == "medium" else "🟢"
            print(f"\n{priority_emoji} {suggestion.dimension.value} ({suggestion.priority}優先度)")
            print(f"現在スコア: {suggestion.current_score:.1f} → 目標: {suggestion.target_score:.1f}")
            print(f"提案: {suggestion.suggestion_text}")

            if suggestion.specific_examples:
                print("具体例:")
                for example in suggestion.specific_examples:
                    print(f"  • {example}")

            if suggestion.literary_techniques:
                print(f"推奨技法: {', '.join(suggestion.literary_techniques)}")

            print(f"期待効果: {suggestion.expected_impact}")
            print(f"実装難易度: {suggestion.implementation_difficulty}")

    # 比較分析結果
    if response.comparative_insights:
        print("\n=== 比較分析 ===")
        insights = response.comparative_insights
        if "genre_comparison" in insights:
            genre_data = insights["genre_comparison"]
            print(f"ジャンル平均との比較: {genre_data['relative_position']:.1f}% 位置")

        if "improvement_trajectory" in insights:
            trajectory = insights["improvement_trajectory"]
            print(f"改善傾向: {trajectory['trend']}")

    # 詳細分析データ（詳細モード時）
    if response.detailed_analysis:
        print("\n=== 詳細分析データ ===")
        for category, data in response.detailed_analysis.items():
            print(f"{category}: {data}")
else:
    print(f"物語深度評価失敗: {response.message}")

# キャラクター特化分析
character_analysis = use_case.analyze_character_depth(
    project_name="fantasy_adventure",
    episode_numbers=[1, 2, 3],
    character_focus="主人公"  # 主人公に焦点を当てた分析
)

print(f"\n👥 キャラクター深度分析:")
print(f"心理描写の深さ: {character_analysis.psychological_depth:.1f}")
print(f"成長軌跡: {character_analysis.growth_trajectory}")

# 雰囲気評価
atmospheric_analysis = use_case.evaluate_atmospheric_richness(
    project_name="fantasy_adventure",
    episode_numbers=[1, 2, 3]
)

print(f"\n🌆 雰囲気分析:")
print(f"情景描写の豊かさ: {atmospheric_analysis.descriptive_richness:.1f}")
print(f"沈没感品質: {atmospheric_analysis.immersion_quality:.1f}")

# テーマ分析
thematic_analysis = use_case.assess_thematic_coherence(
    project_name="fantasy_adventure",
    episode_numbers=[1, 2, 3]
)

print(f"\n🎯 テーマ分析:")
print(f"テーマ一貫性: {thematic_analysis.coherence_score:.1f}")
print(f"主要テーマ: {', '.join(thematic_analysis.identified_themes)}")
```

## 深度分析アルゴリズム

### キャラクター心理分析
```python
class CharacterPsychologyAnalyzer:
    def analyze_internal_depth(self, text: str) -> dict[str, float]:
        # 内面的独白の検出
        internal_thoughts = self._extract_internal_monologue(text)

        # 感情の複雑さ分析
        emotional_complexity = self._analyze_emotional_layers(internal_thoughts)

        # 心理的矛盾の検出
        inner_conflicts = self._detect_psychological_conflicts(text)

        # 動機の明確性評価
        motivation_clarity = self._assess_motivation_clarity(text)

        return {
            "internal_monologue_depth": self._score_monologue_depth(internal_thoughts),
            "emotional_complexity": emotional_complexity,
            "inner_conflict_intensity": self._score_conflict_intensity(inner_conflicts),
            "motivation_clarity": motivation_clarity,
            "psychological_growth_rate": self._calculate_growth_rate(text)
        }

    def _extract_internal_monologue(self, text: str) -> list[str]:
        # 内面描写のパターンマッチング
        patterns = [
            r"（.+?は思った）",
            r"“[^"]*”と.+?は心の中で",
            r"[^.]*だろうか[.?]",  # 自問自答パターン
            # 他の内面描写パターン
        ]
        # 実装...
```

### 雰囲気評価アルゴリズム
```python
class AtmosphericAnalyzer:
    def evaluate_sensory_richness(self, text: str) -> dict[str, float]:
        sensory_words = {
            "visual": ["輝いている", "曇っている", "色とりどり", "美しい"],
            "auditory": ["響く", "静かな", "ざわめく", "音色"],
            "tactile": ["柔らかい", "冷たい", "温かい", "粗い"],
            "olfactory": ["香り", "臭い", "芳香", "アロマ"],
            "gustatory": ["甘い", "苦い", "酸っぱい", "味"]
        }

        scores = {}
        for sense, words in sensory_words.items():
            count = sum(text.count(word) for word in words)
            scores[sense] = min(count / len(text.split()) * 1000, 10.0)  # 正規化

        return scores
```

## エラーハンドリング

### テキスト分析エラー
```python
try:
    text_content = self.episode_repository.get_episode_text(project_name, episode_num)
except EpisodeNotFound:
    logger.warning(f"エピソード {episode_num} が見つかりません")
    continue  # 他のエピソードの分析を継続
except Exception as e:
    logger.error(f"テキスト読み込みエラー: {e}")
    return DepthEvaluationResponse(
        success=False,
        message=f"エピソードテキストの読み込みに失敗しました: {str(e)}"
    )
```

### 分析エラー
```python
try:
    psychology_score = self._analyze_character_psychology(text, character_profiles)
except AnalysisError as e:
    logger.warning(f"キャラクター心理分析エラー: {e}")
    psychology_score = 0.0  # デフォルト値
except Exception as e:
    logger.error(f"予期しない分析エラー: {e}")
    psychology_score = 0.0
```

## テスト観点

### 単体テスト
- 各深度次元の分析精度
- スコア計算アルゴリズムの正確性
- 改善提案生成の品質
- エンゲージメント予測の精度
- エラー条件での処理

### 統合テスト
- 実際の小説テキストでの分析
- 異なるジャンルでの適用
- 長編作品の全体的分析
- 文学的品質との相関性

### 品質テスト
- 文学的有名作品での検証
- 人間評価者との一致度
- ジャンル横断での安定性

## 品質基準

- **文学的妥当性**: 文学理論に基づいた評価基準
- **分析の深さ**: 表面的ではない本質的な評価
- **実用性**: 作家が実際に活用できる改善提案
- **客観性**: 個人的な好みに左右されない評価
- **教育的価値**: 作家の成長を促すフィードバック
