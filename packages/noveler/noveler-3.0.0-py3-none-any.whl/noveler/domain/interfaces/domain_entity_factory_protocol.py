#!/usr/bin/env python3
"""ドメインエンティティファクトリプロトコル

DomainEntityFactoryServiceの循環依存解決
Protocol基盤によるDomainエンティティ生成の抽象化インターフェース
"""

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from noveler.domain.entities.episode import Episode
from noveler.domain.entities.episode_metadata import EpisodeMetadata
from noveler.domain.entities.episode_publisher import EpisodePublisher
from noveler.domain.entities.episode_quality import EpisodeQuality


@runtime_checkable
class DomainEntityFactoryProtocol(Protocol):
    """ドメインエンティティファクトリの抽象インターフェース"""

    @abstractmethod
    def create_episode_publisher(self, episode_id: str) -> EpisodePublisher:
        """EpisodePublisher作成

        Args:
            episode_id: エピソードID

        Returns:
            EpisodePublisher作成インスタンス
        """
        ...

    @abstractmethod
    def create_episode_quality(self, episode_id: str) -> EpisodeQuality:
        """EpisodeQuality作成

        Args:
            episode_id: エピソードID

        Returns:
            EpisodeQuality作成インスタンス
        """
        ...

    @abstractmethod
    def create_episode_metadata(self, episode_id: str) -> EpisodeMetadata:
        """EpisodeMetadata作成

        Args:
            episode_id: エピソードID

        Returns:
            EpisodeMetadata作成インスタンス
        """
        ...

    @abstractmethod
    def create_episode(self, number: int, title: str, target_words: int = 3000) -> Episode:
        """Episode作成（Factory Method）

        Args:
            number: エピソード番号
            title: タイトル
            target_words: 目標文字数

        Returns:
            Episode作成されたエピソード
        """
        ...


class LazyDomainEntityFactoryProxy:
    """遅延ロード対応のドメインエンティティファクトリプロキシ

    循環依存を回避しつつ、実際のDomainEntityFactoryServiceの生成を遅延実行
    """

    def __init__(self) -> None:
        self._cached_factory: DomainEntityFactoryProtocol | None = None

    @property
    def factory(self) -> DomainEntityFactoryProtocol:
        """遅延ロードされるドメインエンティティファクトリ"""
        if self._cached_factory is None:
            # 初回アクセス時のみインポート・インスタンス化
            from noveler.application.services.domain_entity_factory_impl import (  # noqa: PLC0415
                DomainEntityFactoryServiceImpl,
            )

            self._cached_factory = DomainEntityFactoryServiceImpl()
        return self._cached_factory

    def create_episode_publisher(self, episode_id: str) -> EpisodePublisher:
        """EpisodePublisher作成（遅延ロード）

        Args:
            episode_id: エピソードID

        Returns:
            EpisodePublisher作成インスタンス
        """
        return self.factory.create_episode_publisher(episode_id)

    def create_episode_quality(self, episode_id: str) -> EpisodeQuality:
        """EpisodeQuality作成（遅延ロード）

        Args:
            episode_id: エピソードID

        Returns:
            EpisodeQuality作成インスタンス
        """
        return self.factory.create_episode_quality(episode_id)

    def create_episode_metadata(self, episode_id: str) -> EpisodeMetadata:
        """EpisodeMetadata作成（遅延ロード）

        Args:
            episode_id: エピソードID

        Returns:
            EpisodeMetadata作成インスタンス
        """
        return self.factory.create_episode_metadata(episode_id)

    def create_episode(self, number: int, title: str, target_words: int = 3000) -> Episode:
        """Episode作成（遅延ロード）

        Args:
            number: エピソード番号
            title: タイトル
            target_words: 目標文字数

        Returns:
            Episode作成されたエピソード
        """
        return self.factory.create_episode(number, title, target_words)


# グローバル遅延プロキシインスタンス（シングルトン）
_domain_entity_factory_proxy = LazyDomainEntityFactoryProxy()


def get_domain_entity_factory_manager() -> LazyDomainEntityFactoryProxy:
    """ドメインエンティティファクトリプロキシ取得（DI対応）"""
    return _domain_entity_factory_proxy
