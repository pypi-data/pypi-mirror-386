"""
YAML統合基盤依存性注入設定のテストケース

SPEC-YAML-001: DDD準拠YAML処理統合基盤仕様書
依存性注入設定の動作確認テスト
"""

import pytest

from noveler.infrastructure.di.container import DIContainer
from noveler.infrastructure.di.yaml_integration_config import (
    YamlIntegrationDIConfig,
    YamlIntegrationModule,
    YamlProcessorFactoryImpl,
    create_yaml_processing_service_from_container,
    setup_yaml_integration_container,
)


@pytest.mark.spec("SPEC-YAML-001")
class TestYamlIntegrationDIConfig:
    """YAML統合基盤依存性注入設定のテストケース"""

    def test_configure_yaml_integration_registers_services(self):
        """依存性注入設定が正しくサービスを登録することを検証"""
        container = DIContainer()

        YamlIntegrationDIConfig.configure_yaml_integration(container)

        # 設定値が登録されていることを確認
        assert container.has_config("yaml_integration.enabled")
        assert container.get_config("yaml_integration.enabled") is True

        # サービスファクトリーが登録されていることを確認
        assert container.has_factory("IYamlProcessor")
        assert container.has_factory("IYamlContentProcessor")
        assert container.has_factory("YamlProcessingService")
        assert container.has_factory("YamlContentOrchestrator")

    def test_configure_episode_processing_integration(self):
        """エピソード処理統合設定のテスト"""
        container = DIContainer()

        YamlIntegrationDIConfig.configure_episode_processing_integration(container)

        # エピソード処理用設定値が登録されていることを確認
        assert container.has_config("episode_processing.multiline_threshold")
        assert container.get_config("episode_processing.multiline_threshold") == 100

        assert container.has_config("episode_processing.auto_format_enabled")
        assert container.get_config("episode_processing.auto_format_enabled") is True

        # エピソード処理用サービスが登録されていることを確認
        assert container.has_factory("EpisodeYamlProcessingService")

    def test_custom_config_is_applied(self):
        """カスタム設定が正しく適用されることを検証"""
        container = DIContainer()
        custom_config = {"enabled": False, "performance_mode": "optimized", "validation_enabled": False}

        YamlIntegrationDIConfig.configure_yaml_integration(container, custom_config)

        assert container.get_config("yaml_integration.enabled") is False
        assert container.get_config("yaml_integration.performance_mode") == "optimized"
        assert container.get_config("yaml_integration.validation_enabled") is False


@pytest.mark.spec("SPEC-YAML-001")
class TestYamlProcessorFactoryImpl:
    """YAML処理ファクトリー実装のテストケース"""

    def test_factory_creates_yaml_processor(self):
        """ファクトリーがYAML処理実装を生成することを検証"""
        factory = YamlProcessorFactoryImpl()

        processor = factory.create_yaml_processor()

        from noveler.domain.interfaces.yaml_processor import IYamlProcessor

        assert isinstance(processor, IYamlProcessor)

    def test_factory_creates_content_processor(self):
        """ファクトリーがYAMLコンテンツ処理実装を生成することを検証"""
        factory = YamlProcessorFactoryImpl()

        content_processor = factory.create_content_processor()

        from noveler.domain.interfaces.yaml_processor import IYamlContentProcessor

        assert isinstance(content_processor, IYamlContentProcessor)

    def test_factory_creates_different_instances(self):
        """ファクトリーが異なるインスタンスを生成することを検証"""
        factory = YamlProcessorFactoryImpl()

        processor1 = factory.create_yaml_processor()
        processor2 = factory.create_yaml_processor()

        assert processor1 is not processor2  # 別インスタンス


@pytest.mark.spec("SPEC-YAML-001")
class TestSetupYamlIntegrationContainer:
    """YAML統合基盤コンテナセットアップのテストケース"""

    def test_setup_creates_configured_container(self):
        """セットアップが設定済みコンテナを作成することを検証"""
        container = setup_yaml_integration_container()

        # 基本設定が存在することを確認
        assert container.has_config("yaml_integration.enabled")
        assert container.has_config("episode_processing.multiline_threshold")

        # 基本サービスが登録されていることを確認
        assert container.has_factory("IYamlProcessor")
        assert container.has_factory("YamlProcessingService")
        assert container.has_factory("EpisodeYamlProcessingService")

    def test_setup_with_custom_config(self):
        """カスタム設定でのセットアップテスト"""
        custom_config = {"enabled": False, "performance_mode": "debug"}

        container = setup_yaml_integration_container(config=custom_config)

        assert container.get_config("yaml_integration.enabled") is False
        assert container.get_config("yaml_integration.performance_mode") == "debug"

    def test_setup_with_base_container(self):
        """既存コンテナを基にしたセットアップテスト"""
        base_container = DIContainer()
        base_container.register_config("existing_config", "existing_value")

        container = setup_yaml_integration_container(base_container=base_container)

        # 既存設定が保持されていることを確認
        assert container.get_config("existing_config") == "existing_value"

        # 新しい設定も追加されていることを確認
        assert container.has_config("yaml_integration.enabled")


