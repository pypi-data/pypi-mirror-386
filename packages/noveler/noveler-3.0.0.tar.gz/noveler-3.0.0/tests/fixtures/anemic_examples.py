"""
File: tests/fixtures/anemic_examples.py
Purpose: Intentionally anemic domain models for testing detection
Context: Test cases for anemic domain detection scripts
"""

from dataclasses import dataclass


# ===== ANEMIC EXAMPLES (Should be detected) =====

@dataclass
class AnemicEpisode:
    """
    貧血症のEntity例

    問題: ビジネスロジックが一切ない
    """
    episode_number: int
    title: str
    content: str
    status: str


@dataclass
class AnemicEpisodeNumber:
    """
    貧血症のValue Object例

    問題: バリデーションがない
    """
    value: int


# ===== RICH DOMAIN EXAMPLES (Should pass) =====

@dataclass
class RichEpisode:
    """
    豊かなドメインモデルの例

    改善: ビジネスロジックをカプセル化
    """
    episode_number: int
    title: str
    content: str
    status: str

    def __post_init__(self):
        """バリデーション"""
        if not 1 <= self.episode_number <= 9999:
            raise ValueError(f"Invalid episode number: {self.episode_number}")
        if not self.title:
            raise ValueError("Title cannot be empty")

    def complete(self) -> None:
        """ビジネスロジック: 完了状態に遷移"""
        if self.status == "completed":
            raise ValueError("Episode is already completed")
        self.status = "completed"

    def is_draft(self) -> bool:
        """ビジネスロジック: 下書き状態か判定"""
        return self.status == "draft"


@dataclass
class RichEpisodeNumber:
    """
    豊かなValue Objectの例

    改善: 不変性とバリデーションを保証
    """
    value: int

    def __post_init__(self):
        """バリデーション"""
        if not 1 <= self.value <= 9999:
            raise ValueError(f"Invalid episode number: {self.value}")

    def __eq__(self, other):
        """等価性チェック"""
        if not isinstance(other, RichEpisodeNumber):
            return False
        return self.value == other.value

    def __hash__(self):
        """ハッシュ化可能"""
        return hash(self.value)


# ===== PROTOCOL/INTERFACE EXAMPLES (Should be excluded) =====

class IEpisodeRepository:
    """
    プロトコル定義（検知対象外）

    インターフェースなのでビジネスロジックがなくて当然
    """
    def save(self, episode: RichEpisode) -> None:
        raise NotImplementedError

    def find_by_number(self, episode_number: int) -> RichEpisode | None:
        raise NotImplementedError
