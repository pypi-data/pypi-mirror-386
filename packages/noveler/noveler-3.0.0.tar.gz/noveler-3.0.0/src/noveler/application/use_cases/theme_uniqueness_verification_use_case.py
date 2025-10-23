#!/usr/bin/env python3
"""テーマ性・独自性検証ユースケース

A38 STEP 2.5で定義されるテーマ性・独自性検証システムの実装
Golden Sampleとの比較による差別化戦略の提案と品質保証
"""

from dataclasses import dataclass
from pathlib import Path

from noveler.domain.value_objects.golden_samples import (
    DifferentiationStrategy,
    GoldenSample,
    GoldenSampleAnalyzer,
    GoldenSampleComparison,
    UniquenessEvaluation,
)
from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager


@dataclass
class ThemeUniquenessVerificationRequest:
    """テーマ性・独自性検証リクエスト"""

    project_root: Path
    episode_number: int
    plot_content: str
    theme_elements: list[str]
    story_elements: list[str]
    character_descriptions: list[str]


@dataclass
class ThemeUniquenessVerificationResponse:
    """テーマ性・独自性検証レスポンス"""

    success: bool
    uniqueness_evaluation: UniquenessEvaluation | None = None
    theme_consistency_score: float = 0.0
    recommendations: list[str] = None
    error_message: str = ""

    def __post_init__(self) -> None:
        if self.recommendations is None:
            self.recommendations = []


