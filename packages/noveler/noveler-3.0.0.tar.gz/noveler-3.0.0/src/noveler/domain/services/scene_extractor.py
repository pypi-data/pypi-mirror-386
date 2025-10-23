"""Domain.services.scene_extractor
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
重要シーン抽出サービス
全体構成や伏線情報から重要シーンを抽出する
"""


import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from noveler.domain.value_objects.foreshadowing import Foreshadowing

from noveler.domain.entities.scene_management_entities import SceneCategory


class SceneDict(TypedDict):
    """重要シーン辞書表現"""

    scene_id: str
    title: str
    category: str
    description: str
    importance: str
    chapter: int | None
    episode_range: list[int]
    episodes: list[int]
    source: str


class MasterPlotData(TypedDict, total=False):
    """マスタープロット データ"""

    chapters: list[dict[str, str]]
    key_scenes: list[dict[str, str]]
    climax: dict[str, str]
    resolution: dict[str, str]


class ChapterData(TypedDict, total=False):
    """章データ"""

    title: str
    scenes: list[dict[str, str]]
    summary: str
    key_points: list[str]


class SceneImportance(Enum):
    """シーンの重要度"""

    CRITICAL = "critical"  # 物語の核心
    HIGH = "high"  # 重要な展開
    MEDIUM = "medium"  # 標準的な重要度
    LOW = "low"  # 補助的なシーン


@dataclass
class ExtractedScene:
    """抽出されたシーン情報"""

    scene_id: str
    title: str
    category: SceneCategory
    description: str
    importance: SceneImportance
    chapter: int
    episode_range: tuple[int, int]  # (開始話数, 終了話数)
    source: str  # 抽出元(master_plot, foreshadowing等)

    def to_dict(self) -> SceneDict:
        """辞書形式に変換"""
        return {
            "scene_id": self.scene_id,
            "title": self.title,
            "category": self.category.value,
            "description": self.description,
            "importance": self.importance.value,
            "chapter": self.chapter,
            "episode_range": list(self.episode_range),
            "episodes": list(range(self.episode_range[0], self.episode_range[1] + 1)),
            "source": self.source,
        }


