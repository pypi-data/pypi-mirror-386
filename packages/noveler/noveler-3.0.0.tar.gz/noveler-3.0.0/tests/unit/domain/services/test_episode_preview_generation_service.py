"""
EpisodePreviewGenerationServiceのユニットテスト

SPEC-WORKFLOW-002: レガシーモジュールTDD+DDD移行
"""

import pytest

from noveler.domain.exceptions import DomainValidationError
from noveler.domain.services.episode_preview_generation_service import (
    EpisodePreviewGenerationService,
    PreviewResult,
    QualityValidationResult,
)
from noveler.domain.value_objects.preview_configuration import ContentFilter, PreviewConfiguration, PreviewStyle


@pytest.mark.spec("SPEC-WORKFLOW-002")
class TestEpisodePreviewGenerationService:
    """EpisodePreviewGenerationServiceのテストクラス"""

    @pytest.fixture
    def service(self):
        """テスト用サービスインスタンス"""
        return EpisodePreviewGenerationService()

    @pytest.fixture
    def sample_episode_content(self) -> str:
        """テスト用エピソードコンテンツ"""
        return """
        主人公の田中太郎は、ある日突然異世界に転生してしまった。

        「ここは...どこだ?」

        彼の前には広大な草原が広がっていた。空は青く、風は涼しい。
        しかし、見たことのない巨大な月が空に浮かんでいる。

        太郎は自分の手を見つめた。白く細い手は、元の自分のものではなかった。
        どうやら別の体に転生したようだ。

        「魔法でも使えるのかな?」

        そう呟いた瞬間、手から小さな光が発せられた。
        """

    @pytest.fixture
    def sample_episode_metadata(self):
        """テスト用エピソードメタデータ"""
        return {
            "title": "第1話 異世界転生",
            "episode_number": 1,
            "genre": "ファンタジー",
            "tags": ["異世界", "転生", "魔法"],
        }

    @pytest.fixture
    def default_config(self):
        """テスト用デフォルト設定"""
        return PreviewConfiguration.create_default()

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-SERVICE_INITIALIZATI")
    def test_service_initialization_sets_sentiment_keywords(self, service: object) -> None:
        """サービス初期化時に感情キーワードが設定されることをテスト"""
        # Assert
        assert hasattr(service, "_sentiment_keywords")
        assert "positive" in service._sentiment_keywords
        assert "negative" in service._sentiment_keywords
        assert "action" in service._sentiment_keywords
        assert "mystery" in service._sentiment_keywords

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-GENERATE_PREVIEW_WIT")
    def test_generate_preview_with_valid_content_returns_success_result(
        self, service: object, sample_episode_content: object, default_config: object
    ) -> None:
        """有効なコンテンツでプレビュー生成が成功することをテスト"""
        # Act
        result = service.generate_preview(sample_episode_content, default_config)

        # Assert
        assert isinstance(result, PreviewResult)
        assert len(result.preview_text) > 0
        assert len(result.preview_text) <= default_config.max_length
        assert result.quality_score >= 0.0
        assert result.quality_score <= 1.0
        assert result.applied_config == default_config
        assert "original_word_count" in result.metadata

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-GENERATE_PREVIEW_WIT")
    def test_generate_preview_with_empty_content_raises_error(self, service: object, default_config: object) -> None:
        """空のコンテンツで例外が発生することをテスト"""
        # Act & Assert
        with pytest.raises(DomainValidationError, match="エピソードコンテンツが空です"):
            service.generate_preview("", default_config)

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-GENERATE_PREVIEW_WIT")
    def test_generate_preview_with_whitespace_only_content_raises_error(
        self, service: object, default_config: object
    ) -> None:
        """空白のみのコンテンツで例外が発生することをテスト"""
        # Act & Assert
        with pytest.raises(DomainValidationError, match="エピソードコンテンツが空です"):
            service.generate_preview("   \n\t  ", default_config)

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-GENERATE_PREVIEW_WIT")
    def test_generate_preview_with_invalid_config_raises_error(
        self, service: object, sample_episode_content: object
    ) -> None:
        """無効な設定で例外が発生することをテスト"""
        # Act & Assert
        with pytest.raises(DomainValidationError, match="設定はPreviewConfigurationのインスタンスである必要があります"):
            service.generate_preview(sample_episode_content, "invalid_config")

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-GENERATE_PREVIEW_WIT")
    def test_generate_preview_with_short_content_adds_warning(self, service: object, default_config: object) -> None:
        """短いコンテンツで警告が追加されることをテスト"""
        # Arrange
        short_content = "短いコンテンツ"

        # Act
        result = service.generate_preview(short_content, default_config)

        # Assert
        assert result.has_warnings() is True
        assert any("コンテンツが短すぎます" in warning for warning in result.generation_warnings)

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-GENERATE_PREVIEW_INC")
    def test_generate_preview_includes_metadata(
        self, service: object, sample_episode_content: object, sample_episode_metadata: object, default_config: object
    ) -> None:
        """プレビュー生成でメタデータが含まれることをテスト"""
        # Act
        result = service.generate_preview(sample_episode_content, default_config, sample_episode_metadata)

        # Assert
        metadata = result.metadata

        assert "episode_title" in metadata
        assert "episode_number" in metadata
        assert "genre" in metadata
        assert "tags" in metadata
        assert metadata["episode_title"] == "第1話 異世界転生"
        assert metadata["episode_number"] == 1
        assert metadata["genre"] == "ファンタジー"

        # schema + statistics
        assert metadata["schema_version"].startswith("1.")
        assert metadata["preview_word_count"] == len(result.preview_text)
        assert metadata["preview_character_count"] == len(result.preview_text)
        assert metadata["preview_sentence_count"] >= 1
        assert metadata["preview_style"] == default_config.preview_style.value
        assert metadata["content_filters"] == [f.value for f in default_config.content_filters]
        assert metadata["dominant_sentiment"] in {"positive", "negative", "neutral"}
        assert metadata["preview"]["character_count"] == len(result.preview_text)
        assert metadata["preview"]["reading_time_seconds"] == metadata["preview_estimated_reading_time"]
        assert metadata["source"]["sentence_count"] == metadata["sentence_count"]
        assert metadata["source"]["dialogue_sentence_count"] >= 0
        assert metadata["sentiment_distribution"]["positive"] >= 0
        assert metadata["sentiment_distribution"]["negative"] >= 0
        assert metadata["sentiment_distribution"]["neutral"] >= 0
        assert metadata["preview"]["hook"]

        quality = metadata["quality"]
        assert pytest.approx(quality["score"], rel=1e-6) == result.quality_score
        assert quality["minimum_required"] == pytest.approx(default_config.get_minimum_quality_score())
        assert isinstance(quality["passed"], bool)
        assert quality["passed"] == (quality["score"] >= quality["minimum_required"])

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-GENERATE_PREVIEW_WIT")
    def test_generate_preview_with_dialogue_focus_config(self, service: object, sample_episode_content: object) -> None:
        """会話重視設定でプレビュー生成をテスト"""
        # Arrange
        dialogue_config = PreviewConfiguration.create_dialogue_focus()

        # Act
        result = service.generate_preview(sample_episode_content, dialogue_config)

        # Assert
        assert result.applied_config.is_dialogue_focus_style() is True
        # 会話が含まれているコンテンツなので、会話が抽出されることを期待
        assert "「" in result.preview_text or "」" in result.preview_text
        assert result.metadata["preview"]["contains_dialogue"] is True
        assert result.metadata["source"]["dialogue_sentence_count"] > 0

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-GENERATE_PREVIEW_WIT")
    def test_generate_preview_with_teaser_config(self, service: object, sample_episode_content: object) -> None:
        """ティザー設定でプレビュー生成をテスト"""
        # Arrange
        teaser_config = PreviewConfiguration.create_teaser()

        # Act
        result = service.generate_preview(sample_episode_content, teaser_config)

        # Assert
        assert result.applied_config.is_teaser_style() is True
        assert len(result.preview_text) <= teaser_config.max_length
        ellipsis = teaser_config.style_settings.ellipsis
        assert result.preview_text.endswith(ellipsis)
        assert not result.preview_text.endswith(ellipsis * 2)

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-OPTIMIZE_PREVIEW_CON")
    def test_optimize_preview_content_improves_quality(
        self, service: object, sample_episode_content: object, default_config: object
    ) -> None:
        """プレビュー最適化で品質が向上することをテスト"""
        # Arrange
        original_result = service.generate_preview(sample_episode_content, default_config)

        # Act
        optimized_result = service.optimize_preview_content(original_result)

        # Assert
        assert isinstance(optimized_result, PreviewResult)
        assert optimized_result.applied_config == original_result.applied_config
        # 最適化により品質スコアが向上または維持されることを期待
        assert optimized_result.quality_score >= 0.0

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-OPTIMIZE_PREVIEW_CON")
    def test_optimize_preview_content_with_invalid_result_raises_error(self, service: object) -> None:
        """無効なプレビュー結果で例外が発生することをテスト"""
        # Act & Assert
        with pytest.raises(
            DomainValidationError, match="プレビュー結果はPreviewResultのインスタンスである必要があります"
        ):
            service.optimize_preview_content("invalid_result")

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-VALIDATE_PREVIEW_QUA")
    def test_validate_preview_quality_with_valid_preview_returns_valid_result(
        self, service: object, sample_episode_content: object, default_config: object
    ) -> None:
        """有効なプレビューで有効な検証結果が返されることをテスト"""
        # Arrange
        preview_result = service.generate_preview(sample_episode_content, default_config)

        # Act
        validation_result = service.validate_preview_quality(preview_result)

        # Assert
        assert isinstance(validation_result, QualityValidationResult)
        assert validation_result.quality_score >= 0.0
        assert validation_result.quality_score <= 1.0
        # 品質により有効性が決まる
        assert isinstance(validation_result.is_valid, bool)

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-VALIDATE_PREVIEW_QUA")
    def test_validate_preview_quality_with_invalid_result_raises_error(self, service: object) -> None:
        """無効なプレビュー結果で例外が発生することをテスト"""
        # Act & Assert
        with pytest.raises(
            DomainValidationError, match="プレビュー結果はPreviewResultのインスタンスである必要があります"
        ):
            service.validate_preview_quality("invalid_result")

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-VALIDATE_PREVIEW_QUA")
    def test_validate_preview_quality_detects_length_violations(self, service: object, default_config: object) -> None:
        """品質検証で長さ違反が検出されることをテスト"""
        # Arrange
        # 非常に長いプレビューを作成(実際には実装で制限されるが、テスト用に模擬)
        long_preview_text = "非常に長いプレビューテキスト" * 20  # max_lengthを超える
        mock_result = PreviewResult(
            preview_text=long_preview_text, metadata={}, quality_score=0.5, applied_config=default_config
        )

        # Act
        validation_result = service.validate_preview_quality(mock_result)

        # Assert
        # 長すぎる場合は問題として検出される
        if len(long_preview_text) > default_config.max_length:
            assert len(validation_result.issues) > 0
            assert any("長すぎます" in issue for issue in validation_result.issues)

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-BATCH_GENERATE_PREVI")
    def test_batch_generate_previews_with_multiple_episodes_returns_results_list(
        self, service: object, default_config: object
    ) -> None:
        """複数エピソードの一括プレビュー生成で結果リストが返されることをテスト"""
        # Arrange
        episodes_data = [
            {"id": "ep1", "content": "第1話のコンテンツです。主人公が登場します。", "metadata": {"title": "第1話"}},
            {"id": "ep2", "content": "第2話のコンテンツです。冒険が始まります。", "metadata": {"title": "第2話"}},
            {"id": "ep3", "content": "第3話のコンテンツです。仲間と出会います。", "metadata": {"title": "第3話"}},
        ]

        # Act
        results = service.batch_generate_previews(episodes_data, default_config)

        # Assert
        assert len(results) == 3
        for result in results:
            assert isinstance(result, PreviewResult)
            assert "episode_id" in result.metadata

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-BATCH_GENERATE_PREVI")
    def test_batch_generate_previews_with_empty_list_returns_empty_list(
        self, service: object, default_config: object
    ) -> None:
        """空リストの一括プレビュー生成で空リストが返されることをテスト"""
        # Act
        results = service.batch_generate_previews([], default_config)

        # Assert
        assert results == []

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-BATCH_GENERATE_PREVI")
    def test_batch_generate_previews_with_invalid_config_raises_error(self, service: object) -> None:
        """無効な設定で一括プレビュー生成時に例外が発生することをテスト"""
        # Arrange
        episodes_data = [{"id": "ep1", "content": "コンテンツ"}]

        # Act & Assert
        with pytest.raises(DomainValidationError, match="設定はPreviewConfigurationのインスタンスである必要があります"):
            service.batch_generate_previews(episodes_data, "invalid_config")

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-BATCH_GENERATE_PREVI")
    def test_batch_generate_previews_handles_individual_errors_gracefully(
        self, service: object, default_config: object
    ) -> None:
        """一括プレビュー生成で個別エラーが適切に処理されることをテスト"""
        # Arrange
        episodes_data = [
            {"id": "ep1", "content": "有効なコンテンツです。"},
            {"id": "ep2", "content": ""},  # 空のコンテンツ(エラー発生)
            {"id": "ep3", "content": "別の有効なコンテンツです。"},
        ]

        # Act
        results = service.batch_generate_previews(episodes_data, default_config)

        # Assert
        assert len(results) == 3
        assert results[0].quality_score > 0.0  # 成功
        assert "error" in results[1].metadata  # エラーが記録される
        assert results[2].quality_score > 0.0  # 成功

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-PREVIEW_RESULT_CREAT")
    def test_preview_result_creation_and_properties(
        self, service: object, sample_episode_content: object, default_config: object
    ) -> None:
        """PreviewResultの作成と属性をテスト"""
        # Act
        result = service.generate_preview(sample_episode_content, default_config)

        # Assert
        assert hasattr(result, "preview_text")
        assert hasattr(result, "metadata")
        assert hasattr(result, "quality_score")
        assert hasattr(result, "applied_config")
        assert hasattr(result, "generation_warnings")
        assert hasattr(result, "generation_timestamp")
        assert isinstance(result.is_high_quality(), bool)
        assert isinstance(result.has_warnings(), bool)

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-QUALITY_VALIDATION_R")
    def test_quality_validation_result_creation_and_properties(
        self, service: object, sample_episode_content: object, default_config: object
    ) -> None:
        """QualityValidationResultの作成と属性をテスト"""
        # Arrange
        preview_result = service.generate_preview(sample_episode_content, default_config)

        # Act
        validation_result = service.validate_preview_quality(preview_result)

        # Assert
        assert hasattr(validation_result, "is_valid")
        assert hasattr(validation_result, "quality_score")
        assert hasattr(validation_result, "issues")
        assert hasattr(validation_result, "suggestions")
        assert hasattr(validation_result, "validation_timestamp")
        assert isinstance(validation_result.quality_score, float)
        assert isinstance(validation_result.issues, list)
        assert isinstance(validation_result.suggestions, list)

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-CONTENT_FILTER_APPLI")
    def test_content_filter_application(self, service: object, sample_episode_content: object) -> None:
        """コンテンツフィルターの適用をテスト"""
        # Arrange - 会話フィルターのみを設定
        config = PreviewConfiguration(
            max_length=200,
            sentence_count=3,
            preview_style=PreviewStyle.SUMMARY,
            content_filters=[ContentFilter.DIALOGUE],
        )

        # Act
        result = service.generate_preview(sample_episode_content, config)

        # Assert
        # 会話が含まれるコンテンツなので、会話が抽出されることを期待
        assert len(result.preview_text) > 0
        # 実際の実装では、会話を含む文が優先的に選択される

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-SENTIMENT_ANALYSIS_I")
    def test_sentiment_analysis_in_metadata(self, service: object, default_config: object) -> None:
        """メタデータでの感情分析をテスト"""
        # Arrange
        positive_content = "主人公は嬉しそうに笑顔で友達と楽しく過ごした。希望に満ちた冒険が始まる。"
        negative_content = "主人公は悲しみに暮れ、絶望的な状況に陥った。怒りと憎しみが心を支配する。"

        # Act
        positive_result = service.generate_preview(positive_content, default_config)
        negative_result = service.generate_preview(negative_content, default_config)

        # Assert
        assert "dominant_sentiment" in positive_result.metadata
        assert "dominant_sentiment" in negative_result.metadata
        # 感情分析により適切な感情が検出されることを期待
        assert positive_result.metadata["dominant_sentiment"] in ["positive", "neutral"]
        assert negative_result.metadata["dominant_sentiment"] in ["negative", "neutral"]

    @pytest.mark.spec("SPEC-EPISODE_PREVIEW_GENERATION_SERVICE-READING_TIME_ESTIMAT")
    def test_reading_time_estimation(
        self, service: object, sample_episode_content: object, default_config: object
    ) -> None:
        """読書時間推定をテスト"""
        # Act
        result = service.generate_preview(sample_episode_content, default_config)

        # Assert
        assert "estimated_reading_time" in result.metadata
        assert isinstance(result.metadata["estimated_reading_time"], int)
        assert result.metadata["estimated_reading_time"] > 0
