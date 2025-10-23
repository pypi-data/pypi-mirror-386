#!/usr/bin/env python3

"""Domain.ai_integration.services.published_work_analyzer
Where: Domain service aggregating analyses across published benchmark works.
What: Compares AI-generated outputs to reference works and generates insights.
Why: Provides higher-level benchmarking capabilities for AI integration features.
"""

from __future__ import annotations

"""書籍化作品分析サービス

書籍化作品との比較分析を行うドメインサービス
"""


from typing import TYPE_CHECKING, Any

from noveler.domain.ai_integration.value_objects.genre_benchmark_result import (
    ComparisonStatus,
    GenreBenchmarkResult,
    ImprovementSuggestion,
    PublicationReadiness,
    StructuralComparison,
)

if TYPE_CHECKING:
    from noveler.domain.ai_integration.entities.published_work import PublishedWork
    from noveler.domain.ai_integration.value_objects.genre_configuration import GenreConfiguration


class PublishedWorkAnalyzer:
    """書籍化作品分析サービス

    ユーザーのプロットデータを書籍化作品と比較分析
    """

    def __init__(self) -> None:
        """初期化"""
        self.critical_threshold = 0.3
        self.warning_threshold = 0.6
        self.excellent_threshold = 0.8

    def analyze_against_published_works(
        self, user_plot_data: dict[str, Any], similar_works: list[PublishedWork], genre_config: GenreConfiguration
    ) -> GenreBenchmarkResult:
        """書籍化作品との比較分析

        Args:
            user_plot_data: ユーザーのプロットデータ
            similar_works: 類似書籍化作品リスト
            genre_config: ジャンル設定

        Returns:
            比較分析結果
        """
        if not similar_works:
            msg = "比較対象となる書籍化作品がありません"
            raise ValueError(msg)

        # 構造的比較の実行
        structural_comparisons = self._perform_structural_comparison(
            user_plot_data,
            similar_works,
        )

        # 改善提案の生成
        improvement_suggestions = self._generate_improvement_suggestions(
            structural_comparisons,
            similar_works,
        )

        # 書籍化準備度の評価
        publication_readiness = self._evaluate_publication_readiness(
            structural_comparisons,
            similar_works,
        )

        # 参考作品の選定
        reference_works = self._select_reference_works(similar_works)

        return GenreBenchmarkResult(
            genre_config=genre_config,
            comparison_target_count=len(similar_works),
            structural_comparisons=structural_comparisons,
            improvement_suggestions=improvement_suggestions,
            publication_readiness=publication_readiness,
            reference_works=reference_works,
        )

    def _perform_structural_comparison(
        self, user_plot_data: dict[str, Any], similar_works: list[PublishedWork]
    ) -> list[StructuralComparison]:
        """構造的比較の実行"""
        comparisons = []

        # 第1転換点の比較
        user_turning_point = self._extract_turning_point(user_plot_data)
        turning_point_comparison = self._compare_turning_point(
            user_turning_point,
            similar_works,
        )

        comparisons.append(turning_point_comparison)

        # 恋愛要素の比較
        user_romance = self._extract_romance_element(user_plot_data)
        romance_comparison = self._compare_romance_element(
            user_romance,
            similar_works,
        )

        comparisons.append(romance_comparison)

        # 中ボス戦の比較
        user_mid_boss = self._extract_mid_boss_battle(user_plot_data)
        mid_boss_comparison = self._compare_mid_boss_battle(
            user_mid_boss,
            similar_works,
        )

        comparisons.append(mid_boss_comparison)

        # 全体構成の比較
        user_total_episodes = self._extract_total_episodes(user_plot_data)
        total_episodes_comparison = self._compare_total_episodes(
            user_total_episodes,
            similar_works,
        )

        comparisons.append(total_episodes_comparison)

        return comparisons

    def _extract_turning_point(self, user_plot_data: dict[str, Any]) -> int:
        """ユーザーデータから第1転換点を抽出"""
        structure = user_plot_data.get("structure", {})
        return structure.get("first_turning_point", 0)

    def _extract_romance_element(self, user_plot_data: dict[str, Any]) -> int:
        """ユーザーデータから恋愛要素導入時期を抽出"""
        structure = user_plot_data.get("structure", {})
        return structure.get("romance_introduction", 0)

    def _extract_mid_boss_battle(self, user_plot_data: dict[str, Any]) -> int:
        """ユーザーデータから中ボス戦時期を抽出"""
        structure = user_plot_data.get("structure", {})
        return structure.get("mid_boss_battle", 0)

    def _extract_total_episodes(self, user_plot_data: dict[str, Any]) -> int:
        """ユーザーデータから総話数を抽出"""
        structure = user_plot_data.get("structure", {})
        return structure.get("total_episodes", 0)

    def _compare_turning_point(self, user_value: int, similar_works: list[PublishedWork]) -> StructuralComparison:
        """第1転換点の比較"""
        if user_value == 0:
            return StructuralComparison(
                aspect="第1転換点",
                user_value="未設定",
                benchmark_value="第1-5話",
                conformity_rate=0.0,
                status=ComparisonStatus.CRITICAL,
            )

        # 書籍化作品の平均値を計算
        avg_turning_point = sum(work.story_structure.first_turning_point for work in similar_works) / len(similar_works)

        # 適合率を計算(理想値から離れているほど低い)
        ideal_range = (1, 5)
        if ideal_range[0] <= user_value <= ideal_range[1]:
            conformity_rate = 1.0
            status = ComparisonStatus.EXCELLENT
        elif user_value <= ideal_range[1] + 2:
            conformity_rate = 0.7
            status = ComparisonStatus.GOOD
        elif user_value <= ideal_range[1] + 5:
            conformity_rate = 0.4
            status = ComparisonStatus.WARNING
        else:
            conformity_rate = 0.1
            status = ComparisonStatus.CRITICAL

        return StructuralComparison(
            aspect="第1転換点",
            user_value=f"第{user_value}話",
            benchmark_value=f"第{avg_turning_point}話",
            conformity_rate=conformity_rate,
            status=status,
        )

    def _compare_romance_element(self, user_value: int, similar_works: list[PublishedWork]) -> StructuralComparison:
        """恋愛要素の比較"""
        if user_value == 0:
            return StructuralComparison(
                aspect="恋愛要素導入",
                user_value="未設定",
                benchmark_value="第8-12話",
                conformity_rate=0.0,
                status=ComparisonStatus.CRITICAL,
            )

        # 書籍化作品での恋愛要素導入率を計算
        early_romance_count = sum(1 for work in similar_works if work.story_structure.has_early_romance())
        early_romance_rate = early_romance_count / len(similar_works)

        # 適合率を計算
        if user_value <= 12:
            conformity_rate = early_romance_rate
            status = ComparisonStatus.EXCELLENT if conformity_rate > 0.7 else ComparisonStatus.GOOD
        elif user_value <= 20:
            conformity_rate = early_romance_rate * 0.7
            status = ComparisonStatus.WARNING
        else:
            conformity_rate = early_romance_rate * 0.3
            status = ComparisonStatus.CRITICAL

        return StructuralComparison(
            aspect="恋愛要素導入",
            user_value=f"第{user_value}話",
            benchmark_value=f"第8-12話({early_romance_rate:.0%})",
            conformity_rate=conformity_rate,
            status=status,
        )

    def _compare_mid_boss_battle(self, user_value: int, similar_works: list[PublishedWork]) -> StructuralComparison:
        """中ボス戦の比較"""
        if user_value == 0:
            return StructuralComparison(
                aspect="中ボス戦",
                user_value="未設定",
                benchmark_value="第15-20話",
                conformity_rate=0.0,
                status=ComparisonStatus.WARNING,
            )

        # 書籍化作品の平均値を計算
        avg_mid_boss = sum(work.story_structure.mid_boss_battle for work in similar_works) / len(similar_works)

        # 適合率を計算
        ideal_range = (15, 20)
        if ideal_range[0] <= user_value <= ideal_range[1]:
            conformity_rate = 1.0
            status = ComparisonStatus.EXCELLENT
        elif abs(user_value - avg_mid_boss) <= 5:
            conformity_rate = 0.7
            status = ComparisonStatus.GOOD
        else:
            conformity_rate = 0.4
            status = ComparisonStatus.WARNING

        return StructuralComparison(
            aspect="中ボス戦",
            user_value=f"第{user_value}話",
            benchmark_value=f"第{avg_mid_boss}話",
            conformity_rate=conformity_rate,
            status=status,
        )

    def _compare_total_episodes(self, user_value: int, similar_works: list[PublishedWork]) -> StructuralComparison:
        """総話数の比較"""
        if user_value == 0:
            return StructuralComparison(
                aspect="総話数",
                user_value="未設定",
                benchmark_value="20-30話",
                conformity_rate=0.0,
                status=ComparisonStatus.WARNING,
            )

        # 書籍化作品の平均値を計算
        avg_total = sum(work.story_structure.total_episodes for work in similar_works) / len(similar_works)

        # 適合率を計算
        if 20 <= user_value <= 30:
            conformity_rate = 1.0
            status = ComparisonStatus.EXCELLENT
        elif 15 <= user_value <= 40:
            conformity_rate = 0.7
            status = ComparisonStatus.GOOD
        else:
            conformity_rate = 0.4
            status = ComparisonStatus.WARNING

        return StructuralComparison(
            aspect="総話数",
            user_value=f"{user_value}話",
            benchmark_value=f"{avg_total}話",
            conformity_rate=conformity_rate,
            status=status,
        )

    def _generate_improvement_suggestions(
        self, comparisons: list[StructuralComparison], similar_works: list[PublishedWork]
    ) -> list[ImprovementSuggestion]:
        """改善提案の生成"""
        suggestions = []

        # 致命的な問題から改善提案を生成
        for comparison in comparisons:
            if comparison.status == ComparisonStatus.CRITICAL:
                suggestion = self._create_suggestion_for_critical_issue(
                    comparison,
                    similar_works,
                )

                suggestions.append(suggestion)

        # 警告レベルの問題から改善提案を生成
        for comparison in comparisons:
            if comparison.status == ComparisonStatus.WARNING:
                suggestion = self._create_suggestion_for_warning_issue(
                    comparison,
                    similar_works,
                )

                suggestions.append(suggestion)

        return suggestions

    def _create_suggestion_for_critical_issue(
        self, comparison: StructuralComparison, similar_works: list[PublishedWork]
    ) -> ImprovementSuggestion:
        """致命的問題の改善提案"""
        # 成功作品から参考作品を選定
        reference_work = self._select_best_reference_work(similar_works)

        suggestion_map = {
            "第1転換点": ImprovementSuggestion(
                priority="高",
                description="第1-5話以内に大きな転換点を設定してください",
                reference_work=reference_work,
                expected_impact="読者の初期離脱を防ぎ、継続率を向上",
            ),
            "恋愛要素導入": ImprovementSuggestion(
                priority="高",
                description="第8-12話以内に恋愛要素を導入してください",
                reference_work=reference_work,
                expected_impact="読者の感情移入を促進し、継続率を向上",
            ),
        }

        return suggestion_map.get(
            comparison.aspect,
            ImprovementSuggestion(
                priority="高",
                description=f"{comparison.aspect}の改善が必要です",
                reference_work=reference_work,
                expected_impact="書籍化可能性の向上",
            ),
        )

    def _create_suggestion_for_warning_issue(
        self, comparison: StructuralComparison, similar_works: list[PublishedWork]
    ) -> ImprovementSuggestion:
        """警告レベル問題の改善提案"""
        reference_work = self._select_best_reference_work(similar_works)

        return ImprovementSuggestion(
            priority="中",
            description=f"{comparison.aspect}の調整を検討してください",
            reference_work=reference_work,
            expected_impact="市場適合度の向上",
        )

    def _select_best_reference_work(self, similar_works: list[PublishedWork]) -> str:
        """最適な参考作品を選定"""
        # 最も成功している作品を選定
        best_work = max(
            similar_works,
            key=lambda w: (
                self._calculate_popularity_score(w),
                w.publication_metrics.ratings,
            ),
        )

        return best_work.title

    def _evaluate_publication_readiness(
        self, comparisons: list[StructuralComparison], _similar_works: list[PublishedWork]
    ) -> PublicationReadiness:
        """書籍化準備度の評価"""
        # 全体適合率を計算
        overall_conformity = sum(c.conformity_rate for c in comparisons) / len(comparisons)

        # 致命的ギャップを特定
        critical_gaps = [c.aspect for c in comparisons if c.status == ComparisonStatus.CRITICAL]

        # 競合優位性を特定
        competitive_advantages = [c.aspect for c in comparisons if c.status == ComparisonStatus.EXCELLENT]

        # 成功確率を計算
        success_probability = overall_conformity * (1 - len(critical_gaps) * 0.2)
        success_probability = max(0.0, min(1.0, success_probability))

        return PublicationReadiness(
            readiness_score=overall_conformity,
            success_probability=success_probability,
            critical_gaps=critical_gaps,
            competitive_advantages=competitive_advantages,
        )

    def _select_reference_works(self, similar_works: list[PublishedWork]) -> list[str]:
        """参考作品の選定"""
        # 成功レベルと評価順にソート
        sorted_works = sorted(
            similar_works,
            key=lambda w: (
                self._calculate_popularity_score(w),
                w.publication_metrics.ratings,
            ),
            reverse=True,
        )

        # 上位5作品を選定
        return [work.title for work in sorted_works[:5]]

    def _calculate_popularity_score(self, work: PublishedWork) -> float:
        """出版メトリクスから人気スコアを算出するヘルパー。

        巻数・PV・ブックマーク・レビュー・評価を0.0-1.0レンジで正規化し、
        書籍化成功度合いを近似する重み付け平均を返す。
        """

        metrics = work.publication_metrics

        volumes = min(metrics.volumes_published / 12, 1.0)
        pv = min(metrics.total_pv / 1_500_000, 1.0)
        bookmarks = min(metrics.bookmarks / 50_000, 1.0)
        ratings = metrics.ratings / 5.0
        reviews = min(metrics.reviews_count / 1_000, 1.0)

        score = (
            volumes * 0.2
            + pv * 0.25
            + bookmarks * 0.15
            + ratings * 0.25
            + reviews * 0.15
        )

        # 浮動小数点誤差を吸収
        return max(0.0, min(1.0, score))
