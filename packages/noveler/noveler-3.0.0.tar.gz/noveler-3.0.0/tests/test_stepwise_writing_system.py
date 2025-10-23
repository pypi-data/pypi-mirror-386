#!/usr/bin/env python3
"""15ステップ執筆システム包括テスト

SPEC-STEPWISE-WRITING-001準拠システムの統合テスト
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# テスト用のパス設定
test_root = Path(__file__).parent.parent
sys.path.insert(0, str(test_root / "src"))

try:
    from noveler.application.use_cases.stepwise_writing_use_case import (
        StepwiseWritingRequest,
        StepwiseWritingResponse,
        StepwiseWritingUseCase,
    )
    from noveler.domain.services.step_selector_service import StepSelectorService
    from noveler.domain.services.work_file_manager import WorkFile, WorkFileManager
    from noveler.domain.services.writing_steps.manuscript_generator_service import ManuscriptGeneratorService
    from noveler.domain.services.writing_steps.plot_analyzer_service import PlotAnalyzerService
    from noveler.domain.services.writing_steps.scope_definer_service import ScopeDefinerService
except ImportError as e:
    pytest.skip(f"必要なモジュールのインポートに失敗: {e}", allow_module_level=True)


class TestStepSelectorService:
    """StepSelectorServiceのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.step_selector = StepSelectorService()

    @pytest.mark.spec("SPEC-STEPWISE_WRITING_SYSTEM-PARSE_STEP_PATTERN_A")
    def test_parse_step_pattern_all(self):
        """全ステップパターンのテスト"""
        result = self.step_selector.parse_step_pattern("all")
        expected = list(range(16))  # 0-15
        assert result == expected

    @pytest.mark.spec("SPEC-STEPWISE_WRITING_SYSTEM-PARSE_STEP_PATTERN_R")
    def test_parse_step_pattern_range(self):
        """範囲パターンのテスト"""
        result = self.step_selector.parse_step_pattern("0-3")
        expected = [0, 1, 2, 3]
        assert result == expected

    @pytest.mark.spec("SPEC-STEPWISE_WRITING_SYSTEM-PARSE_STEP_PATTERN_S")
    def test_parse_step_pattern_single(self):
        """単一ステップパターンのテスト"""
        result = self.step_selector.parse_step_pattern("5")
        expected = [5]
        assert result == expected

    @pytest.mark.spec("SPEC-STEPWISE_WRITING_SYSTEM-PARSE_STEP_PATTERN_M")
    def test_parse_step_pattern_multiple(self):
        """複数ステップパターンのテスト"""
        result = self.step_selector.parse_step_pattern("0,5,10")
        expected = [0, 5, 10]
        assert result == expected

    @pytest.mark.spec("SPEC-STEPWISE_WRITING_SYSTEM-PARSE_STEP_PATTERN_G")
    def test_parse_step_pattern_group_aliases(self):
        """グループエイリアスのテスト"""
        result = self.step_selector.parse_step_pattern("structure")
        # 構造関連ステップが含まれているか確認
        assert 3 in result  # narrative_structure
        assert 4 in result  # scene_designer
        assert len(result) > 2

    @pytest.mark.spec("SPEC-STEPWISE_WRITING_SYSTEM-PARSE_STEP_PATTERN_R")
    def test_parse_step_pattern_regex(self):
        """正規表現パターンのテスト"""
        result = self.step_selector.parse_step_pattern(".*optimizer")
        assert 11 in result  # content_optimizer


