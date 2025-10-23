#!/usr/bin/env python3
"""QualityStandardsのユニットテスト

TDD原則に従い、品質基準システムのビジネスロジックをテスト
"""

import pytest

from noveler.domain.value_objects.quality_standards import (
    Genre,
    QualityStandard,
    QualityStandardRepository,
    QualityThreshold,
    WriterLevel,
    WriterProgressRepository,
)


class TestQualityThreshold:
    """QualityThresholdのテスト"""

    @pytest.mark.spec("SPEC-QUALITY-001")
    @pytest.mark.requirement("REQ-2.4.1")
    @pytest.mark.requirement("REQ-2.4.3")
    def test_create_valid_threshold(self) -> None:
        """有効な閾値の作成

        仕様書: specs/SPEC-QUALITY-001_quality_check_system.md
        要件: 最低品質スコアの設定と判定、段階的な品質基準(SPEC-QUALITY-004の要件)
        """
        # When
        threshold = QualityThreshold(minimum_score=60, target_score=70, excellent_score=80)

        # Then
        assert threshold.minimum_score == 60
        assert threshold.target_score == 70
        assert threshold.excellent_score == 80

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-CREATE_THRESHOLD_WIT")
    def test_create_threshold_with_boundary_values(self) -> None:
        """境界値での閾値作成"""
        # When
        threshold = QualityThreshold(minimum_score=0, target_score=50, excellent_score=100)

        # Then
        assert threshold.minimum_score == 0
        assert threshold.target_score == 50
        assert threshold.excellent_score == 100

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-CREATE_THRESHOLD_WIT")
    def test_create_threshold_with_same_values(self) -> None:
        """同じ値での閾値作成"""
        # When
        threshold = QualityThreshold(minimum_score=70, target_score=70, excellent_score=70)

        # Then
        assert threshold.minimum_score == 70
        assert threshold.target_score == 70
        assert threshold.excellent_score == 70

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-CREATE_INVALID_THRES")
    def test_create_invalid_threshold_minimum_greater_than_target(self) -> None:
        """最低スコアが目標スコアより大きい場合はエラー"""
        # When/Then
        with pytest.raises(
            ValueError, match="スコアは0-100の範囲で、minimum <= target <= excellentである必要があります"
        ):
            QualityThreshold(minimum_score=80, target_score=70, excellent_score=90)

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-CREATE_INVALID_THRES")
    def test_create_invalid_threshold_target_greater_than_excellent(self) -> None:
        """目標スコアが優秀スコアより大きい場合はエラー"""
        # When/Then
        with pytest.raises(
            ValueError, match="スコアは0-100の範囲で、minimum <= target <= excellentである必要があります"
        ):
            QualityThreshold(minimum_score=60, target_score=90, excellent_score=80)

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-CREATE_INVALID_THRES")
    def test_create_invalid_threshold_negative_score(self) -> None:
        """負のスコアはエラー"""
        # When/Then
        with pytest.raises(
            ValueError, match="スコアは0-100の範囲で、minimum <= target <= excellentである必要があります"
        ):
            QualityThreshold(minimum_score=-10, target_score=70, excellent_score=80)

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-CREATE_INVALID_THRES")
    def test_create_invalid_threshold_over_100(self) -> None:
        """100を超えるスコアはエラー"""
        # When/Then
        with pytest.raises(
            ValueError, match="スコアは0-100の範囲で、minimum <= target <= excellentである必要があります"
        ):
            QualityThreshold(minimum_score=60, target_score=70, excellent_score=110)

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-THRESHOLD_IMMUTABILI")
    def test_threshold_immutability(self) -> None:
        """閾値は不変であること"""
        # Given
        threshold = QualityThreshold(minimum_score=60, target_score=70, excellent_score=80)

        # When/Then
        with pytest.raises(AttributeError, match=".*"):
            threshold.minimum_score = 65


