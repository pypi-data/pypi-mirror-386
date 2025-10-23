#!/usr/bin/env python3
"""ヘキサゴナルアーキテクチャ対応DIコンテナ

SPEC-901-DDD-REFACTORING: Port & Adapter分離実装
Golden Sampleに基づく依存性注入コンテナの拡張

既存のDIコンテナを拡張し、新しいPort & Adapter構造を完全サポート。
"""

from pathlib import Path
from typing import Any

from noveler.infrastructure.factories.di_container import DIContainer, DIContainerError


class HexagonalDIContainer(DIContainer):
    """ヘキサゴナルアーキテクチャ対応DIコンテナ

    Port & Adapterパターンを完全サポートする拡張DIコンテナ。
    Golden Sampleのパターンに従い、実装交換とテスタビリティを提供。
    """

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self._hexagonal_initialized = False
        self._adapter_mode = "production"  # production, test, custom
        # console属性を初期化（親クラスの初期化不備を補完）
        self._console = None
        try:
            from noveler.presentation.shared.shared_utilities import get_console
            self._console = get_console()
        except ImportError:
            # フォールバック: printを使用
            class SimplePrinter:
                def info(self, msg) -> None: pass
                def error(self, msg) -> None: pass
            self._console = SimplePrinter()

    def set_adapter_mode(self, mode: str) -> None:
        """アダプター実装モードを設定

        Args:
            mode: production (本番), test (テスト), custom (カスタム)
        """
        if mode not in ["production", "test", "custom"]:
            msg = f"未対応のアダプターモード: {mode}"
            raise DIContainerError(msg)
        self._adapter_mode = mode

        # 既存のアダプター登録をクリア（モード変更時）
        self._clear_adapter_registrations()

    def initialize_hexagonal_services(self, project_root: Path | None = None) -> None:
        """ヘキサゴナルアーキテクチャサービス初期化

        Args:
            project_root: プロジェクトルートパス
        """
        if self._hexagonal_initialized:
            return

        try:
            # テストモードの場合は基本サービスをスキップ（依存関係の問題を回避）
            if self._adapter_mode != "test" and not self._initialized:
                try:
                    self.initialize_core_services(project_root)
                except (ImportError, AttributeError):
                    # 基本サービスの初期化が失敗してもヘキサゴナルサービスは継続
                    pass

            # ポートインターフェースを登録
            self._register_ports()

            # アダプターモードに基づいてアダプター実装を登録
            self._register_adapters(project_root)

            # ファクトリーを登録
            self._register_factories(project_root)

            self._hexagonal_initialized = True

        except ImportError as e:
            msg = f"ヘキサゴナルサービス初期化失敗: {e}"
            raise DIContainerError(msg) from e

    def _register_ports(self) -> None:
        """ポートインターフェースを登録"""
        # EpisodeRepositoryPort (抽象インターフェース)
        # 実際の登録はアダプターで行うため、ここでは型チェックのみ

    def _register_adapters(self, project_root: Path | None = None) -> None:
        """アダプターモードに基づいてアダプター実装を登録

        Args:
            project_root: プロジェクトルートパス
        """
        if self._adapter_mode == "production":
            self._register_production_adapters(project_root)
        elif self._adapter_mode == "test":
            self._register_test_adapters()
        elif self._adapter_mode == "custom":
            # カスタムモードでは外部から登録されるため何もしない
            pass

    def _register_production_adapters(self, project_root: Path | None = None) -> None:
        """本番用アダプターを登録

        Args:
            project_root: プロジェクトルートパス
        """
        # EpisodeRepositoryPort -> FileEpisodeRepositoryAdapter
        from noveler.infrastructure.adapters.repositories.file_episode_repository import FileEpisodeRepositoryAdapter
        from noveler.infrastructure.ports.repositories.episode_repository import (
            AdvancedEpisodeRepositoryPort,
            EpisodeRepositoryPort,
        )

        def create_file_episode_repository():
            if not project_root:
                msg = "project_rootが設定されていません"
                raise DIContainerError(msg)
            return FileEpisodeRepositoryAdapter(project_root=project_root)

        self.register_singleton(EpisodeRepositoryPort, create_file_episode_repository)
        self.register_singleton(AdvancedEpisodeRepositoryPort, create_file_episode_repository)

    def _register_test_adapters(self) -> None:
        """テスト用アダプターを登録"""
        # EpisodeRepositoryPort -> MemoryEpisodeRepositoryAdapter
        from noveler.infrastructure.adapters.repositories.memory_episode_repository import (
            MemoryEpisodeRepositoryAdapter,
        )
        from noveler.infrastructure.ports.repositories.episode_repository import (
            AdvancedEpisodeRepositoryPort,
            EpisodeRepositoryPort,
        )

        def create_memory_episode_repository():
            return MemoryEpisodeRepositoryAdapter()

        self.register_singleton(EpisodeRepositoryPort, create_memory_episode_repository)
        self.register_singleton(AdvancedEpisodeRepositoryPort, create_memory_episode_repository)

    def _register_factories(self, project_root: Path | None = None) -> None:
        """ファクトリーパターンを登録

        Args:
            project_root: プロジェクトルートパス
        """
        from noveler.infrastructure.factories.repository_factory import (
            RepositoryFactory,
            create_production_repository_factory,
            create_test_repository_factory,
        )

        def create_repository_factory():
            if self._adapter_mode == "production":
                if not project_root:
                    msg = "project_rootが設定されていません"
                    raise DIContainerError(msg)
                return create_production_repository_factory(project_root)
            if self._adapter_mode == "test":
                return create_test_repository_factory()
            msg = f"未対応のファクトリーモード: {self._adapter_mode}"
            raise DIContainerError(msg)

        self.register_singleton(RepositoryFactory, create_repository_factory)

    def _clear_adapter_registrations(self) -> None:
        """アダプター関連の登録をクリア"""
        # 特定のタイプのサービス登録をクリア
        from noveler.infrastructure.factories.repository_factory import RepositoryFactory
        from noveler.infrastructure.ports.repositories.episode_repository import (
            AdvancedEpisodeRepositoryPort,
            EpisodeRepositoryPort,
        )

        adapter_types = [
            EpisodeRepositoryPort,
            AdvancedEpisodeRepositoryPort,
            RepositoryFactory,
        ]

        for adapter_type in adapter_types:
            if adapter_type in self._services:
                del self._services[adapter_type]
            if adapter_type in self._singletons:
                del self._singletons[adapter_type]

    def switch_to_test_mode(self) -> None:
        """テストモードに切り替え（テストヘルパー）"""
        self.set_adapter_mode("test")
        self._hexagonal_initialized = False
        self.initialize_hexagonal_services()

    def switch_to_production_mode(self, project_root: Path) -> None:
        """本番モードに切り替え（テストヘルパー）

        Args:
            project_root: プロジェクトルートパス
        """
        self.set_adapter_mode("production")
        self._hexagonal_initialized = False
        self.initialize_hexagonal_services(project_root)

    def register_custom_adapter(self, interface_type: type, implementation: Any) -> None:
        """カスタムアダプターを登録

        Args:
            interface_type: インターフェース型
            implementation: 実装インスタンス
        """
        self.register_singleton(interface_type, lambda: implementation)

    def get_repository_factory(self) -> Any:
        """リポジトリファクトリーを取得（ヘルパーメソッド）

        Returns:
            RepositoryFactory: リポジトリファクトリー
        """
        from noveler.infrastructure.factories.repository_factory import RepositoryFactory
        return self.resolve(RepositoryFactory)

    def get_episode_repository(self) -> Any:
        """エピソードリポジトリを取得（ヘルパーメソッド）

        Returns:
            EpisodeRepositoryPort: エピソードリポジトリ
        """
        from noveler.infrastructure.ports.repositories.episode_repository import EpisodeRepositoryPort
        return self.resolve(EpisodeRepositoryPort)

    def get_advanced_episode_repository(self) -> Any:
        """高度なエピソードリポジトリを取得（ヘルパーメソッド）

        Returns:
            AdvancedEpisodeRepositoryPort: 高度なエピソードリポジトリ
        """
        from noveler.infrastructure.ports.repositories.episode_repository import AdvancedEpisodeRepositoryPort
        return self.resolve(AdvancedEpisodeRepositoryPort)

    def clear_hexagonal_services(self) -> None:
        """ヘキサゴナルサービスをクリア"""
        self._clear_adapter_registrations()
        self._hexagonal_initialized = False

    def get_hexagonal_registration_info(self) -> dict[str, Any]:
        """ヘキサゴナルサービス登録情報取得（デバッグ用）

        Returns:
            dict: 登録情報
        """
        base_info = self.get_registration_info()

        return {
            "adapter_mode": self._adapter_mode,
            "hexagonal_initialized": self._hexagonal_initialized,
            "registered_services": base_info,
        }



