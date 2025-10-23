# IntegrationYamlPlotRepository 仕様書

## 概要

`IntegrationYamlPlotRepository`は、プロット関連データ（マスタープロット、章別プロット、シーン設計）を統合的に管理するリポジトリです。複数のYAMLファイルに分散したプロット情報を一元的にアクセス・更新できる機能を提供します。

## クラス設計

```python
class IntegrationYamlPlotRepository:
    """統合プロットデータYAMLリポジトリ"""

    def __init__(self, project_root: Path):
        """
        Args:
            project_root: プロジェクトルートパス
        """
        self._project_root = project_root
        self._plot_dir = project_root / "20_プロット"
        self._scene_dir = project_root / "50_管理資料"
        self._cache: Dict[str, Any] = {}
        self._file_watchers: Dict[Path, float] = {}  # ファイル更新監視
```

## データ構造

### インターフェース

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

class IntegrationYamlPlotRepositoryInterface(ABC):
    """統合プロットリポジトリインターフェース"""

    @abstractmethod
    def find_master_plot(self) -> Optional[MasterPlot]:
        """マスタープロットを取得"""
        pass

    @abstractmethod
    def find_chapter_plot(self, chapter_number: int) -> Optional[ChapterPlot]:
        """章別プロットを取得"""
        pass

    @abstractmethod
    def find_all_chapter_plots(self) -> List[ChapterPlot]:
        """全章のプロットを取得"""
        pass

    @abstractmethod
    def find_scene_design(self, scene_id: str) -> Optional[SceneDesign]:
        """シーン設計を取得"""
        pass

    @abstractmethod
    def find_scenes_by_chapter(self, chapter_number: int) -> List[SceneDesign]:
        """章のシーン一覧を取得"""
        pass

    @abstractmethod
    def save_master_plot(self, plot: MasterPlot) -> None:
        """マスタープロットを保存"""
        pass

    @abstractmethod
    def save_chapter_plot(self, plot: ChapterPlot) -> None:
        """章別プロットを保存"""
        pass

    @abstractmethod
    def save_scene_design(self, scene: SceneDesign) -> None:
        """シーン設計を保存"""
        pass

    @abstractmethod
    def analyze_plot_consistency(self) -> PlotConsistencyReport:
        """プロット整合性を分析"""
        pass

    @abstractmethod
    def get_plot_progress(self) -> PlotProgressReport:
        """プロット進捗を取得"""
        pass
