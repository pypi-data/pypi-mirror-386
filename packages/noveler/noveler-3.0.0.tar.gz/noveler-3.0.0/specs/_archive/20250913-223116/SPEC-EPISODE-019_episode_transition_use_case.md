# SPEC-EPISODE-019: エピソード遷移管理ユースケース仕様書

## 概要
`EpisodeTransitionUseCase`は、エピソード間の遷移と流れを管理するユースケースです。エピソード間の接続性、クリフハンガーの設計、読者の誘導、ペーシング管理、遷移の最適化を包括的に提供し、スムーズで魅力的な物語展開を実現します。

## クラス設計

### EpisodeTransitionUseCase

**責務**
- エピソード間の遷移設計
- クリフハンガーの作成と管理
- 読者誘導フローの最適化
- ペーシングとリズムの調整
- 遷移効果の測定と改善
- エピソード間の依存関係管理

## データ構造

### TransitionType (Enum)
```python
class TransitionType(Enum):
    DIRECT = "direct"                # 直接続き
    CLIFFHANGER = "cliffhanger"      # クリフハンガー
    TIME_SKIP = "time_skip"          # 時間経過
    SCENE_CHANGE = "scene_change"    # 場面転換
    PERSPECTIVE_SHIFT = "perspective_shift" # 視点変更
    FLASHBACK = "flashback"          # 回想
    PARALLEL = "parallel"            # 並行展開
```

### TransitionStrength (Enum)
```python
class TransitionStrength(Enum):
    WEAK = "weak"                    # 弱い繋がり
    MODERATE = "moderate"            # 中程度
    STRONG = "strong"                # 強い繋がり
    CRITICAL = "critical"            # 必須の繋がり
```

### EpisodeTransition (DataClass)
```python
@dataclass
class EpisodeTransition:
    from_episode: int                # 遷移元エピソード
    to_episode: int                  # 遷移先エピソード
    transition_type: TransitionType  # 遷移タイプ
    strength: TransitionStrength     # 遷移強度
    hook_text: str                   # フック文章
    bridge_description: str          # 橋渡し説明
    emotional_arc: str               # 感情的な流れ
    pacing_effect: str               # ペーシング効果
    reader_expectation: str          # 読者期待値
    effectiveness_score: float = 0.0 # 効果スコア
```

### TransitionAnalysisRequest (DataClass)
```python
@dataclass
class TransitionAnalysisRequest:
    project_name: str                # プロジェクト名
    start_episode: int | None = None # 開始エピソード
    end_episode: int | None = None   # 終了エピソード
    analyze_hooks: bool = True       # フック分析
    analyze_pacing: bool = True      # ペーシング分析
    suggest_improvements: bool = True # 改善提案
```

### TransitionAnalysisResponse (DataClass)
```python
@dataclass
class TransitionAnalysisResponse:
    success: bool                    # 処理成功フラグ
    transitions: list[EpisodeTransition] # 遷移情報
    flow_quality: float              # フロー品質スコア
    weak_points: list[WeakTransition] # 弱い遷移点
    improvement_suggestions: list[str] # 改善提案
    pacing_analysis: dict[str, any]  # ペーシング分析
    reader_journey_map: dict[str, any] # 読者体験マップ
```

### TransitionDesignRequest (DataClass)
```python
@dataclass
class TransitionDesignRequest:
    project_name: str                # プロジェクト名
    from_episode: int                # 遷移元
    to_episode: int                  # 遷移先
    desired_effect: str              # 望む効果
    context: dict[str, str]          # コンテキスト情報
    auto_generate: bool = True       # 自動生成フラグ
```

## パブリックメソッド

### analyze_transitions()

**シグネチャ**
```python
def analyze_transitions(
    self,
    request: TransitionAnalysisRequest
) -> TransitionAnalysisResponse:
```

**目的**
指定範囲のエピソード遷移を分析する。

**引数**
- `request`: 遷移分析リクエスト

**戻り値**
- `TransitionAnalysisResponse`: 分析結果

**処理フロー**
1. **エピソード読み込み**: 対象エピソードの内容取得
2. **遷移点抽出**: 各エピソードの終わりと始まりの分析
3. **接続性評価**: エピソード間の繋がり強度評価
4. **ペーシング分析**: リズムとテンポの評価
5. **問題点特定**: 弱い遷移点の検出
6. **改善提案生成**: 具体的な改善案の作成
7. **読者体験マップ**: 読者の感情曲線作成

