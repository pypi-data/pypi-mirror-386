"""Claude連携セッション識別子

SPEC-CLAUDE-001に基づくClaude Code連携システムの値オブジェクト
"""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ClaudeSessionId:
    """Claude連携セッション識別子

    Claude Code連携セッションを一意に識別する値オブジェクト
    """

    value: str

    def __post_init__(self) -> None:
        """値の検証"""
        if not self.value:
            msg = "Claude session IDは空にできません"
            raise ValueError(msg)

        if not isinstance(self.value, str):
            msg = "Claude session IDは文字列である必要があります"
            raise TypeError(msg)

        # UUID形式チェック
        try:
            uuid.UUID(self.value)
        except ValueError as e:
            msg = f"無効なUUID形式です: {self.value}"
            raise ValueError(msg) from e

    @classmethod
    def generate(cls) -> "ClaudeSessionId":
        """新しいセッションID生成

        Returns:
            新しいClaudeSessionId
        """
        return cls(str(uuid.uuid4()))

    @classmethod
    def from_string(cls, session_id: str) -> "ClaudeSessionId":
        """文字列からセッションID作成

        Args:
            session_id: セッションID文字列

        Returns:
            ClaudeSessionId
        """
        return cls(session_id)

    def __str__(self) -> str:
        """文字列表現"""
        return self.value

    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return f"ClaudeSessionId('{self.value}')"