```

### データモデル

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class PlotStatus(Enum):
    """プロットステータス"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"

class SceneType(Enum):
    """シーンタイプ"""
    ACTION = "action"
    DIALOGUE = "dialogue"
    DESCRIPTION = "description"
    EMOTION = "emotion"
    TURNING_POINT = "turning_point"

@dataclass
class PlotElement:
    """プロット要素基底クラス"""
    id: str
    title: str
    description: str
    status: PlotStatus
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MasterPlot(PlotElement):
    """マスタープロット"""
    theme: str
    premise: str
    target_episodes: int
    story_arcs: List[StoryArc]
    key_events: List[KeyEvent]
    world_setting: Dict[str, Any]
    character_arcs: Dict[str, CharacterArc]
    resource_allocation: ResourceAllocation

@dataclass
class StoryArc:
    """ストーリーアーク"""
    arc_id: str
    name: str
    start_chapter: int
    end_chapter: int
    description: str
    key_points: List[str]
    tension_curve: List[float]  # 0-100の緊張度

@dataclass
class KeyEvent:
    """重要イベント"""
    event_id: str
    name: str
    chapter: int
    episode: Optional[int]
    impact_level: int  # 1-10
    affected_characters: List[str]
    consequences: List[str]

@dataclass
class CharacterArc:
    """キャラクターアーク"""
    character_name: str
    initial_state: str
    transformation: str
    key_moments: List[Tuple[int, str]]  # (章番号, 説明)
    relationships: Dict[str, RelationshipEvolution]

@dataclass
class RelationshipEvolution:
    """関係性の変化"""
    target_character: str
    initial_relationship: str
    evolution_points: List[Tuple[int, str]]  # (章番号, 変化内容)
    final_relationship: str

@dataclass
class ChapterPlot(PlotElement):
    """章別プロット"""
    chapter_number: int
    episode_range: Tuple[int, int]  # (開始話数, 終了話数)
    chapter_theme: str
    objectives: List[str]
    conflicts: List[Conflict]
    resolutions: List[str]
    scenes: List[SceneOutline]
    word_count_target: int
    pacing_notes: str

@dataclass
class Conflict:
    """コンフリクト"""
    conflict_type: str  # internal, external, environmental
    description: str
    involved_parties: List[str]
    stakes: str
    resolution_hint: Optional[str] = None

@dataclass
class SceneOutline:
    """シーン概要"""
    scene_id: str
    scene_type: SceneType
    location: str
    characters: List[str]
    purpose: str
    key_dialogue: Optional[str] = None
    mood: str
    transition: str

@dataclass
class SceneDesign(PlotElement):
    """詳細シーン設計"""
    scene_id: str
    chapter_number: int
    episode_number: Optional[int]
    scene_type: SceneType
    detailed_setting: SceneSetting
    character_states: Dict[str, CharacterState]
    sensory_details: SensoryDetails
    emotional_beats: List[EmotionalBeat]
    dialogue_notes: List[DialogueNote]
    action_choreography: Optional[ActionChoreography]
    symbolism: List[SymbolicElement]

@dataclass
class SceneSetting:
    """シーン設定"""
    location: str
    time_of_day: str
    weather: Optional[str]
    atmosphere: str
    important_objects: List[str]
    spatial_layout: Optional[str]

@dataclass
class CharacterState:
    """キャラクター状態"""
    physical_state: str
    emotional_state: str
    motivation: str
    internal_conflict: Optional[str]
    observable_behavior: str

@dataclass
class SensoryDetails:
    """感覚的詳細"""
    visual: List[str]
    auditory: List[str]
    tactile: List[str]
    olfactory: List[str]
    gustatory: List[str]

@dataclass
class EmotionalBeat:
    """感情ビート"""
    timing: str
    emotion: str
    intensity: int  # 1-10
    trigger: str
    manifestation: str

@dataclass
class ResourceAllocation:
    """リソース配分"""
    total_episodes: int
    chapter_allocations: Dict[int, int]  # 章番号: 話数
    pacing_strategy: str
    buffer_episodes: int
```

## パブリックメソッド

### プロット取得

```python
def find_master_plot(self) -> Optional[MasterPlot]:
    """マスタープロットを取得"""
    plot_path = self._plot_dir / "全体構成.yaml"

    # キャッシュチェック
    if self._is_cached_valid(plot_path):
        return self._cache.get("master_plot")

    if not plot_path.exists():
        return None

    data = self._load_yaml(plot_path)
    master_plot = self._create_master_plot(data)

    # キャッシュ更新
    self._update_cache("master_plot", master_plot, plot_path)
    return master_plot

def find_chapter_plot(self, chapter_number: int) -> Optional[ChapterPlot]:
    """章別プロットを取得"""
    plot_path = self._plot_dir / "章別プロット" / f"第{chapter_number}章.yaml"
    cache_key = f"chapter_{chapter_number}"

    if self._is_cached_valid(plot_path):
        return self._cache.get(cache_key)

    if not plot_path.exists():
        return None

    data = self._load_yaml(plot_path)
    chapter_plot = self._create_chapter_plot(chapter_number, data)

    self._update_cache(cache_key, chapter_plot, plot_path)
    return chapter_plot

def find_all_chapter_plots(self) -> List[ChapterPlot]:
    """全章のプロットを取得"""
    chapter_dir = self._plot_dir / "章別プロット"
    if not chapter_dir.exists():
        return []

    plots = []
    for yaml_file in sorted(chapter_dir.glob("第*章.yaml")):
        # 章番号を抽出
        match = re.match(r"第(\d+)章\.yaml", yaml_file.name)
        if match:
            chapter_number = int(match.group(1))
            plot = self.find_chapter_plot(chapter_number)
            if plot:
                plots.append(plot)

    return plots
```

### プロット保存

