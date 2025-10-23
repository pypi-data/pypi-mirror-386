#!/usr/bin/env python3
"""ジャンル比較分析ドメインのユニットテスト

TDD+DDD原則に基づく失敗するテストから開始
実行時間目標: < 0.1秒/テスト


仕様書: SPEC-INTEGRATION
"""

from datetime import datetime, timezone

import pytest

from noveler.domain.ai_integration.entities.published_work import (
    PublicationMetrics,
    PublishedWork,
    StoryStructure,
    SuccessLevel,
)
from noveler.domain.ai_integration.services.genre_pattern_matcher import GenrePatternMatcher
from noveler.domain.ai_integration.services.published_work_analyzer import PublishedWorkAnalyzer
from noveler.domain.ai_integration.value_objects.genre_benchmark_result import (
    ComparisonStatus,
    GenreBenchmarkResult,
    ImprovementSuggestion,
    PublicationReadiness,
    StructuralComparison,
)
from noveler.domain.ai_integration.value_objects.genre_configuration import (
    GenreConfiguration,
    MainGenre,
    SubGenre,
    TargetFormat,
)


class TestGenreComparativeAnalysisDomain:
    """ジャンル比較分析ドメインのテストスイート"""

    # =================================================================
    # RED Phase: 失敗するテストを先に書く
    # =================================================================

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-GENRE_CONFIGURATION_")
    def test_genre_configuration_creation(self) -> None:
        """ジャンル設定の作成"""
        config = GenreConfiguration(
            main_genre=MainGenre.FANTASY,
            sub_genres=[SubGenre.ISEKAI, SubGenre.SCHOOL],
            target_format=TargetFormat.LIGHT_NOVEL,
        )

        assert config.main_genre == MainGenre.FANTASY
        assert len(config.sub_genres) == 2
        assert config.target_format == TargetFormat.LIGHT_NOVEL
        assert config.get_genre_combination() == "ファンタジー×異世界×学園"

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-GENRE_CONFIGURATION_")
    def test_genre_configuration_validation(self) -> None:
        """ジャンル設定の検証"""
        # サブジャンルが空の場合はエラー
        with pytest.raises(ValueError, match="サブジャンルは1つ以上"):
            GenreConfiguration(
                main_genre=MainGenre.FANTASY,
                sub_genres=[],
                target_format=TargetFormat.LIGHT_NOVEL,
            )

        # サブジャンルが5つ超の場合はエラー
        with pytest.raises(ValueError, match="サブジャンルは5つまで"):
            GenreConfiguration(
                main_genre=MainGenre.FANTASY,
                sub_genres=[
                    SubGenre.ISEKAI,
                    SubGenre.SCHOOL,
                    SubGenre.MAGIC,
                    SubGenre.ROMANCE,
                    SubGenre.COMEDY,
                    SubGenre.ACTION,
                ],
                target_format=TargetFormat.LIGHT_NOVEL,
            )

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-GENRE_SIMILARITY_CAL")
    def test_genre_similarity_calculation(self) -> None:
        """ジャンル類似度計算"""
        config1 = GenreConfiguration(
            main_genre=MainGenre.FANTASY,
            sub_genres=[SubGenre.ISEKAI, SubGenre.SCHOOL],
            target_format=TargetFormat.LIGHT_NOVEL,
        )

        config2 = GenreConfiguration(
            main_genre=MainGenre.FANTASY,
            sub_genres=[SubGenre.ISEKAI, SubGenre.MAGIC],
            target_format=TargetFormat.LIGHT_NOVEL,
        )

        # 1つ共通、合計3つ → 1/3 = 0.33...
        similarity = config1.similarity_score(config2)
        assert abs(similarity - 0.333333) < 0.0001

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-PUBLISHED_WORK_CREAT")
    def test_published_work_creation(self) -> None:
        """書籍化作品の作成"""
        genre_config = GenreConfiguration(
            main_genre=MainGenre.FANTASY,
            sub_genres=[SubGenre.ISEKAI],
            target_format=TargetFormat.LIGHT_NOVEL,
        )

        metrics = PublicationMetrics(
            publication_year=2023,
            volumes_published=5,
            total_pv=1000000,
            bookmarks=10000,
            ratings=4.2,
            reviews_count=500,
        )

        structure = StoryStructure(
            first_turning_point=3,
            romance_introduction=8,
            mid_boss_battle=15,
            climax_point=20,
            total_episodes=25,
        )

        work = PublishedWork(
            work_id="work_001",
            title="異世界魔法学園",
            author="テスト作者",
            genre_config=genre_config,
            publication_metrics=metrics,
            story_structure=structure,
            success_factors=["独自世界観", "キャラクター魅力"],
        )

        assert work.work_id == "work_001"
        assert work.get_success_level() == SuccessLevel.B_TIER
        assert work.story_structure.get_pacing_ratio() == 0.12  # 3/25

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-PUBLICATION_METRICS_")
    def test_publication_metrics_success_level(self) -> None:
        """出版メトリクスの成功レベル判定"""
        # C級: 基本的な書籍化
        metrics_c = PublicationMetrics(
            publication_year=2023,
            volumes_published=3,
            total_pv=500000,
            bookmarks=5000,
            ratings=3.8,
            reviews_count=200,
        )

        assert metrics_c.get_success_level() == SuccessLevel.C_TIER

        # B級: 5巻以上
        metrics_b = PublicationMetrics(
            publication_year=2023,
            volumes_published=7,
            total_pv=800000,
            bookmarks=8000,
            ratings=4.1,
            reviews_count=400,
        )

        assert metrics_b.get_success_level() == SuccessLevel.B_TIER

        # A級: 10巻以上
        metrics_a = PublicationMetrics(
            publication_year=2022,
            volumes_published=12,
            total_pv=1500000,
            bookmarks=15000,
            ratings=4.3,
            reviews_count=800,
        )

        assert metrics_a.get_success_level() == SuccessLevel.A_TIER

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-STORY_STRUCTURE_VALI")
    def test_story_structure_validation(self) -> None:
        """物語構造の検証"""
        # 転換点が1話より前は無効
        with pytest.raises(ValueError, match="第1転換点は1話以降"):
            StoryStructure(
                first_turning_point=0,
                romance_introduction=8,
                mid_boss_battle=15,
                climax_point=20,
                total_episodes=25,
            )

        # クライマックスが転換点より前は無効
        with pytest.raises(ValueError, match="クライマックスは第1転換点より後"):
            StoryStructure(
                first_turning_point=15,
                romance_introduction=8,
                mid_boss_battle=10,
                climax_point=10,
                total_episodes=25,
            )

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-STRUCTURAL_COMPARISO")
    def test_structural_comparison_creation(self) -> None:
        """構造的比較の作成"""
        comparison = StructuralComparison(
            aspect="転換点タイミング",
            user_value="第8話",
            benchmark_value="第4-6話",
            conformity_rate=0.6,
            status=ComparisonStatus.WARNING,
        )

        assert comparison.aspect == "転換点タイミング"
        assert comparison.conformity_rate == 0.6
        assert comparison.is_problematic()
        assert comparison.get_severity_score() == 3

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-IMPROVEMENT_SUGGESTI")
    def test_improvement_suggestion_priority(self) -> None:
        """改善提案の優先度"""
        high_priority = ImprovementSuggestion(
            priority="高",
            description="恋愛要素を第6話までに導入",
            reference_work="魔法科高校の劣等生",
            expected_impact="読者の感情移入促進",
        )

        assert high_priority.is_high_priority()

        low_priority = ImprovementSuggestion(
            priority="低",
            description="サブキャラクターの描写強化",
            reference_work=None,
            expected_impact="世界観の深化",
        )

        assert not low_priority.is_high_priority()

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-PUBLICATION_READINES")
    def test_publication_readiness_grading(self) -> None:
        """書籍化準備度のグレード判定"""
        # A級: 80%以上
        readiness_a = PublicationReadiness(
            readiness_score=0.85,
            success_probability=0.78,
            critical_gaps=[],
            competitive_advantages=["独自設定", "キャラクター魅力"],
        )

        assert readiness_a.get_readiness_grade() == "A"
        assert readiness_a.is_publication_ready()

        # C級: 40-60%
        readiness_c = PublicationReadiness(
            readiness_score=0.45,
            success_probability=0.35,
            critical_gaps=["恋愛要素不足", "転換点の弱さ"],
            competitive_advantages=["世界観"],
        )

        assert readiness_c.get_readiness_grade() == "C"
        assert not readiness_c.is_publication_ready()

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-GENRE_BENCHMARK_RESU")
    def test_genre_benchmark_result_creation(self) -> None:
        """ジャンル比較結果の作成"""
        genre_config = GenreConfiguration(
            main_genre=MainGenre.FANTASY,
            sub_genres=[SubGenre.ISEKAI, SubGenre.SCHOOL],
            target_format=TargetFormat.LIGHT_NOVEL,
        )

        comparisons = [
            StructuralComparison(
                aspect="転換点",
                user_value="第8話",
                benchmark_value="第4-6話",
                conformity_rate=0.6,
                status=ComparisonStatus.WARNING,
            ),
            StructuralComparison(
                aspect="恋愛導入",
                user_value="未設定",
                benchmark_value="第8-12話",
                conformity_rate=0.0,
                status=ComparisonStatus.CRITICAL,
            ),
        ]

        suggestions = [
            ImprovementSuggestion(
                priority="高",
                description="第6話までに恋愛要素を導入",
                reference_work="魔法科高校の劣等生",
                expected_impact="読者の感情移入促進",
            ),
        ]

        readiness = PublicationReadiness(
            readiness_score=0.45,
            success_probability=0.35,
            critical_gaps=["恋愛要素不足"],
            competitive_advantages=["独自世界観"],
        )

        result = GenreBenchmarkResult(
            genre_config=genre_config,
            comparison_target_count=23,
            structural_comparisons=comparisons,
            improvement_suggestions=suggestions,
            publication_readiness=readiness,
            reference_works=["転生したらスライムだった件", "魔法科高校の劣等生"],
        )

        assert result.comparison_target_count == 23
        assert len(result.get_critical_issues()) == 1
        assert len(result.get_warning_issues()) == 1
        assert len(result.get_high_priority_suggestions()) == 1
        assert result.get_overall_conformity() == 0.3  # (0.6 + 0.0) / 2

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-GENRE_PATTERN_MATCHE")
    def test_genre_pattern_matcher_service_creation(self) -> None:
        """ジャンルパターンマッチャーサービスの作成"""
        matcher = GenrePatternMatcher()

        # このテストは実装が完了するまで失敗する
        assert matcher is not None

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-PUBLISHED_WORK_ANALY")
    def test_published_work_analyzer_service_creation(self) -> None:
        """書籍化作品分析サービスの作成"""
        analyzer = PublishedWorkAnalyzer()

        # このテストは実装が完了するまで失敗する
        assert analyzer is not None

    def test_genre_comparative_analysis_workflow(self) -> None:
        """ジャンル比較分析ワークフロー"""
        genre_config = GenreConfiguration(
            main_genre=MainGenre.FANTASY,
            sub_genres=[SubGenre.ISEKAI, SubGenre.SCHOOL],
            target_format=TargetFormat.LIGHT_NOVEL,
        )

        # 類似ジャンルの書籍化作品を準備
        works: list[PublishedWork] = []
        for idx in range(3):
            metrics = PublicationMetrics(
                publication_year=2022,
                volumes_published=6 + idx,
                total_pv=800_000 + idx * 50_000,
                bookmarks=20_000 + idx * 2_500,
                ratings=4.2 - idx * 0.1,
                reviews_count=400 + idx * 50,
            )
            structure = StoryStructure(
                first_turning_point=4 + idx,
                romance_introduction=9 + idx,
                mid_boss_battle=18 + idx,
                climax_point=24 + idx,
                total_episodes=28 + idx,
            )
            works.append(
                PublishedWork(
                    work_id=f"work_{idx}",
                    title=f"Work {idx}",
                    author="Author",
                    genre_config=genre_config,
                    publication_metrics=metrics,
                    story_structure=structure,
                    success_factors=["独自世界観", "キャラクター魅力"],
                )
            )

        matcher = GenrePatternMatcher()
        similar_works = matcher.find_similar_works(genre_config, works)
        assert len(similar_works) == 3

        analyzer = PublishedWorkAnalyzer()
        user_plot_data = {
            "structure": {
                "first_turning_point": 7,
                "romance_introduction": 0,
                "mid_boss_battle": 35,
                "total_episodes": 32,
            }
        }

        benchmark_result = analyzer.analyze_against_published_works(
            user_plot_data=user_plot_data,
            similar_works=similar_works,
            genre_config=genre_config,
        )

        assert benchmark_result.comparison_target_count == 3
        assert benchmark_result.get_overall_conformity() == pytest.approx(0.45, rel=1e-2)

        critical = benchmark_result.get_critical_issues()
        assert [issue.aspect for issue in critical] == ["恋愛要素導入"]

        warnings = benchmark_result.get_warning_issues()
        assert [issue.aspect for issue in warnings] == ["中ボス戦"]

        suggestions = benchmark_result.improvement_suggestions
        assert len(suggestions) == 2
        assert suggestions[0].priority == "高"
        assert suggestions[1].priority == "中"
        assert suggestions[0].reference_work == "Work 2"

        readiness = benchmark_result.publication_readiness
        assert readiness.readiness_score == pytest.approx(0.45, rel=1e-2)
        assert readiness.success_probability == pytest.approx(0.36, rel=1e-2)
        assert readiness.get_readiness_grade() == "C"

        assert list(benchmark_result.reference_works) == ["Work 2", "Work 1", "Work 0"]
        assert benchmark_result.get_market_position() == "市場適合度は標準的、重要な改善が必要"

    @pytest.mark.spec("SPEC-GENRE_COMPARATIVE_ANALYSIS_DOMAIN-DOMAIN_INTEGRATION_P")
    def test_domain_integration_performance(self) -> None:
        """ドメイン統合パフォーマンステスト"""
        # 大量のデータでも高速に処理できることを確認
        start_time = datetime.now(timezone.utc)

        # 100件の書籍化作品データを作成
        works = []
        for i in range(100):
            genre_config = GenreConfiguration(
                main_genre=MainGenre.FANTASY,
                sub_genres=[SubGenre.ISEKAI],
                target_format=TargetFormat.LIGHT_NOVEL,
            )

            metrics = PublicationMetrics(
                publication_year=2023,
                volumes_published=i % 10 + 1,
                total_pv=100000 * (i + 1),
                bookmarks=1000 * (i + 1),
                ratings=3.0 + (i % 20) * 0.1,
                reviews_count=50 * (i + 1),
            )

            structure = StoryStructure(
                first_turning_point=i % 5 + 1,
                romance_introduction=i % 10 + 5,
                mid_boss_battle=i % 15 + 10,
                climax_point=i % 20 + 15,
                total_episodes=i % 25 + 20,
            )

            work = PublishedWork(
                work_id=f"work_{i:03d}",
                title=f"テスト作品{i}",
                author=f"作者{i}",
                genre_config=genre_config,
                publication_metrics=metrics,
                story_structure=structure,
                success_factors=[f"要因{i}"],
            )

            works.append(work)

        # 処理時間を測定
        end_time = datetime.now(timezone.utc)
        elapsed = (end_time - start_time).total_seconds()

        # 100件のデータ作成が0.1秒以内で完了することを確認
        assert elapsed < 0.1, f"パフォーマンス要件未達成: {elapsed}秒"
        assert len(works) == 100
