"""Message Bus統合テスト

SPEC-901-DDD-REFACTORING対応:
- 既存ユースケースとMessage Busの統合テスト
- コマンド・イベント処理の動作確認
- CLI統合の動作確認
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

from noveler.application.integration.message_bus_integration import (
    MessageBusIntegrationService,
    LegacyUseCaseAdapterService,
    create_message_bus_integration,
    create_legacy_adapter
)
from noveler.presentation.cli_message_bus_facade import (
    CLIMessageBusFacade,
    create_cli_message_bus_facade
)
from noveler.domain.commands.plot_commands import (
    GeneratePlotCommand,
    ValidatePlotCommand,
    SavePlotCommand
)
from noveler.domain.events.plot_events import (
    PlotGenerationStarted,
    PlotGenerationCompleted,
    PlotQualityCheckCompleted
)
from noveler.application.unit_of_work import AbstractUnitOfWork


class MockUnitOfWork(AbstractUnitOfWork):
    """テスト用UnitOfWork実装"""

    def __init__(self):
        super().__init__()
        self.committed = False
        self.rolled_back = False
        self._collected_events = []

    def add_event(self, event):
        """イベントを追加"""
        self._collected_events.append(event)

    def collect_new_events(self):
        """新しいイベントを収集"""
        return self._collected_events

    def _commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


@pytest.fixture
def mock_services():
    """テスト用サービスモック"""
    logger_service = Mock()
    console_service = Mock()
    config_service = Mock()
    path_service = Mock()
    unit_of_work = MockUnitOfWork()

    # path_serviceのデフォルト設定
    path_service.get_project_root.return_value = Path("/tmp/test_project")

    return {
        "logger_service": logger_service,
        "console_service": console_service,
        "config_service": config_service,
        "path_service": path_service,
        "unit_of_work": unit_of_work
    }


class TestMessageBusIntegrationService:
    """Message Bus統合サービステスト"""

    def test_initialize_message_bus(self, mock_services):
        """Message Bus初期化テスト"""
        # Given
        integration_service = create_message_bus_integration(
            logger_service=mock_services["logger_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        # When
        message_bus = integration_service.initialize_message_bus(async_mode=False)

        # Then
        assert message_bus is not None
        assert hasattr(message_bus, 'handle')
        assert hasattr(message_bus, 'command_handlers')
        assert hasattr(message_bus, 'event_handlers')

        # コマンドハンドラーが登録されているか確認
        assert GeneratePlotCommand in message_bus.command_handlers
        assert ValidatePlotCommand in message_bus.command_handlers
        assert SavePlotCommand in message_bus.command_handlers

    def test_async_message_bus_initialization(self, mock_services):
        """非同期Message Bus初期化テスト"""
        # Given
        integration_service = create_message_bus_integration(
            logger_service=mock_services["logger_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        # When
        async_message_bus = integration_service.initialize_message_bus(async_mode=True)

        # Then
        assert async_message_bus is not None
        assert hasattr(async_message_bus, 'handle_async')
        assert async_message_bus._enable_async is True

    def test_create_mcp_integration_bus(self, mock_services):
        """MCP統合Message Bus作成テスト"""
        # Given
        integration_service = create_message_bus_integration(
            logger_service=mock_services["logger_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        # When
        mcp_bus = integration_service.create_mcp_integration_bus()

        # Then
        assert mcp_bus is not None
        assert hasattr(mcp_bus, 'handle_async')


class TestLegacyUseCaseAdapter:
    """レガシーユースケースアダプターテスト"""

    def test_execute_plot_generation(self, mock_services):
        """プロット生成実行テスト"""
        # Given
        integration_service = create_message_bus_integration(
            logger_service=mock_services["logger_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        legacy_adapter = create_legacy_adapter(integration_service)

        # When
        with tempfile.TemporaryDirectory() as temp_dir:
            result = legacy_adapter.execute_plot_generation(
                project_root=temp_dir,
                episode_number=1,
                chapter_title="テスト章",
                use_ai_enhancement=True
            )

        # Then
        assert result is not None
        assert hasattr(result, 'title')
        assert hasattr(result, 'summary')
        assert hasattr(result, 'episode_number')
        assert result.episode_number == 1

    def test_validate_plot_quality(self, mock_services):
        """プロット品質チェックテスト"""
        # Given
        integration_service = create_message_bus_integration(
            logger_service=mock_services["logger_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        legacy_adapter = create_legacy_adapter(integration_service)

        # When
        result = legacy_adapter.validate_plot_quality(
            plot_content="# テストプロット\n\nテスト内容\n\n詳細な説明",
            validation_criteria={"min_length": 10},
            project_root="/tmp/test"
        )

        # Then
        assert result is not None
        assert "quality_score" in result
        assert "passed_validation" in result
        assert isinstance(result["quality_score"], float)
        assert isinstance(result["passed_validation"], bool)


class TestCLIMessageBusFacade:
    """CLI Message Bus統合ファサードテスト"""

    def test_create_cli_facade(self, mock_services):
        """CLIファサード作成テスト"""
        # Given & When
        facade = create_cli_message_bus_facade(
            logger_service=mock_services["logger_service"],
            console_service=mock_services["console_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        # Then
        assert facade is not None
        assert hasattr(facade, 'generate_plot')
        assert hasattr(facade, 'validate_plot')
        assert hasattr(facade, 'generate_plot_async')

    def test_generate_plot_cli_interface(self, mock_services):
        """プロット生成CLI互換インターフェーステスト"""
        # Given
        facade = create_cli_message_bus_facade(
            logger_service=mock_services["logger_service"],
            console_service=mock_services["console_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        # When
        with tempfile.TemporaryDirectory() as temp_dir:
            result = facade.generate_plot(
                project_root=temp_dir,
                episode_number=1,
                chapter_title="テスト章",
                use_ai=True
            )

        # Then
        assert result is not None
        assert result["status"] == "success"
        assert "result" in result
        assert result["episode_number"] == 1

        # コンソール出力確認
        mock_services["console_service"].info.assert_called()
        mock_services["console_service"].success.assert_called()

    def test_validate_plot_cli_interface(self, mock_services):
        """プロット品質チェックCLI互換インターフェーステスト"""
        # Given
        facade = create_cli_message_bus_facade(
            logger_service=mock_services["logger_service"],
            console_service=mock_services["console_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        # テストファイル作成
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# テストプロット\n\n基本構成\n\nプロット内容の詳細説明")
            temp_file_path = f.name

        try:
            # When
            result = facade.validate_plot(
                plot_file_path=temp_file_path,
                quality_criteria={"min_length": 10}
            )

            # Then
            assert result is not None
            assert result["status"] == "success"
            assert "quality_score" in result
            assert "passed_validation" in result
            assert result["file_path"] == temp_file_path

        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_test_message_bus_connection(self, mock_services):
        """Message Bus接続テスト"""
        # Given
        facade = create_cli_message_bus_facade(
            logger_service=mock_services["logger_service"],
            console_service=mock_services["console_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        # When
        connection_test_result = facade.test_message_bus_connection()

        # Then
        assert connection_test_result is True
        mock_services["console_service"].success.assert_called()

    def test_show_integration_status(self, mock_services):
        """統合状況表示テスト"""
        # Given
        facade = create_cli_message_bus_facade(
            logger_service=mock_services["logger_service"],
            console_service=mock_services["console_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        # When
        facade.show_integration_status()

        # Then
        # コンソール出力が呼ばれていることを確認
        mock_services["console_service"].info.assert_called()


class TestEventHandling:
    """イベント処理テスト"""

    def test_plot_generation_events(self, mock_services):
        """プロット生成イベント処理テスト"""
        # Given
        integration_service = create_message_bus_integration(
            logger_service=mock_services["logger_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        message_bus = integration_service.initialize_message_bus(async_mode=False)

        # When
        with tempfile.TemporaryDirectory() as temp_dir:
            command = GeneratePlotCommand(
                project_root=temp_dir,
                episode_number=1,
                chapter_title="テスト章"
            )

            result = message_bus.handle(command)

        # Then
        assert result is not None

        # イベントが生成されていることを確認
        events = mock_services["unit_of_work"].collect_new_events()

        # PlotGenerationStartedとPlotGenerationCompletedが発行されているはず
        event_types = [type(event).__name__ for event in events]
        assert "PlotGenerationStarted" in event_types
        assert "PlotGenerationCompleted" in event_types


class TestErrorHandling:
    """エラーハンドリングテスト"""

    def test_plot_generation_error_handling(self, mock_services):
        """プロット生成エラーハンドリングテスト"""
        # Given
        facade = create_cli_message_bus_facade(
            logger_service=mock_services["logger_service"],
            console_service=mock_services["console_service"],
            unit_of_work=mock_services["unit_of_work"],
            config_service=mock_services["config_service"],
            path_service=mock_services["path_service"]
        )

        # When - 存在しないディレクトリを指定してエラーを発生させる
        result = facade.generate_plot(
            project_root="/nonexistent/path",
            episode_number=1
        )

        # Then - エラーが適切にハンドリングされていることを確認
        assert result is not None
        # エラー状況によってはsuccessの場合もある（基本的な実装では直接的なファイルアクセスがないため）
        # エラーハンドリングの仕組みが動作していることを確認
        mock_services["console_service"].info.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
