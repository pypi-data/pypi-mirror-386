---
spec_id: SPEC-PLOT-006
status: canonical
owner: bamboocity
last_reviewed: 2025-09-13
category: PLOT
sources: [REQ]
tags: [plot]
---
# SPEC-PLOT-006: プロット要素抽出ユースケース仕様書

## 1. 概要

### 1.1 目的
DDD原則に基づき、プロットから重要な要素を自動抽出するビジネスロジックを実装する。キャラクター、場所、アイテム、伏線、転換点などの要素を体系的に抽出・分類する包括的な分析システムを提供。

### 1.2 スコープ
- プロット要素の自動検出・分類
- キャラクター関係性の抽出・分析
- 場所・時系列情報の構造化
- 伏線・回収ポイントの特定
- 感情曲線・テンション推移の分析
- 要素間の関連性マッピング

### 1.3 アーキテクチャ位置
```
Application Layer (Use Case)
├── PlotElementExtractionUseCase               ← Domain Layer
│   ├── PlotElementExtractionInput            └── PlotElement (Entity)
│   ├── ExtractionOptions                     └── ElementClassifier (Service)
│   ├── PlotElementExtractionOutput           └── ElementType (Enum)
│   └── execute(), analyze_relationships()     └── ElementRelation (Value Object)
└── Extraction Functions                       └── PlotRepository (Interface)
    ├── extract_characters()
    ├── extract_locations()
    └── extract_plot_points()
```

### 1.4 ビジネス価値
- **執筆支援の高度化**: 要素の体系的把握による執筆効率向上
- **一貫性の確保**: 設定矛盾の早期発見・防止
- **分析の自動化**: 手動分析作業の大幅削減
- **品質向上**: 伏線管理・キャラクター成長の可視化

## 2. 機能仕様

### 2.1 コアユースケース
```python
class PlotElementExtractionUseCase:
    def __init__(
        self,
        plot_repository: PlotRepository,
        project_repository: ProjectRepository,
        nlp_service: NLPService
    ):
        """依存性注入による初期化"""

    def execute(
        self,
        input_data: PlotElementExtractionInput
    ) -> PlotElementExtractionOutput:
        """プロット要素抽出実行"""

    def analyze_relationships(
        self,
        extracted_elements: dict[str, list[PlotElement]]
    ) -> dict[str, Any]:
        """要素間関係性分析"""
```

### 2.2 入力・出力データ
```python
@dataclass
class PlotElementExtractionInput:
    """要素抽出入力"""
    project_name: str
    target_type: str  # "master", "chapter", "episode"
    target_id: str | int | None = None
    extraction_depth: str = "standard"  # "basic", "standard", "deep"

@dataclass
class ExtractionOptions:
    """抽出オプション"""
    extract_characters: bool = True
    extract_locations: bool = True
    extract_items: bool = True
    extract_plot_points: bool = True
    extract_emotions: bool = True
    analyze_relationships: bool = True
    confidence_threshold: float = 0.7

@dataclass
class PlotElementExtractionOutput:
    """要素抽出出力"""
    success: bool
    extracted_elements: dict[str, list[PlotElement]]
    element_count: dict[str, int]
    relationships: list[ElementRelation]
    timeline: list[dict[str, Any]]
    emotion_curve: list[dict[str, float]]
    message: str = ""
```

### 2.3 要素抽出機能
```python
def extract_characters(
    self,
    plot_content: str
) -> list[PlotElement]:
    """キャラクター抽出"""

def extract_locations(
    self,
    plot_content: str
) -> list[PlotElement]:
    """場所・舞台抽出"""

def extract_plot_points(
    self,
    plot_content: str
) -> list[PlotElement]:
    """重要プロットポイント抽出"""

def extract_foreshadowing(
    self,
    plot_content: str
) -> list[tuple[PlotElement, PlotElement]]:
    """伏線・回収ペア抽出"""
```

### 2.4 分析機能
```python
def analyze_character_relationships(
    self,
    characters: list[PlotElement]
) -> dict[str, Any]:
    """キャラクター関係性分析"""

def generate_timeline(
    self,
    elements: dict[str, list[PlotElement]]
) -> list[dict[str, Any]]:
    """時系列生成"""

def calculate_emotion_curve(
    self,
    plot_content: str,
    elements: dict[str, list[PlotElement]]
) -> list[dict[str, float]]:
    """感情曲線計算"""
```

## 3. 要素タイプ仕様

