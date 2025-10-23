"""Domain.learning.value_objects
Where: Domain value objects capturing learning-related data.
What: Define typed structures for metrics, goals, and session parameters.
Why: Ensure consistent data across learning services and entities.
"""

from __future__ import annotations

"""学習機能付き品質チェックドメイン - 値オブジェクト"""


import math
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class QualityMetric(Enum):
    """品質評価指標。

    小説の品質を評価するための指標の列挙型。
    """

    READABILITY = "readability"
    DIALOGUE_RATIO = "dialogue_ratio"
    SENTENCE_VARIETY = "sentence_variety"
    NARRATIVE_DEPTH = "narrative_depth"
    EMOTIONAL_INTENSITY = "emotional_intensity"


class LearningDataQuality(Enum):
    """学習データの品質レベル。

    機械学習モデルの学習に使用するデータの品質を表す列挙型。
    """

    INSUFFICIENT = "insufficient"  # データ不足
    LOW = "low"  # 品質低
    MEDIUM = "medium"  # 標準
    HIGH = "high"  # 高品質
    EXCELLENT = "excellent"  # 最高品質


@dataclass(frozen=True)
class WritingStyleProfile:
    """文体プロファイル値オブジェクト

    ビジネスルール:
    - 特徴量の正規化・範囲検証
    - 信頼度計算
    - プロファイル間類似度計算
    """

    profile_id: str
    features: dict[str, float]
    confidence_score: float
    sample_count: int
    last_updated: datetime
    genre: str | None = None

    def __post_init__(self) -> None:
        self._validate_features()
        self._validate_confidence()

    def _validate_features(self) -> None:
        """特徴量の検証"""
        for feature_name, value in self.features.items():
            self._validate_single_feature(feature_name, value)

    def _validate_single_feature(self, feature_name: str, value: float) -> None:
        """単一特徴量の検証"""
        if feature_name in ["dialogue_ratio", "comma_frequency", "adjective_ratio", "emotional_words_ratio"]:
            self._validate_ratio_feature(feature_name, value)
        elif feature_name == "avg_sentence_length":
            self._validate_sentence_length_feature(feature_name, value)
        elif value < 0:
            msg = f"特徴量が有効範囲外: {feature_name}={value}"
            raise ValueError(msg)

    def _validate_ratio_feature(self, feature_name: str, value: float) -> None:
        """比率特徴量の検証"""
        if not (0.0 <= value <= 1.0):
            msg = f"特徴量が有効範囲外: {feature_name}={value}"
            raise ValueError(msg)

    def _validate_sentence_length_feature(self, feature_name: str, value: float) -> None:
        """文長特徴量の検証"""
        if not (1.0 <= value <= 200.0):
            msg = f"特徴量が有効範囲外: {feature_name}={value}"
            raise ValueError(msg)

    def _validate_confidence(self) -> None:
        """信頼度の検証"""
        if not (0.0 <= self.confidence_score <= 1.0):
            msg = f"信頼度が有効範囲外: {self.confidence_score}"
            raise ValueError(msg)

    def get_feature(self, feature_name: str) -> float:
        """特徴量取得"""
        return self.features.get(feature_name, 0.0)

    def is_reliable(self) -> bool:
        """信頼度十分チェック"""
        return self.confidence_score >= 0.8 and self.sample_count >= 10

    def calculate_similarity(self, other: WritingStyleProfile) -> float:
        """プロファイル間類似度計算(コサイン類似度)"""
        # 共通する特徴量のみで計算
        common_features = set(self.features.keys()) & set(other.features.keys())

        if not common_features:
            return 0.0

        # ベクトルの内積計算
        dot_product = sum(self.features[feature] * other.features[feature] for feature in common_features)

        # ベクトルの大きさ計算
        magnitude_self = math.sqrt(sum(self.features[feature] ** 2 for feature in common_features))
        magnitude_other = math.sqrt(sum(other.features[feature] ** 2 for feature in common_features))

        if magnitude_self == 0 or magnitude_other == 0:
            return 0.0

        # コサイン類似度
        similarity = dot_product / (magnitude_self * magnitude_other)
        return max(0.0, min(1.0, similarity))  # 0-1の範囲にクランプ

    def get_feature_importance_weights(self) -> dict[str, float]:
        """特徴量重要度ウェイト"""
        base_weights = {
            "avg_sentence_length": 0.2,
            "dialogue_ratio": 0.25,
            "sentence_variety_score": 0.15,
            "emotional_words_ratio": 0.15,
            "comma_frequency": 0.1,
            "adjective_ratio": 0.1,
            "paragraph_length_variance": 0.05,
        }

        # 信頼度による調整
        confidence_multiplier = self.confidence_score
        return {k: v * confidence_multiplier for k, v in base_weights.items()}


@dataclass(frozen=True)
class QualityEvaluationResult:
    """品質評価結果値オブジェクト"""

    total_score: float
    metric_scores: dict[QualityMetric, float]
    confidence_level: float
    personalized_adjustments: dict[str, float]
    evaluation_timestamp: datetime

    def has_personalized_adjustments(self) -> bool:
        """個人化調整有無チェック"""
        return bool(self.personalized_adjustments)

    def get_metric_score(self, metric: str) -> float:
        """メトリック別スコア取得"""
        return self.metric_scores.get(metric, 0.0)

    def is_high_quality(self) -> bool:
        """高品質判定"""
        return self.total_score >= 80.0 and self.confidence_level >= 0.7


@dataclass(frozen=True)
class CorrelationInsight:
    """相関分析洞察値オブジェクト"""

    metric_pair: tuple
    correlation_coefficient: float
    significance_level: float
    sample_size: int
    actionable_insight: str

    def is_significant(self) -> bool:
        """統計的有意性チェック"""
        return self.significance_level < 0.05 and abs(self.correlation_coefficient) > 0.3

    def get_strength_description(self) -> str:
        """相関の強さ説明"""
        abs_corr = abs(self.correlation_coefficient)
        if abs_corr >= 0.8:
            return "非常に強い"
        if abs_corr >= 0.6:
            return "強い"
        if abs_corr >= 0.4:
            return "中程度"
        if abs_corr >= 0.2:
            return "弱い"
        return "非常に弱い"
