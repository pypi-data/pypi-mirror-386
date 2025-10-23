#!/usr/bin/env python3
"""エピソード完成データ値オブジェクトのユニットテスト

TDD原則に従い、値オブジェクトの不変条件とビジネスロジックをテスト
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

pytestmark = pytest.mark.plot_episode



from noveler.domain.exceptions import ValidationError
from noveler.domain.value_objects.episode_completion_data import EpisodeCompletionData
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestEpisodeCompletionData:
    """EpisodeCompletionData値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_create_valid_completion_data(self) -> None:
        """有効な完成データの作成"""
        # Given
        now = datetime.now(timezone.utc)
        quality_results = {
            "basic_writing_style": {"score": 85.0, "passed": True},
            "story_structure": {"score": 90.0, "passed": True},
        }

        # When
        data = EpisodeCompletionData(
            project_name="テストプロジェクト",
            episode_number=1,
            completion_status="執筆済み",
            quality_score=87.5,
            quality_grade="A",
            word_count=5000,
            revision_count=3,
            completion_date=now,
            quality_check_results=quality_results,
        )

        # Then
        assert data.project_name == "テストプロジェクト"
        assert data.episode_number == 1
        assert data.completion_status == "執筆済み"
        assert data.quality_score == 87.5
        assert data.quality_grade == "A"
        assert data.word_count == 5000
        assert data.revision_count == 3
        assert data.completion_date == now
        assert data.quality_check_results == quality_results

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_number_validation_zero(self) -> None:
        """エピソード番号が0の場合のバリデーション"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            EpisodeCompletionData(
                project_name="テスト",
                episode_number=0,
                completion_status="執筆済み",
                quality_score=80.0,
                quality_grade="B",
                word_count=5000,
                revision_count=1,
                completion_date=project_now().datetime,
                quality_check_results={},
            )

        assert "エピソード番号は1以上である必要があります" in str(exc.value)

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_number_validation_negative(self) -> None:
        """エピソード番号が負の場合のバリデーション"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            EpisodeCompletionData(
                project_name="テスト",
                episode_number=-1,
                completion_status="執筆済み",
                quality_score=80.0,
                quality_grade="B",
                word_count=5000,
                revision_count=1,
                completion_date=project_now().datetime,
                quality_check_results={},
            )

        assert "エピソード番号は1以上である必要があります" in str(exc.value)

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_quality_score_validation_too_low(self) -> None:
        """品質スコアが低すぎる場合のバリデーション"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            EpisodeCompletionData(
                project_name="テスト",
                episode_number=1,
                completion_status="執筆済み",
                quality_score=-0.1,
                quality_grade="F",
                word_count=5000,
                revision_count=1,
                completion_date=project_now().datetime,
                quality_check_results={},
            )

        assert "品質スコアは0から100の範囲である必要があります" in str(exc.value)

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_quality_score_validation_too_high(self) -> None:
        """品質スコアが高すぎる場合のバリデーション"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            EpisodeCompletionData(
                project_name="テスト",
                episode_number=1,
                completion_status="執筆済み",
                quality_score=100.1,
                quality_grade="S",
                word_count=5000,
                revision_count=1,
                completion_date=project_now().datetime,
                quality_check_results={},
            )

        assert "品質スコアは0から100の範囲である必要があります" in str(exc.value)

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_quality_score_boundary_values(self) -> None:
        """品質スコアの境界値テスト"""
        # 0は有効
        data1 = EpisodeCompletionData(
            project_name="テスト",
            episode_number=1,
            completion_status="執筆済み",
            quality_score=0.0,
            quality_grade="F",
            word_count=5000,
            revision_count=1,
            completion_date=project_now().datetime,
            quality_check_results={},
        )

        assert data1.quality_score == 0.0

        # 100は有効
        data2 = EpisodeCompletionData(
            project_name="テスト",
            episode_number=1,
            completion_status="執筆済み",
            quality_score=100.0,
            quality_grade="S",
            word_count=5000,
            revision_count=1,
            completion_date=project_now().datetime,
            quality_check_results={},
        )

        assert data2.quality_score == 100.0

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_word_count_validation_negative(self) -> None:
        """文字数が負の場合のバリデーション"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            EpisodeCompletionData(
                project_name="テスト",
                episode_number=1,
                completion_status="執筆済み",
                quality_score=80.0,
                quality_grade="B",
                word_count=-1,
                revision_count=1,
                completion_date=project_now().datetime,
                quality_check_results={},
            )

        assert "文字数は0以上である必要があります" in str(exc.value)

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_word_count_zero_allowed(self) -> None:
        """文字数0は許可される"""
        # When
        data = EpisodeCompletionData(
            project_name="テスト",
            episode_number=1,
            completion_status="未執筆",
            quality_score=0.0,
            quality_grade="F",
            word_count=0,
            revision_count=0,
            completion_date=project_now().datetime,
            quality_check_results={},
        )

        # Then
        assert data.word_count == 0

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_revision_count_validation_negative(self) -> None:
        """修正回数が負の場合のバリデーション"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            EpisodeCompletionData(
                project_name="テスト",
                episode_number=1,
                completion_status="執筆済み",
                quality_score=80.0,
                quality_grade="B",
                word_count=5000,
                revision_count=-1,
                completion_date=project_now().datetime,
                quality_check_results={},
            )

        assert "修正回数は0以上である必要があります" in str(exc.value)

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_revision_count_zero_allowed(self) -> None:
        """修正回数0は許可される"""
        # When
        data = EpisodeCompletionData(
            project_name="テスト",
            episode_number=1,
            completion_status="執筆済み",
            quality_score=95.0,
            quality_grade="S",
            word_count=5000,
            revision_count=0,
            completion_date=project_now().datetime,
            quality_check_results={},
        )

        # Then
        assert data.revision_count == 0

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_project_name_security_validation(self) -> None:
        """プロジェクト名のセキュリティバリデーション"""
        # HTML特殊文字のテスト
        invalid_chars = ["<", ">", "&", '"', "'"]

        for char in invalid_chars:
            with pytest.raises(ValidationError) as exc:
                EpisodeCompletionData(
                    project_name=f"テスト{char}プロジェクト",
                    episode_number=1,
                    completion_status="執筆済み",
                    quality_score=80.0,
                    quality_grade="B",
                    word_count=5000,
                    revision_count=1,
                    completion_date=project_now().datetime,
                    quality_check_results={},
                )

            assert "不正な文字が含まれています" in str(exc.value)

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_project_name_japanese_allowed(self) -> None:
        """日本語のプロジェクト名は許可される"""
        # When
        data = EpisodeCompletionData(
            project_name="転生したら最強の魔法使いだった件",
            episode_number=1,
            completion_status="執筆済み",
            quality_score=80.0,
            quality_grade="B",
            word_count=5000,
            revision_count=1,
            completion_date=project_now().datetime,
            quality_check_results={},
        )

        # Then
        assert data.project_name == "転生したら最強の魔法使いだった件"

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_to_dict_conversion(self) -> None:
        """辞書形式への変換"""
        # Given
        completion_date = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        quality_results = {
            "basic_writing_style": {"score": 85.0, "passed": True},
            "story_structure": {"score": 90.0, "passed": True},
        }

        data = EpisodeCompletionData(
            project_name="テストプロジェクト",
            episode_number=5,
            completion_status="執筆済み",
            quality_score=87.5,
            quality_grade="A",
            word_count=5000,
            revision_count=2,
            completion_date=completion_date,
            quality_check_results=quality_results,
        )

        # When
        with patch("noveler.domain.value_objects.episode_completion_data.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
            result = data.to_dict()

        # Then
        assert result["completion_status"] == "執筆済み"
        assert result["completion_date"] == "2024-01-01T10:00:00"
        assert result["quality_score"] == 87.5
        assert result["quality_grade"] == "A"
        assert result["word_count"] == 5000
        assert result["revision_count"] == 2
        assert result["last_updated"] == "2024-01-01T12:00:00"
        assert result["quality_check_results"] == quality_results

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_to_dict_preserves_quality_check_results(self) -> None:
        """to_dictが品質チェック結果を保持する"""
        # Given
        complex_results = {
            "basic_writing_style": {"score": 85.0, "passed": True, "details": {"redundancy": 0.1, "clarity": 0.9}},
            "story_structure": {"score": 90.0, "passed": True, "details": {"pacing": "good", "coherence": "excellent"}},
        }

        data = EpisodeCompletionData(
            project_name="テスト",
            episode_number=1,
            completion_status="執筆済み",
            quality_score=87.5,
            quality_grade="A",
            word_count=5000,
            revision_count=1,
            completion_date=project_now().datetime,
            quality_check_results=complex_results,
        )

        # When
        result = data.to_dict()

        # Then
        assert result["quality_check_results"] == complex_results

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_immutability(self) -> None:
        """値オブジェクトの不変性"""
        # Given
        data = EpisodeCompletionData(
            project_name="テスト",
            episode_number=1,
            completion_status="執筆済み",
            quality_score=80.0,
            quality_grade="B",
            word_count=5000,
            revision_count=1,
            completion_date=project_now().datetime,
            quality_check_results={},
        )

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            data.project_name = "変更されたプロジェクト"

        with pytest.raises(AttributeError, match=".*"):
            data.episode_number = 2

        with pytest.raises(AttributeError, match=".*"):
            data.quality_score = 90.0

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_various_completion_statuses(self) -> None:
        """様々な完成ステータスでの作成"""
        statuses = ["未執筆", "執筆中", "執筆済み", "推敲済み", "公開済み"]

        for status in statuses:
            data = EpisodeCompletionData(
                project_name="テスト",
                episode_number=1,
                completion_status=status,
                quality_score=80.0,
                quality_grade="B",
                word_count=5000,
                revision_count=1,
                completion_date=project_now().datetime,
                quality_check_results={},
            )

            assert data.completion_status == status

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_various_quality_grades(self) -> None:
        """様々な品質グレードでの作成"""
        grades = ["S", "A", "B", "C", "D", "F"]

        for grade in grades:
            data = EpisodeCompletionData(
                project_name="テスト",
                episode_number=1,
                completion_status="執筆済み",
                quality_score=80.0,
                quality_grade=grade,
                word_count=5000,
                revision_count=1,
                completion_date=project_now().datetime,
                quality_check_results={},
            )

            assert data.quality_grade == grade

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_large_episode_number(self) -> None:
        """大きなエピソード番号のテスト"""
        # When
        data = EpisodeCompletionData(
            project_name="長編小説",
            episode_number=999,
            completion_status="執筆済み",
            quality_score=85.0,
            quality_grade="A",
            word_count=5000,
            revision_count=1,
            completion_date=project_now().datetime,
            quality_check_results={},
        )

        # Then
        assert data.episode_number == 999

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_high_revision_count(self) -> None:
        """高い修正回数のテスト"""
        # When
        data = EpisodeCompletionData(
            project_name="テスト",
            episode_number=1,
            completion_status="推敲済み",
            quality_score=95.0,
            quality_grade="S",
            word_count=5000,
            revision_count=20,
            completion_date=project_now().datetime,
            quality_check_results={},
        )

        # Then
        assert data.revision_count == 20

    @pytest.mark.spec("SPEC-EPISODE-006")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_empty_quality_check_results(self) -> None:
        """空の品質チェック結果"""
        # When
        data = EpisodeCompletionData(
            project_name="テスト",
            episode_number=1,
            completion_status="執筆済み",
            quality_score=80.0,
            quality_grade="B",
            word_count=5000,
            revision_count=1,
            completion_date=project_now().datetime,
            quality_check_results={},
        )

        # Then
        assert data.quality_check_results == {}
