#!/usr/bin/env python3
"""QualityRecord エンティティのユニットテスト

仕様書: specs/quality_record_entity.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from noveler.domain.entities.quality_record import QualityRecord, QualityRecordEntry
from noveler.domain.exceptions import QualityRecordError
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_check_result import CategoryScores, QualityCheckResult, QualityScore

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestQualityRecordEntry:
    """QualityRecordEntryのテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY_RECORD-CREATE_FROM_RESULT_G")
    def test_create_from_result_generates_uuid_and_timestamp(self) -> None:
        """品質チェック結果からエントリ作成時にUUIDと現在時刻が設定されることを確認"""
        # Given
        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),
            checker_version="1.0.0",
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

        metadata = {"project": "test"}
        before_time = project_now().datetime

        # When
        entry = QualityRecordEntry.create_from_result(quality_result, metadata)

        # Then
        after_time = project_now().datetime
        assert entry.id is not None
        assert len(entry.id) == 36  # UUID format
        assert entry.quality_result == quality_result
        assert before_time <= entry.created_at <= after_time
        assert entry.metadata == metadata

    @pytest.mark.spec("SPEC-QUALITY_RECORD-CREATE_FROM_RESULT_W")
    def test_create_from_result_with_no_metadata(self) -> None:
        """メタデータなしでエントリ作成時に空辞書が設定されることを確認"""
        # Given
        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),
            checker_version="1.0.0",
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

        # When
        entry = QualityRecordEntry.create_from_result(quality_result)

        # Then
        assert entry.metadata == {}

    @pytest.mark.spec("SPEC-QUALITY_RECORD-POST_INIT_GENERATES_")
    def test_post_init_generates_id_if_empty(self) -> None:
        """初期化時にIDが空の場合は自動生成されることを確認"""
        # Given
        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="1.0.0",
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

        # When
        entry = QualityRecordEntry(
            id="",  # Empty ID
            quality_result=quality_result,
            created_at=project_now().datetime,
        )

        # Then
        assert entry.id is not None
        assert len(entry.id) == 36  # UUID format


