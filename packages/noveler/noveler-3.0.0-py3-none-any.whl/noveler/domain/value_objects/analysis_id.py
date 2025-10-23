"""分析ID値オブジェクト

分析セッションを一意に識別するID。
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisId:
    """分析ID値オブジェクト

    各種分析セッションを一意に識別するためのID。
    """

    value: str

    def __init__(self, value: str | None) -> None:
        """分析IDを初期化

        Args:
            value: ID値(省略時は自動生成)
        """
        if value is None:
            generated_value = str(uuid.uuid4())
        else:
            if not value or not isinstance(value, str):
                msg = "分析IDは空でない文字列である必要があります"
                raise TypeError(msg)
            generated_value = value

        # frozen=Trueのdataclassなので、object.__setattr__を使用
        object.__setattr__(self, "value", generated_value)

    def __str__(self) -> str:
        """文字列表現"""
        return self.value

    def __repr__(self) -> str:
        """開発者向け表現"""
        return f"AnalysisId('{self.value}')"

    @classmethod
    def from_string(cls, value: str) -> "AnalysisId":
        """文字列からAnalysisIdを作成

        Args:
            value: ID文字列

        Returns:
            AnalysisId
        """
        return cls(value=value)