class TestWorkFileManager:
    """WorkFileManagerのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.work_file_manager = WorkFileManager()

    def teardown_method(self):
        """テストクリーンアップ"""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.spec("SPEC-STEPWISE_WRITING_SYSTEM-CREATE_WORK_FILE")
    def test_create_work_file(self):
        """作業ファイル作成のテスト"""
        work_file = self.work_file_manager.create_work_file(
            episode_number=1,
            step_number=0,
            version=1,
            data={"test": "data"}
        )

        assert isinstance(work_file, WorkFile)
        assert work_file.episode_number == 1
        assert work_file.step_number == 0
        assert work_file.version == 1
        assert work_file.data == {"test": "data"}

    @pytest.mark.spec("SPEC-STEPWISE_WRITING_SYSTEM-GENERATE_FILENAME")
    def test_generate_filename(self):
        """ファイル名生成のテスト"""
        filename = self.work_file_manager.generate_filename(
            episode_number=1,
            step_number=5,
            version=2
        )

        expected = "episode001_step05_v2.yaml"
        assert filename == expected

    @pytest.mark.asyncio
    async def test_save_and_load_work_file(self):
        """ファイル保存・読み込みのテスト"""
        with patch.object(self.work_file_manager, "_get_work_files_dir") as mock_dir:
            mock_dir.return_value = Path(self.temp_dir)

            # テストデータ
            test_data = {
                "step_name": "test_step",
                "success": True,
                "result": "test_result"
            }

            # 保存テスト
            saved_file = await self.work_file_manager.save_work_file(
                episode_number=1,
                step_number=0,
                version=1,
                data=test_data
            )

            assert saved_file is not None
            assert saved_file.episode_number == 1
            assert saved_file.step_number == 0

            # 読み込みテスト
            loaded_data = await self.work_file_manager.load_work_file(
                episode_number=1,
                step_number=0
            )

            assert loaded_data is not None
            assert loaded_data["step_name"] == "test_step"
            assert loaded_data["success"] is True


class TestScopeDefinerService:
    """ScopeDefinerServiceのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_logger = Mock()
        self.mock_path_service = Mock()

        self.scope_definer = ScopeDefinerService(
            logger_service=self.mock_logger,
            path_service=self.mock_path_service
        )

    @pytest.mark.asyncio
    async def test_execute_basic(self):
        """基本実行のテスト"""
        # モックの設定
        self.mock_path_service.get_project_root.return_value = Path("/test/project")

        # 実行
        result = await self.scope_definer.execute(episode_number=1)

        # 検証
        assert result is not None
        assert hasattr(result, "success")
        assert hasattr(result, "step_number")
        assert result.step_number == 0
        assert result.step_name == "scope_definer"

    @pytest.mark.asyncio
    async def test_execute_with_previous_results(self):
        """前ステップ結果ありの実行テスト"""
        previous_results = {}

        # 実行
        result = await self.scope_definer.execute(
            episode_number=1,
            previous_results=previous_results
        )

        # 検証
        assert result is not None
        assert hasattr(result, "success")


class TestPlotAnalyzerService:
    """PlotAnalyzerServiceのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_logger = Mock()
        self.mock_path_service = Mock()

        self.plot_analyzer = PlotAnalyzerService(
            logger_service=self.mock_logger,
            path_service=self.mock_path_service
        )

    @pytest.mark.asyncio
    async def test_execute_basic(self):
        """基本実行のテスト"""
        # モックの設定
        self.mock_path_service.get_plot_dir.return_value = Path("/test/plot")

        # 前ステップの結果をモック
        previous_results = {
            0: Mock(
                success=True,
                scope_result=Mock(project_root="/test/project")
            )
        }

        # 実行
        result = await self.plot_analyzer.execute(
            episode_number=1,
            previous_results=previous_results
        )

        # 検証
        assert result is not None
        assert hasattr(result, "success")
        assert result.step_number == 1
        assert result.step_name == "plot_analyzer"


class TestManuscriptGeneratorService:
    """ManuscriptGeneratorServiceのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_logger = Mock()
        self.mock_path_service = Mock()

        self.manuscript_generator = ManuscriptGeneratorService(
            logger_service=self.mock_logger,
            path_service=self.mock_path_service
        )

    @pytest.mark.asyncio
    async def test_execute_basic(self):
        """基本実行のテスト"""
        # モックの設定
        self.mock_path_service.get_manuscript_dir.return_value = Path("/test/manuscript")
        self.mock_path_service.get_prompts_dir.return_value = Path("/test/prompts")

        # 前ステップの結果をモック
        previous_results = {
            0: Mock(success=True, scope_result=Mock(project_root="/test/project")),
            1: Mock(success=True, analysis_result=Mock(plot_exists=True)),
            2: Mock(success=True, context_result=Mock(character_contexts=[])),
        }

        # 実行
        result = await self.manuscript_generator.execute(
            episode_number=1,
            previous_results=previous_results
        )

        # 検証
        assert result is not None
        assert hasattr(result, "success")
        assert result.step_number == 10
        assert result.step_name == "manuscript_generator"