@pytest.mark.spec("SPEC-YAML-001")
class TestContainerServiceResolution:
    """DIコンテナからのサービス解決テスト"""

    def test_create_yaml_processing_service_from_container(self):
        """コンテナからYAML処理サービスを取得できることを検証"""
        container = setup_yaml_integration_container()

        service = create_yaml_processing_service_from_container(container)

        from noveler.application.services.yaml_processing_service import YamlProcessingService

        assert isinstance(service, YamlProcessingService)

        # サービスが適切に依存性注入されていることを確認
        assert hasattr(service, "_yaml_processor")
        assert service._yaml_processor is not None

    def test_service_has_valid_dependencies(self):
        """サービスが有効な依存関係を持つことを検証"""
        container = setup_yaml_integration_container()
        service = create_yaml_processing_service_from_container(container)

        # 依存性が正しく注入されていることを確認
        from noveler.domain.interfaces.yaml_processor import IYamlProcessor

        assert isinstance(service._yaml_processor, IYamlProcessor)

        # メソッドが正しく動作することを確認
        test_content = "Test content\\nwith multiple lines"
        result = service.process_episode_content(test_content)

        assert isinstance(result, dict)
        assert "content" in result
        assert "processed_at" in result


@pytest.mark.spec("SPEC-YAML-001")
class TestYamlIntegrationModule:
    """YAML統合基盤モジュールのテストケース"""

    def test_module_initialization(self):
        """モジュール初期化のテスト"""
        module = YamlIntegrationModule()
        container = DIContainer()

        module.initialize(container)

        # 初期化後にサービスが取得できることを確認
        service = module.get_yaml_processing_service()
        from noveler.application.services.yaml_processing_service import YamlProcessingService

        assert isinstance(service, YamlProcessingService)

    def test_module_with_custom_config(self):
        """カスタム設定でのモジュール初期化テスト"""
        custom_config = {"enabled": False, "performance_mode": "optimized"}

        module = YamlIntegrationModule(custom_config)
        container = DIContainer()

        module.initialize(container)

        # カスタム設定が反映されていることを確認
        assert container.get_config("yaml_integration.enabled") is False
        assert container.get_config("yaml_integration.performance_mode") == "optimized"

    def test_module_get_services_before_initialization_raises_error(self):
        """初期化前のサービス取得がエラーを発生させることを検証"""
        module = YamlIntegrationModule()

        with pytest.raises(RuntimeError, match="YamlIntegrationModule is not initialized"):
            module.get_yaml_processing_service()

        with pytest.raises(RuntimeError, match="YamlIntegrationModule is not initialized"):
            module.get_yaml_content_orchestrator()

    def test_module_get_orchestrator(self):
        """オーケストレーター取得のテスト"""
        module = YamlIntegrationModule()
        container = DIContainer()

        module.initialize(container)

        orchestrator = module.get_yaml_content_orchestrator()
        from noveler.application.services.yaml_processing_service import YamlContentOrchestrator

        assert isinstance(orchestrator, YamlContentOrchestrator)


@pytest.mark.spec("SPEC-YAML-001")
class TestYamlIntegrationEndToEnd:
    """YAML統合基盤エンドツーエンドテスト"""

    def test_complete_integration_workflow(self):
        """完全な統合ワークフローのテスト"""
        # DIコンテナセットアップ
        container = setup_yaml_integration_container()

        # YAML処理サービス取得
        service = create_yaml_processing_service_from_container(container)

        # エピソード処理ワークフロー実行
        episode_content = """これはテストエピソードの内容です。
複数行にわたる内容で、
YAML処理の動作を確認します。

統合テストの実行です。複数段落を含めて100文字以上の本文を用意し、
要件に沿って十分な分量のテキストであることを保証します。"""

        # 処理実行
        result = service.process_episode_content(episode_content)

        # 結果検証
        assert isinstance(result, dict)
        assert "content" in result
        assert "processed_at" in result
        assert "content_length" in result
        assert "line_count" in result

        # YAML構造生成テスト
        yaml_structure = service.create_episode_yaml_structure(
            episode_number=1, title="テストエピソード", content=episode_content
        )

        assert isinstance(yaml_structure, dict)
        assert "metadata" in yaml_structure
        assert yaml_structure["metadata"]["episode_number"] == 1
        assert yaml_structure["metadata"]["title"] == "テストエピソード"

    def test_yaml_integration_performance(self):
        """YAML統合基盤のパフォーマンステスト"""
        import time

        container = setup_yaml_integration_container()
        service = create_yaml_processing_service_from_container(container)

        # 大きなコンテンツでのパフォーマンステスト
        large_content = "\\n".join([f"Line {i}: Test content for performance testing." for i in range(500)])

        start_time = time.time()
        result = service.process_episode_content(large_content)
        end_time = time.time()

        processing_time = end_time - start_time

        # パフォーマンス要件: 500行の処理が0.5秒以内
        assert processing_time < 0.5, f"Processing took {processing_time:.3f}s, should be < 0.5s"
        assert isinstance(result, dict)
        assert "content" in result
        assert result["line_count"] == 500
