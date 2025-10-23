#!/usr/bin/env python3
"""A31セッションID値オブジェクト

SPEC-QUALITY-001に基づくセッションIDの表現。
一意性と可読性を両立したID管理。
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from noveler.domain.value_objects.project_time import ProjectTimezone


@dataclass(frozen=True)
class SessionId:
    """セッションID値オブジェクト

    自動修正セッションの一意識別子。
    タイムスタンプと UUID を組み合わせた形式。
    """

    value: str

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self._validate_session_id()

    def _validate_session_id(self) -> None:
        """セッションIDの妥当性検証"""
        if not self.value:
            msg = "セッションIDは空であってはいけません"
            raise ValueError(msg)

        if len(self.value) < 10:
            msg = "セッションIDは10文字以上である必要があります"
            raise ValueError(msg)

    def get_timestamp_prefix(self) -> str:
        """タイムスタンプ部分の取得

        Returns:
            str: セッションIDのタイムスタンプ部分
        """
        # A31-20250728-120000-abcd1234 形式を想定
        parts = self.value.split("-")
        if len(parts) >= 3:
            return f"{parts[1]}-{parts[2]}"
        return ""

    def get_short_id(self) -> str:
        """短縮IDの取得

        Returns:
            str: 表示用の短縮ID
        """
        # 最後の8文字を使用
        return self.value[-8:] if len(self.value) >= 8 else self.value

    def is_valid_format(self) -> bool:
        """形式の有効性チェック

        Returns:
            bool: 有効な形式の場合True
        """
        # A31-YYYYMMDD-HHMMSS-xxxxxxxx 形式かチェック
        parts = self.value.split("-")
        if len(parts) != 4:
            return False

        if parts[0] != "A31":
            return False

        # 日付部分のチェック(YYYYMMDD)
        if len(parts[1]) != 8 or not parts[1].isdigit():
            return False

        # 時刻部分のチェック(HHMMSS)
        if len(parts[2]) != 6 or not parts[2].isdigit():
            return False

        # UUID部分のチェック(8文字以上の英数字)
        return not (len(parts[3]) < 8 or not parts[3].isalnum())

    def __str__(self) -> str:
        """文字列表現の取得"""
        return self.value

    def __repr__(self) -> str:
        """デバッグ用表現の取得"""
        return f"SessionId('{self.value}')"

    @classmethod
    def generate(cls) -> "SessionId":
        """新しいセッションIDの生成

        Returns:
            SessionId: 新規生成されたセッションID
        """
        jst = ProjectTimezone.jst().timezone
        now = datetime.now(jst)
        date_part = now.strftime("%Y%m%d")
        time_part = now.strftime("%H%M%S")
        uuid_part = str(uuid.uuid4()).replace("-", "")[:8]

        session_id = f"A31-{date_part}-{time_part}-{uuid_part}"
        return cls(session_id)

    @classmethod
    def from_string(cls, session_id_str: str) -> "SessionId":
        """文字列からの変換

        Args:
            session_id_str: セッションID文字列

        Returns:
            SessionId: 対応するセッションIDインスタンス
        """
        return cls(session_id_str)

    @classmethod
    def create_test_id(cls, suffix: str = "test") -> "SessionId":
        """テスト用IDの作成

        Args:
            suffix: テスト用の識別子

        Returns:
            SessionId: テスト用セッションID
        """
        session_id = f"A31-20250728-120000-{suffix:0>8}"
        return cls(session_id)
