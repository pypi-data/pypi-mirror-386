# 拡張遷移管理ユースケース仕様書

## 概要
`ExpandedTransitionUseCase`は、エピソード遷移管理の拡張版で、より高度な遷移設計機能を提供します。マルチパス遷移、条件付き分岐、読者選択型展開、並行ストーリーライン、インタラクティブ要素を含む複雑な物語構造の管理を実現します。

## クラス設計

### ExpandedTransitionUseCase

**責務**
- マルチパス物語展開の設計
- 条件付き分岐の管理
- 読者選択型ストーリーの構築
- 並行ストーリーラインの統合
- インタラクティブ要素の実装
- 複雑な遷移パターンの最適化

## データ構造

### ExpandedTransitionType (Enum)
```python
class ExpandedTransitionType(Enum):
    LINEAR = "linear"                      # 線形遷移
    BRANCHING = "branching"                # 分岐遷移
    MERGING = "merging"                    # 合流遷移
    PARALLEL = "parallel"                  # 並行遷移
    CONDITIONAL = "conditional"            # 条件付き遷移
    INTERACTIVE = "interactive"            # インタラクティブ遷移
    RECURSIVE = "recursive"                # 再帰的遷移
    QUANTUM = "quantum"                    # 量子的遷移（複数状態）
```

### StoryPath (DataClass)
```python
@dataclass
class StoryPath:
    path_id: str                           # パスID
    name: str                              # パス名
    episodes: list[int]                    # エピソード番号リスト
    conditions: list[PathCondition]        # パス条件
    probability: float                     # 選択確率
    reader_profile: str                    # 想定読者プロファイル
    narrative_weight: float                # 物語上の重要度
    is_canonical: bool = True              # 正史フラグ
```

### BranchPoint (DataClass)
```python
@dataclass
class BranchPoint:
    episode_number: int                    # 分岐点エピソード
    branch_type: str                       # 分岐タイプ
    options: list[BranchOption]            # 選択肢
    decision_criteria: dict[str, any]      # 判断基準
    merge_point: int | None                # 合流点エピソード
    impact_scope: str                      # 影響範囲
```

### ParallelStoryline (DataClass)
```python
@dataclass
class ParallelStoryline:
    storyline_id: str                      # ストーリーラインID
    name: str                              # ストーリーライン名
    episodes: list[int]                    # エピソードリスト
    sync_points: list[int]                 # 同期ポイント
    perspective: str                       # 視点
    timeline_offset: int                   # タイムライン オフセット
    interaction_points: list[dict]         # 相互作用点
```

### ExpandedTransitionRequest (DataClass)
```python
@dataclass
class ExpandedTransitionRequest:
    project_name: str                      # プロジェクト名
    transition_mode: ExpandedTransitionType # 遷移モード
    story_structure: dict[str, any]        # 物語構造
    optimization_goals: list[str]          # 最適化目標
    enable_interactivity: bool = False     # インタラクティブ有効
    maintain_coherence: bool = True        # 一貫性維持
```

### ExpandedTransitionResponse (DataClass)
```python
@dataclass
class ExpandedTransitionResponse:
    success: bool                          # 処理成功フラグ
    story_graph: StoryGraph                # 物語グラフ
    paths: list[StoryPath]                 # ストーリーパス
    branch_points: list[BranchPoint]       # 分岐点
    parallel_storylines: list[ParallelStoryline] # 並行ストーリー
    complexity_score: float                # 複雑度スコア
    coherence_score: float                 # 一貫性スコア
    navigation_guide: dict[str, any]       # ナビゲーションガイド
```

## パブリックメソッド

### design_multi_path_story()

**シグネチャ**
```python
def design_multi_path_story(
    self,
    request: ExpandedTransitionRequest
) -> ExpandedTransitionResponse:
```

**目的**
マルチパス型の物語構造を設計する。

**引数**
- `request`: 拡張遷移リクエスト

**戻り値**
- `ExpandedTransitionResponse`: 設計結果

**処理フロー**
1. **構造分析**: 物語構造の解析
2. **パス生成**: 可能なストーリーパスの生成
3. **分岐点設計**: 重要な分岐点の特定と設計
4. **並行展開設計**: 並行ストーリーラインの構築
5. **整合性検証**: 全パスの物語的整合性確認
6. **最適化**: 読者体験の最適化
7. **ナビゲーション生成**: 読者向けガイドの作成

