"""ContextualPlotGeneration エンティティのテスト

SPEC-PLOT-004: Enhanced Claude Code Integration Phase 2
"""

from datetime import datetime, timezone

import pytest
pytestmark = pytest.mark.plot_episode

from noveler.domain.entities.contextual_plot_generation import (
    ContextualPlotGeneration,
    ContextualPlotResult,
    PlotGenerationConfig,
    QualityIndicators,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber


@pytest.mark.spec("SPEC-PLOT-004")
class TestContextualPlotGeneration:
    """ContextualPlotGeneration エンティティのテスト"""

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-CREATE_CONTEXTUAL_PL")
    def test_create_contextual_plot_generation_with_basic_config(self) -> None:
        """基本設定でContextualPlotGenerationを作成"""
        # Arrange
        episode_number = EpisodeNumber(7)
        config = PlotGenerationConfig(
            target_word_count=5000, technical_accuracy_required=True, character_consistency_check=True
        )

        # Act
        plot_generation = ContextualPlotGeneration(episode_number=episode_number, config=config)

        # Assert
        assert plot_generation.episode_number == episode_number
        assert plot_generation.config == config
        assert plot_generation.generation_id is not None
        assert plot_generation.status == "pending"

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-UPDATE_CONTEXT_WITH_")
    def test_update_context_with_previous_episodes(self) -> None:
        """前エピソードコンテキストの更新"""
        # Arrange
        plot_generation = ContextualPlotGeneration(episode_number=EpisodeNumber(7), config=PlotGenerationConfig())

        previous_context = {
            "episode_6": {
                "technical_elements": ["デバッグログ", "アサーション"],
                "character_development": {"直人": "成長段階1", "あすか": "理論確立期"},
            }
        }

        # Act
        plot_generation.update_context(previous_context)

        # Assert
        assert plot_generation.context_data == previous_context
        assert plot_generation.has_context_data is True

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-GENERATE_PLOT_RESULT")
    def test_generate_plot_result_with_quality_indicators(self) -> None:
        """品質指標付きプロット結果生成"""
        # Arrange
        plot_generation = ContextualPlotGeneration(episode_number=EpisodeNumber(7), config=PlotGenerationConfig())

        quality_indicators = QualityIndicators(
            technical_accuracy=95.0, character_consistency=88.5, plot_coherence=91.2, overall_score=91.6
        )

        # Act
        result = plot_generation.create_result(
            generated_content="生成されたプロット内容...", quality_indicators=quality_indicators
        )

        # Assert
        assert isinstance(result, ContextualPlotResult)
        assert result.content == "生成されたプロット内容..."
        assert result.quality_indicators == quality_indicators
        assert result.episode_number == EpisodeNumber(7)
        assert result.generation_timestamp is not None

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-VALIDATE_GENERATION_")
    def test_validate_generation_config(self) -> None:
        """生成設定の検証"""
        # Arrange & Act & Assert - 有効な設定
        valid_config = PlotGenerationConfig(
            target_word_count=5000,
            technical_accuracy_required=True,
            character_consistency_check=True,
            scene_structure_enhanced=True,
        )

        assert valid_config.is_valid() is True

        # Assert - 無効な設定(単語数が少なすぎる)
        invalid_config = PlotGenerationConfig(
            target_word_count=1000  # 最小値以下
        )
        assert invalid_config.is_valid() is False

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-PLOT_GENERATION_WITH")
    def test_plot_generation_with_chapter_context(self) -> None:
        """章コンテキスト情報を含むプロット生成"""
        # Arrange
        episode_number = EpisodeNumber(7)
        config = PlotGenerationConfig(target_word_count=6000)
        plot_generation = ContextualPlotGeneration(episode_number=episode_number, config=config)

        chapter_context = {
            "chapter_number": 1,
            "chapter_theme": "Fランク魔法使いの憂鬱",
            "key_events": ["DEBUG能力発覚", "アサート少女との出会い"],
            "technical_focus": ["デバッグ手法", "例外処理"],
        }

        # Act
        plot_generation.set_chapter_context(chapter_context)

        # Assert
        assert plot_generation.chapter_context == chapter_context
        assert plot_generation.get_technical_focus() == ["デバッグ手法", "例外処理"]

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-QUALITY_SCORE_CALCUL")
    def test_quality_score_calculation(self) -> None:
        """品質スコア計算の検証"""
        # Arrange
        quality_indicators = QualityIndicators(technical_accuracy=95.0, character_consistency=88.5, plot_coherence=91.2)

        # Act
        overall_score = quality_indicators.calculate_overall_score()

        # Assert
        assert isinstance(overall_score, float)
        assert 85.0 <= overall_score <= 95.0  # 期待範囲内
        assert overall_score == pytest.approx(91.57, rel=1e-2)

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-CONTEXTUAL_PLOT_RESU")
    def test_contextual_plot_result_serialization(self) -> None:
        """ContextualPlotResult のシリアライゼーション"""
        # Arrange
        quality_indicators = QualityIndicators(
            technical_accuracy=95.0, character_consistency=88.5, plot_coherence=91.2, overall_score=91.6
        )

        result = ContextualPlotResult(
            episode_number=EpisodeNumber(7),
            content="テストプロット内容",
            quality_indicators=quality_indicators,
            generation_timestamp=datetime.now(timezone.utc),
        )

        # Act
        serialized = result.to_dict()

        # Assert
        assert serialized["episode_number"] == 7
        assert serialized["content"] == "テストプロット内容"
        assert "quality_indicators" in serialized
        assert "generation_timestamp" in serialized
        assert serialized["quality_indicators"]["overall_score"] == 91.6


@pytest.mark.spec("SPEC-PLOT-004")
class TestPlotGenerationConfig:
    """PlotGenerationConfig 値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-DEFAULT_CONFIGURATIO")
    def test_default_configuration(self) -> None:
        """デフォルト設定の検証"""
        # Act
        config = PlotGenerationConfig()

        # Assert
        assert config.target_word_count == 5000
        assert config.technical_accuracy_required is True
        assert config.character_consistency_check is True
        assert config.scene_structure_enhanced is False

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-CUSTOM_CONFIGURATION")
    def test_custom_configuration(self) -> None:
        """カスタム設定の検証"""
        # Act
        config = PlotGenerationConfig(
            target_word_count=7000,
            technical_accuracy_required=False,
            character_consistency_check=True,
            scene_structure_enhanced=True,
        )

        # Assert
        assert config.target_word_count == 7000
        assert config.technical_accuracy_required is False
        assert config.character_consistency_check is True
        assert config.scene_structure_enhanced is True

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-CONFIG_VALIDATION_RU")
    def test_config_validation_rules(self) -> None:
        """設定検証ルールの確認"""
        # Valid configurations
        assert PlotGenerationConfig(target_word_count=4000).is_valid() is True
        assert PlotGenerationConfig(target_word_count=7000).is_valid() is True

        # Invalid configurations
        assert PlotGenerationConfig(target_word_count=2000).is_valid() is False  # Too short
        assert PlotGenerationConfig(target_word_count=10000).is_valid() is False  # Too long


@pytest.mark.spec("SPEC-PLOT-004")
class TestQualityIndicators:
    """QualityIndicators 値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-QUALITY_INDICATORS_C")
    def test_quality_indicators_creation(self) -> None:
        """品質指標の作成"""
        # Act
        indicators = QualityIndicators(technical_accuracy=95.0, character_consistency=88.5, plot_coherence=91.2)

        # Assert
        assert indicators.technical_accuracy == 95.0
        assert indicators.character_consistency == 88.5
        assert indicators.plot_coherence == 91.2

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-OVERALL_SCORE_CALCUL")
    def test_overall_score_calculation_accuracy(self) -> None:
        """総合スコア計算の正確性"""
        # Arrange
        indicators = QualityIndicators(technical_accuracy=90.0, character_consistency=85.0, plot_coherence=95.0)

        # Act
        overall = indicators.calculate_overall_score()

        # Assert
        expected_score = (90.0 + 85.0 + 95.0) / 3
        assert overall == pytest.approx(expected_score, rel=1e-2)

    @pytest.mark.spec("SPEC-CONTEXTUAL_PLOT_GENERATION-QUALITY_THRESHOLD_CH")
    def test_quality_threshold_check(self) -> None:
        """品質閾値チェック"""
        # Arrange
        high_quality = QualityIndicators(technical_accuracy=95.0, character_consistency=90.0, plot_coherence=92.0)

        low_quality = QualityIndicators(technical_accuracy=60.0, character_consistency=55.0, plot_coherence=65.0)

        # Act & Assert
        assert high_quality.meets_threshold(80.0) is True
        assert low_quality.meets_threshold(80.0) is False
        assert low_quality.meets_threshold(50.0) is True
