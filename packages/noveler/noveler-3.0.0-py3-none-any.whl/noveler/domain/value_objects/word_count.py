#!/usr/bin/env python3
"""文字数値オブジェクト

DDD原則に基づく不変の値オブジェクト
"""

from dataclasses import dataclass
from typing import ClassVar

# 定数定義
MAX_WORD_COUNT = 100000
MIN_WORD_COUNT_FOR_EPISODE = 1000


@dataclass(frozen=True)
class WordCount:
    """文字数を表す値オブジェクト."""

    value: int

    MAX_WORD_COUNT: ClassVar[int] = MAX_WORD_COUNT
    MIN_WORD_COUNT_FOR_EPISODE: ClassVar[int] = MIN_WORD_COUNT_FOR_EPISODE
    SHORT_STORY_THRESHOLD: ClassVar[int] = 5000
    LONG_STORY_THRESHOLD: ClassVar[int] = 50000

    def __post_init__(self) -> None:
        """バリデーション."""
        if not isinstance(self.value, int):
            error_msg = f"文字数は整数である必要があります: {type(self.value)}"
            raise TypeError(error_msg)

        if self.value < 0:
            error_msg = f"文字数は0以上である必要があります: {self.value}"
            raise ValueError(error_msg)

        if self.value > MAX_WORD_COUNT:
            error_msg = f"文字数は{MAX_WORD_COUNT}以下である必要があります: {self.value}"
            raise ValueError(error_msg)

    def __str__(self) -> str:
        """文字列表現."""
        return f"{self.value:,}文字"

    def __add__(self, other: "WordCount | int") -> "WordCount":
        """加算."""
        if isinstance(other, WordCount):
            result = self.value + other.value
        elif isinstance(other, int):
            result = self.value + other
        else:
            return NotImplemented
        return WordCount(result)

    def __sub__(self, other: "WordCount | int") -> "WordCount":
        """減算."""
        if isinstance(other, WordCount):
            result = self.value - other.value
        elif isinstance(other, int):
            result = self.value - other
        else:
            return NotImplemented
        return WordCount(max(0, result))

    def __lt__(self, other: "WordCount | int") -> bool:
        """比較演算子(小なり)."""
        if isinstance(other, WordCount):
            return self.value < other.value
        if isinstance(other, int):
            return self.value < other
        return NotImplemented

    def __le__(self, other: "WordCount | int") -> bool:
        """比較演算子(小なりイコール)."""
        if isinstance(other, WordCount):
            return self.value <= other.value
        if isinstance(other, int):
            return self.value <= other
        return NotImplemented

    def __gt__(self, other: "WordCount | int") -> bool:
        """比較演算子(大なり)."""
        if isinstance(other, WordCount):
            return self.value > other.value
        if isinstance(other, int):
            return self.value > other
        return NotImplemented

    def __ge__(self, other: "WordCount | int") -> bool:
        """比較演算子(大なりイコール)."""
        if isinstance(other, WordCount):
            return self.value >= other.value
        if isinstance(other, int):
            return self.value >= other
        return NotImplemented

    def is_short_story(self) -> bool:
        """短編かどうかを判定する."""
        return self.value < self.SHORT_STORY_THRESHOLD

    def is_normal_story(self) -> bool:
        """中編かどうかを判定する."""
        return self.SHORT_STORY_THRESHOLD <= self.value <= self.LONG_STORY_THRESHOLD

    def is_long_story(self) -> bool:
        """長編かどうかを判定する."""
        return self.value > self.LONG_STORY_THRESHOLD

    def percentage_of(self, target: "WordCount") -> float:
        """指定した文字数に対する達成率を計算する."""
        if not isinstance(target, WordCount):
            raise TypeError("target には WordCount を指定してください")
        if target.value == 0:
            return 0.0
        return round((self.value / target.value) * 100, 2)

    def calculate_percentage(self, target: "WordCount") -> float:
        """目標に対する達成率を計算."""
        if target.value == 0:
            return 100.0
        return (self.value / target.value) * 100

    def is_sufficient_for_episode(self) -> bool:
        """エピソードとして十分な文字数かチェック."""
        return self.value >= MIN_WORD_COUNT_FOR_EPISODE
