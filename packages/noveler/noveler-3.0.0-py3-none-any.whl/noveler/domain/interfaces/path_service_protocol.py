#!/usr/bin/env python3
"""パスサービスプロトコル

PathServiceFactoryの循環依存解決
Protocol基盤によるパス管理の抽象化インターフェース
"""

import importlib
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from noveler.domain.interfaces.i_path_service import IPathService


from noveler.domain.interfaces.path_service import IPathService


@runtime_checkable
class PathServiceFactoryProtocol(Protocol):
    """パスサービスファクトリの抽象インターフェース"""

    @abstractmethod
    def create_path_service(self, project_root: Path | str | None = None) -> IPathService:
        """パスサービスインスタンス作成

        Args:
            project_root: プロジェクトルートパス（オプション）

        Returns:
            パスサービス実装インスタンス
        """
        ...

    @abstractmethod
    def create_mcp_aware_path_service(self) -> IPathService:
        """MCP環境対応パスサービス作成

        Returns:
            MCP対応パスサービス実装インスタンス
        """
        ...

    @abstractmethod
    def create_common_path_service(self, project_root: Path | str | None = None) -> IPathService:
        """共通パスサービス作成

        Args:
            project_root: プロジェクトルートパス（オプション）

        Returns:
            共通パスサービス実装インスタンス
        """
        ...

    @abstractmethod
    def is_mcp_environment(self) -> bool:
        """MCP環境判定

        Returns:
            MCP環境かどうか
        """
        ...


class LazyPathServiceProxy:
    """遅延ロード対応のパスサービスプロキシ

    循環依存を回避しつつ、実際のPathServiceFactoryの生成を遅延実行
    """

    def __init__(self) -> None:
        self._cached_factory: PathServiceFactoryProtocol | None = None
        self._cached_service: IPathService | None = None
        self._cached_mcp_service: IPathService | None = None

    @property
    def factory(self) -> PathServiceFactoryProtocol:
        """遅延ロードされるパスサービスファクトリ"""
        if self._cached_factory is None:
            # 初回アクセス時のみインポート・インスタンス化
            # B20準拠修正: Infrastructure依存をInterface経由に変更
            mod = importlib.import_module("noveler.infrastructure.factories.path_service_factory_impl")
            self._cached_factory = mod.PathServiceFactoryImpl()
        return self._cached_factory

    def create_path_service(self, project_root: Path | str | None = None) -> IPathService:
        """パスサービス作成（遅延ロード）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            パスサービスインスタンス
        """
        return self.factory.create_path_service(project_root)

    def get_path_service(self, project_root: Path | str | None = None) -> IPathService:
        """パスサービス取得（シングルトン + 遅延ロード）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            パスサービスインスタンス（キャッシュ付き）
        """
        if self._cached_service is None:
            self._cached_service = self.factory.create_path_service(project_root)
        return self._cached_service

    def create_mcp_aware_path_service(self) -> IPathService:
        """MCP対応パスサービス作成（遅延ロード）

        Returns:
            MCP対応パスサービスインスタンス
        """
        if self._cached_mcp_service is None:
            self._cached_mcp_service = self.factory.create_mcp_aware_path_service()
        return self._cached_mcp_service

    def create_common_path_service(self, project_root: Path | str | None = None) -> IPathService:
        """共通パスサービス作成（遅延ロード）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            共通パスサービスインスタンス
        """
        return self.factory.create_common_path_service(project_root)

    def is_mcp_environment(self) -> bool:
        """MCP環境判定（遅延ロード）

        Returns:
            MCP環境かどうか
        """
        return self.factory.is_mcp_environment()


# グローバル遅延プロキシインスタンス（シングルトン）
_path_service_proxy = LazyPathServiceProxy()


def get_path_service_manager() -> LazyPathServiceProxy:
    """パスサービスプロキシ取得（DI対応）"""
    return _path_service_proxy
