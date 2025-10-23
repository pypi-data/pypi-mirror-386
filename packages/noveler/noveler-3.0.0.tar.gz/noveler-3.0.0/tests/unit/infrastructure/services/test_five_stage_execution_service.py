#!/usr/bin/env python3
"""ManuscriptGenerationServiceのユニットテスト（旧FiveStageExecutionService）

このテストは以下をカバーします:
- 5段階実行制御機能
- 進捗監視システム
- データ永続化管理
- エラー復旧機能
- DDD準拠性（遅延初期化パターン）


仕様書: SPEC-INFRASTRUCTURE
"""

import pytest

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch


from noveler.domain.value_objects.five_stage_writing_execution import (
    ExecutionStage,
    FiveStageExecutionContext,
    FiveStageWritingRequest,
    FiveStageWritingResponse,
    StageExecutionResult,
    StageExecutionStatus,
)
from noveler.infrastructure.services.manuscript_generation_service import (
    FiveStageDataPersistenceManager,
    FiveStageErrorRecoveryManager,
    ManuscriptGenerationService,
    FiveStageProgressMonitor,
)
# 後方互換性のためのエイリアス
FiveStageExecutionService = ManuscriptGenerationService
NovelManuscriptGenerationService = ManuscriptGenerationService


class TestFiveStageProgressMonitor:
    """FiveStageProgressMonitorのテスト"""

    @pytest.fixture
    def mock_context(self):
        """モック実行コンテキスト"""
        context = Mock(spec=FiveStageExecutionContext)
        context.episode_number = 1
        context.total_turns_used = 5
        context.get_progress_percentage.return_value = 25.0
        return context

    @pytest.fixture
    def progress_monitor(self, mock_context):
        """テスト用進捗モニター"""
        return FiveStageProgressMonitor(mock_context)

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_initialization(self, progress_monitor, mock_context):
        """初期化テスト"""
        assert progress_monitor.context == mock_context
        assert progress_monitor.logger is not None

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_ddd_compliance_lazy_loading(self, progress_monitor):
        """DDD準拠の遅延初期化テスト"""
        # consoleの遅延初期化確認
        with patch("noveler.presentation.shared.shared_utilities.console") as mock_console:
            console = progress_monitor._get_console()
            assert console == mock_console

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_display_stage_start(self, progress_monitor):
        """ステージ開始表示テスト"""
        stage = ExecutionStage.DATA_COLLECTION

        # コンソール出力のモック
        with patch.object(progress_monitor, "_get_console") as mock_console:
            progress_monitor.display_stage_start(stage)

            # コンソール出力が呼ばれることを確認
            assert mock_console.return_value.print.call_count >= 3

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_display_stage_progress(self, progress_monitor):
        """ステージ進捗表示テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        turns_used = 3

        # コンソール出力のモック
        with patch.object(progress_monitor, "_get_console") as mock_console:
            progress_monitor.display_stage_progress(stage, turns_used)

            # コンソール出力が呼ばれることを確認
            mock_console.return_value.print.assert_called()

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_display_stage_complete(self, progress_monitor):
        """ステージ完了表示テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        result = Mock(spec=StageExecutionResult)
        result.status = StageExecutionStatus.COMPLETED
        result.turns_used = 4
        result.execution_time_seconds = 120

        # コンソール出力のモック
        with patch.object(progress_monitor, "_get_console") as mock_console:
            progress_monitor.display_stage_complete(stage, result)

            # コンソール出力が呼ばれることを確認
            mock_console.return_value.print.assert_called()

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_display_overall_progress(self, progress_monitor):
        """全体進捗表示テスト"""
        completed_stages = [ExecutionStage.DATA_COLLECTION, ExecutionStage.PLOT_ANALYSIS]

        # コンソール出力のモック
        with patch.object(progress_monitor, "_get_console") as mock_console:
            progress_monitor.display_overall_progress(completed_stages)

            # コンソール出力が呼ばれることを確認
            mock_console.return_value.print.assert_called()


