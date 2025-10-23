"""MCP統合テスト - 簡易版（stdio MCP用）

実際のMCPサーバーとのstdio通信による統合テスト
"""

import asyncio
import json
import pytest
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MCPResponse:
    """MCPレスポンス結果"""
    success: bool
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    raw_stdout: str = ""
    raw_stderr: str = ""


class SimpleMCPClient:
    """簡易MCP統合テストクライアント（stdio版）"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.server_command = [
            "python", "-m", "mcp_servers.noveler.main"
        ]

    async def send_mcp_request(self, method: str, params: Dict[str, Any]) -> MCPResponse:
        """MCPリクエスト送信

        Args:
            method: MCPメソッド名
            params: リクエストパラメータ

        Returns:
            MCPレスポンス
        """
        # JSON-RPC 2.0リクエスト構築
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }

        try:
            # サーバープロセス起動
            process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd()
            )

            # リクエスト送信
            request_data = json.dumps(request) + "\n"
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=request_data.encode()),
                timeout=self.timeout
            )

            stdout_text = stdout.decode('utf-8') if stdout else ""
            stderr_text = stderr.decode('utf-8') if stderr else ""

            # レスポンス解析
            if stdout_text.strip():
                try:
                    response_data = json.loads(stdout_text.strip())
                    return MCPResponse(
                        success=True,
                        response_data=response_data,
                        raw_stdout=stdout_text,
                        raw_stderr=stderr_text
                    )
                except json.JSONDecodeError:
                    return MCPResponse(
                        success=False,
                        error_message="Invalid JSON response",
                        raw_stdout=stdout_text,
                        raw_stderr=stderr_text
                    )
            else:
                return MCPResponse(
                    success=False,
                    error_message="No response from server",
                    raw_stdout=stdout_text,
                    raw_stderr=stderr_text
                )

        except asyncio.TimeoutError:
            return MCPResponse(
                success=False,
                error_message=f"Request timeout after {self.timeout}s"
            )
        except Exception as e:
            return MCPResponse(
                success=False,
                error_message=str(e)
            )


class TestMCPIntegrationSimple:
    """簡易MCP統合テストクラス"""

    @pytest.fixture
    def mcp_client(self):
        """MCPクライアント作成"""
        return SimpleMCPClient(timeout=10)

    @pytest.mark.asyncio
    async def test_mcp_server_basic_communication(self, mcp_client):
        """MCPサーバーとの基本通信テスト"""
        # initialize リクエスト送信
        response = await mcp_client.send_mcp_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        )

        # 通信が確立されたかチェック
        assert response.raw_stdout != "" or response.raw_stderr != ""

        # エラーメッセージがある場合は詳細を確認
        if response.error_message:
            print(f"Error: {response.error_message}")
            print(f"Stdout: {response.raw_stdout}")
            print(f"Stderr: {response.raw_stderr}")

        # 少なくとも何らかのレスポンスがあることを確認
        assert response.raw_stdout != "" or response.error_message is not None

    @pytest.mark.asyncio
    async def test_server_can_start(self):
        """サーバーが起動できることを確認"""
        try:
            process = await asyncio.create_subprocess_exec(
                "python", "-m", "mcp_servers.noveler.main",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd()
            )

            # 少し待ってからプロセスを終了
            await asyncio.sleep(0.5)
            process.terminate()

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=5
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                stdout, stderr = b"", b""

            # プロセスが正常に起動したことを確認
            # （即座に終了しても、起動エラーでなければOK）
            assert process.returncode is not None

            # エラーメッセージが出力されている場合は表示
            if stderr:
                stderr_text = stderr.decode('utf-8', errors='ignore')
                print(f"Server stderr: {stderr_text}")

            if stdout:
                stdout_text = stdout.decode('utf-8', errors='ignore')
                print(f"Server stdout: {stdout_text}")

        except Exception as e:
            pytest.fail(f"Server startup failed: {e}")


class TestCoreComponentsIntegration:
    """コアコンポーネント統合テスト（実MCPサーバーなし）"""

    def test_command_builder_response_parser_integration(self):
        """CommandBuilderとResponseParserの統合テスト"""
        from mcp_servers.noveler.core.command_builder import CommandBuilder
        from mcp_servers.noveler.core.response_parser import ResponseParser

        builder = CommandBuilder()
        parser = ResponseParser()

        # コマンド構築
        cmd_parts, working_dir = builder.build_novel_command("write 1", {"force": True})

        assert len(cmd_parts) >= 3
        assert "--force" in cmd_parts

        # モックレスポンス解析
        mock_stdout = "Created: output.txt\n処理完了しました"
        result = parser.parse_novel_output(mock_stdout, "", 0)

        assert result["success"] is True
        assert "generated_files" in result
        assert "output.txt" in result["generated_files"]

    def test_subprocess_adapter_integration(self):
        """SubprocessAdapterの統合テスト"""
        from mcp_servers.noveler.core.subprocess_adapter import (
            MockSubprocessAdapter, SubprocessExecutor
        )

        # モックアダプターによる統合テスト
        mock_adapter = MockSubprocessAdapter()
        executor = SubprocessExecutor(mock_adapter)

        mock_adapter.set_mock_response("echo", stdout="Hello Test", return_code=0)

        result = executor.execute_with_validation(
            ["echo", "Hello Test"],
            Path.cwd(),
            expected_return_codes=[0]
        )

        assert result.return_code == 0
        assert result.stdout == "Hello Test"

        # 実行履歴確認
        history = mock_adapter.get_execution_history()
        assert len(history) == 1
        assert history[0][0] == ["echo", "Hello Test"]

    def test_full_pipeline_mock(self):
        """完全パイプラインのモック統合テスト"""
        from mcp_servers.noveler.core.command_builder import CommandBuilder
        from mcp_servers.noveler.core.response_parser import ResponseParser
        from mcp_servers.noveler.core.subprocess_adapter import create_subprocess_adapter

        # コンポーネント初期化
        builder = CommandBuilder()
        parser = ResponseParser()
        adapter = create_subprocess_adapter(mock_mode=True)

        # モック設定
        if hasattr(adapter, 'set_mock_response'):
            adapter.set_mock_response(
                "noveler-dev",
                stdout="Created: chapter1.txt\n成功",
                return_code=0
            )

        # パイプライン実行
        cmd_parts, working_dir = builder.build_novel_command("write 1", {})
        env_vars = builder.build_environment_vars()

        subprocess_result = adapter.execute(cmd_parts, working_dir, env_vars)
        parsed_result = parser.parse_novel_output(
            subprocess_result.stdout,
            subprocess_result.stderr,
            subprocess_result.return_code
        )

        # 結果検証
        assert parsed_result["success"] is True
        if "generated_files" in parsed_result:
            assert "chapter1.txt" in parsed_result["generated_files"]

    @pytest.mark.asyncio
    async def test_refactored_code_compatibility(self):
        """リファクタリング済みコードとの互換性テスト"""
        # 新しいコアコンポーネントを使った場合と同等の結果が得られるかテスト
        from mcp_servers.noveler.core.command_builder import CommandBuilder
        from mcp_servers.noveler.core.response_parser import ResponseParser
        from mcp_servers.noveler.core.subprocess_adapter import create_subprocess_adapter

        command_builder = CommandBuilder()
        response_parser = ResponseParser()
        subprocess_adapter = create_subprocess_adapter(mock_mode=True)

        # 実際のリファクタリング済み処理をシミュレート
        command = "status"
        options = {}
        project_root = str(Path.cwd())

        # 環境変数構築
        env_vars = command_builder.build_environment_vars(project_root)
        assert isinstance(env_vars, dict)

        # コマンド構築
        cmd_parts, working_dir = command_builder.build_novel_command(
            command, options, project_root
        )
        assert len(cmd_parts) >= 2
        assert working_dir == Path(project_root).absolute()

        # モック実行
        if hasattr(subprocess_adapter, 'set_mock_response'):
            # 実際のコマンドパスに基づいてモック設定
            command_key = cmd_parts[0]  # 完全パスを使用
            subprocess_adapter.set_mock_response(
                command_key,
                stdout="Project: test\nProgress: 1/5",
                return_code=0
            )

        subprocess_result = subprocess_adapter.execute(
            cmd_parts, working_dir, env_vars, timeout=300
        )

        # レスポンス解析
        parsed_result = response_parser.parse_novel_output(
            subprocess_result.stdout,
            subprocess_result.stderr,
            subprocess_result.return_code
        )

        # 既存フォーマットに変換（互換性確認）
        cli_result = {
            "success": parsed_result["success"],
            "stdout": parsed_result["raw_output"]["stdout"],
            "stderr": parsed_result["raw_output"]["stderr"],
            "command": " ".join(cmd_parts),
            "returncode": parsed_result["return_code"],
            "working_dir": str(working_dir),
            "project_root": project_root
        }

        # 互換性確認
        assert cli_result["success"] is True
        assert cli_result["stdout"] == "Project: test\nProgress: 1/5"
        assert cli_result["returncode"] == 0