### create_branching_narrative()

**シグネチャ**
```python
def create_branching_narrative(
    self,
    project_name: str,
    branch_episode: int,
    branch_options: list[dict]
) -> BranchPoint:
```

**目的**
分岐する物語展開を作成する。

### manage_parallel_storylines()

**シグネチャ**
```python
def manage_parallel_storylines(
    self,
    project_name: str,
    storylines: list[dict],
    sync_strategy: str
) -> ParallelNarrativeStructure:
```

**目的**
並行する複数のストーリーラインを管理する。

### design_interactive_elements()

**シグネチャ**
```python
def design_interactive_elements(
    self,
    project_name: str,
    interaction_points: list[dict]
) -> InteractiveDesign:
```

**目的**
インタラクティブな要素を設計する。

## プライベートメソッド

### _build_story_graph()

**シグネチャ**
```python
def _build_story_graph(
    self,
    episodes: list[Episode],
    transitions: list[Transition]
) -> StoryGraph:
```

**目的**
エピソードと遷移から物語グラフを構築する。

**グラフ構造**
```python
story_graph = {
    "nodes": {
        "episode_id": {
            "content": Episode,
            "incoming": list[str],
            "outgoing": list[str],
            "properties": dict
        }
    },
    "edges": {
        "transition_id": {
            "from": str,
            "to": str,
            "type": ExpandedTransitionType,
            "weight": float,
            "conditions": list
        }
    }
}
```

### _generate_story_paths()

**シグネチャ**
```python
def _generate_story_paths(
    self,
    story_graph: StoryGraph,
    start_node: str,
    end_nodes: list[str]
) -> list[StoryPath]:
```

**目的**
開始点から終了点までの全ての可能なパスを生成する。

### _optimize_branch_placement()

**シグネチャ**
```python
def _optimize_branch_placement(
    self,
    story_structure: dict,
    reader_metrics: dict
) -> list[int]:
```

**目的**
読者体験を最大化する分岐点の配置を最適化する。

### _synchronize_parallel_stories()

**シグネチャ**
```python
def _synchronize_parallel_stories(
    self,
    storylines: list[ParallelStoryline],
    sync_points: list[int]
) -> SynchronizationPlan:
```

**目的**
並行ストーリーラインの同期計画を作成する。

### _validate_narrative_coherence()

**シグネチャ**
```python
def _validate_narrative_coherence(
    self,
    paths: list[StoryPath],
    world_state: dict
) -> CoherenceReport:
```

**目的**
全てのパスで物語の一貫性を検証する。

## 高度な遷移パターン

### 量子的遷移
```python
quantum_transition = {
    "type": "quantum",
    "description": "複数の状態が同時に存在",
    "implementation": {
        "parallel_realities": [
            {"reality_a": "主人公が成功"},
            {"reality_b": "主人公が失敗"}
        ],
        "collapse_point": "第30話で収束",
        "reader_choice": "どちらの現実を選ぶか"
    }
}
```

### 条件付き分岐
```python
conditional_branch = {
    "type": "conditional",
    "conditions": [
        {
            "if": "reader_chose_path_a",
            "then": "episode_25a",
            "else": "episode_25b"
        },
        {
            "if": "character_trust_level > 80",
            "then": "secret_episode",
            "else": "normal_progression"
        }
    ]
}
```

### インタラクティブ要素
```python
interactive_element = {
    "type": "reader_choice",
    "prompt": "主人公はどう行動すべきか？",
    "options": [
        {
            "choice": "剣を取る",
            "consequence": "戦闘ルート",
            "next_episode": 31
        },
        {
            "choice": "交渉する",
            "consequence": "外交ルート",
            "next_episode": 32
        }
    ],
    "time_limit": "24時間以内に選択"
}
```

## 依存関係

### ドメインサービス
- `GraphBuilder`: グラフ構造構築
- `PathFinder`: パス探索アルゴリズム
- `CoherenceValidator`: 一貫性検証
- `ComplexityAnalyzer`: 複雑度分析

### 高度なサービス
- `QuantumNarrativeEngine`: 量子的物語エンジン
- `InteractiveStoryManager`: インタラクティブ管理
- `ParallelTimelineCoordinator`: 並行タイムライン調整

### リポジトリ
- `StoryGraphRepository`: 物語グラフ管理
- `BranchRepository`: 分岐情報管理
- `InteractionRepository`: インタラクション管理

