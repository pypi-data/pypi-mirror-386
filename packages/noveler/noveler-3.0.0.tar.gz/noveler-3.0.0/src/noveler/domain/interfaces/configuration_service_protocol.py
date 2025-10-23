#!/usr/bin/env python3
"""設定サービスプロトコル

ConfigurationServiceFactoryの循環依存解決
Protocol基盤による設定管理の抽象化インターフェース
"""

import importlib
from abc import abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

from noveler.domain.entities.novel_configuration import NovelConfiguration


@runtime_checkable
class ConfigurationServiceProtocol(Protocol):
    """設定サービスの抽象インターフェース"""

    @abstractmethod
    async def load_configuration(self, config_path: Path | None = None) -> NovelConfiguration | None:
        """設定ファイルを読み込む

        Args:
            config_path: 設定ファイルパス（Noneの場合デフォルト使用）

        Returns:
            設定エンティティまたはNone
        """
        ...

    @abstractmethod
    def get_default_config_path(self) -> Path:
        """デフォルト設定ファイルパスを取得

        Returns:
            デフォルト設定ファイルパス
        """
        ...


@runtime_checkable
class ConfigurationServiceFactoryProtocol(Protocol):
    """設定サービスファクトリの抽象インターフェース"""

    @abstractmethod
    def create_configuration_service(self) -> ConfigurationServiceProtocol:
        """本番環境用設定サービス作成"""
        ...

    @abstractmethod
    def create_test_configuration_service(self) -> ConfigurationServiceProtocol:
        """テスト環境用設定サービス作成"""
        ...


class LazyConfigurationServiceProxy:
    """遅延ロード対応の設定サービスプロキシ

    循環依存を回避しつつ、実際のConfigurationServiceの生成を遅延実行
    """

    def __init__(self) -> None:
        self._cached_factory: ConfigurationServiceFactoryProtocol | None = None
        self._cached_service: ConfigurationServiceProtocol | None = None
        self._cached_test_service: ConfigurationServiceProtocol | None = None

    @property
    def factory(self) -> ConfigurationServiceFactoryProtocol:
        """遅延ロードされる設定サービスファクトリ"""
        if self._cached_factory is None:
            # 初回アクセス時のみインポート・インスタンス化
            # B20準拠修正: Infrastructure依存をInterface経由に変更
            mod = importlib.import_module(
                "noveler.infrastructure.factories.configuration_service_factory_impl"
            )
            self._cached_factory = mod.ConfigurationServiceFactoryImpl()
        return self._cached_factory

    def get_configuration_service(self, for_test: bool = False) -> ConfigurationServiceProtocol:
        """設定サービス取得（遅延ロード）

        Args:
            for_test: テスト用サービスを取得するか

        Returns:
            設定サービスインスタンス
        """
        if for_test:
            if self._cached_test_service is None:
                self._cached_test_service = self.factory.create_test_configuration_service()
            return self._cached_test_service
        if self._cached_service is None:
            self._cached_service = self.factory.create_configuration_service()
        return self._cached_service

    async def load_configuration(self, config_path: Path | None = None, for_test: bool = False) -> NovelConfiguration | None:
        """設定読み込み（遅延ロード）

        Args:
            config_path: 設定ファイルパス
            for_test: テスト用設定を使用するか

        Returns:
            設定エンティティまたはNone
        """
        service = self.get_configuration_service(for_test)
        return await service.load_configuration(config_path)


# グローバル遅延プロキシインスタンス（シングルトン）
_configuration_service_proxy = LazyConfigurationServiceProxy()


def get_configuration_service_manager() -> LazyConfigurationServiceProxy:
    """設定サービスプロキシ取得（DI対応）"""
    return _configuration_service_proxy