class SceneExtractor:
    """重要シーン抽出サービス"""

    def extract_from_master_plot(self, master_plot_data: MasterPlotData) -> list[ExtractedScene]:
        """全体構成から重要シーンを抽出"""
        scenes = []
        scene_counter = 1

        # メタデータから総話数を取得
        total_episodes = master_plot_data.get("metadata", {}).get("total_episodes", 30)
        total_chapters = master_plot_data.get("metadata", {}).get("total_chapters", 3)
        episodes_per_chapter = total_episodes // max(total_chapters, 1)

        # 物語構成から抽出
        story_structure = master_plot_data.get("story_structure", {})

        # オープニング
        if "opening" in story_structure:
            opening = story_structure["opening"]
            scenes.append(
                ExtractedScene(
                    scene_id=f"scene_{scene_counter:03d}",
                    title="物語の開幕",
                    category=SceneCategory.OPENING,
                    description=opening.get("description", ""),
                    importance=SceneImportance.CRITICAL,
                    chapter=1,
                    episode_range=(1, 2),
                    source="master_plot.opening",
                )
            )
            scene_counter += 1

        # 転換点
        development = story_structure.get("development", {})
        turning_points = development.get("turning_points", [])
        for i, point in enumerate(turning_points):
            chapter = min(i + 1, total_chapters) if total_chapters else 1
            start_ep = (chapter - 1) * episodes_per_chapter + 5
            scenes.append(
                ExtractedScene(
                    scene_id=f"scene_{scene_counter:03d}",
                    title=f"転換点{i + 1}",
                    category=SceneCategory.TURNING_POINT,
                    description=point,
                    importance=SceneImportance.HIGH,
                    chapter=chapter,
                    episode_range=(start_ep, start_ep + 1),
                    source="master_plot.turning_points",
                )
            )
            scene_counter += 1

        # 主要な暴露
        major_revelations = development.get("major_revelations", [])
        for i, revelation in enumerate(major_revelations):
            chapter = 2 if i == 0 else min(3, total_chapters or 3)
            ep = (chapter - 1) * episodes_per_chapter + 8
            scenes.append(
                ExtractedScene(
                    scene_id=f"scene_{scene_counter:03d}",
                    title="重要な真実の開示",
                    category=SceneCategory.CLIMAX,
                    description=revelation,
                    importance=SceneImportance.CRITICAL,
                    chapter=chapter,
                    episode_range=(ep, ep),
                    source="master_plot.revelations",
                )
            )
            scene_counter += 1

        # クライマックス (+解決要素)
        if "climax" in story_structure:
            climax = story_structure["climax"]
            climax_description = climax.get("description", "")
            resolution_text = climax.get("resolution")
            if resolution_text:
                if climax_description:
                    climax_description = f"{climax_description}\n{resolution_text}"
                else:
                    climax_description = resolution_text

            scenes.append(
                ExtractedScene(
                    scene_id=f"scene_{scene_counter:03d}",
                    title="クライマックス",
                    category=SceneCategory.CLIMAX,
                    description=climax_description,
                    importance=SceneImportance.CRITICAL,
                    chapter=max(total_chapters, 1),
                    episode_range=(total_episodes - 3, total_episodes - 1),
                    source="master_plot.climax",
                )
            )

        return scenes

    def extract_from_foreshadowing(self, foreshadowings: list[Foreshadowing]) -> list[ExtractedScene]:
        """伏線情報から重要シーンを抽出"""
        scenes = []
        scene_counter = 100  # 伏線由来のシーンは100番台

        for f in foreshadowings:
            # 重要度が高い伏線のみ
            if f.importance >= 4:
                # 伏線の仕込みシーン
                scenes.append(
                    ExtractedScene(
                        scene_id=f"scene_{scene_counter:03d}",
                        title=f"{f.title}の仕込み",
                        category=SceneCategory.FORESHADOWING,
                        description=f.planting.content,
                        importance=SceneImportance.MEDIUM,
                        chapter=f.planting.chapter,
                        episode_range=(
                            self._extract_episode_number(f.planting.episode),
                            self._extract_episode_number(f.planting.episode),
                        ),
                        source=f"foreshadowing.{f.id.value}.planting",
                    )
                )

                scene_counter += 1

                # 伏線の回収シーン
                scenes.append(
                    ExtractedScene(
                        scene_id=f"scene_{scene_counter:03d}",
                        title=f"{f.title}の回収",
                        category=SceneCategory.CLIMAX,
                        description=f.resolution.impact,
                        importance=SceneImportance.HIGH,
                        chapter=f.resolution.chapter,
                        episode_range=(
                            self._extract_episode_number(f.resolution.episode),
                            self._extract_episode_number(f.resolution.episode),
                        ),
                        source=f"foreshadowing.{f.id.value}.resolution",
                    )
                )

                scene_counter += 1

        return scenes

    def extract_from_chapter_plot(self, chapter_data: ChapterData) -> list[ExtractedScene]:
        """章別プロットから細かなシーンを抽出"""
        scenes = []
        scene_counter = 200  # 章別プロット由来のシーンは200番台

        # データが辞書でない場合の安全チェック
        if not isinstance(chapter_data, dict):
            return scenes

        # メタデータから章情報を取得
        metadata = chapter_data.get("metadata", {})
        chapter_number = metadata.get("chapter_number", 1) if isinstance(metadata, dict) else 1

        # エピソードごとのシーンを抽出
        episodes = chapter_data.get("episodes", [])
        if not isinstance(episodes, list):
            return scenes

        for episode in episodes:
            if not isinstance(episode, dict):
                continue

            episode_number = episode.get("number", 1)
            episode_scenes = episode.get("scenes", [])

            if not isinstance(episode_scenes, list):
                continue

            # 各シーンを詳細に抽出
            for scene_title in episode_scenes:
                scenes.append(
                    ExtractedScene(
                        scene_id=f"scene_{scene_counter:03d}",
                        title=str(scene_title),
                        category=SceneCategory.NORMAL,  # デフォルトは通常シーン
                        description=f"第{chapter_number}章 第{episode_number}話のシーン",
                        importance=SceneImportance.MEDIUM,
                        chapter=chapter_number,
                        episode_range=(episode_number, episode_number),
                        source=f"chapter_plot.ch{chapter_number}.ep{episode_number}",
                    )
                )

                scene_counter += 1

        return scenes

    def merge_and_deduplicate(self, scenes: list[ExtractedScene]) -> list[ExtractedScene]:
        """重複するシーンをマージして整理"""
        if not scenes:
            return []

        # エピソード範囲でグループ化
        episode_map: dict[tuple[int, int], list[ExtractedScene]] = {}
        for scene in scenes:
            episode_map.setdefault(scene.episode_range, []).append(scene)

        # 各グループから最も重要なシーンを選択
        merged_scenes: list[ExtractedScene] = []
        importance_order = {
            SceneImportance.CRITICAL: 0,
            SceneImportance.HIGH: 1,
            SceneImportance.MEDIUM: 2,
            SceneImportance.LOW: 3,
        }

        for group in episode_map.values():
            group.sort(key=lambda s: (importance_order.get(s.importance, 4), s.scene_id))
            primary_scene = group[0]

            if len(group) > 1:
                combined_desc = primary_scene.description or ""
                for other in group[1:]:
                    if other.description and other.description not in combined_desc:
                        combined_desc = (combined_desc + "\n- " + other.description) if combined_desc else other.description
                primary_scene = ExtractedScene(
                    scene_id=primary_scene.scene_id,
                    title=primary_scene.title,
                    category=primary_scene.category,
                    description=combined_desc,
                    importance=primary_scene.importance,
                    chapter=primary_scene.chapter,
                    episode_range=primary_scene.episode_range,
                    source=f"{primary_scene.source}+{len(group) - 1}others",
                )

            merged_scenes.append(primary_scene)

        merged_scenes.sort(key=lambda s: (s.episode_range[0], s.episode_range[1], s.scene_id))
        return merged_scenes

    def _extract_episode_number(self, episode_str: str | tuple[int, int]) -> int:
        """エピソード文字列や範囲から番号を抽出"""

        if isinstance(episode_str, tuple):
            return int(episode_str[0]) if episode_str else 1

        match = re.search(r"\d+", str(episode_str))
        if match:
            return int(match.group())
        return 1  # デフォルト値  # デフォルト値