## 設計原則遵守

### DDD準拠
- ✅ 複雑なドメインモデルの実装
- ✅ 集約の適切な境界設定
- ✅ イベントソーシングパターン
- ✅ CQRSの適用

### TDD準拠
- ✅ 複雑な遷移ロジックのテスト
- ✅ グラフアルゴリズムのテスト
- ✅ 一貫性検証のテスト
- ✅ インタラクションのテスト

## 使用例

```python
# 依存関係の準備
graph_builder = GraphBuilder()
path_finder = PathFinder()
coherence_validator = CoherenceValidator()
complexity_analyzer = ComplexityAnalyzer()
quantum_engine = QuantumNarrativeEngine()
interactive_manager = InteractiveStoryManager()
timeline_coordinator = ParallelTimelineCoordinator()
story_graph_repo = StoryGraphRepository()
branch_repo = BranchRepository()
interaction_repo = InteractionRepository()

# ユースケース作成
use_case = ExpandedTransitionUseCase(
    graph_builder=graph_builder,
    path_finder=path_finder,
    coherence_validator=coherence_validator,
    complexity_analyzer=complexity_analyzer,
    quantum_narrative_engine=quantum_engine,
    interactive_story_manager=interactive_manager,
    parallel_timeline_coordinator=timeline_coordinator,
    story_graph_repository=story_graph_repo,
    branch_repository=branch_repo,
    interaction_repository=interaction_repo
)

# マルチパス物語の設計
multi_path_request = ExpandedTransitionRequest(
    project_name="interactive_fantasy",
    transition_mode=ExpandedTransitionType.BRANCHING,
    story_structure={
        "main_arc": {
            "start": 1,
            "major_branches": [10, 20, 30],
            "endings": ["good", "neutral", "bad"]
        },
        "side_quests": [
            {"start": 15, "episodes": 3, "optional": True},
            {"start": 25, "episodes": 2, "optional": True}
        ]
    },
    optimization_goals=[
        "maximize_replayability",
        "maintain_narrative_coherence",
        "balance_path_lengths"
    ],
    enable_interactivity=True
)

response = use_case.design_multi_path_story(multi_path_request)

if response.success:
    print(f"マルチパス物語設計完了")
    print(f"複雑度スコア: {response.complexity_score:.1f}")
    print(f"一貫性スコア: {response.coherence_score:.1f}")

    # ストーリーパスの表示
    print(f"\n=== ストーリーパス ({len(response.paths)}本) ===")
    for path in response.paths[:5]:  # 最初の5本
        print(f"\n{path.name}:")
        print(f"  エピソード: {path.episodes}")
        print(f"  選択確率: {path.probability:.1%}")
        print(f"  物語重要度: {path.narrative_weight:.1f}")
        if not path.is_canonical:
            print(f"  ※ 番外編")

    # 分岐点の表示
    print(f"\n=== 主要分岐点 ===")
    for branch in response.branch_points:
        print(f"\n第{branch.episode_number}話での分岐:")
        print(f"  タイプ: {branch.branch_type}")
        print(f"  選択肢: {len(branch.options)}個")
        for i, option in enumerate(branch.options, 1):
            print(f"    {i}. {option.description}")
        if branch.merge_point:
            print(f"  合流点: 第{branch.merge_point}話")

# 分岐物語の作成
branch_options = [
    {
        "option_id": "hero_path",
        "description": "英雄として立ち上がる",
        "next_episode": 21,
        "consequences": ["味方増加", "敵対勢力の警戒"],
        "required_conditions": ["勇気ポイント >= 50"]
    },
    {
        "option_id": "stealth_path",
        "description": "影から行動する",
        "next_episode": 22,
        "consequences": ["情報収集", "孤独な戦い"],
        "required_conditions": []
    },
    {
        "option_id": "diplomat_path",
        "description": "交渉による解決を試みる",
        "next_episode": 23,
        "consequences": ["同盟可能性", "時間消費"],
        "required_conditions": ["交渉スキル >= 30"]
    }
]

branch_point = use_case.create_branching_narrative(
    project_name="interactive_fantasy",
    branch_episode=20,
    branch_options=branch_options
)

print(f"\n分岐点作成: 第{branch_point.episode_number}話")
print(f"影響範囲: {branch_point.impact_scope}")

# 並行ストーリーラインの管理
parallel_stories = [
    {
        "name": "主人公の旅",
        "episodes": list(range(1, 31)),
        "perspective": "主人公"
    },
    {
        "name": "宿敵の陰謀",
        "episodes": list(range(5, 28, 3)),
        "perspective": "敵視点",
        "timeline_offset": -2  # 2話分前の時系列
    },
    {
        "name": "王国の政治",
        "episodes": list(range(10, 30, 5)),
        "perspective": "第三者",
        "timeline_offset": 0
    }
]

parallel_structure = use_case.manage_parallel_storylines(
    project_name="interactive_fantasy",
    storylines=parallel_stories,
    sync_strategy="key_events"
)

print(f"\n=== 並行ストーリーライン ===")
for storyline in parallel_structure.storylines:
    print(f"\n{storyline.name}:")
    print(f"  視点: {storyline.perspective}")
    print(f"  エピソード数: {len(storyline.episodes)}")
    print(f"  同期ポイント: {storyline.sync_points}")

# インタラクティブ要素の設計
interaction_points = [
    {
        "episode": 15,
        "type": "reader_vote",
        "question": "主人公は誰を信じるべきか？",
        "duration": "48時間",
        "affects": ["character_relationships", "story_branch"]
    },
    {
        "episode": 25,
        "type": "puzzle",
        "description": "古代の謎を解く",
        "success_path": 26,
        "failure_path": 27
    }
]

interactive_design = use_case.design_interactive_elements(
    project_name="interactive_fantasy",
    interaction_points=interaction_points
)

print(f"\n=== インタラクティブ要素 ===")
for element in interactive_design.elements:
    print(f"\n第{element.episode}話:")
    print(f"  タイプ: {element.type}")
    print(f"  説明: {element.description}")
    print(f"  影響: {element.impact}")

# 物語グラフの可視化データ
graph_data = response.story_graph.to_visualization_format()
print(f"\n物語グラフ:")
print(f"  ノード数: {len(graph_data['nodes'])}")
print(f"  エッジ数: {len(graph_data['edges'])}")
print(f"  最長パス: {graph_data['longest_path_length']}話")
print(f"  最短パス: {graph_data['shortest_path_length']}話")
```