### design_transition()

**シグネチャ**
```python
def design_transition(
    self,
    request: TransitionDesignRequest
) -> EpisodeTransition:
```

**目的**
エピソード間の遷移を設計する。

### optimize_episode_flow()

**シグネチャ**
```python
def optimize_episode_flow(
    self,
    project_name: str,
    optimization_goals: list[str]
) -> FlowOptimizationResult:
```

**目的**
エピソード全体の流れを最適化する。

### create_cliffhanger()

**シグネチャ**
```python
def create_cliffhanger(
    self,
    project_name: str,
    episode_number: int,
    intensity: str = "moderate"
) -> CliffhangerDesign:
```

**目的**
エピソード末尾にクリフハンガーを作成する。

## プライベートメソッド

### _extract_episode_endings()

**シグネチャ**
```python
def _extract_episode_endings(
    self,
    episode_content: str
) -> dict[str, any]:
```

**目的**
エピソードの終わり部分を抽出・分析する。

**抽出要素**
```python
ending_elements = {
    "final_scene": str,              # 最終シーン
    "emotional_state": str,          # 感情状態
    "unresolved_elements": list[str], # 未解決要素
    "tension_level": float,          # 緊張レベル
    "hook_potential": float,         # フック可能性
    "natural_break_point": bool      # 自然な区切り
}
```

### _evaluate_connection_strength()

**シグネチャ**
```python
def _evaluate_connection_strength(
    self,
    from_ending: dict[str, any],
    to_beginning: dict[str, any]
) -> TransitionStrength:
```

**目的**
エピソード間の接続強度を評価する。

### _analyze_pacing_flow()

**シグネチャ**
```python
def _analyze_pacing_flow(
    self,
    episodes: list[Episode],
    transitions: list[EpisodeTransition]
) -> dict[str, any]:
```

**目的**
エピソード群のペーシングを分析する。

**分析項目**
```python
pacing_metrics = {
    "tension_curve": list[float],    # 緊張曲線
    "rhythm_pattern": str,           # リズムパターン
    "momentum_changes": list[dict],  # 勢いの変化
    "reader_fatigue_points": list[int], # 読者疲労点
    "optimal_break_points": list[int], # 最適休憩点
    "flow_consistency": float        # フロー一貫性
}
```

### _generate_hook_text()

**シグネチャ**
```python
def _generate_hook_text(
    self,
    episode_context: dict[str, any],
    desired_effect: str
) -> str:
```

**目的**
エピソード末尾のフックテキストを生成する。

### _create_reader_journey_map()

**シグネチャ**
```python
def _create_reader_journey_map(
    self,
    episodes: list[Episode],
    transitions: list[EpisodeTransition]
) -> dict[str, any]:
```

**目的**
読者の感情的な旅路をマッピングする。

## 遷移パターン

### クリフハンガーパターン
```python
cliffhanger_patterns = {
    "revelation": {
        "description": "重要な真実の暴露",
        "example": "その時、彼女が見たものは...",
        "intensity": "high",
        "suitable_for": ["mystery", "thriller"]
    },
    "danger": {
        "description": "差し迫った危険",
        "example": "背後から忍び寄る影に気づかずに...",
        "intensity": "high",
        "suitable_for": ["action", "horror"]
    },
    "decision": {
        "description": "重大な決断の瞬間",
        "example": "彼は震える手で、運命を決める選択を...",
        "intensity": "moderate",
        "suitable_for": ["drama", "romance"]
    }
}
```

### 場面転換パターン
```python
scene_transition_patterns = {
    "time_lapse": {
        "description": "時間経過による転換",
        "example": "三日後、状況は一変していた",
        "smoothness": "high"
    },
    "location_shift": {
        "description": "場所の移動",
        "example": "一方その頃、王都では",
        "smoothness": "moderate"
    },
    "perspective_change": {
        "description": "視点の切り替え",
        "example": "彼女の目から見た世界は",
        "smoothness": "moderate"
    }
}
```

## 依存関係

### ドメインサービス
- `TextAnalyzer`: テキスト分析
- `EmotionAnalyzer`: 感情分析
- `PacingCalculator`: ペーシング計算
- `HookGenerator`: フック生成

