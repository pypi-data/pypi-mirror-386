"""MCP Test Client - JSON-RPC統合テスト用クライアント

実際のMCPサーバーとのJSON-RPC通信をテストするクライアント
"""

import asyncio
import json
import subprocess
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx


@dataclass
class MCPTestResult:
    """MCPテスト結果"""
    success: bool
    response_data: dict[str, Any] | None = None
    error_message: str | None = None
    execution_time: float = 0.0
    status_code: int | None = None
    raw_response: str | None = None


@dataclass
class MCPServerProcess:
    """MCPサーバープロセス管理"""
    process: subprocess.Popen
    port: int
    base_url: str
    started_at: float = field(default_factory=time.time)

    def is_running(self) -> bool:
        """プロセスが実行中かチェック"""
        return self.process.poll() is None

    def terminate(self):
        """プロセスを終了"""
        if self.is_running():
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


class MCPTestClient:
    """MCP統合テスト用クライアント"""

    def __init__(
        self,
        server_command: list[str] | None = None,
        port: int = 8080,
        timeout: int = 30
    ) -> None:
        """初期化

        Args:
            server_command: MCPサーバー起動コマンド
            port: サーバーポート番号
            timeout: タイムアウト秒数
        """
        self.server_command = server_command or [
            "python", "-m", "src.mcp_servers.noveler.main"
        ]
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://localhost:{port}"
        self._server_process: MCPServerProcess | None = None
        self._client: httpx.AsyncClient | None = None

    async def start_server(self) -> MCPServerProcess:
        """MCPサーバーを起動

        Returns:
            サーバープロセス管理オブジェクト

        Raises:
            RuntimeError: サーバー起動に失敗した場合
        """
        # 既存のサーバーが動いている場合は停止
        if self._server_process and self._server_process.is_running():
            await self.stop_server()

        try:
            # サーバープロセス起動
            full_command = [*self.server_command, "--port", str(self.port)]
            print(f"[DEBUG] Starting MCP server with command: {full_command}")
            print(f"[DEBUG] Working directory: {Path.cwd()}")
            process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path.cwd()
            )

            self._server_process = MCPServerProcess(
                process=process,
                port=self.port,
                base_url=self.base_url
            )

            # サーバー起動待機
            await self._wait_for_server_start()

            return self._server_process

        except Exception as e:
            if self._server_process:
                self._server_process.terminate()
            msg = f"MCPサーバー起動に失敗: {e}"
            raise RuntimeError(msg)

    async def stop_server(self):
        """MCPサーバーを停止"""
        if self._server_process:
            self._server_process.terminate()
            self._server_process = None

    async def _wait_for_server_start(self, max_attempts: int = 30) -> None:
        """サーバー起動待機

        Args:
            max_attempts: 最大試行回数

        Raises:
            RuntimeError: サーバー起動タイムアウト
        """
        for _attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"{self.base_url}/health")
                    if response.status_code == 200:
                        return
            except (httpx.RequestError, httpx.TimeoutException):
                pass

            if not self._server_process or not self._server_process.is_running():
                # プロセスが死んでいる場合はエラー出力を取得
                stderr_output = ""
                if self._server_process and self._server_process.process.stderr:
                    stderr_output = self._server_process.process.stderr.read()
                msg = f"MCPサーバープロセスが終了しました: {stderr_output}"
                raise RuntimeError(msg)

            await asyncio.sleep(0.5)

        msg = f"MCPサーバー起動タイムアウト（{max_attempts * 0.5}秒）"
        raise RuntimeError(msg)

    @asynccontextmanager
    async def server_context(self):
        """サーバーコンテキストマネージャー

        with文でサーバーの起動・停止を自動管理
        """
        server_process = None
        try:
            server_process = await self.start_server()
            yield server_process
        finally:
            await self.stop_server()

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        method: str = "POST"
    ) -> MCPTestResult:
        """MCPツール呼び出し

        Args:
            tool_name: ツール名
            arguments: ツール引数
            method: HTTPメソッド

        Returns:
            テスト結果
        """
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/tools/{tool_name}"

                if method.upper() == "GET":
                    response = await client.get(url, params=arguments)
                else:
                    response = await client.post(url, json=arguments)

                execution_time = time.time() - start_time

                # レスポンス解析
                try:
                    response_data = response.json()
                    success = response.status_code == 200 and not response_data.get("error")
                except json.JSONDecodeError:
                    response_data = {"raw_text": response.text}
                    success = response.status_code == 200

                return MCPTestResult(
                    success=success,
                    response_data=response_data,
                    execution_time=execution_time,
                    status_code=response.status_code,
                    raw_response=response.text
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return MCPTestResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )

    async def list_tools(self) -> MCPTestResult:
        """利用可能ツール一覧取得

        Returns:
            ツール一覧のテスト結果
        """
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/tools")
                execution_time = time.time() - start_time

                response_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"raw_text": response.text}

                return MCPTestResult(
                    success=response.status_code == 200,
                    response_data=response_data,
                    execution_time=execution_time,
                    status_code=response.status_code,
                    raw_response=response.text
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return MCPTestResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )

    async def health_check(self) -> MCPTestResult:
        """ヘルスチェック

        Returns:
            ヘルスチェック結果
        """
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                execution_time = time.time() - start_time

                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = {"status": "ok" if response.status_code == 200 else "error"}

                return MCPTestResult(
                    success=response.status_code == 200,
                    response_data=response_data,
                    execution_time=execution_time,
                    status_code=response.status_code,
                    raw_response=response.text
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return MCPTestResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )

    async def run_test_suite(
        self,
        test_cases: list[dict[str, Any]]
    ) -> list[tuple[dict[str, Any], MCPTestResult]]:
        """テストスイート実行

        Args:
            test_cases: テストケースリスト

        Returns:
            (テストケース, 結果)のタプルリスト
        """
        results = []

        async with self.server_context():
            # ヘルスチェック
            health_result = await self.health_check()
            if not health_result.success:
                msg = f"サーバーヘルスチェック失敗: {health_result.error_message}"
                raise RuntimeError(msg)

            # 各テストケース実行
            for test_case in test_cases:
                tool_name = test_case.get("tool_name")
                arguments = test_case.get("arguments", {})
                method = test_case.get("method", "POST")

                if not tool_name:
                    result = MCPTestResult(
                        success=False,
                        error_message="tool_name が指定されていません"
                    )
                else:
                    result = await self.call_tool(tool_name, arguments, method)

                results.append((test_case, result))

                # テスト間の間隔
                if test_case.get("delay_after", 0) > 0:
                    await asyncio.sleep(test_case["delay_after"])

        return results

    def get_server_logs(self) -> tuple[str, str] | None:
        """サーバーログ取得

        Returns:
            (stdout, stderr)のタプル、サーバーが動いていない場合はNone
        """
        if not self._server_process or not self._server_process.process:
            return None

        try:
            stdout, stderr = self._server_process.process.communicate(timeout=1)
            return stdout, stderr
        except subprocess.TimeoutExpired:
            return None, None
        except Exception:
            return None, None


