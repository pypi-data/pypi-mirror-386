"""Enhanced Plot Generation Use Case のテスト

SPEC-PLOT-004: Enhanced Claude Code Integration Phase 2
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.application.use_cases.enhanced_plot_generation_use_case import EnhancedPlotGenerationUseCase
from noveler.domain.entities.contextual_plot_generation import (
    ContextualPlotResult,
    PlotGenerationConfig,
    QualityIndicators,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.presentation.shared.shared_utilities import get_common_path_service


@pytest.mark.spec("SPEC-PLOT-004")
class TestEnhancedPlotGenerationUseCase:
    """Enhanced Plot Generation Use Case のテスト"""

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-USE_CASE_INITIALIZAT")
    def test_use_case_initialization(self) -> None:
        """ユースケース初期化のテスト"""
        # Arrange - Mock Repository Factory for DI compliance
        get_common_path_service()
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())

        # Act
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # Assert
        assert use_case is not None
        assert use_case._enhanced_service is not None
        assert use_case._chapter_repository is not None
        assert use_case._result_repository is not None

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-USE_CASE_INITIALIZAT")
    def test_use_case_initialization_with_dependency_injection(self) -> None:
        """依存注入によるユースケース初期化のテスト"""
        # Arrange - Mock Repository Factory for B30 compliance
        mock_service = Mock()
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())

        # Act
        use_case = EnhancedPlotGenerationUseCase(
            enhanced_service=mock_service, repository_factory=mock_repository_factory
        )

        # Assert
        assert use_case._enhanced_service == mock_service
        assert use_case._chapter_repository is not None
        assert use_case._result_repository is not None

    @patch("noveler.application.use_cases.enhanced_plot_generation_use_case.Path")
    def test_generate_enhanced_episode_plot_basic_flow(self, mock_path) -> None:
        """基本的な拡張エピソードプロット生成フローのテスト"""
        # Arrange
        mock_path.cwd.return_value = Path("/test/project")

        # B30 compliance: Mock Repository Factory
        mock_repository_factory = Mock()
        mock_chapter_repo = Mock()
        mock_result_repo = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=mock_chapter_repo)
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=mock_result_repo)

        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # モックの設定
        mock_chapter_plot = self._create_mock_chapter_plot()
        mock_result = self._create_mock_contextual_plot_result()

        # B30品質作業指示書遵守: 実装の実際の呼び出しメソッドに合わせる
        mock_chapter_repo.find_by_chapter_number = Mock(return_value=mock_chapter_plot)
        use_case._enhanced_service.generate_contextual_plot = Mock(return_value=mock_result)
        mock_result_repo.save_result = Mock()
        mock_result_repo.set_project_root = Mock()
        mock_chapter_repo.set_project_root = Mock()

        # Act
        result = use_case.generate_enhanced_episode_plot(
            episode_number=7, config=PlotGenerationConfig(target_word_count=6000), save_result=True
        )

        # Assert
        assert isinstance(result, ContextualPlotResult)
        assert result.episode_number == EpisodeNumber(7)
        assert "quality_report" in result.metadata
        mock_result_repo.save_result.assert_called_once()

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-GENERATE_ENHANCED_EP")
    def test_generate_enhanced_episode_plot_with_invalid_episode_number(self) -> None:
        """無効なエピソード番号での生成テスト"""
        # Arrange - Mock Repository Factory for B30 compliance
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())

        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid episode number"):
            use_case.generate_enhanced_episode_plot(episode_number=0)

    @patch("noveler.application.use_cases.enhanced_plot_generation_use_case.Path")
    def test_batch_generate_enhanced_plots(self, mock_path) -> None:
        """一括拡張プロット生成のテスト"""
        # Arrange
        mock_path.cwd.return_value = Path("/test/project")

        # B30 compliance: Mock Repository Factory
        mock_repository_factory = Mock()
        mock_chapter_repo = Mock()
        mock_result_repo = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=mock_chapter_repo)
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=mock_result_repo)

        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # モックの設定
        mock_chapter_plot = self._create_mock_chapter_plot()
        mock_result_7 = self._create_mock_contextual_plot_result(episode_number=7)
        mock_result_8 = self._create_mock_contextual_plot_result(episode_number=8)

        # B30品質作業指示書遵守: 実装の実際の呼び出しメソッドに合わせる
        mock_chapter_repo.find_by_chapter_number = Mock(return_value=mock_chapter_plot)
        use_case._enhanced_service.generate_contextual_plot = Mock(side_effect=[mock_result_7, mock_result_8])

        mock_result_repo.save_result = Mock()
        mock_result_repo.set_project_root = Mock()
        mock_chapter_repo.set_project_root = Mock()

        # Act
        results = use_case.batch_generate_enhanced_plots([7, 8])

        # Assert
        assert len(results) == 2
        assert 7 in results
        assert 8 in results
        assert isinstance(results[7], ContextualPlotResult)
        assert isinstance(results[8], ContextualPlotResult)

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-BATCH_GENERATE_WITH_")
    def test_batch_generate_with_partial_failures(self) -> None:
        """部分的な失敗を含む一括生成のテスト"""
        # Arrange - B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # 一部のエピソードで失敗するようにモック設定
        def mock_generate(episode_number, **kwargs):
            if episode_number == 8:
                msg = "Generation failed for episode 8"
                raise Exception(msg)
            return self._create_mock_contextual_plot_result(episode_number)

        use_case.generate_enhanced_episode_plot = Mock(side_effect=mock_generate)

        # Act
        results = use_case.batch_generate_enhanced_plots([7, 8, 9])

        # Assert
        assert len(results) == 2  # エピソード8は失敗
        assert 7 in results
        assert 9 in results
        assert 8 not in results

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-GET_GENERATION_HISTO")
    def test_get_generation_history(self) -> None:
        """生成履歴取得のテスト"""
        # Arrange - B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        mock_history = [
            self._create_mock_contextual_plot_result(episode_number=7),
            self._create_mock_contextual_plot_result(episode_number=6),
        ]
        use_case._result_repository.get_generation_history = Mock(return_value=mock_history)

        # Act
        history = use_case.get_generation_history(episode_number=7, limit=5)

        # Assert
        assert len(history) == 2
        use_case._result_repository.get_generation_history.assert_called_once_with(episode_number=7, limit=5)

    @patch("noveler.application.use_cases.enhanced_plot_generation_use_case.Path")
    def test_regenerate_with_improved_quality(self, mock_path) -> None:
        """品質向上を目指した再生成のテスト"""
        # Arrange
        mock_path.cwd.return_value = Path("/test/project")

        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # 段階的に品質が向上するモック結果
        low_quality_result = self._create_mock_contextual_plot_result(quality_score=75.0)
        medium_quality_result = self._create_mock_contextual_plot_result(quality_score=82.0)
        high_quality_result = self._create_mock_contextual_plot_result(quality_score=88.0)

        results = [low_quality_result, medium_quality_result, high_quality_result]
        use_case.generate_enhanced_episode_plot = Mock(side_effect=results)

        # Act
        result = use_case.regenerate_with_improved_quality(episode_number=7, quality_threshold=85.0, max_attempts=3)

        # Assert
        assert isinstance(result, ContextualPlotResult)
        # 3回呼ばれる(閾値に達しないため)
        assert use_case.generate_enhanced_episode_plot.call_count == 3

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-ESTIMATE_CHAPTER_NUM")
    def test_estimate_chapter_number(self) -> None:
        """章番号推定のテスト"""
        # Arrange
        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # Act & Assert
        # B30品質作業指示書遵守: ChapterNumber Value Object型安全性規約
        from noveler.domain.value_objects.chapter_number import ChapterNumber

        assert use_case._estimate_chapter_number(EpisodeNumber(1)) == ChapterNumber(1)
        assert use_case._estimate_chapter_number(EpisodeNumber(5)) == ChapterNumber(1)
        assert use_case._estimate_chapter_number(EpisodeNumber(10)) == ChapterNumber(1)
        assert use_case._estimate_chapter_number(EpisodeNumber(11)) == ChapterNumber(1)  # 修正: 範囲1-20は章1
        assert use_case._estimate_chapter_number(EpisodeNumber(25)) == ChapterNumber(2)  # 修正: 範囲21-80は章2

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-CREATE_FALLBACK_CHAP")
    def test_create_fallback_chapter_plot(self) -> None:
        """フォールバック章プロット作成のテスト"""
        # Arrange
        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # Act
        # B30品質作業指示書遵守: ChapterNumber Value Object型安全性規約
        from noveler.domain.value_objects.chapter_number import ChapterNumber

        chapter_plot = use_case._create_fallback_chapter_plot(ChapterNumber(1), EpisodeNumber(7))

        # Assert
        assert chapter_plot is not None
        assert chapter_plot.chapter_number.value == 1
        assert "chapter01" in chapter_plot.title
        assert len(chapter_plot.episodes) == 1
        assert chapter_plot.episodes[0]["episode_number"] == 7

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-CREATE_DEFAULT_CONFI")
    def test_create_default_config(self) -> None:
        """デフォルト設定作成のテスト"""
        # Arrange
        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # Act
        config = use_case._create_default_config()

        # Assert
        assert isinstance(config, PlotGenerationConfig)
        assert config.target_word_count == 6000
        assert config.technical_accuracy_required is True
        assert config.character_consistency_check is True
        assert config.scene_structure_enhanced is True

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-CREATE_QUALITY_FOCUS")
    def test_create_quality_focused_config(self) -> None:
        """品質重視設定作成のテスト"""
        # Arrange
        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # Act
        config_0 = use_case._create_quality_focused_config(0)
        config_1 = use_case._create_quality_focused_config(1)
        config_2 = use_case._create_quality_focused_config(2)

        # Assert
        assert config_0.target_word_count == 6000
        assert config_1.target_word_count == 6500
        assert config_2.target_word_count == 7000
        # 上限チェック
        config_high = use_case._create_quality_focused_config(10)
        assert config_high.target_word_count == 8000  # 上限

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-CALCULATE_QUALITY_GR")
    def test_calculate_quality_grade(self) -> None:
        """品質グレード計算のテスト"""
        # Arrange
        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # Act & Assert
        assert use_case._calculate_quality_grade(97.0) == "A+"
        assert use_case._calculate_quality_grade(92.0) == "A"
        assert use_case._calculate_quality_grade(87.0) == "B+"
        assert use_case._calculate_quality_grade(82.0) == "B"
        assert use_case._calculate_quality_grade(77.0) == "C+"
        assert use_case._calculate_quality_grade(72.0) == "C"
        assert use_case._calculate_quality_grade(65.0) == "D"

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_USE_CASE-GENERATE_QUALITY_REC")
    def test_generate_quality_recommendations(self) -> None:
        """品質改善推奨事項生成のテスト"""
        # Arrange
        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # 低品質指標
        low_quality_indicators = QualityIndicators(
            technical_accuracy=80.0, character_consistency=75.0, plot_coherence=70.0
        )

        # 高品質指標
        high_quality_indicators = QualityIndicators(
            technical_accuracy=95.0, character_consistency=90.0, plot_coherence=85.0
        )

        # Act
        low_recommendations = use_case._generate_quality_recommendations(low_quality_indicators)
        high_recommendations = use_case._generate_quality_recommendations(high_quality_indicators)

        # Assert
        assert len(low_recommendations) > 1  # 複数の改善提案
        assert any("技術要素" in rec for rec in low_recommendations)
        assert any("キャラクター一貫性" in rec for rec in low_recommendations)
        assert any("プロット連結性" in rec for rec in low_recommendations)

        assert len(high_recommendations) == 1
        assert "高品質" in high_recommendations[0]

    @patch("os.environ.get")
    @patch("noveler.application.use_cases.enhanced_plot_generation_use_case.EnhancedPlotGenerationUseCase._get_configuration_manager")
    def test_detect_project_root_from_env(self, mock_get_config, mock_env_get) -> None:
        """環境変数からのプロジェクトルート検出テスト"""
        # Arrange
        mock_env_get.return_value = "/test/project/root"
        # ConfigurationManagerのモック設定
        mock_config_manager = Mock()
        mock_config_manager.get_system_setting.return_value = "/test/project/root"
        mock_get_config.return_value = mock_config_manager

        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # Act
        project_root = use_case._detect_project_root()

        # Assert
        assert project_root == Path("/test/project/root")
        mock_config_manager.get_system_setting.assert_called_once_with("project_root")

    @patch("os.environ.get")
    @patch("noveler.application.use_cases.enhanced_plot_generation_use_case.Path")
    def test_detect_project_root_by_search(self, mock_path, mock_env_get) -> None:
        """検索によるプロジェクトルート検出テスト"""
        # Arrange
        mock_env_get.return_value = None  # 環境変数なし

        mock_current = Mock()
        mock_parent = Mock()
        mock_path.cwd.return_value = mock_current
        mock_current.parents = [mock_parent]

        # プロット検索パターンのモック
        def exists_side_effect(path):
            path_service = get_common_path_service()
            return str(path).endswith(str(path_service.get_plots_dir()))

        mock_parent.__truediv__ = Mock(return_value=Mock(exists=Mock(side_effect=exists_side_effect)))

        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # Act
        project_root = use_case._detect_project_root()

        # Assert
        # フォールバックでカレントディレクトリが返される
        assert project_root == mock_current

    def _create_mock_chapter_plot(self):
        """モック章プロットの作成"""
        mock_chapter_plot = Mock()
        mock_chapter_plot.chapter_number.value = 1
        mock_chapter_plot.title = "ch01"
        mock_chapter_plot.central_theme = "Fランク魔法使いの憂鬱"
        mock_chapter_plot.key_events = ["DEBUG能力発覚"]
        mock_chapter_plot.episodes = [{"episode_number": 7, "title": "第007話", "summary": "テスト概要"}]
        mock_chapter_plot.viewpoint_management = {"primary": "主人公視点"}
        return mock_chapter_plot

    def _create_mock_contextual_plot_result(
        self, episode_number: int = 7, quality_score: float = 85.0
    ) -> ContextualPlotResult:
        """モックコンテキスト駆動プロット結果の作成"""
        quality_indicators = QualityIndicators(
            technical_accuracy=quality_score,
            character_consistency=quality_score - 5.0,
            plot_coherence=quality_score - 3.0,
        )

        return ContextualPlotResult(
            episode_number=EpisodeNumber(episode_number),
            content=f"第{episode_number:03d}話のプロット内容",
            quality_indicators=quality_indicators,
            generation_timestamp=datetime.now(timezone.utc),
            metadata={"test": True},
        )


@pytest.mark.spec("SPEC-PLOT-004")
class TestEnhancedPlotGenerationUseCaseIntegration:
    """Enhanced Plot Generation Use Case の統合テスト"""

    @patch("noveler.application.use_cases.enhanced_plot_generation_use_case.Path")
    def test_full_workflow_integration(self, mock_path) -> None:
        """完全ワークフロー統合テスト"""
        # Arrange
        mock_path.cwd.return_value = Path("/test/project")

        # B30品質作業指示書遵守: 適切なDI使用
        mock_repository_factory = Mock()
        mock_repository_factory.create_yaml_chapter_plot_repository = Mock(return_value=Mock())
        mock_repository_factory.create_enhanced_plot_result_repository = Mock(return_value=Mock())
        use_case = EnhancedPlotGenerationUseCase(repository_factory=mock_repository_factory)

        # リアルに近いモック設定
        mock_chapter_plot = Mock()
        mock_chapter_plot.chapter_number.value = 1
        mock_chapter_plot.title = "ch01 Fランク魔法使いの憂鬱"
        mock_chapter_plot.central_theme = "DEBUG能力の発見と成長"
        mock_chapter_plot.key_events = ["DEBUG能力発覚", "アサート少女との出会い"]
        mock_chapter_plot.episodes = [
            {
                "episode_number": 7,
                "title": "第007話 ペアプログラミング魔法入門",
                "summary": "直人とあすかが協調魔法を学ぶエピソード",
            }
        ]
        mock_chapter_plot.viewpoint_management = {"primary": "直人一人称視点"}

        high_quality_result = ContextualPlotResult(
            episode_number=EpisodeNumber(7),
            content="高品質な生成プロット内容...",
            quality_indicators=QualityIndicators(
                technical_accuracy=92.0, character_consistency=88.0, plot_coherence=90.0
            ),
            generation_timestamp=datetime.now(timezone.utc),
            metadata={"generation_method": "enhanced_contextual"},
        )

        # モック設定 - B30品質作業指示書遵守: 実装に合わせたMock期待値
        use_case._chapter_repository.find_by_chapter_number = Mock(return_value=mock_chapter_plot)
        use_case._enhanced_service.generate_contextual_plot = Mock(return_value=high_quality_result)
        use_case._result_repository.save_result = Mock()
        use_case._result_repository.set_project_root = Mock()
        use_case._chapter_repository.set_project_root = Mock()

        # Act
        result = use_case.generate_enhanced_episode_plot(
            episode_number=7,
            config=PlotGenerationConfig(
                target_word_count=6000,
                technical_accuracy_required=True,
                character_consistency_check=True,
                scene_structure_enhanced=True,
            ),
            save_result=True,
        )

        # Assert
        assert isinstance(result, ContextualPlotResult)
        assert result.episode_number == EpisodeNumber(7)
        assert result.quality_indicators.overall_score >= 85.0
        assert "quality_report" in result.metadata

        # 品質レポートの検証
        quality_report = result.metadata["quality_report"]
        assert "overall_score" in quality_report
        assert "quality_grade" in quality_report
        assert "recommendations" in quality_report
        assert quality_report["quality_grade"] in ["A+", "A", "B+", "B", "C+", "C", "D"]

        # 各コンポーネントが適切に呼ばれたことを確認 - B30遵守: 実装呼び出しに合わせた検証
        from noveler.domain.value_objects.chapter_number import ChapterNumber

        use_case._chapter_repository.set_project_root.assert_called_once()
        use_case._result_repository.set_project_root.assert_called_once()
        use_case._chapter_repository.find_by_chapter_number.assert_called_once_with(
            ChapterNumber(1)
        )  # ChapterNumber型で推定章番号
        use_case._enhanced_service.generate_contextual_plot.assert_called_once()
        use_case._result_repository.save_result.assert_called_once_with(result)
