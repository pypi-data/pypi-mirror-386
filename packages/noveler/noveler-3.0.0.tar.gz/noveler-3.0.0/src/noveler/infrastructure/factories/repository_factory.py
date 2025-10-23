"""Repository Factory for Hexagonal Architecture

SPEC-901-DDD-REFACTORING: Port & Adapter分離実装
Golden Sampleに基づくファクトリーパターン適用

このファクトリーはリポジトリのポートとアダプターを管理し、
依存性注入と設定に基づく実装の切り替えを可能にします。
"""

from pathlib import Path
from typing import Protocol, runtime_checkable

from noveler.infrastructure.ports.repositories.episode_repository import (
    AdvancedEpisodeRepositoryPort,
    EpisodeRepositoryPort,
)


class RepositoryFactoryConfig:
    """リポジトリファクトリー設定クラス"""

    def __init__(self) -> None:
        self._config = {
            "episode_repository_type": "file",  # file, database, memory
            "project_root": None,
            "database_url": None,
            "enable_caching": False,
            "enable_async": True,
        }

    def configure(self, **config_dict) -> None:
        """設定を更新"""
        self._config.update(config_dict)

    def get(self, key: str, default=None):
        """設定値を取得"""
        return self._config.get(key, default)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            return super().__getattribute__(name)
        try:
            return self._config[name]
        except KeyError:
            msg = f"'{self.__class__.__name__}' object has no attribute '{name}'"
            raise AttributeError(msg)


@runtime_checkable
class RepositoryFactory(Protocol):
    """リポジトリファクトリーインターフェース"""

    def create_episode_repository(self) -> EpisodeRepositoryPort:
        """エピソードリポジトリを作成"""
        ...

    def create_advanced_episode_repository(self) -> AdvancedEpisodeRepositoryPort:
        """高度なエピソードリポジトリを作成"""
        ...


class DefaultRepositoryFactory:
    """デフォルトリポジトリファクトリー実装

    Golden Sampleのパターンに従い、設定に基づいて
    適切なアダプター実装を選択・作成します。
    """

    def __init__(self, config: RepositoryFactoryConfig = None) -> None:
        """初期化

        Args:
            config: ファクトリー設定
        """
        self.config = config or RepositoryFactoryConfig()

    def create_episode_repository(self) -> EpisodeRepositoryPort:
        """エピソードリポジトリを作成

        設定に基づいて適切な実装を選択：
        - file: ファイルシステムベース（デフォルト）
        - database: データベースベース
        - memory: インメモリ（テスト用）

        Returns:
            EpisodeRepositoryPort: 設定された実装
        """
        repo_type = self.config.get("episode_repository_type", "file")

        if repo_type == "file":
            return self._create_file_episode_repository()
        if repo_type == "database":
            return self._create_database_episode_repository()
        if repo_type == "memory":
            return self._create_memory_episode_repository()
        msg = f"未対応のリポジトリタイプ: {repo_type}"
        raise ValueError(msg)

    def create_advanced_episode_repository(self) -> AdvancedEpisodeRepositoryPort:
        """高度なエピソードリポジトリを作成

        基本リポジトリと同じ設定を使用し、高度な機能を含む実装を作成

        Returns:
            AdvancedEpisodeRepositoryPort: 高度な機能を含む実装
        """
        # 基本的に同じアダプターを返す（AdvancedEpisodeRepositoryPortを実装済みのため）
        basic_repo = self.create_episode_repository()

        # 型安全性のチェック
        if isinstance(basic_repo, AdvancedEpisodeRepositoryPort):
            return basic_repo
        # 必要に応じてラッパーを作成（現在の実装では不要）
        msg = f"リポジトリ {type(basic_repo)} は高度な機能をサポートしていません"
        raise ValueError(msg)

    def _create_file_episode_repository(self) -> AdvancedEpisodeRepositoryPort:
        """ファイルベースエピソードリポジトリを作成"""
        from noveler.infrastructure.adapters.repositories.file_episode_repository import FileEpisodeRepositoryAdapter

        project_root = self.config.get("project_root")
        if not project_root:
            msg = "project_rootの設定が必要です"
            raise ValueError(msg)

        # パスサービスの依存性注入
        path_service = self._create_path_service()

        return FileEpisodeRepositoryAdapter(
            project_root=project_root,
            path_service=path_service
        )

    def _create_database_episode_repository(self) -> AdvancedEpisodeRepositoryPort:
        """データベースベースエピソードリポジトリを作成"""
        # 将来の実装のための枠組み
        database_url = self.config.get("database_url")
        if not database_url:
            msg = "database_urlの設定が必要です"
            raise ValueError(msg)

        # TODO: DatabaseEpisodeRepositoryAdapterの実装
        msg = "データベースリポジトリは未実装です"
        raise NotImplementedError(msg)

    def _create_memory_episode_repository(self) -> AdvancedEpisodeRepositoryPort:
        """インメモリエピソードリポジトリを作成（テスト用）"""
        from noveler.infrastructure.adapters.repositories.memory_episode_repository import (
            MemoryEpisodeRepositoryAdapter,
        )

        return MemoryEpisodeRepositoryAdapter()

    def _create_path_service(self):
        """パスサービスを作成"""
        # パスサービスファクトリーからの作成（既存実装を利用）
        try:
            from noveler.infrastructure.adapters.path_service_adapter import PathServiceAdapter

            project_root = self.config.get("project_root")
            return PathServiceAdapter(project_root)
        except ImportError:
            # フォールバック: パスサービスなし
            return None


