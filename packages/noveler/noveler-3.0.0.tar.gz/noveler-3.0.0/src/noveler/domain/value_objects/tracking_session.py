#!/usr/bin/env python3
"""TrackingSession値オブジェクト

読者行動追跡セッションを表現する不変オブジェクト
SPEC-ANALYSIS-001準拠
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass(frozen=True)
class TrackingSession:
    """追跡セッションを表現する値オブジェクト

    Attributes:
        session_id (str): セッションID
        tracking_start (datetime): 追跡開始時刻
        tracking_end (datetime): 追跡終了時刻
        events_count (int): イベント数
    """

    session_id: str
    tracking_start: datetime
    tracking_end: datetime
    events_count: int

    def __post_init__(self) -> None:
        """値オブジェクト作成後の検証"""
        self._validate_session()

    def _validate_session(self) -> None:
        """セッションの妥当性検証"""
        if self.tracking_start >= self.tracking_end:
            msg = "tracking_start must be before tracking_end"
            raise ValueError(msg)

        if self.events_count < 0:
            msg = "events_count must be non-negative"
            raise ValueError(msg)

        if not self.session_id:
            msg = "session_id cannot be empty"
            raise ValueError(msg)

    def duration(self) -> timedelta:
        """セッション継続時間を計算する

        Returns:
            timedelta: セッション継続時間
        """
        return self.tracking_end - self.tracking_start

    def is_active(self) -> bool:
        """セッションがアクティブかどうかを判定する

        Returns:
            bool: 現在時刻が終了時刻前の場合True
        """
        return project_now().datetime < self.tracking_end

    def events_per_minute(self) -> float:
        """1分あたりのイベント数を計算する

        Returns:
            float: 1分あたりのイベント数
        """
        duration_minutes = self.duration().total_seconds() / 60
        if duration_minutes == 0:
            return 0.0
        return self.events_count / duration_minutes

    @classmethod
    def create_new_session(cls, duration_minutes: int) -> "TrackingSession":
        """新しい追跡セッションを作成する

        Args:
            duration_minutes (int): セッション継続時間(分)

        Returns:
            TrackingSession: 新しいセッション
        """
        now = project_now().datetime
        return cls(
            session_id=str(uuid4()),
            tracking_start=now,
            tracking_end=now + timedelta(minutes=duration_minutes),
            events_count=0,
        )

    def add_events(self, event_count: int) -> "TrackingSession":
        """イベント数を追加した新しいセッションを作成する

        Args:
            event_count (int): 追加するイベント数

        Returns:
            TrackingSession: イベント数が更新されたセッション
        """
        if event_count < 0:
            msg = "event_count must be non-negative"
            raise ValueError(msg)

        return TrackingSession(
            session_id=self.session_id,
            tracking_start=self.tracking_start,
            tracking_end=self.tracking_end,
            events_count=self.events_count + event_count,
        )