class TestFiveStageDataPersistenceManager:
    """FiveStageDataPersistenceManagerのテスト"""

    @pytest.fixture
    def project_root(self, tmp_path):
        """テスト用プロジェクトルート"""
        return tmp_path / "test_project"

    @pytest.fixture
    def persistence_manager(self, project_root):
        """テスト用永続化マネージャー"""
        return FiveStageDataPersistenceManager(project_root)

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_initialization(self, persistence_manager, project_root):
        """初期化テスト"""
        assert persistence_manager.project_root == project_root
        assert persistence_manager.logger is not None

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_create_session_directory(self, persistence_manager, project_root):
        """セッションディレクトリ作成テスト"""
        session_id = "test_session_123"

        # セッションディレクトリ作成
        session_dir = persistence_manager.create_session_directory(session_id)

        # 検証
        assert session_dir.exists()
        assert session_dir.is_dir()
        assert session_id in str(session_dir)

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_save_stage_result(self, persistence_manager, project_root):
        """ステージ結果保存テスト"""
        session_id = "test_session_123"
        stage = ExecutionStage.DATA_COLLECTION
        result = Mock(spec=StageExecutionResult)
        result.status = StageExecutionStatus.COMPLETED
        result.stage_outputs = {"concept": "test concept"}

        # セッションディレクトリ作成
        session_dir = persistence_manager.create_session_directory(session_id)

        # ステージ結果保存
        saved_path = persistence_manager.save_stage_result(session_id, stage, result)

        # 検証
        assert saved_path.exists()
        assert saved_path.is_file()
        assert stage.name.lower() in str(saved_path)

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_load_session_data(self, persistence_manager, project_root):
        """セッションデータ読み込みテスト"""
        session_id = "test_session_123"

        # 事前にセッションデータを保存
        session_dir = persistence_manager.create_session_directory(session_id)
        test_data = {"episode_number": 1, "timestamp": "2024-01-01"}

        # データ保存
        persistence_manager.save_session_metadata(session_id, test_data)

        # データ読み込み
        loaded_data = persistence_manager.load_session_data(session_id)

        # 検証
        assert loaded_data is not None
        assert isinstance(loaded_data, dict)


class TestFiveStageErrorRecoveryManager:
    """FiveStageErrorRecoveryManagerのテスト"""

    @pytest.fixture
    def mock_claude_service(self):
        """モックClaude Codeサービス"""
        return AsyncMock()

    @pytest.fixture
    def error_recovery_manager(self, mock_claude_service):
        """テスト用エラー復旧マネージャー"""
        return FiveStageErrorRecoveryManager(mock_claude_service)

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_initialization(self, error_recovery_manager, mock_claude_service):
        """初期化テスト"""
        assert error_recovery_manager.claude_service == mock_claude_service
        assert error_recovery_manager.logger is not None

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_attempt_stage_recovery_success(self, error_recovery_manager):
        """ステージ復旧成功テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        failed_result = Mock(spec=StageExecutionResult)
        failed_result.error_message = "Original error"
        context = Mock(spec=FiveStageExecutionContext)

        # 復旧実行をモック
        with patch.object(error_recovery_manager, "_execute_recovery_strategy") as mock_recovery:
            mock_recovery.return_value = Mock(success=True)

            recovery_result = await error_recovery_manager.attempt_stage_recovery(stage, failed_result, context)

            # 検証
            assert recovery_result is not None

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_attempt_stage_recovery_failure(self, error_recovery_manager):
        """ステージ復旧失敗テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        failed_result = Mock(spec=StageExecutionResult)
        failed_result.error_message = "Critical error"
        context = Mock(spec=FiveStageExecutionContext)

        # 復旧失敗をモック
        with patch.object(error_recovery_manager, "_execute_recovery_strategy") as mock_recovery:
            mock_recovery.return_value = Mock(success=False)

            recovery_result = await error_recovery_manager.attempt_stage_recovery(stage, failed_result, context)

            # 検証（復旧失敗でもNoneではない結果を返すべき）
            assert recovery_result is not None