class ThemeUniquenessVerificationUseCase:
    """テーマ性・独自性検証ユースケース

    A38 STEP 2.5の実装として、以下の機能を提供：
    1. Golden Sampleとの比較分析
    2. テーマ一貫性の評価
    3. 独自性スコアの算出
    4. 差別化戦略の提案
    """

    def __init__(self) -> None:
        self.config_manager = get_configuration_manager()
        self.analyzer = GoldenSampleAnalyzer()

    async def execute(self, request: ThemeUniquenessVerificationRequest) -> ThemeUniquenessVerificationResponse:
        """テーマ性・独自性検証を実行

        Args:
            request: 検証リクエスト

        Returns:
            検証結果レスポンス
        """
        try:
            # プロジェクト設定からGolden Samplesを取得
            golden_samples = await self._load_golden_samples(request.project_root)
            if not golden_samples:
                return ThemeUniquenessVerificationResponse(
                    success=False,
                    error_message="Golden Samplesが設定されていません。プロジェクト設定を確認してください。"
                )

            # 各Golden Sampleとの比較分析を実行
            comparisons = []
            for sample in golden_samples:
                comparison = await self._compare_with_golden_sample(
                    sample, request.plot_content, request.theme_elements, request.story_elements
                )
                comparisons.append(comparison)

            # テーマ一貫性スコアを計算
            theme_consistency_score = await self._calculate_theme_consistency(
                request.theme_elements, request.character_descriptions
            )

            # 差別化戦略を生成
            differentiation_strategy = await self._generate_differentiation_strategy(
                comparisons, request.theme_elements
            )

            # 独自性評価を作成
            uniqueness_evaluation = UniquenessEvaluation(
                comparisons=comparisons,
                theme_consistency_score=theme_consistency_score,
                differentiation_strategy=differentiation_strategy
            )

            # 改善提案を生成
            recommendations = await self._generate_recommendations(uniqueness_evaluation)

            return ThemeUniquenessVerificationResponse(
                success=True,
                uniqueness_evaluation=uniqueness_evaluation,
                theme_consistency_score=theme_consistency_score,
                recommendations=recommendations
            )

        except Exception as e:
            return ThemeUniquenessVerificationResponse(
                success=False,
                error_message=f"テーマ性・独自性検証エラー: {e!s}"
            )

    async def _load_golden_samples(self, project_root: Path) -> list[GoldenSample]:
        """プロジェクト設定からGolden Samplesを読み込み"""
        try:
            project_config = self.config_manager.get_project_configuration(project_root)
            if not project_config or "golden_samples" not in project_config:
                return []

            golden_samples = []
            samples_config = project_config["golden_samples"]

            for sample_data in samples_config.values():
                if isinstance(sample_data, dict) and "title" in sample_data:
                    golden_sample = GoldenSample(
                        title=sample_data["title"],
                        url=sample_data["url"],
                        genre=sample_data["genre"],
                        key_features=sample_data.get("key_features", []),
                        reference_aspects=sample_data.get("reference_aspects", []),
                        differentiation_notes=sample_data.get("differentiation_notes", "")
                    )
                    golden_samples.append(golden_sample)

            return golden_samples

        except Exception:
            return []

    async def _compare_with_golden_sample(
        self,
        golden_sample: GoldenSample,
        plot_content: str,
        theme_elements: list[str],
        story_elements: list[str]
    ) -> GoldenSampleComparison:
        """Golden Sampleとの比較分析を実行"""

        # 共通要素を特定
        common_elements = [
            f"「{feature}」要素の類似性"
            for feature in golden_sample.key_features
            if any(feature.lower() in element.lower() for element in story_elements + theme_elements)
        ]

        # 差別化要素を特定
        differentiation_elements = [
            f"独自の{element}要素"
            for element in theme_elements + story_elements
            if not any(feature.lower() in element.lower() for feature in golden_sample.key_features)
        ]

        # プロット内容からの差別化要素を追加
        if "AI" in plot_content.upper() and not any("AI" in feature for feature in golden_sample.key_features):
            differentiation_elements.append("AI/人工知能を核とした物語構造")

        if "現代知識" in plot_content and not any("知識" in feature for feature in golden_sample.key_features):
            differentiation_elements.append("現代知識活用型の独自アプローチ")

        # 独自性スコアを計算
        uniqueness_score = self.analyzer.calculate_uniqueness_score(
            common_elements, differentiation_elements
        )

        # 差別化戦略を提案
        differentiation_strategy = self.analyzer.suggest_differentiation_strategy([])

        return GoldenSampleComparison(
            sample=golden_sample,
            common_elements=common_elements,
            differentiation_elements=differentiation_elements,
            uniqueness_score=uniqueness_score,
            differentiation_strategy=differentiation_strategy
        )

    async def _calculate_theme_consistency(
        self, theme_elements: list[str], character_descriptions: list[str]
    ) -> float:
        """テーマ一貫性スコアを計算"""
        if not theme_elements:
            return 0.0

        consistency_score = 80.0  # ベーススコア

        # テーマ要素の数による加点
        if len(theme_elements) >= 3:
            consistency_score += 10.0
        elif len(theme_elements) >= 2:
            consistency_score += 5.0

        # キャラクターとテーマの整合性チェック
        theme_character_alignment = 0
        for char_desc in character_descriptions:
            for theme in theme_elements:
                if theme.lower() in char_desc.lower():
                    theme_character_alignment += 1

        if theme_character_alignment >= 2:
            consistency_score += 10.0
        elif theme_character_alignment >= 1:
            consistency_score += 5.0

        return min(100.0, consistency_score)

    async def _generate_differentiation_strategy(
        self, comparisons: list[GoldenSampleComparison], theme_elements: list[str]
    ) -> DifferentiationStrategy:
        """差別化戦略を生成"""

        # 独自の強みを抽出
        unique_selling_points = []
        all_differentiation_elements = []
        for comparison in comparisons:
            all_differentiation_elements.extend(comparison.differentiation_elements)

        # 最も頻出する差別化要素を強みとして特定
        element_counts = {}
        for element in all_differentiation_elements:
            element_counts[element] = element_counts.get(element, 0) + 1

        unique_selling_points = [
            element for element, count in element_counts.items()
            if count >= len(comparisons) // 2  # 半数以上の比較で差別化要素となっているもの
        ][:3]  # 上位3つまで

        # 独自アプローチを生成
        unique_approaches = [
            "現代知識と異世界システムの創造的融合",
            "読者の知的好奇心を刺激する段階的情報開示",
            "技術解説と物語進行の自然な統合"
        ]

        # 避けるパターンを特定
        avoided_patterns = [
            "過度な技術解説による物語の停滞",
            "チート能力による安易な問題解決",
            "説教臭い現代価値観の押し付け"
        ]

        # コアテーマを設定
        core_theme = theme_elements[0] if theme_elements else "知識と創造性の価値"

        return DifferentiationStrategy(
            unique_selling_points=unique_selling_points or ["独自の世界観設定", "革新的なキャラクター設計"],
            unique_approaches=unique_approaches,
            avoided_patterns=avoided_patterns,
            core_theme=core_theme,
            sub_themes=theme_elements[1:3] if len(theme_elements) > 1 else [],
            theme_expression_method="各エピソードでテーマを象徴する場面や対話を配置"
        )

    async def _generate_recommendations(self, evaluation: UniquenessEvaluation) -> list[str]:
        """改善提案を生成"""
        recommendations = []

        # 独自性スコアが低い場合の提案
        if evaluation.overall_uniqueness_score < 70.0:
            recommendations.append("独自性スコアが基準値を下回っています。差別化要素の強化を検討してください。")

            # 最も弱い差別化の比較結果から具体的提案
            weakest = evaluation.get_weakest_differentiation()
            if weakest:
                recommendations.append(
                    f"「{weakest.sample.title}」との差別化が不十分です。"
                    f"特に{weakest.sample.key_features[:2]}要素の差別化を強化してください。"
                )

        # テーマ一貫性が低い場合の提案
        if evaluation.theme_consistency_score < 80.0:
            recommendations.append("テーマ一貫性の向上が必要です。キャラクターの行動や対話でテーマをより明確に表現してください。")

        # 品質基準を満たしている場合の確認
        if evaluation.meets_quality_threshold():
            recommendations.append("品質基準を満たしています。現在の方向性で執筆を続けてください。")

        # 差別化戦略に基づく具体的提案
        if evaluation.differentiation_strategy:
            recommendations.append(
                f"コアテーマ「{evaluation.differentiation_strategy.core_theme}」を"
                f"{evaluation.differentiation_strategy.theme_expression_method}で表現してください。"
            )

        return recommendations if recommendations else ["検証が完了しました。現在の品質を維持してください。"]


        # ファクトリーメソッド
def create_theme_uniqueness_verification_use_case() -> ThemeUniquenessVerificationUseCase:
        """テーマ性・独自性検証ユースケースを作成"""
        return ThemeUniquenessVerificationUseCase()
