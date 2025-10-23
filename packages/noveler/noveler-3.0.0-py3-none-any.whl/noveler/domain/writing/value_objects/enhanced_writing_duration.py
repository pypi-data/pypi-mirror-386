"""執筆時間値オブジェクト(Design by Contract強化版)

執筆セッションの時間を管理する不変オブジェクト
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from noveler.domain.exceptions import DomainException


@dataclass(frozen=True)
class EnhancedWritingDuration:
    """執筆時間を表す値オブジェクト(契約強化版)

    不変条件:
    - 開始時刻は終了時刻より前
    - 執筆時間は0秒以上
    - 最大執筆時間は24時間以内
    """

    start_time: datetime
    end_time: datetime

    # 制限
    MAX_DURATION_HOURS = 24

    def __post_init__(self) -> None:
        """不変条件の検証"""
        if not isinstance(self.start_time, datetime):
            msg = "開始時刻はdatetimeである必要があります"
            raise DomainException(msg)
        if not isinstance(self.end_time, datetime):
            msg = "終了時刻はdatetimeである必要があります"
            raise DomainException(msg)

        if self.start_time > self.end_time:
            msg = "開始時刻は終了時刻より前である必要があります"
            raise DomainException(msg)

        duration_hours = (self.end_time - self.start_time).total_seconds() / 3600
        if duration_hours > self.MAX_DURATION_HOURS:
            msg = f"執筆時間は{self.MAX_DURATION_HOURS}時間以内である必要があります"
            raise DomainException(msg)

    @property
    def duration(self) -> timedelta:
        """執筆時間を取得"""
        return self.end_time - self.start_time

    @property
    def minutes(self) -> int:
        """執筆時間を分単位で取得"""
        return int(self.duration.total_seconds() / 60)

    @property
    def hours(self) -> float:
        """執筆時間を時間単位で取得"""
        return self.duration.total_seconds() / 3600

    def __str__(self) -> str:
        """文字列表現"""
        total_minutes = self.minutes
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours > 0:
            return f"{hours}時間{minutes}分"
        return f"{minutes}分"

    def __add__(self, other: "EnhancedWritingDuration") -> "EnhancedWritingDuration":
        """執筆時間の加算"""
        # 新しい開始時刻と終了時刻を計算
        new_start = min(self.start_time, other.start_time)
        total_duration = self.duration + other.duration
        new_end = new_start + total_duration

        # 24時間制限のチェック
        if total_duration.total_seconds() / 3600 > self.MAX_DURATION_HOURS:
            msg = f"合計執筆時間は{self.MAX_DURATION_HOURS}時間を超えることはできません"
            raise DomainException(msg)

        return EnhancedWritingDuration(new_start, new_end)

    def is_productive(self, min_minutes: int) -> bool:
        """生産的な執筆セッションかどうか"""
        return self.minutes >= min_minutes

    def is_marathon_session(self, threshold_hours: float) -> bool:
        """長時間執筆セッションかどうか"""
        return self.hours >= threshold_hours

    def _validate_invariants(self) -> None:
        """不変条件の検証"""
        if self.start_time > self.end_time:
            msg = "開始時刻は終了時刻より前である必要があります"
            raise DomainException(msg)
        if self.duration.total_seconds() < 0:
            msg = "執筆時間は0秒以上である必要があります"
            raise DomainException(msg)
        if self.hours > self.MAX_DURATION_HOURS:
            msg = f"執筆時間は{self.MAX_DURATION_HOURS}時間以内である必要があります"
            raise DomainException(msg)
