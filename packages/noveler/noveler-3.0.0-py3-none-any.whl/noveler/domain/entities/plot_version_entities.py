#!/usr/bin/env python3

"""Domain.entities.plot_version_entities
Where: Supporting domain entities for plot version operations.
What: Defines helper data structures used by plot version workflows.
Why: Keeps plot version domain concepts cohesive.
"""

from __future__ import annotations

"""プロットバージョン管理のドメインエンティティ
ビジネスルールとドメイン知識を表現
"""


import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from noveler.domain.exceptions import InvalidVersionError

if TYPE_CHECKING:
    from datetime import datetime


EPISODE_NUMBER_WIDTH = 3


@dataclass
class PlotVersion:
    """プロットバージョンエンティティ"""

    version_number: str
    created_at: datetime
    author: str
    major_changes: list[str]
    affected_chapters: list[int]
    git_tag: str | None = None
    git_commit_range: str | None = None
    previous_version: PlotVersion | None = None

    def __post_init__(self) -> None:
        """初期化後の検証"""
        if not self._is_valid_version_number(self.version_number):
            msg = f"不正なバージョン番号: {self.version_number}. v1.0.0のような形式で指定してください"
            raise InvalidVersionError(
                msg,
            )

    def _is_valid_version_number(self, version: str) -> bool:
        """セマンティックバージョニング形式の検証"""
        pattern = r"^v\d+\.\d+\.\d+$"
        return bool(re.match(pattern, version))

    def _parse_version(self, version: str) -> tuple[int, int, int]:
        """バージョン番号をパース"""
        match = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", version)
        if match:
            return int(match.group(1)), int(match.group(2)), int(match.group(3))
        return 0, 0, 0

    def is_newer_than(self, other: PlotVersion) -> bool:
        """他のバージョンより新しいか判定"""
        self_parsed = self._parse_version(self.version_number)
        other_parsed = self._parse_version(other.version_number)
        return self_parsed > other_parsed

    def is_initial_version(self) -> bool:
        """初版かどうか判定"""
        return self.previous_version is None

    def get_semantic_version_type(self) -> str:
        """バージョンアップの種類を判定(major/minor/patch)"""
        if not self.previous_version:
            return "initial"

        prev_major, prev_minor, prev_patch = self._parse_version(
            self.previous_version.version_number,
        )

        curr_major, curr_minor, curr_patch = self._parse_version(
            self.version_number,
        )

        if curr_major > prev_major:
            return "major"
        if curr_minor > prev_minor:
            return "minor"
        return "patch"


@dataclass
class ManuscriptPlotLink:
    """原稿とプロットバージョンの紐付けエンティティ"""

    episode_number: str
    plot_version: PlotVersion
    implementation_date: datetime
    git_commit: str
    plot_snapshot: dict | None = None

    def is_outdated_for(self, current_version: PlotVersion) -> bool:
        """現在のバージョンに対して古いか判定"""
        return current_version.is_newer_than(self.plot_version)

    def get_chapter_number(self) -> int:
        """エピソード番号から章番号を計算"""
        try:
            ep_num = int(self.episode_number)
            return (ep_num - 1) // 10 + 1
        except ValueError:
            return 0

    def is_affected_by_version(self, version: PlotVersion) -> bool:
        """特定バージョンの変更に影響を受けるか判定"""
        chapter = self.get_chapter_number()
        return chapter in version.affected_chapters


@dataclass
class PlotChangeSet:
    """プロットバージョン間の変更セット"""

    from_version: PlotVersion
    to_version: PlotVersion
    git_diff_files: list[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        """変更があるか判定"""
        return self.from_version.version_number != self.to_version.version_number

    def get_affected_episode_numbers(self) -> list[str]:
        """影響章から算出した3桁ゼロ埋めのエピソード番号一覧を返す.

        Returns:
            list[str]: ゼロパディングされたエピソード番号(例: "001")。

        Preconditions:
            `affected_chapters` が1始まりの章番号で保持されていること。
        """
        affected_episode_numbers: set[int] = set()

        # from_versionからto_versionまでの全ての影響章を収集
        affected_chapters = set(self.to_version.affected_chapters)

        # 章番号からエピソード番号を計算
        for chapter in sorted(affected_chapters):
            if chapter <= 0:
                continue
            start_ep = (chapter - 1) * 10 + 1
            end_ep = chapter * 10
            affected_episode_numbers.update(range(start_ep, end_ep + 1))

        # 3桁ゼロ埋めで昇順リストに整形
        return [f"{episode:0{EPISODE_NUMBER_WIDTH}d}" for episode in sorted(affected_episode_numbers)]

    def get_version_path(self) -> list[PlotVersion]:
        """バージョン間の経路を取得"""
        # 簡易実装: 直接遷移のみ
        return [self.from_version, self.to_version]
