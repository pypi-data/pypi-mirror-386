#!/usr/bin/env python3
"""Domain層テスト用共通フィクスチャ

ドメインロジックテストで使用する共通フィクスチャ群
"""

from typing import Any

import pytest

from noveler.domain.entities.episode import Episode
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.word_count import WordCount


@pytest.fixture
def episode_builder() -> Any:
    """エピソードビルダーパターン"""

    class EpisodeBuilder:
        def __init__(self) -> None:
            self._number = 1
            self._title = "デフォルトタイトル"
            self._word_count = 3000
            self._content = "デフォルト内容"

        def with_number(self, number: int) -> Any:
            self._number = number
            return self

        def with_title(self, title: str) -> Any:
            self._title = title
            return self

        def with_word_count(self, word_count: int) -> int:
            self._word_count = word_count
            return self

        def with_content(self, content: str) -> Any:
            self._content = content
            return self

        def build(self) -> Episode:
            return Episode(
                number=EpisodeNumber(self._number),
                title=EpisodeTitle(self._title),
                target_words=WordCount(self._word_count),
                content=self._content,
            )

    return EpisodeBuilder()


@pytest.fixture
def valid_episode() -> Episode:
    """有効なエピソードエンティティ"""
    return Episode(
        number=EpisodeNumber(1),
        title=EpisodeTitle("テストエピソード"),
        target_words=WordCount(3000),
        content="これはテスト用のエピソード内容です。",
    )


@pytest.fixture
def sample_episode_data() -> dict:
    """テスト用エピソードデータ"""
    return {
        "episode_number": 1,
        "title": "テストエピソード",
        "word_count": 3000,
        "status": "draft",
        "content": "テスト内容",
    }
