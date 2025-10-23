"""エラーメッセージドメインの値オブジェクト

不変で交換可能な値を表現
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorCode:
    """エラーコード値オブジェクト"""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            msg = "エラーコードは空にできません"
            raise ValueError(msg)
        if not self.value[0].isalpha():
            msg = "エラーコードは文字で始まる必要があります"
            raise ValueError(msg)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ErrorLocation:
    """エラー位置値オブジェクト"""

    line: int
    column: int = 0

    def __post_init__(self) -> None:
        if self.line < 1:
            msg = "行番号は1以上である必要があります"
            raise ValueError(msg)
        if self.column < 0:
            msg = "列番号は0以上である必要があります"
            raise ValueError(msg)

    def format(self) -> str:
        """位置情報をフォーマット"""
        if self.column > 0:
            return f"行{self.line}:列{self.column}"
        return f"行{self.line}"


@dataclass(frozen=True)
class ImprovementExample:
    """改善例値オブジェクト"""

    before: str
    after: str
    explanation: str

    def __post_init__(self) -> None:
        if not self.before.strip():
            msg = "改善前のテキストは空にできません"
            raise ValueError(msg)
        if not self.after.strip():
            msg = "改善後のテキストは空にできません"
            raise ValueError(msg)
        if not self.explanation.strip():
            msg = "説明は空にできません"
            raise ValueError(msg)
        if self.before == self.after:
            msg = "改善前後のテキストが同じです"
            raise ValueError(msg)

    def get_improvement_ratio(self) -> float:
        """改善による文字数変化率を取得"""
        return len(self.after) / len(self.before) if self.before else 0.0

    def is_splitting(self) -> bool:
        """文を分割しているかどうか"""
        return self.after.count("。") > self.before.count("。")
