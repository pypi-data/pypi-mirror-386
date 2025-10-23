#!/usr/bin/env python3
"""AccessPattern値オブジェクト

アクセスパターンデータを表現する不変オブジェクト
SPEC-ANALYSIS-001準拠
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AccessPattern:
    """アクセスパターンを表現する値オブジェクト

    Attributes:
        pv (int): ページビュー数
        ua (int): ユニークアクセス数
        episode_number (int): エピソード番号
        measurement_date (date): 計測日
    """

    pv: int
    ua: int
    episode_number: int
    measurement_date: date

    def calculate_pv_per_ua(self) -> float:
        """PV/UA比率を計算する

        Returns:
            float: PV/UA比率(UA=0の場合は0.0を返す)
        """
        if self.ua == 0:
            return 0.0
        return self.pv / self.ua

    def is_valid_data(self) -> bool:
        """データの有効性を判定する

        Returns:
            bool: データが有効な場合True
        """
        return self.pv > 0 and self.ua >= 0 and self.episode_number > 0
