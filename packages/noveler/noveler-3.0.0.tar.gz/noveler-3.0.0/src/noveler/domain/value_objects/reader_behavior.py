#!/usr/bin/env python3
"""ReaderBehavior値オブジェクト

読者行動パターンを表現する不変オブジェクト
SPEC-ANALYSIS-001準拠
"""

from dataclasses import dataclass

from noveler.domain.value_objects.reader_segment import ReaderSegment


@dataclass(frozen=True)
class ReaderBehavior:
    """読者行動パターンを表現する値オブジェクト

    Attributes:
        reader_segment (ReaderSegment): 読者セグメント
        engagement_score (float): エンゲージメントスコア(0.0-1.0)
        retention_rate (float): 継続率(0.0-1.0)
        dropout_probability (float): 離脱確率(0.0-1.0)
    """

    reader_segment: ReaderSegment
    engagement_score: float
    retention_rate: float
    dropout_probability: float

    def __post_init__(self) -> None:
        """値オブジェクト作成後の検証"""
        self._validate_score_ranges()

    def _validate_score_ranges(self) -> None:
        """スコア値の範囲検証"""
        scores = [
            ("engagement_score", self.engagement_score),
            ("retention_rate", self.retention_rate),
            ("dropout_probability", self.dropout_probability),
        ]

        for name, value in scores:
            if not (0.0 <= value <= 1.0):
                msg = f"{name} must be between 0.0 and 1.0, got {value}"
                raise ValueError(msg)

    def is_high_risk(self) -> bool:
        """高リスク読者かどうかを判定する

        Returns:
            bool: 離脱確率が50%超の場合True
        """
        return self.dropout_probability > 0.5

    def calculate_lifetime_value(self) -> float:
        """読者の生涯価値を計算する

        Returns:
            float: 生涯価値
        """
        return self.engagement_score * self.retention_rate * (1 - self.dropout_probability)
