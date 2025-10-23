"""
from noveler.presentation.shared.shared_utilities import get_common_path_service
品質チェックプロンプト生成ユースケースのテスト

SPEC-STAGE5-SEPARATION対応
TDD実装: ユースケース層のテストケース
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from noveler.application.use_cases.quality_check_prompt_use_case import (
    QualityCheckPromptGenerationRequest,
    QualityCheckPromptGenerationResponse,
    QualityCheckPromptUseCase,
    QualityCheckPromptUseCaseFactory,
)
from noveler.domain.value_objects.quality_check_level import QualityCheckLevel, QualityCriterion


class FakePromptId:
    """テスト用のシンプルなプロンプトID値オブジェクト"""

    def __init__(self, value: str) -> None:
        self.value = value

    def __str__(self) -> str:  # pragma: no cover - trivial string conversion
        return self.value


@pytest.mark.spec("SPEC-STAGE5-SEPARATION")
class TestQualityCheckPromptGenerationRequest:
    """品質チェックプロンプト生成要求DTOのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT_USE_CASE-BASIC_REQUEST_CREATI")
    def test_basic_request_creation(self):
        """基本要求作成テスト"""
        request = QualityCheckPromptGenerationRequest(
            project_name="Test Project", episode_number=1, check_level=QualityCheckLevel.STANDARD
        )

        assert request.project_name == "Test Project"
        assert request.episode_number == 1
        assert request.check_level == QualityCheckLevel.STANDARD
        assert request.plot_file_path is None
        assert request.custom_criteria is None
        assert not request.force_regenerate

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT_USE_CASE-FULL_REQUEST_CREATIO")
    def test_full_request_creation(self):
        """完全要求作成テスト"""
        custom_criteria = [
            QualityCriterion(
                criterion_id="TEST001",
                name="Test Criterion",
                description="Test description",
                weight=0.5,
                check_method="test_method",
            )
        ]

        request = QualityCheckPromptGenerationRequest(
            project_name="Test Project",
            episode_number=2,
            check_level=QualityCheckLevel.CLAUDE_OPTIMIZED,
            plot_file_path="/path/to/plot.yaml",
            custom_criteria=custom_criteria,
            force_regenerate=True,
        )

        assert request.project_name == "Test Project"
        assert request.episode_number == 2
        assert request.check_level == QualityCheckLevel.CLAUDE_OPTIMIZED
        assert request.plot_file_path == "/path/to/plot.yaml"
        assert request.custom_criteria == custom_criteria
        assert request.force_regenerate