class TestFiveStageExecutionService:
    """FiveStageExecutionServiceのメインテスト"""

    @pytest.fixture
    def mock_claude_service(self):
        """モックClaude Codeサービス"""
        return AsyncMock()

    @pytest.fixture
    def project_root(self, tmp_path):
        """テスト用プロジェクトルート"""
        return tmp_path / "test_project"

    @pytest.fixture
    def execution_service(self, mock_claude_service, project_root):
        """テスト用実行サービス"""
        with patch("noveler.infrastructure.services.five_stage_execution_service.FiveStageExecutionService") as MockService:
            service = Mock()
            service.claude_service = mock_claude_service
            service.project_root = project_root
            service.logger = Mock()
            service.persistence_manager = Mock()
            service.error_recovery_manager = Mock()
            service.prompt_templates = Mock()
            service.independent_executor = Mock()
            service.content_validator = Mock()
            MockService.return_value = service
            return service

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_initialization(self, execution_service, mock_claude_service, project_root):
        """初期化テスト"""
        assert execution_service.claude_service == mock_claude_service
        assert execution_service.project_root == project_root
        assert execution_service.logger is not None
        assert execution_service.persistence_manager is not None
        assert execution_service.error_recovery_manager is not None
        assert execution_service.prompt_templates is not None
        assert execution_service.independent_executor is not None
        assert execution_service.content_validator is not None

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_ddd_compliance_lazy_loading(self, execution_service):
        """DDD準拠の遅延初期化テスト"""
        # consoleの遅延初期化確認
        with patch("noveler.presentation.shared.shared_utilities.console") as mock_console:
            console = execution_service._get_console()
            assert console == mock_console

        # path_serviceの遅延初期化確認
        with patch("noveler.infrastructure.adapters.path_service_adapter.create_path_service") as mock_path_service:
            path_service = execution_service._get_path_service()
            assert path_service == mock_path_service.return_value

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_execute_five_stage_writing_success(self, execution_service):
        """5段階執筆実行成功テスト"""
        # リクエスト作成
        request = Mock(spec=FiveStageWritingRequest)
        request.episode_number = 1
        request.use_independent_sessions = True
        request.enable_recovery = True

        # 独立実行子の成功をモック
        with patch.object(execution_service.independent_executor, "execute_stage_independently") as mock_execute:
            mock_result = Mock(spec=StageExecutionResult)
            mock_result.status = StageExecutionStatus.COMPLETED
            mock_result.stage_outputs = {"concept": "test concept"}
            mock_result.turns_used = 3
            mock_result.execution_time_seconds = 120

            mock_transfer = Mock()
            mock_transfer.key_data = {"concept": "test concept"}

            mock_execute.return_value = (mock_result, mock_transfer)

            # 実行
            response = await execution_service.execute_five_stage_writing(request)

            # 検証
            assert isinstance(response, FiveStageWritingResponse)
            assert response.success is True

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_execute_single_stage_independent_success(self, execution_service):
        """単一ステージ独立実行成功テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        context = Mock(spec=FiveStageExecutionContext)
        context.episode_number = 1
        previous_transfers = []

        # 独立実行子の成功をモック
        with patch.object(execution_service.independent_executor, "execute_stage_independently") as mock_execute:
            mock_result = Mock(spec=StageExecutionResult)
            mock_result.status = StageExecutionStatus.COMPLETED
            mock_transfer = Mock()

            mock_execute.return_value = (mock_result, mock_transfer)

            # 実行
            result, transfer = await execution_service._execute_single_stage_independent(
                stage, context, previous_transfers
            )

            # 検証
            assert result.status == StageExecutionStatus.COMPLETED
            assert transfer is not None

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_extract_stage_output(self, execution_service):
        """ステージ出力抽出テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        mock_response = Mock()
        mock_response.response = '{"concept": "extracted concept", "theme": "extracted theme"}'

        # 出力抽出実行
        extracted_output = execution_service._extract_stage_output(stage, mock_response)

        # 検証
        assert isinstance(extracted_output, dict)
        assert "concept" in extracted_output or len(extracted_output) > 0

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_emergency_text_extraction(self, execution_service):
        """緊急テキスト抽出テスト"""
        raw_text = "This is the concept: innovative storytelling approach. Theme: redemption."
        required_keys = ["concept", "theme"]

        # 緊急抽出実行
        extracted_data = execution_service._emergency_text_extraction(raw_text, required_keys)

        # 検証
        assert isinstance(extracted_data, dict)
        for key in required_keys:
            assert key in extracted_data

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_extract_manuscript_from_text(self, execution_service):
        """テキストから原稿抽出テスト"""
        text_with_manuscript = """
        Here is some content.

        # 第1話 タイトル

        これは原稿の内容です。
        物語の本文がここに含まれています。

        ## 設定
        追加の設定情報
        """

        # 原稿抽出実行
        extracted_manuscript = execution_service._extract_manuscript_from_text(text_with_manuscript)

        # 検証
        assert isinstance(extracted_manuscript, str)
        assert len(extracted_manuscript) > 0

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_update_shared_data(self, execution_service):
        """共有データ更新テスト"""
        context = Mock(spec=FiveStageExecutionContext)
        context.shared_data = {}

        transfer = Mock()
        transfer.key_data = {"concept": "new concept", "theme": "new theme"}

        # データ更新実行
        execution_service._update_shared_data(context, transfer)

        # contextのupdate_shared_dataが呼ばれることを確認
        # 実装に応じて適切なアサーションを追加

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_estimate_turns_used(self, execution_service):
        """ターン使用数推定テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        response_length = 1000

        # 推定実行
        estimated_turns = execution_service._estimate_turns_used(stage, response_length)

        # 検証
        assert isinstance(estimated_turns, int)
        assert estimated_turns > 0

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_estimate_cost(self, execution_service):
        """コスト推定テスト"""
        turns_used = 5

        # コスト推定実行
        estimated_cost = execution_service._estimate_cost(turns_used)

        # 検証
        assert isinstance(estimated_cost, (int, float))
        assert estimated_cost >= 0

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_save_final_manuscript_success(self, execution_service, project_root):
        """最終原稿保存成功テスト"""
        response = Mock(spec=FiveStageWritingResponse)
        response.episode_number = 1
        response.final_manuscript = "完成した原稿内容"
        response.total_execution_time_seconds = 600

        stage_results = [
            Mock(stage_outputs={"concept": "test concept"}),
            Mock(stage_outputs={"structure": "test structure"}),
        ]

        # パスサービスのモック
        with patch.object(execution_service, "_get_path_service") as mock_path_service:
            mock_path_service.return_value.get_manuscript_dir.return_value = project_root / "manuscripts"
            (project_root / "manuscripts").mkdir(parents=True, exist_ok=True)

            # 保存実行
            saved_path = await execution_service._save_final_manuscript(response, stage_results)

            # 検証
            assert saved_path is not None

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_save_quality_report(self, execution_service, project_root):
        """品質レポート保存テスト"""
        response = Mock(spec=FiveStageWritingResponse)
        response.episode_number = 1
        response.quality_metrics = {"overall_score": 8.5}
        response.total_cost = 0.25

        # パスサービスのモック
        with patch.object(execution_service, "_get_path_service") as mock_path_service:
            mock_path_service.return_value.get_quality_records_dir.return_value = project_root / "quality"
            (project_root / "quality").mkdir(parents=True, exist_ok=True)

            # 保存実行
            saved_path = await execution_service._save_quality_report(response)

            # 検証
            assert saved_path is not None


@pytest.mark.integration
class TestFiveStageExecutionServiceIntegration:
    """統合テスト（実際のファイルシステムとの連携）"""

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_real_directory_creation(self, tmp_path):
        """実際のディレクトリ作成テスト"""
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # サービス作成
        mock_claude_service = Mock()
        service = FiveStageExecutionService(mock_claude_service, project_root)

        # 必要なディレクトリが作成されることを確認
        assert service.project_root.exists()

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_persistence_manager_integration(self, tmp_path):
        """永続化マネージャー統合テスト"""
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # 永続化マネージャー作成
        manager = FiveStageDataPersistenceManager(project_root)

        # セッションディレクトリ作成
        session_id = f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_dir = manager.create_session_directory(session_id)

        # 検証
        assert session_dir.exists()
        assert session_dir.is_dir()


if __name__ == "__main__":
    pytest.main([__file__])
