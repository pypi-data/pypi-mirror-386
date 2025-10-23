"""SubprocessAdapterのユニットテスト

subprocess実行の抽象化とモック機能をテスト
"""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from mcp_servers.noveler.core.subprocess_adapter import (
    SubprocessResult,
    SubprocessAdapter,
    MockSubprocessAdapter,
    SubprocessExecutor,
    create_subprocess_adapter
)


class TestSubprocessResult:
    """SubprocessResultのテストクラス"""

    def test_subprocess_result_initialization(self):
        """SubprocessResult初期化テスト"""
        result = SubprocessResult(
            stdout="test output",
            stderr="test error",
            return_code=0,
            command=["echo", "test"],
            working_dir=Path("/tmp"),
            execution_time=1.5
        )

        assert result.stdout == "test output"
        assert result.stderr == "test error"
        assert result.return_code == 0
        assert result.command == ["echo", "test"]
        assert result.working_dir == Path("/tmp")
        assert result.execution_time == 1.5


class TestMockSubprocessAdapter:
    """MockSubprocessAdapterのテストクラス"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.mock_adapter = MockSubprocessAdapter()

    def test_mock_adapter_default_response(self):
        """デフォルトモックレスポンステスト"""
        command = ["test", "command"]
        working_dir = Path("/tmp")

        result = self.mock_adapter.execute(command, working_dir)

        assert result.stdout == "Mock output"
        assert result.stderr == ""
        assert result.return_code == 0
        assert result.command == command
        assert result.working_dir == working_dir
        assert result.execution_time == 0.1

    def test_mock_adapter_custom_response(self):
        """カスタムモックレスポンステスト"""
        self.mock_adapter.set_mock_response(
            "test",
            stdout="Custom output",
            stderr="Custom error",
            return_code=1,
            execution_time=2.0
        )

        command = ["test", "arg1", "arg2"]
        working_dir = Path("/home")

        result = self.mock_adapter.execute(command, working_dir)

        assert result.stdout == "Custom output"
        assert result.stderr == "Custom error"
        assert result.return_code == 1
        assert result.command == command
        assert result.working_dir == working_dir
        assert result.execution_time == 2.0

    def test_mock_adapter_execution_history(self):
        """実行履歴記録テスト"""
        commands = [
            (["cmd1", "arg1"], Path("/path1"), None),
            (["cmd2", "arg2"], Path("/path2"), {"ENV": "test"}),
        ]

        for command, working_dir, env in commands:
            self.mock_adapter.execute(command, working_dir, env)

        history = self.mock_adapter.get_execution_history()

        assert len(history) == 2
        assert history[0] == (["cmd1", "arg1"], Path("/path1"), None)
        assert history[1] == (["cmd2", "arg2"], Path("/path2"), {"ENV": "test"})

    def test_mock_adapter_clear_history(self):
        """履歴クリアテスト"""
        self.mock_adapter.execute(["test"], Path("/tmp"))
        assert len(self.mock_adapter.get_execution_history()) == 1

        self.mock_adapter.clear_history()
        assert len(self.mock_adapter.get_execution_history()) == 0

    def test_mock_adapter_clear_responses(self):
        """レスポンスクリアテスト"""
        self.mock_adapter.set_mock_response("test", stdout="Custom")

        # カスタムレスポンス確認
        result1 = self.mock_adapter.execute(["test"], Path("/tmp"))
        assert result1.stdout == "Custom"

        # レスポンスクリア後はデフォルトに戻る
        self.mock_adapter.clear_mock_responses()
        result2 = self.mock_adapter.execute(["test"], Path("/tmp"))
        assert result2.stdout == "Mock output"


class TestSubprocessAdapter:
    """SubprocessAdapterのテストクラス（実際のsubprocess呼び出しなしでテスト）"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.adapter = SubprocessAdapter(timeout_default=60)

    @patch('subprocess.run')
    def test_subprocess_adapter_success(self, mock_run):
        """成功時のsubprocess実行テスト"""
        # subprocess.runのモック設定
        mock_result = Mock()
        mock_result.stdout = "Success output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        command = ["echo", "test"]
        working_dir = Path("/tmp")

        result = self.adapter.execute(command, working_dir)

        assert result.stdout == "Success output"
        assert result.stderr == ""
        assert result.return_code == 0
        assert result.command == command
        assert result.working_dir == working_dir
        assert result.execution_time >= 0

        # subprocess.runが正しく呼ばれたか確認
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == command
        assert call_args[1]['cwd'] == working_dir

    @patch('subprocess.run')
    def test_subprocess_adapter_with_env(self, mock_run):
        """環境変数付きsubprocess実行テスト"""
        mock_result = Mock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        command = ["env", "test"]
        working_dir = Path("/tmp")
        env = {"TEST_VAR": "test_value"}

        with patch('os.environ', {"EXISTING": "value"}):
            result = self.adapter.execute(command, working_dir, env)

        assert result.return_code == 0

        # 環境変数がマージされて渡されたか確認
        call_args = mock_run.call_args
        passed_env = call_args[1]['env']
        assert "TEST_VAR" in passed_env
        assert passed_env["TEST_VAR"] == "test_value"
        assert "EXISTING" in passed_env  # 既存環境変数も含まれる

    @patch('subprocess.run')
    def test_subprocess_adapter_timeout(self, mock_run):
        """タイムアウト処理テスト"""
        # TimeoutExpiredエラーを発生させる
        mock_run.side_effect = subprocess.TimeoutExpired(
            ["slow", "command"], timeout=30
        )

        command = ["slow", "command"]
        working_dir = Path("/tmp")

        result = self.adapter.execute(command, working_dir, timeout=30)

        assert result.return_code == -1
        assert "timed out" in result.stderr
        assert result.execution_time >= 0

    @patch('subprocess.run')
    def test_subprocess_adapter_exception(self, mock_run):
        """例外処理テスト"""
        mock_run.side_effect = OSError("Permission denied")

        command = ["failed", "command"]
        working_dir = Path("/tmp")

        result = self.adapter.execute(command, working_dir)

        assert result.return_code == -1
        assert "Execution failed" in result.stderr
        assert "Permission denied" in result.stderr