```python
def save_master_plot(self, plot: MasterPlot) -> None:
    """マスタープロットを保存"""
    plot_path = self._plot_dir / "全体構成.yaml"
    plot.updated_at = datetime.now()

    # 既存データとマージ（メタデータ保持）
    existing_data = self._load_yaml(plot_path) if plot_path.exists() else {}
    plot_data = self._master_plot_to_dict(plot)
    merged_data = self._merge_plot_data(existing_data, plot_data)

    self._save_yaml(plot_path, merged_data)
    self._update_cache("master_plot", plot, plot_path)

def save_chapter_plot(self, plot: ChapterPlot) -> None:
    """章別プロットを保存"""
    chapter_dir = self._plot_dir / "章別プロット"
    chapter_dir.mkdir(exist_ok=True)

    plot_path = chapter_dir / f"第{plot.chapter_number}章.yaml"
    plot.updated_at = datetime.now()

    existing_data = self._load_yaml(plot_path) if plot_path.exists() else {}
    plot_data = self._chapter_plot_to_dict(plot)
    merged_data = self._merge_plot_data(existing_data, plot_data)

    self._save_yaml(plot_path, merged_data)
    cache_key = f"chapter_{plot.chapter_number}"
    self._update_cache(cache_key, plot, plot_path)

def save_scene_design(self, scene: SceneDesign) -> None:
    """シーン設計を保存"""
    scene_file = self._scene_dir / "重要シーン.yaml"
    scene.updated_at = datetime.now()

    # 既存のシーンデータを読み込み
    data = self._load_yaml(scene_file) if scene_file.exists() else {"scenes": {}}

    # シーンデータを更新
    scene_data = self._scene_design_to_dict(scene)
    data["scenes"][scene.scene_id] = scene_data
    data["updated_at"] = datetime.now().isoformat()

    self._save_yaml(scene_file, data)
    cache_key = f"scene_{scene.scene_id}"
    self._update_cache(cache_key, scene, scene_file)
```

### プロット分析

```python
def analyze_plot_consistency(self) -> PlotConsistencyReport:
    """プロット整合性を分析"""
    master_plot = self.find_master_plot()
    chapter_plots = self.find_all_chapter_plots()

    issues = []
    warnings = []

    if not master_plot:
        issues.append("マスタープロットが存在しません")
        return PlotConsistencyReport(issues=issues, warnings=warnings)

    # 章数の整合性チェック
    expected_chapters = len(master_plot.resource_allocation.chapter_allocations)
    actual_chapters = len(chapter_plots)
    if expected_chapters != actual_chapters:
        issues.append(f"章数の不一致: 予定{expected_chapters}章、実際{actual_chapters}章")

    # ストーリーアークの整合性
    for arc in master_plot.story_arcs:
        for chapter_num in range(arc.start_chapter, arc.end_chapter + 1):
            chapter_plot = next((cp for cp in chapter_plots if cp.chapter_number == chapter_num), None)
            if not chapter_plot:
                warnings.append(f"第{chapter_num}章のプロットが未作成（{arc.name}の一部）")

    # キャラクターアークの追跡
    for char_name, char_arc in master_plot.character_arcs.items():
        for chapter_num, moment in char_arc.key_moments:
            chapter_plot = next((cp for cp in chapter_plots if cp.chapter_number == chapter_num), None)
            if chapter_plot and char_name not in str(chapter_plot.scenes):
                warnings.append(f"第{chapter_num}章に{char_name}の重要な場面が含まれていない可能性")

    # 話数配分の検証
    total_episodes = sum(cp.episode_range[1] - cp.episode_range[0] + 1 for cp in chapter_plots)
    if total_episodes != master_plot.target_episodes:
        issues.append(f"総話数の不一致: 予定{master_plot.target_episodes}話、実際{total_episodes}話")

    return PlotConsistencyReport(
        issues=issues,
        warnings=warnings,
        master_plot=master_plot,
        chapter_plots=chapter_plots,
        analysis_date=datetime.now()
    )

def get_plot_progress(self) -> PlotProgressReport:
    """プロット進捗を取得"""
    master_plot = self.find_master_plot()
    chapter_plots = self.find_all_chapter_plots()
    all_scenes = self._load_all_scenes()

    # 進捗計算
    total_chapters = len(master_plot.resource_allocation.chapter_allocations) if master_plot else 0
    completed_chapters = len([cp for cp in chapter_plots if cp.status == PlotStatus.COMPLETED])

    # シーン設計進捗
    total_scenes = sum(len(cp.scenes) for cp in chapter_plots)
    designed_scenes = len(all_scenes)

    # 章ごとの進捗
    chapter_progress = {}
    for chapter_plot in chapter_plots:
        scene_count = len(chapter_plot.scenes)
        designed_count = len([s for s in all_scenes.values() if s.chapter_number == chapter_plot.chapter_number])
        chapter_progress[chapter_plot.chapter_number] = {
            'status': chapter_plot.status.value,
            'scenes_total': scene_count,
            'scenes_designed': designed_count,
            'completion_rate': (designed_count / scene_count * 100) if scene_count > 0 else 0
        }

    return PlotProgressReport(
        total_chapters=total_chapters,
        completed_chapters=completed_chapters,
        in_progress_chapters=len([cp for cp in chapter_plots if cp.status == PlotStatus.IN_PROGRESS]),
        total_scenes=total_scenes,
        designed_scenes=designed_scenes,
        chapter_progress=chapter_progress,
        overall_completion_rate=(completed_chapters / total_chapters * 100) if total_chapters > 0 else 0,
        last_updated=datetime.now()
    )
```

