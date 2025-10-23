"""Domain.value_objects.episode_completion
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""執筆完了関連の値オブジェクト
DDD原則:不変性とビジネスルールのカプセル化
"""


from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


class GrowthType(Enum):
    """キャラクター成長タイプ"""

    REALIZATION = "realization"  # 気づき・理解
    SKILL_ACQUISITION = "skill_acquisition"  # スキル習得
    EMOTIONAL_CHANGE = "emotional_change"  # 感情変化
    RELATIONSHIP_CHANGE = "relationship_change"  # 関係性変化
    WORLDVIEW_CHANGE = "worldview_change"  # 世界観変化


class SceneType(Enum):
    """重要シーンタイプ"""

    TURNING_POINT = "turning_point"  # ターニングポイント
    EMOTIONAL_PEAK = "emotional_peak"  # 感情的高まり
    ACTION_SEQUENCE = "action_sequence"  # アクションシーケンス
    REVELATION = "revelation"  # 真実の開示
    CLIMAX = "climax"  # クライマックス
    CHARACTER_MOMENT = "character_moment"  # キャラクターの見せ場


class ForeshadowingStatus(Enum):
    """伏線ステータス"""

    PLANNED = "planned"  # 計画中
    PLANTED = "planted"  # 仕込み済み
    RESOLVED = "resolved"  # 回収済み
    ABANDONED = "abandoned"  # 放棄


@dataclass(frozen=True)
class EpisodeCompletionEvent:
    """執筆完了イベント(不変)"""

    episode_number: int
    completed_at: datetime
    quality_score: Decimal
    word_count: int
    plot_data: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.episode_number <= 0:
            msg = "Episode number must be positive"
            raise ValueError(msg)

        if not (Decimal("0") <= self.quality_score <= Decimal("100")):
            msg = "Quality score must be between 0 and 100"
            raise ValueError(msg)

        if self.word_count < 0:
            msg = "Word count must be non-negative"
            raise ValueError(msg)


@dataclass(frozen=True)
class CharacterGrowthEvent:
    """キャラクター成長イベント"""

    character_name: str
    growth_type: GrowthType
    description: str
    importance: str = "medium"  # low, medium, high
    auto_detected: bool = False

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.character_name or not self.character_name.strip():
            msg = "Character name cannot be empty"
            raise ValueError(msg)

        if self.importance not in ["low", "medium", "high"]:
            msg = "Invalid importance level"
            raise ValueError(msg)


@dataclass(frozen=True)
class ImportantScene:
    """重要シーン"""

    scene_id: str
    scene_type: SceneType
    description: str
    emotion_level: str = "medium"  # low, medium, high
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """タグをタプルに変換(不変性保証)"""
        object.__setattr__(self, "tags", tuple(self.tags))


@dataclass(frozen=True)
class CompletionStatus:
    """完成ステータス(値オブジェクト)"""

    value: str

    WRITTEN = "執筆済み"
    REVISED = "推敲済み"
    PUBLISHED = "公開済み"

    def __post_init__(self) -> None:
        """バリデーション"""
        valid_statuses = [self.WRITTEN, self.REVISED, self.PUBLISHED]
        if self.value not in valid_statuses:
            msg = f"Invalid completion status: {self.value}"
            raise ValueError(msg)

    @classmethod
    def written(cls) -> CompletionStatus:
        """執筆済みステータスを作成"""
        return cls(cls.WRITTEN)

    @classmethod
    def revised(cls) -> CompletionStatus:
        """推敲済みステータスを作成"""
        return cls(cls.REVISED)

    @classmethod
    def published(cls) -> CompletionStatus:
        """公開済みステータスを作成"""
        return cls(cls.PUBLISHED)

    def can_transition_to(self, other: CompletionStatus) -> bool:
        """指定されたステータスへの遷移が可能かチェック"""
        valid_transitions = {
            self.WRITTEN: [self.REVISED, self.PUBLISHED],
            self.REVISED: [self.PUBLISHED],
            self.PUBLISHED: [],
        }
        return other.value in valid_transitions.get(self.value, [])


@dataclass(frozen=True)
class ImplementationDiff:
    """計画と実装の差分情報"""

    planned_content: str
    actual_content: str
    major_changes: tuple[str, ...]
    minor_changes: tuple[str, ...]
    reason: str | None = None

    def __post_init__(self) -> None:
        """リストをタプルに変換(不変性保証)"""
        # major_changes、minor_changesは既にtupleとして型定義されているため、変換処理不要

    def has_differences(self) -> bool:
        """差分があるかチェック"""
        return bool(self.major_changes or self.minor_changes)

    def is_major_change(self) -> bool:
        """大きな変更があるかチェック"""
        return bool(self.major_changes)


@dataclass(frozen=True)
class QualityCheckResult:
    """品質チェック結果"""

    check_date: datetime
    overall_score: Decimal
    category_scores: dict[str, Decimal]
    issues: tuple[str, ...]
    warnings: tuple[str, ...]
    suggestions: tuple[str, ...]

    def __post_init__(self) -> None:
        """リストをタプルに変換(不変性保証)"""
        # issues、warnings、suggestionsは既にtupleとして型定義されているため、変換処理不要

    def has_issues(self) -> bool:
        """問題があるかチェック"""
        return bool(self.issues)

    def is_passing(self, threshold: float) -> bool:
        """合格基準を満たしているかチェック"""
        return self.overall_score >= threshold and not self.has_issues()


@dataclass(frozen=True)
class ForeshadowingUpdate:
    """伏線更新情報"""

    foreshadowing_id: str
    description: str
    update_type: str  # "planted", "resolved", "modified", "new"
    related_episodes: tuple[int, ...]
    effectiveness: str | None = None  # "excellent", "good", "fair", "poor"

    def __post_init__(self) -> None:
        """バリデーションとタプル変換"""
        valid_types = ["planted", "resolved", "modified", "new"]
        if self.update_type not in valid_types:
            msg = f"Invalid update type: {self.update_type}"
            raise ValueError(msg)

        # related_episodesは既にtupleとして型定義されているため、変換処理不要

        if self.effectiveness:
            valid_effectiveness = ["excellent", "good", "fair", "poor"]
            if self.effectiveness not in valid_effectiveness:
                msg = f"Invalid effectiveness: {self.effectiveness}"
                raise ValueError(msg)
