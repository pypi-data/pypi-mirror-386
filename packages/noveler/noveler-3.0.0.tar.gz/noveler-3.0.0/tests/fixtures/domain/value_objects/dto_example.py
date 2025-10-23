"""
File: tests/fixtures/domain/value_objects/dto_example.py
Purpose: DTO examples for testing exclusion logic
Context: DTOs should be excluded from anemic domain detection
"""

from dataclasses import dataclass


@dataclass
class CreateEpisodeRequest:
    """
    リクエストDTO - Should be excluded

    DTOはビジネスロジックを持たないのが正常
    """
    episode_number: int
    title: str
    content: str


@dataclass
class EpisodeResponse:
    """
    レスポンスDTO - Should be excluded

    DTOはデータ転送用のみ
    """
    episode_number: int
    title: str
    status: str


@dataclass
class EpisodeUpdateDTO:
    """
    汎用DTO - Should be excluded

    DTO suffixで除外される
    """
    episode_number: int
    updates: dict