### 3.1 キャラクター要素
```python
@dataclass
class CharacterElement(PlotElement):
    """キャラクター要素"""
    name: str
    role: str  # "protagonist", "antagonist", "supporting", "minor"
    first_appearance: str
    attributes: list[str]
    relationships: dict[str, str]  # {character_name: relationship_type}
    growth_points: list[str]
    importance_score: float
```

### 3.2 場所要素
```python
@dataclass
class LocationElement(PlotElement):
    """場所要素"""
    name: str
    description: str
    significance: str  # "major", "minor", "transitional"
    associated_events: list[str]
    mood: str
    first_mention: str
```

### 3.3 プロットポイント要素
```python
@dataclass
class PlotPointElement(PlotElement):
    """プロットポイント要素"""
    description: str
    point_type: str  # "inciting_incident", "turning_point", "climax", "resolution"
    chapter: int
    impact_level: str  # "high", "medium", "low"
    affected_characters: list[str]
    consequences: list[str]
```

## 4. 抽出アルゴリズム仕様

### 4.1 NLP基盤抽出
```python
def extract_with_nlp(
    self,
    text: str,
    element_type: ElementType
) -> list[PlotElement]:
    """NLP による要素抽出"""

    # トークン化と品詞タグ付け
    tokens = self.nlp_service.tokenize(text)
    pos_tags = self.nlp_service.pos_tag(tokens)

    # 固有表現抽出
    named_entities = self.nlp_service.extract_named_entities(text)

    # タイプ別フィルタリング
    if element_type == ElementType.CHARACTER:
        candidates = filter_person_entities(named_entities)
    elif element_type == ElementType.LOCATION:
        candidates = filter_location_entities(named_entities)

    # 文脈分析による検証
    validated = self.validate_with_context(candidates, text)

    return validated
```

### 4.2 パターンベース抽出
```python
CHARACTER_PATTERNS = [
    r"(.+?)は",  # ～は（主語マーカー）
    r"(.+?)が",  # ～が（主語マーカー）
    r"「.+?」と(.+?)は言った",  # 発話者パターン
    r"(.+?)の(?:目|顔|表情|声)",  # 身体部位による特定
]

LOCATION_PATTERNS = [
    r"(.+?)で",  # ～で（場所マーカー）
    r"(.+?)に(?:向かう|到着|入る)",  # 移動先パターン
    r"(.+?)の(?:中|上|下|前|後ろ)",  # 位置関係パターン
]

PLOT_POINT_PATTERNS = [
    r"(?:突然|いきなり|突如)(.+)",  # 急展開マーカー
    r"(?:ついに|ようやく|とうとう)(.+)",  # 達成マーカー
    r"(?:しかし|だが|ところが)(.+)",  # 転換マーカー
]
```

### 4.3 関係性分析アルゴリズム
```python
def analyze_character_relationships(
    self,
    characters: list[PlotElement],
    plot_content: str
) -> dict[str, Any]:
    """キャラクター関係性分析"""

    relationships = []

    for char1, char2 in combinations(characters, 2):
        # 共起分析
        co_occurrence = count_co_occurrences(char1.name, char2.name, plot_content)

        # 関係性キーワード検出
        relationship_keywords = detect_relationship_keywords(
            char1.name, char2.name, plot_content
        )

        # 関係性タイプ推定
        relationship_type = infer_relationship_type(relationship_keywords)

        if co_occurrence > RELATIONSHIP_THRESHOLD:
            relationships.append({
                "character1": char1.name,
                "character2": char2.name,
                "type": relationship_type,
                "strength": co_occurrence,
                "keywords": relationship_keywords
            })

    return {"relationships": relationships}
```

## 5. データ構造仕様

### 5.1 抽出入力構造
```python
# マスタープロット要素抽出
master_extraction_input = PlotElementExtractionInput(
    project_name="転生したら最強の魔法使いだった件",
    target_type="master",
    extraction_depth="deep"
)

# 特定章の要素抽出
chapter_extraction_input = PlotElementExtractionInput(
    project_name="転生したら最強の魔法使いだった件",
    target_type="chapter",
    target_id=3,
    extraction_depth="standard"
)

# エピソード単位の要素抽出
episode_extraction_input = PlotElementExtractionInput(
    project_name="転生したら最強の魔法使いだった件",
    target_type="episode",
    target_id="第15話",
    extraction_depth="basic"
)
```

