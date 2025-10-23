"""話数を表す値オブジェクト"""

from dataclasses import dataclass
from typing import Optional

from noveler.domain.exceptions import DomainException


@dataclass(frozen=True)
class EpisodeNumber:
    """話数を表す値オブジェクト

    不変条件:
    - 話数は1以上9999以下の整数である
    - 話数は連続性を保つ(next/previousメソッドも制約を守る)
    """

    value: int

    # 話数の制限(多くの小説プラットフォームの上限)
    MIN_EPISODE = 1
    MAX_EPISODE = 9999

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if self.value < self.MIN_EPISODE:
            msg = f"話数は{self.MIN_EPISODE}以上である必要があります"
            raise DomainException(msg)
        if self.value > self.MAX_EPISODE:
            msg = f"話数は{self.MAX_EPISODE}以下である必要があります"
            raise DomainException(msg)

    def __str__(self) -> str:
        return self.format()

    def format(self) -> str:
        """話数を標準形式でフォーマット"""
        if self.value < 1000:
            return f"第{self.value:03d}話"
        return f"第{self.value}話"

    def next(self) -> "EpisodeNumber":
        """次の話数を生成"""
        if self.value >= self.MAX_EPISODE:
            msg = f"話数は{self.MAX_EPISODE}以下である必要があります"
            raise DomainException(msg)
        return EpisodeNumber(self.value + 1)

    def previous(self) -> Optional["EpisodeNumber"]:
        """前の話数を生成(存在する場合)"""
        if self.value > self.MIN_EPISODE:
            return EpisodeNumber(self.value - 1)
        return None

    # 比較演算子の実装
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, EpisodeNumber):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, EpisodeNumber):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, EpisodeNumber):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, EpisodeNumber):
            return NotImplemented
        return self.value >= other.value
