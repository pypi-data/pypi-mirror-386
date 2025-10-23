"""Enhanced Plot Generation Service のテスト

SPEC-PLOT-004: Enhanced Claude Code Integration Phase 2
"""

from unittest.mock import Mock, patch

import pytest

from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.entities.contextual_plot_generation import (
    ContextualPlotResult,
    PlotGenerationConfig,
    QualityIndicators,
)
from noveler.domain.services.enhanced_plot_generation_service import EnhancedPlotGenerationService
from noveler.domain.value_objects.chapter_number import ChapterNumber
from noveler.domain.value_objects.episode_number import EpisodeNumber


@pytest.mark.spec("SPEC-PLOT-004")
class TestEnhancedPlotGenerationService:
    """Enhanced Plot Generation Service のテスト"""

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-SERVICE_INITIALIZATI")
    def test_service_initialization(self) -> None:
        """サービス初期化のテスト"""
        # Arrange
        mock_claude_service = Mock()

        # Act
        service = EnhancedPlotGenerationService(claude_service=mock_claude_service)

        # Assert
        assert service is not None
        assert service._claude_service is not None

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-SERVICE_INITIALIZATI")
    def test_service_initialization_with_dependency_injection(self) -> None:
        """依存注入によるサービス初期化のテスト"""
        # Arrange
        mock_claude_service = Mock()

        # Act
        service = EnhancedPlotGenerationService(claude_service=mock_claude_service)

        # Assert
        assert service._claude_service == mock_claude_service

    @patch("noveler.domain.services.enhanced_plot_generation_service.is_claude_code_environment")
    def test_contextual_plot_generation_basic_flow(self, mock_claude_env) -> None:
        """基本的なコンテキスト駆動プロット生成フローのテスト"""
        # Arrange
        mock_claude_env.return_value = False  # Claude Code環境外

        mock_claude_service = Mock()
        service = EnhancedPlotGenerationService(claude_service=mock_claude_service)
        episode_number = EpisodeNumber(7)
        chapter_plot = self._create_mock_chapter_plot()
        config = PlotGenerationConfig(target_word_count=6000)

        # Claude serviceのモック設定
        mock_generated_plot = {
            "episode_number": 7,
            "title": "第007話 ペアプログラミング魔法入門",
            "summary": "直人とあすかがペアプログラミング魔法を学び、協調関係を深める話",
            "scenes": [
                {"scene_title": "理論授業", "description": "ペア魔法の基礎理論を学ぶシーン"},
                {"scene_title": "実践練習", "description": "初めてのシンクロ魔法練習"},
            ],
            "key_events": ["ペア魔法理論習得", "初回シンクロ成功"],
            "viewpoint": "主人公(直人一人称視点)",
            "tone": "学習と成長",
            "conflict": "ペア魔法の難しさ",
            "resolution": "協調関係確立",
        }
        mock_claude_service._call_claude_code = Mock(return_value=mock_generated_plot)

        # Act
        result = service.generate_contextual_plot(episode_number, chapter_plot, config)

        # Assert
        assert isinstance(result, ContextualPlotResult)
        assert result.episode_number == episode_number
        assert result.quality_indicators is not None
        assert result.metadata["generation_method"] == "enhanced_contextual"
        assert "claude_code_integration" in result.metadata

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-CHAPTER_CONTEXT_EXTR")
    def test_chapter_context_extraction(self) -> None:
        """章コンテキスト抽出のテスト"""
        # Arrange
        service = EnhancedPlotGenerationService()
        chapter_plot = self._create_mock_chapter_plot()
        episode_number = EpisodeNumber(7)

        # Act
        context = service._extract_chapter_context(chapter_plot, episode_number)

        # Assert
        assert "chapter_number" in context
        assert "chapter_theme" in context
        assert "key_events" in context
        assert "technical_focus" in context
        assert "viewpoint_management" in context
        assert "episode_position" in context
        assert context["chapter_number"] == 1

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-TECHNICAL_FOCUS_EXTR")
    def test_technical_focus_extraction(self) -> None:
        """技術フォーカス抽出のテスト"""
        # Arrange
        service = EnhancedPlotGenerationService()
        chapter_plot = self._create_mock_chapter_plot_with_technical_events()

        # Act
        technical_focus = service._extract_technical_focus(chapter_plot)

        # Assert
        assert isinstance(technical_focus, list)
        assert len(technical_focus) > 0
        assert "デバッグ手法" in technical_focus

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-EPISODE_POSITION_CAL")
    def test_episode_position_calculation(self) -> None:
        """エピソード位置計算のテスト"""
        # Arrange
        service = EnhancedPlotGenerationService()
        chapter_plot = self._create_mock_chapter_plot_with_episodes()
        episode_number = EpisodeNumber(7)

        # Act
        position = service._calculate_episode_position(episode_number, chapter_plot)

        # Assert
        assert "position" in position
        assert "total" in position
        assert "is_first" in position
        assert "is_last" in position
        assert isinstance(position["position"], int)

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-PREVIOUS_EPISODES_CO")
    def test_previous_episodes_context_retrieval(self) -> None:
        """前エピソードコンテキスト取得のテスト"""
        # Arrange
        service = EnhancedPlotGenerationService()
        chapter_plot = self._create_mock_chapter_plot_with_episodes()
        episode_number = EpisodeNumber(7)

        # Act
        context = service._get_previous_episodes_context(episode_number, chapter_plot)

        # Assert
        if context:  # 前エピソードが存在する場合:
            assert "episode_6" in context
            assert "title" in context["episode_6"]
            assert "technical_elements" in context["episode_6"]
            assert "character_development" in context["episode_6"]

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-ENHANCED_PROMPT_BUIL")
    def test_enhanced_prompt_building(self) -> None:
        """拡張プロンプト構築のテスト"""
        # Arrange
        service = EnhancedPlotGenerationService()
        episode_number = EpisodeNumber(7)
        config = PlotGenerationConfig(target_word_count=6000)
        chapter_plot = self._create_mock_chapter_plot()

        # ContextualPlotGenerationのモック作成
        from noveler.domain.entities.contextual_plot_generation import ContextualPlotGeneration

        contextual_generation = ContextualPlotGeneration(episode_number, config)
        contextual_generation.set_chapter_context(
            {
                "chapter_number": 1,
                "chapter_theme": "Fランク魔法使いの憂鬱",
                "key_events": ["DEBUG能力発覚"],
                "technical_focus": ["デバッグ手法"],
                "episode_position": {"position": 1, "total": 3, "is_first": True, "is_last": False},
            }
        )

        # Act
        prompt = service._build_enhanced_prompt(contextual_generation, chapter_plot)

        # Assert
        assert "SPEC-PLOT-004" in prompt
        assert "Enhanced Claude Code Integration Phase 2" in prompt
        assert str(episode_number.value) in prompt
        assert str(config.target_word_count) in prompt
        assert "章コンテキスト情報" in prompt

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-QUALITY_INDICATORS_C")
    def test_quality_indicators_calculation(self) -> None:
        """品質指標計算のテスト"""
        # Arrange
        service = EnhancedPlotGenerationService()
        generated_plot = {
            "technical_elements": ["デバッグ手法", "アサーション"],
            "character_development": {"直人": "成長段階1", "あすか": "理論確立期"},
            "scenes": [{"scene_title": "シーン1", "description": "デバッグ手法を学ぶシーン"}],
        }

        from noveler.domain.entities.contextual_plot_generation import ContextualPlotGeneration

        contextual_generation = ContextualPlotGeneration(EpisodeNumber(7), PlotGenerationConfig())

        contextual_generation.set_chapter_context({"chapter_theme": "テーマ"})

        chapter_plot = self._create_mock_chapter_plot()

        # Act
        quality_indicators = service._calculate_quality_indicators(generated_plot, contextual_generation, chapter_plot)

        # Assert
        assert isinstance(quality_indicators, QualityIndicators)
        assert 0 <= quality_indicators.technical_accuracy <= 100
        assert 0 <= quality_indicators.character_consistency <= 100
        assert 0 <= quality_indicators.plot_coherence <= 100

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-TECHNICAL_ACCURACY_E")
    def test_technical_accuracy_evaluation(self) -> None:
        """技術精度評価のテスト"""
        # Arrange
        service = EnhancedPlotGenerationService()
        generated_plot = {
            "technical_elements": ["デバッグ手法", "アサーション"],
            "scenes": [{"description": "デバッグ手法を使ったプログラミング"}],
        }
        technical_focus = ["デバッグ手法"]

        # Act
        score = service._evaluate_technical_accuracy(generated_plot, technical_focus)

        # Assert
        assert isinstance(score, float)
        assert 85.0 <= score <= 100.0  # ベーススコア以上

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-CHARACTER_CONSISTENC")
    def test_character_consistency_evaluation(self) -> None:
        """キャラクター一貫性評価のテスト"""
        # Arrange
        service = EnhancedPlotGenerationService()
        generated_plot = {"character_development": {"直人": "成長段階1", "あすか": "理論確立期"}}
        context_data = {}

        # Act
        score = service._evaluate_character_consistency(generated_plot, context_data)

        # Assert
        assert isinstance(score, float)
        assert 80.0 <= score <= 100.0  # ベーススコア以上

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-PLOT_COHERENCE_EVALU")
    def test_plot_coherence_evaluation(self) -> None:
        """プロット連結性評価のテスト"""
        # Arrange
        service = EnhancedPlotGenerationService()
        generated_plot = {
            "episode_number": 7,
            "title": "テストタイトル",
            "summary": "Fランク魔法使いの憂鬱に関する話",
            "scenes": [],
            "key_events": [],
        }
        chapter_context = {"chapter_theme": "Fランク魔法使いの憂鬱"}

        # Act
        score = service._evaluate_plot_coherence(generated_plot, chapter_context)

        # Assert
        assert isinstance(score, float)
        assert 75.0 <= score <= 100.0  # ベーススコア以上

    @pytest.mark.spec("SPEC-ENHANCED_PLOT_GENERATION_SERVICE-INVALID_CONFIG_HANDL")
    def test_invalid_config_handling(self) -> None:
        """無効な設定の処理テスト"""
        # Arrange
        service = EnhancedPlotGenerationService()
        episode_number = EpisodeNumber(7)
        chapter_plot = self._create_mock_chapter_plot()
        invalid_config = PlotGenerationConfig(target_word_count=1000)  # 無効な設定

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid plot generation config"):
            service.generate_contextual_plot(episode_number, chapter_plot, invalid_config)

    @patch("noveler.domain.services.enhanced_plot_generation_service.is_claude_code_environment")
    def test_error_handling_with_fallback(self, mock_claude_env) -> None:
        """エラーハンドリングとフォールバック処理のテスト"""
        # Arrange
        mock_claude_env.return_value = False
        mock_claude_service = Mock()
        service = EnhancedPlotGenerationService(claude_service=mock_claude_service)
        episode_number = EpisodeNumber(7)
        chapter_plot = self._create_mock_chapter_plot()

        # Claude serviceでエラーを発生させるモック設定
        mock_claude_service._call_claude_code = Mock(side_effect=Exception("Test error"))
        mock_claude_service._generate_high_quality_plot_mock_response = Mock(
            return_value={
                "episode_number": 7,
                "title": "フォールバック生成",
                "summary": "エラー時のフォールバック生成",
                "scenes": [],
                "key_events": [],
            }
        )

        # Act
        result = service.generate_contextual_plot(episode_number, chapter_plot)

        # Assert
        assert isinstance(result, ContextualPlotResult)
        assert result.episode_number == episode_number

    def _create_mock_chapter_plot(self) -> ChapterPlot:
        """モック章プロットの作成"""
        mock_chapter = Mock(spec=ChapterPlot)
        mock_chapter.chapter_number = ChapterNumber(1)
        mock_chapter.central_theme = "Fランク魔法使いの憂鬱"
        mock_chapter.key_events = ["DEBUG能力発覚", "アサート少女との出会い"]
        mock_chapter.viewpoint_management = {"primary": "主人公視点"}
        mock_chapter.episodes = [
            {"episode_number": 7, "title": "ペアプログラミング魔法入門", "summary": "ペア魔法を学ぶ"}
        ]

        # contains_episode メソッドのモック
        mock_chapter.contains_episode = Mock(return_value=True)

        return mock_chapter

    def _create_mock_chapter_plot_with_technical_events(self) -> ChapterPlot:
        """技術要素を含むモック章プロットの作成"""
        mock_chapter = self._create_mock_chapter_plot()
        mock_chapter.key_events = ["DEBUG能力発覚", "デバッグログ解析", "アサーション魔法習得"]
        return mock_chapter

    def _create_mock_chapter_plot_with_episodes(self) -> ChapterPlot:
        """複数エピソードを含むモック章プロットの作成"""
        mock_chapter = self._create_mock_chapter_plot()
        mock_chapter.episodes = [
            {"episode_number": 6, "title": "前話タイトル", "summary": "前話概要"},
            {"episode_number": 7, "title": "現在話タイトル", "summary": "現在話概要"},
            {"episode_number": 8, "title": "次話タイトル", "summary": "次話概要"},
        ]
        return mock_chapter


