"""18ステップ執筆システムの統合テスト

writeコマンド実行時の18ステップ処理、サブタスク登録、
各ステップの実行状況の統合的な動作を検証するテストケース群
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.mcp_servers.noveler.main import execute_novel_command
from noveler.presentation.mcp.adapters.mcp_protocol_adapter import MCPProtocolAdapter


class TestEighteenStepIntegration:
    """18ステップ執筆システム統合テストクラス"""

    @pytest.fixture
    def temp_project_dir(self):
        """テスト用の一時プロジェクトディレクトリ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()

            # プロジェクト構造を作成
            (project_path / "episodes").mkdir()
            (project_path / "settings").mkdir()
            (project_path / "templates").mkdir()

            yield str(project_path)

    @pytest.fixture
    def mock_eighteen_step_service_detailed(self):
        """詳細な18ステップサービスのモック"""
        mock = AsyncMock()

        # 18ステップの詳細な実行結果をシミュレート
        step_results = []
        for i in range(1, 18):
            step_results.append({
                "step_number": i,
                "step_name": f"Step{i:02d}",
                "status": "completed",
                "duration": 0.5 + (i * 0.1),
                "output": f"Step {i} completed successfully",
                "subtasks": [
                    {"name": f"Subtask {i}-1", "status": "completed"},
                    {"name": f"Subtask {i}-2", "status": "completed"}
                ]
            })

        mock.execute_eighteen_step_writing.return_value = {
            "success": True,
            "episode": 1,
            "completed_steps": 17,
            "total_steps": 17,
            "output_file": "/test/project/episodes/001.md",
            "execution_time": 15.8,
            "step_results": step_results,
            "metadata": {
                "word_count": 3500,
                "character_count": 12000,
                "scene_count": 5
            }
        }
        return mock

    @pytest.fixture
    def mock_task_manager(self):
        """タスクマネージャーのモック"""
        mock = Mock()
        mock.register_subtasks = Mock()
        mock.update_task_progress = Mock()
        mock.complete_task = Mock()
        mock.get_task_status = Mock(return_value="in_progress")
        return mock

    @pytest.fixture
    def mock_console_with_progress(self):
        """プログレス表示付きコンソールのモック"""
        mock = Mock()
        mock.print_info = Mock()
        mock.print_success = Mock()
        mock.print_error = Mock()
        mock.print_progress = Mock()
        mock.update_progress = Mock()
        return mock

    @pytest.mark.asyncio
    async def test_full_eighteen_step_execution_flow(
        self, temp_project_dir, mock_eighteen_step_service_detailed,
        mock_task_manager, mock_console_with_progress
    ):
        """完全な18ステップ実行フローの統合テスト"""
        with patch("src.mcp_servers.noveler.main.get_console", return_value=mock_console_with_progress), \
             patch("src.mcp_servers.noveler.main.PATH_SERVICE_AVAILABLE", False), \
             patch("src.mcp_servers.noveler.main.convert_cli_to_json", lambda x: x), \
             patch("noveler.application.use_cases.integrated_writing_use_case.IntegratedWritingUseCase.execute", mock_eighteen_step_service_detailed.execute_eighteen_step_writing), \
             patch("noveler.infrastructure.task_management.task_manager.TaskManager", return_value=mock_task_manager):

            # 実行
            result = await execute_novel_command(
                command="write 1",
                project_root=temp_project_dir,
                options={"dry_run": False}
            )

            # 18ステップ実行の完了を検証
            assert result["jsonrpc"] == "2.0"
            assert result["result"]["success"] is True

            data = result["result"]["data"]
            assert data["status"] == "success"
            assert data["operation"] == "eighteen_step_writing"
            assert data["result"]["completed_steps"] == 17
            assert data["result"]["total_steps"] == 17

            # 詳細な実行結果の検証
            step_results = data["result"]["step_results"]
            assert len(step_results) == 17

            for i, step in enumerate(step_results, 1):
                assert step["step_number"] == i
                assert step["status"] == "completed"
                assert "subtasks" in step

            # サブタスク登録が呼び出されたことを検証
            mock_task_manager.register_subtasks.assert_called()

    @pytest.mark.asyncio
    async def test_eighteen_step_progress_tracking(
        self, temp_project_dir, mock_console_with_progress
    ):
        """18ステップ進捗追跡の統合テスト"""
        # プログレス追跡付きのモック
        mock_service = AsyncMock()
        progress_updates = []

        async def mock_execute_with_progress(*args, **kwargs):
            # 各ステップの進捗をシミュレート
            for i in range(1, 18):
                progress_updates.append({
                    "current_step": i,
                    "total_steps": 17,
                    "step_name": f"Step{i:02d}",
                    "progress_percentage": (i / 17) * 100
                })
                # プログレスコールバック呼び出しをシミュレート
                if hasattr(kwargs.get('progress_callback'), '__call__'):
                    await kwargs['progress_callback'](progress_updates[-1])

            return {
                "success": True,
                "episode": 1,
                "completed_steps": 17,
                "total_steps": 17,
                "progress_updates": progress_updates
            }

        mock_service.execute_eighteen_step_writing = mock_execute_with_progress

        with patch("src.mcp_servers.noveler.main.get_console", return_value=mock_console_with_progress), \
             patch("src.mcp_servers.noveler.main.PATH_SERVICE_AVAILABLE", False), \
             patch("src.mcp_servers.noveler.main.convert_cli_to_json", lambda x: x), \
             patch("noveler.application.use_cases.integrated_writing_use_case.IntegratedWritingUseCase.execute", mock_service.execute_eighteen_step_writing):

            result = await execute_novel_command(
                command="write 1",
                project_root=temp_project_dir,
                options={}
            )

            # プログレス追跡が適切に動作したことを検証
            assert result["result"]["success"] is True
            assert len(progress_updates) == 17

    @pytest.mark.asyncio
    async def test_eighteen_step_partial_execution_recovery(
        self, temp_project_dir, mock_console_with_progress
    ):
        """18ステップ部分実行・復旧の統合テスト"""
        # 途中でエラーが発生するシナリオ
        mock_service = AsyncMock()

        async def mock_execute_with_partial_failure(*args, **kwargs):
            # ステップ10で失敗するシミュレート
            completed_steps = []
            for i in range(1, 11):  # ステップ10まで実行
                completed_steps.append({
                    "step_number": i,
                    "status": "completed" if i < 10 else "failed",
                    "error": "Step 10 execution failed" if i == 10 else None
                })

            return {
                "success": False,
                "episode": 1,
                "completed_steps": 9,  # 9ステップまで完了
                "total_steps": 17,
                "failed_step": 10,
                "error": "Step 10 execution failed",
                "step_results": completed_steps,
                "recovery_possible": True
            }

        mock_service.execute_eighteen_step_writing = mock_execute_with_partial_failure

        with patch("src.mcp_servers.noveler.main.get_console", return_value=mock_console_with_progress), \
             patch("src.mcp_servers.noveler.main.PATH_SERVICE_AVAILABLE", False), \
             patch("src.mcp_servers.noveler.main.convert_cli_to_json", lambda x: x), \
             patch("noveler.application.use_cases.integrated_writing_use_case.IntegratedWritingUseCase.execute", mock_service.execute_eighteen_step_writing):

            result = await execute_novel_command(
                command="write 1",
                project_root=temp_project_dir,
                options={}
            )

            # 部分実行とエラー状況が適切に報告されることを検証
            assert result["result"]["success"] is False

            data = result["result"]["data"]
            assert data["status"] == "error"
            assert "Step 10 execution failed" in str(data["error_details"])

            # 部分実行結果の検証
            if "result" in data:
                assert data["result"]["completed_steps"] == 9
                assert data["result"]["failed_step"] == 10

    @pytest.mark.asyncio
    async def test_eighteen_step_dry_run_mode(
        self, temp_project_dir, mock_console_with_progress
    ):
        """18ステップドライランモードの統合テスト"""
        mock_service = AsyncMock()

        async def mock_dry_run_execution(*args, **kwargs):
            # ドライランモードでの実行をシミュレート
            return {
                "success": True,
                "dry_run": True,
                "episode": 1,
                "estimated_steps": 17,
                "estimated_duration": 16.5,
                "preview_results": [
                    {"step": i, "estimated_duration": 0.5 + (i * 0.1), "dependencies": []}
                    for i in range(1, 18)
                ],
                "would_create_files": [
                    "/test/project/episodes/001.md",
                    "/test/project/episodes/001_metadata.json"
                ]
            }

        mock_service.execute_eighteen_step_writing = mock_dry_run_execution

        with patch("src.mcp_servers.noveler.main.get_console", return_value=mock_console_with_progress), \
             patch("src.mcp_servers.noveler.main.PATH_SERVICE_AVAILABLE", False), \
             patch("src.mcp_servers.noveler.main.convert_cli_to_json", lambda x: x), \
             patch("noveler.application.use_cases.integrated_writing_use_case.IntegratedWritingUseCase.execute", mock_service.execute_eighteen_step_writing):

            result = await execute_novel_command(
                command="write 1",
                project_root=temp_project_dir,
                options={"dry_run": True}
            )

            # ドライランモードが適切に実行されることを検証
            assert result["result"]["success"] is True

            data = result["result"]["data"]
            assert data["result"]["dry_run"] is True
            assert "estimated_duration" in data["result"]
            assert "would_create_files" in data["result"]

    @pytest.mark.asyncio
    async def test_eighteen_step_with_custom_options(
        self, temp_project_dir, mock_console_with_progress
    ):
        """18ステップカスタムオプション付き実行の統合テスト"""
        custom_options = {
            "template": "custom_template.md",
            "word_count_target": 4000,
            "style": "fantasy",
            "pov": "third_person",
            "enable_auto_save": True,
            "backup_enabled": True
        }

        mock_service = AsyncMock()
        mock_service.execute_eighteen_step_writing.return_value = {
            "success": True,
            "episode": 1,
            "completed_steps": 17,
            "total_steps": 17,
            "options_applied": custom_options,
            "final_word_count": 4050,
            "style_compliance": "fantasy",
            "pov_consistency": "third_person"
        }

        with patch("src.mcp_servers.noveler.main.get_console", return_value=mock_console_with_progress), \
             patch("src.mcp_servers.noveler.main.PATH_SERVICE_AVAILABLE", False), \
             patch("src.mcp_servers.noveler.main.convert_cli_to_json", lambda x: x), \
             patch("noveler.application.use_cases.integrated_writing_use_case.IntegratedWritingUseCase.execute", mock_service.execute_eighteen_step_writing):

            result = await execute_novel_command(
                command="write 1",
                project_root=temp_project_dir,
                options=custom_options
            )

            # カスタムオプションが適切に処理されることを検証
            assert result["result"]["success"] is True

            data = result["result"]["data"]
            assert data["result"]["options_applied"] == custom_options
            assert "final_word_count" in data["result"]

    @pytest.mark.asyncio
    async def test_eighteen_step_concurrent_executions(
        self, temp_project_dir, mock_console_with_progress
    ):
        """18ステップ並行実行の統合テスト"""
        import asyncio

        mock_service = AsyncMock()

        execution_count = 0
        async def mock_concurrent_execution(*args, **kwargs):
            nonlocal execution_count
            execution_count += 1
            episode_num = execution_count

            # 並行実行をシミュレート
            await asyncio.sleep(0.1)  # 短い処理時間

            return {
                "success": True,
                "episode": episode_num,
                "completed_steps": 17,
                "total_steps": 17,
                "execution_id": f"exec_{episode_num}",
                "concurrent_execution": True
            }

        mock_service.execute_eighteen_step_writing = mock_concurrent_execution

        with patch("src.mcp_servers.noveler.main.get_console", return_value=mock_console_with_progress), \
             patch("src.mcp_servers.noveler.main.PATH_SERVICE_AVAILABLE", False), \
             patch("src.mcp_servers.noveler.main.convert_cli_to_json", lambda x: x), \
             patch("noveler.application.use_cases.integrated_writing_use_case.IntegratedWritingUseCase.execute", mock_service.execute_eighteen_step_writing):

            # 複数エピソードの並行実行
            tasks = [
                execute_novel_command("write 1", temp_project_dir, {}),
                execute_novel_command("write 2", temp_project_dir, {}),
                execute_novel_command("write 3", temp_project_dir, {}),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # すべての並行実行が成功することを検証
            for i, result in enumerate(results, 1):
                assert not isinstance(result, Exception)
                assert result["result"]["success"] is True
                assert result["result"]["data"]["result"]["episode"] == i

    @pytest.mark.asyncio
    async def test_eighteen_step_resource_management(
        self, temp_project_dir, mock_console_with_progress
    ):
        """18ステップリソース管理の統合テスト"""
        class ResourceManager:
            def __init__(self):
                self.opened_files = []
                self.memory_allocated = 0
                self.connections_opened = []

            def open_file(self, filename):
                self.opened_files.append(filename)

            def close_file(self, filename):
                if filename in self.opened_files:
                    self.opened_files.remove(filename)

            def allocate_memory(self, size):
                self.memory_allocated += size

            def deallocate_memory(self, size):
                self.memory_allocated -= size

        resource_manager = ResourceManager()

        mock_service = AsyncMock()

        async def mock_execution_with_resources(*args, **kwargs):
            # リソースを使用した処理をシミュレート
            try:
                resource_manager.open_file("template.md")
                resource_manager.open_file("output.md")
                resource_manager.allocate_memory(1024 * 1024)  # 1MB

                # 処理をシミュレート
                await asyncio.sleep(0.1)

                return {
                    "success": True,
                    "episode": 1,
                    "completed_steps": 17,
                    "total_steps": 17,
                    "resources_used": {
                        "files_opened": len(resource_manager.opened_files),
                        "memory_allocated": resource_manager.memory_allocated
                    }
                }
            finally:
                # リソースクリーンアップ
                for filename in resource_manager.opened_files.copy():
                    resource_manager.close_file(filename)
                resource_manager.deallocate_memory(resource_manager.memory_allocated)

        mock_service.execute_eighteen_step_writing = mock_execution_with_resources

        with patch("src.mcp_servers.noveler.main.get_console", return_value=mock_console_with_progress), \
             patch("src.mcp_servers.noveler.main.PATH_SERVICE_AVAILABLE", False), \
             patch("src.mcp_servers.noveler.main.convert_cli_to_json", lambda x: x), \
             patch("noveler.application.use_cases.integrated_writing_use_case.IntegratedWritingUseCase.execute", mock_service.execute_eighteen_step_writing):

            result = await execute_novel_command(
                command="write 1",
                project_root=temp_project_dir,
                options={}
            )

            # リソース管理が適切に行われることを検証
            assert result["result"]["success"] is True

            # リソースがクリーンアップされていることを確認
            assert len(resource_manager.opened_files) == 0
            assert resource_manager.memory_allocated == 0
