#!/usr/bin/env python3
"""AnalysisPeriod値オブジェクト

分析期間を表現する不変オブジェクト
SPEC-ANALYSIS-001準拠
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone


@dataclass(frozen=True)
class AnalysisPeriod:
    """分析期間を表現する値オブジェクト

    Attributes:
        start_date (date): 開始日
        end_date (date): 終了日
        days (int): 期間日数
    """

    start_date: date
    end_date: date
    days: int

    def __post_init__(self) -> None:
        """値オブジェクト作成後の検証"""
        self._validate_period()

    def _validate_period(self) -> None:
        """期間の妥当性検証"""
        if self.start_date > self.end_date:
            msg = "start_date must be before or equal to end_date"
            raise ValueError(msg)

        if self.days <= 0:
            msg = "days must be positive"
            raise ValueError(msg)

        # 実際の日数と指定日数の整合性チェック
        actual_days = (self.end_date - self.start_date).days + 1
        if actual_days != self.days:
            msg = (
                f"days ({self.days}) doesn't match actual period "
                f"({actual_days} days from {self.start_date} to {self.end_date})"
            )

            raise ValueError(msg)

    def contains(self, target_date: date) -> bool:
        """指定した日付が期間内に含まれるかどうかを判定する

        Args:
            target_date (date): 判定対象の日付

        Returns:
            bool: 期間内に含まれる場合True
        """
        return self.start_date <= target_date <= self.end_date

    def is_recent_data(self, target_date: date) -> bool:
        """指定した日付が直近2日間以内かどうかを判定する

        Args:
            target_date (date): 判定対象の日付

        Returns:
            bool: 直近2日間以内の場合True
        """
        today = datetime.now(timezone.utc).date()
        cutoff_date = today - timedelta(days=2)
        return target_date > cutoff_date

    @classmethod
    def last_14_days(cls) -> "AnalysisPeriod":
        """直近14日間の分析期間を作成する

        Returns:
            AnalysisPeriod: 直近14日間の期間
        """
        today = datetime.now(timezone.utc).date()
        start_date = today - timedelta(days=13)  # 14日間なので13日前から
        return cls(start_date=start_date, end_date=today, days=14)

    @classmethod
    def last_30_days(cls) -> "AnalysisPeriod":
        """直近30日間の分析期間を作成する

        Returns:
            AnalysisPeriod: 直近30日間の期間
        """
        today = datetime.now(timezone.utc).date()
        start_date = today - timedelta(days=29)  # 30日間なので29日前から
        return cls(start_date=start_date, end_date=today, days=30)

    @classmethod
    def custom_period(cls, start_date: date, end_date: date) -> "AnalysisPeriod":
        """カスタム期間の分析期間を作成する

        Args:
            start_date (date): 開始日
            end_date (date): 終了日

        Returns:
            AnalysisPeriod: カスタム期間
        """
        days = (end_date - start_date).days + 1
        return cls(start_date=start_date, end_date=end_date, days=days)