## 複雑度管理

### 複雑度メトリクス
```python
complexity_metrics = {
    "cyclomatic_complexity": float,      # サイクロマティック複雑度
    "narrative_entropy": float,          # 物語エントロピー
    "choice_paralysis_risk": float,      # 選択麻痺リスク
    "coherence_challenge": float,        # 一貫性維持難度
    "reader_cognitive_load": float       # 読者認知負荷
}
```

### 複雑度制御戦略
```python
def _control_complexity(self, story_graph: StoryGraph) -> StoryGraph:
    if story_graph.complexity > self.max_complexity:
        # プルーニング戦略
        pruned_paths = self._prune_redundant_paths(story_graph)

        # マージ戦略
        merged_branches = self._merge_similar_branches(pruned_paths)

        # 簡素化戦略
        simplified = self._simplify_choice_points(merged_branches)

    return simplified
```

## エラーハンドリング

### 循環参照の検出
```python
def _detect_cycles(self, story_graph: StoryGraph) -> list[Cycle]:
    visited = set()
    rec_stack = set()
    cycles = []

    for node in story_graph.nodes:
        if node not in visited:
            self._dfs_cycle_detection(
                node, visited, rec_stack, cycles, story_graph
            )

    return cycles
```

### 到達不可能パスの処理
```python
unreachable_paths = self._find_unreachable_paths(story_graph)
if unreachable_paths:
    logger.warning(f"到達不可能なパス検出: {len(unreachable_paths)}")
    # 自動修復または警告
```

## テスト観点

### 単体テスト
- グラフ構築アルゴリズム
- パス探索の正確性
- 一貫性検証ロジック
- インタラクション処理

### 統合テスト
- 大規模な分岐構造での性能
- 並行ストーリーラインの同期
- リアルタイムインタラクション
- 複雑度制御の効果

### シナリオテスト
- 典型的な分岐パターン
- エッジケースの処理
- 読者選択シミュレーション

## 品質基準

- **柔軟性**: 多様な物語構造のサポート
- **一貫性**: 全パスでの物語的整合性
- **管理性**: 複雑な構造の効率的管理
- **体験性**: 豊かな読者体験の提供
- **拡張性**: 新しい遷移パターンの追加容易性