class TestStepwiseWritingUseCase:
    """StepwiseWritingUseCaseの統合テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.mock_logger = Mock()
        self.mock_unit_of_work = Mock()
        self.mock_path_service = Mock()

        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # ユースケース初期化
        self.use_case = StepwiseWritingUseCase(
            logger_service=self.mock_logger,
            unit_of_work=self.mock_unit_of_work,
            path_service=self.mock_path_service
        )

    def teardown_method(self):
        """テストクリーンアップ"""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_execute_single_step(self):
        """単一ステップ実行のテスト"""
        request = StepwiseWritingRequest(
            project_root=self.project_root,
            episode_number=1,
            step_pattern="0",  # STEP 0のみ
            resume_from_cache=False,
            save_intermediate_results=False
        )

        # ステップサービスのモック
        mock_step_service = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.step_name = "scope_definer"
        mock_step_service.execute = AsyncMock(return_value=mock_result)

        self.use_case._step_services[0] = mock_step_service

        # 実行
        response = await self.use_case.execute(request)

        # 検証
        assert isinstance(response, StepwiseWritingResponse)
        assert response.success is True
        assert response.episode_number == 1
        assert 0 in response.executed_steps
        assert response.successful_steps == 1
        assert response.failed_steps == 0

    @pytest.mark.asyncio
    async def test_execute_multiple_steps(self):
        """複数ステップ実行のテスト"""
        request = StepwiseWritingRequest(
            project_root=self.project_root,
            episode_number=1,
            step_pattern="0,1",  # STEP 0,1
            resume_from_cache=False,
            save_intermediate_results=False
        )

        # ステップサービスのモック
        for step_num in [0, 1]:
            mock_step_service = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.step_name = f"step_{step_num}"
            mock_step_service.execute = AsyncMock(return_value=mock_result)

            self.use_case._step_services[step_num] = mock_step_service

        # 実行
        response = await self.use_case.execute(request)

        # 検証
        assert response.success is True
        assert len(response.executed_steps) == 2
        assert 0 in response.executed_steps
        assert 1 in response.executed_steps
        assert response.successful_steps == 2
        assert response.failed_steps == 0

    @pytest.mark.asyncio
    async def test_execute_with_error(self):
        """エラー発生時のテスト"""
        request = StepwiseWritingRequest(
            project_root=self.project_root,
            episode_number=1,
            step_pattern="0",
            resume_from_cache=False,
            save_intermediate_results=False
        )

        # エラーが発生するステップサービスのモック
        mock_step_service = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "テストエラー"
        mock_step_service.execute = AsyncMock(return_value=mock_result)

        self.use_case._step_services[0] = mock_step_service

        # 実行
        response = await self.use_case.execute(request)

        # 検証
        assert response.success is True  # システム全体は成功（ステップが失敗しても継続）
        assert response.failed_steps == 1
        assert response.successful_steps == 0

    @pytest.mark.asyncio
    async def test_execute_with_invalid_pattern(self):
        """無効なパターンのテスト"""
        request = StepwiseWritingRequest(
            project_root=self.project_root,
            episode_number=1,
            step_pattern="invalid_pattern",
            resume_from_cache=False
        )

        # 実行
        response = await self.use_case.execute(request)

        # 無効なパターンでも基本的にはエラーにならない（空の結果）
        assert isinstance(response, StepwiseWritingResponse)


class TestSystemIntegration:
    """システム統合テスト"""

    def setup_method(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # 必要なディレクトリ作成
        (self.project_root / "設定").mkdir(exist_ok=True)
        (self.project_root / "プロット").mkdir(exist_ok=True)
        (self.project_root / "原稿").mkdir(exist_ok=True)

    def teardown_method(self):
        """テストクリーンアップ"""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.spec("SPEC-STEPWISE_WRITING_SYSTEM-STEP_SELECTOR_INTEGR")
    def test_step_selector_integration(self):
        """ステップセレクター統合テスト"""
        selector = StepSelectorService()

        # 各種パターンのテスト
        test_cases = [
            ("all", lambda r: len(r) == 16),
            ("0-2", lambda r: r == [0, 1, 2]),
            ("0,5,10", lambda r: r == [0, 5, 10]),
            ("structure", lambda r: len(r) > 0 and 3 in r),
        ]

        for pattern, validator in test_cases:
            result = selector.parse_step_pattern(pattern)
            assert validator(result), f"パターン '{pattern}' のテストに失敗: {result}"

    @pytest.mark.spec("SPEC-STEPWISE_WRITING_SYSTEM-WORK_FILE_MANAGER_IN")
    def test_work_file_manager_integration(self):
        """作業ファイルマネージャー統合テスト"""
        manager = WorkFileManager()

        # ファイル名生成テスト
        filename = manager.generate_filename(1, 0, 1)
        assert filename == "episode001_step00_v1.yaml"

        # WorkFile作成テスト
        work_file = manager.create_work_file(1, 0, 1, {"test": "data"})
        assert work_file.episode_number == 1
        assert work_file.step_number == 0
        assert work_file.version == 1


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "--tb=short"])
