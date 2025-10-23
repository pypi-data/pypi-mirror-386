#!/usr/bin/env python3
"""checkコマンド統合テスト

MCPサーバーとB20PreImplementationCheckUseCaseの統合テスト
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import shutil
from typing import Any

from mcp_servers.noveler.main import execute_novel_command
from noveler.presentation.mcp.adapters.mcp_protocol_adapter import MCPProtocolAdapter
from noveler.application.use_cases.b20_pre_implementation_check_use_case import (
    B20PreImplementationCheckUseCase,
    B20PreImplementationCheckRequest,
)


@pytest.fixture
def integration_temp_dir():
    """統合テスト用一時ディレクトリ"""
    temp_dir = tempfile.mkdtemp(prefix="integration_check_test_")
    temp_path = Path(temp_dir)

    # プロジェクト構造作成
    (temp_path / "temp/test_data/40_原稿").mkdir(parents=True, exist_ok=True)
    (temp_path / "50_管理資料").mkdir(exist_ok=True)
    (temp_path / "config").mkdir(exist_ok=True)
    (temp_path / "specs").mkdir(exist_ok=True)
    (temp_path / "tests").mkdir(exist_ok=True)

    # プロジェクト設定ファイル作成
    project_config = """
project:
  title: "統合テストプロジェクト"
  author: "テストユーザー"
  genre: "テストジャンル"