## プライベートメソッド

### データ変換

```python
def _create_master_plot(self, data: Dict[str, Any]) -> MasterPlot:
    """辞書からマスタープロットを作成"""
    # ストーリーアークの作成
    story_arcs = []
    for arc_data in data.get('story_arcs', []):
        arc = StoryArc(
            arc_id=arc_data.get('arc_id'),
            name=arc_data.get('name'),
            start_chapter=arc_data.get('start_chapter'),
            end_chapter=arc_data.get('end_chapter'),
            description=arc_data.get('description'),
            key_points=arc_data.get('key_points', []),
            tension_curve=arc_data.get('tension_curve', [])
        )
        story_arcs.append(arc)

    # キーイベントの作成
    key_events = []
    for event_data in data.get('key_events', []):
        event = KeyEvent(
            event_id=event_data.get('event_id'),
            name=event_data.get('name'),
            chapter=event_data.get('chapter'),
            episode=event_data.get('episode'),
            impact_level=event_data.get('impact_level', 5),
            affected_characters=event_data.get('affected_characters', []),
            consequences=event_data.get('consequences', [])
        )
        key_events.append(event)

    # キャラクターアークの作成
    character_arcs = {}
    for char_name, arc_data in data.get('character_arcs', {}).items():
        character_arcs[char_name] = self._create_character_arc(char_name, arc_data)

    # リソース配分の作成
    resource_data = data.get('resource_allocation', {})
    resource_allocation = ResourceAllocation(
        total_episodes=resource_data.get('total_episodes', 0),
        chapter_allocations=resource_data.get('chapter_allocations', {}),
        pacing_strategy=resource_data.get('pacing_strategy', ''),
        buffer_episodes=resource_data.get('buffer_episodes', 0)
    )

    return MasterPlot(
        id=data.get('id', 'master_plot'),
        title=data.get('title', ''),
        description=data.get('description', ''),
        status=PlotStatus(data.get('status', 'draft')),
        created_at=self._parse_datetime(data.get('created_at')),
        updated_at=self._parse_datetime(data.get('updated_at')),
        tags=data.get('tags', []),
        metadata=data.get('metadata', {}),
        theme=data.get('theme', ''),
        premise=data.get('premise', ''),
        target_episodes=data.get('target_episodes', 0),
        story_arcs=story_arcs,
        key_events=key_events,
        world_setting=data.get('world_setting', {}),
        character_arcs=character_arcs,
        resource_allocation=resource_allocation
    )

def _master_plot_to_dict(self, plot: MasterPlot) -> Dict[str, Any]:
    """マスタープロットを辞書に変換"""
    return {
        'id': plot.id,
        'title': plot.title,
        'description': plot.description,
        'status': plot.status.value,
        'created_at': plot.created_at.isoformat(),
        'updated_at': plot.updated_at.isoformat(),
        'tags': plot.tags,
        'metadata': plot.metadata,
        'theme': plot.theme,
        'premise': plot.premise,
        'target_episodes': plot.target_episodes,
        'story_arcs': [self._story_arc_to_dict(arc) for arc in plot.story_arcs],
        'key_events': [self._key_event_to_dict(event) for event in plot.key_events],
        'world_setting': plot.world_setting,
        'character_arcs': {name: self._character_arc_to_dict(arc) for name, arc in plot.character_arcs.items()},
        'resource_allocation': self._resource_allocation_to_dict(plot.resource_allocation)
    }
```

