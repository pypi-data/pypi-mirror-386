# File: tests/unit/domain/test_yaml_processor_interface.py
# Purpose: Verify YAML processing interfaces, services, and adapters across unit and integration flows.
# Context: Depends on domain interfaces, application services, and infrastructure adapters for YAML processing.

"""
YAML統合基盤インターフェースのテストケース

SPEC-YAML-001: DDD準拠YAML処理統合基盤仕様書
"""

from abc import ABC
from pathlib import Path
from unittest.mock import Mock
import time

import pytest
import yaml

from noveler.application.services.yaml_processing_service import YamlProcessingService
from noveler.domain.interfaces.yaml_processor import IYamlProcessor
from noveler.infrastructure.adapters.yaml_processor_adapter import YamlProcessorAdapter
from noveler.infrastructure.di.container import DIContainer
from noveler.infrastructure.utils.yaml_utils import YAMLMultilineString

@pytest.mark.spec("SPEC-YAML-001")
class TestIYamlProcessor:
    """IYamlProcessorインターフェースのテストケース"""

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-INTERFACE_IS_ABSTRAC")
    def test_interface_is_abstract(self):
        """インターフェースが抽象クラスであることを検証"""

        assert issubclass(IYamlProcessor, ABC)

        # 抽象クラスなので直接インスタンス化できない
        with pytest.raises(TypeError):
            IYamlProcessor()

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-INTERFACE_HAS_REQUIR")
    def test_interface_has_required_methods(self):
        """必須メソッドが定義されていることを検証"""

        # 抽象メソッドが存在することを確認
        abstract_methods = IYamlProcessor.__abstractmethods__
        expected_methods = {"create_multiline_string", "process_content_to_dict"}

        assert expected_methods.issubset(abstract_methods)

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-CREATE_MULTILINE_STR")
    def test_create_multiline_string_signature(self):
        """create_multiline_stringメソッドのシグネチャ検証"""

        # メソッドが存在することを確認
        assert hasattr(IYamlProcessor, "create_multiline_string")

        # 型注釈を確認（import time後に実装予定）
        method = IYamlProcessor.create_multiline_string
        assert callable(method)

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-PROCESS_CONTENT_TO_D")
    def test_process_content_to_dict_signature(self):
        """process_content_to_dictメソッドのシグネチャ検証"""

        # メソッドが存在することを確認
        assert hasattr(IYamlProcessor, "process_content_to_dict")

        method = IYamlProcessor.process_content_to_dict
        assert callable(method)


@pytest.mark.spec("SPEC-YAML-001")
class TestYamlProcessingService:
    """YamlProcessingServiceクラスのテストケース"""

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-SERVICE_DEPENDENCY_I")
    def test_service_dependency_injection(self):
        """依存性注入が正しく動作することを検証"""

        # モックの依存性を注入
        mock_processor = Mock(spec=IYamlProcessor)
        service = YamlProcessingService(yaml_processor=mock_processor)

        assert service._yaml_processor is mock_processor

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-PROCESS_EPISODE_CONT")
    def test_process_episode_content_calls_processor(self):
        """process_episode_contentがプロセッサーを呼び出すことを検証"""

        # モックプロセッサーを設定
        mock_processor = Mock(spec=IYamlProcessor)
        mock_processor.create_multiline_string.return_value = Mock()
        mock_processor.process_content_to_dict.return_value = {"processed": True}

        service = YamlProcessingService(yaml_processor=mock_processor)

        # テスト実行
        content = "Test content\\nwith newlines"
        result = service.process_episode_content(content)

        # プロセッサーが呼び出されることを確認
        mock_processor.create_multiline_string.assert_called_once_with(content)
        assert isinstance(result, dict)

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-PROCESS_EPISODE_CONT")
    def test_process_episode_content_returns_dict(self):
        """process_episode_contentが辞書を返すことを検証"""

        mock_processor = Mock(spec=IYamlProcessor)
        mock_processor.create_multiline_string.return_value = "MultilineString"
        mock_processor.process_content_to_dict.return_value = {
            "content": "MultilineString",
            "processed_at": "2025-08-06",
        }

        service = YamlProcessingService(yaml_processor=mock_processor)
        result = service.process_episode_content("test content")

        assert isinstance(result, dict)
        assert "content" in result
        assert "processed_at" in result