### 5.2 抽出出力構造
```python
# 成功レスポンス例
success_output = PlotElementExtractionOutput(
    success=True,
    extracted_elements={
        "characters": [
            CharacterElement(
                name="田中太郎",
                role="protagonist",
                first_appearance="第1話",
                attributes=["勇敢", "正義感が強い", "魔法の才能"],
                relationships={"ミナ": "仲間", "魔王": "敵対"},
                growth_points=["魔法覚醒", "リーダーシップ獲得"],
                importance_score=0.95
            ),
            CharacterElement(
                name="ミナ",
                role="supporting",
                first_appearance="第3話",
                attributes=["聡明", "回復魔法使い"],
                relationships={"田中太郎": "仲間"},
                growth_points=["自信の獲得"],
                importance_score=0.75
            )
        ],
        "locations": [
            LocationElement(
                name="魔法学校",
                description="主人公が通う名門魔法学校",
                significance="major",
                associated_events=["入学式", "魔法試験", "決闘"],
                mood="academic",
                first_mention="第2話"
            )
        ],
        "plot_points": [
            PlotPointElement(
                description="主人公の魔法覚醒",
                point_type="turning_point",
                chapter=1,
                impact_level="high",
                affected_characters=["田中太郎", "学校関係者"],
                consequences=["特別クラス編入", "注目を集める"]
            )
        ]
    },
    element_count={
        "characters": 12,
        "locations": 8,
        "items": 5,
        "plot_points": 15
    },
    relationships=[
        ElementRelation(
            source="田中太郎",
            target="ミナ",
            relation_type="ally",
            strength=0.85
        )
    ],
    timeline=[
        {
            "episode": 1,
            "events": ["異世界転生", "魔法学校到着"],
            "introduced_characters": ["田中太郎"],
            "introduced_locations": ["異世界", "転生の間"]
        }
    ],
    emotion_curve=[
        {"episode": 1, "tension": 0.7, "hope": 0.8, "fear": 0.3},
        {"episode": 2, "tension": 0.5, "hope": 0.6, "fear": 0.2}
    ],
    message="プロット要素を抽出しました"
)
```

### 5.3 関係性マトリックス構造
```python
# キャラクター関係性マトリックス
relationship_matrix = {
    "characters": ["田中太郎", "ミナ", "魔王", "師匠"],
    "matrix": [
        [None, "ally", "enemy", "mentor"],  # 田中太郎の関係
        ["ally", None, "neutral", "respect"],  # ミナの関係
        ["enemy", "neutral", None, "unknown"],  # 魔王の関係
        ["student", "neutral", "unknown", None]  # 師匠の関係
    ],
    "strength": [
        [0, 0.85, 0.90, 0.75],
        [0.85, 0, 0.20, 0.60],
        [0.90, 0.20, 0, 0.10],
        [0.75, 0.60, 0.10, 0]
    ]
}
```

### 5.4 時系列構造
```python
# 詳細時系列データ
timeline_detail = [
    {
        "episode": 1,
        "title": "異世界への転生",
        "timestamp": "物語開始",
        "events": [
            {
                "type": "inciting_incident",
                "description": "トラックに轢かれて転生",
                "characters": ["田中太郎", "女神"],
                "location": "転生の間"
            }
        ],
        "emotional_state": {
            "protagonist": "confused",
            "overall_mood": "mysterious"
        }
    },
    {
        "episode": 5,
        "title": "初めての実戦",
        "timestamp": "1ヶ月後",
        "events": [
            {
                "type": "turning_point",
                "description": "魔法の覚醒",
                "characters": ["田中太郎", "ミナ", "教官"],
                "location": "訓練場"
            }
        ],
        "emotional_state": {
            "protagonist": "determined",
            "overall_mood": "intense"
        }
    }
]
```

## 6. 感情分析仕様

### 6.1 感情曲線計算
```python
def calculate_emotion_curve(
    self,
    plot_content: str,
    elements: dict[str, list[PlotElement]]
) -> list[dict[str, float]]:
    """感情曲線計算アルゴリズム"""

    emotion_markers = {
        "tension": ["戦い", "対決", "緊張", "危機", "追い詰められ"],
        "hope": ["希望", "光", "可能性", "チャンス", "成功"],
        "fear": ["恐怖", "不安", "怖い", "震え", "逃げ"],
        "joy": ["喜び", "笑顔", "幸せ", "楽しい", "祝"],
        "sadness": ["悲しみ", "涙", "別れ", "失う", "孤独"]
    }

    # セクション分割
    sections = split_into_sections(plot_content)

    emotion_curve = []
    for section in sections:
        emotions = {}
        for emotion, markers in emotion_markers.items():
            score = calculate_emotion_score(section, markers)
            emotions[emotion] = normalize_score(score)

        emotion_curve.append(emotions)

    return emotion_curve
```