class CachedRepositoryFactory:
    """キャッシュ機能付きリポジトリファクトリー

    リポジトリインスタンスをキャッシュし、パフォーマンスを向上させます。
    """

    def __init__(self, base_factory: RepositoryFactory) -> None:
        """初期化

        Args:
            base_factory: ベースとなるファクトリー
        """
        self.base_factory = base_factory
        self._cache = {}

    def create_episode_repository(self) -> EpisodeRepositoryPort:
        """キャッシュ機能付きエピソードリポジトリを作成"""
        if "episode_repository" not in self._cache:
            self._cache["episode_repository"] = self.base_factory.create_episode_repository()
        return self._cache["episode_repository"]

    def create_advanced_episode_repository(self) -> AdvancedEpisodeRepositoryPort:
        """キャッシュ機能付き高度なエピソードリポジトリを作成"""
        if "advanced_episode_repository" not in self._cache:
            self._cache["advanced_episode_repository"] = self.base_factory.create_advanced_episode_repository()
        return self._cache["advanced_episode_repository"]

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self._cache.clear()


# 設定ベースファクトリー作成関数

def create_production_repository_factory(project_root: str | Path) -> RepositoryFactory:
    """本番用リポジトリファクトリーを作成

    Args:
        project_root: プロジェクトルートパス

    Returns:
        RepositoryFactory: 本番用ファクトリー
    """
    config = RepositoryFactoryConfig()
    config.configure(
        episode_repository_type="file",
        project_root=project_root,
        enable_caching=True,
        enable_async=True,
    )

    base_factory = DefaultRepositoryFactory(config)
    return CachedRepositoryFactory(base_factory)


def create_test_repository_factory() -> RepositoryFactory:
    """テスト用リポジトリファクトリーを作成

    Returns:
        RepositoryFactory: テスト用ファクトリー
    """
    config = RepositoryFactoryConfig()
    config.configure(
        episode_repository_type="memory",
        enable_caching=False,
        enable_async=False,
    )

    return DefaultRepositoryFactory(config)


def create_custom_repository_factory(custom_config: RepositoryFactoryConfig) -> RepositoryFactory:
    """カスタム設定でリポジトリファクトリーを作成

    Args:
        custom_config: カスタム設定

    Returns:
        RepositoryFactory: カスタム設定ファクトリー
    """
    base_factory = DefaultRepositoryFactory(custom_config)

    if custom_config.get("enable_caching", False):
        return CachedRepositoryFactory(base_factory)
    return base_factory


# グローバルファクトリー（レガシー互換性のため）
_default_factory: RepositoryFactory | None = None


def get_default_repository_factory() -> RepositoryFactory:
    """デフォルトリポジトリファクトリーを取得

    Returns:
        RepositoryFactory: デフォルトファクトリー
    """
    global _default_factory
    if _default_factory is None:
        # 環境変数やデフォルト設定から作成
        import os
        project_root = os.getenv("NOVELER_PROJECT_ROOT", ".")
        _default_factory = create_production_repository_factory(project_root)
    return _default_factory


def set_default_repository_factory(factory: RepositoryFactory) -> None:
    """デフォルトリポジトリファクトリーを設定

    Args:
        factory: 設定するファクトリー
    """
    global _default_factory
    _default_factory = factory
