#!/usr/bin/env python3
"""LearningSession エンティティのユニットテスト

仕様書: specs/learning_session_entity.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

from datetime import datetime, timedelta

import pytest
pytestmark = pytest.mark.quality_domain

from noveler.domain.entities.learning_session import LearningSession
from noveler.domain.exceptions import BusinessRuleViolationError
from noveler.domain.value_objects.learning_metrics import LearningMetrics
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestLearningSession:
    """LearningSessionのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.start_time = datetime(2025, 1, 22, 10, 0, 0, tzinfo=JST)
        self.project_name = "テストプロジェクト"
        self.episode_number = 1

    # ===== 1. 初期化と検証テスト =====

    @pytest.mark.spec("SPEC-LEARNING_SESSION-VALID_INITIALIZATION")
    def test_valid_initialization(self) -> None:
        """TEST-1: 必須パラメータでの正常初期化"""
        # Given & When
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        # Then
        assert session.project_name == self.project_name
        assert session.episode_number == self.episode_number
        assert session.start_time == self.start_time
        # デフォルト値の確認
        assert session.writing_environment is None
        assert session.target_audience is None
        assert session.writing_goal is None
        assert session.end_time is None
        assert session.total_writing_time == 0
        assert session.is_completed is False

    @pytest.mark.spec("SPEC-LEARNING_SESSION-INITIALIZATION_WITH_")
    def test_initialization_with_all_parameters(self) -> None:
        """TEST-2: 全パラメータ指定での初期化"""
        # Given
        writing_environment = "静かなカフェ"
        target_audience = "10代読者"
        writing_goal = "感動的なクライマックス"

        # When
        session = LearningSession(
            project_name=self.project_name,
            episode_number=self.episode_number,
            start_time=self.start_time,
            writing_environment=writing_environment,
            target_audience=target_audience,
            writing_goal=writing_goal,
        )

        # Then
        assert session.writing_environment == writing_environment
        assert session.target_audience == target_audience
        assert session.writing_goal == writing_goal

    @pytest.mark.spec("SPEC-LEARNING_SESSION-EMPTY_PROJECT_NAME_R")
    def test_empty_project_name_raises_error(self) -> None:
        """TEST-3: 空文字列でBusinessRuleViolationError"""
        # When & Then
        with pytest.raises(BusinessRuleViolationError, match="プロジェクト名は必須です"):
            LearningSession(project_name="", episode_number=self.episode_number, start_time=self.start_time)

    @pytest.mark.spec("SPEC-LEARNING_SESSION-WHITESPACE_PROJECT_N")
    def test_whitespace_project_name_raises_error(self) -> None:
        """TEST-4: 空白文字のみでBusinessRuleViolationError"""
        # When & Then
        with pytest.raises(BusinessRuleViolationError, match="プロジェクト名は必須です"):
            LearningSession(project_name="   \t\n  ", episode_number=self.episode_number, start_time=self.start_time)

    @pytest.mark.spec("SPEC-LEARNING_SESSION-VALID_PROJECT_NAME_A")
    def test_valid_project_name_accepted(self) -> None:
        """TEST-5: 有効なプロジェクト名での成功"""
        # Given
        valid_names = ["プロジェクト", "My Novel Project", "小説 - 第1部", "異世界転生もの123", "  前後の空白は許可  "]

        # When & Then
        for name in valid_names:
            session = LearningSession(project_name=name, episode_number=self.episode_number, start_time=self.start_time)
            assert session.project_name == name

    @pytest.mark.spec("SPEC-LEARNING_SESSION-ZERO_EPISODE_NUMBER_")
    def test_zero_episode_number_raises_error(self) -> None:
        """TEST-6: エピソード番号0でBusinessRuleViolationError"""
        # When & Then
        with pytest.raises(BusinessRuleViolationError, match="エピソード番号は1以上の正の整数である必要があります"):
            LearningSession(project_name=self.project_name, episode_number=0, start_time=self.start_time)

    @pytest.mark.spec("SPEC-LEARNING_SESSION-NEGATIVE_EPISODE_NUM")
    def test_negative_episode_number_raises_error(self) -> None:
        """TEST-7: 負の番号でBusinessRuleViolationError"""
        # When & Then
        with pytest.raises(BusinessRuleViolationError, match="エピソード番号は1以上の正の整数である必要があります"):
            LearningSession(project_name=self.project_name, episode_number=-1, start_time=self.start_time)

    @pytest.mark.spec("SPEC-LEARNING_SESSION-POSITIVE_EPISODE_NUM")
    def test_positive_episode_number_accepted(self) -> None:
        """TEST-8: 正の整数での成功"""
        # Given
        valid_numbers = [1, 2, 100, 999]

        # When & Then
        for number in valid_numbers:
            session = LearningSession(project_name=self.project_name, episode_number=number, start_time=self.start_time)
            assert session.episode_number == number

    @pytest.mark.spec("SPEC-LEARNING_SESSION-NONE_START_TIME_RAIS")
    def test_none_start_time_raises_error(self) -> None:
        """TEST-9: start_time=NoneでBusinessRuleViolationError"""
        # When & Then
        with pytest.raises(BusinessRuleViolationError, match="開始時刻は必須です"):
            LearningSession(project_name=self.project_name, episode_number=self.episode_number, start_time=None)

    # ===== 2. セッション完了テスト =====

    @pytest.mark.spec("SPEC-LEARNING_SESSION-COMPLETE_SESSION_WIT")
    def test_complete_session_with_end_time(self) -> None:
        """TEST-10: 明示的終了時刻での完了"""
        # Given
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        end_time = self.start_time + timedelta(minutes=90)

        # When
        session.complete(end_time)

        # Then
        assert session.is_completed is True
        assert session.end_time == end_time
        assert session.total_writing_time == 90  # 90分

    @pytest.mark.spec("SPEC-LEARNING_SESSION-COMPLETE_SESSION_WIT")
    def test_complete_session_without_end_time(self) -> None:
        """TEST-11: 現在時刻での自動完了"""
        # Given
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        before_complete = project_now().datetime

        # When
        session.complete()

        # Then
        after_complete = project_now().datetime
        assert session.is_completed is True
        assert before_complete <= session.end_time <= after_complete
        assert session.total_writing_time >= 0

    @pytest.mark.spec("SPEC-LEARNING_SESSION-COMPLETE_ALREADY_COM")
    def test_complete_already_completed_session_raises_error(self) -> None:
        """TEST-12: 既完了セッションの再完了でエラー"""
        # Given
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        session.complete()

        # When & Then
        with pytest.raises(BusinessRuleViolationError, match="既に完了したセッションです"):
            session.complete()

    @pytest.mark.spec("SPEC-LEARNING_SESSION-COMPLETION_FLAGS_SET")
    def test_completion_flags_set_correctly(self) -> None:
        """TEST-13: is_completed = True の設定確認"""
        # Given
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        # 初期状態確認
        assert session.is_completed is False

        # When
        session.complete()

        # Then
        assert session.is_completed is True

    @pytest.mark.spec("SPEC-LEARNING_SESSION-END_TIME_BEFORE_STAR")
    def test_end_time_before_start_time_raises_error(self) -> None:
        """TEST-14: 終了時刻 < 開始時刻でBusinessRuleViolationError"""
        # Given
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        end_time = self.start_time - timedelta(minutes=30)  # 30分前

        # When & Then
        with pytest.raises(BusinessRuleViolationError, match="終了時刻は開始時刻より後である必要があります"):
            session.complete(end_time)

    @pytest.mark.spec("SPEC-LEARNING_SESSION-END_TIME_EQUALS_STAR")
    def test_end_time_equals_start_time_accepted(self) -> None:
        """TEST-15: 終了時刻 = 開始時刻での成功(0分セッション)"""
        # Given
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        # When
        session.complete(self.start_time)

        # Then
        assert session.is_completed is True
        assert session.end_time == self.start_time
        assert session.total_writing_time == 0

    @pytest.mark.spec("SPEC-LEARNING_SESSION-WRITING_TIME_CALCULA")
    def test_writing_time_calculation_accuracy(self) -> None:
        """TEST-16: 分単位計算の正確性(秒は切り捨て)"""
        # Given
        LearningSession(project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time)

        # Case 1: 正確に90分
        end_time_90min = self.start_time + timedelta(minutes=90)
        session_copy1 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session_copy1.complete(end_time_90min)
        assert session_copy1.total_writing_time == 90

        # Case 2: 90分30秒 → 90分(切り捨て)
        end_time_90min30sec = self.start_time + timedelta(minutes=90, seconds=30)
        session_copy2 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session_copy2.complete(end_time_90min30sec)
        assert session_copy2.total_writing_time == 90

        # Case 3: 90分59秒 → 90分(切り捨て)
        end_time_90min59sec = self.start_time + timedelta(minutes=90, seconds=59)
        session_copy3 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session_copy3.complete(end_time_90min59sec)
        assert session_copy3.total_writing_time == 90

    @pytest.mark.spec("SPEC-LEARNING_SESSION-VARIOUS_DURATION_CAL")
    def test_various_duration_calculations(self) -> None:
        """TEST-17: 様々な時間間隔での計算確認"""
        # Given
        test_cases = [
            (timedelta(minutes=1), 1),
            (timedelta(minutes=30), 30),
            (timedelta(hours=2), 120),
            (timedelta(hours=1, minutes=15), 75),
            (timedelta(days=1), 1440),  # 24時間
        ]

        # When & Then
        for duration, expected_minutes in test_cases:
            session = LearningSession(
                project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
            )

            session.complete(self.start_time + duration)
            assert session.total_writing_time == expected_minutes

    # ===== 3. セッション継続時間テスト =====

    @pytest.mark.spec("SPEC-LEARNING_SESSION-GET_SESSION_DURATION")
    def test_get_session_duration_incomplete_session(self) -> None:
        """TEST-18: 未完了セッションで0を返却"""
        # Given
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        # When
        duration = session.get_session_duration()

        # Then
        assert duration == 0

    @pytest.mark.spec("SPEC-LEARNING_SESSION-GET_SESSION_DURATION")
    def test_get_session_duration_completed_session(self) -> None:
        """TEST-19: 完了セッションで正確な時間を返却"""
        # Given
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        session.complete(self.start_time + timedelta(minutes=60))

        # When
        duration = session.get_session_duration()

        # Then
        assert duration == 60

    # ===== 4. コンテキスト取得テスト =====

    @pytest.mark.spec("SPEC-LEARNING_SESSION-GET_SESSION_CONTEXT_")
    def test_get_session_context_incomplete_session(self) -> None:
        """TEST-20: 未完了セッションのコンテキスト"""
        # Given
        session = LearningSession(
            project_name=self.project_name,
            episode_number=self.episode_number,
            start_time=self.start_time,
            writing_environment="自宅書斎",
        )

        # When
        context = session.get_session_context()

        # Then
        assert context["project_name"] == self.project_name
        assert context["episode_number"] == self.episode_number
        assert context["writing_environment"] == "自宅書斎"
        assert context["target_audience"] is None
        assert context["writing_goal"] is None
        assert context["start_time"] == self.start_time.isoformat()
        assert context["end_time"] is None
        assert context["total_writing_time"] == 0
        assert context["is_completed"] is False

    @pytest.mark.spec("SPEC-LEARNING_SESSION-GET_SESSION_CONTEXT_")
    def test_get_session_context_completed_session(self) -> None:
        """TEST-21: 完了セッションのコンテキスト"""
        # Given
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        end_time = self.start_time + timedelta(minutes=45)
        session.complete(end_time)

        # When
        context = session.get_session_context()

        # Then
        assert context["end_time"] == end_time.isoformat()
        assert context["total_writing_time"] == 45
        assert context["is_completed"] is True

    @pytest.mark.spec("SPEC-LEARNING_SESSION-SESSION_CONTEXT_INCL")
    def test_session_context_includes_all_fields(self) -> None:
        """TEST-22: 全フィールドの含有確認"""
        # Given
        session = LearningSession(
            project_name="完全テスト",
            episode_number=5,
            start_time=self.start_time,
            writing_environment="図書館",
            target_audience="大学生",
            writing_goal="謎解きシーン",
        )

        # When
        context = session.get_session_context()

        # Then
        required_fields = [
            "project_name",
            "episode_number",
            "writing_environment",
            "target_audience",
            "writing_goal",
            "start_time",
            "end_time",
            "total_writing_time",
            "is_completed",
        ]
        for field in required_fields:
            assert field in context

    # ===== 5. 学習メトリクス生成テスト =====

    @pytest.mark.spec("SPEC-LEARNING_SESSION-CREATE_LEARNING_METR")
    def test_create_learning_metrics_incomplete_session_raises_error(self) -> None:
        """TEST-23: 未完了セッションでBusinessRuleViolationError"""
        # Given
        session = LearningSession(
            project_name=self.project_name, episode_number=self.episode_number, start_time=self.start_time
        )

        # When & Then
        with pytest.raises(BusinessRuleViolationError, match="セッションが完了していません"):
            session.create_learning_metrics(improvement_from_previous=5.0, revision_count=3)

    @pytest.mark.spec("SPEC-LEARNING_SESSION-CREATE_LEARNING_METR")
    def test_create_learning_metrics_completed_session(self) -> None:
        """TEST-24: 完了セッションでの正常生成"""
        # Given
        session = LearningSession(
            project_name=self.project_name,
            episode_number=self.episode_number,
            start_time=self.start_time,
            writing_environment="カフェ",
        )

        session.complete(self.start_time + timedelta(minutes=60))

        # When
        metrics = session.create_learning_metrics(
            improvement_from_previous=8.5, revision_count=2, user_feedback="良い進歩"
        )

        # Then
        assert isinstance(metrics, LearningMetrics)
        assert metrics.improvement_from_previous == 8.5
        assert metrics.time_spent_writing == 60
        assert metrics.revision_count == 2
        assert metrics.user_feedback == "良い進歩"
        assert metrics.writing_context == "カフェ"

    @pytest.mark.spec("SPEC-LEARNING_SESSION-LEARNING_METRICS_DAT")
    def test_learning_metrics_data_accuracy(self) -> None:
        """TEST-25: メトリクス内のデータ正確性"""
        # Given
        session = LearningSession(
            project_name=self.project_name,
            episode_number=self.episode_number,
            start_time=self.start_time,
            writing_environment="静寂な部屋",
        )

        session.complete(self.start_time + timedelta(minutes=90))

        # When
        metrics = session.create_learning_metrics(improvement_from_previous=15.0, revision_count=4)

        # Then
        assert metrics.improvement_from_previous == 15.0
        assert metrics.time_spent_writing == 90  # セッションの総時間と一致
        assert metrics.revision_count == 4
        assert metrics.user_feedback is None
        assert metrics.writing_context == "静寂な部屋"  # writing_environmentが伝播

    # ===== 6. 生産性分析テスト =====

    @pytest.mark.spec("SPEC-LEARNING_SESSION-IS_LONG_SESSION_DEFA")
    def test_is_long_session_default_threshold(self) -> None:
        """TEST-26: デフォルト閾値(120分)での判定"""
        # Given
        session = LearningSession(self.project_name, self.episode_number, self.start_time)

        # Case 1: 120分ちょうど → True
        session.complete(self.start_time + timedelta(minutes=120))
        assert session.is_long_session() is True

        # Case 2: 119分 → False
        session2 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session2.complete(self.start_time + timedelta(minutes=119))
        assert session2.is_long_session() is False

        # Case 3: 121分 → True
        session3 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session3.complete(self.start_time + timedelta(minutes=121))
        assert session3.is_long_session() is True

    @pytest.mark.spec("SPEC-LEARNING_SESSION-IS_LONG_SESSION_CUST")
    def test_is_long_session_custom_threshold(self) -> None:
        """TEST-27: カスタム閾値での判定"""
        # Given
        session = LearningSession(self.project_name, self.episode_number, self.start_time)
        session.complete(self.start_time + timedelta(minutes=90))

        # When & Then
        assert session.is_long_session(threshold_minutes=90) is True
        assert session.is_long_session(threshold_minutes=91) is False
        assert session.is_long_session(threshold_minutes=60) is True

    @pytest.mark.spec("SPEC-LEARNING_SESSION-IS_SHORT_SESSION_DEF")
    def test_is_short_session_default_threshold(self) -> None:
        """TEST-28: デフォルト閾値(30分)での判定"""
        # Given
        session = LearningSession(self.project_name, self.episode_number, self.start_time)

        # Case 1: 30分ちょうど → True
        session.complete(self.start_time + timedelta(minutes=30))
        assert session.is_short_session() is True

        # Case 2: 29分 → True
        session2 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session2.complete(self.start_time + timedelta(minutes=29))
        assert session2.is_short_session() is True

        # Case 3: 31分 → False
        session3 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session3.complete(self.start_time + timedelta(minutes=31))
        assert session3.is_short_session() is False

    @pytest.mark.spec("SPEC-LEARNING_SESSION-IS_SHORT_SESSION_CUS")
    def test_is_short_session_custom_threshold(self) -> None:
        """TEST-29: カスタム閾値での判定"""
        # Given
        session = LearningSession(self.project_name, self.episode_number, self.start_time)
        session.complete(self.start_time + timedelta(minutes=45))

        # When & Then
        assert session.is_short_session(threshold_minutes=45) is True
        assert session.is_short_session(threshold_minutes=44) is False
        assert session.is_short_session(threshold_minutes=60) is True

    @pytest.mark.spec("SPEC-LEARNING_SESSION-PRODUCTIVITY_LEVEL_H")
    def test_productivity_level_high(self) -> None:
        """TEST-30: 高生産性(≥120分)の判定"""
        # Given
        session = LearningSession(self.project_name, self.episode_number, self.start_time)
        session.complete(self.start_time + timedelta(minutes=150))

        # When
        level = session.get_productivity_level()

        # Then
        assert level == "高生産性"

    @pytest.mark.spec("SPEC-LEARNING_SESSION-PRODUCTIVITY_LEVEL_L")
    def test_productivity_level_low(self) -> None:
        """TEST-31: 低生産性(≤30分)の判定"""
        # Given
        session = LearningSession(self.project_name, self.episode_number, self.start_time)
        session.complete(self.start_time + timedelta(minutes=25))

        # When
        level = session.get_productivity_level()

        # Then
        assert level == "低生産性"

    @pytest.mark.spec("SPEC-LEARNING_SESSION-PRODUCTIVITY_LEVEL_S")
    def test_productivity_level_standard(self) -> None:
        """TEST-32: 標準生産性(31-119分)の判定"""
        # Given
        test_cases = [31, 60, 90, 119]

        # When & Then
        for minutes in test_cases:
            session = LearningSession(self.project_name, self.episode_number, self.start_time)
            session.complete(self.start_time + timedelta(minutes=minutes))
            level = session.get_productivity_level()
            assert level == "標準生産性", f"{minutes}分で標準生産性のはずが{level}"

    # ===== 7. エッジケーステスト =====

    @pytest.mark.spec("SPEC-LEARNING_SESSION-BOUNDARY_VALUES_FOR_")
    def test_boundary_values_for_productivity(self) -> None:
        """TEST-33: 生産性判定の境界値(30分、120分)"""
        # Case 1: 30分(低生産性境界)
        session30 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session30.complete(self.start_time + timedelta(minutes=30))
        assert session30.get_productivity_level() == "低生産性"
        assert session30.is_short_session() is True
        assert session30.is_long_session() is False

        # Case 2: 31分(標準生産性開始)
        session31 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session31.complete(self.start_time + timedelta(minutes=31))
        assert session31.get_productivity_level() == "標準生産性"
        assert session31.is_short_session() is False
        assert session31.is_long_session() is False

        # Case 3: 119分(標準生産性終了)
        session119 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session119.complete(self.start_time + timedelta(minutes=119))
        assert session119.get_productivity_level() == "標準生産性"
        assert session119.is_short_session() is False
        assert session119.is_long_session() is False

        # Case 4: 120分(高生産性境界)
        session120 = LearningSession(self.project_name, self.episode_number, self.start_time)
        session120.complete(self.start_time + timedelta(minutes=120))
        assert session120.get_productivity_level() == "高生産性"
        assert session120.is_short_session() is False
        assert session120.is_long_session() is True

    @pytest.mark.spec("SPEC-LEARNING_SESSION-ZERO_DURATION_SESSIO")
    def test_zero_duration_session(self) -> None:
        """TEST-34: 0分セッションの処理"""
        # Given
        session = LearningSession(self.project_name, self.episode_number, self.start_time)
        session.complete(self.start_time)  # 同じ時刻で完了

        # When & Then
        assert session.total_writing_time == 0
        assert session.get_session_duration() == 0
        assert session.get_productivity_level() == "低生産性"
        assert session.is_short_session() is True
        assert session.is_long_session() is False

    @pytest.mark.spec("SPEC-LEARNING_SESSION-VERY_LONG_SESSION")
    def test_very_long_session(self) -> None:
        """TEST-35: 極長時間セッション(24時間超)の処理"""
        # Given
        session = LearningSession(self.project_name, self.episode_number, self.start_time)
        end_time = self.start_time + timedelta(hours=25)  # 25時間後
        session.complete(end_time)

        # When & Then
        assert session.total_writing_time == 1500  # 25 * 60 = 1500分
        assert session.get_productivity_level() == "高生産性"
        assert session.is_long_session() is True
        assert session.is_short_session() is False

    @pytest.mark.spec("SPEC-LEARNING_SESSION-MICROSECOND_PRECISIO")
    def test_microsecond_precision_handling(self) -> None:
        """TEST-36: マイクロ秒精度の時刻処理"""
        # Given
        start = datetime(2025, 1, 22, 10, 0, 0, 123456)  # マイクロ秒付き
        end = datetime(2025, 1, 22, 11, 30, 30, 987654)  # マイクロ秒付き
        session = LearningSession(self.project_name, self.episode_number, start)

        # When
        session.complete(end)

        # Then
        # 90分30秒だが、秒は切り捨てられるため90分
        assert session.total_writing_time == 90

    @pytest.mark.spec("SPEC-LEARNING_SESSION-UNICODE_PROJECT_NAME")
    def test_unicode_project_names(self) -> None:
        """TEST-37: Unicode文字のプロジェクト名"""
        # Given
        unicode_names = [
            "異世界転生物語",
            "🌟 Magic Novel ✨",
            "Русский роман",
            "العربية قصة",
            "日本の小説 - English Mix",
        ]

        # When & Then
        for name in unicode_names:
            session = LearningSession(project_name=name, episode_number=self.episode_number, start_time=self.start_time)
            assert session.project_name == name
            context = session.get_session_context()
            assert context["project_name"] == name

    # ===== 8. データ整合性テスト =====

    @pytest.mark.spec("SPEC-LEARNING_SESSION-OPTIONAL_FIELDS_NONE")
    def test_optional_fields_none_values(self) -> None:
        """TEST-38: オプションフィールドのNone値処理"""
        # Given & When
        session = LearningSession(
            project_name=self.project_name,
            episode_number=self.episode_number,
            start_time=self.start_time,
            # オプションフィールドは未指定(Noneになる
        )

        # Then
        assert session.writing_environment is None
        assert session.target_audience is None
        assert session.writing_goal is None

        # メトリクス生成時もNoneを正しく扱う
        session.complete()
        metrics = session.create_learning_metrics(5.0, 1)
        assert metrics.writing_context is None

    @pytest.mark.spec("SPEC-LEARNING_SESSION-OPTIONAL_FIELDS_WITH")
    def test_optional_fields_with_values(self) -> None:
        """TEST-39: オプションフィールドの値設定"""
        # Given
        environment = "家のリビング"
        audience = "中学生"
        goal = "主人公の成長を描く"

        # When
        session = LearningSession(
            project_name=self.project_name,
            episode_number=self.episode_number,
            start_time=self.start_time,
            writing_environment=environment,
            target_audience=audience,
            writing_goal=goal,
        )

        session.complete()

        # Then
        context = session.get_session_context()
        assert context["writing_environment"] == environment
        assert context["target_audience"] == audience
        assert context["writing_goal"] == goal

        # メトリクス生成でも正しく伝播
        metrics = session.create_learning_metrics(7.5, 2)
        assert metrics.writing_context == environment