### キャッシュ管理

```python
def _is_cached_valid(self, file_path: Path) -> bool:
    """キャッシュが有効かチェック"""
    if not file_path.exists():
        return False

    # ファイルの更新時刻をチェック
    current_mtime = file_path.stat().st_mtime
    cached_mtime = self._file_watchers.get(file_path, 0)

    return current_mtime == cached_mtime

def _update_cache(self, key: str, value: Any, file_path: Path) -> None:
    """キャッシュを更新"""
    self._cache[key] = value
    if file_path.exists():
        self._file_watchers[file_path] = file_path.stat().st_mtime

def _invalidate_cache(self) -> None:
    """キャッシュを無効化"""
    self._cache.clear()
    self._file_watchers.clear()
```

### ユーティリティ

```python
def _load_all_scenes(self) -> Dict[str, SceneDesign]:
    """全シーンを読み込み"""
    scene_file = self._scene_dir / "重要シーン.yaml"
    if not scene_file.exists():
        return {}

    data = self._load_yaml(scene_file)
    scenes = {}

    for scene_id, scene_data in data.get('scenes', {}).items():
        scene = self._create_scene_design(scene_id, scene_data)
        scenes[scene_id] = scene

    return scenes

def _merge_plot_data(self, existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """プロットデータをマージ（メタデータ保持）"""
    # 基本的には新しいデータで上書き
    result = new.copy()

    # 作成日時は既存のものを保持
    if 'created_at' in existing and 'created_at' not in new:
        result['created_at'] = existing['created_at']

    # カスタムメタデータは深くマージ
    if 'metadata' in existing and 'metadata' in new:
        result['metadata'] = {**existing['metadata'], **new['metadata']}

    return result
```

## 永続化仕様

### ファイル構造

```
[プロジェクト名]/
├── 20_プロット/
│   ├── 全体構成.yaml          # マスタープロット
│   ├── 章別プロット/
│   │   ├── 第1章.yaml
│   │   ├── 第2章.yaml
│   │   └── ...
│   └── リソース配分.yaml      # 話数配分詳細
└── 50_管理資料/
    └── 重要シーン.yaml        # シーン設計集
```

### YAMLフォーマット

#### マスタープロット（全体構成.yaml）
```yaml
id: "master_plot"
title: "転生したら最強の魔法使いだった件 - 全体構成"
description: "異世界転生ファンタジーの全体プロット"
status: "in_progress"
created_at: "2025-01-01T10:00:00"
updated_at: "2025-01-21T15:30:00"

theme: "弱者が知恵と勇気で成長する物語"
premise: "現代の大学生が異世界に転生し、最弱と思われた能力で最強になる"
target_episodes: 100

story_arcs:
  - arc_id: "arc_1"
    name: "覚醒編"
    start_chapter: 1
    end_chapter: 3
    description: "主人公が自分の能力に目覚める"
    key_points:
      - "転生と能力の発見"
      - "最初の仲間との出会い"
      - "初めての大きな戦い"
    tension_curve: [20, 30, 40, 60, 80, 70, 90, 60]

key_events:
  - event_id: "event_001"
    name: "転生"
    chapter: 1
    episode: 1
    impact_level: 10
    affected_characters: ["主人公"]
    consequences:
      - "新しい世界での生活開始"
      - "魔法能力の覚醒"

character_arcs:
  主人公:
    initial_state: "平凡な大学生"
    transformation: "最強の魔法使い"
    key_moments:
      - [1, "転生と能力覚醒"]
      - [3, "初めての勝利"]
      - [5, "師匠との出会い"]

resource_allocation:
  total_episodes: 100
  chapter_allocations:
    1: 10
    2: 8
    3: 12
  pacing_strategy: "序盤は丁寧に、中盤から加速"
  buffer_episodes: 5
```

