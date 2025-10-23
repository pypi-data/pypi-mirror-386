#!/usr/bin/env python3
"""TrackingSession値オブジェクトのユニットテスト

SPEC-ANALYSIS-001に基づくTDD実装
"""

from datetime import datetime, timedelta

import pytest

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.tracking_session import TrackingSession

pytestmark = pytest.mark.vo_smoke


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestTrackingSession:
    """TrackingSession値オブジェクトのテストクラス"""

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_create_valid_tracking_session(self) -> None:
        """正常なTrackingSessionの作成テスト"""
        # Given: 正常なセッションデータ
        session_id = "test-session-123"
        tracking_start = datetime(2025, 7, 24, 10, 0, 0, tzinfo=JST)
        tracking_end = datetime(2025, 7, 24, 11, 0, 0, tzinfo=JST)
        events_count = 10

        # When: TrackingSessionを作成
        session = TrackingSession(
            session_id=session_id, tracking_start=tracking_start, tracking_end=tracking_end, events_count=events_count
        )

        # Then: 正しく作成される
        assert session.session_id == session_id
        assert session.tracking_start == tracking_start
        assert session.tracking_end == tracking_end
        assert session.events_count == events_count

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_invalid_session_start_after_end(self) -> None:
        """開始時刻が終了時刻以降の場合のエラーテスト"""
        # Given: 開始時刻が終了時刻以降
        session_id = "test-session"
        tracking_start = datetime(2025, 7, 24, 11, 0, 0, tzinfo=JST)
        tracking_end = datetime(2025, 7, 24, 10, 0, 0, tzinfo=JST)
        events_count = 10

        # When/Then: エラーが発生
        with pytest.raises(ValueError, match="tracking_start must be before tracking_end"):
            TrackingSession(
                session_id=session_id,
                tracking_start=tracking_start,
                tracking_end=tracking_end,
                events_count=events_count,
            )

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_invalid_session_negative_events(self) -> None:
        """負のイベント数の場合のエラーテスト"""
        # Given: 負のイベント数
        session_id = "test-session"
        tracking_start = datetime(2025, 7, 24, 10, 0, 0, tzinfo=JST)
        tracking_end = datetime(2025, 7, 24, 11, 0, 0, tzinfo=JST)
        events_count = -5

        # When/Then: エラーが発生
        with pytest.raises(ValueError, match="events_count must be non-negative"):
            TrackingSession(
                session_id=session_id,
                tracking_start=tracking_start,
                tracking_end=tracking_end,
                events_count=events_count,
            )

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_invalid_session_empty_id(self) -> None:
        """空のセッションIDの場合のエラーテスト"""
        # Given: 空のセッションID
        session_id = ""
        tracking_start = datetime(2025, 7, 24, 10, 0, 0, tzinfo=JST)
        tracking_end = datetime(2025, 7, 24, 11, 0, 0, tzinfo=JST)
        events_count = 10

        # When/Then: エラーが発生
        with pytest.raises(ValueError, match="session_id cannot be empty"):
            TrackingSession(
                session_id=session_id,
                tracking_start=tracking_start,
                tracking_end=tracking_end,
                events_count=events_count,
            )

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_duration_calculation(self) -> None:
        """セッション継続時間計算テスト"""
        # Given: 1時間のセッション
        session = TrackingSession(
            session_id="test-session",
            tracking_start=datetime(2025, 7, 24, 10, 0, 0, tzinfo=JST),
            tracking_end=datetime(2025, 7, 24, 11, 0, 0, tzinfo=JST),
            events_count=10,
        )

        # When: 継続時間を計算
        duration = session.duration()

        # Then: 1時間が返される
        assert duration == timedelta(hours=1)

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_active_true(self) -> None:
        """アクティブセッション判定テスト(True)"""
        # Given: 未来に終了するセッション
        now = project_now().datetime
        session = TrackingSession(
            session_id="test-session",
            tracking_start=now - timedelta(minutes=30),
            tracking_end=now + timedelta(minutes=30),
            events_count=10,
        )

        # When: アクティブ判定
        result = session.is_active()

        # Then: Trueが返される
        assert result is True

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_active_false(self) -> None:
        """非アクティブセッション判定テスト(False)"""
        # Given: 過去に終了したセッション
        now = project_now().datetime
        session = TrackingSession(
            session_id="test-session",
            tracking_start=now - timedelta(hours=2),
            tracking_end=now - timedelta(hours=1),
            events_count=10,
        )

        # When: アクティブ判定
        result = session.is_active()

        # Then: Falseが返される
        assert result is False

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_events_per_minute_calculation(self) -> None:
        """1分あたりのイベント数計算テスト"""
        # Given: 60分で60イベントのセッション
        session = TrackingSession(
            session_id="test-session",
            tracking_start=datetime(2025, 7, 24, 10, 0, 0, tzinfo=JST),
            tracking_end=datetime(2025, 7, 24, 11, 0, 0, tzinfo=JST),
            events_count=60,
        )

        # When: 1分あたりのイベント数を計算
        result = session.events_per_minute()

        # Then: 1.0が返される
        assert result == 1.0

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_events_per_minute_minimal_duration(self) -> None:
        """最小継続時間の場合のイベント数計算テスト"""
        # Given: 1秒のセッション
        start_time = datetime(2025, 7, 24, 10, 0, 0, tzinfo=JST)
        end_time = datetime(2025, 7, 24, 10, 0, 1, tzinfo=JST)  # 1秒後
        session = TrackingSession(
            session_id="test-session", tracking_start=start_time, tracking_end=end_time, events_count=10
        )

        # When: 1分あたりのイベント数を計算
        result = session.events_per_minute()

        # Then: 600.0が返される(10イベント/秒 * 60秒)
        assert result == 600.0

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_create_new_session_factory(self) -> None:
        """新規セッション作成ファクトリメソッドテスト"""
        # When: 新規セッションを作成
        session = TrackingSession.create_new_session(duration_minutes=30)

        # Then: 正しいセッションが作成される
        assert session.session_id is not None
        assert len(session.session_id) > 0
        assert session.events_count == 0
        assert session.duration() == timedelta(minutes=30)

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_add_events_success(self) -> None:
        """イベント追加テスト(正常)"""
        # Given: 既存のセッション
        original_session = TrackingSession(
            session_id="test-session",
            tracking_start=datetime(2025, 7, 24, 10, 0, 0, tzinfo=JST),
            tracking_end=datetime(2025, 7, 24, 11, 0, 0, tzinfo=JST),
            events_count=10,
        )

        # When: イベントを追加
        new_session = original_session.add_events(5)

        # Then: 新しいセッションでイベント数が更新される
        assert new_session.session_id == original_session.session_id
        assert new_session.tracking_start == original_session.tracking_start
        assert new_session.tracking_end == original_session.tracking_end
        assert new_session.events_count == 15
        # 元のセッションは変更されない
        assert original_session.events_count == 10

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_add_events_negative_count(self) -> None:
        """負のイベント数追加エラーテスト"""
        # Given: 既存のセッション
        session = TrackingSession(
            session_id="test-session",
            tracking_start=datetime(2025, 7, 24, 10, 0, 0, tzinfo=JST),
            tracking_end=datetime(2025, 7, 24, 11, 0, 0, tzinfo=JST),
            events_count=10,
        )

        # When/Then: 負のイベント数追加でエラー
        with pytest.raises(ValueError, match="event_count must be non-negative"):
            session.add_events(-5)

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_tracking_session_immutability(self) -> None:
        """TrackingSessionの不変性テスト"""
        # Given: TrackingSession
        session = TrackingSession(
            session_id="test-session",
            tracking_start=datetime(2025, 7, 24, 10, 0, 0, tzinfo=JST),
            tracking_end=datetime(2025, 7, 24, 11, 0, 0, tzinfo=JST),
            events_count=10,
        )

        # When/Then: 属性変更を試行するとエラーが発生
        with pytest.raises(AttributeError, match=".*"):
            session.events_count = 20
