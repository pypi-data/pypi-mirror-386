# SPEC-PLOT-003: 章別プロット・シーン統合ユースケース仕様書

## 要件トレーサビリティ

**要件ID**: REQ-PLOT-004, REQ-PLOT-005, REQ-PLOT-007 (プロット編集・管理・分析)

**主要要件**:
- REQ-PLOT-004: インタラクティブプロット編集
- REQ-PLOT-005: プロットバージョン管理
- REQ-PLOT-007: プロット要素抽出・分析

**実装状況**: ✅実装済み
**テストカバレッジ**: tests/unit/test_chapter_plot_with_scenes_use_case.py
**関連仕様書**: SPEC-PLOT-001_claude-code-integration-plot-generation.md

## 概要
`ChapterPlotWithScenesUseCase`は、章別プロットとシーン詳細を統合的に管理するユースケースです。章の全体構造設計、シーンの詳細設計、シーン間の関連性管理、エピソードへの展開支援を包括的に提供し、構造化された物語展開を実現します。

## クラス設計

### ChapterPlotWithScenesUseCase

**責務**
- 章別プロットの作成と管理
- シーン詳細の設計と保存
- シーン間の依存関係管理
- エピソード分割の提案
- プロット・シーン統合ビューの生成
- 執筆ガイドラインの自動生成

## データ構造

### SceneType (Enum)
```python
class SceneType(Enum):
    ACTION = "action"                # アクションシーン
    DIALOGUE = "dialogue"            # 会話シーン
    EXPOSITION = "exposition"        # 説明・描写シーン
    EMOTIONAL = "emotional"          # 感情シーン
    TRANSITION = "transition"        # 転換シーン
    CLIMAX = "climax"               # クライマックスシーン
```

### SceneDetail (DataClass)
```python
@dataclass
class SceneDetail:
    scene_id: str                    # シーンID
    scene_type: SceneType            # シーンタイプ
    title: str                       # シーンタイトル
    purpose: str                     # シーンの目的
    location: str                    # 場所
    time: str                        # 時間帯
    characters: list[str]            # 登場人物
    key_events: list[str]            # 主要イベント
    emotions: dict[str, str]         # キャラクター別感情
    foreshadowing: list[str] = []    # 伏線要素
    callbacks: list[str] = []        # 回収要素
    estimated_words: int = 0         # 推定文字数
    writing_notes: str = ""          # 執筆メモ
```

### ChapterPlotRequest (DataClass)
```python
@dataclass
class ChapterPlotRequest:
    project_name: str                # プロジェクト名
    chapter_number: int              # 章番号
    chapter_theme: str               # 章のテーマ
    target_word_count: int           # 目標文字数
    create_scenes: bool = True       # シーン作成フラグ
    auto_split_episodes: bool = True # エピソード自動分割フラグ
    scene_templates: list[str] = []  # 使用するシーンテンプレート
```

### ChapterPlotResponse (DataClass)
```python
@dataclass
class ChapterPlotResponse:
    success: bool                    # 処理成功フラグ
    message: str                     # 結果メッセージ
    chapter_file: Path | None = None # 章プロットファイルパス
    scene_count: int = 0             # 作成シーン数
    suggested_episodes: list[dict] = [] # 推奨エピソード分割
    total_estimated_words: int = 0   # 推定総文字数
    plot_summary: str = ""           # プロットサマリー
```

### ChapterStructure (DataClass)
```python
@dataclass
class ChapterStructure:
    chapter_number: int              # 章番号
    title: str                       # 章タイトル
    theme: str                       # 章のテーマ
    synopsis: str                    # あらすじ
    scenes: list[SceneDetail]        # シーンリスト
    plot_points: list[str]           # プロットポイント
    character_arcs: dict[str, str]   # キャラクターアーク
    pacing: str                      # ペーシング（slow/medium/fast）
    tension_curve: list[int]         # 緊張曲線（1-10）
```

### EpisodeSuggestion (DataClass)
```python
@dataclass
class EpisodeSuggestion:
    episode_number: int              # エピソード番号
    title: str                       # エピソードタイトル
    included_scenes: list[str]       # 含まれるシーンID
    estimated_words: int             # 推定文字数
    start_hook: str                  # 開始フック
    end_hook: str                    # 終了フック
    key_points: list[str]            # 重要ポイント
```

