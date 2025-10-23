#!/usr/bin/env python3
"""A31チェックリスト閾値値オブジェクト

SPEC-QUALITY-001に基づく閾値の表現。
異なるタイプの閾値(パーセンテージ、スコア、範囲、ブール)を統一的に管理。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ThresholdType(Enum):
    """閾値タイプ"""

    PERCENTAGE = "percentage"  # パーセンテージ(0-100)
    SCORE = "score"  # スコア(任意の数値)
    RANGE = "range"  # 範囲(min-max)
    BOOLEAN = "boolean"  # ブール値(0.0または1.0)


@dataclass(frozen=True)
class Threshold:
    """閾値値オブジェクト

    A31チェックリスト項目の評価基準を表現。
    タイプに応じて異なる閾値形式をサポート。
    """

    threshold_type: ThresholdType
    value: float
    min_value: float | None = None
    max_value: float | None = None

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self._validate_threshold()

    def _validate_threshold(self) -> None:
        """閾値の妥当性検証"""
        if self.threshold_type == ThresholdType.PERCENTAGE:
            if not 0.0 <= self.value <= 100.0:
                msg = f"パーセンテージ閾値は0-100の範囲である必要があります: {self.value}"
                raise ValueError(msg)

        elif self.threshold_type == ThresholdType.BOOLEAN:
            if self.value not in (0.0, 1.0):
                msg = f"ブール閾値は0.0または1.0である必要があります: {self.value}"
                raise ValueError(msg)

        elif self.threshold_type == ThresholdType.RANGE:
            if self.min_value is None or self.max_value is None:
                msg = "範囲閾値にはmin_valueとmax_valueが必要です"
                raise ValueError(msg)
            if self.min_value >= self.max_value:
                msg = f"min_value ({self.min_value}) はmax_value ({self.max_value}) より小さい必要があります"
                raise ValueError(msg)

    def evaluate(self, current_value: float) -> bool:
        """現在値が閾値を満たすかの評価

        Args:
            current_value: 評価対象の値

        Returns:
            bool: 閾値を満たす場合True
        """
        if self.threshold_type in (ThresholdType.PERCENTAGE, ThresholdType.SCORE):
            return current_value >= self.value

        if self.threshold_type == ThresholdType.BOOLEAN:
            return abs(current_value - self.value) < 0.001  # 浮動小数点誤差考慮

        if self.threshold_type == ThresholdType.RANGE:
            return self.min_value <= current_value <= self.max_value

        return False

    def check(self, current_value: float) -> bool:
        """現在値が閾値を満たすかの評価(evaluateのエイリアス)

        Args:
            current_value: 評価対象の値

        Returns:
            bool: 閾値を満たす場合True
        """
        return self.evaluate(current_value)

    def get_distance_to_pass(self, current_value: float) -> float:
        """閾値達成までの距離計算

        Args:
            current_value: 現在値

        Returns:
            float: 閾値達成までの距離(負数は既に達成を意味)
        """
        if self.threshold_type in (ThresholdType.PERCENTAGE, ThresholdType.SCORE):
            return self.value - current_value

        if self.threshold_type == ThresholdType.BOOLEAN:
            return 0.0 if self.evaluate(current_value) else 1.0

        if self.threshold_type == ThresholdType.RANGE:
            if current_value < self.min_value:
                return self.min_value - current_value
            if current_value > self.max_value:
                return current_value - self.max_value
            return 0.0  # 範囲内

        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換

        Returns:
            Dict[str, Any]: 閾値データの辞書表現
        """
        result = {"type": self.threshold_type.value, "value": self.value}

        if self.min_value is not None:
            result["min_value"] = self.min_value
        if self.max_value is not None:
            result["max_value"] = self.max_value

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Threshold":
        """辞書からの復元

        Args:
            data: 閾値データの辞書

        Returns:
            Threshold: 復元された閾値インスタンス
        """
        return cls(
            threshold_type=ThresholdType(data["type"]),
            value=data["value"],
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
        )

    @classmethod
    def create_range(cls, min_value: float, max_value: float) -> "Threshold":
        """範囲閾値の作成

        Args:
            min_value: 最小値
            max_value: 最大値

        Returns:
            Threshold: 範囲閾値インスタンス
        """
        return cls(
            threshold_type=ThresholdType.RANGE,
            value=(min_value + max_value) / 2,  # 中央値を代表値とする
            min_value=min_value,
            max_value=max_value,
        )
