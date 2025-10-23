# File: src/noveler/domain/initialization/value_objects.py
# Purpose: Provide immutable value objects backing the project initialization
#          workflow, including genre enums and configuration validation.
# Context: Consumed by initialization entities/services and downstream
#          application layers; must remain in sync with validation rules in
#          shared validators and documentation.

"""Domain.initialization.value_objects
Where: Domain value objects supporting initialization workflows.
What: Define typed data for initialization configuration and status.
Why: Keep initialization data structures consistent across services.
"""

from __future__ import annotations

"""プロジェクト初期化ドメイン - 値オブジェクト"""


import re
from dataclasses import dataclass
from enum import Enum, EnumMeta
from typing import Any, Mapping

from noveler.domain.exceptions import DomainException


class _LegacyFilteringEnumMeta(EnumMeta):
    """EnumMeta that skips legacy members during iteration/counting.

    The initialization domain keeps a handful of historical genre labels for
    backward compatibility. They should remain addressable but excluded from
    the canonical member list so spec assertions on the supported genre count
    stay accurate.
    """

    def __iter__(cls):  # type: ignore[override]
        """Iterate over non-legacy members only."""
        for member in super().__iter__():
            if not getattr(member, "is_legacy", False):
                yield member

    def __len__(cls) -> int:  # type: ignore[override]
        """Return the number of canonical (non-legacy) members."""
        return sum(1 for member in super().__iter__() if not getattr(member, "is_legacy", False))


class Genre(str, Enum, metaclass=_LegacyFilteringEnumMeta):
    """小説のジャンル。

    サポートされている小説ジャンルの列挙型。
    """

    def __new__(cls, value: str, legacy: bool = False):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.is_legacy = legacy
        return obj

    FANTASY = "fantasy"
    ROMANCE = "romance"
    MYSTERY = "mystery"
    SLICE_OF_LIFE = "slice_of_life"
    SCIENCE_FICTION = "science_fiction"
    HORROR = ("horror", True)
    LITERARY = ("literary", True)
    OTHER = ("other", True)
    SCIFI = ("science_fiction", True)


class WritingStyle(Enum):
    """執筆スタイル。

    小説の文体や雰囲気を表す列挙型。
    """

    LIGHT = "light"
    SERIOUS = "serious"
    COMEDY = "comedy"
    COMICAL = "comedy"
    DARK = "dark"


class UpdateFrequency(Enum):
    """更新頻度。

    小説の連載更新頻度を表す列挙型。
    """

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


@dataclass(init=False, frozen=True)
class InitializationConfig:
    """プロジェクト初期化設定値オブジェクト

    ビジネスルール:
    - プロジェクト名は1-50文字
    - 作者名は必須
    - ジャンル・スタイル・頻度の組み合わせ検証
    """

    genre: Genre
    writing_style: WritingStyle
    update_frequency: UpdateFrequency
    project_name: str
    author_name: str
    template_id: str | None
    additional_settings: Mapping[str, Any]

    def __init__(
        self,
        genre: Genre | None = None,
        writing_style: WritingStyle | None = None,
        update_frequency: UpdateFrequency | None = None,
        project_name: str | None = None,
        author_name: str | None = None,
        *,
        _genre: Genre | None = None,
        _project_name: str | None = None,
        _author_name: str | None = None,
        template_id: str | None = None,
        _template_id: str | None = None,
        additional_settings: dict[str, Any] | None = None,
        _additional_settings: dict[str, Any] | None = None,
    ) -> None:
        assigned_genre = genre or _genre
        if assigned_genre is None:
            msg = "genre is required"
            raise ValueError(msg)

        object.__setattr__(self, "genre", assigned_genre)
        object.__setattr__(self, "writing_style", writing_style or WritingStyle.LIGHT)
        object.__setattr__(self, "update_frequency", update_frequency or UpdateFrequency.WEEKLY)

        resolved_project_name = (project_name or _project_name or "").strip()
        resolved_author_name = (author_name or _author_name or "").strip()

        object.__setattr__(self, "project_name", resolved_project_name)
        object.__setattr__(self, "_project_name", resolved_project_name)
        object.__setattr__(self, "author_name", resolved_author_name)
        object.__setattr__(self, "template_id", template_id or _template_id)

        additional_source = additional_settings or _additional_settings or {}
        object.__setattr__(self, "additional_settings", dict(additional_source))

        self._validate_project_name()
        self._validate_author_name()

    def _validate_project_name(self) -> None:
        """プロジェクト名の検証"""
        if not self.project_name or len(self.project_name.strip()) == 0:
            msg = "プロジェクト名は1文字以上50文字以下で入力してください"
            raise DomainException(msg)

        if len(self.project_name) > 50:
            msg = "プロジェクト名は1文字以上50文字以下で入力してください"
            raise DomainException(msg)

        # 無効文字チェック
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, self.project_name):
            msg = "プロジェクト名に使用できない文字が含まれています"
            raise DomainException(msg)

    def _validate_author_name(self) -> None:
        """作者名の検証"""
        if not self.author_name or len(self.author_name.strip()) == 0:
            msg = "作者名は必須です"
            raise DomainException(msg)

    def is_valid(self) -> bool:
        """設定の有効性チェック"""
        try:
            self._validate_project_name()
            self._validate_author_name()
            return True
        except (ValueError, DomainException):
            return False

    def is_compatible_with_style(self, style: WritingStyle) -> bool:
        """スタイル互換性チェック"""
        # ダークとコメディは基本的に非互換
        if self.writing_style == WritingStyle.DARK and style == WritingStyle.COMEDY:
            return False
        return not (self.writing_style == WritingStyle.COMEDY and style == WritingStyle.DARK)

    def get_recommended_settings(self) -> dict[str, Any]:
        """ジャンル・スタイルに基づく推奨設定"""
        recommendations = {
            "target_episode_length": 3000,  # デフォルト文字数
            "chapters_per_arc": 10,
            "quality_focus_areas": ["readability", "engagement"],
        }

        # ジャンル別調整
        if self.genre == Genre.FANTASY:
            recommendations["target_episode_length"] = 4000
            recommendations["quality_focus_areas"].append("world_building")
        elif self.genre == Genre.MYSTERY:
            recommendations["quality_focus_areas"].extend(["logical_consistency", "tension"])
        elif self.genre == Genre.ROMANCE:
            recommendations["quality_focus_areas"].extend(["emotional_depth", "character_development"])

        # スタイル別調整
        if self.writing_style == WritingStyle.LIGHT:
            recommendations["target_episode_length"] = min(recommendations["target_episode_length"], 3500)
        elif self.writing_style == WritingStyle.SERIOUS:
            recommendations["target_episode_length"] = max(recommendations["target_episode_length"], 3500)

        return recommendations
