"""章番号値オブジェクト

SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

from dataclasses import dataclass


class ChapterNumberError(ValueError):
    """章番号に関するエラー"""


@dataclass(frozen=True)
class ChapterNumber:
    """章番号値オブジェクト

    章番号を表現する不変の値オブジェクト。
    1以上の整数のみを受け付ける。
    """

    value: int

    def __post_init__(self) -> None:
        """初期化後の検証"""
        if not isinstance(self.value, int) or self.value < 1:
            msg = "章番号は1以上の整数である必要があります"
            raise ChapterNumberError(msg)

    def __str__(self) -> str:
        """文字列表現"""
        return f"chapter{self.value:02d}"

    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return f"ChapterNumber({self.value})"

    def __eq__(self, other: object) -> bool:
        """等価性比較"""
        if not isinstance(other, ChapterNumber):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """ハッシュ値"""
        return hash(self.value)

    def __lt__(self, other: "ChapterNumber") -> bool:
        """小なり比較"""
        if not isinstance(other, ChapterNumber):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: "ChapterNumber") -> bool:
        """小なりイコール比較"""
        if not isinstance(other, ChapterNumber):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: "ChapterNumber") -> bool:
        """大なり比較"""
        if not isinstance(other, ChapterNumber):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: "ChapterNumber") -> bool:
        """大なりイコール比較"""
        if not isinstance(other, ChapterNumber):
            return NotImplemented
        return self.value >= other.value

    @classmethod
    def from_episode_number(cls, episode_number: int, episodes_per_chapter: int = 10) -> "ChapterNumber":
        """エピソード番号から章番号を計算

        Args:
            episode_number: エピソード番号(1以上)
            episodes_per_chapter: 1章あたりのエピソード数(デフォルト: 10)

        Returns:
            ChapterNumber: 計算された章番号

        Raises:
            ChapterNumberError: エピソード番号が無効な場合
        """
        if not isinstance(episode_number, int) or episode_number < 1:
            msg = "エピソード番号は1以上の整数である必要があります"
            raise ChapterNumberError(msg)

        if not isinstance(episodes_per_chapter, int) or episodes_per_chapter < 1:
            msg = "1章あたりのエピソード数は1以上の整数である必要があります"
            raise ChapterNumberError(msg)

        # エピソード番号から章番号を計算(切り上げ)
        chapter_value = ((episode_number - 1) // episodes_per_chapter) + 1
        return cls(chapter_value)
