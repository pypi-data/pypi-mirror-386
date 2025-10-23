"""Domain.writing.value_objects.word_count
Where: Domain value object describing word count metrics.
What: Encapsulates counts and thresholds used in writing analytics.
Why: Provides consistent word count handling across services.
"""

from __future__ import annotations

"""文字数を表す値オブジェクト"""


import unicodedata
from dataclasses import dataclass

from noveler.domain.exceptions import DomainException


@dataclass(frozen=True)
class WordCount:
    """文字数を表す値オブジェクト

    不変条件:
    - 文字数は0以上1,000,000以下の整数である
    - 文字数の演算結果も制約を守る
    """

    value: int

    # 文字数の制限
    MIN_COUNT = 0
    MAX_COUNT = 1000000  # 100万文字(現実的な上限)

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if self.value < self.MIN_COUNT:
            msg = f"文字数は{self.MIN_COUNT}以上である必要があります"
            raise DomainException(msg)
        if self.value > self.MAX_COUNT:
            msg = f"文字数は{self.MAX_COUNT}以下である必要があります"
            raise DomainException(msg)

    def __str__(self) -> str:
        return self.format()

    def format(self) -> str:
        """文字数を読みやすい形式でフォーマット"""
        return f"{self.value:,}文字"

    def is_within_range(self, min_count: int, max_count: int) -> bool:
        """指定範囲内かチェック"""
        return min_count <= self.value <= max_count

    def is_optimal_for_web(self) -> bool:
        """Web小説として最適な文字数かチェック(2000-5000文字)"""
        return self.is_within_range(2000, 5000)

    def is_short_story(self) -> bool:
        """ショートショート(1000文字未満)"""
        return self.value < 1000

    def is_normal_story(self) -> bool:
        """通常話(1000-5000文字)"""
        return 1000 <= self.value <= 5000

    def is_long_story(self) -> bool:
        """長編話(5000文字超)"""
        return self.value > 5000

    def __add__(self, other: WordCount) -> WordCount:
        """文字数を加算"""
        if not isinstance(other, WordCount):
            return NotImplemented
        result_value = self.value + other.value
        if result_value > self.MAX_COUNT:
            msg = f"文字数は{self.MAX_COUNT}以下である必要があります"
            raise DomainException(msg)
        return WordCount(result_value)

    def __sub__(self, other: WordCount) -> WordCount:
        """文字数を減算"""
        if not isinstance(other, WordCount):
            return NotImplemented
        if self.value < other.value:
            msg = f"文字数は{self.MIN_COUNT}以上である必要があります"
            raise DomainException(msg)
        return WordCount(self.value - other.value)

    # 比較演算子の実装
    def __lt__(self, other: WordCount) -> bool:
        if not isinstance(other, WordCount):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: WordCount) -> bool:
        if not isinstance(other, WordCount):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: WordCount) -> bool:
        if not isinstance(other, WordCount):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: WordCount) -> bool:
        if not isinstance(other, WordCount):
            return NotImplemented
        return self.value >= other.value

    @classmethod
    def from_japanese_text(cls, text: str) -> WordCount:
        """日本語テキストから正確な文字数を計算

        Args:
            text: 分析対象の日本語テキスト

        Returns:
            WordCount: 計算された文字数

        Note:
            改行文字、全角・半角スペース、制御文字を除いた実質文字数を計算。
            結合文字は適切にカウントされます。
        """
        if not text:
            return cls(0)

        # Unicode正規化（NFC: 合成済み形式）
        normalized_text = unicodedata.normalize("NFC", text)

        # 実質文字数をカウント（制御文字・空白文字を除く）
        count = 0
        for char in normalized_text:
            category = unicodedata.category(char)
            # 制御文字(Cc)、書式文字(Cf)、空白・改行を除く
            if category not in ("Cc", "Cf") and char not in ("\n", "\r", " ", "\u3000", "\t"):
                count += 1

        return cls(count)

    @classmethod
    def from_display_length(cls, text: str) -> WordCount:
        """表示文字数として計算（空白・改行含む）

        Args:
            text: 分析対象のテキスト

        Returns:
            WordCount: 表示文字数
        """
        if not text:
            return cls(0)

        # Unicode正規化
        normalized_text = unicodedata.normalize("NFC", text)

        # 制御文字のみを除外し、空白・改行は含める
        count = 0
        for char in normalized_text:
            category = unicodedata.category(char)
            # 制御文字(Cc)、書式文字(Cf)のみを除く
            if category not in ("Cc", "Cf"):
                count += 1

        return cls(count)
