"""Domain.analysis.value_objects
Where: Domain value objects supporting analysis workflows.
What: Encapsulates typed data such as metrics and thresholds.
Why: Keeps analysis-related data structures consistent across the domain.
"""

from __future__ import annotations

"""分析ドメインの値オブジェクト"""


import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class AnalysisPeriod(Enum):
    """分析期間"""

    DAILY = "daily"  # 日次
    WEEKLY = "weekly"  # 週次
    MONTHLY = "monthly"  # 月次
    ALL_TIME = "all_time"  # 全期間


class DropoutSeverity(Enum):
    """離脱率の深刻度"""

    LOW = "low"  # 低(0-10%)
    MODERATE = "moderate"  # 中(10-20%)
    HIGH = "high"  # 高(20-30%)
    CRITICAL = "critical"  # 危険(30%以上)


@dataclass(frozen=True)
class DropoutRate:
    """離脱率を表す値オブジェクト"""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            msg = "離脱率は0.0から1.0の範囲である必要があります"
            raise ValueError(msg)

    def to_percentage(self) -> float:
        """パーセンテージ表記に変換"""
        return self.value * 100.0

    def get_severity(self) -> DropoutSeverity:
        """深刻度を判定"""
        percentage = self.to_percentage()
        if percentage < 10:
            return DropoutSeverity.LOW
        if percentage < 20:
            return DropoutSeverity.MODERATE
        if percentage < 30:
            return DropoutSeverity.HIGH
        return DropoutSeverity.CRITICAL

    def is_acceptable(self, threshold: float = 0.2) -> bool:
        """許容可能な離脱率かチェック(デフォルト閾値: 20%)"""
        return self.value <= threshold

    def __str__(self) -> str:
        return f"{self.to_percentage():.1f}%"


@dataclass(frozen=True)
class PageView:
    """ページビューを表す値オブジェクト"""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            msg = "ページビューは0以上である必要があります"
            raise ValueError(msg)

    def __add__(self, other: PageView) -> PageView:
        """ページビューの加算"""
        return PageView(self.value + other.value)

    def __sub__(self, other: PageView) -> int:
        """ページビューの差分"""
        return self.value - other.value


@dataclass(frozen=True)
class UniqueUser:
    """ユニークユーザー数を表す値オブジェクト"""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            msg = "ユニークユーザー数は0以上である必要があります"
            raise ValueError(msg)

    def calculate_dropout_rate(self, previous: UniqueUser) -> DropoutRate | None:
        """前話からの離脱率を計算"""
        if previous.value == 0:
            return None

        if self.value > previous.value:
            # ユーザー数が増えた場合は離脱率0とする
            return DropoutRate(0.0)

        dropout = (previous.value - self.value) / previous.value
        return DropoutRate(dropout)


@dataclass(frozen=True)
class DateRange:
    """日付範囲を表す値オブジェクト"""

    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            msg = "開始日は終了日以前である必要があります"
            raise ValueError(msg)

    def contains(self, target_date: date) -> bool:
        """指定日が範囲内かチェック"""
        return self.start_date <= target_date <= self.end_date

    def days(self) -> int:
        """期間の日数"""
        return (self.end_date - self.start_date).days + 1

    def weeks(self) -> int:
        """期間の週数"""
        return self.days() // 7

    @classmethod
    def last_n_days(cls, n: int) -> DateRange:
        """過去n日間の範囲を作成"""
        end_date = project_now().datetime.date()
        start_date = end_date - timedelta(days=n - 1)
        return cls(start_date, end_date)

    @classmethod
    def last_week(cls) -> DateRange:
        """先週の範囲を作成"""
        today = project_now().datetime.date()
        start_of_week = today - timedelta(days=today.weekday() + 7)
        end_of_week = start_of_week + timedelta(days=6)
        return cls(start_of_week, end_of_week)

    @classmethod
    def last_month(cls) -> DateRange:
        """先月の範囲を作成"""
        today = project_now().datetime.date()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)
        return cls(first_day_of_last_month, last_day_of_last_month)

    @classmethod
    def current_month(cls) -> DateRange:
        """今月の範囲を作成"""
        today = project_now().datetime.date()
        first_day_of_current_month = today.replace(day=1)
        # 次月の1日から1日を引くことで今月の最終日を取得
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        last_day_of_current_month = next_month - timedelta(days=1)
        return cls(first_day_of_current_month, last_day_of_current_month)


@dataclass(frozen=True)
class NarouCode:
    """なろう小説コードを表す値オブジェクト"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            msg = "なろうコードは必須です"
            raise ValueError(msg)

        # なろうコードの形式チェック(nXXXXXXXXXX)
        if not re.match(r"^n\d{10}[a-z]?$", self.value):
            msg = "無効ななろうコード形式です"
            raise ValueError(msg)

    def get_kasasagi_url(self) -> str:
        """KASASAGI APIのURLを生成"""
        return f"https://kasasagi.hinaproject.com/access/top/ncode/{self.value}/"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class AnalysisTimestamp:
    """分析実行時刻を表す値オブジェクト"""

    value: datetime

    def is_recent(self, hours: int) -> bool:
        """最近の分析かチェック"""
        time_diff = project_now().datetime - self.value
        return time_diff.total_seconds() < hours * 3600

    def time_since(self) -> timedelta:
        """分析からの経過時間"""
        return project_now().datetime - self.value

    def __str__(self) -> str:
        return self.value.strftime("%Y-%m-%d %H:%M:%S")