class TestQualityRecord:
    """QualityRecordのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.project_name = "テスト小説"
        self.sample_result = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),
            checker_version="1.0.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(85.0),
                composition=QualityScore.from_float(80.0),
                character_consistency=QualityScore.from_float(85.0),
                readability=QualityScore.from_float(85.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

    @pytest.mark.spec("SPEC-QUALITY_RECORD-CONSTRUCTOR_WITH_VAL")
    def test_constructor_with_valid_project_name(self) -> None:
        """有効なプロジェクト名で正常に初期化されることを確認"""
        # When
        record = QualityRecord("テスト小説")

        # Then
        assert record.project_name == "テスト小説"
        assert record.entry_count == 0
        assert len(record.entries) == 0
        assert record.last_updated is not None

    @pytest.mark.spec("SPEC-QUALITY_RECORD-CONSTRUCTOR_WITH_EXI")
    def test_constructor_with_existing_entries(self) -> None:
        """既存のエントリありで初期化されることを確認"""
        # Given
        existing_entry = QualityRecordEntry.create_from_result(self.sample_result)
        entries = [existing_entry]

        # When
        record = QualityRecord("テスト小説", entries)

        # Then
        assert record.entry_count == 1
        assert len(record.entries) == 1
        assert record.entries[0].id == existing_entry.id

    @pytest.mark.spec("SPEC-QUALITY_RECORD-CONSTRUCTOR_TRIMS_PR")
    def test_constructor_trims_project_name(self) -> None:
        """プロジェクト名が自動的にトリムされることを確認"""
        # When
        record = QualityRecord("  テスト小説  ")

        # Then
        assert record.project_name == "テスト小説"

    @pytest.mark.spec("SPEC-QUALITY_RECORD-CONSTRUCTOR_WITH_EMP")
    def test_constructor_with_empty_project_name_raises_error(self) -> None:
        """空のプロジェクト名でエラーが発生することを確認"""
        # When & Then
        with pytest.raises(QualityRecordError) as exc_info:
            QualityRecord("")
        assert "Project name cannot be empty" in str(exc_info.value)

        with pytest.raises(QualityRecordError) as exc_info:
            QualityRecord("   ")
        assert "Project name cannot be empty" in str(exc_info.value)

    @pytest.mark.spec("SPEC-QUALITY_RECORD-ENTRIES_PROPERTY_RET")
    def test_entries_property_returns_copy(self) -> None:
        """entriesプロパティが不変性を保証することを確認"""
        # Given
        record = QualityRecord("テスト小説")
        original_entries = record.entries

        # When
        returned_entries = record.entries
        returned_entries.append("fake_entry")

        # Then
        assert record.entries == original_entries
        assert len(record.entries) == 0

    @pytest.mark.spec("SPEC-QUALITY_RECORD-ADD_QUALITY_CHECK_RE")
    def test_add_quality_check_result_success(self) -> None:
        """品質チェック結果の正常追加を確認"""
        # Given
        record = QualityRecord("テスト小説")
        metadata = {"version": "1.0"}
        before_time = project_now().datetime

        # When
        entry_id = record.add_quality_check_result(self.sample_result, metadata)

        # Then
        after_time = project_now().datetime
        assert entry_id is not None
        assert record.entry_count == 1
        assert before_time <= record.last_updated <= after_time

        # ドメインイベント確認
        events = record.get_domain_events()
        assert len(events) == 1
        event = events[0]
        assert event["type"] == "QualityCheckAdded"
        assert event["entry_id"] == entry_id
        assert event["episode_number"] == 1
        assert event["score"] == 83.75  # (85.0 + 80.0 + 85.0 + 85.0) / 4

    @pytest.mark.spec("SPEC-QUALITY_RECORD-ADD_QUALITY_CHECK_RE")
    def test_add_quality_check_result_duplicate_prevention(self) -> None:
        """重複エントリの防止を確認"""
        # Given
        record = QualityRecord("テスト小説")
        record.add_quality_check_result(self.sample_result)

        # 同じエピソード・同じ時刻の結果を作成
        duplicate_result = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 10, 0, 30, tzinfo=JST),  # 30秒後(60秒以内)
            checker_version="1.0.0",
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

        # When & Then
        with pytest.raises(QualityRecordError) as exc_info:
            record.add_quality_check_result(duplicate_result)
        assert "Duplicate quality check for episode 1" in str(exc_info.value)

    @pytest.mark.spec("SPEC-QUALITY_RECORD-ADD_QUALITY_CHECK_RE")
    def test_add_quality_check_result_different_time_allowed(self) -> None:
        """異なる時刻の同一エピソードは追加可能であることを確認"""
        # Given
        record = QualityRecord("テスト小説")
        record.add_quality_check_result(self.sample_result)

        different_time_result = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 10, 2, 0, tzinfo=JST),  # 2分後(60秒超)
            checker_version="1.0.0",
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

        # When
        entry_id = record.add_quality_check_result(different_time_result)

        # Then
        assert entry_id is not None
        assert record.entry_count == 2

    @pytest.mark.spec("SPEC-QUALITY_RECORD-GET_LATEST_FOR_EPISO")
    def test_get_latest_for_episode_existing(self) -> None:
        """指定エピソードの最新記録取得を確認"""
        # Given
        record = QualityRecord("テスト小説")

        # 異なる時刻で2つの結果を追加
        older_result = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 9, 0, 0, tzinfo=JST),
            checker_version="1.0.0",
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

        newer_result = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),
            checker_version="1.0.0",
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

        record.add_quality_check_result(older_result)
        record.add_quality_check_result(newer_result)

        # When
        latest_entry = record.get_latest_for_episode(1)

        # Then
        assert latest_entry is not None
        assert latest_entry.quality_result.overall_score.to_float() == 85.0
        assert latest_entry.quality_result.timestamp == datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST)

    @pytest.mark.spec("SPEC-QUALITY_RECORD-GET_LATEST_FOR_EPISO")
    def test_get_latest_for_episode_not_existing(self) -> None:
        """存在しないエピソードの場合にNoneが返されることを確認"""
        # Given
        record = QualityRecord("テスト小説")
        record.add_quality_check_result(self.sample_result)

        # When
        latest_entry = record.get_latest_for_episode(999)

        # Then
        assert latest_entry is None

    @pytest.mark.spec("SPEC-QUALITY_RECORD-GET_QUALITY_TREND_WI")
    def test_get_quality_trend_with_limit(self) -> None:
        """品質トレンドが制限件数で取得されることを確認"""
        # Given
        record = QualityRecord("テスト小説")

        # 複数の記録を時系列で追加
        for i, score in enumerate([80.0, 85.0, 82.0, 88.0, 90.0], 1):
            result = QualityCheckResult(
                episode_number=1,
                timestamp=datetime(2025, 1, 1, 9 + i, 0, 0),
                checker_version="1.0.0",
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

        # When
        trend = record.get_quality_trend(1, limit=3)

        # Then
        assert len(trend) == 3
        # 新しい順(最後の3件): 82.0, 88.0, 90.0
        assert [score.to_float() for score in trend] == [82.0, 88.0, 90.0]

    @pytest.mark.spec("SPEC-QUALITY_RECORD-GET_QUALITY_TREND_NO")
    def test_get_quality_trend_no_entries(self) -> None:
        """エントリがない場合は空リストが返されることを確認"""
        # Given
        record = QualityRecord("テスト小説")

        # When
        trend = record.get_quality_trend(1)

        # Then
        assert trend == []

    @pytest.mark.spec("SPEC-QUALITY_RECORD-CALCULATE_AVERAGE_SC")
    def test_calculate_average_score_with_entries(self) -> None:
        """エントリがある場合の平均スコア計算を確認"""
        # Given
        record = QualityRecord("テスト小説")

        # 複数のエピソードの記録を追加
        scores = [80.0, 85.0, 90.0]
        for i, score in enumerate(scores, 1):
            result = QualityCheckResult(
                episode_number=i,
                timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),
                checker_version="1.0.0",
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

        # When
        average_score = record.calculate_average_score()

        # Then
        assert average_score is not None
        expected_average = sum(scores) / len(scores)  # 85.0
        assert average_score.to_float() == expected_average

    @pytest.mark.spec("SPEC-QUALITY_RECORD-CALCULATE_AVERAGE_SC")
    def test_calculate_average_score_no_entries(self) -> None:
        """エントリがない場合はNoneが返されることを確認"""
        # Given
        record = QualityRecord("テスト小説")

        # When
        average_score = record.calculate_average_score()

        # Then
        assert average_score is None

    @pytest.mark.spec("SPEC-QUALITY_RECORD-GET_EPISODES_BELOW_T")
    def test_get_episodes_below_threshold_with_default(self) -> None:
        """デフォルト閾値(80.0)以下のエピソード取得を確認"""
        # Given
        record = QualityRecord("テスト小説")

        # 異なるスコアの記録を追加
        test_data = [(1, 75.0), (2, 85.0), (3, 78.0), (4, 82.0)]
        for episode_num, score in test_data:
            result = QualityCheckResult(
                episode_number=episode_num,
                timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),
                checker_version="1.0.0",
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

        # When
        below_threshold = record.get_episodes_below_threshold()

        # Then
        # 80.0以下は episode 1 (75.0) と episode 3 (78.0)
        assert below_threshold == [1, 3]

    @pytest.mark.spec("SPEC-QUALITY_RECORD-GET_EPISODES_BELOW_T")
    def test_get_episodes_below_threshold_with_custom(self) -> None:
        """カスタム閾値以下のエピソード取得を確認"""
        # Given
        record = QualityRecord("テスト小説")
        custom_threshold = QualityScore.from_float(85.0)

        # 異なるスコアの記録を追加
        test_data = [(1, 75.0), (2, 85.0), (3, 88.0), (4, 82.0)]
        for episode_num, score in test_data:
            result = QualityCheckResult(
                episode_number=episode_num,
                timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),
                checker_version="1.0.0",
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

        # When
        below_threshold = record.get_episodes_below_threshold(custom_threshold)

        # Then
        # 85.0未満は episode 1 (75.0) と episode 4 (82.0)
        assert below_threshold == [1, 4]

    @pytest.mark.spec("SPEC-QUALITY_RECORD-GET_EPISODES_BELOW_T")
    def test_get_episodes_below_threshold_deduplication(self) -> None:
        """重複するエピソード番号が重複排除されることを確認"""
        # Given
        record = QualityRecord("テスト小説")

        # 同じエピソードで複数の記録(異なる時刻)
        result1 = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 9, 0, 0, tzinfo=JST),
            checker_version="1.0.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(75.0),
                composition=QualityScore.from_float(75.0),
                character_consistency=QualityScore.from_float(75.0),
                readability=QualityScore.from_float(75.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        result2 = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),
            checker_version="1.0.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(78.0),
                composition=QualityScore.from_float(78.0),
                character_consistency=QualityScore.from_float(78.0),
                readability=QualityScore.from_float(78.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        record.add_quality_check_result(result1)
        record.add_quality_check_result(result2)

        # When
        below_threshold = record.get_episodes_below_threshold()

        # Then
        # 重複排除されて episode 1 が1つだけ
        assert below_threshold == [1]

    @patch("domain.entities.quality_record.datetime")
    def test_purge_old_entries_success(self, mock_datetime_class: object) -> None:
        """古い記録のパージが正常に動作することを確認"""
        # Given
        fixed_now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=JST)
        mock_datetime_class.now.return_value = fixed_now

        record = QualityRecord("テスト小説")

        # 新しい記録と古い記録を追加(異なる品質結果を使用)
        old_result = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 9, 0, 0, tzinfo=JST),
            checker_version="1.0.0",
            category_scores=CategoryScores(
                basic_style=QualityScore.from_float(75.0),
                composition=QualityScore.from_float(75.0),
                character_consistency=QualityScore.from_float(75.0),
                readability=QualityScore.from_float(75.0),
            ),
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        recent_result = QualityCheckResult(
            episode_number=2,
            timestamp=datetime(2025, 1, 10, 10, 0, 0, tzinfo=JST),
            checker_version="1.0.0",
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

        old_entry = QualityRecordEntry(
            id=str(uuid4()),
            quality_result=old_result,
            created_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),  # 14日前
        )
        recent_entry = QualityRecordEntry(
            id=str(uuid4()),
            quality_result=recent_result,
            created_at=datetime(2025, 1, 10, 10, 0, 0, tzinfo=JST),  # 5日前
        )

        record._entries = [old_entry, recent_entry]

        # When
        purged_count = record.purge_old_entries(days_to_keep=7)

        # Then
        assert purged_count == 1  # 古い記録1件がパージされる
        assert record.entry_count == 1
        assert record.entries[0].id == recent_entry.id

        # ドメインイベント確認
        events = record.get_domain_events()
        assert len(events) == 1
        assert events[0]["type"] == "OldEntriesPurged"
        assert events[0]["purged_count"] == 1

    @pytest.mark.spec("SPEC-QUALITY_RECORD-PURGE_OLD_ENTRIES_IN")
    def test_purge_old_entries_invalid_days(self) -> None:
        """保持期間が無効な場合にエラーが発生することを確認"""
        # Given
        record = QualityRecord("テスト小説")

        # When & Then
        with pytest.raises(QualityRecordError) as exc_info:
            record.purge_old_entries(0)
        assert "Days to keep must be positive" in str(exc_info.value)

        with pytest.raises(QualityRecordError) as exc_info:
            record.purge_old_entries(-1)
        assert "Days to keep must be positive" in str(exc_info.value)

    @pytest.mark.spec("SPEC-QUALITY_RECORD-PURGE_OLD_ENTRIES_NO")
    def test_purge_old_entries_no_old_entries(self) -> None:
        """古い記録がない場合はパージされないことを確認"""
        # Given
        record = QualityRecord("テスト小説")
        record.add_quality_check_result(self.sample_result)

        # When
        purged_count = record.purge_old_entries(days_to_keep=30)

        # Then
        assert purged_count == 0
        assert record.entry_count == 1

    @pytest.mark.spec("SPEC-QUALITY_RECORD-DOMAIN_EVENTS_MANAGE")
    def test_domain_events_management(self) -> None:
        """ドメインイベントの管理が正しく動作することを確認"""
        # Given
        record = QualityRecord("テスト小説")

        # When
        record.add_quality_check_result(self.sample_result)
        events_before_clear = record.get_domain_events()

        record.clear_domain_events()
        events_after_clear = record.get_domain_events()

        # Then
        assert len(events_before_clear) == 1
        assert len(events_after_clear) == 0

    @pytest.mark.spec("SPEC-QUALITY_RECORD-TO_PERSISTENCE_DICT_")
    def test_to_persistence_dict_structure(self) -> None:
        """永続化辞書の構造が正しいことを確認"""
        # Given
        record = QualityRecord("テスト小説")
        record.add_quality_check_result(self.sample_result, {"test": "metadata"})

        # When
        persistence_dict = record.to_persistence_dict()

        # Then
        assert "metadata" in persistence_dict
        assert "quality_checks" in persistence_dict

        metadata = persistence_dict["metadata"]
        assert metadata["project_name"] == "テスト小説"
        assert metadata["entry_count"] == 1
        assert "last_updated" in metadata

        quality_checks = persistence_dict["quality_checks"]
        assert len(quality_checks) == 1

        check = quality_checks[0]
        assert "id" in check
        assert check["episode_number"] == 1
        assert check["checker_version"] == "1.0.0"
        assert check["metadata"] == {"test": "metadata"}
        assert "timestamp" in check
        assert "created_at" in check
        assert "results" in check