class MCPIntegrationTestSuite:
    """MCP統合テストスイート"""

    def __init__(self, client: MCPTestClient) -> None:
        self.client = client

    async def test_basic_functionality(self) -> dict[str, Any]:
        """基本機能テスト

        Returns:
            テスト結果サマリー
        """
        test_cases = [
            {
                "name": "ツール一覧取得",
                "tool_name": None,  # list_tools用の特別ケース
                "test_type": "list_tools"
            },
            {
                "name": "ステータス確認",
                "tool_name": "status",
                "arguments": {}
            },
            {
                "name": "JSON変換機能",
                "tool_name": "convert_cli_to_json",
                "arguments": {
                    "cli_result": {
                        "success": True,
                        "stdout": "テスト出力",
                        "stderr": "",
                        "command": "test command"
                    }
                }
            },
        ]

        results = []

        async with self.client.server_context():
            for test_case in test_cases:
                if test_case.get("test_type") == "list_tools":
                    result = await self.client.list_tools()
                else:
                    result = await self.client.call_tool(
                        test_case["tool_name"],
                        test_case["arguments"]
                    )

                results.append({
                    "test_name": test_case["name"],
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "error": result.error_message,
                    "status_code": result.status_code
                })

        # サマリー作成
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r["success"])
        total_time = sum(r["execution_time"] for r in results)

        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_execution_time": total_time
            },
            "test_results": results
        }

    async def test_error_handling(self) -> dict[str, Any]:
        """エラーハンドリングテスト

        Returns:
            エラーハンドリングテスト結果
        """
        error_test_cases = [
            {
                "name": "存在しないツール",
                "tool_name": "non_existent_tool",
                "arguments": {},
                "expected_success": False
            },
            {
                "name": "無効な引数",
                "tool_name": "status",
                "arguments": {"invalid_param": "invalid_value"},
                "expected_success": False  # または True（引数を無視する場合）
            },
            {
                "name": "必須パラメータ不足",
                "tool_name": "convert_cli_to_json",
                "arguments": {},  # cli_resultが不足
                "expected_success": False
            }
        ]

        results = []

        async with self.client.server_context():
            for test_case in error_test_cases:
                result = await self.client.call_tool(
                    test_case["tool_name"],
                    test_case["arguments"]
                )

                expected_success = test_case.get("expected_success", False)
                test_passed = (result.success == expected_success)

                results.append({
                    "test_name": test_case["name"],
                    "expected_success": expected_success,
                    "actual_success": result.success,
                    "test_passed": test_passed,
                    "execution_time": result.execution_time,
                    "error": result.error_message,
                    "status_code": result.status_code
                })

        # エラーハンドリングサマリー
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r["test_passed"])

        return {
            "error_handling_summary": {
                "total_error_tests": total_tests,
                "passed_error_tests": passed_tests,
                "error_handling_rate": passed_tests / total_tests if total_tests > 0 else 0
            },
            "error_test_results": results
        }