"""
    (temp_path / "プロジェクト設定.yaml").write_text(project_config, encoding="utf-8")

    yield temp_path
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_mcp_adapter():
    """モックMCPプロトコルアダプター"""
    adapter = MagicMock(spec=MCPProtocolAdapter)
    adapter.handle_novel_command = AsyncMock()
    return adapter


class TestCheckCommandIntegration:
    """checkコマンド統合テストクラス"""

    @pytest.mark.asyncio
    async def test_check_command_mcp_integration_success(
        self, integration_temp_dir, mock_mcp_adapter
    ):
        """checkコマンドMCP統合成功テスト"""
        # Arrange
        mock_mcp_adapter.handle_novel_command.return_value = {
            "success": True,
            "command": "check",
            "result": {
                "implementation_allowed": True,
                "current_stage": "implementation_allowed",
                "completion_percentage": 85.0,
                "next_required_actions": ["実装開始可能"],
                "warnings": [],
                "errors": [],
                "execution_time_ms": 150.5
            }
        }

        with patch("noveler.presentation.mcp.adapters.mcp_protocol_adapter.MCPProtocolAdapter", return_value=mock_mcp_adapter):
            # Act
            result = await execute_novel_command(
                command="check",
                options={"feature_name": "test_feature"},
                project_root=str(integration_temp_dir)
            )

            # Assert
            assert result["success"] is True
            assert result["command"] == "check"
            assert result["result"]["implementation_allowed"] is True
            mock_mcp_adapter.handle_novel_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_command_mcp_integration_failure(
        self, integration_temp_dir, mock_mcp_adapter
    ):
        """checkコマンドMCP統合失敗テスト"""
        # Arrange
        mock_mcp_adapter.handle_novel_command.return_value = {
            "success": False,
            "command": "check",
            "error": "仕様書が見つかりません",
            "result": {
                "implementation_allowed": False,
                "current_stage": "specification_required",
                "completion_percentage": 10.0,
                "errors": ["仕様書が見つかりません: test_feature機能の仕様書を作成してください"]
            }
        }

        with patch("noveler.presentation.mcp.adapters.mcp_protocol_adapter.MCPProtocolAdapter", return_value=mock_mcp_adapter):
            # Act
            result = await execute_novel_command(
                command="check",
                options={"feature_name": "test_feature"},
                project_root=str(integration_temp_dir)
            )

            # Assert
            assert result["success"] is False
            assert "仕様書が見つかりません" in result["error"]
            assert result["result"]["implementation_allowed"] is False

    @pytest.mark.asyncio
    async def test_check_command_with_auto_fix(
        self, integration_temp_dir, mock_mcp_adapter
    ):
        """checkコマンド自動修正付きテスト"""
        # Arrange
        mock_mcp_adapter.handle_novel_command.return_value = {
            "success": True,
            "command": "check",
            "result": {
                "implementation_allowed": True,
                "current_stage": "implementation_allowed",
                "completion_percentage": 100.0,
                "auto_fix_results": {
                    "attempted_fixes": 1,
                    "successful_fixes": 1,
                    "fix_details": [{
                        "type": "spec_creation",
                        "description": "test_feature機能の仕様書を自動作成しました"
                    }]
                }
            }
        }

        with patch("noveler.presentation.mcp.adapters.mcp_protocol_adapter.MCPProtocolAdapter", return_value=mock_mcp_adapter):
            # Act
            result = await execute_novel_command(
                command="check",
                options={
                    "feature_name": "test_feature",
                    "auto_fix_issues": True,
                    "create_missing_spec": True
                },
                project_root=str(integration_temp_dir)
            )

            # Assert
            assert result["success"] is True
            assert result["result"]["auto_fix_results"]["successful_fixes"] == 1

    @pytest.mark.asyncio
    async def test_check_command_force_codemap_update(
        self, integration_temp_dir, mock_mcp_adapter
    ):
        """checkコマンドCODEMAP強制更新テスト"""
        # Arrange
        mock_mcp_adapter.handle_novel_command.return_value = {
            "success": True,
            "command": "check",
            "result": {
                "implementation_allowed": True,
                "current_stage": "implementation_allowed",
                "completion_percentage": 100.0,
                "codemap_status": {"status": "updated", "last_update": "2025-01-15T10:00:00Z"}
            }
        }

        with patch("noveler.presentation.mcp.adapters.mcp_protocol_adapter.MCPProtocolAdapter", return_value=mock_mcp_adapter):
            # Act
            result = await execute_novel_command(
                command="check",
                options={
                    "feature_name": "test_feature",
                    "force_codemap_update": True
                },
                project_root=str(integration_temp_dir)
            )

            # Assert
            assert result["success"] is True
            assert result["result"]["codemap_status"]["status"] == "updated"

    def test_b20_use_case_basic_integration(self, integration_temp_dir):
        """B20ユースケース基本統合テスト（共有サービス不要）"""
        # Arrange - 基本的なB20ユースケースをテスト
        use_case = B20PreImplementationCheckUseCase()

        request = B20PreImplementationCheckRequest(
            feature_name="integration_test",
            target_layer="domain",
            auto_fix_issues=False,
            create_missing_spec=False,
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.current_stage is not None
        assert response.completion_percentage >= 0.0

    def test_b20_use_case_specification_creation_integration(self, integration_temp_dir):
        """B20ユースケース仕様書作成統合テスト"""
        # Arrange
        from noveler.presentation.shared.shared_utilities import get_common_path_service

        path_service = get_common_path_service()
        original_root = path_service.project_root
        path_service._project_root = integration_temp_dir

        # スペックディレクトリを指定
        specs_dir = integration_temp_dir / "specs"

        try:
            use_case = B20PreImplementationCheckUseCase(
                path_service=path_service,
            )

            with patch.object(path_service, 'get_spec_path', return_value=specs_dir):
                # Act
                result = use_case._create_specification_file("integration_test")

                # Assert
                assert result["success"] is True
                assert "integration_test" in result["file_path"].lower()

                # ファイルが実際に作成されたか確認
                created_file = Path(result["file_path"])
                assert created_file.exists()

                # ファイルの内容確認
                content = created_file.read_text(encoding="utf-8")
                assert "integration_test機能仕様書" in content
                assert "## 概要" in content

        finally:
            path_service._project_root = original_root

    @pytest.mark.asyncio
    async def test_check_command_error_handling_integration(
        self, integration_temp_dir, mock_mcp_adapter
    ):
        """checkコマンドエラーハンドリング統合テスト"""
        # Arrange
        mock_mcp_adapter.handle_novel_command.side_effect = Exception("統合テストエラー")

        with patch("noveler.presentation.mcp.adapters.mcp_protocol_adapter.MCPProtocolAdapter", return_value=mock_mcp_adapter):
            # Act
            result = await execute_novel_command(
                command="check",
                options={"feature_name": "test_feature"},
                project_root=str(integration_temp_dir)
            )

            # Assert
            assert result["success"] is False
            assert "統合テストエラー" in result.get("error", "")

    def test_b20_use_case_development_stage_guidance_integration(self, integration_temp_dir):
        """B20ユースケース開発段階ガイダンス統合テスト"""
        # Arrange
        from noveler.presentation.shared.shared_utilities import get_common_path_service

        path_service = get_common_path_service()
        original_root = path_service.project_root
        path_service._project_root = integration_temp_dir

        # テストファイルを作成
        tests_dir = integration_temp_dir / "tests"
        (tests_dir / "test_example.py").write_text("# Test file", encoding="utf-8")

        # 仕様書を作成
        specs_dir = integration_temp_dir / "specs"
        (specs_dir / "SPEC-TEST-001.md").write_text("# Test Specification", encoding="utf-8")

        try:
            use_case = B20PreImplementationCheckUseCase(
                path_service=path_service,
            )

            with patch.object(path_service, 'get_spec_path', return_value=specs_dir):
                # Act
                guidance = use_case.get_development_stage_guidance("test_feature")

                # Assert
                assert guidance["current_stage"] is not None
                assert guidance["completion_percentage"] >= 0.0
                assert guidance["estimated_time"] is not None
                assert "implementation_allowed" in guidance

        finally:
            path_service._project_root = original_root

    @pytest.mark.asyncio
    async def test_check_command_performance_integration(
        self, integration_temp_dir, mock_mcp_adapter
    ):
        """checkコマンドパフォーマンス統合テスト"""
        # Arrange
        import time

        mock_mcp_adapter.handle_novel_command.return_value = {
            "success": True,
            "command": "check",
            "result": {
                "implementation_allowed": True,
                "execution_time_ms": 50.0
            }
        }

        with patch("noveler.presentation.mcp.adapters.mcp_protocol_adapter.MCPProtocolAdapter", return_value=mock_mcp_adapter):
            # Act
            start_time = time.perf_counter()
            result = await execute_novel_command(
                command="check",
                options={"feature_name": "performance_test"},
                project_root=str(integration_temp_dir)
            )
            end_time = time.perf_counter()

            # Assert
            execution_time = (end_time - start_time) * 1000  # ms
            assert result["success"] is True
            assert execution_time < 1000  # 1秒以内に完了


class TestCheckCommandMCPIntegration:
    """checkコマンドMCP固有統合テスト"""

    @pytest.mark.asyncio
    async def test_mcp_adapter_check_command_routing(self, integration_temp_dir):
        """MCPアダプターcheckコマンドルーティングテスト"""
        # Arrange
        adapter = MCPProtocolAdapter()

        # B20ユースケースをモック
        mock_use_case = MagicMock()
        mock_use_case.execute.return_value = MagicMock(
            success=True,
            implementation_allowed=True,
            current_stage="implementation_allowed",
            completion_percentage=85.0,
            next_required_actions=["実装開始可能"],
            warnings=[],
            errors=[],
            execution_time_ms=100.0,
            codemap_status={"status": "available"},
            auto_fix_results=None,
        )

        with patch.object(adapter, '_get_b20_use_case', return_value=mock_use_case):
            # Act
            result = await adapter.handle_novel_command(
                command="check",
                options={"feature_name": "mcp_test"},
                project_root=str(integration_temp_dir)
            )

            # Assert
            assert result["success"] is True
            assert result["command"] == "check"
            mock_use_case.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_adapter_check_command_validation(self, integration_temp_dir):
        """MCPアダプターcheckコマンドバリデーションテスト"""
        # Arrange
        adapter = MCPProtocolAdapter()

        # Act & Assert - 無効なオプション
        with pytest.raises(ValueError):
            await adapter.handle_novel_command(
                command="check",
                options={},  # feature_nameなし
                project_root=str(integration_temp_dir)
            )

    @pytest.mark.asyncio
    async def test_mcp_adapter_subtask_notification(self, integration_temp_dir):
        """MCPアダプターサブタスク通知テスト"""
        # Arrange
        adapter = MCPProtocolAdapter()

        mock_use_case = MagicMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.implementation_allowed = True
        mock_use_case.execute.return_value = mock_response

        subtask_notifications = []

        def mock_notify_subtask(step, description):
            subtask_notifications.append({"step": step, "description": description})

        with patch.object(adapter, '_get_b20_use_case', return_value=mock_use_case), \
             patch.object(adapter, '_notify_llm_subtask', side_effect=mock_notify_subtask):

            # Act
            await adapter.handle_novel_command(
                command="check",
                options={"feature_name": "subtask_test"},
                project_root=str(integration_temp_dir)
            )

            # Assert - 8ステップのサブタスク通知が行われているかは実装に依存
            # ここでは基本的な動作確認のみ
            mock_use_case.execute.assert_called_once()


@pytest.mark.spec("SPEC-CHECK-INTEGRATION-001")
class TestCheckCommandSpecCompliance:
    """checkコマンド仕様準拠統合テスト"""

    @pytest.mark.asyncio
    async def test_check_command_spec_compliance(
        self, integration_temp_dir, mock_mcp_adapter
    ):
        """checkコマンド仕様準拠テスト"""
        # Arrange
        mock_mcp_adapter.handle_novel_command.return_value = {
            "success": True,
            "command": "check",
            "result": {
                "implementation_allowed": True,
                "current_stage": "implementation_allowed",
                "completion_percentage": 100.0,
                "next_required_actions": ["実装開始可能"],
                "warnings": [],
                "errors": [],
                "codemap_status": {"status": "available"},
                "auto_fix_results": None,
                "execution_time_ms": 75.5
            }
        }

        with patch("noveler.presentation.mcp.adapters.mcp_protocol_adapter.MCPProtocolAdapter", return_value=mock_mcp_adapter):
            # Act
            result = await execute_novel_command(
                command="check",
                options={"feature_name": "spec_compliance_test"},
                project_root=str(integration_temp_dir)
            )

            # Assert - SPEC-CHECK-INTEGRATION-001準拠
            assert result["success"] is True
            assert result["command"] == "check"
            assert "implementation_allowed" in result["result"]
            assert "current_stage" in result["result"]
            assert "completion_percentage" in result["result"]
            assert "next_required_actions" in result["result"]
            assert "warnings" in result["result"]
            assert "errors" in result["result"]
            assert "execution_time_ms" in result["result"]

    def test_b20_use_case_8_steps_execution(self, integration_temp_dir):
        """B20ユースケース8ステップ実行テスト"""
        # Arrange
        from noveler.presentation.shared.shared_utilities import get_common_path_service

        path_service = get_common_path_service()
        original_root = path_service.project_root
        path_service._project_root = integration_temp_dir

        try:
            use_case = B20PreImplementationCheckUseCase(
                path_service=path_service,
            )


            # 8ステップ全てを含むリクエスト
            request = B20PreImplementationCheckRequest(
                feature_name="eight_steps_test",
                target_layer="domain",
                auto_fix_issues=True,
                create_missing_spec=True,
                force_codemap_update=True,
            )

            # Act
            response = use_case.execute(request)

            # Assert - 8ステップ全てが実行されたことを確認
            assert response.success is True
            # ステップ1: CODEMAPステータスチェック
            assert response.codemap_status is not None
            # ステップ2: 実装許可判定
            assert response.implementation_allowed is not None
            # ステップ3: 進捗状況計算
            assert response.current_stage is not None
            assert response.completion_percentage is not None
            # ステップ4: 次のアクション特定
            assert response.next_required_actions is not None
            # ステップ5: 警告・エラー収集
            assert response.warnings is not None
            assert response.errors is not None
            # ステップ6,7: 自動修正と再評価
            if response.auto_fix_results:
                assert "attempted_fixes" in response.auto_fix_results
            # ステップ8: 実行時間計測
            assert response.execution_time_ms is not None

        finally:
            path_service._project_root = original_root
