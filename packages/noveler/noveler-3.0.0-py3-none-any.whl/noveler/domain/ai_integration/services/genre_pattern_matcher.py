#!/usr/bin/env python3

"""Domain.ai_integration.services.genre_pattern_matcher
Where: Domain service that matches works against genre patterns.
What: Analyses text features to evaluate genre alignment.
Why: Helps AI integration leverage genre benchmarks effectively.
"""

from __future__ import annotations

"""ジャンルパターンマッチャーサービス

ジャンル設定に基づいて類似書籍化作品を検索するドメインサービス
"""


from typing import TYPE_CHECKING, Any

from noveler.domain.ai_integration.entities.published_work import PublishedWork, SuccessLevel

if TYPE_CHECKING:
    from noveler.domain.ai_integration.value_objects.genre_configuration import GenreConfiguration


class GenrePatternMatcher:
    """ジャンルパターンマッチャー

    ジャンル設定に基づいて類似書籍化作品を検索
    """

    def __init__(self) -> None:
        """初期化"""
        self.min_similarity_threshold = 0.5
        self.max_results = 50

    def find_similar_works(
        self,
        genre_config: GenreConfiguration,
        all_works: list[PublishedWork],
        min_success_level: SuccessLevel | None = None,
        max_results: int | None = None,
    ) -> list[PublishedWork]:
        """類似書籍化作品を検索

        Args:
            genre_config: 対象のジャンル設定
            all_works: 全書籍化作品リスト
            min_success_level: 最低成功レベル
            max_results: 最大結果数

        Returns:
            類似書籍化作品のリスト
        """
        if max_results is None:
            max_results = self.max_results

        if min_success_level is None:
            min_success_level = SuccessLevel.C_TIER

        # 条件に一致する作品を抽出
        matching_works = []
        for work in all_works:
            if work.matches_criteria(genre_config, min_success_level):
                similarity = work.genre_config.similarity_score(genre_config)
                if similarity >= self.min_similarity_threshold:
                    matching_works.append((work, similarity))

        # 類似度順にソート
        matching_works.sort(key=lambda x: x[1], reverse=True)

        # 結果を制限
        return [work for work, _ in matching_works[:max_results]]

    def find_exact_matches(
        self, genre_config: GenreConfiguration, all_works: list[PublishedWork]
    ) -> list[PublishedWork]:
        """完全一致するジャンル作品を検索

        Args:
            genre_config: 対象のジャンル設定
            all_works: 全書籍化作品リスト

        Returns:
            完全一致する作品のリスト
        """
        return [
            work
            for work in all_works
            if work.genre_config.matches_genre(
                genre_config.main_genre,
                list(genre_config.sub_genres),
            )
        ]

    def get_genre_statistics(self, genre_config: GenreConfiguration, all_works: list[PublishedWork]) -> dict[str, Any]:
        """ジャンル統計情報を取得

        Args:
            genre_config: 対象のジャンル設定
            all_works: 全書籍化作品リスト

        Returns:
            ジャンル統計情報
        """
        similar_works = self.find_similar_works(genre_config, all_works)

        if not similar_works:
            return {
                "total_works": 0,
                "avg_rating": 0.0,
                "avg_volumes": 0.0,
                "success_distribution": {},
                "avg_first_turning_point": 0.0,
                "romance_introduction_ratio": 0.0,
            }

        # 基本統計
        total_works = len(similar_works)
        avg_rating = sum(work.publication_metrics.ratings for work in similar_works) / total_works
        avg_volumes = sum(work.publication_metrics.volumes_published for work in similar_works) / total_works

        # 成功レベル分布
        success_distribution = {}
        for work in similar_works:
            level = work.get_success_level()
            success_distribution[level.value] = success_distribution.get(level.value, 0) + 1

        # 構造統計
        avg_first_turning_point = sum(work.story_structure.first_turning_point for work in similar_works) / total_works

        early_romance_count = sum(1 for work in similar_works if work.story_structure.has_early_romance())
        romance_introduction_ratio = early_romance_count / total_works

        return {
            "total_works": total_works,
            "avg_rating": avg_rating,
            "avg_volumes": avg_volumes,
            "success_distribution": success_distribution,
            "avg_first_turning_point": avg_first_turning_point,
            "romance_introduction_ratio": romance_introduction_ratio,
        }

    def analyze_competition(self, genre_config: GenreConfiguration, all_works: list[PublishedWork]) -> dict[str, Any]:
        """競合状況を分析

        Args:
            genre_config: 対象のジャンル設定
            all_works: 全書籍化作品リスト

        Returns:
            競合分析結果
        """
        similar_works = self.find_similar_works(genre_config, all_works)

        # 直近3年の作品を抽出
        recent_year_threshold = 2021
        recent_works = [
            work for work in similar_works if work.publication_metrics.publication_year >= recent_year_threshold
        ]

        # 競合密度計算
        competition_density = len(recent_works) / max(len(similar_works), 1)

        # 成功作品の共通要因分析
        success_factors_count = {}
        for work in similar_works:
            if work.get_success_level() in [SuccessLevel.A_TIER, SuccessLevel.S_TIER]:
                for factor in work.success_factors:
                    success_factors_count[factor] = success_factors_count.get(factor, 0) + 1

        # 上位成功要因を抽出
        top_success_factors = sorted(
            success_factors_count.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        return {
            "competition_density": competition_density,
            "recent_works_count": len(recent_works),
            "market_saturation": "高" if competition_density > 0.3 else "中" if competition_density > 0.1 else "低",
            "top_success_factors": [factor for factor, count in top_success_factors],
            "market_opportunity": self._assess_market_opportunity(competition_density, similar_works),
        }

    def _assess_market_opportunity(self, competition_density: float, similar_works: list[PublishedWork]) -> str:
        """市場機会を評価"""
        if competition_density < 0.1:
            return "高い市場機会 - 競合が少なく参入の余地がある"
        if competition_density < 0.3:
            return "中程度の市場機会 - 適度な競合、差別化が重要"
        # 高評価作品の割合をチェック
        high_rated_ratio = sum(1 for work in similar_works if work.publication_metrics.ratings >= 4.0) / len(
            similar_works
        )

        if high_rated_ratio < 0.5:
            return "品質向上による機会 - 競合は多いが品質で差別化可能"
        return "飽和市場 - 革新的な要素が必要"