### リポジトリ
- `EpisodeRepository`: エピソード情報管理
- `TransitionRepository`: 遷移情報管理
- `AnalyticsRepository`: 分析データ管理

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`EpisodeTransition`）の適切な使用
- ✅ 値オブジェクト（列挙型）の活用
- ✅ ドメインサービスの適切な活用
- ✅ リポジトリパターンによるデータアクセス抽象化

### TDD準拠
- ✅ 明確な責務分離
- ✅ 包括的なエラーハンドリング
- ✅ 型安全な実装
- ✅ 列挙型による型安全性

## 使用例

```python
# 依存関係の準備
text_analyzer = TextAnalyzer()
emotion_analyzer = EmotionAnalyzer()
pacing_calculator = PacingCalculator()
hook_generator = HookGenerator()
episode_repo = YamlEpisodeRepository()
transition_repo = TransitionRepository()
analytics_repo = AnalyticsRepository()

# ユースケース作成
use_case = EpisodeTransitionUseCase(
    text_analyzer=text_analyzer,
    emotion_analyzer=emotion_analyzer,
    pacing_calculator=pacing_calculator,
    hook_generator=hook_generator,
    episode_repository=episode_repo,
    transition_repository=transition_repo,
    analytics_repository=analytics_repo
)

# エピソード遷移の分析
analysis_request = TransitionAnalysisRequest(
    project_name="fantasy_adventure",
    start_episode=10,
    end_episode=15,
    analyze_hooks=True,
    analyze_pacing=True,
    suggest_improvements=True
)

analysis_response = use_case.analyze_transitions(analysis_request)

if analysis_response.success:
    print(f"遷移分析完了: フロー品質 {analysis_response.flow_quality:.1f}/100")

    # 遷移情報の表示
    print("\n=== エピソード遷移 ===")
    for transition in analysis_response.transitions:
        strength_emoji = "🔗" if transition.strength == TransitionStrength.STRONG else "🔸"
        print(f"{strength_emoji} 第{transition.from_episode}話 → 第{transition.to_episode}話")
        print(f"   タイプ: {transition.transition_type.value}")
        print(f"   強度: {transition.strength.value}")
        print(f"   フック: {transition.hook_text[:50]}...")
        print(f"   効果スコア: {transition.effectiveness_score:.1f}")

    # 弱い遷移点
    if analysis_response.weak_points:
        print("\n⚠️ 改善が必要な遷移点:")
        for weak in analysis_response.weak_points:
            print(f"  - 第{weak.from_episode}話 → 第{weak.to_episode}話")
            print(f"    問題: {weak.issue}")
            print(f"    提案: {weak.suggestion}")

    # ペーシング分析
    pacing = analysis_response.pacing_analysis
    print(f"\n📊 ペーシング分析:")
    print(f"リズムパターン: {pacing['rhythm_pattern']}")
    print(f"フロー一貫性: {pacing['flow_consistency']:.1f}%")

    # 読者体験マップ
    journey = analysis_response.reader_journey_map
    print(f"\n🗺️ 読者体験マップ:")
    print(f"感情の高低差: {journey['emotional_variance']:.1f}")
    print(f"満足度予測: {journey['satisfaction_prediction']:.1f}%")

# 新しい遷移の設計
design_request = TransitionDesignRequest(
    project_name="fantasy_adventure",
    from_episode=15,
    to_episode=16,
    desired_effect="high_suspense",
    context={
        "from_ending": "主人公が重要な手がかりを発見",
        "to_beginning": "敵の襲撃シーン",
        "emotional_goal": "緊張感の最大化"
    }
)

new_transition = use_case.design_transition(design_request)

print(f"\n=== 新規遷移デザイン ===")
print(f"タイプ: {new_transition.transition_type.value}")
print(f"フックテキスト:\n{new_transition.hook_text}")
print(f"橋渡し説明:\n{new_transition.bridge_description}")

# クリフハンガーの作成
cliffhanger = use_case.create_cliffhanger(
    project_name="fantasy_adventure",
    episode_number=20,
    intensity="high"
)

print(f"\n💥 クリフハンガー作成:")
print(f"パターン: {cliffhanger.pattern}")
print(f"テキスト案:\n{cliffhanger.text}")
print(f"予想される読者反応: {cliffhanger.expected_reaction}")
print(f"次話への誘導力: {cliffhanger.pull_strength:.1f}/10")

# エピソードフローの最適化
optimization_result = use_case.optimize_episode_flow(
    project_name="fantasy_adventure",
    optimization_goals=[
        "maintain_tension",      # 緊張感の維持
        "avoid_reader_fatigue",  # 読者疲労の回避
        "maximize_engagement"    # エンゲージメント最大化
    ]
)

print(f"\n=== フロー最適化結果 ===")
print(f"改善されたフロー品質: {optimization_result.improved_score:.1f}")
print(f"推奨される変更:")
for change in optimization_result.recommended_changes:
    print(f"  - {change.description}")
    print(f"    影響: {change.impact}")
    print(f"    優先度: {change.priority}")

# 遷移効果の測定（読者データがある場合）
if has_reader_data:
    effectiveness = use_case.measure_transition_effectiveness(
        project_name="fantasy_adventure",
        episode_pairs=[(10, 11), (11, 12), (12, 13)]
    )

    print(f"\n📈 遷移効果測定:")
    for pair, metrics in effectiveness.items():
        print(f"第{pair[0]}話 → 第{pair[1]}話:")
        print(f"  継続率: {metrics['continuation_rate']:.1f}%")
        print(f"  読了時間: {metrics['reading_time']}分")
        print(f"  エンゲージメント: {metrics['engagement_score']:.1f}")
```