### 6.2 テンション推移分析
```python
def analyze_tension_progression(
    self,
    plot_points: list[PlotPointElement]
) -> dict[str, Any]:
    """テンション推移分析"""

    tension_weights = {
        "inciting_incident": 0.7,
        "rising_action": 0.5,
        "turning_point": 0.8,
        "climax": 1.0,
        "falling_action": 0.3,
        "resolution": 0.2
    }

    progression = []
    for point in plot_points:
        tension = tension_weights.get(point.point_type, 0.5)
        tension *= impact_multiplier[point.impact_level]

        progression.append({
            "point": point.description,
            "tension": tension,
            "chapter": point.chapter
        })

    return {
        "progression": progression,
        "peak_tension": max(p["tension"] for p in progression),
        "average_tension": sum(p["tension"] for p in progression) / len(progression)
    }
```

## 7. エラーハンドリング仕様

### 7.1 ドメイン例外
```python
# プロジェクト不存在エラー
try:
    result = use_case.execute(input_data)
except ProjectNotFoundException as e:
    # "プロジェクトが存在しません: {project_name}"

# プロット不存在エラー
try:
    result = use_case.execute(input_data)
except PlotNotFoundException as e:
    # "指定されたプロットが見つかりません"
```

### 7.2 抽出エラー
```python
# NLPサービスエラー
try:
    elements = self.extract_with_nlp(text, element_type)
except NLPServiceException as e:
    # フォールバック: パターンベース抽出を使用
    elements = self.extract_with_patterns(text, element_type)

# 抽出結果不足エラー（警告）
if len(extracted_elements["characters"]) < MIN_EXPECTED_CHARACTERS:
    warnings.warn("抽出されたキャラクター数が少ない可能性があります")
```

### 7.3 分析エラー
```python
# 関係性分析エラー
try:
    relationships = self.analyze_relationships(extracted_elements)
except AnalysisException as e:
    # 部分的な結果を返す
    relationships = {"error": str(e), "partial_results": partial_data}

# 感情分析エラー
try:
    emotion_curve = self.calculate_emotion_curve(plot_content, elements)
except EmotionAnalysisException:
    # デフォルト値を返す
    emotion_curve = [{"tension": 0.5, "hope": 0.5} for _ in range(episode_count)]
```

## 8. 使用例

### 8.1 基本的な要素抽出
```python
# ユースケース初期化
plot_repository = YamlPlotRepository(project_path)
project_repository = YamlProjectRepository(base_path)
nlp_service = NLPService()

use_case = PlotElementExtractionUseCase(
    plot_repository=plot_repository,
    project_repository=project_repository,
    nlp_service=nlp_service
)

# マスタープロットから要素抽出
input_data = PlotElementExtractionInput(
    project_name="転生したら最強の魔法使いだった件",
    target_type="master",
    extraction_depth="standard"
)

result = use_case.execute(input_data)

if result.success:
    print(f"✅ 要素抽出成功")
    print(f"\n📊 抽出結果:")
    for element_type, count in result.element_count.items():
        print(f"  {element_type}: {count}個")

    # キャラクター一覧
    print("\n👥 主要キャラクター:")
    for char in result.extracted_elements["characters"][:5]:
        print(f"  • {char.name} ({char.role}) - 重要度: {char.importance_score:.2f}")
```

### 8.2 関係性分析と可視化
```python
# 関係性分析の実行
relationships = use_case.analyze_relationships(result.extracted_elements)

print("\n🔗 キャラクター関係性:")
for rel in relationships["relationships"]:
    print(f"  {rel['character1']} ↔ {rel['character2']}: {rel['type']} (強度: {rel['strength']:.2f})")

# 関係性マトリックスの生成
matrix = relationships.get("relationship_matrix", {})
if matrix:
    print("\n📋 関係性マトリックス:")
    print("     ", "\t".join(matrix["characters"]))
    for i, char in enumerate(matrix["characters"]):
        row = [matrix["matrix"][i][j] or "-" for j in range(len(matrix["characters"]))]
        print(f"{char:10}", "\t".join(row))
```