@pytest.mark.spec("SPEC-PLOT-004")
class TestEnhancedPlotGenerationServiceIntegration:
    """Enhanced Plot Generation Service の統合テスト"""

    @patch("noveler.domain.services.enhanced_plot_generation_service.is_claude_code_environment")
    def test_full_contextual_generation_workflow(self, mock_claude_env) -> None:
        """完全なコンテキスト駆動生成ワークフローのテスト"""
        # Arrange
        mock_claude_env.return_value = True  # Claude Code環境内

        service = EnhancedPlotGenerationService()
        episode_number = EpisodeNumber(7)

        # 実際のChapter Plot構造に近いモック
        chapter_plot = Mock(spec=ChapterPlot)
        chapter_plot.chapter_number = ChapterNumber(1)
        chapter_plot.central_theme = "Fランク魔法使いの憂鬱"
        chapter_plot.key_events = ["DEBUG能力発覚", "ペアプログラミング開始"]
        chapter_plot.viewpoint_management = {"primary": "直人一人称"}
        chapter_plot.episodes = [
            {"episode_number": 6, "title": "アサーション少女との出会い", "summary": "あすかとの初対面"},
            {"episode_number": 7, "title": "ペアプログラミング魔法入門", "summary": "協調魔法の基礎"},
        ]
        chapter_plot.contains_episode = Mock(return_value=True)

        config = PlotGenerationConfig(
            target_word_count=6000,
            technical_accuracy_required=True,
            character_consistency_check=True,
            scene_structure_enhanced=True,
        )

        # Claude Code実行をモック
        with patch.object(service, "_execute_claude_code_generation") as mock_execute:
            mock_execute.return_value = {
                "episode_number": 7,
                "title": "第007話 ペアプログラミング魔法入門",
                "summary": "直人とあすかが初めて協調魔法に挑戦し、技術と心の両面で成長する物語",
                "scenes": [
                    {"scene_title": "理論講座", "description": "ペアプログラミング魔法の基礎理論を学ぶ講義シーン"},
                    {"scene_title": "初回シンクロ", "description": "あすかとの初めての魔法同期練習"},
                ],
                "key_events": ["理論習得", "シンクロ成功"],
                "viewpoint": "直人一人称視点",
                "tone": "学習と発見の喜び",
                "conflict": "技術的な難しさと人間関係の課題",
                "resolution": "協調による問題解決",
                "technical_elements": ["デバッグ手法", "ペア魔法"],
                "character_development": {"直人": "協調スキル向上", "あすか": "実践経験獲得"},
            }

            # Act
            result = service.generate_contextual_plot(episode_number, chapter_plot, config)

            # Assert
            assert isinstance(result, ContextualPlotResult)
            assert result.episode_number == episode_number
            assert result.quality_indicators.technical_accuracy >= 85.0
            assert result.quality_indicators.character_consistency >= 80.0
            assert result.quality_indicators.plot_coherence >= 75.0
            assert result.metadata["generation_method"] == "enhanced_contextual"
            assert result.metadata["claude_code_integration"] is True
            assert result.metadata["chapter_number"] == 1

            # プロンプト構築が呼ばれたことを確認
            mock_execute.assert_called_once()