## 遷移分析レポート例

```
=== エピソード遷移分析レポート ===
対象: 第10話 〜 第15話
分析日: 2024-01-20

📊 全体評価
フロー品質スコア: 78.5/100
強い遷移: 3件 (60%)
要改善: 2件 (40%)

📈 ペーシング分析
┌─────────────────────────────────────┐
│ 緊張度                              │
│ 10 ┤    ╱╲                         │
│  8 ┤   ╱  ╲    ╱╲                 │
│  6 ┤  ╱    ╲  ╱  ╲               │
│  4 ┤ ╱      ╲╱    ╲              │
│  2 ┤                ╲            │
│    └─┬───┬───┬───┬───┬───┬──     │
│      10  11  12  13  14  15  話    │
└─────────────────────────────────────┘

⚠️ 問題点
1. 第12→13話: 緊張感の急激な低下
   提案: 第12話末尾に軽いフックを追加

2. 第14→15話: 接続が弱い
   提案: 第15話冒頭で前話の要素を引用

✨ 優れた遷移
- 第10→11話: 完璧なクリフハンガー
- 第13→14話: スムーズな場面転換
```

## エラーハンドリング

### エピソード不存在
```python
if not self.episode_repository.exists(project_name, episode_number):
    raise EpisodeNotFoundError(
        f"エピソード {episode_number} が見つかりません"
    )
```

### 遷移設計の失敗
```python
try:
    transition = self._design_transition(context)
except TransitionDesignError as e:
    # フォールバックパターンを使用
    transition = self._apply_fallback_pattern(context)
```

## 最適化アルゴリズム

### 動的プログラミングによるフロー最適化
```python
def _optimize_flow_dp(self, episodes: list[Episode]) -> list[int]:
    n = len(episodes)
    dp = [0] * n  # dp[i] = i番目までの最適スコア
    parent = [-1] * n  # 経路復元用

    for i in range(1, n):
        for j in range(i):
            score = dp[j] + self._calculate_transition_score(
                episodes[j], episodes[i]
            )
            if score > dp[i]:
                dp[i] = score
                parent[i] = j

    # 最適経路の復元
    return self._reconstruct_path(parent)
```

## テスト観点

### 単体テスト
- 遷移強度の評価ロジック
- フック生成アルゴリズム
- ペーシング計算
- 読者体験予測

### 統合テスト
- 実際のエピソードでの分析
- 最適化アルゴリズムの効果
- 大規模プロジェクトでの性能

## 品質基準

- **連続性**: エピソード間のスムーズな流れ
- **魅力**: 読者を引き込む効果的なフック
- **バランス**: 適切なペーシングとリズム
- **予測性**: 読者反応の正確な予測
- **改善性**: 具体的で実用的な改善提案
