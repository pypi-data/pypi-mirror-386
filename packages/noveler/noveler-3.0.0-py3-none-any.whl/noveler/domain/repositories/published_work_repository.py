#!/usr/bin/env python3
"""書籍化作品リポジトリインターフェース

書籍化作品データの永続化インターフェース
"""

from abc import ABC, abstractmethod
from typing import Any

from noveler.domain.ai_integration.entities.published_work import PublishedWork


class PublishedWorkRepository(ABC):
    """書籍化作品リポジトリの抽象基底クラス"""

    @abstractmethod
    def find_all(self) -> list[PublishedWork]:
        """全ての書籍化作品を取得

        Returns:
            書籍化作品のリスト
        """

    @abstractmethod
    def find_by_genre(self, genre_config: dict[str, Any]) -> list[PublishedWork]:
        """ジャンルによる書籍化作品の検索

        Args:
            genre_config: ジャンル設定

        Returns:
            該当する書籍化作品のリスト
        """

    @abstractmethod
    def save_work(self, work: PublishedWork) -> None:
        """書籍化作品を保存

        Args:
            work: 保存する書籍化作品
        """

    @abstractmethod
    def get_statistics(self) -> dict[str, Any]:
        """統計情報を取得

        Returns:
            統計情報
        """
