"""Domain.value_objects.foreshadowing
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""
伏線管理のための値オブジェクト群
DDD原則に従い、不変性と豊富なビジネスロジックを持つ
"""


import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class ForeshadowingCategory(Enum):
    """伏線のカテゴリー"""

    MAIN = "main"  # メインプロット関連
    CHARACTER = "character"  # キャラクター関連
    WORLDBUILDING = "worldbuilding"  # 世界観・設定関連
    MYSTERY = "mystery"  # 謎・ミステリー関連
    EMOTIONAL = "emotional"  # 感情的伏線
    THEMATIC = "thematic"  # テーマ的伏線


class ForeshadowingStatus(Enum):
    """伏線のステータス"""

    PLANNED = "planned"  # 計画済み
    PLANTED = "planted"  # 仕込み済み
    READY_TO_RESOLVE = "ready_to_resolve"  # 回収準備完了
    RESOLVED = "resolved"  # 回収済み


class SubtletyLevel(Enum):
    """伏線の巧妙さレベル"""

    HIGH = "high"  # 非常に巧妙(読者が気づきにくい)
    MEDIUM = "medium"  # 適度に巧妙
    LOW = "low"  # 明確(読者が気づきやすい)


@dataclass(frozen=True)
class ForeshadowingId:
    """伏線ID値オブジェクト"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            msg = "伏線IDは必須です"
            raise ValueError(msg)
        if not self.value.startswith("F"):
            msg = "伏線IDは'F'で始まる必要があります(例: F001)"
            raise ValueError(msg)
        if len(self.value) != 4:
            msg = "伏線IDは4文字である必要があります(例: F001)"
            raise ValueError(msg)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PlantingInfo:
    """伏線の仕込み情報"""

    episode: str
    chapter: int
    method: str
    content: str
    subtlety_level: SubtletyLevel = SubtletyLevel.MEDIUM

    def __post_init__(self) -> None:
        if not self.episode:
            msg = "仕込みエピソードは必須です"
            raise ValueError(msg)
        if self.chapter < 1:
            msg = "章番号は1以上である必要があります"
            raise ValueError(msg)
        if not self.method:
            msg = "仕込み方法は必須です"
            raise ValueError(msg)
        if not self.content:
            msg = "仕込み内容は必須です"
            raise ValueError(msg)

    def is_subtle(self) -> bool:
        """巧妙な仕込みかどうか"""
        return self.subtlety_level == SubtletyLevel.HIGH


@dataclass(frozen=True)
class ResolutionInfo:
    """伏線の回収情報"""

    episode: str
    chapter: int
    method: str
    impact: str

    def __post_init__(self) -> None:
        if not self.episode:
            msg = "回収エピソードは必須です"
            raise ValueError(msg)
        if self.chapter < 1:
            msg = "章番号は1以上である必要があります"
            raise ValueError(msg)
        if not self.method:
            msg = "回収方法は必須です"
            raise ValueError(msg)
        if not self.impact:
            msg = "期待される影響は必須です"
            raise ValueError(msg)


@dataclass(frozen=True)
class Hint:
    """伏線のヒント情報"""

    episode: str
    content: str
    subtlety: SubtletyLevel

    def __post_init__(self) -> None:
        if not self.episode:
            msg = "ヒントのエピソードは必須です"
            raise ValueError(msg)
        if not self.content:
            msg = "ヒント内容は必須です"
            raise ValueError(msg)


@dataclass(frozen=True)
class ReaderReaction:
    """読者反応予測"""

    on_planting: str
    on_hints: str
    on_resolution: str

    def __post_init__(self) -> None:
        if not all([self.on_planting, self.on_hints, self.on_resolution]):
            msg = "すべての読者反応予測は必須です"
            raise ValueError(msg)


@dataclass(frozen=True)
class Foreshadowing:
    """伏線エンティティ(値オブジェクトとして扱う)"""

    id: ForeshadowingId
    title: str
    category: ForeshadowingCategory
    description: str
    importance: int  # 1-5
    planting: PlantingInfo
    resolution: ResolutionInfo
    status: ForeshadowingStatus
    related_scene_ids: dict | None = None  # {"planting": "scene_id", "resolution": "scene_id"}
    hints: list[Hint] | None = None
    notes: str | None = None
    expected_reader_reaction: ReaderReaction | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title:
            msg = "伏線タイトルは必須です"
            raise ValueError(msg)
        if not self.description:
            msg = "伏線の説明は必須です"
            raise ValueError(msg)
        if not 1 <= self.importance <= 5:
            msg = "重要度は1-5の範囲である必要があります"
            raise ValueError(msg)

    def get_planting_to_resolution_distance(self) -> int:
        """仕込みから回収までの話数間隔を計算"""
        planting_num = self._extract_episode_number(self.planting.episode)
        resolution_num = self._extract_episode_number(self.resolution.episode)
        return resolution_num - planting_num

    def _extract_episode_number(self, episode_str: str) -> int:
        """エピソード文字列から話数を抽出"""
        # "第001話" -> 1

        match = re.search(r"第(\d+)話", episode_str)
        if match:
            return int(match.group(1))
        msg = f"エピソード番号を抽出できません: {episode_str}"
        raise ValueError(msg)

    def is_long_term(self) -> bool:
        """長期的な伏線かどうか(10話以上離れている)"""
        return self.get_planting_to_resolution_distance() >= 10

    def is_critical(self) -> bool:
        """重要な伏線かどうか"""
        return self.importance >= 4 and self.category in [ForeshadowingCategory.MAIN, ForeshadowingCategory.MYSTERY]

    def can_be_resolved(self) -> bool:
        """回収可能な状態かどうか"""
        return self.status in [ForeshadowingStatus.PLANTED, ForeshadowingStatus.READY_TO_RESOLVE]

    def get_hint_episodes(self) -> list[str]:
        """ヒントが配置されているエピソードのリストを取得"""
        if not self.hints:
            return []
        return [hint.episode for hint in self.hints]

    def to_summary(self) -> str:
        """サマリー文字列を生成"""
        status_emoji = {
            ForeshadowingStatus.PLANNED: "📝",
            ForeshadowingStatus.PLANTED: "🌱",
            ForeshadowingStatus.READY_TO_RESOLVE: "⏰",
            ForeshadowingStatus.RESOLVED: "✅",
        }

        return (
            f"{self.id}: {self.title} "
            f"[{self.category.value}] "
            f"{'⭐' * self.importance} "
            f"{status_emoji.get(self.status, '❓')}"
        )


@dataclass(frozen=True)
class ForeshadowingRelationship:
    """伏線間の関係性"""

    from_id: ForeshadowingId
    to_id: ForeshadowingId
    relationship_type: str  # prerequisite/parallel/contradictory
    description: str

    def __post_init__(self) -> None:
        if self.from_id.value == self.to_id.value:
            msg = "同じ伏線同士の関係は定義できません"
            raise ValueError(msg)
        if self.relationship_type not in ["prerequisite", "parallel", "contradictory"]:
            msg = "関係タイプが不正です"
            raise ValueError(msg)
