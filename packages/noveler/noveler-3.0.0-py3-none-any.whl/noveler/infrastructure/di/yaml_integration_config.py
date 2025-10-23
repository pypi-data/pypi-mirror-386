"""
YAML統合基盤 依存性注入設定

SPEC-YAML-001: DDD準拠YAML処理統合基盤仕様書準拠
依存性注入コンテナにYAML統合基盤サービスを登録する設定
"""

from typing import Any

from noveler.application.services.yaml_processing_service import YamlContentOrchestrator, YamlProcessingService
from noveler.domain.interfaces.yaml_processor import IYamlContentProcessor, IYamlProcessor, IYamlProcessorFactory
from noveler.infrastructure.adapters.yaml_processor_adapter import (
    YamlContentProcessorAdapter,
    YamlProcessorAdapter,
    YamlUtilsWrapper,
)
from noveler.infrastructure.di.container import DIContainer


class YamlIntegrationDIConfig:
    """YAML統合基盤依存性注入設定クラス

    DDD準拠のYAML処理統合基盤における依存性注入を設定する。
    ドメイン→アプリケーション→インフラの依存方向を厳守した設定を提供。
    """

    @staticmethod
    def configure_yaml_integration(container: DIContainer, config: dict[str, Any] | None = None) -> None:
        """YAML統合基盤の依存性注入設定

        Args:
            container (DIContainer): 依存性注入コンテナ
            config (Optional[Dict[str, Any]]): 追加設定
        """
        config = config or {}

        # 設定値の登録
        container.register_config("yaml_integration.enabled", config.get("enabled", True))
        container.register_config("yaml_integration.performance_mode", config.get("performance_mode", "standard"))
        container.register_config("yaml_integration.validation_enabled", config.get("validation_enabled", True))
        container.register_config("yaml_integration.backup_enabled", config.get("backup_enabled", True))

        # インフラ層アダプターの登録
        container.register_factory("IYamlProcessor", lambda: YamlProcessorAdapter())

        container.register_factory(
            "IYamlContentProcessor", lambda: YamlContentProcessorAdapter(container.resolve("IYamlProcessor"))
        )

        # アプリケーション層サービスの登録
        container.register_factory(
            "YamlProcessingService", lambda: YamlProcessingService(yaml_processor=container.resolve("IYamlProcessor"))
        )

        container.register_factory(
            "YamlContentOrchestrator",
            lambda: YamlContentOrchestrator(
                yaml_processing_service=container.resolve("YamlProcessingService"),
                content_processor=container.resolve("IYamlContentProcessor"),
            ),
        )

        # ファクトリーパターンの登録
        container.register_singleton("IYamlProcessorFactory", YamlProcessorFactoryImpl())

        # 互換性レイヤーの登録（段階的マイグレーション用）
        container.register_singleton("YamlUtilsWrapper", YamlUtilsWrapper())

    @staticmethod
    def configure_episode_processing_integration(container: DIContainer) -> None:
        """エピソード処理特化YAML統合設定

        Args:
            container (DIContainer): 依存性注入コンテナ
        """
        # エピソード処理用の特化設定
        container.register_config("episode_processing.multiline_threshold", 100)
        container.register_config("episode_processing.auto_format_enabled", True)
        container.register_config("episode_processing.quality_validation_enabled", True)

        # エピソード処理特化サービスの登録
        container.register_factory(
            "EpisodeYamlProcessingService",
            lambda: YamlProcessingService(yaml_processor=container.resolve("IYamlProcessor")),
        )


class YamlProcessorFactoryImpl(IYamlProcessorFactory):
    """YAML処理統合基盤ファクトリー実装

    DIコンテナと協調してYAML処理実装を生成する。
    """

    def create_yaml_processor(self) -> IYamlProcessor:
        """YAML処理インスタンス生成

        Returns:
            IYamlProcessor: YAML処理実装インスタンス
        """
        return YamlProcessorAdapter()

    def create_content_processor(self) -> IYamlContentProcessor:
        """YAMLコンテンツ処理インスタンス生成

        Returns:
            IYamlContentProcessor: YAMLコンテンツ処理実装インスタンス
        """
        yaml_processor = self.create_yaml_processor()
        return YamlContentProcessorAdapter(yaml_processor)


