"""Async subprocess adapters used by the MCP server integration tests."""

import asyncio
from noveler.infrastructure.logging.unified_logger import get_logger
import time
from pathlib import Path
from typing import Any, Protocol

from mcp_servers.noveler.core.subprocess_adapter import SubprocessResult


class AsyncSubprocessProtocol(Protocol):
    """Protocol describing the asynchronous subprocess interface."""

    async def execute(
        self,
        command: list[str],
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None
    ) -> SubprocessResult:
        """Execute a command asynchronously.

        Args:
            command (list[str]): Command arguments.
            working_dir (Path): Working directory for command execution.
            env (dict[str, str] | None): Optional environment overrides.
            timeout (int | None): Optional timeout in seconds.

        Returns:
            SubprocessResult: Captured outputs and metadata.
        """
        ...


class AsyncSubprocessAdapter:
    """Async adapter leveraging ``asyncio.create_subprocess_exec``."""

    def __init__(self, timeout_default: int = 300) -> None:
        """Initialise the adapter with a default timeout.

        Args:
            timeout_default (int): Default timeout applied when
                :meth:`execute` receives no explicit value.
        """
        self._timeout_default = timeout_default
        self._logger = get_logger(__name__)

    async def execute(
        self,
        command: list[str],
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None
    ) -> SubprocessResult:
        """Execute the command asynchronously and capture its output.

        Args:
            command (list[str]): Command arguments.
            working_dir (Path): Working directory for command execution.
            env (dict[str, str] | None): Optional environment overrides.
            timeout (int | None): Optional timeout in seconds; defaults to the
                constructor value when not specified.

        Returns:
            SubprocessResult: Captured outputs, return code and metadata.
        """
        start_time = time.time()
        effective_timeout = timeout or self._timeout_default

        try:
            # 環境変数のマージ
            merged_env = None
            if env:
                import os
                merged_env = os.environ.copy()
                merged_env.update(env)

            self._logger.debug("非同期コマンド実行開始: %s", " ".join(command))

            # asyncio.create_subprocess_execによる完全非同期実行
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=merged_env
            )

            # 非同期タイムアウト制御
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=effective_timeout
                )
            except asyncio.TimeoutError:
                # プロセス強制終了
                process.kill()
                await process.wait()

                execution_time = time.time() - start_time
                self._logger.warning("コマンドタイムアウト: %ss", effective_timeout)

                return SubprocessResult(
                    stdout="",
                    stderr=f"Command timed out after {effective_timeout} seconds",
                    return_code=-1,
                    command=command,
                    working_dir=working_dir,
                    execution_time=execution_time
                )

            execution_time = time.time() - start_time
            stdout_str = stdout.decode("utf-8") if stdout else ""
            stderr_str = stderr.decode("utf-8") if stderr else ""

            self._logger.debug("コマンド実行完了: %s秒", execution_time)

            return SubprocessResult(
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=process.returncode or 0,
                command=command,
                working_dir=working_dir,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._logger.exception("非同期コマンド実行エラー: %s", str(e))

            return SubprocessResult(
                stdout="",
                stderr=f"Async execution failed: {e!s}",
                return_code=-1,
                command=command,
                working_dir=working_dir,
                execution_time=execution_time
            )


class AsyncMockSubprocessAdapter:
    """Mock implementation of :class:`AsyncSubprocessAdapter` for tests."""

    def __init__(self, response_delay: float = 0.1) -> None:
        """Initialise the mock adapter.

        Args:
            response_delay (float): Artificial delay applied before returning a
                mock response.
        """
        self._mock_responses: dict[str, SubprocessResult] = {}
        self._execution_history: list[tuple] = []
        self._response_delay = response_delay

    def set_mock_response(
        self,
        command_pattern: str,
        stdout: str = "",
        stderr: str = "",
        return_code: int = 0,
        execution_time: float = 0.1
    ) -> None:
        """Register a mock response that matches the given command prefix.

        Args:
            command_pattern (str): Key used to locate the response, typically
                the command name (first argument).
            stdout (str): Mocked standard output.
            stderr (str): Mocked error output.
            return_code (int): Mocked return code.
            execution_time (float): Simulated execution time in seconds.
        """
        self._mock_responses[command_pattern] = SubprocessResult(
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            command=[],  # 後で実際のコマンドで上書き
            working_dir=Path.cwd(),  # 後で実際の作業ディレクトリで上書き
            execution_time=execution_time
        )

    async def execute(
        self,
        command: list[str],
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None
    ) -> SubprocessResult:
        """Return the preconfigured async mock response.

        Args:
            command (list[str]): Command arguments.
            working_dir (Path): Working directory for command execution.
            env (dict[str, str] | None): Optional environment overrides.
            timeout (int | None): Ignored but accepted for signature
                compatibility.

        Returns:
            SubprocessResult: Mocked subprocess result.
        """
        start_time = time.time()

        # 実行履歴を記録
        self._execution_history.append((command.copy(), working_dir, env, time.time()))

        # 非同期遅延をシミュレート
        await asyncio.sleep(self._response_delay)

        # コマンドパターンにマッチするモックレスポンスを探す
        if command:
            command_key = command[0]
            if command_key in self._mock_responses:
                mock_result = self._mock_responses[command_key]
                execution_time = time.time() - start_time

                # 実際のコマンドと作業ディレクトリで更新
                return SubprocessResult(
                    stdout=mock_result.stdout,
                    stderr=mock_result.stderr,
                    return_code=mock_result.return_code,
                    command=command,
                    working_dir=working_dir,
                    execution_time=execution_time
                )

        # デフォルトのモックレスポンス
        execution_time = time.time() - start_time
        return SubprocessResult(
            stdout="Async mock output",
            stderr="",
            return_code=0,
            command=command,
            working_dir=working_dir,
            execution_time=execution_time
        )

    def get_execution_history(self) -> list[tuple]:
        """Return a shallow copy of the execution history."""
        return self._execution_history.copy()

    def clear_history(self) -> None:
        """Clear the stored execution history."""
        self._execution_history.clear()

    def clear_mock_responses(self) -> None:
        """Remove all registered mock responses."""
        self._mock_responses.clear()


class ConcurrentSubprocessExecutor:
    """Coordinate multiple asynchronous subprocess executions."""

    def __init__(
        self,
        adapter: AsyncSubprocessProtocol,
        max_concurrent: int = 3,
        retry_policy: dict[str, Any] | None = None
    ) -> None:
        """Initialise the concurrent executor.

        Args:
            adapter (AsyncSubprocessProtocol): Adapter used for command
                execution.
            max_concurrent (int): Maximum number of concurrent subprocesses.
            retry_policy (dict[str, Any] | None): Optional retry configuration
                containing ``max_retries`` and ``retry_delay`` keys.
        """
        self._adapter = adapter
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._retry_policy = retry_policy or {"max_retries": 2, "retry_delay": 1.0}
        self._logger = get_logger(__name__)

    async def execute_single(
        self,
        command: list[str],
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None
    ) -> SubprocessResult:
        """Execute a single command while respecting concurrency limits.

        Args:
            command (list[str]): Command arguments.
            working_dir (Path): Working directory for command execution.
            env (dict[str, str] | None): Optional environment overrides.
            timeout (int | None): Optional timeout in seconds.

        Returns:
            SubprocessResult: Execution result produced by the adapter.
        """
        async with self._semaphore:
            return await self._adapter.execute(command, working_dir, env, timeout)

    async def execute_concurrent(
        self,
        commands: list[tuple[list[str], Path, dict[str, str] | None, int | None]]
    ) -> list[SubprocessResult]:
        """Execute multiple commands concurrently.

        Args:
            commands (list[tuple[list[str], Path, dict[str, str] | None, int | None]]):
                Sequence of command tuples consisting of arguments, working
                directory, environment overrides and timeout.

        Returns:
            list[SubprocessResult]: Execution results in submission order.
        """
        tasks = [
            self.execute_single(cmd, work_dir, env, timeout)
            for cmd, work_dir, env, timeout in commands
        ]

        self._logger.info("並列実行開始: %d個のコマンド", len(tasks))
        start_time = time.time()

        results = await asyncio.gather(*tasks, return_exceptions=True)

        execution_time = time.time() - start_time
        self._logger.info("並列実行完了: %s秒", execution_time)

        # 例外を適切なSubprocessResultに変換
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                cmd, work_dir, _, _ = commands[i]
                processed_results.append(SubprocessResult(
                    stdout="",
                    stderr=f"Concurrent execution failed: {result!s}",
                    return_code=-1,
                    command=cmd,
                    working_dir=work_dir,
                    execution_time=0.0
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def execute_with_retry(
        self,
        command: list[str],
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None
    ) -> SubprocessResult:
        """Execute a command with simple retry semantics.

        Args:
            command (list[str]): Command arguments.
            working_dir (Path): Working directory for command execution.
            env (dict[str, str] | None): Optional environment overrides.
            timeout (int | None): Optional timeout in seconds.

        Returns:
            SubprocessResult: Execution result produced by the adapter.
        """
        max_retries = self._retry_policy["max_retries"]
        retry_delay = self._retry_policy["retry_delay"]

        for attempt in range(max_retries + 1):
            result = await self.execute_single(command, working_dir, env, timeout)

            # 成功時は即座に返す
            if result.return_code == 0:
                return result

            # 最後の試行でない場合はリトライ
            if attempt < max_retries:
                self._logger.warning(
                    "コマンド実行失敗 (試行 %d/%d): %s",
                    attempt + 1, max_retries + 1, " ".join(command)
                )
                await asyncio.sleep(retry_delay)

        return result


def create_async_subprocess_adapter(mock_mode: bool = False) -> AsyncSubprocessProtocol:
    """Factory helper that returns an async subprocess adapter.

    Args:
        mock_mode (bool): When ``True`` the mock adapter is returned instead of
            the concrete implementation.

    Returns:
        AsyncSubprocessProtocol: Adapter instance suitable for asynchronous
        command execution.
    """
    if mock_mode:
        return AsyncMockSubprocessAdapter()
    return AsyncSubprocessAdapter()


def create_concurrent_executor(
    mock_mode: bool = False,
    max_concurrent: int = 3,
    retry_policy: dict[str, Any] | None = None
) -> ConcurrentSubprocessExecutor:
    """Factory helper that returns a concurrent executor.

    Args:
        mock_mode (bool): When ``True`` use the mock subprocess adapter.
        max_concurrent (int): Maximum number of concurrent subprocesses.
        retry_policy (dict[str, Any] | None): Optional retry policy override.

    Returns:
        ConcurrentSubprocessExecutor: Executor configured with the requested
        adapter and concurrency settings.
    """
    adapter = create_async_subprocess_adapter(mock_mode)
    return ConcurrentSubprocessExecutor(adapter, max_concurrent, retry_policy)
