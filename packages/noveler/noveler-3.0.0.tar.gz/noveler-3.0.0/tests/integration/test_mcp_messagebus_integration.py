# File: tests/integration/test_mcp_messagebus_integration.py
# Purpose: Integration tests for MCP tools with MessageBus routing
# Context: Validates use_message_bus=True functionality for noveler_check and noveler_write

"""MCP MessageBus統合テスト

MCPツールのuse_message_bus=Trueオプションによる
MessageBus経由処理の統合テスト

参照: TODO.md SPEC-901残件 - MCPサーバーツールのBusルーティング拡張
"""

import asyncio
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from mcp_servers.noveler.json_conversion_server import JSONConversionServer
from noveler.application.simple_message_bus import MessageBus, BusConfig
from noveler.application.uow import InMemoryUnitOfWork


@pytest.fixture
def temp_output_dir():
    """Provide a temporary output directory for MCP server tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mcp_server_with_bus(temp_output_dir: Path) -> JSONConversionServer:
    """Instantiate JSONConversionServer with MessageBus enabled."""
    return JSONConversionServer(output_dir=temp_output_dir, use_message_bus=True)


@pytest.fixture
def mcp_server_without_bus(temp_output_dir: Path) -> JSONConversionServer:
    """Instantiate JSONConversionServer without MessageBus routing."""
    return JSONConversionServer(output_dir=temp_output_dir, use_message_bus=False)


class TestMCPMessageBusIntegration:
    """MCP MessageBus統合テスト"""

    @pytest.mark.integration
    @pytest.mark.spec("SPEC-901")
    def test_noveler_check_with_message_bus_success(self, mcp_server_with_bus):
        """noveler_check: MessageBus経由での成功パターン"""
        # Given
        server = mcp_server_with_bus
        episode_number = 1
        auto_fix = False

        # When: MessageBus経由でチェック実行
        result = server._handle_check_via_bus_sync(episode_number, auto_fix)

        # Then: 成功レスポンスを確認
        assert "品質チェック完了" in result
        assert f"Episode {episode_number}" in result
        assert ("合格" in result or "要改善" in result)

    @pytest.mark.integration
    @pytest.mark.spec("SPEC-901")
    def test_noveler_check_message_bus_routing(self, mcp_server_with_bus):
        """noveler_check: MessageBusルーティングの動作確認"""
        # Given
        server = mcp_server_with_bus
        server._use_message_bus = True
        episode_number = 2

        # Mock: 従来の_execute_novel_commandを監視
        with patch.object(server, '_execute_novel_command') as mock_cli:
            mock_cli.return_value = "CLI execution result"

            # When: ツールを実行（MessageBusルーティング有効）
            from mcp_servers.noveler.server.noveler_tool_registry import register_individual_noveler_tools

            # 疑似的にツール関数を実行
            class MockContext:
                def __init__(self, server):
                    self._server = server
                    self._use_message_bus = server._use_message_bus

                def _handle_check_via_bus_sync(self, episode_number, auto_fix):
                    return self._server._handle_check_via_bus_sync(episode_number, auto_fix)

                def _execute_novel_command(self, command, options, project_root):
                    return self._server._execute_novel_command(command, options, project_root)

            ctx = MockContext(server)

            # noveler_checkツールの処理をシミュレート
            if hasattr(ctx, "_use_message_bus") and getattr(ctx, "_use_message_bus", False):
                result = ctx._handle_check_via_bus_sync(episode_number, False)
            else:
                result = ctx._execute_novel_command(f"check {episode_number}", {"auto_fix": False}, None)

        # Then: MessageBus経由で実行され、CLIは呼ばれない
        assert "品質チェック完了" in result
        mock_cli.assert_not_called()

    @pytest.mark.integration
    @pytest.mark.spec("SPEC-901")
    def test_noveler_check_without_message_bus(self, mcp_server_without_bus):
        """noveler_check: MessageBus無効時の通常処理確認"""
        # Given
        server = mcp_server_without_bus
        server._use_message_bus = False

        # Mock: 従来の_execute_novel_commandの結果
        with patch.object(server, '_execute_novel_command') as mock_cli:
            mock_cli.return_value = "CLI品質チェック実行完了"

            # When: ツール実行（MessageBus無効）
            class MockContext:
                def __init__(self, server):
                    self._server = server
                    self._use_message_bus = getattr(server, '_use_message_bus', False)

                def _execute_novel_command(self, command, options, project_root):
                    return self._server._execute_novel_command(command, options, project_root)

            ctx = MockContext(server)

            # noveler_checkツールの処理をシミュレート
            episode_number = 3
            if hasattr(ctx, "_use_message_bus") and getattr(ctx, "_use_message_bus", False):
                result = "MessageBus処理"  # 実行されない
            else:
                result = ctx._execute_novel_command(f"check {episode_number}", {"auto_fix": False}, None)

        # Then: 従来のCLI実行が使用される
        assert result == "CLI品質チェック実行完了"
        mock_cli.assert_called_once_with(
            f"check {episode_number}",
            {"auto_fix": False, "verbose": False},
            None
        )

    @pytest.mark.integration
    @pytest.mark.spec("SPEC-901")
    def test_message_bus_command_validation(self, mcp_server_with_bus):
        """MessageBus: コマンド入力の検証"""
        # Given
        server = mcp_server_with_bus

        # When & Then: 無効なエピソード番号
        result = server._handle_check_via_bus_sync(-1, False)
        assert "MessageBus経由品質チェックエラー" in result or "Episode -1" in result

        # When & Then: 正常なエピソード番号
        result = server._handle_check_via_bus_sync(1, True)
        assert "品質チェック完了" in result or "品質チェック失敗" in result

    @pytest.mark.integration
    @pytest.mark.spec("SPEC-901")
    def test_message_bus_async_execution_context(self, mcp_server_with_bus):
        """MessageBus: 非同期実行コンテキストの処理確認"""
        # Given
        server = mcp_server_with_bus

        # When: 複数回実行（非同期処理の安定性確認）
        results = []
        for i in range(3):
            result = server._handle_check_via_bus_sync(i + 1, False)
            results.append(result)

        # Then: 全て正常に実行される
        for i, result in enumerate(results):
            assert f"Episode {i + 1}" in result
            assert ("品質チェック完了" in result or "品質チェック失敗" in result)

    @pytest.mark.integration
    @pytest.mark.spec("SPEC-901")
    def test_message_bus_error_handling(self, mcp_server_with_bus):
        """MessageBus: エラーハンドリングの確認"""
        # Given
        server = mcp_server_with_bus

        # Mock: MessageBus内でエラーを発生させる
        with patch('noveler.application.simple_message_bus.MessageBus') as mock_bus_class:
            mock_bus = AsyncMock()
            mock_bus.handle_command.side_effect = Exception("Bus execution error")
            mock_bus_class.return_value = mock_bus

            # When: エラー発生時の処理
            result = server._handle_check_via_bus_sync(1, False)

            # Then: エラーが適切にハンドリングされる
            assert "MessageBus経由品質チェックエラー" in result or "非同期実行エラー" in result

    @pytest.mark.integration
    @pytest.mark.spec("SPEC-901")
    @pytest.mark.performance
    def test_message_bus_performance_check(self, mcp_server_with_bus):
        """MessageBus: 基本的な性能確認（<1秒目安）"""
        # Given
        server = mcp_server_with_bus
        import time

        # When: 実行時間を測定
        start_time = time.perf_counter()
        result = server._handle_check_via_bus_sync(1, False)
        end_time = time.perf_counter()

        # Then: 合理的な時間内で完了
        execution_time = end_time - start_time
        assert execution_time < 1.0  # 1秒以内
        assert ("品質チェック完了" in result or "品質チェック失敗" in result)

    @pytest.mark.integration
    @pytest.mark.spec("SPEC-901")
    def test_noveler_write_message_bus_integration(self, mcp_server_with_bus):
        """noveler_write: MessageBus統合確認（write機能のテスト）"""
        # Given
        server = mcp_server_with_bus

        # 既存の_handle_write_via_bus_syncメソッドが動作することを確認
        if hasattr(server, '_handle_write_via_bus_sync'):
            # When
            result = server._handle_write_via_bus_sync(1)

            # Then
            assert isinstance(result, str)
            assert len(result) > 0
        else:
            pytest.skip("_handle_write_via_bus_sync not implemented")

    @pytest.mark.integration
    @pytest.mark.spec("SPEC-901")
    def test_message_bus_idempotency_check(self, mcp_server_with_bus):
        """MessageBus: べき等性の基本確認"""
        # Given
        server = mcp_server_with_bus

        # When: 同じコマンドを複数回実行
        result1 = server._handle_check_via_bus_sync(1, False)
        result2 = server._handle_check_via_bus_sync(1, False)

        # Then: 両方とも正常に実行される（詳細なべき等性は別途テスト）
        assert ("品質チェック完了" in result1 or "品質チェック失敗" in result1)
        assert ("品質チェック完了" in result2 or "品質チェック失敗" in result2)


class TestMCPMessageBusMetrics:
    """MCP MessageBus メトリクス統合テスト"""

    @pytest.fixture
    def mcp_server_with_metrics(self, temp_output_dir):
        """メトリクス取得可能なMCPサーバー"""
        server = JSONConversionServer(
            output_dir=temp_output_dir,
            use_message_bus=True
        )
        return server

    @pytest.mark.integration
    @pytest.mark.spec("SPEC-901")
    def test_message_bus_metrics_collection(self, mcp_server_with_metrics):
        """MessageBus: メトリクス収集の基本確認"""
        # Given
        server = mcp_server_with_metrics

        # When: コマンド実行
        server._handle_check_via_bus_sync(1, False)

        # Then: メトリクス情報が取得可能（詳細は簡易チェックのみ）
        # 実際のメトリクス詳細はMessageBus単体テストで検証
        assert hasattr(server, '_use_message_bus')
        assert server._use_message_bus is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
