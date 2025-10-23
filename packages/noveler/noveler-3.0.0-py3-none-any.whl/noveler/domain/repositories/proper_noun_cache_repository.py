#!/usr/bin/env python3
"""固有名詞キャッシュリポジトリインターフェース

固有名詞の永続化を抽象化する
リポジトリインターフェース(ドメイン層で定義)
"""

from abc import ABC, abstractmethod

from noveler.domain.entities.proper_noun_collection import ProperNounCollection


class ProperNounCacheRepository(ABC):
    """固有名詞キャッシュリポジトリインターフェース"""

    @abstractmethod
    def save_terms(self, collection: ProperNounCollection) -> None:
        """固有名詞コレクションを保存

        Args:
            collection: 保存する固有名詞コレクション

        Raises:
            IOError: 保存に失敗した場合
        """

    @abstractmethod
    def get_cached_terms(self) -> ProperNounCollection:
        """キャッシュされた固有名詞コレクションを取得

        Returns:
            ProperNounCollection: キャッシュされたコレクション
                                 キャッシュが存在しない場合は空のコレクション
        """

    @abstractmethod
    def clear_cache(self) -> None:
        """キャッシュをクリア

        Raises:
            IOError: クリアに失敗した場合
        """

    @abstractmethod
    def is_cache_valid(self) -> bool:
        """キャッシュが有効かどうかの判定

        Returns:
            bool: キャッシュが有効な場合True
        """

    @abstractmethod
    def get_cache_timestamp(self) -> float:
        """キャッシュのタイムスタンプを取得

        Returns:
            float: UNIXタイムスタンプ(キャッシュが存在しない場合は0)
        """
