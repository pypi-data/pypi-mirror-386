"""
プロンプト保存機能統合テスト

SPEC-PROMPT-SAVE-001: プロンプト保存機能仕様書準拠
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from noveler.application.use_cases.episode_prompt_save_use_case import (
    EpisodePromptSaveUseCase,
    PromptSaveRequest,
)
from noveler.application.use_cases.plot_generation_use_case import PlotGenerationUseCase
from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.services.enhanced_prompt_template_service import (
    EnhancedPromptContext,
    EnhancedPromptTemplateService,
)
from noveler.domain.value_objects.chapter_number import ChapterNumber
from noveler.presentation.shared.shared_utilities import get_common_path_service


@pytest.mark.spec("SPEC-PROMPT-SAVE-001")
class TestEnhancedPromptSaveIntegration:
    """プロンプト保存機能統合テスト"""

    def setup_method(self) -> None:
        """テストメソッド前処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        # CommonPathService統合対応

        path_service = get_common_path_service(self.project_root)
        path_service = get_common_path_service()
        self.prompt_dir = path_service.get_prompts_dir() / "話別プロット"
        self.prompt_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self) -> None:
        """テストメソッド後処理"""

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.spec("SPEC-ENHANCED_PROMPT_SAVE_INTEGRATION-EPISODE_PROMPT_SAVE_")
    def test_episode_prompt_save_use_case_integration(self) -> None:
        """エピソードプロンプト保存ユースケース統合テスト"""
        # テストデータ準備
        prompt_content = "x" * 200  # 200文字の詳細プロンプト

        request = PromptSaveRequest(
            episode_number=5,
            episode_title="統合テストエピソード",
            prompt_content=prompt_content,
            project_root=self.project_root,
            content_sections={"test_section": "test_data", "scenes": ["scene1", "scene2"]},

        )
        # ユースケース実行
        use_case = EpisodePromptSaveUseCase()
        response = use_case.execute(request)

        # 結果検証
        assert response.success is True
        assert response.saved_file_path is not None
        assert response.episode_prompt is not None
        assert response.quality_score > 0.0

        # ファイル存在確認
        expected_filename = "第005話_統合テストエピソード.yaml"
        expected_path = self.prompt_dir / expected_filename
        assert expected_path.exists()

        # ファイル内容確認
        with expected_path.open("r", encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["metadata"]["episode_number"] == 5
        assert saved_data["metadata"]["title"] == "統合テストエピソード"
        assert saved_data["prompt_content"] == prompt_content
        assert saved_data["content_sections"]["test_section"] == "test_data"

    @pytest.mark.spec("SPEC-ENHANCED_PROMPT_SAVE_INTEGRATION-PLOT_GENERATION_WITH")
    def test_plot_generation_with_prompt_save_integration(self) -> None:
        """プロット生成＋プロンプト保存統合テスト"""
        # PlotGenerationUseCaseのモック準備
        with patch.dict("os.environ", {"PROJECT_ROOT": str(self.project_root)}):
            # モック設定
            mock_chapter_plot_info = {
                "chapter_number": 1,
                "title": "Test Chapter",
                "summary": "Test chapter summary",
                "episodes": [{"episode_number": 7, "title": "統合テストプロット", "summary": "Test episode summary"}],
            }

            # プロット生成結果のモック
            with patch(
                "noveler.application.use_cases.plot_generation_use_case.PlotGenerationUseCase._orchestrator"
            ) as mock_orchestrator:
                mock_result = Mock()
                mock_result.success = True
                mock_result.generated_plot = "Generated plot content for testing"
                mock_result.quality_score = 0.85
                mock_orchestrator.generate_plot.return_value = mock_result

                # プロンプト保存機能が有効な状態でプロット生成実行
                use_case = PlotGenerationUseCase()

                # _save_enhanced_promptメソッドのモック（実際の保存処理は回避）
                with patch.object(use_case, "_save_enhanced_prompt") as mock_save:
                    result = use_case.generate_episode_plot_auto(
                        episode_number=7, chapter_plot_info=mock_chapter_plot_info, enable_prompt_save=True
                    )

                    # 結果検証
                    assert result is not None

                    # プロンプト保存メソッドが呼び出されたことを確認
                    mock_save.assert_called_once_with(7, mock_chapter_plot_info, mock_result, self.project_root)

    @pytest.mark.spec("SPEC-ENHANCED_PROMPT_SAVE_INTEGRATION-ENHANCED_PROMPT_TEMP")
    def test_enhanced_prompt_template_service_integration(self) -> None:
        """強化プロンプトテンプレートサービス統合テスト"""

        # テストコンテキスト準備
        chapter_plot = ChapterPlot(
            chapter_number=ChapterNumber(1),
            title="Test Chapter",
            summary="Test chapter summary",
            episode_range=(1, 20),
            key_events=["event1", "event2"],
            character_arcs={},
            foreshadowing_elements={},
        )
        context = EnhancedPromptContext(
            episode_number=10,
            episode_title="テンプレートテストエピソード",
            chapter_plot=chapter_plot,
            previous_episodes=[],
            following_episodes=[],
            project_context={"project_root": str(self.project_root)},
        )

        # 強化プロンプト生成
        service = EnhancedPromptTemplateService()
        enhanced_prompt = service.generate_enhanced_prompt(context)

        # 結果検証
        assert enhanced_prompt is not None
        assert isinstance(enhanced_prompt, str)
        assert len(enhanced_prompt) > 1000  # 詳細化要件：大幅な情報量増加

        # 必須セクションの存在確認
        required_sections = [
            "第010話：テンプレートテストエピソード",
            "# シーン構成",
            "# キャラクター成長",
            "# 伏線要素",
            "# 品質チェック項目",
        ]

        for section in required_sections:
            assert section in enhanced_prompt, f"Required section missing: {section}"

    @pytest.mark.spec("SPEC-ENHANCED_PROMPT_SAVE_INTEGRATION-FILE_NAMING_CONVENTI")
    def test_file_naming_convention_compliance(self) -> None:
        """ファイル命名規則準拠テスト"""
        test_cases = [
            (1, "テスト", "第001話_テスト.yaml"),
            (42, "長いタイトル名", "第042話_長いタイトル名.yaml"),
            (999, "最終話", "第999話_最終話.yaml"),
        ]

        for episode_number, title, expected_filename in test_cases:
            request = PromptSaveRequest(
                episode_number=episode_number,
                episode_title=title,
                prompt_content="x" * 150,
                project_root=self.project_root,
            )

            use_case = EpisodePromptSaveUseCase()
            response = use_case.execute(request)

            assert response.success is True
            assert response.saved_file_path.name == expected_filename

    @pytest.mark.spec("SPEC-ENHANCED_PROMPT_SAVE_INTEGRATION-COMMON_PATH_SERVICE_")
    def test_common_path_service_integration(self) -> None:
        """CommonPathService統合テスト"""
        with patch.dict("os.environ", {"PROJECT_ROOT": str(self.project_root)}):
            request = PromptSaveRequest(episode_number=15, episode_title="パスサービステスト", prompt_content="x" * 150)
            # project_rootを明示せず、環境変数から取得

            use_case = EpisodePromptSaveUseCase()
            response = use_case.execute(request)

            assert response.success is True

            # 正しいディレクトリ構造で保存されることを確認
            # CommonPathService統合対応
            path_service = get_common_path_service()
            expected_dir = path_service.get_prompts_dir() / "話別プロット"
            assert response.saved_file_path.parent == expected_dir

    @pytest.mark.spec("SPEC-ENHANCED_PROMPT_SAVE_INTEGRATION-ERROR_HANDLING_INTEG")
    def test_error_handling_integration(self) -> None:
        """エラーハンドリング統合テスト"""
        # 不正なプロジェクトルートでテスト
        invalid_root = Path("/nonexistent/path")

        request = PromptSaveRequest(
            episode_number=1,
            episode_title="エラーテスト",
            prompt_content="x" * 150,
            project_root=invalid_root,
        )

        use_case = EpisodePromptSaveUseCase()
        response = use_case.execute(request)

        # エラー処理が適切に動作することを確認
        assert response.success is False
        assert response.error_message is not None
        assert "エラー" in response.error_message or "Error" in response.error_message

    @pytest.mark.spec("SPEC-ENHANCED_PROMPT_SAVE_INTEGRATION-YAML_CONTENT_QUALITY")
    def test_yaml_content_quality_validation(self) -> None:
        """YAML内容品質バリデーションテスト"""
        request = PromptSaveRequest(
            episode_number=20,
            episode_title="品質テストエピソード",
            prompt_content="x" * 300,  # 高品質コンテンツ
            project_root=self.project_root,
            content_sections={"section1": "data1", "section2": "data2", "section3": "data3"},
        )

        use_case = EpisodePromptSaveUseCase()
        response = use_case.execute(request)

        assert response.success is True
        assert response.quality_score > 0.5  # 品質スコア閾値確認

        # 保存されたファイルの品質検証

        with response.saved_file_path.Path("r").open(encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        # メタデータの完全性確認
        metadata = saved_data["metadata"]
        assert metadata["spec_id"] == "SPEC-PROMPT-SAVE-001"
        assert "generation_timestamp" in metadata
        assert "template_version" in metadata

        # バリデーション情報の確認
        validation = saved_data["validation"]
        assert validation["quality_validated"] is True
        assert validation["content_length"] == len(request.prompt_content)
        assert validation["sections_count"] == len(request.content_sections)
