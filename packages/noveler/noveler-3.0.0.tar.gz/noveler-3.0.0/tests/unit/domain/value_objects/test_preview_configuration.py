"""
PreviewConfiguration値オブジェクトのユニットテスト

SPEC-WORKFLOW-002: レガシーモジュールTDD+DDD移行
"""

import pytest

from noveler.domain.exceptions import DomainValidationError
from noveler.domain.value_objects.preview_configuration import (
    ContentFilter,
    PreviewConfiguration,
    PreviewStyle,
    QualityThreshold,
    StyleSettings,
)

pytestmark = pytest.mark.vo_smoke


@pytest.mark.spec("SPEC-WORKFLOW-002")
class TestQualityThreshold:
    """QualityThresholdのテストクラス"""

    def test_valid_quality_threshold_creation(self) -> None:
        """有効な品質基準の作成をテスト"""
        # Arrange & Act
        threshold = QualityThreshold(metric_name="readability", min_value=0.7, max_value=1.0, weight=1.5)

        # Assert
        assert threshold.metric_name == "readability"
        assert threshold.min_value == 0.7
        assert threshold.max_value == 1.0
        assert threshold.weight == 1.5

    def test_empty_metric_name_raises_error(self) -> None:
        """空のmetric_nameで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="metric_nameは空にできません"):
            QualityThreshold(metric_name="", min_value=0.5)

    def test_invalid_min_value_range_raises_error(self) -> None:
        """無効なmin_value範囲で例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="min_valueは0.0から1.0の範囲である必要があります"):
            QualityThreshold(metric_name="test", min_value=1.5)

    def test_invalid_max_value_range_raises_error(self) -> None:
        """無効なmax_value範囲で例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="max_valueは0.0から1.0の範囲である必要があります"):
            QualityThreshold(metric_name="test", min_value=0.5, max_value=1.5)

    def test_min_value_greater_than_max_value_raises_error(self) -> None:
        """min_valueがmax_valueより大きい場合に例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="min_valueはmax_value以下である必要があります"):
            QualityThreshold(metric_name="test", min_value=0.8, max_value=0.5)

    def test_zero_weight_raises_error(self) -> None:
        """重みが0以下で例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="weightは正の値である必要があります"):
            QualityThreshold(metric_name="test", min_value=0.5, weight=0)


@pytest.mark.spec("SPEC-WORKFLOW-002")
class TestStyleSettings:
    """StyleSettingsのテストクラス"""

    def test_valid_style_settings_creation(self) -> None:
        """有効なスタイル設定の作成をテスト"""
        # Arrange & Act
        settings = StyleSettings(emphasis_marker="**", ellipsis="……", line_break="\n\n", quote_style="「」")

        # Assert
        assert settings.emphasis_marker == "**"
        assert settings.ellipsis == "……"
        assert settings.line_break == "\n\n"
        assert settings.quote_style == "「」"

    def test_empty_emphasis_marker_raises_error(self) -> None:
        """空のemphasis_markerで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="emphasis_markerは空にできません"):
            StyleSettings(emphasis_marker="")

    def test_empty_ellipsis_raises_error(self) -> None:
        """空のellipsisで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="ellipsisは空にできません"):
            StyleSettings(ellipsis="")


@pytest.mark.spec("SPEC-WORKFLOW-002")
class TestPreviewConfiguration:
    """PreviewConfiguration値オブジェクトのテストクラス"""

    def test_valid_preview_configuration_creation(self) -> None:
        """有効なプレビュー設定の作成をテスト"""
        # Arrange
        quality_thresholds = [QualityThreshold("readability", 0.7, 1.0, 1.0)]
        content_filters = [ContentFilter.DIALOGUE, ContentFilter.ACTION]
        style_settings = StyleSettings()

        # Act
        config = PreviewConfiguration(
            max_length=200,
            sentence_count=3,
            preview_style=PreviewStyle.SUMMARY,
            content_filters=content_filters,
            style_settings=style_settings,
            quality_thresholds=quality_thresholds,
            preserve_formatting=True,
            include_metadata=True,
            description="テスト設定",
        )

        # Assert
        assert config.max_length == 200
        assert config.sentence_count == 3
        assert config.preview_style == PreviewStyle.SUMMARY
        assert config.content_filters == content_filters
        assert config.style_settings == style_settings
        assert config.quality_thresholds == quality_thresholds
        assert config.preserve_formatting is True
        assert config.include_metadata is True
        assert config.description == "テスト設定"

    def test_zero_max_length_raises_error(self) -> None:
        """max_lengthが0以下で例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="max_lengthは正の値である必要があります"):
            PreviewConfiguration(max_length=0, sentence_count=3, preview_style=PreviewStyle.SUMMARY)

    def test_too_large_max_length_raises_error(self) -> None:
        """max_lengthが大きすぎる場合に例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="max_lengthは1000文字以下である必要があります"):
            PreviewConfiguration(max_length=1500, sentence_count=3, preview_style=PreviewStyle.SUMMARY)

    def test_zero_sentence_count_raises_error(self) -> None:
        """sentence_countが0以下で例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="sentence_countは正の値である必要があります"):
            PreviewConfiguration(max_length=200, sentence_count=0, preview_style=PreviewStyle.SUMMARY)

    def test_too_large_sentence_count_raises_error(self) -> None:
        """sentence_countが大きすぎる場合に例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="sentence_countは20以下である必要があります"):
            PreviewConfiguration(max_length=200, sentence_count=25, preview_style=PreviewStyle.SUMMARY)

    def test_invalid_preview_style_raises_error(self) -> None:
        """無効なpreview_styleで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(DomainValidationError, match="preview_styleは有効なPreviewStyleである必要があります"):
            PreviewConfiguration(
                max_length=200,
                sentence_count=3,
                preview_style="invalid_style",  # str型は無効
            )

    def test_invalid_content_filter_raises_error(self) -> None:
        """無効なcontent_filterで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(
            DomainValidationError, match="content_filtersは有効なContentFilterのリストである必要があります"
        ):
            PreviewConfiguration(
                max_length=200,
                sentence_count=3,
                preview_style=PreviewStyle.SUMMARY,
                content_filters=["invalid_filter"],  # str型は無効
            )

    def test_invalid_quality_threshold_raises_error(self) -> None:
        """無効なquality_thresholdで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(
            DomainValidationError, match="quality_thresholdsは有効なQualityThresholdのリストである必要があります"
        ):
            PreviewConfiguration(
                max_length=200,
                sentence_count=3,
                preview_style=PreviewStyle.SUMMARY,
                quality_thresholds=["invalid_threshold"],  # str型は無効
            )

    def test_is_summary_style_returns_true_for_summary(self) -> None:
        """SUMMARYスタイルでTrueが返されることをテスト"""
        # Arrange
        config = PreviewConfiguration(max_length=200, sentence_count=3, preview_style=PreviewStyle.SUMMARY)

        # Act & Assert
        assert config.is_summary_style() is True
        assert config.is_excerpt_style() is False

    def test_is_excerpt_style_returns_true_for_excerpt(self) -> None:
        """EXCERPTスタイルでTrueが返されることをテスト"""
        # Arrange
        config = PreviewConfiguration(max_length=200, sentence_count=3, preview_style=PreviewStyle.EXCERPT)

        # Act & Assert
        assert config.is_excerpt_style() is True
        assert config.is_summary_style() is False

    def test_is_teaser_style_returns_true_for_teaser(self) -> None:
        """TEASERスタイルでTrueが返されることをテスト"""
        # Arrange
        config = PreviewConfiguration(max_length=200, sentence_count=3, preview_style=PreviewStyle.TEASER)

        # Act & Assert
        assert config.is_teaser_style() is True
        assert config.is_summary_style() is False

    def test_is_dialogue_focus_style_returns_true_for_dialogue_focus(self) -> None:
        """DIALOGUE_FOCUSスタイルでTrueが返されることをテスト"""
        # Arrange
        config = PreviewConfiguration(max_length=200, sentence_count=3, preview_style=PreviewStyle.DIALOGUE_FOCUS)

        # Act & Assert
        assert config.is_dialogue_focus_style() is True
        assert config.is_summary_style() is False

    def test_has_content_filter_returns_true_for_existing_filter(self) -> None:
        """存在するコンテンツフィルターでTrueが返されることをテスト"""
        # Arrange
        config = PreviewConfiguration(
            max_length=200,
            sentence_count=3,
            preview_style=PreviewStyle.SUMMARY,
            content_filters=[ContentFilter.DIALOGUE, ContentFilter.ACTION],
        )

        # Act & Assert
        assert config.has_content_filter(ContentFilter.DIALOGUE) is True
        assert config.has_content_filter(ContentFilter.ACTION) is True
        assert config.has_content_filter(ContentFilter.EMOTION) is False

    def test_should_include_dialogue_returns_true_when_filter_exists(self) -> None:
        """DIALOGUEフィルターが存在する場合にTrueが返されることをテスト"""
        # Arrange
        config = PreviewConfiguration(
            max_length=200,
            sentence_count=3,
            preview_style=PreviewStyle.SUMMARY,
            content_filters=[ContentFilter.DIALOGUE],
        )

        # Act & Assert
        assert config.should_include_dialogue() is True

    def test_should_include_action_returns_true_when_filter_exists(self) -> None:
        """ACTIONフィルターが存在する場合にTrueが返されることをテスト"""
        # Arrange
        config = PreviewConfiguration(
            max_length=200, sentence_count=3, preview_style=PreviewStyle.SUMMARY, content_filters=[ContentFilter.ACTION]
        )

        # Act & Assert
        assert config.should_include_action() is True

    def test_should_include_emotion_returns_true_when_filter_exists(self) -> None:
        """EMOTIONフィルターが存在する場合にTrueが返されることをテスト"""
        # Arrange
        config = PreviewConfiguration(
            max_length=200,
            sentence_count=3,
            preview_style=PreviewStyle.SUMMARY,
            content_filters=[ContentFilter.EMOTION],
        )

        # Act & Assert
        assert config.should_include_emotion() is True

    def test_should_include_description_returns_true_when_filter_exists(self) -> None:
        """DESCRIPTIONフィルターが存在する場合にTrueが返されることをテスト"""
        # Arrange
        config = PreviewConfiguration(
            max_length=200,
            sentence_count=3,
            preview_style=PreviewStyle.SUMMARY,
            content_filters=[ContentFilter.DESCRIPTION],
        )

        # Act & Assert
        assert config.should_include_description() is True

    def test_get_quality_threshold_returns_correct_threshold(self) -> None:
        """正しい品質基準が返されることをテスト"""
        # Arrange
        target_threshold = QualityThreshold("readability", 0.7, 1.0, 1.0)
        config = PreviewConfiguration(
            max_length=200, sentence_count=3, preview_style=PreviewStyle.SUMMARY, quality_thresholds=[target_threshold]
        )

        # Act
        retrieved_threshold = config.get_quality_threshold("readability")

        # Assert
        assert retrieved_threshold == target_threshold
        assert config.get_quality_threshold("non_existent") is None

    def test_get_minimum_quality_score_returns_weighted_average(self) -> None:
        """品質基準の重み付き平均が返されることをテスト"""
        # Arrange
        thresholds = [QualityThreshold("readability", 0.8, 1.0, 1.0), QualityThreshold("engagement", 0.6, 1.0, 2.0)]
        config = PreviewConfiguration(
            max_length=200, sentence_count=3, preview_style=PreviewStyle.SUMMARY, quality_thresholds=thresholds
        )

        # Act
        min_score = config.get_minimum_quality_score()

        # Assert
        # (0.8 * 1.0 + 0.6 * 2.0) / (1.0 + 2.0) = (0.8 + 1.2) / 3 = 0.667
        expected_score = (0.8 * 1.0 + 0.6 * 2.0) / (1.0 + 2.0)
        assert abs(min_score - expected_score) < 0.001

    def test_get_minimum_quality_score_returns_default_for_empty_thresholds(self) -> None:
        """品質基準が空の場合にデフォルト値が返されることをテスト"""
        # Arrange
        config = PreviewConfiguration(max_length=200, sentence_count=3, preview_style=PreviewStyle.SUMMARY)

        # Act
        min_score = config.get_minimum_quality_score()

        # Assert
        assert min_score == 0.7  # デフォルト値

    def test_to_dict_returns_complete_representation(self) -> None:
        """完全な辞書表現が返されることをテスト"""
        # Arrange
        quality_thresholds = [QualityThreshold("readability", 0.7, 1.0, 1.0)]
        content_filters = [ContentFilter.DIALOGUE]
        style_settings = StyleSettings(emphasis_marker="*")

        config = PreviewConfiguration(
            max_length=200,
            sentence_count=3,
            preview_style=PreviewStyle.SUMMARY,
            content_filters=content_filters,
            style_settings=style_settings,
            quality_thresholds=quality_thresholds,
            preserve_formatting=True,
            include_metadata=False,
            description="テスト設定",
        )

        # Act
        dict_repr = config.to_dict()

        # Assert
        assert dict_repr["max_length"] == 200
        assert dict_repr["sentence_count"] == 3
        assert dict_repr["preview_style"] == "summary"
        assert dict_repr["content_filters"] == ["dialogue"]
        assert dict_repr["style_settings"]["emphasis_marker"] == "*"
        assert len(dict_repr["quality_thresholds"]) == 1
        assert dict_repr["preserve_formatting"] is True
        assert dict_repr["include_metadata"] is False
        assert dict_repr["description"] == "テスト設定"

    def test_from_dict_creates_correct_instance(self) -> None:
        """辞書から正しいインスタンスが作成されることをテスト"""
        # Arrange
        data = {
            "max_length": 200,
            "sentence_count": 3,
            "preview_style": "summary",
            "content_filters": ["dialogue", "action"],
            "style_settings": {"emphasis_marker": "*", "ellipsis": "...", "line_break": "\n", "quote_style": '""'},
            "quality_thresholds": [{"metric_name": "readability", "min_value": 0.7, "max_value": 1.0, "weight": 1.0}],
            "preserve_formatting": True,
            "include_metadata": False,
            "description": "テスト設定",
        }

        # Act
        config = PreviewConfiguration.from_dict(data)

        # Assert
        assert config.max_length == 200
        assert config.sentence_count == 3
        assert config.preview_style == PreviewStyle.SUMMARY
        assert len(config.content_filters) == 2
        assert ContentFilter.DIALOGUE in config.content_filters
        assert ContentFilter.ACTION in config.content_filters
        assert config.style_settings.emphasis_marker == "*"
        assert len(config.quality_thresholds) == 1
        assert config.quality_thresholds[0].metric_name == "readability"
        assert config.preserve_formatting is True
        assert config.include_metadata is False
        assert config.description == "テスト設定"

    def test_create_default_returns_valid_default_config(self) -> None:
        """デフォルト設定が正しく作成されることをテスト"""
        # Act
        config = PreviewConfiguration.create_default()

        # Assert
        assert config.max_length == 200
        assert config.sentence_count == 3
        assert config.preview_style == PreviewStyle.SUMMARY
        assert len(config.content_filters) == 3
        assert ContentFilter.DIALOGUE in config.content_filters
        assert ContentFilter.ACTION in config.content_filters
        assert ContentFilter.EMOTION in config.content_filters
        assert len(config.quality_thresholds) == 3
        assert config.preserve_formatting is False
        assert config.include_metadata is True

    def test_create_teaser_returns_valid_teaser_config(self) -> None:
        """ティザー設定が正しく作成されることをテスト"""
        # Act
        config = PreviewConfiguration.create_teaser()

        # Assert
        assert config.max_length == 150
        assert config.sentence_count == 2
        assert config.preview_style == PreviewStyle.TEASER
        assert len(config.content_filters) == 2
        assert ContentFilter.DIALOGUE in config.content_filters
        assert ContentFilter.ACTION in config.content_filters
        assert config.style_settings.ellipsis == "…?"
        assert config.preserve_formatting is True
        assert config.include_metadata is False

    def test_create_dialogue_focus_returns_valid_dialogue_config(self) -> None:
        """会話重視設定が正しく作成されることをテスト"""
        # Act
        config = PreviewConfiguration.create_dialogue_focus()

        # Assert
        assert config.max_length == 250
        assert config.sentence_count == 4
        assert config.preview_style == PreviewStyle.DIALOGUE_FOCUS
        assert len(config.content_filters) == 2
        assert ContentFilter.DIALOGUE in config.content_filters
        assert ContentFilter.EMOTION in config.content_filters
        assert config.preserve_formatting is True
        assert config.include_metadata is True

    def test_immutability_of_preview_configuration(self) -> None:
        """PreviewConfigurationの不変性をテスト"""
        # Arrange
        config = PreviewConfiguration(max_length=200, sentence_count=3, preview_style=PreviewStyle.SUMMARY)

        # Act & Assert
        with pytest.raises(AttributeError, match=".*"):
            config.max_length = 300  # frozen=Trueなので変更不可

    def test_equality_of_preview_configurations(self) -> None:
        """PreviewConfigurationの等価性をテスト"""
        # Arrange
        config1 = PreviewConfiguration(max_length=200, sentence_count=3, preview_style=PreviewStyle.SUMMARY)
        config2 = PreviewConfiguration(max_length=200, sentence_count=3, preview_style=PreviewStyle.SUMMARY)
        config3 = PreviewConfiguration(max_length=150, sentence_count=2, preview_style=PreviewStyle.TEASER)

        # Act & Assert
        assert config1 == config2
        assert config1 != config3
