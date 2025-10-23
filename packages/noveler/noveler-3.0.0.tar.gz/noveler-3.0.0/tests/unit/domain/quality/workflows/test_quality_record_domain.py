#!/usr/bin/env python3
"""品質記録ドメインエンティティのテスト
TDD原則:失敗するテストを先に書く(RED段階)


仕様書: SPEC-UNIT-TEST
"""

from datetime import timedelta
from decimal import Decimal

import pytest
pytestmark = pytest.mark.quality_domain


from noveler.domain.entities.quality_record import QualityRecord, QualityRecordEntry
from noveler.domain.exceptions import QualityRecordError
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_check_result import (
    AutoFix,
    CategoryScores,
    QualityCheckResult,
    QualityError,
    QualityScore,
)

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestQualityScore:
    """品質スコア値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-VALID_QUALITY_SCORE")
    def test_valid_quality_score(self) -> None:
        """有効な品質スコアが作成できる"""
        score = QualityScore(Decimal("85.5"))
        assert score.value == Decimal("85.5")
        assert score.to_float() == 85.5

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_SCORE_FROM_F")
    def test_quality_score_from_float(self) -> None:
        """floatから品質スコア作成"""
        score = QualityScore.from_float(92.3)
        assert score.to_float() == 92.3

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_SCORE_VALIDA")
    def test_quality_score_validation_too_low(self) -> None:
        """0未満のスコアは無効"""
        with pytest.raises(ValueError, match="Quality score must be between 0 and 100"):
            QualityScore(Decimal("-1"))

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_SCORE_VALIDA")
    def test_quality_score_validation_too_high(self) -> None:
        """100超のスコアは無効"""
        with pytest.raises(ValueError, match="Quality score must be between 0 and 100"):
            QualityScore(Decimal("101"))

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_SCORE_IS_PAS")
    def test_quality_score_is_passing(self) -> None:
        """合格基準チェック"""
        passing_score = QualityScore.from_float(85.0)
        failing_score = QualityScore.from_float(75.0)
        default_threshold = Decimal("80")

        assert passing_score.is_passing(default_threshold)
        assert not failing_score.is_passing(default_threshold)
        assert not failing_score.is_passing(Decimal("80"))


class TestCategoryScores:
    """カテゴリ別スコアのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-CATEGORY_SCORES_CREA")
    def test_category_scores_creation(self) -> None:
        """カテゴリ別スコア作成"""
        scores = CategoryScores(
            basic_style=QualityScore.from_float(90.0),
            composition=QualityScore.from_float(85.0),
            character_consistency=QualityScore.from_float(88.0),
            readability=QualityScore.from_float(82.0),
        )

        assert scores.basic_style.to_float() == 90.0
        assert scores.composition.to_float() == 85.0

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-OVERALL_SCORE_CALCUL")
    def test_overall_score_calculation(self) -> None:
        """総合スコア計算"""
        scores = CategoryScores(
            basic_style=QualityScore.from_float(90.0),
            composition=QualityScore.from_float(80.0),
            character_consistency=QualityScore.from_float(85.0),
            readability=QualityScore.from_float(85.0),
        )

        overall = scores.overall_score()
        expected = (90.0 + 80.0 + 85.0 + 85.0) / 4
        assert overall.to_float() == expected