@pytest.mark.spec("SPEC-STAGE5-SEPARATION")
class TestQualityCheckPromptGenerationResponse:
    """品質チェックプロンプト生成応答DTOのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT_USE_CASE-SUCCESS_RESPONSE")
    def test_success_response(self):
        """成功応答テスト"""
        response = QualityCheckPromptGenerationResponse(
            success=True,
            prompt_id="test-prompt-123",
            generated_prompt="Generated prompt content",
            prompt_length=100,
            execution_time_ms=500,
        )

        assert response.success
        assert response.prompt_id == "test-prompt-123"
        assert response.generated_prompt == "Generated prompt content"
        assert response.prompt_length == 100
        assert response.execution_time_ms == 500
        assert response.is_success()

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT_USE_CASE-FAILURE_RESPONSE")
    def test_failure_response(self):
        """失敗応答テスト"""
        response = QualityCheckPromptGenerationResponse(
            success=False, error_message="Plot not found", execution_time_ms=100
        )

        assert not response.success
        assert response.error_message == "Plot not found"
        assert response.prompt_id is None
        assert response.generated_prompt is None
        assert not response.is_success()


@pytest.mark.spec("SPEC-STAGE5-SEPARATION")
class TestQualityCheckPromptUseCase:
    """品質チェックプロンプトユースケースのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_prompt_generator = Mock()
        self.mock_prompt_repository = Mock()
        self.mock_plot_repository = Mock()
        self.mock_common_path_service = Mock()
        self.plot_dir = Path(tempfile.mkdtemp())
        (self.plot_dir / "第001話.yaml").write_text("dummy", encoding="utf-8")
        self.mock_common_path_service.get_plot_dir.return_value = self.plot_dir

        self.use_case = QualityCheckPromptUseCase(
            prompt_generator=self.mock_prompt_generator,
            prompt_repository=self.mock_prompt_repository,
            plot_repository=self.mock_plot_repository,
            common_path_service=self.mock_common_path_service,
        )

    @pytest.mark.asyncio
    async def test_generate_prompt_success(self):
        """プロンプト生成成功テスト"""
        # モック設定
        self.mock_prompt_repository.find_by_episode.return_value = []  # 既存プロンプトなし

        mock_plot = Mock()
        self.use_case._load_episode_plot = AsyncMock(return_value=mock_plot)

        mock_prompt = Mock()
        mock_prompt.prompt_id = FakePromptId("test-prompt-123")
        mock_prompt.generated_prompt = "Generated test prompt"
        self.mock_prompt_generator.generate_prompt.return_value = mock_prompt

        # テスト実行
        request = QualityCheckPromptGenerationRequest(
            project_name="Test Project", episode_number=1, check_level=QualityCheckLevel.STANDARD
        )

        response = await self.use_case.generate_quality_check_prompt(request)

        # 検証
        assert response.success
        assert response.prompt_id == "test-prompt-123"
        assert response.generated_prompt == "Generated test prompt"
        assert response.execution_time_ms >= 0

        self.mock_prompt_repository.save.assert_called_once_with(mock_prompt)

    @pytest.mark.asyncio
    async def test_generate_prompt_plot_not_found(self):
        """プロンプト生成プロット未発見テスト"""
        # モック設定
        self.mock_prompt_repository.find_by_episode.return_value = []
        self.use_case._load_episode_plot = AsyncMock(return_value=None)  # プロットなし

        # テスト実行
        request = QualityCheckPromptGenerationRequest(
            project_name="Test Project", episode_number=1, check_level=QualityCheckLevel.STANDARD
        )

        response = await self.use_case.generate_quality_check_prompt(request)

        # 検証
        assert not response.success
        assert "Episode plot not found" in response.error_message
        assert response.prompt_id is None

        self.mock_prompt_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_prompt_with_existing_prompt(self):
        """既存プロンプトありの生成テスト"""
        # 既存プロンプトのモック
        existing_prompt = Mock()
        existing_prompt.prompt_id = FakePromptId("existing-123")
        existing_prompt.generated_prompt = "Existing prompt content"
        existing_prompt.request.check_level = QualityCheckLevel.STANDARD

        self.mock_prompt_repository.find_by_episode.return_value = [existing_prompt]

        # テスト実行（force_regenerate=False）
        request = QualityCheckPromptGenerationRequest(
            project_name="Test Project",
            episode_number=1,
            check_level=QualityCheckLevel.STANDARD,
            force_regenerate=False,
        )

        response = await self.use_case.generate_quality_check_prompt(request)

        # 検証
        assert response.success
        assert response.prompt_id == "existing-123"
        assert response.generated_prompt == "Existing prompt content"

        # 新しいプロンプトは生成されない
        self.mock_prompt_generator.generate_prompt.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_prompt_force_regenerate(self):
        """強制再生成テスト"""
        # 既存プロンプトあり
        existing_prompt = Mock()
        existing_prompt.request.check_level = QualityCheckLevel.STANDARD
        existing_prompt.generated_prompt = "Existing prompt content"
        self.mock_prompt_repository.find_by_episode.return_value = [existing_prompt]

        # 新しいプロンプト生成のモック設定
        mock_plot = Mock()
        self.use_case._load_episode_plot = AsyncMock(return_value=mock_plot)

        new_prompt = Mock()
        new_prompt.prompt_id = FakePromptId("new-prompt-456")
        new_prompt.generated_prompt = "New generated prompt"
        self.mock_prompt_generator.generate_prompt.return_value = new_prompt

        # テスト実行（force_regenerate=True）
        request = QualityCheckPromptGenerationRequest(
            project_name="Test Project", episode_number=1, check_level=QualityCheckLevel.STANDARD, force_regenerate=True
        )

        response = await self.use_case.generate_quality_check_prompt(request)

        # 検証
        assert response.success
        assert response.prompt_id == "new-prompt-456"
        assert response.generated_prompt == "New generated prompt"

        # 新しいプロンプトが生成された
        self.mock_prompt_generator.generate_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_prompt_validation_error(self):
        """プロンプト生成検証エラーテスト"""
        # モック設定
        self.mock_prompt_repository.find_by_episode.return_value = []

        mock_plot = Mock()
        self.use_case._load_episode_plot = AsyncMock(return_value=mock_plot)

        # 検証エラーを発生させる
        self.mock_prompt_generator.generate_prompt.side_effect = ValueError("Plot validation failed")

        # テスト実行
        request = QualityCheckPromptGenerationRequest(
            project_name="Test Project", episode_number=1, check_level=QualityCheckLevel.STANDARD
        )

        response = await self.use_case.generate_quality_check_prompt(request)

        # 検証
        assert not response.success
        assert "Plot validation failed" in response.error_message
        assert response.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_get_existing_prompts(self):
        """既存プロンプト取得テスト"""
        # モックプロンプト作成
        mock_prompt1 = Mock()
        mock_prompt1.prompt_id = FakePromptId("prompt-1")
        mock_prompt1.creation_timestamp = datetime(2023, 1, 1, 10, 0, 0)
        mock_prompt1.request.check_level = QualityCheckLevel.STANDARD
        mock_prompt1.generated_prompt = "Prompt content 1"
        mock_prompt1.check_result = None

        mock_prompt2 = Mock()
        mock_prompt2.prompt_id = FakePromptId("prompt-2")
        mock_prompt2.creation_timestamp = datetime(2023, 1, 2, 10, 0, 0)
        mock_prompt2.request.check_level = QualityCheckLevel.CLAUDE_OPTIMIZED
        mock_prompt2.generated_prompt = "Prompt content 2"
        mock_prompt2.check_result = Mock()
        mock_prompt2.check_result.overall_score = 85.0
        mock_prompt2.check_result.is_passing_grade.return_value = True

        self.mock_prompt_repository.find_by_episode.return_value = [mock_prompt1, mock_prompt2]

        # テスト実行
        results = await self.use_case.get_existing_prompts("Test Project", 1)

        # 検証
        assert len(results) == 2
        assert results[0]["prompt_id"] == "prompt-1"
        assert results[0]["check_level"] == "standard"
        assert results[0]["has_result"] is False

        assert results[1]["prompt_id"] == "prompt-2"
        assert results[1]["check_level"] == "claude_optimized"
        assert results[1]["has_result"] is True
        assert results[1]["overall_score"] == 85.0
        assert results[1]["is_passing"] is True

    @pytest.mark.asyncio
    async def test_delete_prompt_success(self):
        """プロンプト削除成功テスト"""
        self.mock_prompt_repository.delete.return_value = True

        result = await self.use_case.delete_prompt("test-prompt-123")

        assert result is True
        self.mock_prompt_repository.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_prompt_failure(self):
        """プロンプト削除失敗テスト"""
        self.mock_prompt_repository.delete.return_value = False

        result = await self.use_case.delete_prompt("nonexistent-prompt")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_repository_statistics(self):
        """リポジトリ統計取得テスト"""
        expected_stats = {
            "total_prompts": 10,
            "level_distribution": {"standard": 5, "claude_optimized": 3, "basic": 2},
            "project_distribution": {"Project A": 6, "Project B": 4},
        }

        self.mock_prompt_repository.get_statistics.return_value = expected_stats

        result = await self.use_case.get_repository_statistics()

        assert result == expected_stats

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT_USE_CASE-GET_DEFAULT_PLOT_PAT")
    def test_get_default_plot_path(self):
            """デフォルトプロットパス取得テスト"""
            stage4_file = self.plot_dir / "第001話_stage4.yaml"
            stage4_file.write_text("dummy stage4", encoding="utf-8")

            plot_path = self.use_case._get_default_plot_path("Test Project", 1)
            assert plot_path == stage4_file

            stage4_file.unlink()
            plot_path = self.use_case._get_default_plot_path("Test Project", 1)
            assert plot_path == self.plot_dir / "第001話.yaml"


