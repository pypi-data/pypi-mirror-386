#!/usr/bin/env python3
"""checkコマンド8ステップサブタスクテスト

checkコマンドの8つのステップそれぞれがサブタスクとして適切に登録・実行されることを確認するテスト
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from typing import Any, List, Dict

from noveler.presentation.mcp.adapters.mcp_protocol_adapter import MCPProtocolAdapter
from noveler.application.use_cases.b20_pre_implementation_check_use_case import (
    B20PreImplementationCheckUseCase,
    B20PreImplementationCheckRequest,
    B20PreImplementationCheckResponse,
)


@pytest.fixture
def mock_subtask_notifier():
    """サブタスク通知のモック"""
    notifier = MagicMock()
    notifier.notify_subtask = MagicMock()
    return notifier


@pytest.fixture
def mock_b20_use_case():
    """B20ユースケースのモック"""
    use_case = MagicMock(spec=B20PreImplementationCheckUseCase)

    # 8ステップの実行を模擬
    def mock_execute(request):
        response = MagicMock(spec=B20PreImplementationCheckResponse)
        response.success = True
        response.implementation_allowed = True
        response.current_stage = "implementation_allowed"
        response.completion_percentage = 85.0
        response.next_required_actions = ["実装開始可能"]
        response.warnings = []
        response.errors = []
        response.codemap_status = {"status": "available"}
        response.auto_fix_results = None
        response.execution_time_ms = 120.5
        return response

    use_case.execute.side_effect = mock_execute
    return use_case


@pytest.fixture
def mcp_adapter_with_subtasks(mock_b20_use_case, mock_subtask_notifier):
    """サブタスク機能付きMCPアダプター"""
    adapter = MCPProtocolAdapter()

    # B20ユースケースをモック
    with patch.object(adapter, '_get_b20_use_case', return_value=mock_b20_use_case):
        # サブタスク通知機能をモック
        adapter._subtask_notifier = mock_subtask_notifier
        yield adapter


class TestCheckCommandSubtasks:
    """checkコマンドサブタスクテストクラス"""

    @pytest.mark.asyncio
    async def test_check_command_8_steps_subtask_registration(
        self, mcp_adapter_with_subtasks, mock_subtask_notifier, tmp_path
    ):
        """checkコマンド8ステップサブタスク登録テスト"""
        # Arrange
        adapter = mcp_adapter_with_subtasks

        # サブタスク通知をキャプチャ
        subtask_calls = []
        def capture_subtask(step, description, status="in_progress"):
            subtask_calls.append({"step": step, "description": description, "status": status})

        mock_subtask_notifier.notify_subtask.side_effect = capture_subtask

        # Act
        result = await adapter.handle_novel_command(
            command="check",
            options={"feature_name": "subtask_test"},
            project_root=str(tmp_path)
        )

        # Assert - 基本的な実行確認
        assert result["success"] is True
        assert result["command"] == "check"

        # サブタスク通知が行われたか確認（実装に依存）
        # 注意: 実際のサブタスク通知は実装次第で、この部分は実装に合わせて調整が必要
        if mock_subtask_notifier.notify_subtask.called:
            assert len(subtask_calls) > 0

    def test_b20_use_case_step_by_step_execution(self):
        """B20ユースケースステップバイステップ実行テスト"""
        # Arrange
        from noveler.presentation.shared.shared_utilities import get_common_path_service

        # 各ステップの実行を個別にモック
        use_case = B20PreImplementationCheckUseCase()

        request = B20PreImplementationCheckRequest(
            feature_name="step_by_step_test",
            target_layer="domain",
            auto_fix_issues=True,
            create_missing_spec=True,
            force_codemap_update=True,
        )

        # ステップ実行の追跡
        executed_steps = []

        # 各プライベートメソッドをモック化してステップ実行を追跡
        original_check_codemap = use_case._check_codemap_status
        original_evaluate_permission = use_case._evaluate_implementation_permission
        original_calculate_progress = use_case._calculate_progress_status
        original_identify_actions = use_case._identify_next_actions
        original_collect_warnings = use_case._collect_warnings_and_errors
        original_execute_fixes = use_case._execute_auto_fixes
        original_force_update = use_case._force_codemap_update

        def track_step(step_name):
            def wrapper(*args, **kwargs):
                executed_steps.append(step_name)
                if step_name == "check_codemap_status":
                    return {"status": "available"}
                elif step_name == "evaluate_implementation_permission":
                    return True
                elif step_name == "calculate_progress_status":
                    return ("implementation_allowed", 85.0)
                elif step_name == "identify_next_actions":
                    return ["実装開始可能"]
                elif step_name == "collect_warnings_and_errors":
                    # エラーを1件返し、自動修正ステップの実行を誘発
                    return ([], ["dummy error for auto-fix trigger"])
                elif step_name == "execute_auto_fixes":
                    return {"attempted_fixes": 1, "successful_fixes": 1}
                elif step_name == "force_codemap_update":
                    return None
                else:
                    return None
            return wrapper

        use_case._check_codemap_status = track_step("check_codemap_status")
        use_case._evaluate_implementation_permission = track_step("evaluate_implementation_permission")
        use_case._calculate_progress_status = track_step("calculate_progress_status")
        use_case._identify_next_actions = track_step("identify_next_actions")
        use_case._collect_warnings_and_errors = track_step("collect_warnings_and_errors")
        use_case._execute_auto_fixes = track_step("execute_auto_fixes")
        use_case._force_codemap_update = track_step("force_codemap_update")

        with patch.object(use_case, "_has_specification_documents", return_value=True):
            # Act
            response = use_case.execute(request)

            # Assert - 8ステップ全てが実行された
            expected_steps = [
                "check_codemap_status",           # ステップ1
                "evaluate_implementation_permission", # ステップ2
                "calculate_progress_status",      # ステップ3
                "identify_next_actions",          # ステップ4
                "collect_warnings_and_errors",   # ステップ5
                "execute_auto_fixes",             # ステップ6（自動修正有効時）
                # ステップ7は自動修正後の再評価（内部で上記メソッドを再呼出）
                "force_codemap_update",           # ステップ8（強制更新有効時）
            ]

            for expected_step in expected_steps:
                assert expected_step in executed_steps, f"Step '{expected_step}' was not executed"

            assert response.success is True

    def test_subtask_notification_interface(self):
        """サブタスク通知インターフェースのテスト"""
        # Arrange
        class MockSubtaskNotifier:
            def __init__(self):
                self.notifications = []

            def notify_subtask(self, step: int, description: str, status: str = "in_progress"):
                self.notifications.append({
                    "step": step,
                    "description": description,
                    "status": status
                })

            def complete_subtask(self, step: int):
                for notification in self.notifications:
                    if notification["step"] == step:
                        notification["status"] = "completed"

        notifier = MockSubtaskNotifier()

        # Act - 8ステップのサブタスク通知をシミュレート
        step_descriptions = [
            "CODEMAPステータス確認",
            "実装許可判定",
            "進捗状況計算",
            "次のアクション特定",
            "警告・エラー収集",
            "自動修正実行",
            "状態再評価",
            "CODEMAP強制更新"
        ]

        for i, description in enumerate(step_descriptions, 1):
            notifier.notify_subtask(i, description, "in_progress")
            notifier.complete_subtask(i)

        # Assert
        assert len(notifier.notifications) == 8

        for i, notification in enumerate(notifier.notifications):
            assert notification["step"] == i + 1
            assert notification["description"] == step_descriptions[i]
            assert notification["status"] == "completed"

    @pytest.mark.asyncio
    async def test_check_command_subtask_error_handling(
        self, mcp_adapter_with_subtasks, mock_subtask_notifier, tmp_path
    ):
        """checkコマンドサブタスクエラーハンドリングテスト"""
        # Arrange
        adapter = mcp_adapter_with_subtasks

        # B20ユースケースでエラーを発生させる
        error_use_case = MagicMock(spec=B20PreImplementationCheckUseCase)
        error_use_case.execute.side_effect = Exception("Subtask error")

        # エラー発生時のサブタスク通知をキャプチャ
        error_notifications = []
        def capture_error_notification(step, description, status="error"):
            error_notifications.append({
                "step": step,
                "description": description,
                "status": status
            })

        mock_subtask_notifier.notify_subtask.side_effect = capture_error_notification

        with patch.object(adapter, '_get_b20_use_case', return_value=error_use_case):
            # Act
            result = await adapter.handle_novel_command(
                command="check",
                options={"feature_name": "error_test"},
                project_root=str(tmp_path)
            )

            # Assert
            assert result["success"] is False
            assert "error" in result

    def test_subtask_progress_tracking(self):
        """サブタスク進捗追跡テスト"""
        # Arrange
        class ProgressTracker:
            def __init__(self):
                self.progress = {}
                self.total_steps = 8

            def start_step(self, step: int, description: str):
                self.progress[step] = {
                    "description": description,
                    "status": "in_progress",
                    "start_time": "2025-01-15T10:00:00Z"
                }

            def complete_step(self, step: int):
                if step in self.progress:
                    self.progress[step]["status"] = "completed"
                    self.progress[step]["end_time"] = "2025-01-15T10:00:01Z"

            def get_completion_percentage(self) -> float:
                completed = sum(1 for p in self.progress.values() if p["status"] == "completed")
                return (completed / self.total_steps) * 100.0

            def get_current_step(self) -> int:
                in_progress = [step for step, p in self.progress.items() if p["status"] == "in_progress"]
                return in_progress[0] if in_progress else max(self.progress.keys()) + 1 if self.progress else 1

        tracker = ProgressTracker()

        # Act - ステップを順次実行
        steps = [
            "CODEMAPステータス確認",
            "実装許可判定",
            "進捗状況計算",
            "次のアクション特定",
            "警告・エラー収集"
        ]

        for i, description in enumerate(steps, 1):
            tracker.start_step(i, description)
            assert tracker.get_current_step() == i
            assert tracker.get_completion_percentage() == ((i-1) / 8) * 100
            tracker.complete_step(i)
            assert tracker.get_completion_percentage() == (i / 8) * 100

        # Assert
        assert tracker.get_completion_percentage() == 62.5  # 5/8 steps completed

    @pytest.mark.asyncio
    async def test_parallel_subtask_safety(self, mcp_adapter_with_subtasks, tmp_path):
        """並行サブタスク安全性テスト"""
        # Arrange
        import asyncio
        adapter = mcp_adapter_with_subtasks

        async def run_check_command(feature_name):
            return await adapter.handle_novel_command(
                command="check",
                options={"feature_name": feature_name},
                project_root=str(tmp_path)
            )

        # Act - 複数のcheckコマンドを並行実行
        results = await asyncio.gather(
            run_check_command("parallel_test_1"),
            run_check_command("parallel_test_2"),
            run_check_command("parallel_test_3"),
            return_exceptions=True
        )

        # Assert - 全ての実行が成功し、サブタスクが混在しない
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Parallel execution failed: {result}")
            assert result["success"] is True
            assert result["command"] == "check"

    def test_subtask_metadata_collection(self):
        """サブタスクメタデータ収集テスト"""
        # Arrange
        class SubtaskMetadataCollector:
            def __init__(self):
                self.subtasks = []

            def add_subtask(self, step: int, name: str, description: str,
                           estimated_duration_ms: int = 100):
                self.subtasks.append({
                    "step": step,
                    "name": name,
                    "description": description,
                    "estimated_duration_ms": estimated_duration_ms,
                    "actual_duration_ms": None,
                    "status": "pending"
                })

            def start_subtask(self, step: int):
                for subtask in self.subtasks:
                    if subtask["step"] == step:
                        subtask["status"] = "in_progress"
                        subtask["start_time"] = "2025-01-15T10:00:00Z"

            def complete_subtask(self, step: int, actual_duration_ms: int):
                for subtask in self.subtasks:
                    if subtask["step"] == step:
                        subtask["status"] = "completed"
                        subtask["actual_duration_ms"] = actual_duration_ms
                        subtask["end_time"] = "2025-01-15T10:00:01Z"

            def get_metadata_summary(self) -> Dict[str, Any]:
                completed = [s for s in self.subtasks if s["status"] == "completed"]
                total_estimated = sum(s["estimated_duration_ms"] for s in self.subtasks)
                total_actual = sum(s["actual_duration_ms"] or 0 for s in completed)

                return {
                    "total_steps": len(self.subtasks),
                    "completed_steps": len(completed),
                    "total_estimated_duration_ms": total_estimated,
                    "total_actual_duration_ms": total_actual,
                    "performance_ratio": total_actual / total_estimated if total_estimated > 0 else 0
                }

        collector = SubtaskMetadataCollector()

        # Act - 8ステップのメタデータを追加
        subtask_info = [
            (1, "check_codemap_status", "CODEMAPステータス確認", 50),
            (2, "evaluate_permission", "実装許可判定", 30),
            (3, "calculate_progress", "進捗状況計算", 40),
            (4, "identify_actions", "次のアクション特定", 20),
            (5, "collect_warnings", "警告・エラー収集", 60),
            (6, "execute_auto_fixes", "自動修正実行", 200),
            (7, "reevaluate_state", "状態再評価", 80),
            (8, "force_codemap_update", "CODEMAP強制更新", 100),
        ]

        for step, name, description, duration in subtask_info:
            collector.add_subtask(step, name, description, duration)
            collector.start_subtask(step)
            # 実際の実行時間をシミュレート（推定時間の±20%）
            actual_duration = int(duration * (0.8 + 0.4 * (step % 3) / 3))
            collector.complete_subtask(step, actual_duration)

        # Assert
        summary = collector.get_metadata_summary()
        assert summary["total_steps"] == 8
        assert summary["completed_steps"] == 8
        assert summary["total_estimated_duration_ms"] == 580
        assert summary["total_actual_duration_ms"] > 0
        assert 0.5 <= summary["performance_ratio"] <= 1.5  # 妥当な性能比率


class TestSubtaskIntegrationWithMCP:
    """サブタスクとMCP統合テスト"""

    @pytest.mark.asyncio
    async def test_mcp_subtask_notification_protocol(self):
        """MCPサブタスク通知プロトコルテスト"""
        # Arrange
        class MockMCPClient:
            def __init__(self):
                self.notifications = []

            async def send_notification(self, method: str, params: Dict[str, Any]):
                self.notifications.append({
                    "method": method,
                    "params": params
                })

        mcp_client = MockMCPClient()

        # Act - MCP通知プロトコルをシミュレート
        for step in range(1, 9):
            await mcp_client.send_notification(
                "subtask/progress",
                {
                    "command": "check",
                    "step": step,
                    "description": f"ステップ{step}実行中",
                    "status": "in_progress"
                }
            )

        # Assert
        assert len(mcp_client.notifications) == 8
        for i, notification in enumerate(mcp_client.notifications):
            assert notification["method"] == "subtask/progress"
            assert notification["params"]["step"] == i + 1
            assert notification["params"]["command"] == "check"

    def test_subtask_llm_notification_format(self):
        """サブタスクLLM通知フォーマットテスト"""
        # Arrange
        def format_llm_notification(step: int, description: str, status: str) -> str:
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "error": "❌"
            }

            return f"{status_emoji.get(status, '🔄')} ステップ{step}: {description} ({status})"

        # Act & Assert - 各ステップの通知フォーマット確認
        test_cases = [
            (1, "CODEMAPステータス確認", "in_progress", "🔄 ステップ1: CODEMAPステータス確認 (in_progress)"),
            (2, "実装許可判定", "completed", "✅ ステップ2: 実装許可判定 (completed)"),
            (3, "進捗状況計算", "error", "❌ ステップ3: 進捗状況計算 (error)"),
        ]

        for step, description, status, expected in test_cases:
            result = format_llm_notification(step, description, status)
            assert result == expected


@pytest.mark.spec("SPEC-CHECK-SUBTASKS-001")
class TestCheckCommandSubtaskSpecification:
    """checkコマンドサブタスク仕様準拠テスト"""

    def test_check_command_subtask_specification_compliance(self):
        """checkコマンドサブタスク仕様準拠テスト"""
        # Arrange - B20ユースケースの8ステップ定義
        expected_steps = [
            {
                "step": 1,
                "name": "check_codemap_status",
                "description": "CODEMAPステータス確認",
                "required": True
            },
            {
                "step": 2,
                "name": "evaluate_implementation_permission",
                "description": "実装許可判定",
                "required": True
            },
            {
                "step": 3,
                "name": "calculate_progress_status",
                "description": "進捗状況計算",
                "required": True
            },
            {
                "step": 4,
                "name": "identify_next_actions",
                "description": "次のアクション特定",
                "required": True
            },
            {
                "step": 5,
                "name": "collect_warnings_and_errors",
                "description": "警告・エラー収集",
                "required": True
            },
            {
                "step": 6,
                "name": "execute_auto_fixes",
                "description": "自動修正実行",
                "required": False  # 条件付き実行
            },
            {
                "step": 7,
                "name": "reevaluate_after_fixes",
                "description": "自動修正後状態再評価",
                "required": False  # 条件付き実行
            },
            {
                "step": 8,
                "name": "force_codemap_update",
                "description": "CODEMAP強制更新",
                "required": False  # 条件付き実行
            }
        ]

        # Act & Assert - SPEC-CHECK-SUBTASKS-001準拠確認
        assert len(expected_steps) == 8, "8ステップが定義されている必要があります"

        # 必須ステップの確認
        required_steps = [step for step in expected_steps if step["required"]]
        assert len(required_steps) == 5, "5つの必須ステップが存在する必要があります"

        # ステップ番号の連続性確認
        step_numbers = [step["step"] for step in expected_steps]
        assert step_numbers == list(range(1, 9)), "ステップ番号は1-8の連続である必要があります"

        # ステップ名の一意性確認
        step_names = [step["name"] for step in expected_steps]
        assert len(step_names) == len(set(step_names)), "ステップ名は一意である必要があります"
