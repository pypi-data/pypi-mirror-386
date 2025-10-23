"""公開スケジュールを表す値オブジェクト"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass(frozen=True)
class PublicationSchedule:
    """公開スケジュールを表す値オブジェクト"""

    scheduled_at: datetime

    def __post_init__(self) -> None:
        if self.scheduled_at < project_now().datetime:
            msg = "公開予定日時は現在時刻より後である必要があります"
            raise ValueError(msg)

    def is_ready_to_publish(self) -> bool:
        """公開可能な時刻になったかチェック"""
        return project_now().datetime >= self.scheduled_at

    def time_until_publication(self) -> timedelta:
        """公開までの残り時間"""
        delta = self.scheduled_at - project_now().datetime
        return delta if delta.total_seconds() > 0 else timedelta(0)