#### 章別プロット（第1章.yaml）
```yaml
id: "chapter_1"
title: "第1章 - 異世界への転生"
description: "主人公が異世界に転生し、新たな人生を始める"
status: "completed"
chapter_number: 1
episode_range: [1, 10]
chapter_theme: "新世界での目覚めと適応"

objectives:
  - "世界観の提示"
  - "主人公の能力の伏線"
  - "基本的な人間関係の構築"

conflicts:
  - conflict_type: "internal"
    description: "前世の記憶と現在の状況のギャップ"
    involved_parties: ["主人公"]
    stakes: "アイデンティティの確立"

  - conflict_type: "external"
    description: "村を襲う魔物"
    involved_parties: ["主人公", "村人", "魔物"]
    stakes: "村の存続"

scenes:
  - scene_id: "ch1_sc1"
    scene_type: "description"
    location: "見知らぬ森"
    characters: ["主人公"]
    purpose: "転生直後の混乱と世界観の提示"
    mood: "神秘的で不安"
    transition: "意識を失う"
```

## 依存関係

- `pathlib.Path`: ファイルパス操作
- `yaml`: YAML形式の読み書き
- `datetime`: タイムスタンプ管理
- `re`: ファイル名からの章番号抽出
- `dataclasses`: データモデル定義
- Domain層のPlotエンティティ群

## 設計原則遵守

### DDDの原則
- **レポジトリパターン**: プロット永続化の詳細を隠蔽
- **集約**: プロット全体の一貫性を保証
- **値オブジェクト**: プロット要素を不変オブジェクトとして扱う

### リポジトリパターンの実装
- 複数YAMLファイルの統合的管理
- キャッシュによるパフォーマンス最適化
- ファイル更新の自動検知

## 使用例