class TestQualityError:
    """品質エラー値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-VALID_QUALITY_ERROR")
    def test_valid_quality_error(self) -> None:
        """有効な品質エラー作成"""
        error = QualityError(
            type="halfwidth_punctuation", message="半角記号の使用", line_number=42, severity="error", fixed=True
        )

        assert error.type == "halfwidth_punctuation"
        assert error.line_number == 42
        assert error.fixed is True

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_ERROR_VALIDA")
    def test_quality_error_validation_empty_type(self) -> None:
        """エラータイプが空の場合は無効"""
        with pytest.raises(ValueError, match="Error type cannot be empty"):
            QualityError(type="", message="テストメッセージ")

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_ERROR_VALIDA")
    def test_quality_error_validation_empty_message(self) -> None:
        """エラーメッセージが空の場合は無効"""
        with pytest.raises(ValueError, match="Error message cannot be empty"):
            QualityError(type="test_type", message="")

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_ERROR_VALIDA")
    def test_quality_error_validation_invalid_severity(self) -> None:
        """無効な重要度は拒否される"""
        with pytest.raises(ValueError, match="Invalid severity"):
            QualityError(type="test", message="test", severity="critical")

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_ERROR_VALIDA")
    def test_quality_error_validation_negative_line(self) -> None:
        """負の行番号は無効"""
        with pytest.raises(ValueError, match="Line number must be positive"):
            QualityError(type="test", message="test", line_number=-1)


class TestQualityCheckResult:
    """品質チェック結果値オブジェクトのテスト"""

    def create_sample_result(self, episode_number: int = 1) -> QualityCheckResult:
        """テスト用のサンプル結果作成"""
        return QualityCheckResult(
            episode_number=episode_number,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(90.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[
                QualityError(type="punctuation", message="記号エラー", line_number=10),
                QualityError(type="spacing", message="スペースエラー", line_number=20),
            ],
            warnings=[QualityError(type="style", message="スタイル警告", severity="warning")],
            auto_fixes=[AutoFix(type="punctuation_fix", description="記号修正", count=2)],
        )

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_CHECK_RESULT")
    def test_quality_check_result_creation(self) -> None:
        """品質チェック結果作成"""
        result = self.create_sample_result()

        assert result.episode_number == 1
        assert result.checker_version == "test_v1.0"
        assert result.error_count == 2
        assert result.warning_count == 1
        assert result.auto_fix_applied is True
        assert result.total_fixes_count == 2

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_CHECK_RESULT")
    def test_quality_check_result_validation_negative_episode(self) -> None:
        """負のエピソード番号は無効"""
        with pytest.raises(ValueError, match="Episode number must be positive"):
            QualityCheckResult(
                episode_number=-1,
                timestamp=project_now().datetime,
                checker_version="test",
                category_scores=CategoryScores(
                    basic_style=QualityScore.from_float(80.0),
                    composition=QualityScore.from_float(80.0),
                    character_consistency=QualityScore.from_float(80.0),
                    readability=QualityScore.from_float(80.0),
                ),
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_CHECK_RESULT")
    def test_quality_check_result_immutability(self) -> None:
        """品質チェック結果の不変性"""
        result = self.create_sample_result()

        # リストが不変になっていることを確認
        assert isinstance(result.errors, tuple)
        assert isinstance(result.warnings, tuple)
        assert isinstance(result.auto_fixes, tuple)

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-IS_HIGH_QUALITY")
    def test_is_high_quality(self) -> None:
        """高品質判定テスト"""
        high_quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(90.0),
                composition=QualityScore.from_float(90.0),
                character_consistency=QualityScore.from_float(90.0),
                readability=QualityScore.from_float(90.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        low_quality_result = QualityCheckResult(
            episode_number=2,
            timestamp=project_now().datetime,
            checker_version="test",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(70.0),
                composition=QualityScore.from_float(70.0),
                character_consistency=QualityScore.from_float(70.0),
                readability=QualityScore.from_float(70.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        threshold = Decimal("80")
        assert high_quality_result.is_high_quality(threshold)
        assert not low_quality_result.is_high_quality(threshold)

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-HAS_CRITICAL_ERRORS")
    def test_has_critical_errors(self) -> None:
        """重大エラー検出テスト"""
        result_with_errors = self.create_sample_result()

        result_without_errors = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(80.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(80.0),
                readability=QualityScore.from_float(80.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        assert result_with_errors.has_critical_errors()
        assert not result_without_errors.has_critical_errors()


class TestQualityRecord:
    """品質記録エンティティのテスト(ビジネスルール中心)"""

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_RECORD_CREAT")
    def test_quality_record_creation(self) -> None:
        """品質記録作成"""
        record = QualityRecord("  test_project \t")

        assert record.project_name == "test_project"
        assert record.entry_count == 0
        assert len(record.entries) == 0

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-QUALITY_RECORD_VALID")
    def test_quality_record_validation_empty_project_name(self) -> None:
        """空のプロジェクト名は無効"""
        with pytest.raises(QualityRecordError, match="Project name cannot be empty"):
            QualityRecord("")

        with pytest.raises(QualityRecordError, match="Project name cannot be empty"):
            QualityRecord("   ")

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-ADD_QUALITY_CHECK_RE")
    def test_add_quality_check_result(self) -> None:
        """品質チェック結果追加"""
        record = QualityRecord("test_project")

        result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        entry_id = record.add_quality_check_result(result)

        assert record.entry_count == 1
        assert entry_id is not None
        assert len(record.get_domain_events()) == 1

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-DUPLICATE_ENTRY_PREV")
    def test_duplicate_entry_prevention(self) -> None:
        """重複エントリ防止のビジネスルール"""
        record = QualityRecord("test_project")
        timestamp = project_now().datetime

        result1 = QualityCheckResult(
            episode_number=1,
            timestamp=timestamp,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        # 同じエピソード・同じ時刻の重複結果
        result2 = QualityCheckResult(
            episode_number=1,
            timestamp=timestamp,  # 同じタイムスタンプ
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(90.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(90.0),
                readability=QualityScore.from_float(87.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        # 最初の追加は成功
        record.add_quality_check_result(result1)

        # 重複追加は失敗
        with pytest.raises(QualityRecordError, match="Duplicate quality check"):
            record.add_quality_check_result(result2)

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-GET_LATEST_FOR_EPISO")
    def test_get_latest_for_episode(self) -> None:
        """指定エピソードの最新記録取得"""
        record = QualityRecord("test_project")

        # 異なる時刻で同じエピソードの結果を複数追加
        old_timestamp = project_now().datetime - timedelta(hours=1)
        new_timestamp = project_now().datetime

        old_result = QualityCheckResult(
            episode_number=1,
            timestamp=old_timestamp,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(80.0),
                composition=QualityScore.from_float(75.0),
                character_consistency=QualityScore.from_float(78.0),
                readability=QualityScore.from_float(72.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        new_result = QualityCheckResult(
            episode_number=1,
            timestamp=new_timestamp,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(90.0),
                composition=QualityScore.from_float(85.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        record.add_quality_check_result(old_result)
        record.add_quality_check_result(new_result)

        latest = record.get_latest_for_episode(1)
        assert latest is not None
        assert latest.quality_result.timestamp == new_timestamp

        # 存在しないエピソード
        assert record.get_latest_for_episode(999) is None

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-CALCULATE_AVERAGE_SC")
    def test_calculate_average_score(self) -> None:
        """平均品質スコア計算"""
        record = QualityRecord("test_project")

        # 空の場合
        assert record.calculate_average_score() is None

        # 複数結果追加
        for i, score in enumerate([80.0, 85.0, 90.0], 1):
            result = QualityCheckResult(
                episode_number=i,
                timestamp=project_now().datetime + timedelta(minutes=i),
                checker_version="test_v1.0",
                category_scores=CategoryScores(
                    basic_style=QualityScore.from_float(score),
                    composition=QualityScore.from_float(score),
                    character_consistency=QualityScore.from_float(score),
                    readability=QualityScore.from_float(score),
                ),
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

            record.add_quality_check_result(result)

        average = record.calculate_average_score()
        assert average is not None
        assert average.to_float() == 85.0  # (80+85+90)/3

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-GET_EPISODES_BELOW_T")
    def test_get_episodes_below_threshold(self) -> None:
        """閾値以下のエピソード取得"""
        record = QualityRecord("test_project")

        # 異なる品質スコアの結果を追加
        scores = [75.0, 85.0, 78.0, 92.0]  # 75, 78が80未満
        for i, score in enumerate(scores, 1):
            result = QualityCheckResult(
                episode_number=i,
                timestamp=project_now().datetime + timedelta(minutes=i),
                checker_version="test_v1.0",
                category_scores=CategoryScores(
                    basic_style=QualityScore.from_float(score),
                    composition=QualityScore.from_float(score),
                    character_consistency=QualityScore.from_float(score),
                    readability=QualityScore.from_float(score),
                ),
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

            record.add_quality_check_result(result)

        low_quality_episodes = record.get_episodes_below_threshold()
        assert low_quality_episodes == [1, 3]  # Episode 1(75.0, Episode 3(78.0)

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-PURGE_OLD_ENTRIES")
    def test_purge_old_entries(self) -> None:
        """古い記録のパージ"""
        record = QualityRecord("test_project")

        # 古い記録を作成
        old_timestamp = project_now().datetime - timedelta(days=40)
        recent_timestamp = project_now().datetime - timedelta(days=10)

        old_entry = QualityRecordEntry.create_from_result(
            QualityCheckResult(
                episode_number=1,
                timestamp=old_timestamp,
                checker_version="test_v1.0",
                category_scores=CategoryScores(
                    basic_style=QualityScore.from_float(80.0),
                    composition=QualityScore.from_float(80.0),
                    character_consistency=QualityScore.from_float(80.0),
                    readability=QualityScore.from_float(80.0),
                ),
                errors=[],
                warnings=[],
                auto_fixes=[],
            )
        )

        recent_entry = QualityRecordEntry.create_from_result(
            QualityCheckResult(
                episode_number=2,
                timestamp=recent_timestamp,
                checker_version="test_v1.0",
                category_scores=CategoryScores(
                    basic_style=QualityScore.from_float(85.0),
                    composition=QualityScore.from_float(85.0),
                    character_consistency=QualityScore.from_float(85.0),
                    readability=QualityScore.from_float(85.0),
                ),
                errors=[],
                warnings=[],
                auto_fixes=[],
            )
        )

        # エントリを手動で追加(created_atを制御するため)
        old_entry = QualityRecordEntry(
            id=old_entry.id,
            quality_result=old_entry.quality_result,
            created_at=old_timestamp,
            metadata=old_entry.metadata,
        )

        recent_entry = QualityRecordEntry(
            id=recent_entry.id,
            quality_result=recent_entry.quality_result,
            created_at=recent_timestamp,
            metadata=recent_entry.metadata,
        )

        record._entries.extend([old_entry, recent_entry])

        # 30日より古い記録をパージ
        purged_count = record.purge_old_entries(30)

        assert purged_count == 1
        assert record.entry_count == 1
        assert record.entries[0].quality_result.episode_number == 2

    @pytest.mark.spec("SPEC-QUALITY_RECORD_DOMAIN-DOMAIN_EVENTS")
    def test_domain_events(self) -> None:
        """ドメインイベントの記録・取得・クリア"""
        record = QualityRecord("test_project")

        result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="test_v1.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(88.0),
                readability=QualityScore.from_float(82.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        record.add_quality_check_result(result)

        events = record.get_domain_events()
        assert len(events) == 1
        assert events[0]["type"] == "QualityCheckAdded"
        assert events[0]["episode_number"] == 1

        record.clear_domain_events()
        assert len(record.get_domain_events()) == 0
