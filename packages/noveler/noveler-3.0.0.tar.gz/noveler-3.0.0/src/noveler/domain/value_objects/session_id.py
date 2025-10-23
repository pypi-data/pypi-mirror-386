"""セッションID値オブジェクト

一意のセッション識別子を表す値オブジェクト。
"""

import uuid


class SessionId:
    """セッションID値オブジェクト

    各種チェックセッションを一意に識別するためのID。
    """

    def __init__(self, value: str | None = None) -> None:
        """セッションIDを初期化

        Args:
            value: ID値(省略時は自動生成)
        """
        if value is None:
            self._value = str(uuid.uuid4())
        else:
            if not value or not isinstance(value, str):
                msg = "SessionIDは空でない文字列である必要があります"
                raise TypeError(msg)
            self._value = value

    @property
    def value(self) -> str:
        """ID値を取得"""
        return self._value

    def __str__(self) -> str:
        """文字列表現"""
        return self._value

    def __repr__(self) -> str:
        """開発者向け表現"""
        return f"SessionId('{self._value}')"

    def __eq__(self, other: object) -> bool:
        """等価性の判定"""
        if not isinstance(other, SessionId):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """ハッシュ値の生成"""
        return hash(self._value)
