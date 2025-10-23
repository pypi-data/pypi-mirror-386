"""Golden Sample（類似作品参照）の値オブジェクト

プロジェクト設定で定義されたGolden Sample（類似作品）を管理し、
独自性検証や差別化戦略の基準として活用する。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ComparisonDepth(Enum):
    """比較深度レベル"""
    SIMPLE = "simple"  # 基本的な比較
    MODERATE = "moderate"  # 中程度の比較
    DETAILED = "detailed"  # 詳細な比較


class SampleType(Enum):
    """Golden Sampleのタイプ"""
    MAIN_REFERENCE = "main_reference"  # メイン参考作品
    SUB_REFERENCE = "sub_reference"  # サブ参考作品
    CONTRAST_REFERENCE = "contrast_reference"  # 対照参考作品


@dataclass(frozen=True)
class GoldenSample:
    """Golden Sample（参照作品）の定義"""

    title: str  # 作品タイトル
    url: str  # なろう小説URL
    genre: str  # ジャンル
    key_features: list[str] = field(default_factory=list)  # 主要な特徴
    reference_aspects: list[str] = field(default_factory=list)  # 参考にする側面
    differentiation_notes: str = ""  # 差別化方針のメモ
    sample_type: SampleType | None = None  # サンプルタイプ

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.title:
            msg = "タイトルは必須です"
            raise ValueError(msg)
        if not self.url:
            msg = "URLは必須です"
            raise ValueError(msg)
        if not self.url.startswith("https://ncode.syosetu.com/"):
            msg = "なろう小説のURLを指定してください"
            raise ValueError(msg)
        if len(self.key_features) < 3:
            msg = "主要な特徴は3つ以上必要です"
            raise ValueError(msg)
        if len(self.reference_aspects) < 2:
            msg = "参考にする側面は2つ以上必要です"
            raise ValueError(msg)

    def get_ncode(self) -> str:
        """URLからNコードを抽出"""
        # https://ncode.syosetu.com/n9736bm/ -> n9736bm
        parts = self.url.strip("/").split("/")
        if len(parts) >= 4:
            return parts[-1]
        return ""

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "title": self.title,
            "url": self.url,
            "genre": self.genre,
            "key_features": self.key_features,
            "reference_aspects": self.reference_aspects,
            "differentiation_notes": self.differentiation_notes,
            "sample_type": self.sample_type.value if self.sample_type else None
        }


@dataclass(frozen=True)
class GoldenSampleComparison:
    """Golden Sampleとの比較結果"""

    sample: GoldenSample  # 比較対象のGolden Sample
    common_elements: list[str] = field(default_factory=list)  # 共通要素
    differentiation_elements: list[str] = field(default_factory=list)  # 差別化要素
    uniqueness_score: float = 0.0  # 独自性スコア（0-100%）
    differentiation_strategy: str = ""  # 差別化戦略

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.uniqueness_score < 0 or self.uniqueness_score > 100:
            msg = "独自性スコアは0-100の範囲で指定してください"
            raise ValueError(msg)
        if len(self.differentiation_elements) < 2:
            msg = "差別化要素は2つ以上必要です"
            raise ValueError(msg)

    def is_sufficiently_unique(self, threshold: float = 70.0) -> bool:
        """十分な独自性があるか判定"""
        return self.uniqueness_score >= threshold

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "title": self.sample.title,
            "common_elements": self.common_elements,
            "differentiation_elements": self.differentiation_elements,
            "uniqueness_score": self.uniqueness_score,
            "differentiation_strategy": self.differentiation_strategy
        }


@dataclass(frozen=True)
class DifferentiationStrategy:
    """差別化戦略"""

    unique_selling_points: list[str] = field(default_factory=list)  # 独自の強み
    unique_approaches: list[str] = field(default_factory=list)  # 独自のアプローチ
    avoided_patterns: list[str] = field(default_factory=list)  # 避けるパターン
    core_theme: str = ""  # コアテーマ
    sub_themes: list[str] = field(default_factory=list)  # サブテーマ
    theme_expression_method: str = ""  # テーマの表現方法

    def __post_init__(self) -> None:
        """バリデーション"""
        if len(self.unique_selling_points) < 2:
            msg = "独自の強みは2つ以上必要です"
            raise ValueError(msg)
        if not self.core_theme:
            msg = "コアテーマは必須です"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "unique_selling_points": self.unique_selling_points,
            "unique_approaches": self.unique_approaches,
            "avoided_patterns": self.avoided_patterns,
            "core_theme": self.core_theme,
            "sub_themes": self.sub_themes,
            "theme_expression_method": self.theme_expression_method
        }


@dataclass(frozen=True)
class UniquenessEvaluation:
    """独自性評価結果"""

    comparisons: list[GoldenSampleComparison] = field(default_factory=list)  # 比較結果リスト
    overall_uniqueness_score: float = 0.0  # 総合独自性スコア
    theme_consistency_score: float = 0.0  # テーマ一貫性スコア
    differentiation_strategy: DifferentiationStrategy | None = None  # 差別化戦略

    def __post_init__(self) -> None:
        """バリデーションと自動計算"""
        if len(self.comparisons) < 3:
            msg = "3作品以上との比較が必要です"
            raise ValueError(msg)

        # 総合独自性スコアの自動計算（比較結果の平均）
        if self.overall_uniqueness_score == 0.0 and self.comparisons:
            scores = [comp.uniqueness_score for comp in self.comparisons]
            object.__setattr__(self, "overall_uniqueness_score", sum(scores) / len(scores))

    def meets_quality_threshold(
        self,
        uniqueness_threshold: float = 70.0,
        theme_threshold: float = 80.0
    ) -> bool:
        """品質基準を満たしているか判定"""
        return (
            self.overall_uniqueness_score >= uniqueness_threshold and
            self.theme_consistency_score >= theme_threshold
        )

    def get_weakest_differentiation(self) -> GoldenSampleComparison | None:
        """最も差別化が弱い比較結果を取得"""
        if not self.comparisons:
            return None
        return min(self.comparisons, key=lambda c: c.uniqueness_score)

    def get_strongest_differentiation(self) -> GoldenSampleComparison | None:
        """最も差別化が強い比較結果を取得"""
        if not self.comparisons:
            return None
        return max(self.comparisons, key=lambda c: c.uniqueness_score)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "comparisons": [comp.to_dict() for comp in self.comparisons],
            "overall_uniqueness_score": self.overall_uniqueness_score,
            "theme_consistency_score": self.theme_consistency_score,
            "differentiation_strategy": (
                self.differentiation_strategy.to_dict()
                if self.differentiation_strategy else None
            ),
            "meets_quality_threshold": self.meets_quality_threshold()
        }


class GoldenSampleAnalyzer:
    """Golden Sample分析ツール"""

    @staticmethod
    def calculate_uniqueness_score(
        common_elements: list[str],
        differentiation_elements: list[str]
    ) -> float:
        """独自性スコアを計算

        Args:
            common_elements: 共通要素のリスト
            differentiation_elements: 差別化要素のリスト

        Returns:
            独自性スコア（0-100%）
        """
        if not common_elements and not differentiation_elements:
            return 100.0  # 全く異なる作品

        total = len(common_elements) + len(differentiation_elements)
        if total == 0:
            return 0.0

        # 差別化要素の割合をスコアとする
        score = (len(differentiation_elements) / total) * 100

        # 差別化要素が多いほどボーナス
        if len(differentiation_elements) >= 5:
            score = min(100.0, score * 1.2)
        elif len(differentiation_elements) >= 3:
            score = min(100.0, score * 1.1)

        return round(score, 1)

    @staticmethod
    def suggest_differentiation_strategy(
        comparisons: list[GoldenSampleComparison]
    ) -> str:
        """差別化戦略の提案を生成

        Args:
            comparisons: 比較結果のリスト

        Returns:
            差別化戦略の提案テキスト
        """
        weak_points = []
        strong_points = []

        for comp in comparisons:
            if comp.uniqueness_score < 60:
                weak_points.append(f"{comp.sample.title}との差別化")
            elif comp.uniqueness_score > 80:
                strong_points.append(f"{comp.sample.title}に対する独自性")

        suggestions = []

        if weak_points:
            suggestions.append(f"改善が必要な点: {', '.join(weak_points)}")

        if strong_points:
            suggestions.append(f"強みとなる点: {', '.join(strong_points)}")

        if not suggestions:
            suggestions.append("バランスの取れた差別化が実現されています")

        return " / ".join(suggestions)
