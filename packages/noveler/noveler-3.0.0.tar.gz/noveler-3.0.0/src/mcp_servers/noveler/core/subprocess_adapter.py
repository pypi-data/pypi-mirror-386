"""Provide concrete and mockable subprocess adapters for the CLI tests."""

import subprocess
from pathlib import Path
from typing import Protocol


class SubprocessResult:
    """Container that stores the outcome of a subprocess execution."""

    def __init__(
        self,
        stdout: str,
        stderr: str,
        return_code: int,
        command: list[str],
        working_dir: Path,
        execution_time: float = 0.0
    ) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.command = command
        self.working_dir = working_dir
        self.execution_time = execution_time


class SubprocessProtocol(Protocol):
    """Protocol describing the callable interface for subprocess adapters."""

    def execute(
        self,
        command: list[str],
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None
    ) -> SubprocessResult:
        """Execute the provided command.

        Args:
            command (list[str]): Command arguments.
            working_dir (Path): Working directory for the subprocess.
            env (dict[str, str] | None): Optional environment overrides.
            timeout (int | None): Optional timeout in seconds.

        Returns:
            SubprocessResult: Execution payload emitted by the adapter.
        """
        ...


class SubprocessAdapter:
    """Adapter that proxies to :func:`subprocess.run` with safe defaults."""

    def __init__(self, timeout_default: int = 300) -> None:
        """Initialise the concrete subprocess adapter.

        Args:
            timeout_default (int): Default timeout in seconds applied when no
                specific timeout is passed to :meth:`execute`.
        """
        self._timeout_default = timeout_default

    def execute(
        self,
        command: list[str],
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None
    ) -> SubprocessResult:
        """Execute the command and capture stdout/stderr.

        Args:
            command (list[str]): Command arguments.
            working_dir (Path): Working directory for command execution.
            env (dict[str, str] | None): Optional environment overrides.
            timeout (int | None): Optional timeout in seconds. Defaults to the
                ``timeout_default`` passed to the constructor.

        Returns:
            SubprocessResult: Captured outputs, return code and metadata.
        """
        import time
        start_time = time.time()

        try:
            # 環境変数のマージ
            merged_env = {}
            if env:
                import os
                merged_env = os.environ.copy()
                merged_env.update(env)

            # subprocess実行
            result = subprocess.run(
                command,
                cwd=working_dir,
                env=merged_env if env else None,
                capture_output=True,
                text=True,
                timeout=timeout or self._timeout_default,
                check=False
            )

            execution_time = time.time() - start_time

            return SubprocessResult(
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                command=command,
                working_dir=working_dir,
                execution_time=execution_time
            )

        except subprocess.TimeoutExpired as e:
            execution_time = time.time() - start_time
            return SubprocessResult(
                stdout=e.stdout.decode("utf-8") if e.stdout else "",
                stderr=f"Command timed out after {timeout or self._timeout_default} seconds",
                return_code=-1,
                command=command,
                working_dir=working_dir,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return SubprocessResult(
                stdout="",
                stderr=f"Execution failed: {e!s}",
                return_code=-1,
                command=command,
                working_dir=working_dir,
                execution_time=execution_time
            )


class MockSubprocessAdapter:
    """In-memory subprocess adapter used by unit tests."""

    def __init__(self) -> None:
        self._mock_responses: dict[str, SubprocessResult] = {}
        self._execution_history: list[tuple[list[str], Path, dict[str, str] | None]] = []

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

    def execute(
        self,
        command: list[str],
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None
    ) -> SubprocessResult:
        """Return a preconfigured response instead of spawning a subprocess.

        Args:
            command (list[str]): Command arguments.
            working_dir (Path): Working directory for command execution.
            env (dict[str, str] | None): Optional environment overrides (stored
                with the execution history for later inspection).
            timeout (int | None): Ignored but accepted for API compatibility.

        Returns:
            SubprocessResult: Mocked subprocess result.
        """
        # 実行履歴を記録
        self._execution_history.append((command.copy(), working_dir, env))

        # コマンドパターンにマッチするモックレスポンスを探す
        if command:
            command_key = command[0]
            if command_key in self._mock_responses:
                mock_result = self._mock_responses[command_key]
                # 実際のコマンドと作業ディレクトリで更新
                return SubprocessResult(
                    stdout=mock_result.stdout,
                    stderr=mock_result.stderr,
                    return_code=mock_result.return_code,
                    command=command,
                    working_dir=working_dir,
                    execution_time=mock_result.execution_time
                )

        # デフォルトのモックレスポンス
        return SubprocessResult(
            stdout="Mock output",
            stderr="",
            return_code=0,
            command=command,
            working_dir=working_dir,
            execution_time=0.1
        )

    def get_execution_history(self) -> list[tuple[list[str], Path, dict[str, str] | None]]:
        """実行履歴を取得

        Returns:
            実行履歴のリスト
        """
        return self._execution_history.copy()

    def clear_history(self):
        """実行履歴をクリア"""
        self._execution_history.clear()

    def clear_mock_responses(self):
        """モックレスポンスをクリア"""
        self._mock_responses.clear()


class SubprocessExecutor:
    """SubprocessAdapterを使用した高レベル実行器"""

    def __init__(self, adapter: SubprocessProtocol) -> None:
        """初期化

        Args:
            adapter: 使用するSubprocessAdapter
        """
        self._adapter = adapter

    def execute_with_validation(
        self,
        command: list[str],
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None,
        expected_return_codes: list[int] | None = None
    ) -> SubprocessResult:
        """バリデーション付きでコマンドを実行

        Args:
            command: 実行するコマンド配列
            working_dir: 作業ディレクトリ
            env: 環境変数
            timeout: タイムアウト秒数
            expected_return_codes: 期待する終了コードのリスト

        Returns:
            実行結果

        Raises:
            RuntimeError: 予期しない終了コードの場合
        """
        result = self._adapter.execute(command, working_dir, env, timeout)

        if expected_return_codes is not None:
            if result.return_code not in expected_return_codes:
                msg = (
                    f"Command failed with unexpected return code {result.return_code}. "
                    f"Expected: {expected_return_codes}. "
                    f"Command: {' '.join(command)}. "
                    f"Error: {result.stderr}"
                )
                raise RuntimeError(
                    msg
                )

        return result

    def execute_with_retry(
        self,
        command: list[str],
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout: int | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> SubprocessResult:
        """リトライ付きでコマンドを実行

        Args:
            command: 実行するコマンド配列
            working_dir: 作業ディレクトリ
            env: 環境変数
            timeout: タイムアウト秒数
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）

        Returns:
            実行結果
        """
        import time

        last_result = None

        for attempt in range(max_retries + 1):
            result = self._adapter.execute(command, working_dir, env, timeout)

            # 成功した場合はすぐに返す
            if result.return_code == 0:
                return result

            last_result = result

            # 最後の試行でない場合はリトライ
            if attempt < max_retries:
                time.sleep(retry_delay)

        return last_result


def create_subprocess_adapter(mock_mode: bool = False) -> SubprocessProtocol:
    """SubprocessAdapterファクトリー関数

    Args:
        mock_mode: Trueの場合モックアダプターを返す

    Returns:
        SubprocessAdapter インスタンス
    """
    if mock_mode:
        return MockSubprocessAdapter()
    return SubprocessAdapter()