# グローバルヘキサゴナルDIコンテナ
_global_hexagonal_container: HexagonalDIContainer | None = None


def get_hexagonal_di_container() -> HexagonalDIContainer:
    """グローバルヘキサゴナルDIコンテナ取得

    Returns:
        HexagonalDIContainer: ヘキサゴナルDIコンテナ
    """
    global _global_hexagonal_container
    if _global_hexagonal_container is None:
        _global_hexagonal_container = HexagonalDIContainer()
    return _global_hexagonal_container


def initialize_hexagonal_container(
    project_root: Path | None = None,
    adapter_mode: str = "production"
) -> HexagonalDIContainer:
    """ヘキサゴナルDIコンテナ初期化

    Args:
        project_root: プロジェクトルートパス
        adapter_mode: アダプターモード (production, test, custom)

    Returns:
        HexagonalDIContainer: 初期化済みコンテナ
    """
    container = get_hexagonal_di_container()
    container.set_adapter_mode(adapter_mode)
    container.initialize_hexagonal_services(project_root)
    return container


def create_test_hexagonal_container() -> HexagonalDIContainer:
    """テスト用ヘキサゴナルDIコンテナ作成

    Returns:
        HexagonalDIContainer: テスト用コンテナ
    """
    container = HexagonalDIContainer()
    container.set_adapter_mode("test")
    container.initialize_hexagonal_services()
    return container


def create_production_hexagonal_container(project_root: Path) -> HexagonalDIContainer:
    """本番用ヘキサゴナルDIコンテナ作成

    Args:
        project_root: プロジェクトルートパス

    Returns:
        HexagonalDIContainer: 本番用コンテナ
    """
    container = HexagonalDIContainer()
    container.set_adapter_mode("production")
    container.initialize_hexagonal_services(project_root)
    return container


# 既存コンテナとの互換性ヘルパー
def migrate_to_hexagonal_container(project_root: Path | None = None) -> None:
    """既存システムをヘキサゴナルコンテナに移行

    Args:
        project_root: プロジェクトルートパス
    """
    # グローバルコンテナをヘキサゴナル版に置き換え
    global _global_hexagonal_container
    if _global_hexagonal_container is None:
        _global_hexagonal_container = HexagonalDIContainer()
        _global_hexagonal_container.initialize_hexagonal_services(project_root)