class TestSubprocessExecutor:
    """SubprocessExecutorのテストクラス"""

    def setup_method(self):
        """各テストメソッド前の初期化"""
        self.mock_adapter = MockSubprocessAdapter()
        self.executor = SubprocessExecutor(self.mock_adapter)

    def test_execute_with_validation_success(self):
        """バリデーション成功テスト"""
        self.mock_adapter.set_mock_response("test", return_code=0)

        command = ["test", "command"]
        working_dir = Path("/tmp")
        expected_return_codes = [0]

        result = self.executor.execute_with_validation(
            command, working_dir, expected_return_codes=expected_return_codes
        )

        assert result.return_code == 0

    def test_execute_with_validation_failure(self):
        """バリデーション失敗テスト"""
        self.mock_adapter.set_mock_response("test", return_code=1)

        command = ["test", "command"]
        working_dir = Path("/tmp")
        expected_return_codes = [0]

        with pytest.raises(RuntimeError) as exc_info:
            self.executor.execute_with_validation(
                command, working_dir, expected_return_codes=expected_return_codes
            )

        assert "unexpected return code 1" in str(exc_info.value)
        assert "Expected: [0]" in str(exc_info.value)

    @patch('time.sleep')  # sleepをモック化して高速テスト
    def test_execute_with_retry_success_first_try(self, mock_sleep):
        """リトライ成功（初回）テスト"""
        self.mock_adapter.set_mock_response("test", return_code=0)

        command = ["test", "command"]
        working_dir = Path("/tmp")

        result = self.executor.execute_with_retry(
            command, working_dir, max_retries=3
        )

        assert result.return_code == 0
        mock_sleep.assert_not_called()  # sleepは呼ばれない

    @patch('time.sleep')
    def test_execute_with_retry_success_second_try(self, mock_sleep):
        """リトライ成功（2回目）テスト"""
        # 1回目は失敗、2回目は成功するようにモック設定
        call_count = 0
        def side_effect_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return SubprocessResult("", "error", 1, [], Path("/tmp"))
            else:
                return SubprocessResult("success", "", 0, [], Path("/tmp"))

        self.mock_adapter.execute = side_effect_execute

        command = ["test", "command"]
        working_dir = Path("/tmp")

        result = self.executor.execute_with_retry(
            command, working_dir, max_retries=3, retry_delay=0.1
        )

        assert result.return_code == 0
        assert result.stdout == "success"
        mock_sleep.assert_called_once_with(0.1)

    @patch('time.sleep')
    def test_execute_with_retry_max_retries_reached(self, mock_sleep):
        """最大リトライ回数到達テスト"""
        self.mock_adapter.set_mock_response("test", return_code=1)

        command = ["test", "command"]
        working_dir = Path("/tmp")

        result = self.executor.execute_with_retry(
            command, working_dir, max_retries=2, retry_delay=0.1
        )

        assert result.return_code == 1
        assert mock_sleep.call_count == 2  # 2回リトライしたのでsleepは2回


class TestSubprocessAdapterFactory:
    """create_subprocess_adapter関数のテスト"""

    def test_create_real_adapter(self):
        """実際のアダプター作成テスト"""
        adapter = create_subprocess_adapter(mock_mode=False)

        assert isinstance(adapter, SubprocessAdapter)

    def test_create_mock_adapter(self):
        """モックアダプター作成テスト"""
        adapter = create_subprocess_adapter(mock_mode=True)

        assert isinstance(adapter, MockSubprocessAdapter)


class TestSubprocessAdapterIntegration:
    """統合テスト（軽量コマンドでの実際実行）"""

    def test_real_adapter_echo_command(self):
        """実際のechoコマンド実行テスト"""
        adapter = SubprocessAdapter()
        command = ["echo", "Hello, World!"]
        working_dir = Path.cwd()

        result = adapter.execute(command, working_dir, timeout=5)

        assert result.return_code == 0
        assert "Hello, World!" in result.stdout
        assert result.stderr == ""
        assert result.execution_time >= 0

    def test_real_adapter_false_command(self):
        """失敗コマンド実行テスト"""
        adapter = SubprocessAdapter()
        command = ["false"]  # 常に終了コード1で終了するコマンド
        working_dir = Path.cwd()

        result = adapter.execute(command, working_dir, timeout=5)

        assert result.return_code == 1
        assert result.execution_time >= 0
