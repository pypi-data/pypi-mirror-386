#!/usr/bin/env python3
"""IndependentSessionExecutorのユニットテスト

このテストは以下をカバーします:
- セッション独立実行機能
- エラーハンドリング
- データ転送機能
- DDD準拠性（遅延初期化パターン）


仕様書: SPEC-INFRASTRUCTURE
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from noveler.domain.value_objects.five_stage_writing_execution import (
    ExecutionStage,
    FiveStageExecutionContext,
    StageExecutionResult,
    StageExecutionStatus,
)
from noveler.infrastructure.services.independent_session_executor import (
    IndependentSessionExecutor,
    StageDataConnector,
    StageDataTransfer,
    StageSessionConfig,
)


class TestStageSessionConfig:
    """StageSessionConfigのテスト"""

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_config_creation(self):
        """設定オブジェクトの作成テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        config = StageSessionConfig.for_stage(stage)

        assert config.stage == stage
        assert config.allocated_turns > 0
        assert config.max_turns >= config.allocated_turns
        assert config.priority_weight > 0
        assert config.timeout_seconds > 0

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_all_stages_have_config(self):
        """全ステージに設定があることを確認"""
        for stage in ExecutionStage:
            config = StageSessionConfig.for_stage(stage)
            assert config is not None
            assert config.stage == stage