## パブリックメソッド

### create_chapter_plot()

**シグネチャ**
```python
def create_chapter_plot(self, request: ChapterPlotRequest) -> ChapterPlotResponse:
```

**目的**
章別プロットを作成し、シーン詳細を含む構造化されたプロットを生成する。

**引数**
- `request`: 章プロット作成リクエスト

**戻り値**
- `ChapterPlotResponse`: 作成結果

**処理フロー**
1. **マスタープロット確認**: 全体構成との整合性確認
2. **章構造設計**: テーマに基づく章構造の設計
3. **シーン生成**: 章構造に基づくシーン詳細の生成
4. **関連性設定**: シーン間の依存関係設定
5. **エピソード分割**: 適切なエピソード分割の提案
6. **ファイル保存**: 構造化データの保存
7. **サマリー生成**: 執筆用サマリーの作成

### add_scene_to_chapter()

**シグネチャ**
```python
def add_scene_to_chapter(
    self,
    project_name: str,
    chapter_number: int,
    scene: SceneDetail,
    position: int | None = None
) -> bool:
```

**目的**
既存の章にシーンを追加する。

### update_scene_details()

**シグネチャ**
```python
def update_scene_details(
    self,
    project_name: str,
    chapter_number: int,
    scene_id: str,
    updates: dict[str, any]
) -> bool:
```

**目的**
シーンの詳細情報を更新する。

### generate_writing_guide()

**シグネチャ**
```python
def generate_writing_guide(
    self,
    project_name: str,
    chapter_number: int,
    scene_id: str | None = None
) -> str:
```

**目的**
章またはシーンの執筆ガイドを生成する。

### analyze_chapter_pacing()

**シグネチャ**
```python
def analyze_chapter_pacing(
    self,
    project_name: str,
    chapter_number: int
) -> dict[str, any]:
```

**目的**
章のペーシングとリズムを分析する。

## プライベートメソッド

### _design_chapter_structure()

**シグネチャ**
```python
def _design_chapter_structure(
    self,
    chapter_theme: str,
    target_word_count: int,
    master_plot_context: dict
) -> ChapterStructure:
```

**目的**
マスタープロットのコンテキストに基づいて章構造を設計する。

### _generate_scenes()

**シグネチャ**
```python
def _generate_scenes(
    self,
    chapter_structure: ChapterStructure,
    scene_templates: list[str]
) -> list[SceneDetail]:
```

**目的**
章構造に基づいてシーン詳細を生成する。

**シーン生成ロジック**
```python
# 基本的なシーン構成
scene_composition = {
    "opening": 1,        # 導入シーン
    "development": 3-5,  # 展開シーン
    "turning_point": 1,  # 転換点シーン
    "climax": 1,         # クライマックスシーン
    "resolution": 1      # 解決シーン
}
```

### _calculate_scene_dependencies()

**シグネチャ**
```python
def _calculate_scene_dependencies(
    self,
    scenes: list[SceneDetail]
) -> dict[str, list[str]]:
```

**目的**
シーン間の依存関係を計算する。

### _suggest_episode_splits()

**シグネチャ**
```python
def _suggest_episode_splits(
    self,
    scenes: list[SceneDetail],
    target_words_per_episode: int = 4000
) -> list[EpisodeSuggestion]:
```

**目的**
シーンを適切なエピソードに分割する提案を生成する。

**分割基準**
- 目標文字数の維持
- シーンの完結性
- クリフハンガーの配置
- ペーシングのバランス

### _create_scene_transition_map()

**シグネチャ**
```python
def _create_scene_transition_map(
    self,
    scenes: list[SceneDetail]
) -> dict[str, dict[str, str]]:
```

**目的**
シーン間の遷移マップを作成する。

### _generate_plot_summary()

**シグネチャ**
```python
def _generate_plot_summary(
    self,
    chapter_structure: ChapterStructure,
    episode_suggestions: list[EpisodeSuggestion]
) -> str:
```

**目的**
章プロットの執筆用サマリーを生成する。

## シーンテンプレート

### アクションシーンテンプレート
```python
action_template = {
    "structure": {
        "setup": "状況設定と緊張の構築",
        "escalation": "アクションの段階的激化",
        "climax": "最高潮の瞬間",
        "resolution": "結果と余韻"
    },
    "elements": ["物理的障害", "時間制限", "リスクと結果"],
    "pacing": "fast",
    "word_distribution": {
        "description": 40,
        "action": 40,
        "dialogue": 20
    }
}
```

