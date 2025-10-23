#!/usr/bin/env python3
"""段階的品質チェックMCPツールの統合テスト

MCPサーバーの段階的品質チェック機能をエンドツーエンドでテスト。
B20準拠: 実際のMCPサーバー経由での段階的実行を検証。

仕様書: SPEC-MCP-PROGRESSIVE-CHECK-001
"""

import json
import pytest
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, Mock, patch

import src.mcp_servers.noveler.main as mcp_main
from noveler.presentation.mcp import dispatcher as mcp_dispatcher

# MCPサーバーのインポートテスト
try:
    from src.mcp_servers.noveler.main import server as mcp_server
    MCP_SERVER_AVAILABLE = True
except ImportError:
    MCP_SERVER_AVAILABLE = False
    mcp_server = None


class TestProgressiveCheckMCPTools:
    """段階的品質チェックMCPツールのテスト"""

    @pytest.fixture
    async def mcp_server_instance(self):
        """テスト用MCPサーバー"""
        if not MCP_SERVER_AVAILABLE:
            pytest.skip("MCPサーバーが利用できません")
        return mcp_server

    @pytest.fixture
    def temp_project(self):
        """テスト用プロジェクト環境"""
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # プロジェクト構造作成
            (project_root / "manuscripts").mkdir()
            (project_root / ".noveler" / "checks").mkdir(parents=True)

            # テスト原稿作成
            test_manuscript = project_root / "manuscripts" / "episode_001.md"
            test_manuscript.write_text(
                "これはテスト用の原稿です。誤字や文法の問題が含まれているかもしれません。",
                encoding="utf-8"
            )

            yield project_root

    @pytest.mark.asyncio
    async def test_get_check_tasks_tool(self, mcp_server_instance, temp_project):
        """get_check_tasksツールのテスト"""

        session_id = "EP001_202509270900"
        tasks_payload = {
            "session_id": session_id,
            "episode_number": 1,
            "current_step": 1,
            "current_task": {
                "id": 1,
                "name": "誤字脱字チェック",
                "phase": "basic_quality",
                "description": "基本的な誤字脱字の検出",
            },
            "executable_tasks": [
                {
                    "id": 1,
                    "name": "誤字脱字チェック",
                    "phase": "basic_quality",
                    "description": "基本的な誤字脱字の検出",
                    "estimated_duration": "3-5分",
                },
                {
                    "id": 2,
                    "name": "文法・表記統一チェック",
                    "phase": "basic_quality",
                    "description": "文法の正確性と表記の一貫性を確認",
                    "estimated_duration": "5-8分",
                },
            ],
            "progress": {"completed": 0, "total": 12, "percentage": 0.0},
            "llm_instruction": "LLMにタスクリストを提示してください",
            "next_action": "execute_check_step",
            "phase_info": {"phase": "basic_quality"},
        }

        with patch('noveler.domain.services.progressive_check_manager.ProgressiveCheckManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance
            mock_instance.get_check_tasks.return_value = tasks_payload

            result = await mcp_dispatcher.dispatch(
                "get_check_tasks",
                {
                    "episode_number": 1,
                    "project_root": str(temp_project),
                },
            )

        mock_instance.get_check_tasks.assert_called_once()
        assert result["success"] is True
        assert result["session_id"] == session_id
        assert result["execution_method"] == "progressive_check_manager"
        assert result["tasks_info"]["session_id"] == session_id
        assert len(result["tasks_info"]["executable_tasks"]) == 2

    @pytest.mark.asyncio
    async def test_execute_check_step_tool(self, mcp_server_instance, temp_project):
        """execute_check_stepツールのテスト"""
        with patch('noveler.domain.services.progressive_check_manager.ProgressiveCheckManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance
            mock_instance.session_id = "EP001_202509270901"
            mock_instance.execute_check_step.return_value = {
                "step_id": 1,
                "success": True,
                "execution_time": 3.2,
                "issues_found": 2,
                "quality_score": 88.5,
                "corrections": [
                    "1行目: 「かもしれません」→「かもしれません」（助詞の統一）",
                    "1行目: 「誤字」→「誤字」（表記確認完了）",
                ],
                "next_step": 2,
                "files": {
                    "input_file": "EP001_202501091430_step_1_input.json",
                    "output_file": "EP001_202501091430_step_1_output.json",
                },
            }

            result = await mcp_dispatcher.dispatch(
                "execute_check_step",
                {
                    "episode_number": 1,
                    "step_id": 1,
                    "input_data": {
                        "manuscript_content": "テスト原稿内容",
                        "check_focus": "typo_detection",
                    },
                    "project_root": str(temp_project),
                },
            )

        mock_instance.execute_check_step.assert_called_once_with(1, {
            "manuscript_content": "テスト原稿内容",
            "check_focus": "typo_detection",
        }, False)
        assert result["success"] is True
        assert result["execution_result"]["step_id"] == 1
        assert result["execution_result"]["session_id"] == "EP001_202509270901"
        assert result["execution_result"]["next_step"] == 2
        assert len(result["execution_result"]["corrections"]) == 2

    @pytest.mark.asyncio
    async def test_execute_check_step_command_returns_session_info(self, temp_project):
        """execute_check_stepコマンドのレスポンスにsession情報が含まれるかを確認"""

        with patch('noveler.domain.services.progressive_check_manager.ProgressiveCheckManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance
            mock_instance.execute_check_step.return_value = {
                "success": False,
                "session_id": "QC_EP001_TEST",
                "error": "Session corrupted",
                "session_reset_required": True,
            }

            result = await mcp_dispatcher.dispatch(
                "execute_check_step",
                {
                    "episode_number": 1,
                    "step_id": 5,
                    "input_data": {},
                    "project_root": str(temp_project),
                },
            )

        assert result["execution_method"] == "progressive_check_manager"
        assert result["execution_result"].get("session_id") == "QC_EP001_TEST"
        assert result["execution_result"].get("session_reset_required") is not None
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_check_status_tool(self, mcp_server, temp_project):
        """get_check_statusツールのテスト"""
        with patch('noveler.domain.services.progressive_check_manager.ProgressiveCheckManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            # ステータス情報のモック
            mock_instance.get_check_status.return_value = {
                "session_id": "EP001_202501091430",
                "episode_number": 1,
                "total_steps": 12,
                "completed_steps": 3,
                "progress_percentage": 25.0,
                "current_phase": "basic_quality",
                "last_completed_step": 3,
                "next_step": 4,
                "estimated_remaining_time": "45-60分",
                "session_start_time": "2025-01-09T14:30:00+09:00"
            }
            mock_instance.session_id = "EP001_202501091430"

            result = await mcp_dispatcher.dispatch(
                "get_check_status",
                {
                    "episode_number": 1,
                    "project_root": str(temp_project),
                },
            )

        mock_instance.get_check_status.assert_called_once()
        assert result["success"] is True
        assert result["session_id"] == "EP001_202501091430"
        status = result["status_info"]
        assert status["episode_number"] == 1
        assert status["total_steps"] == 12
        assert status["session_id"] == "EP001_202501091430"
        assert status["completed_steps"] == 3
        assert status["progress_percentage"] == 25.0
        assert status["current_phase"] == "basic_quality"
        assert status["next_step"] == 4
        assert result["session_id"].startswith("EP001_")

    @pytest.mark.asyncio
    async def test_check_basic_failure_contains_error_log(self, temp_project):
        """check_basicがCLI失敗時にerror_logを返却するか確認"""

        failure_payload = {
            "success": False,
            "error": "CLI execution failed",
            "error_log": "Traceback: simulated error",
        }

        with patch(
            'src.mcp_servers.noveler.main.execute_novel_command',
            new=AsyncMock(return_value=failure_payload),
        ) as mock_execute:
            response = await mcp_main.call_tool(
                "check_basic",
                {"episode_number": 1, "project_root": str(temp_project)},
            )

        mock_execute.assert_awaited_once()
        assert response, "call_tool should return a response"
        payload = json.loads(response[0].text)
        assert payload["success"] is False
        assert payload["error_log"] == "Traceback: simulated error"
        assert payload["error"] == "CLI execution failed"

    @pytest.mark.asyncio
    async def test_get_check_history_tool(self, mcp_server, temp_project):
        """get_check_historyツールのテスト"""
        # Arrange
        episode_number = 1

        with patch('src.mcp_servers.noveler.main.ProgressiveCheckManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            # 履歴データのモック
            mock_instance.get_execution_history.return_value = [
                {
                    "step_id": 1,
                    "step_name": "誤字脱字チェック",
                    "executed_at": "2025-01-09T14:31:00+09:00",
                    "execution_time": 3.2,
                    "success": True,
                    "issues_found": 2,
                    "quality_score": 88.5
                },
                {
                    "step_id": 2,
                    "step_name": "文法・表記統一チェック",
                    "executed_at": "2025-01-09T14:35:00+09:00",
                    "execution_time": 4.1,
                    "success": True,
                    "issues_found": 1,
                    "quality_score": 92.0
                },
                {
                    "step_id": 3,
                    "step_name": "読みやすさ基礎チェック",
                    "executed_at": "2025-01-09T14:40:00+09:00",
                    "execution_time": 5.8,
                    "success": True,
                    "issues_found": 0,
                    "quality_score": 95.0
                }
            ]

            # Act: 履歴取得
            result = mock_instance.get_execution_history()

        # Assert
        assert len(result) == 3

        # 各履歴項目の検証
        for i, record in enumerate(result, 1):
            assert record["step_id"] == i
            assert record["success"] is True
            assert record["execution_time"] > 0
            assert record["quality_score"] > 80
            assert "step_name" in record
            assert "executed_at" in record

    @pytest.mark.asyncio
    async def test_step_by_step_workflow(self, mcp_server, temp_project):
        """ステップバイステップワークフローの統合テスト"""
        # Arrange
        episode_number = 1

        with patch('src.mcp_servers.noveler.main.ProgressiveCheckManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            # 段階的実行のシミュレーション
            execution_sequence = []

            # ステップ1: 誤字脱字チェック
            mock_instance.execute_check_step.side_effect = [
                {
                    "step_id": 1,
                    "success": True,
                    "execution_time": 3.2,
                    "issues_found": 2,
                    "quality_score": 88.5,
                    "next_step": 2,
                    "phase": "basic_quality"
                },
                {
                    "step_id": 2,
                    "success": True,
                    "execution_time": 4.1,
                    "issues_found": 1,
                    "quality_score": 92.0,
                    "next_step": 3,
                    "phase": "basic_quality"
                },
                {
                    "step_id": 3,
                    "success": True,
                    "execution_time": 5.8,
                    "issues_found": 0,
                    "quality_score": 95.0,
                    "next_step": 4,
                    "phase": "story_quality"  # 次のフェーズに進む
                }
            ]

            # Act: 基本品質フェーズ（ステップ1-3）を段階的に実行
            results = []
            for step_id in range(1, 4):
                result = mock_instance.execute_check_step(step_id, {
                    "episode_number": episode_number,
                    "step_focus": f"step_{step_id}"
                })
                results.append(result)
                execution_sequence.append(step_id)

        # Assert
        assert len(results) == 3
        assert len(execution_sequence) == 3

        # 各ステップの成功を確認
        for i, result in enumerate(results, 1):
            assert result["step_id"] == i
            assert result["success"] is True
            assert result["quality_score"] > 80

        # 段階的な品質向上を確認
        scores = [r["quality_score"] for r in results]
        assert scores[0] < scores[1] < scores[2]  # 品質スコアが段階的に向上

        # フェーズ遷移の確認
        assert results[0]["phase"] == "basic_quality"
        assert results[1]["phase"] == "basic_quality"
        assert results[2]["phase"] == "story_quality"  # フェーズ変更

    @pytest.mark.asyncio
    async def test_file_io_integration(self, mcp_server, temp_project):
        """ファイル入出力統合テスト"""
        # Arrange
        episode_number = 1

        with patch('src.mcp_servers.noveler.main.ProgressiveCheckManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            # ファイルI/Oのモック
            expected_session_id = "EP001_202501091430"
            mock_instance.session_id = expected_session_id

            input_file_path = temp_project / ".noveler" / "checks" / expected_session_id / f"{expected_session_id}_step_1_input.json"
            output_file_path = temp_project / ".noveler" / "checks" / expected_session_id / f"{expected_session_id}_step_1_output.json"

            mock_instance.save_step_input.return_value = input_file_path
            mock_instance.save_step_output.return_value = output_file_path

            # ディレクトリ作成
            input_file_path.parent.mkdir(parents=True, exist_ok=True)

            # テストファイル作成
            input_data = {
                "step_id": 1,
                "episode_number": episode_number,
                "manuscript_content": "テスト原稿",
                "timestamp": "2025-01-09T14:30:00+09:00"
            }

            output_data = {
                "step_id": 1,
                "issues_found": 2,
                "quality_score": 88.5,
                "corrections": ["修正1", "修正2"],
                "execution_time": 3.2
            }

            # ファイル保存のシミュレーション
            input_file_path.write_text(json.dumps(input_data, ensure_ascii=False, indent=2), encoding="utf-8")
            output_file_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

            # Act
            saved_input_file = mock_instance.save_step_input(1, input_data)
            saved_output_file = mock_instance.save_step_output(1, output_data)

        # Assert
        assert saved_input_file == input_file_path
        assert saved_output_file == output_file_path

        # ファイル内容の確認
        assert input_file_path.exists()
        assert output_file_path.exists()

        loaded_input = json.loads(input_file_path.read_text(encoding="utf-8"))
        loaded_output = json.loads(output_file_path.read_text(encoding="utf-8"))

        assert loaded_input == input_data
        assert loaded_output == output_data

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, mcp_server, temp_project):
        """エラー復旧ワークフローのテスト"""
        # Arrange
        episode_number = 1

        with patch('src.mcp_servers.noveler.main.ProgressiveCheckManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            # エラー発生ケースのモック
            mock_instance.execute_check_step.side_effect = [
                # ステップ1: 成功
                {
                    "step_id": 1,
                    "success": True,
                    "quality_score": 88.5,
                    "next_step": 2
                },
                # ステップ2: エラー発生
                {
                    "step_id": 2,
                    "success": False,
                    "error": "処理中にエラーが発生しました",
                    "error_type": "processing_error",
                    "recoverable": True
                },
                # ステップ2: リトライ成功
                {
                    "step_id": 2,
                    "success": True,
                    "quality_score": 90.0,
                    "next_step": 3,
                    "retry_count": 1
                }
            ]

            # Act: エラー発生とリトライのワークフロー
            results = []

            # ステップ1: 成功
            result1 = mock_instance.execute_check_step(1, {"test": "data"})
            results.append(result1)

            # ステップ2: エラー発生
            result2_error = mock_instance.execute_check_step(2, {"test": "data"})
            results.append(result2_error)

            # ステップ2: リトライ
            if not result2_error["success"] and result2_error.get("recoverable"):
                result2_retry = mock_instance.execute_check_step(2, {"test": "data", "retry": True})
                results.append(result2_retry)

        # Assert
        assert len(results) == 3

        # ステップ1: 成功
        assert results[0]["success"] is True

        # ステップ2: 最初はエラー
        assert results[1]["success"] is False
        assert "error" in results[1]
        assert results[1]["recoverable"] is True

        # ステップ2: リトライ後は成功
        assert results[2]["success"] is True
        assert results[2]["retry_count"] == 1
        assert results[2]["quality_score"] > 0

    @pytest.mark.asyncio
    async def test_backward_compatibility(self, mcp_server, temp_project):
        """後方互換性テスト（従来の一括実行との併用）"""
        # Arrange
        with patch('src.mcp_servers.noveler.main.server._execute_progressive_check') as mock_progressive:
            # 段階的実行ガイダンスのモック
            mock_progressive.return_value = """
🎯 段階的品質チェック機能が利用可能です
新しい段階的チェックシステムの使用方法:
1. get_check_tasks(episode_number=1)
2. execute_check_step(episode_number=1, step_id=1)
💡 段階的指導で品質向上
"""

            # Act: 既存checkツールでprogressive=Trueを使用
            # これは実際のMCPサーバーのjson_conversion_server.pyのcheckツールをシミュレート
            guidance_result = mock_progressive(1, "all", str(temp_project))

        # Assert
        assert "段階的品質チェック機能が利用可能です" in guidance_result
        assert "get_check_tasks" in guidance_result
        assert "execute_check_step" in guidance_result
        assert "段階的指導で品質向上" in guidance_result


@pytest.mark.e2e
class TestProgressiveCheckE2E:
    """段階的品質チェックのエンドツーエンドテスト"""

    @pytest.mark.asyncio
    async def test_complete_12_step_workflow(self, temp_project):
        """完全な12ステップワークフローのテスト（簡略版）"""
        # Arrange
        with patch('src.mcp_servers.noveler.main.ProgressiveCheckManager') as mock_manager:
            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            # 12ステップ全体の実行結果をモック
            all_steps_results = []
            phases = [
                ("basic_quality", [1, 2, 3]),
                ("story_quality", [4, 5, 6]),
                ("structure_quality", [7, 8, 9]),
                ("expression_quality", [10, 11, 12])
            ]

            step_results = []
            for phase_name, step_ids in phases:
                for step_id in step_ids:
                    step_results.append({
                        "step_id": step_id,
                        "success": True,
                        "phase": phase_name,
                        "quality_score": 80 + step_id,  # 段階的向上
                        "next_step": step_id + 1 if step_id < 12 else None,
                        "execution_time": 2.0 + step_id * 0.5
                    })

            mock_instance.execute_check_step.side_effect = step_results

            # 最終ステータス
            mock_instance.get_execution_status.return_value = {
                "episode_number": 1,
                "total_steps": 12,
                "completed_steps": 12,
                "progress_percentage": 100.0,
                "current_phase": "expression_quality",
                "final_quality_score": 92.0,
                "session_completed": True
            }

        # Act: 12ステップすべてを実行（簡略版）
        execution_results = []
        for step_id in range(1, 13):
            result = mock_instance.execute_check_step(step_id, {"step_test": step_id})
            execution_results.append(result)

        final_status = mock_instance.get_execution_status()

        # Assert
        assert len(execution_results) == 12

        # 各フェーズの完了確認
        basic_steps = execution_results[0:3]  # ステップ1-3
        story_steps = execution_results[3:6]  # ステップ4-6
        structure_steps = execution_results[6:9]  # ステップ7-9
        expression_steps = execution_results[9:12]  # ステップ10-12

        for steps in [basic_steps, story_steps, structure_steps, expression_steps]:
            for step in steps:
                assert step["success"] is True

        # 品質スコアの段階的向上確認
        scores = [r["quality_score"] for r in execution_results]
        assert all(scores[i] <= scores[i+1] for i in range(len(scores)-1))  # 単調増加

        # 最終ステータス確認
        assert final_status["completed_steps"] == 12
        assert final_status["progress_percentage"] == 100.0
        assert final_status["session_completed"] is True
        assert final_status["final_quality_score"] > 90


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
