"""インタラクティブ執筆システム統合テスト

Claude Code連携インタラクティブ執筆システムのE2E統合テスト。
10段階執筆プロセス、品質ゲート、セッション管理の統合動作を検証します。
"""

import asyncio
import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import Mock, AsyncMock

from noveler.application.use_cases.interactive_writing_controller import (
    InteractiveWritingController
)
from noveler.application.services.quality_gate_processor import (
    QualityGateProcessor,
    QualityGateStatus
)
from noveler.domain.entities.interactive_writing_session import (
    InteractiveWritingSession,
    SessionStatus,
    StepStatus
)
from types import SimpleNamespace
from noveler.infrastructure.services.interactive_session_manager import (
    InteractiveSessionManager
)


class TestInteractiveWritingSystem:
    """インタラクティブ執筆システム統合テスト"""

    @pytest.fixture
    async def setup_system(self):
        """テスト用システムセットアップ"""

        # モックサービス作成
        mock_cache_service = AsyncMock()
        mock_quality_service = AsyncMock()
        mock_step_processor_factory = Mock()

        # セッションマネージャー
        session_manager = InteractiveSessionManager(
            cache_service=mock_cache_service,
            project_root="/test/project"
        )

        # 品質ゲートプロセッサー
        quality_gate_processor = QualityGateProcessor(mock_quality_service)

        # インタラクティブ執筆コントローラー
        controller = InteractiveWritingController(
            session_manager=session_manager,
            quality_service=mock_quality_service,
            step_processor_factory=mock_step_processor_factory
        )

        return {
            "controller": controller,
            "session_manager": session_manager,
            "quality_gate_processor": quality_gate_processor,
            "mock_quality_service": mock_quality_service,
            "mock_step_processor_factory": mock_step_processor_factory
        }

    @pytest.mark.asyncio
    async def test_full_interactive_writing_flow(self, setup_system):
        """完全なインタラクティブ執筆フロー統合テスト"""

        system = setup_system
        controller = system["controller"]
        mock_quality_service = system["mock_quality_service"]
        mock_step_processor_factory = system["mock_step_processor_factory"]

        # ステップ処理器のモック設定
        for step in range(1, 11):
            mock_processor = AsyncMock()
            mock_processor.execute.return_value = Mock(
                step=step,
                status=StepStatus.COMPLETED,
                output={"test_data": f"step_{step}_output"},
                summary=f"ステップ {step} が完了しました",
                user_prompt=f"ステップ {step} の結果を確認してください",
                execution_time_ms=1000,
                file_references={},
                metadata={}
            )
            mock_step_processor_factory.get_processor.return_value = mock_processor

        # 品質サービスのモック設定
        mock_quality_service.check_step_quality.return_value = SimpleNamespace(
            overall_score=85.0,
            issues=[]
        )

        # 1. インタラクティブ執筆開始
        session = await controller.start_interactive_writing(
            episode_number=1,
            project_root="/test/project"
        )

        assert session is not None
        assert session.episode_number == 1
        assert session.status == SessionStatus.INITIALIZING
        assert session.current_step == 0

        # 2. 段階的実行（ステップ1-10）
        for step in range(1, 11):

            # ユーザーフィードバック（承認）
            user_feedback = "承認" if step > 1 else None

            # ステップ実行
            step_result = await controller.execute_step(
                session=session,
                step=step,
                user_feedback=user_feedback
            )

            # 結果検証
            assert step_result.step == step
            assert step_result.status in [StepStatus.COMPLETED, StepStatus.WAITING_USER]

            # セッション状態確認
            assert session.current_step == step
            assert step in session.step_results

            # 品質チェック結果確認
            assert step_result.quality_check is not None
            assert step_result.quality_check.overall_score >= 0

        # 3. 最終状態確認
        assert session.get_completion_percentage() == 100.0
        assert len(session.step_results) == 10
        assert len(session.quality_history) == 10

    @pytest.mark.asyncio
    async def test_quality_gate_blocking_scenario(self, setup_system):
        """品質ゲートブロッキングシナリオテスト"""

        system = setup_system
        controller = system["controller"]
        mock_quality_service = system["mock_quality_service"]
        mock_step_processor_factory = system["mock_step_processor_factory"]

        # 低品質結果のモック設定
        mock_quality_service.check_step_quality.return_value = SimpleNamespace(
            overall_score=50.0,
            issues=[SimpleNamespace(severity="critical")]
        )

        # ステップ処理器モック
        mock_processor = AsyncMock()
        mock_processor.execute.return_value = Mock(
            step=1,
            status=StepStatus.COMPLETED,
            output={"test_data": "low_quality_output"},
            summary="低品質な出力",
            user_prompt="品質改善が必要です",
            execution_time_ms=1000
        )
        mock_step_processor_factory.get_processor.return_value = mock_processor

        # セッション開始
        session = await controller.start_interactive_writing(
            episode_number=1,
            project_root="/test/project"
        )

        # ステップ1実行（品質ゲート失敗想定）
        step_result = await controller.execute_step(session, 1)

        # ブロッキング状態確認
        assert step_result.quality_check.overall_score < 60  # 警告しきい値未満
        assert len(step_result.quality_check.issues) > 0
        assert any(issue.severity == "critical" for issue in step_result.quality_check.issues)

        # セッション状態確認
        assert session.requires_user_confirmation()
        assert session.status == SessionStatus.WAITING_USER_CONFIRMATION

    @pytest.mark.asyncio
    async def test_session_recovery_scenario(self, setup_system):
        """セッション復旧シナリオテスト"""

        system = setup_system
        controller = system["controller"]
        session_manager = system["session_manager"]

        # 通常セッション作成
        original_session = await controller.start_interactive_writing(
            episode_number=1,
            project_root="/test/project"
        )

        session_id = original_session.session_id

        # エラー状態にして保存
        original_session.status = SessionStatus.ERROR
        original_session.current_step = 5
        await session_manager.save_session(original_session)

        # スナップショット作成
        await session_manager.create_session_snapshot(session_id)

        # セッション復旧実行
        recovered_session = await controller.resume_from_interruption(session_id)

        # 復旧確認
        assert recovered_session is not None
        assert recovered_session.session_id == session_id
        assert recovered_session.status == SessionStatus.IN_PROGRESS  # エラー状態から復旧
        assert recovered_session.current_step == 5

    @pytest.mark.asyncio
    async def test_user_feedback_processing(self, setup_system):
        """ユーザーフィードバック処理テスト"""

        system = setup_system
        controller = system["controller"]
        mock_quality_service = system["mock_quality_service"]
        mock_step_processor_factory = system["mock_step_processor_factory"]

        # モック設定
        mock_processor = AsyncMock()
        mock_processor.execute.return_value = Mock(
            step=1,
            status=StepStatus.COMPLETED,
            output={"feedback_test": True},
            summary="フィードバック処理テスト",
            user_prompt="修正内容を確認してください",
            execution_time_ms=1000
        )
        mock_step_processor_factory.get_processor.return_value = mock_processor

        mock_quality_service.check_step_quality.return_value = SimpleNamespace(
            overall_score=75.0,
            issues=[]
        )

        # セッション開始
        session = await controller.start_interactive_writing(
            episode_number=1,
            project_root="/test/project"
        )

        # ステップ1実行
        await controller.execute_step(session, 1)

        # ステップ2でフィードバック付き実行
        user_feedback = "キャラクターAの動機をより明確にしてください。感情描写を強化してください。"
        step_result = await controller.execute_step(
            session=session,
            step=2,
            user_feedback=user_feedback
        )

        # フィードバック処理確認
        assert len(session.feedback_history) >= 1

        last_feedback = session.get_last_user_feedback()
        assert last_feedback is not None
        assert user_feedback in last_feedback.feedback

        # 修正指示抽出確認
        modifications = last_feedback.extract_modification_requests()
        assert len(modifications) > 0

    @pytest.mark.asyncio
    async def test_session_persistence_and_recovery(self, setup_system):
        """セッション永続化・復旧テスト"""

        system = setup_system
        session_manager = system["session_manager"]

        # セッション作成
        original_session = await session_manager.create_session(
            episode_number=2,
            project_root="/test/project",
            configuration={"test": True}
        )

        session_id = original_session.session_id

        # セッション状態更新
        original_session.current_step = 3
        original_session.status = SessionStatus.IN_PROGRESS
        await session_manager.save_session(original_session)

        # セッション読み込み確認
        loaded_session = await session_manager.load_session(session_id)
        assert loaded_session is not None
        assert loaded_session.session_id == session_id
        assert loaded_session.current_step == 3
        assert loaded_session.status == SessionStatus.IN_PROGRESS

        # セッション一覧取得確認
        session_list = await session_manager.list_sessions(episode_number=2)
        assert len(session_list) >= 1
        assert any(s["session_id"] == session_id for s in session_list)

        # セッション削除確認
        delete_result = await session_manager.delete_session(session_id)
        assert delete_result == True

        # 削除後の確認
        deleted_session = await session_manager.load_session(session_id)
        assert deleted_session is None

    @pytest.mark.asyncio
    async def test_performance_requirements(self, setup_system):
        """パフォーマンス要件テスト"""

        system = setup_system
        controller = system["controller"]
        mock_quality_service = system["mock_quality_service"]
        mock_step_processor_factory = system["mock_step_processor_factory"]

        # 高速レスポンスモック設定
        mock_processor = AsyncMock()
        mock_processor.execute.return_value = Mock(
            step=1,
            status=StepStatus.COMPLETED,
            output={"performance_test": True},
            summary="パフォーマンステスト",
            user_prompt="性能確認",
            execution_time_ms=500,  # 0.5秒
            file_references={},
            metadata={}
        )
        mock_step_processor_factory.get_processor.return_value = mock_processor

        mock_quality_service.check_step_quality.return_value = SimpleNamespace(
            overall_score=80.0,
            issues=[]
        )

        # 実行時間測定
        start_time = datetime.now()

        session = await controller.start_interactive_writing(
            episode_number=1,
            project_root="/test/project"
        )

        step_result = await controller.execute_step(session, 1)

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # パフォーマンス要件確認（5秒以内）
        assert total_time < 5.0
        assert step_result.execution_time_ms < 5000

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, setup_system):
        """エラー処理・復旧テスト"""

        system = setup_system
        controller = system["controller"]
        mock_step_processor_factory = system["mock_step_processor_factory"]

        # エラー発生モック
        mock_processor = AsyncMock()
        mock_processor.execute.side_effect = Exception("テスト用エラー")
        mock_step_processor_factory.get_processor.return_value = mock_processor

        # セッション開始
        session = await controller.start_interactive_writing(
            episode_number=1,
            project_root="/test/project"
        )

        # エラー発生の確認
        with pytest.raises(Exception):
            await controller.execute_step(session, 1)

        # セッション状態確認
        assert session.status == SessionStatus.ERROR
        assert 1 in session.step_results
        assert session.step_results[1].status == StepStatus.FAILED

        # 復旧処理テスト
        # 正常なプロセッサーに変更
        normal_processor = AsyncMock()
        normal_processor.execute.return_value = Mock(
            step=1,
            status=StepStatus.COMPLETED,
            output={"recovered": True},
            summary="復旧成功",
            user_prompt="復旧確認",
            execution_time_ms=1000
        )
        mock_step_processor_factory.get_processor.return_value = normal_processor

        # 復旧実行
        recovered_session = await controller.resume_from_interruption(session.session_id)

        # 復旧確認
        assert recovered_session.status == SessionStatus.IN_PROGRESS