### 感情シーンテンプレート
```python
emotional_template = {
    "structure": {
        "trigger": "感情を引き起こす出来事",
        "reaction": "初期反応",
        "exploration": "感情の深掘り",
        "resolution": "新たな理解や決意"
    },
    "elements": ["内面描写", "身体的反応", "記憶の想起"],
    "pacing": "slow",
    "word_distribution": {
        "description": 30,
        "internal": 50,
        "dialogue": 20
    }
}
```

## 依存関係

### ドメインサービス
- `PlotAnalyzer`: プロット構造分析
- `SceneGenerator`: シーン生成
- `PacingCalculator`: ペーシング計算
- `EpisodeSplitter`: エピソード分割

### リポジトリ
- `ProjectRepository`: プロジェクト情報管理
- `PlotRepository`: プロット情報管理
- `SceneRepository`: シーン情報管理
- `TemplateRepository`: テンプレート管理

## 設計原則遵守

### DDD準拠
- ✅ エンティティ（`ChapterStructure`, `SceneDetail`）の適切な使用
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
plot_analyzer = PlotAnalyzer()
scene_generator = SceneGenerator()
pacing_calculator = PacingCalculator()
episode_splitter = EpisodeSplitter()
project_repo = YamlProjectRepository()
plot_repo = YamlPlotRepository()
scene_repo = YamlSceneRepository()
template_repo = TemplateRepository()

# ユースケース作成
use_case = ChapterPlotWithScenesUseCase(
    plot_analyzer=plot_analyzer,
    scene_generator=scene_generator,
    pacing_calculator=pacing_calculator,
    episode_splitter=episode_splitter,
    project_repository=project_repo,
    plot_repository=plot_repo,
    scene_repository=scene_repo,
    template_repository=template_repo
)

# 章プロットの作成
request = ChapterPlotRequest(
    project_name="fantasy_adventure",
    chapter_number=3,
    chapter_theme="師弟の絆と最初の試練",
    target_word_count=20000,
    create_scenes=True,
    auto_split_episodes=True,
    scene_templates=["action", "emotional", "dialogue"]
)

response = use_case.create_chapter_plot(request)

if response.success:
    print(f"章プロット作成完了: {response.message}")
    print(f"作成シーン数: {response.scene_count}")
    print(f"推定総文字数: {response.total_estimated_words:,}文字")

    print("\n推奨エピソード分割:")
    for suggestion in response.suggested_episodes:
        print(f"\nエピソード{suggestion['episode_number']}: {suggestion['title']}")
        print(f"  含まれるシーン: {', '.join(suggestion['included_scenes'])}")
        print(f"  推定文字数: {suggestion['estimated_words']:,}文字")
        print(f"  開始フック: {suggestion['start_hook']}")
        print(f"  終了フック: {suggestion['end_hook']}")

    print(f"\nプロットサマリー:\n{response.plot_summary}")
else:
    print(f"章プロット作成失敗: {response.message}")

# 個別シーンの追加
new_scene = SceneDetail(
    scene_id="ch3_s8",
    scene_type=SceneType.EMOTIONAL,
    title="師の過去の告白",
    purpose="師弟の絆を深め、主人公の決意を固める",
    location="師の隠れ家",
    time="深夜",
    characters=["主人公", "師匠"],
    key_events=[
        "師が自身の失敗談を語る",
        "主人公が師の人間性を理解する",
        "新たな修行への決意"
    ],
    emotions={
        "主人公": "驚き→共感→決意",
        "師匠": "躊躇→解放→希望"
    },
    foreshadowing=["師の過去の敵との因縁"],
    estimated_words=2000,
    writing_notes="静かで内省的なトーンで。月明かりの描写を効果的に使う。"
)

success = use_case.add_scene_to_chapter(
    project_name="fantasy_adventure",
    chapter_number=3,
    scene=new_scene,
    position=7  # 8番目の位置に挿入
)

print(f"\nシーン追加: {'成功' if success else '失敗'}")

# 執筆ガイドの生成
writing_guide = use_case.generate_writing_guide(
    project_name="fantasy_adventure",
    chapter_number=3,
    scene_id="ch3_s8"
)