# 便利関数
def setup_yaml_integration_container(
    base_container: DIContainer | None = None, config: dict[str, Any] | None = None
) -> DIContainer:
    """YAML統合基盤設定済みDIコンテナ作成

    Args:
        base_container (Optional[DIContainer]): ベースコンテナ（既存設定の継承用）
        config (Optional[Dict[str, Any]]): YAML統合基盤設定

    Returns:
        DIContainer: 設定済み依存性注入コンテナ
    """
    container = base_container or DIContainer()

    YamlIntegrationDIConfig.configure_yaml_integration(container, config)
    YamlIntegrationDIConfig.configure_episode_processing_integration(container)

    return container


def create_yaml_processing_service_from_container(container: DIContainer) -> YamlProcessingService:
    """DIコンテナからYAML処理サービス取得

    Args:
        container (DIContainer): 依存性注入コンテナ

    Returns:
        YamlProcessingService: YAML処理サービス
    """
    return container.resolve("YamlProcessingService")


def create_episode_yaml_service_from_container(container: DIContainer) -> YamlProcessingService:
    """DIコンテナからエピソード用YAML処理サービス取得

    Args:
        container (DIContainer): 依存性注入コンテナ

    Returns:
        YamlProcessingService: エピソード用YAML処理サービス
    """
    return container.resolve("EpisodeYamlProcessingService")


# デフォルト設定
DEFAULT_YAML_INTEGRATION_CONFIG = {
    "enabled": True,
    "performance_mode": "standard",
    "validation_enabled": True,
    "backup_enabled": True,
}

# パフォーマンス最適化設定
PERFORMANCE_YAML_INTEGRATION_CONFIG = {
    "enabled": True,
    "performance_mode": "optimized",
    "validation_enabled": False,
    "backup_enabled": False,
}

# 開発環境設定
DEVELOPMENT_YAML_INTEGRATION_CONFIG = {
    "enabled": True,
    "performance_mode": "debug",
    "validation_enabled": True,
    "backup_enabled": True,
}


class YamlIntegrationModule:
    """YAML統合基盤モジュール

    アプリケーション起動時にYAML統合基盤を初期化するためのモジュール。
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """コンストラクタ

        Args:
            config (Optional[Dict[str, Any]]): 統合基盤設定
        """
        self._config = config or DEFAULT_YAML_INTEGRATION_CONFIG
        self._container: DIContainer | None = None

    def initialize(self, container: DIContainer) -> None:
        """モジュール初期化

        Args:
            container (DIContainer): 依存性注入コンテナ
        """
        YamlIntegrationDIConfig.configure_yaml_integration(container, self._config)
        YamlIntegrationDIConfig.configure_episode_processing_integration(container)
        self._container = container

    def get_yaml_processing_service(self) -> YamlProcessingService:
        """YAML処理サービス取得

        Returns:
            YamlProcessingService: YAML処理サービス

        Raises:
            RuntimeError: モジュールが未初期化の場合
        """
        if not self._container:
            msg = "YamlIntegrationModule is not initialized"
            raise RuntimeError(msg)

        return self._container.resolve("YamlProcessingService")

    def get_yaml_content_orchestrator(self) -> YamlContentOrchestrator:
        """YAMLコンテンツオーケストレーター取得

        Returns:
            YamlContentOrchestrator: YAMLコンテンツオーケストレーター

        Raises:
            RuntimeError: モジュールが未初期化の場合
        """
        if not self._container:
            msg = "YamlIntegrationModule is not initialized"
            raise RuntimeError(msg)

        return self._container.resolve("YamlContentOrchestrator")