class TestQualityStandard:
    """QualityStandardのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-CREATE_QUALITY_STAND")
    def test_create_quality_standard(self) -> None:
        """品質基準の作成"""
        # Given
        thresholds = {
            "basic_writing": QualityThreshold(50, 60, 70),
            "story_structure": QualityThreshold(55, 65, 75),
        }
        weight_adjustments = {
            "basic_writing": 1.2,
            "story_structure": 0.8,
        }

        # When
        standard = QualityStandard(
            writer_level=WriterLevel.BEGINNER,
            genre=Genre.FANTASY,
            thresholds=thresholds,
            weight_adjustments=weight_adjustments,
        )

        # Then
        assert standard.writer_level == WriterLevel.BEGINNER
        assert standard.genre == Genre.FANTASY
        assert standard.thresholds == thresholds
        assert standard.weight_adjustments == weight_adjustments

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GET_THRESHOLD_EXISTI")
    def test_get_threshold_existing(self) -> None:
        """存在するチェック項目の閾値取得"""
        # Given
        threshold = QualityThreshold(50, 60, 70)
        standard = QualityStandard(
            writer_level=WriterLevel.BEGINNER,
            genre=Genre.FANTASY,
            thresholds={"basic_writing": threshold},
            weight_adjustments={},
        )

        # When
        result = standard.get_threshold("basic_writing")

        # Then
        assert result == threshold

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GET_THRESHOLD_NON_EX")
    def test_get_threshold_non_existing_beginner(self) -> None:
        """存在しないチェック項目の閾値取得(初心者)"""
        # Given
        standard = QualityStandard(
            writer_level=WriterLevel.BEGINNER, genre=Genre.FANTASY, thresholds={}, weight_adjustments={}
        )

        # When
        result = standard.get_threshold("non_existing")

        # Then
        assert result.minimum_score == 50
        assert result.target_score == 60
        assert result.excellent_score == 70

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GET_THRESHOLD_NON_EX")
    def test_get_threshold_non_existing_intermediate(self) -> None:
        """存在しないチェック項目の閾値取得(中級者)"""
        # Given
        standard = QualityStandard(
            writer_level=WriterLevel.INTERMEDIATE, genre=Genre.FANTASY, thresholds={}, weight_adjustments={}
        )

        # When
        result = standard.get_threshold("non_existing")

        # Then
        assert result.minimum_score == 60
        assert result.target_score == 70
        assert result.excellent_score == 80

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GET_THRESHOLD_NON_EX")
    def test_get_threshold_non_existing_advanced(self) -> None:
        """存在しないチェック項目の閾値取得(上級者)"""
        # Given
        standard = QualityStandard(
            writer_level=WriterLevel.ADVANCED, genre=Genre.FANTASY, thresholds={}, weight_adjustments={}
        )

        # When
        result = standard.get_threshold("non_existing")

        # Then
        assert result.minimum_score == 70
        assert result.target_score == 80
        assert result.excellent_score == 90

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GET_THRESHOLD_NON_EX")
    def test_get_threshold_non_existing_expert(self) -> None:
        """存在しないチェック項目の閾値取得(エキスパート)"""
        # Given
        standard = QualityStandard(
            writer_level=WriterLevel.EXPERT, genre=Genre.FANTASY, thresholds={}, weight_adjustments={}
        )

        # When
        result = standard.get_threshold("non_existing")

        # Then
        assert result.minimum_score == 75
        assert result.target_score == 85
        assert result.excellent_score == 95

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GET_WEIGHT_EXISTING")
    def test_get_weight_existing(self) -> None:
        """存在するチェック項目の重み取得"""
        # Given
        standard = QualityStandard(
            writer_level=WriterLevel.BEGINNER,
            genre=Genre.FANTASY,
            thresholds={},
            weight_adjustments={"basic_writing": 1.5},
        )

        # When
        result = standard.get_weight("basic_writing")

        # Then
        assert result == 1.5

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GET_WEIGHT_NON_EXIST")
    def test_get_weight_non_existing(self) -> None:
        """存在しないチェック項目の重み取得(デフォルト値)"""
        # Given
        standard = QualityStandard(
            writer_level=WriterLevel.BEGINNER, genre=Genre.FANTASY, thresholds={}, weight_adjustments={}
        )

        # When
        result = standard.get_weight("non_existing")

        # Then
        assert result == 1.0

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-QUALITY_STANDARD_IMM")
    def test_quality_standard_immutability(self) -> None:
        """品質基準は不変であること"""
        # Given
        standard = QualityStandard(
            writer_level=WriterLevel.BEGINNER, genre=Genre.FANTASY, thresholds={}, weight_adjustments={}
        )

        # When/Then
        with pytest.raises(AttributeError, match=".*"):
            standard.writer_level = WriterLevel.INTERMEDIATE


class TestGenreEnum:
    """Genreのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-ALL_GENRES_DEFINED")
    def test_all_genres_defined(self) -> None:
        """全てのジャンルが定義されている"""
        # When
        genres = list(Genre)

        # Then
        assert Genre.FANTASY in genres
        assert Genre.ROMANCE in genres
        assert Genre.MYSTERY in genres
        assert Genre.SF in genres
        assert Genre.LITERARY in genres
        assert Genre.LIGHT_NOVEL in genres
        assert Genre.OTHER in genres
        assert len(genres) == 7

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GENRE_VALUES")
    def test_genre_values(self) -> None:
        """ジャンルの値が正しい"""
        assert Genre.FANTASY.value == "fantasy"
        assert Genre.ROMANCE.value == "romance"
        assert Genre.MYSTERY.value == "mystery"
        assert Genre.SF.value == "science_fiction"
        assert Genre.LITERARY.value == "literary"
        assert Genre.LIGHT_NOVEL.value == "light_novel"
        assert Genre.OTHER.value == "other"


