"""品質管理ドメインの値オブジェクト"""

from dataclasses import dataclass
from enum import Enum

from noveler.domain.exceptions import DomainException


class ErrorSeverity(Enum):
    """エラーの重要度"""

    ERROR = "error"  # 必ず修正が必要
    WARNING = "warning"  # 修正を推奨
    INFO = "info"  # 参考情報


class RuleCategory(Enum):
    """ルールカテゴリー"""

    BASIC_STYLE = "基本文体"
    COMPOSITION = "構成"
    PROPER_NOUN = "固有名詞"
    READABILITY = "読みやすさ"
    CONSISTENCY = "一貫性"


@dataclass(frozen=True)
class LineNumber:
    """行番号を表す値オブジェクト

    不変条件:
    - 行番号は1以上の整数である
    """

    value: int

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if self.value < 1:
            msg = "行番号は1以上である必要があります"
            raise DomainException(msg)

    def format(self) -> str:
        """行番号をフォーマット"""
        return f"{self.value}行目"

    def __str__(self) -> str:
        return self.format()


@dataclass(frozen=True)
class ErrorContext:
    """エラーコンテキストを表す値オブジェクト

    不変条件:
    - コンテキストテキストは空でない
    """

    text: str
    start_pos: int | None = None
    end_pos: int | None = None

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if not self.text:
            msg = "コンテキストテキストは必須です"
            raise DomainException(msg)

    def get_highlighted_text(self) -> str:
        """エラー箇所をハイライトしたテキストを返す"""
        if self.start_pos is None or self.end_pos is None:
            return self.text

        before = self.text[: self.start_pos]
        error_part = self.text[self.start_pos : self.end_pos]
        after = self.text[self.end_pos :]

        # 既にハイライト済みの場合は再適用しない
        if "【" in error_part or "】" in error_part:
            return self.text
        if (
            self.start_pos > 0
            and self.text[self.start_pos - 1] == "【"
            and self.end_pos < len(self.text)
            and self.text[self.end_pos] == "】"
        ):
            return self.text

        return f"{before}【{error_part}】{after}"


@dataclass(frozen=True)
class QualityScore:
    """品質スコアを表す値オブジェクト

    不変条件:
    - スコアは0.0から100.0の範囲内である
    """

    value: float

    MIN_SCORE = 0.0
    MAX_SCORE = 100.0

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if not self.MIN_SCORE <= self.value <= self.MAX_SCORE:
            msg = "品質スコアは0から100の範囲である必要があります"
            raise DomainException(msg)

    def format(self) -> str:
        """スコアをフォーマット"""
        return f"{self.value}点"

    def __str__(self) -> str:
        return self.format()

    # 比較演算子の実装
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, QualityScore):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, QualityScore):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, QualityScore):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, QualityScore):
            return NotImplemented
        return self.value >= other.value

    def get_grade(self) -> str:
        """スコアをグレードに変換"""
        if self.value >= 90:
            return "A"
        if self.value >= 80:
            return "B"
        if self.value >= 70:
            return "C"
        if self.value >= 60:
            return "D"
        return "F"

    def is_acceptable(self, threshold: float = 70.0) -> bool:
        """許容可能なスコアかどうか"""
        return self.value >= threshold


class AdaptationStrength(Enum):
    """適応強度"""

    WEAK = "weak"  # 弱い適応(5%調整)
    MODERATE = "moderate"  # 中程度適応(15%調整)
    STRONG = "strong"  # 強い適応(25%調整)


@dataclass(frozen=True)
class EvaluationContext:
    """評価コンテキストを表す値オブジェクト

    不変条件:
    - エピソード番号は1以上の整数
    - 章番号は1以上の整数
    - ジャンルは空でない文字列
    - 視点タイプは空でない文字列
    """

    episode_number: int
    chapter_number: int
    genre: str
    viewpoint_type: str

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if self.episode_number < 1:
            msg = "エピソード番号は1以上である必要があります"
            raise DomainException(msg)
        if self.chapter_number < 1:
            msg = "章番号は1以上である必要があります"
            raise DomainException(msg)
        if not self.genre:
            msg = "ジャンルは必須です"
            raise DomainException(msg)
        if not self.viewpoint_type:
            msg = "視点タイプは必須です"
            raise DomainException(msg)

    def is_complex_viewpoint(self) -> bool:
        """複雑な視点かどうか"""
        return "multiple" in self.viewpoint_type or "complex" in self.viewpoint_type

    def is_introspective_type(self) -> bool:
        """内省的タイプかどうか"""
        return "introspective" in self.viewpoint_type
