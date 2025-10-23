"""Domain.value_objects.time_estimation
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""時間見積もり値オブジェクト

作業時間の見積もりを管理するドメイン値オブジェクト
不変性を保ち、ビジネスルールを表現
"""


from dataclasses import dataclass

from noveler.domain.exceptions import DomainException


@dataclass(frozen=True)
class TimeEstimation:
    """時間見積もり値オブジェクト"""

    minutes: int

    def __post_init__(self) -> None:
        """値の検証"""
        if self.minutes < 0:
            msg = "時間見積もりは0分以上である必要があります"
            raise DomainException(msg)
        if self.minutes > 60 * 24:  # 24時間以上はエラー:
            msg = "時間見積もりは24時間以下である必要があります"
            raise DomainException(msg)

    @classmethod
    def from_minutes(cls, minutes: int) -> TimeEstimation:
        """分単位から時間見積もりを作成"""
        return cls(minutes=minutes)

    @classmethod
    def from_hours(cls, hours: float) -> TimeEstimation:
        """時間単位から時間見積もりを作成"""
        return cls(minutes=int(hours * 60))

    def in_minutes(self) -> int:
        """分単位で取得"""
        return self.minutes

    def in_hours(self) -> float:
        """時間単位で取得"""
        return self.minutes / 60

    def display_text(self) -> str:
        """表示用テキスト"""
        if self.minutes < 60:
            return f"{self.minutes}分"
        if self.minutes % 60 == 0:
            return f"{self.minutes // 60}時間"
        hours = self.minutes // 60
        mins = self.minutes % 60
        return f"{hours}時間{mins}分"

    def __add__(self, other: TimeEstimation) -> TimeEstimation:
        """時間見積もりの加算"""
        return TimeEstimation(self.minutes + other.minutes)

    def __mul__(self, factor: int | float) -> TimeEstimation:
        """時間見積もりの倍数"""
        return TimeEstimation(self.minutes * factor)