print(f"\n執筆ガイド:\n{writing_guide}")

# ペーシング分析
pacing_analysis = use_case.analyze_chapter_pacing(
    project_name="fantasy_adventure",
    chapter_number=3
)

print(f"\nペーシング分析:")
print(f"全体ペース: {pacing_analysis['overall_pacing']}")
print(f"緊張曲線: {pacing_analysis['tension_curve']}")
print(f"シーンバランス: {pacing_analysis['scene_type_balance']}")
print(f"推奨事項: {pacing_analysis['recommendations']}")

# シーン詳細の更新
updates = {
    "estimated_words": 2500,
    "writing_notes": "師の声に震えを持たせる。過去の痛みを表現。",
    "emotions": {
        "主人公": "驚き→共感→決意→不安",
        "師匠": "躊躇→解放→希望→懸念"
    }
}

success = use_case.update_scene_details(
    project_name="fantasy_adventure",
    chapter_number=3,
    scene_id="ch3_s8",
    updates=updates
)
```

## 生成される章プロットファイル例

```yaml
# 20_プロット/章別プロット/第3章.yaml
chapter_info:
  number: 3
  title: "師弟の絆と最初の試練"
  theme: "信頼関係の構築と成長への第一歩"
  target_words: 20000
  actual_estimated: 19500

synopsis: |
  主人公は師匠との修行を開始する。
  初めは反発し合う二人だったが、数々の試練を通じて
  互いを理解し、真の師弟関係を築いていく。
  章の終わりには、最初の大きな試練に挑む。

plot_points:
  - "師匠との出会いと第一印象"
  - "基礎修行での衝突"
  - "師の過去を知る夜"
  - "共同での試練準備"
  - "最初の試練への挑戦"

character_arcs:
  主人公:
    start: "自信過剰で独りよがり"
    end: "謙虚さと協調性を学ぶ"
    key_moments: ["修行での失敗", "師の過去を聞く", "試練での気づき"]

  師匠:
    start: "厳格で近寄りがたい"
    end: "弟子への信頼と期待"
    key_moments: ["弟子の素質を見出す", "過去を打ち明ける", "試練を見守る"]

scenes:
  - id: "ch3_s1"
    type: "dialogue"
    title: "師匠の試験"
    location: "修行場の入口"
    time: "早朝"
    characters: ["主人公", "師匠"]
    estimated_words: 2000
    purpose: "主人公の現在の実力を測り、師弟関係の始まり"

  - id: "ch3_s2"
    type: "action"
    title: "基礎修行 - 失敗の連続"
    location: "修行場"
    time: "午前中"
    characters: ["主人公", "師匠", "先輩弟子"]
    estimated_words: 3000
    purpose: "主人公の未熟さと成長の必要性を示す"

pacing:
  overall: "medium"
  rhythm: "緩→急→緩→急→最急"
  tension_peaks: [2, 5, 9]

episode_splits:
  - episode: 9
    scenes: ["ch3_s1", "ch3_s2"]
    end_hook: "明日からが本当の修行だ"

  - episode: 10
    scenes: ["ch3_s3", "ch3_s4", "ch3_s5"]
    end_hook: "師の瞳に宿る、遠い過去の影"
```

## エラーハンドリング

### マスタープロット不在
```python
if not self.plot_repository.has_master_plot(project_name):
    return ChapterPlotResponse(
        success=False,
        message="マスタープロットが存在しません。先に 'novel plot master' を実行してください。"
    )
```

### シーンID重複
```python
if self.scene_repository.exists(project_name, chapter_number, scene.scene_id):
    raise SceneIdDuplicateError(
        f"シーンID '{scene.scene_id}' は既に存在します。"
    )
```

## テスト観点

### 単体テスト
- 章構造設計の妥当性
- シーン生成ロジック
- エピソード分割アルゴリズム
- ペーシング計算
- 依存関係の処理

### 統合テスト
- 実際のプロジェクトでの章作成
- 大規模章（10シーン以上）の処理
- テンプレート適用の動作
- ファイル入出力

## 品質基準

- **構造性**: 明確で論理的な章構造
- **一貫性**: マスタープロットとの整合性
- **実用性**: 執筆に直結する具体的な情報
- **柔軟性**: シーンの追加・修正の容易さ
- **可視性**: 章全体の見通しの良さ