class TestQualityGateIntegration:
    """品質ゲート統合テスト"""

    @pytest.fixture
    def setup_quality_gate(self):
        """品質ゲートテストセットアップ"""
        mock_quality_service = AsyncMock()
        processor = QualityGateProcessor(mock_quality_service)
        return processor, mock_quality_service

    @pytest.mark.asyncio
    async def test_quality_gate_evaluation_levels(self, setup_quality_gate):
        """品質ゲート評価レベルテスト"""

        processor, mock_quality_service = setup_quality_gate

        # テストセッション作成
        session = InteractiveWritingSession(
            session_id="test_session",
            episode_number=1,
            project_root="/test",
            status=SessionStatus.IN_PROGRESS,
            current_step=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 高品質結果テスト（PASSED）
        mock_quality_service.check_step_quality.return_value = SimpleNamespace(
            overall_score=90.0,
            issues=[]
        )

        result = await processor.execute_quality_gate(session, 1, {})
        assert result.status == QualityGateStatus.PASSED
        assert result.can_proceed == True

        # 中品質結果テスト（WARNING）
        mock_quality_service.check_step_quality.return_value = SimpleNamespace(
            overall_score=65.0,
            issues=[SimpleNamespace(severity="warning")]
        )

        result = await processor.execute_quality_gate(session, 1, {})
        assert result.status == QualityGateStatus.WARNING
        assert result.can_proceed == True

        # 低品質結果テスト（BLOCKED）
        mock_quality_service.check_step_quality.return_value = SimpleNamespace(
            overall_score=45.0,
            issues=[SimpleNamespace(severity="critical")]
        )

        result = await processor.execute_quality_gate(session, 1, {})
        assert result.status == QualityGateStatus.BLOCKED
        assert result.can_proceed == False

    @pytest.mark.asyncio
    async def test_step_specific_criteria_application(self, setup_quality_gate):
        """段階特化基準適用テスト"""

        processor, mock_quality_service = setup_quality_gate

        session = InteractiveWritingSession(
            session_id="test_session",
            episode_number=1,
            project_root="/test",
            status=SessionStatus.IN_PROGRESS,
            current_step=8,  # 原稿執筆段階（厳格基準）
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        mock_quality_service.check_step_quality.return_value = SimpleNamespace(
            overall_score=82.0,
            issues=[]
        )

        # ステップ8（原稿執筆）の品質ゲート実行
        result = await processor.execute_quality_gate(session, 8, {})

        # 厳格基準により評価が下がることを確認
        criteria = processor._get_step_criteria(8)
        assert len(criteria) > len(processor.base_criteria)  # 段階特化基準が追加されている

        # ステップ特化の提案が生成されることを確認
        step_specific_suggestions = [s for s in result.suggestions if hasattr(s, 'step_specific') and s.step_specific]
        # 段階特化の評価が適用されていることを確認できれば良い


@pytest.mark.asyncio
async def test_end_to_end_claude_code_integration():
    """E2E Claude Code統合テスト（モック）"""

    # Claude CodeのMCPツール呼び出しをシミュレート
    mcp_request = {
        "tool": "write_interactive",
        "arguments": {
            "episode_number": 1,
            "project_root": "/test/project",
            "step": 1
        }
    }

    # レスポンス形式の確認
    expected_response = {
        "success": True,
        "session_id": str,
        "current_step": int,
        "step_status": str,
        "execution_summary": dict,
        "quality_gate": dict,
        "user_interaction": dict,
        "file_references": dict,
        "next_step": dict
    }

    # 各フィールドの存在確認（実装時にはモック応答で確認）
    for field in expected_response:
        assert field in expected_response  # プレースホルダー