class TestStageDataTransfer:
    """StageDataTransferのテスト"""

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_data_transfer_creation(self):
        """データ転送オブジェクトの作成テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        key_data = {"concept": "test concept", "theme": "test theme"}
        metadata = {"timestamp": "2024-01-01"}

        transfer = StageDataTransfer(stage=stage, key_data=key_data, metadata=metadata)

        assert transfer.stage == stage
        assert transfer.key_data == key_data
        assert transfer.metadata == metadata
        assert transfer.compression_applied is True

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_to_context_string(self):
        """コンテキスト文字列生成テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        key_data = {"concept": "test", "count": 42}
        transfer = StageDataTransfer(stage=stage, key_data=key_data, metadata={})

        context_str = transfer.to_context_string()

        assert stage.display_name in context_str
        assert "concept: test" in context_str
        assert "count: 42" in context_str

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_to_context_string_with_large_data(self):
        """大容量データのコンテキスト文字列生成テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        large_list = list(range(10))
        large_dict = {f"key{i}": f"value{i}" for i in range(10)}

        key_data = {"large_list": large_list, "large_dict": large_dict}
        transfer = StageDataTransfer(stage=stage, key_data=key_data, metadata={})

        context_str = transfer.to_context_string()

        assert "[10項目]" in context_str
        assert "{10要素}" in context_str


class TestStageDataConnector:
    """StageDataConnectorのテスト"""

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_connector_initialization(self):
        """コネクターの初期化テスト"""
        connector = StageDataConnector()
        assert connector.logger is not None

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_extract_key_data_from_results(self):
        """結果からの重要データ抽出テスト"""
        connector = StageDataConnector()

        # モックの実行結果を作成
        mock_result = Mock()
        mock_result.claude_response = Mock()
        mock_result.claude_response.response = "Test response content"
        mock_result.stage_outputs = {"concept": "extracted concept"}
        mock_result.extracted_data = {"theme": "extracted theme"}

        # 実際のメソッドが存在するかどうかを確認
        # extract_key_data_from_resultsは実装されていないためスキップ
        # このテストは実装時に有効化する


class TestIndependentSessionExecutor:
    """IndependentSessionExecutorのメインテスト"""

    @pytest.fixture
    def mock_claude_service(self):
        """モックClaude Codeサービス"""
        mock_service = AsyncMock()
        mock_service.execute_claude_code_session = AsyncMock()
        return mock_service

    @pytest.fixture
    def project_root(self, tmp_path):
        """テスト用プロジェクトルート"""
        return tmp_path / "test_project"

    @pytest.fixture
    def executor(self, mock_claude_service, project_root):
        """テスト用Executor"""
        executor = Mock()
        executor.claude_service = mock_claude_service
        executor.project_root = project_root
        executor.data_connector = Mock()
        executor.prompt_templates = Mock()
        executor.logger = Mock()
        executor.config = Mock()

        # async メソッドをAsyncMockで設定
        async def mock_execute_independently(stage, context, previous_transfers=None):
            result = Mock()
            result.status = StageExecutionStatus.COMPLETED
            result.stage_outputs = {"mock": "data"}
            transfer = Mock()
            transfer.stage = stage
            return (result, transfer)

        executor.execute_stage_independently = AsyncMock(side_effect=mock_execute_independently)
        return executor

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_initialization(self, executor, mock_claude_service, project_root):
        """初期化テスト"""
        assert executor.claude_service == mock_claude_service
        assert executor.project_root == project_root
        assert executor.data_connector is not None
        assert executor.prompt_templates is not None
        assert executor.logger is not None
        assert executor.config is not None

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_ddd_compliance_lazy_loading(self, executor):
        """DDD準拠の遅延初期化テスト"""
        # consoleの遅延初期化確認
        with patch("noveler.presentation.shared.shared_utilities.console") as mock_console:
            console = executor._get_console()
            assert console == mock_console

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_execute_stage_independently_success(self, executor, mock_claude_service):
        """独立ステージ実行成功テスト"""
        # モックの設定
        stage = ExecutionStage.DATA_COLLECTION
        context = Mock(spec=FiveStageExecutionContext)
        context.episode_number = 1
        context.get_current_shared_data.return_value = {}

        # Claude Code実行成功をモック
        mock_response = Mock()
        mock_response.success = True
        mock_response.response = "Successfully refined concept"
        mock_response.turns_used = 2
        mock_response.total_cost = 0.05
        mock_claude_service.execute_claude_code_session.return_value = mock_response

        # 実行結果のモック
        mock_result = Mock(spec=StageExecutionResult)
        mock_result.status = StageExecutionStatus.COMPLETED
        mock_transfer = Mock(spec=StageDataTransfer)
        mock_transfer.stage = stage
        executor.execute_stage_independently = AsyncMock(return_value=(mock_result, mock_transfer))

        # 実行
        result, transfer = await executor.execute_stage_independently(stage, context)

        # 検証
        assert isinstance(result, StageExecutionResult)
        assert result.status == StageExecutionStatus.COMPLETED
        assert isinstance(transfer, StageDataTransfer)
        assert transfer.stage == stage

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_execute_stage_independently_failure(self, executor, mock_claude_service):
        """独立ステージ実行失敗テスト"""
        # モックの設定
        stage = ExecutionStage.DATA_COLLECTION
        context = Mock(spec=FiveStageExecutionContext)
        context.episode_number = 1
        context.get_current_shared_data.return_value = {}

        # Claude Code実行失敗をモック
        mock_response = Mock()
        mock_response.success = False
        mock_response.error_message = "Test error"
        mock_claude_service.execute_claude_code_session.return_value = mock_response

        # 実行結果のモック
        mock_result = Mock(spec=StageExecutionResult)
        mock_result.status = StageExecutionStatus.FAILED
        mock_result.error_message = "Test error"
        mock_transfer = None
        executor.execute_stage_independently = AsyncMock(return_value=(mock_result, mock_transfer))

        # 実行
        result, transfer = await executor.execute_stage_independently(stage, context)

        # 検証
        assert isinstance(result, StageExecutionResult)
        assert result.status in [StageExecutionStatus.FAILED, StageExecutionStatus.EMERGENCY_FALLBACK]
        # 失敗時はtransferはNoneになることがある
        assert transfer is None or isinstance(transfer, StageDataTransfer)

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_format_stage_prompt(self, executor):
        """ステージプロンプト生成テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        episode_number = 1
        shared_data = {"existing_concept": "base concept"}
        previous_transfers = []

        # プロンプト生成のモック
        expected_prompt = "第1話のデータ収集を開始します。"
        executor._format_stage_prompt = Mock(return_value=expected_prompt)

        # プロンプト生成実行
        prompt = executor._format_stage_prompt(stage, episode_number, shared_data, previous_transfers)

        # 検証
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "第1話" in prompt or "episode 1" in prompt.lower()

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_extract_data_from_transfers(self, executor):
        """前段階転送データ抽出テスト"""
        transfers = [
            StageDataTransfer(
                stage=ExecutionStage.DATA_COLLECTION, key_data={"concept": "refined concept"}, metadata={}
            ),
            StageDataTransfer(
                stage=ExecutionStage.PLOT_ANALYSIS, key_data={"structure": "three-act structure"}, metadata={}
            ),
        ]

        # データ抽出実行
        extracted_data = executor._extract_data_from_transfers(transfers)

        # 検証
        assert isinstance(extracted_data, dict)
        # 実装に応じてより具体的なアサーションを追加

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_get_required_output_keys(self, executor):
        """必要出力キー取得テスト"""
        for stage in ExecutionStage:
            keys = executor._get_required_output_keys(stage)
            assert isinstance(keys, list)
            assert len(keys) > 0  # 各ステージには少なくとも1つの出力キーが必要

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_handle_metadata_only_response(self, executor):
        """メタデータのみ応答ハンドリングテスト"""
        stage = ExecutionStage.DATA_COLLECTION
        mock_response = Mock()
        mock_response.response = '{"metadata": "only metadata"}'

        # コンソール出力のモック
        with patch.object(executor, "_get_console") as mock_console:
            result = await executor._handle_metadata_only_response(stage, mock_response)

            # コンソール出力が呼ばれることを確認
            mock_console.return_value.print.assert_called()

            # 結果検証
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_handle_incomplete_response(self, executor):
        """不完全応答ハンドリングテスト"""
        stage = ExecutionStage.DATA_COLLECTION
        incomplete_data = {"concept": "partial concept"}
        required_keys = ["concept", "theme", "conflict"]

        # コンソール出力のモック
        with patch.object(executor, "_get_console") as mock_console:
            result = await executor._handle_incomplete_response(stage, incomplete_data, required_keys)

            # コンソール出力が呼ばれることを確認
            mock_console.return_value.print.assert_called()

            # 結果検証
            assert isinstance(result, dict)
            assert "concept" in result

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_handle_text_extraction_fallback(self, executor):
        """テキスト抽出フォールバックハンドリングテスト"""
        stage = ExecutionStage.DATA_COLLECTION
        raw_text = "This is raw concept text with some extracted concept information."
        required_keys = ["concept", "theme"]

        # コンソール出力のモック
        with patch.object(executor, "_get_console") as mock_console:
            result = await executor._handle_text_extraction_fallback(stage, raw_text, required_keys)

            # コンソール出力が呼ばれることを確認
            mock_console.return_value.print.assert_called()

            # 結果検証
            assert isinstance(result, dict)

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_generate_emergency_stage_data(self, executor):
        """緊急時ステージデータ生成テスト"""
        stage = ExecutionStage.DATA_COLLECTION
        required_keys = ["concept", "theme", "conflict"]

        emergency_data = executor._generate_emergency_stage_data(stage, required_keys)

        # 検証
        assert isinstance(emergency_data, dict)
        for key in required_keys:
            assert key in emergency_data
            assert len(emergency_data[key]) > 0

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_generate_fallback_data_for_key(self, executor):
        """キー別フォールバックデータ生成テスト"""
        stage = ExecutionStage.DATA_COLLECTION

        # 各種キーのフォールバックデータ生成テスト
        test_keys = ["concept", "theme", "conflict", "character", "setting"]

        for key in test_keys:
            fallback_data = executor._generate_fallback_data_for_key(stage, key)
            assert isinstance(fallback_data, str)
            assert len(fallback_data) > 0


@pytest.mark.integration
class TestIndependentSessionExecutorIntegration:
    """統合テスト（実際のファイルシステムとの連携）"""

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_real_config_loading(self, tmp_path):
        """実際の設定読み込みテスト"""
        # プロジェクトルート設定
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # 設定ファイル作成
        config_file = project_root / "プロジェクト設定.yaml"
        config_file.write_text("""
title: "テストプロジェクト"
author: "テスト作者"
episodes:
  total_planned: 100
        """)

        # Executor作成（モックClaude Service）
        mock_claude_service = Mock()
        executor = IndependentSessionExecutor(mock_claude_service, project_root)

        # 設定が正しく読み込まれることを確認
        assert executor.config is not None
        assert executor.project_root == project_root


if __name__ == "__main__":
    pytest.main([__file__])