```python
# リポジトリの初期化
plot_repo = IntegrationYamlPlotRepository(
    project_root=Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/転生したら最強の魔法使いだった件")
)

# マスタープロットの作成
master_plot = MasterPlot(
    id="master_plot",
    title="転生したら最強の魔法使いだった件",
    description="異世界転生ファンタジー",
    status=PlotStatus.IN_PROGRESS,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    theme="弱者が知恵と勇気で成長する物語",
    premise="現代の大学生が異世界に転生し、最弱と思われた能力で最強になる",
    target_episodes=100,
    story_arcs=[
        StoryArc(
            arc_id="arc_1",
            name="覚醒編",
            start_chapter=1,
            end_chapter=3,
            description="主人公が自分の能力に目覚める",
            key_points=["転生", "能力発見", "初戦"],
            tension_curve=[20, 40, 60, 80, 70]
        )
    ],
    key_events=[],
    world_setting={"magic_system": "属性魔法", "technology_level": "中世"},
    character_arcs={},
    resource_allocation=ResourceAllocation(
        total_episodes=100,
        chapter_allocations={1: 10, 2: 8, 3: 12},
        pacing_strategy="序盤は丁寧に",
        buffer_episodes=5
    )
)

plot_repo.save_master_plot(master_plot)

# 章別プロットの作成
chapter1_plot = ChapterPlot(
    id="chapter_1",
    title="第1章 - 異世界への転生",
    description="主人公が異世界に転生し、新たな人生を始める",
    status=PlotStatus.COMPLETED,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    chapter_number=1,
    episode_range=(1, 10),
    chapter_theme="新世界での目覚めと適応",
    objectives=["世界観の提示", "能力の伏線"],
    conflicts=[
        Conflict(
            conflict_type="internal",
            description="前世の記憶との葛藤",
            involved_parties=["主人公"],
            stakes="アイデンティティの確立"
        )
    ],
    resolutions=["自分の運命を受け入れる"],
    scenes=[
        SceneOutline(
            scene_id="ch1_sc1",
            scene_type=SceneType.DESCRIPTION,
            location="見知らぬ森",
            characters=["主人公"],
            purpose="転生直後の混乱",
            mood="神秘的",
            transition="意識を失う"
        )
    ],
    word_count_target=30000,
    pacing_notes="ゆっくりと世界観を展開"
)

plot_repo.save_chapter_plot(chapter1_plot)

# プロット整合性の分析
consistency_report = plot_repo.analyze_plot_consistency()
if consistency_report.issues:
    print("整合性の問題:")
    for issue in consistency_report.issues:
        print(f"  - {issue}")

# プロット進捗の確認
progress = plot_repo.get_plot_progress()
print(f"全体進捗: {progress.overall_completion_rate:.1f}%")
print(f"完成章数: {progress.completed_chapters}/{progress.total_chapters}")

# シーン設計の詳細化
scene = SceneDesign(
    scene_id="ch1_sc1",
    title="転生の瞬間",
    description="主人公が異世界で目覚める",
    status=PlotStatus.COMPLETED,
    created_at=datetime.now(),
    updated_at=datetime.now(),
    chapter_number=1,
    episode_number=1,
    scene_type=SceneType.DESCRIPTION,
    detailed_setting=SceneSetting(
        location="古い森の奥深く",
        time_of_day="夕暮れ",
        weather="霧が立ち込めている",
        atmosphere="神秘的で少し不気味",
        important_objects=["光る石", "古い祭壇"],
        spatial_layout="円形の空き地、中央に祭壇"
    ),
    character_states={
        "主人公": CharacterState(
            physical_state="疲労困憊",
            emotional_state="混乱と不安",
            motivation="状況を理解したい",
            internal_conflict="これは夢か現実か",
            observable_behavior="きょろきょろと周囲を見回す"
        )
    },
    sensory_details=SensoryDetails(
        visual=["薄暗い森", "光る苔", "古代文字"],
        auditory=["鳥の鳴き声", "風の音", "遠くの水音"],
        tactile=["湿った土", "冷たい空気"],
        olfactory=["土と落ち葉の匂い", "かすかな花の香り"],
        gustatory=[]
    ),
    emotional_beats=[
        EmotionalBeat(
            timing="冒頭",
            emotion="混乱",
            intensity=8,
            trigger="見知らぬ場所で目覚める",
            manifestation="頭を抱える、呼吸が荒くなる"
        )
    ],
    dialogue_notes=[],
    action_choreography=None,
    symbolism=[]
)

plot_repo.save_scene_design(scene)

# 特定章のシーン一覧取得
chapter1_scenes = plot_repo.find_scenes_by_chapter(1)
for scene in chapter1_scenes:
    print(f"シーン: {scene.title} - {scene.scene_type.value}")
```

## エラーハンドリング

```python
class PlotError(Exception):
    """プロットエラーの基底クラス"""
    pass

class PlotNotFoundError(PlotError):
    """プロットが見つからない"""
    pass

class PlotConsistencyError(PlotError):
    """プロット整合性エラー"""
    pass

class PlotValidationError(PlotError):
    """プロット検証エラー"""
    pass

# 使用例
try:
    # 存在しない章のプロット取得
    chapter_plot = plot_repo.find_chapter_plot(99)
    if not chapter_plot:
        raise PlotNotFoundError("第99章のプロットが存在しません")

    # プロット整合性チェック
    report = plot_repo.analyze_plot_consistency()
    if report.issues:
        raise PlotConsistencyError(f"プロットに整合性の問題があります: {report.issues}")

except PlotError as e:
    logger.error(f"プロットエラー: {e}")
    # エラーに応じた対処
```

## テスト観点

### ユニットテスト
- 各プロットタイプの作成・読み込み・保存
- データ変換ロジック
- キャッシュ機能
- ファイル更新検知

### 統合テスト
- 複数YAMLファイルの連携
- プロット整合性分析
- 進捗計算の正確性
- 大規模プロットデータの処理

### E2Eテスト
```gherkin
Feature: 統合プロット管理
  Scenario: プロット全体の一貫性維持
    Given マスタープロットで100話構成を計画している
    When 各章のプロットを作成する
    Then 合計話数が100話になる
    And 各章の話数配分が計画通りである
```

## 品質基準

- コードカバレッジ: 90%以上
- サイクロマティック複雑度: 10以下
- YAMLスキーマ検証の実装
- 大規模データでのパフォーマンステスト
- エラーメッセージの具体性と対処法の明示
