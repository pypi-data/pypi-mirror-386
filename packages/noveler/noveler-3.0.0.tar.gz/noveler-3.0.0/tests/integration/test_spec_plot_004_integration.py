"""SPEC-PLOT-004統合テスト

Enhanced Claude Code Integration Phase 2の統合テスト
"""

import tempfile
from datetime import timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.application.use_cases.enhanced_plot_generation_use_case import EnhancedPlotGenerationUseCase
from noveler.domain.entities.contextual_plot_generation import ContextualPlotResult, PlotGenerationConfig
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.presentation.shared.shared_utilities import get_common_path_service


@pytest.mark.spec("SPEC-PLOT-004")
class TestSPECPLOT004Integration:
    """SPEC-PLOT-004統合テスト"""

    @pytest.mark.spec("SPEC-SPEC_PLOT_004_INTEGRATION-END_TO_END_ENHANCED_")
    def test_end_to_end_enhanced_plot_generation(self) -> None:
        """エンドツーエンド拡張プロット生成テスト"""
        # テスト用の一時ディレクトリ作成
        path_service = get_common_path_service()
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # 必要なディレクトリ構造作成
            (project_root / str(path_service.get_plots_dir()) / "章別プロット").mkdir(parents=True, exist_ok=True)
            (project_root / "30_話別プロット_Enhanced").mkdir(parents=True, exist_ok=True)

            # 章プロット情報を作成（モック）
            chapter_plot_path = project_root / str(path_service.get_plots_dir()) / "章別プロット" / "chapter01.yaml"
            chapter_plot_content = """
chapter_number: 1
title: "ch01　Fランク魔法使いの憂鬱"
central_theme: "DEBUG能力の発見と成長"
key_events:
  - "DEBUG能力発覚"
  - "アサート少女との出会い"
episodes:
  - episode_number: 7
    title: "第007話　ペアプログラミング魔法入門"
    summary: "直人とあすかが協調魔法を学ぶエピソード"
viewpoint_management:
  primary: "直人一人称視点"
"""
            chapter_plot_path.write_text(chapter_plot_content, encoding="utf-8")

            # テスト実行 - B30品質作業指示書遵守: 適切なDI使用
            mock_repository_factory = Mock()
            mock_repository_factory.create_yaml_chapter_plot_repository = Mock()
            mock_repository_factory.create_enhanced_plot_result_repository = Mock()
            use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

            # モックの設定
            mock_chapter_repo = Mock()
            mock_chapter_plot = Mock()
            mock_chapter_plot.chapter_number.value = 1
            mock_chapter_plot.central_theme = "DEBUG能力の発見と成長"
            mock_chapter_plot.key_events = ["DEBUG能力発覚", "アサート少女との出会い"]
            mock_chapter_plot.episodes = [
                {
                    "episode_number": 7,
                    "title": "第007話　ペアプログラミング魔法入門",
                    "summary": "直人とあすかが協調魔法を学ぶエピソード",
                }
            ]
            mock_chapter_plot.viewpoint_management = {"primary": "直人一人称視点"}

            mock_chapter_repo.get_chapter_plot.return_value = mock_chapter_plot
            use_case._chapter_repository = mock_chapter_repo

            # 拡張サービスのモック
            mock_enhanced_service = Mock()
            from datetime import datetime

            from noveler.domain.entities.contextual_plot_generation import QualityIndicators

            mock_result = ContextualPlotResult(
                episode_number=EpisodeNumber(7),
                content="高品質な生成プロット内容...",
                quality_indicators=QualityIndicators(
                    technical_accuracy=92.0, character_consistency=88.0, plot_coherence=90.0
                ),
                generation_timestamp=datetime.now(timezone.utc),
                metadata={"generation_method": "enhanced_contextual"},
            )

            mock_enhanced_service.generate_contextual_plot.return_value = mock_result
            use_case._enhanced_service = mock_enhanced_service

            # 結果リポジトリのモック
            mock_result_repo = Mock()
            use_case._result_repository = mock_result_repo

            # テスト実行
            config = PlotGenerationConfig(
                target_word_count=6000,
                technical_accuracy_required=True,
                character_consistency_check=True,
                scene_structure_enhanced=True,
            )

            result = use_case.generate_enhanced_episode_plot(
                episode_number=7, config=config, save_result=True, project_root=project_root
            )

            # 結果検証
            assert isinstance(result, ContextualPlotResult)
            assert result.episode_number == EpisodeNumber(7)
            assert result.quality_indicators.overall_score >= 85.0
            assert "quality_report" in result.metadata

            # 品質指標の検証
            quality_indicators = result.quality_indicators
            assert quality_indicators.technical_accuracy >= 80.0
            assert quality_indicators.character_consistency >= 80.0
            assert quality_indicators.plot_coherence >= 75.0

            # サービス呼び出しの検証
            mock_enhanced_service.generate_contextual_plot.assert_called_once()
            mock_result_repo.save_result.assert_called_once_with(result)

    @pytest.mark.spec("SPEC-SPEC_PLOT_004_INTEGRATION-QUALITY_FOCUSED_REGE")
    def test_quality_focused_regeneration_integration(self) -> None:
        """品質重視再生成の統合テスト"""
        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock()
        mock_repository_factory.create_enhanced_plot_result_repository = Mock()
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # モックの設定
        mock_chapter_repo = Mock()
        mock_chapter_plot = Mock()
        mock_chapter_plot.chapter_number.value = 1
        mock_chapter_plot.central_theme = "テスト章テーマ"
        mock_chapter_plot.key_events = ["テストイベント"]
        mock_chapter_plot.episodes = [{"episode_number": 7, "title": "テスト話", "summary": "テスト概要"}]

        mock_chapter_repo.get_chapter_plot.return_value = mock_chapter_plot
        use_case._chapter_repository = mock_chapter_repo

        # 段階的に品質が向上するモック結果
        from datetime import datetime

        from noveler.domain.entities.contextual_plot_generation import QualityIndicators

        results = []
        for i, score in enumerate([75.0, 82.0, 88.0]):
            result = ContextualPlotResult(
                episode_number=EpisodeNumber(7),
                content=f"プロット内容 試行{i + 1}",
                quality_indicators=QualityIndicators(
                    technical_accuracy=score, character_consistency=score - 2.0, plot_coherence=score - 1.0
                ),
                generation_timestamp=datetime.now(timezone.utc),
                metadata={"attempt": i + 1},
            )

            results.append(result)

        # generate_enhanced_episode_plotをモック
        use_case.generate_enhanced_episode_plot = Mock(side_effect=results)

        # テスト実行
        result = use_case.regenerate_with_improved_quality(episode_number=7, quality_threshold=85.0, max_attempts=3)

        # 結果検証
        assert isinstance(result, ContextualPlotResult)
        assert result.quality_indicators.technical_accuracy >= 85.0
        # 3回試行されることを確認
        assert use_case.generate_enhanced_episode_plot.call_count == 3

    @pytest.mark.spec("SPEC-SPEC_PLOT_004_INTEGRATION-BATCH_GENERATION_INT")
    def test_batch_generation_integration(self) -> None:
        """一括生成の統合テスト"""
        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # generate_enhanced_episode_plotをモック
        def mock_generate(episode_number, **kwargs):
            from datetime import datetime

            from noveler.domain.entities.contextual_plot_generation import QualityIndicators

            if episode_number == 8:
                # エピソード8で失敗をシミュレート
                msg = f"エピソード{episode_number}生成失敗"
                raise Exception(msg)

            return ContextualPlotResult(
                episode_number=EpisodeNumber(episode_number),
                content=f"第{episode_number:03d}話プロット内容",
                quality_indicators=QualityIndicators(
                    technical_accuracy=85.0, character_consistency=83.0, plot_coherence=87.0
                ),
                generation_timestamp=datetime.now(timezone.utc),
                metadata={"batch_generation": True},
            )

        use_case.generate_enhanced_episode_plot = Mock(side_effect=mock_generate)

        # テスト実行
        results = use_case.batch_generate_enhanced_plots([7, 8, 9])

        # 結果検証
        assert len(results) == 2  # エピソード8は失敗
        assert 7 in results
        assert 9 in results
        assert 8 not in results

        # 成功した結果の検証
        assert isinstance(results[7], ContextualPlotResult)
        assert isinstance(results[9], ContextualPlotResult)

    @pytest.mark.spec("SPEC-SPEC_PLOT_004_INTEGRATION-CONFIGURATION_VALIDA")
    def test_configuration_validation_integration(self) -> None:
        """設定検証の統合テスト"""
        # 有効な設定
        valid_config = PlotGenerationConfig(
            target_word_count=5000,
            technical_accuracy_required=True,
            character_consistency_check=True,
            scene_structure_enhanced=True,
        )

        assert valid_config.is_valid() is True

        # 無効な設定（文字数が少なすぎる）
        invalid_config = PlotGenerationConfig(
            target_word_count=1000  # 最小値以下
        )
        assert invalid_config.is_valid() is False

        # 無効な設定（文字数が多すぎる）
        invalid_config_2 = PlotGenerationConfig(
            target_word_count=10000  # 最大値以上
        )
        assert invalid_config_2.is_valid() is False

    @pytest.mark.spec("SPEC-SPEC_PLOT_004_INTEGRATION-QUALITY_GRADE_CALCUL")
    def test_quality_grade_calculation_integration(self) -> None:
        """品質グレード計算の統合テスト"""
        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # 各グレードのテスト
        test_cases = [(97.0, "A+"), (92.0, "A"), (87.0, "B+"), (82.0, "B"), (77.0, "C+"), (72.0, "C"), (65.0, "D")]

        for score, expected_grade in test_cases:
            actual_grade = use_case._calculate_quality_grade(score)
            assert actual_grade == expected_grade, (
                f"スコア{score}のグレードが{expected_grade}であるべきところ{actual_grade}でした"
            )

    @patch("noveler.infrastructure.integrations.claude_code_session_interface.is_claude_code_environment")
    def test_claude_code_environment_detection(self, mock_claude_env) -> None:
        """Claude Code環境検出の統合テスト"""
        from noveler.domain.services.enhanced_plot_generation_service import EnhancedPlotGenerationService

        # Claude Code環境内での実行
        mock_claude_env.return_value = True
        EnhancedPlotGenerationService()

        # 環境検出の確認
        assert mock_claude_env.return_value is True

        # Claude Code環境外での実行
        mock_claude_env.return_value = False
        assert mock_claude_env.return_value is False
