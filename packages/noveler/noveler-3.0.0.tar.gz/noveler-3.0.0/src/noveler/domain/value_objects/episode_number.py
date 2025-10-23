#!/usr/bin/env python3
"""エピソード番号値オブジェクト

DDD原則に基づく不変の値オブジェクト
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EpisodeNumber:
    """エピソード番号を表す値オブジェクト"""

    value: int

    def __post_init__(self) -> None:
        """バリデーション"""
        if not isinstance(self.value, int):
            msg = "エピソード番号は整数である必要があります"
            raise ValueError(msg)

        if self.value < 1:
            msg = f"エピソード番号は1以上である必要があります: {self.value}"
            raise ValueError(msg)

        if self.value > 9999:
            msg = f"エピソード番号は9999以下である必要があります: {self.value}"
            raise ValueError(msg)

    def __str__(self) -> str:
        """文字列表現"""
        return f"第{self.value:03d}話"

    def __lt__(self, other: object) -> bool:
        """比較演算子(小なり)"""
        if not isinstance(other, EpisodeNumber):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        """比較演算子(小なりイコール)"""
        if not isinstance(other, EpisodeNumber):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        """比較演算子(大なり)"""
        if not isinstance(other, EpisodeNumber):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        """比較演算子(大なりイコール)"""
        if not isinstance(other, EpisodeNumber):
            return NotImplemented
        return self.value >= other.value

    def next(self) -> "EpisodeNumber":
        """次のエピソード番号を取得"""
        if self.value >= 9999:
            msg = "エピソード番号は9999以下である必要があります"
            raise ValueError(msg)
        return EpisodeNumber(self.value + 1)

    def previous(self) -> "EpisodeNumber":
        """前のエピソード番号を取得"""
        if self.value <= 1:
            msg = "最初のエピソードに前のエピソードはありません"
            raise ValueError(msg)
        return EpisodeNumber(self.value - 1)