@pytest.mark.spec("SPEC-YAML-001")
class TestYamlProcessorAdapter:
    """YamlProcessorAdapterクラスのテストケース"""

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-ADAPTER_IMPLEMENTS_I")
    def test_adapter_implements_interface(self):
        """アダプターがインターフェースを実装していることを検証"""

        adapter = YamlProcessorAdapter()
        assert isinstance(adapter, IYamlProcessor)

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-CREATE_MULTILINE_STR")
    def test_create_multiline_string_returns_yaml_multiline(self):
        """create_multiline_stringがYAMLMultilineStringを返すことを検証"""

        adapter = YamlProcessorAdapter()
        content = "Test content\\nwith\\nmultiple lines"

        result = adapter.create_multiline_string(content)

        assert isinstance(result, YAMLMultilineString)
        # YAMLMultilineStringの内容を確認
        assert str(result) == content or hasattr(result, "content")

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-PROCESS_CONTENT_TO_D")
    def test_process_content_to_dict_handles_multiline(self):
        """process_content_to_dictがマルチライン文字列を適切に処理することを検証"""

        adapter = YamlProcessorAdapter()

        input_content = {
            "title": "Episode Title",
            "content": "Long content\\nwith multiple\\nlines",
            "metadata": {"episode": 1},
        }

        result = adapter.process_content_to_dict(input_content)

        assert isinstance(result, dict)
        assert "title" in result
        assert "content" in result
        assert "metadata" in result

        # contentがYAMLMultilineStringに変換されていることを確認

        assert isinstance(result["content"], YAMLMultilineString)

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-PROCESS_CONTENT_TO_D")
    def test_process_content_to_dict_preserves_non_string_values(self):
        """process_content_to_dictが文字列以外の値を保持することを検証"""

        adapter = YamlProcessorAdapter()

        input_content = {
            "episode_number": 42,
            "is_completed": True,
            "tags": ["action", "adventure"],
            "metadata": {"quality_score": 8.5},
        }

        result = adapter.process_content_to_dict(input_content)

        assert result["episode_number"] == 42
        assert result["is_completed"] is True
        assert result["tags"] == ["action", "adventure"]
        assert result["metadata"]["quality_score"] == 8.5


@pytest.mark.spec("SPEC-YAML-001")
class TestYamlIntegration:
    """YAML統合基盤の統合テストケース"""

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-END_TO_END_EPISODE_P")
    def test_end_to_end_episode_processing(self):
        """エピソード処理のエンドツーエンドテスト"""

        # 実際の実装を使用した統合テスト
        adapter = YamlProcessorAdapter()
        service = YamlProcessingService(yaml_processor=adapter)

        # エピソードコンテンツをシミュレート
        episode_content = """これは長いエピソードの内容です。
複数行にわたって記述されており、
YAML処理時に適切にフォーマットされる必要があります。

このテストは統合的な動作を確認します。"""

        result = service.process_episode_content(episode_content)

        assert isinstance(result, dict)
        assert "content" in result

        # 結果がYAML serializable であることを確認

        yaml_str = yaml.dump(result, allow_unicode=True, default_style=None)
        assert isinstance(yaml_str, str)
        assert len(yaml_str) > 0

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-DEPENDENCY_INJECTION")
    def test_dependency_injection_container_integration(self):
        """依存性注入コンテナとの統合テスト"""
        # 注意: これは実装後に有効になる将来のテスト
        pytest.skip("Dependency injection container implementation pending")


        container = DIContainer()
        service = container.resolve(YamlProcessingService)

        assert isinstance(service, YamlProcessingService)
        assert hasattr(service, "_yaml_processor")


@pytest.mark.spec("SPEC-YAML-001")
class TestDDDCompliance:
    """DDD準拠性のテストケース"""

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-DOMAIN_LAYER_HAS_NO_")
    def test_domain_layer_has_no_infrastructure_dependencies(self):
        """ドメイン層がインフラ層に依存していないことを検証"""
        # このテストは静的解析で実装される予定
        # 現在は概念的な検証として残す

        # ドメイン層のファイルを確認

        domain_interfaces_path = Path(__file__).parent.parent.parent.parent / "domain" / "interfaces"

        if domain_interfaces_path.exists():
            for py_file in domain_interfaces_path.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue

                with py_file.open(encoding="utf-8") as f:
                    content = f.read()

                # インフラ層への直接インポートが無いことを確認
                assert "from noveler.infrastructure" not in content
                assert "import noveler.infrastructure" not in content

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-APPLICATION_LAYER_DE")
    def test_application_layer_depends_only_on_domain_interface(self):
        """アプリケーション層がドメインインターフェースのみに依存することを検証"""
        # 同様に静的解析で実装予定
        pytest.skip("Static analysis implementation pending")


# パフォーマンステスト
@pytest.mark.spec("SPEC-YAML-001")
@pytest.mark.performance
class TestYamlPerformance:
    """YAML処理のパフォーマンステスト"""

    @pytest.mark.spec("SPEC-YAML_PROCESSOR_INTERFACE-LARGE_CONTENT_PROCES")
    def test_large_content_processing_performance(self):
        """大容量コンテンツ処理のパフォーマンス検証"""


        adapter = YamlProcessorAdapter()
        service = YamlProcessingService(yaml_processor=adapter)

        # 大きなコンテンツを生成
        large_content = "\\n".join(
            [f"Line {i}: This is a long line of content for performance testing." for i in range(1000)]
        )

        start_time = time.time()
        result = service.process_episode_content(large_content)
        end_time = time.time()

        processing_time = end_time - start_time

        # パフォーマンス要求: 1000行の処理が1秒以内
        assert processing_time < 1.0, f"Processing took {processing_time:.3f}s, should be < 1.0s"
        assert isinstance(result, dict)
        assert "content" in result
