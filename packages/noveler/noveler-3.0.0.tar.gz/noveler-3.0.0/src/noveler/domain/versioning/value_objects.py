"""Domain.versioning.value_objects
Where: Domain value objects representing versioning attributes.
What: Define typed data for version identifiers, metadata, and policies.
Why: Ensure versioning data structures remain consistent.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""自動バージョニングの値オブジェクト"""


import re
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from noveler.domain.exceptions import DomainException, InvalidVersionError


@dataclass(frozen=True)
class ChangeSignificance:
    """変更重要度の値オブジェクト

    不変条件:
    - レベルはmajor, minor, patchのいずれか
    - 理由は空でない文字列
    """

    level: str  # "major", "minor", "patch"
    _reason: str

    VALID_LEVELS: ClassVar[set[str]] = {"major", "minor", "patch"}

    def __post_init__(self) -> None:
        """不変条件の検証"""
        normalized_level = self.level.lower()
        if normalized_level not in self.VALID_LEVELS:
            msg = "変更レベルはmajor, minor, patchのいずれかである必要があります"
            raise DomainException(msg)
        object.__setattr__(self, "level", normalized_level)

        if not isinstance(self._reason, str):
            msg = "変更理由は文字列で指定してください"
            raise DomainException(msg)

        trimmed = self._reason.strip()
        if not trimmed:
            msg = "変更理由は必須です"
            raise DomainException(msg)
        object.__setattr__(self, "_reason", trimmed)

    @property
    def reason(self) -> str:
        """正規化済みの理由を返す"""
        return self._reason

    @classmethod
    def major(cls, reason: str) -> ChangeSignificance:
        """メジャー重要度を生成"""
        return cls("major", reason)

    @classmethod
    def minor(cls, reason: str) -> ChangeSignificance:
        """マイナー重要度を生成"""
        return cls("minor", reason)

    @classmethod
    def patch(cls, reason: str) -> ChangeSignificance:
        """パッチ重要度を生成"""
        return cls("patch", reason)

    def requires_versioning(self) -> bool:
        """バージョン管理が必要かどうか"""
        # majorのみバージョン管理必須、minor/patchは軽微変更として扱う
        return self.level == "major"


# 代表的な重要度インスタンス（テスト互換のための定数）
ChangeSignificance.HIGH = ChangeSignificance.major("プロット全体の重大な変更")
ChangeSignificance.MEDIUM = ChangeSignificance.minor("章別プロットの変更")
ChangeSignificance.LOW = ChangeSignificance.patch("軽微な変更")


@dataclass(frozen=True)
class ConsistencyImpact:
    """整合性影響の値オブジェクト

    不変条件:
    - バージョンタイプはmajor, minor, patchのいずれか
    """

    version_type: str

    VALID_TYPES: ClassVar[set[str]] = {"major", "minor", "patch"}

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if self.version_type not in self.VALID_TYPES:
            msg = "バージョンタイプはmajor, minor, patchのいずれかである必要があります"
            raise DomainException(msg)

    @property
    def requires_episode_status_update(self) -> bool:
        """エピソードステータス更新が必要かどうか。

        Returns:
            bool: 常にTrueを返す
        """
        return True  # 常に必要

    @property
    def requires_foreshadowing_review(self) -> bool:
        """伏線レビューが必要かどうか。

        Returns:
            bool: majorバージョンの場合True
        """
        return self.version_type == "major"

    @property
    def requires_character_growth_review(self) -> bool:
        """キャラクター成長レビューが必要かどうか。

        Returns:
            bool: majorバージョンの場合True
        """
        return self.version_type == "major"

    @property
    def requires_important_scenes_review(self) -> bool:
        """重要シーンレビューが必要かどうか。

        Returns:
            bool: majorバージョンの場合True
        """
        return self.version_type == "major"

    @property
    def affected_management_files(self) -> list[str]:
        files = ["話数管理.yaml"]
        if self.version_type == "major":
            files.extend(
                [
                    "伏線管理.yaml",
                    "キャラ成長.yaml",
                    "重要シーン.yaml",
                ],
            )

        return files


class ForeshadowingImpact:
    """伏線影響分析の値オブジェクト"""

    def __init__(self) -> None:
        self.potentially_invalidated = []
        self.review_recommendations = []

    def add_invalidated_foreshadowing(self, foreshadow_id: str, reason: str | None = None) -> None:
        """無効化された可能性がある伏線を追加"""
        self.potentially_invalidated.append(foreshadow_id)
        if reason:
            self.review_recommendations.append(reason)
        else:
            self.review_recommendations.append(f"{foreshadow_id}: {reason if reason is not None else ''}")


