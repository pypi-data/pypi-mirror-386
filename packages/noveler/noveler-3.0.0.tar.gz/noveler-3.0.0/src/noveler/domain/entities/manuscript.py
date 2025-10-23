# File: src/noveler/domain/entities/manuscript.py
# Purpose: Domain entity representing a manuscript with encapsulated business logic
# Context: Prevents anemic domain model by containing validation and business rules

"""原稿エンティティ

ビジネスロジックをカプセル化し、ドメインモデル貧血症を防ぐ。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from noveler.domain.value_objects.project_time import ProjectDateTime, project_now


@dataclass(frozen=True)
class Manuscript:
    """原稿エンティティ

    Responsibility:
        原稿のビジネスルールをカプセル化し、検証ロジックを内包する

    Business Rules:
        - 原稿は最低100文字以上必要
        - エピソード番号は1以上の整数
        - セッションIDは空文字列不可
        - 生成日時は必須
    """

    episode_number: int
    content: str
    generated_at: ProjectDateTime
    session_id: str

    # ビジネスルール定数
    MIN_CONTENT_LENGTH = 100

    def __post_init__(self) -> None:
        """初期化後のバリデーション"""
        if self.episode_number < 1:
            raise ValueError(f"Episode number must be >= 1, got {self.episode_number}")

        if not self.session_id or not self.session_id.strip():
            raise ValueError("Session ID cannot be empty")

        if not isinstance(self.content, str):
            raise TypeError(f"Content must be str, got {type(self.content)}")

    @classmethod
    def create_new(
        cls,
        episode_number: int,
        content: str,
        session_id: str,
        generated_at: ProjectDateTime | None = None
    ) -> Manuscript:
        """新規原稿を作成

        Args:
            episode_number: エピソード番号
            content: 原稿内容
            session_id: セッションID
            generated_at: 生成日時（省略時は現在時刻）

        Returns:
            Manuscript: 新規作成された原稿
        """
        if generated_at is None:
            generated_at = project_now()

        return cls(
            episode_number=episode_number,
            content=content,
            generated_at=generated_at,
            session_id=session_id
        )

    def is_publishable(self) -> bool:
        """公開可能な原稿か判定

        Business Rule:
            公開可能な原稿は以下の条件を満たす:
            - 十分な長さがある
            - 空白のみではない

        Returns:
            bool: 公開可能な場合True
        """
        return self.is_sufficient_length() and self._has_meaningful_content()

    def is_sufficient_length(self) -> bool:
        """十分な長さがあるか判定

        Business Rule:
            原稿は最低MIN_CONTENT_LENGTH文字以上必要

        Returns:
            bool: 十分な長さがある場合True
        """
        return len(self.content.strip()) >= self.MIN_CONTENT_LENGTH

    def _has_meaningful_content(self) -> bool:
        """意味のある内容を持つか判定

        Returns:
            bool: 空白のみでない場合True
        """
        return self.content.strip() != ""

    def get_character_count(self) -> int:
        """文字数を取得

        Returns:
            int: 原稿の文字数
        """
        return len(self.content)

    def get_stripped_character_count(self) -> int:
        """空白を除いた文字数を取得

        Returns:
            int: 空白を除いた文字数
        """
        return len(self.content.strip())

    def to_metadata_dict(self) -> dict[str, Any]:
        """メタデータ辞書に変換（Repository保存用）

        Returns:
            dict[str, Any]: メタデータ辞書
        """
        return {
            "episode_number": self.episode_number,
            "generated_at": self.generated_at.to_iso_string(),
            "session_id": self.session_id,
            "character_count": self.get_character_count(),
        }

    def get_filename(self) -> str:
        """ファイル名を取得

        Returns:
            str: ファイル名（拡張子なし）
        """
        return str(self.episode_number)

    def __repr__(self) -> str:
        """開発用の文字列表現"""
        return (
            f"Manuscript(episode={self.episode_number}, "
            f"chars={self.get_character_count()}, "
            f"session={self.session_id})"
        )
