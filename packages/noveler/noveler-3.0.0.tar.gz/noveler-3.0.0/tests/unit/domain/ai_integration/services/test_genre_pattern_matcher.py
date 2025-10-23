#!/usr/bin/env python3
"""GenrePatternMatcherサービスのユニットテスト

TDD原則に従い、ジャンルパターンマッチングのビジネスロジックをテスト


仕様書: SPEC-INTEGRATION
"""

import pytest

from noveler.domain.ai_integration.entities.published_work import (
    PublicationMetrics,
    PublishedWork,
    StoryStructure,
    SuccessLevel,
)
from noveler.domain.ai_integration.services.genre_pattern_matcher import GenrePatternMatcher
from noveler.domain.ai_integration.value_objects.genre_configuration import (
    GenreConfiguration,
    MainGenre,
    SubGenre,
    TargetFormat,
)


class TestGenrePatternMatcher:
    """GenrePatternMatcherのテスト"""

    @pytest.fixture
    def matcher(self):
        """GenrePatternMatcherのフィクスチャ"""
        return GenrePatternMatcher()

    @pytest.fixture
    def sample_genre_config(self):
        """サンプルジャンル設定"""
        return GenreConfiguration(
            main_genre=MainGenre.FANTASY,
            sub_genres={SubGenre.ISEKAI, SubGenre.SCHOOL},
            target_format=TargetFormat.LIGHT_NOVEL,
        )

    @pytest.fixture
    def sample_works(self):
        """サンプル書籍化作品リスト"""
        # 完全一致する作品
        work1 = PublishedWork(
            work_id="work_001",
            title="異世界学園の英雄",
            author="作者A",
            publication_metrics=PublicationMetrics(
                publication_year=2022,
                volumes_published=10,
                total_pv=1000000,
                bookmarks=50000,
                ratings=4.5,
                reviews_count=1000,
            ),
            story_structure=StoryStructure(
                first_turning_point=20,
                romance_introduction=30,
                mid_boss_battle=100,
                climax_point=180,
                total_episodes=200,
            ),
            genre_config=GenreConfiguration(
                main_genre=MainGenre.FANTASY,
                sub_genres={SubGenre.ISEKAI, SubGenre.SCHOOL},
                target_format=TargetFormat.LIGHT_NOVEL,
            ),
            success_factors=["魅力的な主人公", "独創的な世界観"],
        )

        # 部分一致する作品
        work2 = PublishedWork(
            work_id="work_002",
            title="魔法学園の日常",
            author="作者B",
            publication_metrics=PublicationMetrics(
                publication_year=2021,
                volumes_published=5,
                total_pv=500000,
                bookmarks=25000,
                ratings=4.0,
                reviews_count=500,
            ),
            story_structure=StoryStructure(
                first_turning_point=15,
                romance_introduction=25,
                mid_boss_battle=50,
                climax_point=80,
                total_episodes=100,
            ),
            genre_config=GenreConfiguration(
                main_genre=MainGenre.FANTASY,
                sub_genres={SubGenre.ISEKAI, SubGenre.SCHOOL, SubGenre.MAGIC},
                target_format=TargetFormat.LIGHT_NOVEL,
            ),
            success_factors=["学園設定", "日常描写"],
        )

        # 異なるジャンルの作品
        work3 = PublishedWork(
            work_id="work_003",
            title="推理小説の名探偵",
            author="作者C",
            publication_metrics=PublicationMetrics(
                publication_year=2020,
                volumes_published=3,
                total_pv=300000,
                bookmarks=15000,
                ratings=3.5,
                reviews_count=300,
            ),
            story_structure=StoryStructure(
                first_turning_point=10,
                romance_introduction=51,  # ロマンスなし(総話数より大きい値)
                mid_boss_battle=25,
                climax_point=40,
                total_episodes=50,
            ),
            genre_config=GenreConfiguration(
                main_genre=MainGenre.MYSTERY,
                sub_genres={SubGenre.ACTION},
                target_format=TargetFormat.WEB_NOVEL,
            ),
            success_factors=["緻密なプロット"],
        )

        return [work1, work2, work3]

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-INITIALIZE_MATCHER")
    def test_initialize_matcher(self, matcher: object) -> None:
        """マッチャーの初期化"""
        assert matcher.min_similarity_threshold == 0.5
        assert matcher.max_results == 50

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-FIND_SIMILAR_WORKS_B")
    def test_find_similar_works_basic(self, matcher: object, sample_genre_config: object, sample_works: object) -> None:
        """類似作品の基本検索"""
        # Debug: 類似度を確認
        for work in sample_works:
            if work.genre_config.main_genre == sample_genre_config.main_genre:
                sim = work.genre_config.similarity_score(sample_genre_config)
                print(f"{work.title}: similarity = {sim}")

        # When
        similar_works = matcher.find_similar_works(sample_genre_config, sample_works)

        # Then
        # work2のサブジャンルは{ISEKAI, SCHOOL, MAGIC}、検索は{ISEKAI, SCHOOL}なので
        # 交差は{ISEKAI, SCHOOL}、和集合は{ISEKAI, SCHOOL, MAGIC}で2/3 = 0.66...
        # これは0.5以上なので含まれる
        assert len(similar_works) == 2  # work1とwork2が類似
        assert sample_works[0] in similar_works  # 完全一致
        assert sample_works[1] in similar_works  # 部分一致(類似度0.66)
        assert sample_works[2] not in similar_works  # 異なるジャンル

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-FIND_SIMILAR_WORKS_W")
    def test_find_similar_works_with_min_success_level(
        self, matcher: object, sample_genre_config: object, sample_works: object
    ) -> None:
        """成功レベルフィルタ付き検索"""
        # When
        similar_works = matcher.find_similar_works(
            sample_genre_config, sample_works, min_success_level=SuccessLevel.A_TIER
        )

        # Then
        # work1のみがA_TIER以上(ratings 4.5)
        assert len(similar_works) == 1
        assert similar_works[0].work_id == "work_001"

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-FIND_SIMILAR_WORKS_W")
    def test_find_similar_works_with_max_results(
        self, matcher: object, sample_genre_config: object, sample_works: object
    ) -> None:
        """結果数制限付き検索"""
        # When
        similar_works = matcher.find_similar_works(sample_genre_config, sample_works, max_results=1)

        # Then
        assert len(similar_works) == 1
        # 最も類似度の高い作品が返される
        assert similar_works[0].work_id == "work_001"

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-FIND_EXACT_MATCHES")
    def test_find_exact_matches(self, matcher: object, sample_genre_config: object, sample_works: object) -> None:
        """完全一致検索"""
        # When
        exact_matches = matcher.find_exact_matches(sample_genre_config, sample_works)

        # Then
        assert len(exact_matches) == 1
        assert exact_matches[0].work_id == "work_001"
        # work2は部分一致なので含まれない

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-GET_GENRE_STATISTICS")
    def test_get_genre_statistics_with_works(
        self, matcher: object, sample_genre_config: object, sample_works: object
    ) -> None:
        """ジャンル統計情報の取得(作品あり)"""
        # When
        stats = matcher.get_genre_statistics(sample_genre_config, sample_works)

        # Then
        assert stats["total_works"] == 2
        assert stats["avg_rating"] == 4.25  # (4.5 + 4.0) / 2
        assert stats["avg_volumes"] == 7.5  # (10 + 5) / 2
        assert stats["avg_first_turning_point"] == 17.5  # (20 + 15) / 2
        assert stats["romance_introduction_ratio"] == 1.0  # 両作品ともロマンスあり
        assert SuccessLevel.S_TIER.value in stats["success_distribution"]  # work1
        assert SuccessLevel.B_TIER.value in stats["success_distribution"]  # work2

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-GET_GENRE_STATISTICS")
    def test_get_genre_statistics_no_works(self, matcher: object, sample_genre_config: object) -> None:
        """ジャンル統計情報の取得(作品なし)"""
        # When
        stats = matcher.get_genre_statistics(sample_genre_config, [])

        # Then
        assert stats["total_works"] == 0
        assert stats["avg_rating"] == 0.0
        assert stats["avg_volumes"] == 0.0
        assert stats["success_distribution"] == {}
        assert stats["avg_first_turning_point"] == 0.0
        assert stats["romance_introduction_ratio"] == 0.0

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-ANALYZE_COMPETITION_")
    def test_analyze_competition_with_recent_works(
        self, matcher: object, sample_genre_config: object, sample_works: object
    ) -> None:
        """競合分析(最近の作品あり)"""
        # When
        analysis = matcher.analyze_competition(sample_genre_config, sample_works)

        # Then
        assert "competition_density" in analysis
        assert "recent_works_count" in analysis
        assert "market_saturation" in analysis
        assert "top_success_factors" in analysis
        assert "market_opportunity" in analysis

        # 2021年以降の作品は2つ
        assert analysis["recent_works_count"] == 2
        assert analysis["competition_density"] == 1.0  # 2/2
        assert analysis["market_saturation"] == "高"

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-ANALYZE_COMPETITION_")
    def test_analyze_competition_success_factors(
        self, matcher: object, sample_genre_config: object, sample_works: object
    ) -> None:
        """競合分析の成功要因抽出"""
        # When
        analysis = matcher.analyze_competition(sample_genre_config, sample_works)

        # Then
        top_factors = analysis["top_success_factors"]
        assert isinstance(top_factors, list)
        # A_TIER以上の作品の成功要因が含まれる
        assert "魅力的な主人公" in top_factors or "独創的な世界観" in top_factors

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-ASSESS_MARKET_OPPORT")
    def test_assess_market_opportunity_low_density(self, matcher: object) -> None:
        """市場機会評価(低競合密度)"""
        # Given
        similar_works = []  # 空のリスト

        # When
        opportunity = matcher._assess_market_opportunity(0.05, similar_works)

        # Then
        assert "高い市場機会" in opportunity

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-ASSESS_MARKET_OPPORT")
    def test_assess_market_opportunity_medium_density(self, matcher: object, sample_works: object) -> None:
        """市場機会評価(中競合密度)"""
        # When
        opportunity = matcher._assess_market_opportunity(0.2, sample_works[:2])

        # Then
        assert "中程度の市場機会" in opportunity

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-ASSESS_MARKET_OPPORT")
    def test_assess_market_opportunity_high_density_low_quality(self, matcher: object, sample_works: object) -> None:
        """市場機会評価(高競合密度・低品質)"""
        # Given
        # 低評価作品を追加
        low_quality_works = [
            PublishedWork(
                work_id=f"low_{i}",
                title=f"低評価作品{i}",
                author=f"作者{i}",
                publication_metrics=PublicationMetrics(
                    publication_year=2023,
                    volumes_published=1,
                    total_pv=10000,
                    bookmarks=500,
                    ratings=3.0,
                    reviews_count=100,
                ),
                story_structure=StoryStructure(
                    first_turning_point=10,
                    romance_introduction=20,
                    mid_boss_battle=25,
                    climax_point=40,
                    total_episodes=50,
                ),
                genre_config=sample_works[0].genre_config,
                success_factors=["標準的な構成"],
            )
            for i in range(3)
        ]

        # When
        opportunity = matcher._assess_market_opportunity(0.5, low_quality_works)

        # Then
        assert "品質向上による機会" in opportunity

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-ASSESS_MARKET_OPPORT")
    def test_assess_market_opportunity_saturated_market(self, matcher: object, sample_works: object) -> None:
        """市場機会評価(飽和市場)"""
        # Given
        # 高評価作品のみ
        high_quality_works = [sample_works[0]] * 5  # work1を5つ複製

        # When
        opportunity = matcher._assess_market_opportunity(0.5, high_quality_works)

        # Then
        assert "飽和市場" in opportunity

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-FIND_SIMILAR_WORKS_E")
    def test_find_similar_works_empty_list(self, matcher: object, sample_genre_config: object) -> None:
        """空のリストでの類似作品検索"""
        # When
        similar_works = matcher.find_similar_works(sample_genre_config, [])

        # Then
        assert similar_works == []

    @pytest.mark.spec("SPEC-GENRE_PATTERN_MATCHER-FIND_SIMILAR_WORKS_N")
    def test_find_similar_works_no_matches(self, matcher: object) -> None:
        """一致する作品がない場合の検索"""
        # Given
        mystery_config = GenreConfiguration(
            main_genre=MainGenre.MYSTERY,
            sub_genres={SubGenre.ACTION},
            target_format=TargetFormat.WEB_NOVEL,
        )

        fantasy_work = PublishedWork(
            work_id="fantasy_001",
            title="ファンタジー作品",
            author="作者F",
            publication_metrics=PublicationMetrics(
                publication_year=2023,
                volumes_published=5,
                total_pv=500000,
                bookmarks=25000,
                ratings=4.0,
                reviews_count=500,
            ),
            story_structure=StoryStructure(
                first_turning_point=20,
                romance_introduction=30,
                mid_boss_battle=50,
                climax_point=80,
                total_episodes=100,
            ),
            genre_config=GenreConfiguration(
                main_genre=MainGenre.FANTASY,
                sub_genres={SubGenre.MAGIC},
                target_format=TargetFormat.LIGHT_NOVEL,
            ),
            success_factors=["標準的な構成"],
        )

        # When
        similar_works = matcher.find_similar_works(mystery_config, [fantasy_work])

        # Then
        assert similar_works == []