@dataclass(frozen=True)
class ChapterImpact:
    """章別影響の値オブジェクト

    不変条件:
    - 章番号は1以上の整数
    """

    affected_chapter: int

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if self.affected_chapter < 1:
            msg = "章番号は1以上である必要があります"
            raise DomainException(msg)

    @property
    def chapter_name(self) -> str:
        return f"chapter{self.affected_chapter:02d}"

    @property
    def requires_episode_review(self) -> bool:
        return True

    @property
    def requires_foreshadowing_review(self) -> bool:
        return True

    @property
    def impact_scope(self) -> str:
        return "chapter_specific"


@dataclass(frozen=True)
class MultiChapterImpact:
    """複数章影響の値オブジェクト

    不変条件:
    - 少なくとも1つの章番号が必要
    - 各章番号は1以上の整数
    """

    chapter_numbers: list[int]

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if not self.chapter_numbers:
            msg = "少なくとも1つの章番号が必要です"
            raise DomainException(msg)

        for ch in self.chapter_numbers:
            if ch < 1:
                msg = "章番号は1以上である必要があります"
                raise DomainException(msg)

        # ソートされたリストを保持
        object.__setattr__(self, "chapter_numbers", sorted(self.chapter_numbers))

    @property
    def affected_chapters(self) -> list[int]:
        return self.chapter_numbers

    @property
    def chapter_impacts(self) -> list[ChapterImpact]:
        return [ChapterImpact(ch) for ch in self.chapter_numbers]

    @property
    def impact_scope(self) -> str:
        return "multi_chapter"


class ChapterForeshadowingImpact:
    """章別伏線影響の値オブジェクト"""

    def __init__(self, chapter_number: int) -> None:
        self.chapter = chapter_number
        self.affected_foreshadowing = []
        self.review_recommendation = ""

    def add_affected_foreshadowing(self, foreshadow_id: str) -> None:
        """影響を受ける伏線を追加"""
        self.affected_foreshadowing.append(foreshadow_id)
        self.review_recommendation = f"第{self.chapter}章の変更により伏線レビューが必要"


class BidirectionalForeshadowingImpact:
    """双方向伏線影響の値オブジェクト"""

    def __init__(self, affected_chapter: int) -> None:
        self.affected_chapter = affected_chapter
        self.setup_modified = []  # [(foreshadow_id, resolution_chapter)]
        self.resolution_modified = []  # [(foreshadow_id, target_chapter)]

    def add_setup_modified(self, foreshadow_id: str, resolution_chapter: int) -> None:
        """仕込み変更を追加(回収章も記録)"""
        self.setup_modified.append((foreshadow_id, resolution_chapter))

    def add_resolution_modified(self, foreshadow_id: str, target_chapter: int) -> None:
        """回収変更を追加(仕込み章も記録)"""
        self.resolution_modified.append((foreshadow_id, target_chapter))

    @property
    def has_bidirectional_impact(self) -> bool:
        """双方向の影響があるかチェック"""
        return bool(self.setup_modified or self.resolution_modified)

    @property
    def impact_summary(self) -> str:
        """影響サマリーを生成"""
        parts = []
        if self.setup_modified:
            parts.append(f"仕込み変更: {len(self.setup_modified)}件")
        if self.resolution_modified:
            parts.append(f"回収変更: {len(self.resolution_modified)}件")
        return f"第{self.affected_chapter}章 - " + ", ".join(parts)


class ChangeScope(Enum):
    """変更スコープ"""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class VersionCalculator:
    """バージョン計算器"""

    def calculate_next_version(self, current_version: str, version_type: str) -> str:
        """次のバージョンを計算"""
        major, minor, patch = self._parse_version(current_version)

        if version_type == "major":
            return f"v{major + 1}.0.0"
        if version_type == "minor":
            return f"v{major}.{minor + 1}.0"
        if version_type == "patch":
            return f"v{major}.{minor}.{patch + 1}"
        msg = f"Unknown version type: {version_type}"
        raise InvalidVersionError(msg)

    def _parse_version(self, version: str) -> tuple[int, int, int]:
        """バージョン文字列を解析"""
        pattern = r"^v(\d+)\.(\d+)\.(\d+)$"
        match = re.match(pattern, version)

        if not match:
            msg = f"Invalid version format: {version}"
            raise InvalidVersionError(msg)

        return int(match.group(1)), int(match.group(2)), int(match.group(3))