class TestWriterLevelEnum:
    """WriterLevelのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-ALL_LEVELS_DEFINED")
    def test_all_levels_defined(self) -> None:
        """全てのレベルが定義されている"""
        # When
        levels = list(WriterLevel)

        # Then
        assert WriterLevel.BEGINNER in levels
        assert WriterLevel.INTERMEDIATE in levels
        assert WriterLevel.ADVANCED in levels
        assert WriterLevel.EXPERT in levels
        assert len(levels) == 4

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-LEVEL_VALUES")
    def test_level_values(self) -> None:
        """レベルの値が正しい"""
        assert WriterLevel.BEGINNER.value == "beginner"
        assert WriterLevel.INTERMEDIATE.value == "intermediate"
        assert WriterLevel.ADVANCED.value == "advanced"
        assert WriterLevel.EXPERT.value == "expert"


class TestQualityStandardRepository:
    """QualityStandardRepositoryのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GET_STANDARD_NOT_IMP")
    def test_get_standard_not_implemented(self) -> None:
        """get_standardは実装が必要"""
        # Given - 抽象クラスなので具体的な実装を作る
        class TestRepo(QualityStandardRepository):
            def get_standard(self, level: WriterLevel, genre: Genre) -> QualityStandard:
                raise NotImplementedError("Subclasses must implement get_standard")

            def save_standard(self, standard: QualityStandard) -> None:
                raise NotImplementedError("Subclasses must implement save_standard")

        repo = TestRepo()

        # When/Then
        with pytest.raises(NotImplementedError, match=".*"):
            repo.get_standard(WriterLevel.BEGINNER, Genre.FANTASY)

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-SAVE_STANDARD_NOT_IM")
    def test_save_standard_not_implemented(self) -> None:
        """save_standardは実装が必要"""
        # Given - 抽象クラスなので具体的な実装を作る
        class TestRepo(QualityStandardRepository):
            def get_standard(self, level: WriterLevel, genre: Genre) -> QualityStandard:
                raise NotImplementedError("Subclasses must implement get_standard")

            def save_standard(self, standard: QualityStandard) -> None:
                raise NotImplementedError("Subclasses must implement save_standard")

        repo = TestRepo()
        standard = QualityStandard(
            writer_level=WriterLevel.BEGINNER, genre=Genre.FANTASY, thresholds={}, weight_adjustments={}
        )

        # When/Then
        with pytest.raises(NotImplementedError, match=".*"):
            repo.save_standard(standard)


class TestWriterProgressRepository:
    """WriterProgressRepositoryのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GET_COMPLETED_EPISOD")
    def test_get_completed_episodes_count_not_implemented(self) -> None:
        """get_completed_episodes_countは実装が必要"""
        # Given - 抽象クラスなので具体的な実装を作る
        class TestRepo(WriterProgressRepository):
            def get_completed_episodes_count(self, project_id: str) -> int:
                raise NotImplementedError("Subclasses must implement get_completed_episodes_count")

            def get_average_quality_score(self, project_id: str) -> float:
                raise NotImplementedError("Subclasses must implement get_average_quality_score")

        repo = TestRepo()

        # When/Then
        with pytest.raises(NotImplementedError, match=".*"):
            repo.get_completed_episodes_count("project_id")

    @pytest.mark.spec("SPEC-QUALITY_STANDARDS-GET_AVERAGE_QUALITY_")
    def test_get_average_quality_score_not_implemented(self) -> None:
        """get_average_quality_scoreは実装が必要"""
        # Given - 抽象クラスなので具体的な実装を作る
        class TestRepo(WriterProgressRepository):
            def get_completed_episodes_count(self, project_id: str) -> int:
                raise NotImplementedError("Subclasses must implement get_completed_episodes_count")

            def get_average_quality_score(self, project_id: str) -> float:
                raise NotImplementedError("Subclasses must implement get_average_quality_score")

        repo = TestRepo()

        # When/Then
        with pytest.raises(NotImplementedError, match=".*"):
            repo.get_average_quality_score("project_id")