### 8.3 時系列と感情曲線
```python
# カスタムオプションで詳細抽出
options = ExtractionOptions(
    extract_characters=True,
    extract_locations=True,
    extract_items=True,
    extract_plot_points=True,
    extract_emotions=True,
    analyze_relationships=True,
    confidence_threshold=0.8  # 高精度モード
)

# 章別の詳細抽出
chapter_input = PlotElementExtractionInput(
    project_name="転生したら最強の魔法使いだった件",
    target_type="chapter",
    target_id=1,
    extraction_depth="deep"
)

detailed_result = use_case.execute(chapter_input)

# 時系列表示
print("\n📅 イベント時系列:")
for event in detailed_result.timeline:
    print(f"\n第{event['episode']}話:")
    for e in event['events']:
        print(f"  • {e}")

# 感情曲線の分析
print("\n📈 感情曲線分析:")
for i, emotions in enumerate(detailed_result.emotion_curve):
    print(f"第{i+1}話: ", end="")
    print(f"緊張度: {emotions['tension']:.1f}, ", end="")
    print(f"希望: {emotions['hope']:.1f}, ", end="")
    print(f"不安: {emotions['fear']:.1f}")
```

### 8.4 伏線管理との連携
```python
# 伏線抽出と管理
foreshadowing_pairs = use_case.extract_foreshadowing(plot_content)

print("\n🎯 伏線と回収:")
for setup, payoff in foreshadowing_pairs:
    print(f"\n伏線: {setup.description}")
    print(f"  場所: {setup.chapter}章")
    print(f"回収: {payoff.description}")
    print(f"  場所: {payoff.chapter}章")
    print(f"  間隔: {payoff.chapter - setup.chapter}章")

# 未回収伏線の検出
unresolved = [f for f, p in foreshadowing_pairs if p is None]
if unresolved:
    print("\n⚠️ 未回収の伏線:")
    for f in unresolved:
        print(f"  • {f.description} (第{f.chapter}章)")
```

## 9. テスト仕様

### 9.1 単体テスト
```python
class TestPlotElementExtractionUseCase:
    def test_character_extraction_success(self):
        """キャラクター抽出成功テスト"""

    def test_location_extraction_success(self):
        """場所抽出成功テスト"""

    def test_plot_point_extraction_success(self):
        """プロットポイント抽出成功テスト"""

    def test_relationship_analysis(self):
        """関係性分析テスト"""

    def test_emotion_curve_calculation(self):
        """感情曲線計算テスト"""

    def test_timeline_generation(self):
        """時系列生成テスト"""

    def test_extraction_with_low_confidence(self):
        """低信頼度での抽出テスト"""

    def test_empty_plot_handling(self):
        """空プロット処理テスト"""
```

### 9.2 統合テスト
```python
class TestPlotElementExtractionIntegration:
    def test_full_extraction_workflow(self):
        """完全抽出ワークフローテスト"""

    def test_multi_chapter_extraction(self):
        """複数章連続抽出テスト"""

    def test_extraction_with_nlp_fallback(self):
        """NLPフォールバック統合テスト"""

    def test_large_plot_performance(self):
        """大規模プロット性能テスト"""
```

### 9.3 精度テスト
```python
class TestExtractionAccuracy:
    def test_character_extraction_accuracy(self):
        """キャラクター抽出精度テスト"""

    def test_relationship_detection_accuracy(self):
        """関係性検出精度テスト"""

    def test_emotion_analysis_accuracy(self):
        """感情分析精度テスト"""
```

## 10. 実装メモ

### 10.1 実装ファイル
- **メインクラス**: `scripts/application/use_cases/plot_element_extraction_use_case.py`
- **テストファイル**: `tests/unit/application/use_cases/test_plot_element_extraction_use_case.py`
- **統合テスト**: `tests/integration/test_plot_element_extraction_workflow.py`

### 10.2 設計方針
- **DDD原則の厳格遵守**: アプリケーション層でのビジネスロジック集約
- **高精度抽出**: NLPとパターンマッチングのハイブリッド方式
- **拡張性の確保**: 新しい要素タイプの追加が容易
- **性能最適化**: 大規模プロットでも実用的な処理速度

### 10.3 今後の改善点
- [ ] 深層学習モデルによる抽出精度向上
- [ ] カスタム要素タイプの定義機能
- [ ] リアルタイム抽出・更新機能
- [ ] 他言語対応（英語プロット等）
- [ ] ビジュアル化機能の統合
- [ ] 抽出結果の学習・フィードバック機能