@pytest.mark.spec("SPEC-STAGE5-SEPARATION")
class TestQualityCheckPromptUseCaseFactory:
    """品質チェックプロンプトユースケースファクトリーのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT_USE_CASE-CREATE_USE_CASE_WITH")
    def test_create_use_case_with_defaults(self):
        """デフォルト設定でのユースケース作成テスト"""
        use_case = QualityCheckPromptUseCaseFactory.create_use_case()

        assert isinstance(use_case, QualityCheckPromptUseCase)
        assert use_case._prompt_generator is not None
        assert use_case._prompt_repository is not None

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT_USE_CASE-CREATE_USE_CASE_WITH")
    def test_create_use_case_with_custom_storage(self):
        """カスタム保存ディレクトリでのユースケース作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_dir = Path(temp_dir) / "custom_storage"

            with patch(
                "noveler.presentation.shared.shared_utilities.get_common_path_service"
            ) as mock_get_common_path_service:
                mock_path_service = Mock()
                mock_path_service.get_episode_prompts_dir.return_value = storage_dir
                mock_get_common_path_service.return_value = mock_path_service

                use_case = QualityCheckPromptUseCaseFactory.create_use_case(storage_directory=storage_dir)

            assert isinstance(use_case, QualityCheckPromptUseCase)
            assert storage_dir.exists()

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT_USE_CASE-CREATE_USE_CASE_WITH")
    def test_create_use_case_with_common_path_service(self):
        """共通パスサービス付きユースケース作成テスト"""
        mock_path_service = Mock()
        mock_path_service.get_episode_prompts_dir.return_value = Path(tempfile.mkdtemp())

        use_case = QualityCheckPromptUseCaseFactory.create_use_case(common_path_service=mock_path_service)

        assert isinstance(use_case, QualityCheckPromptUseCase)
        assert use_case._common_path_service == mock_path_service
