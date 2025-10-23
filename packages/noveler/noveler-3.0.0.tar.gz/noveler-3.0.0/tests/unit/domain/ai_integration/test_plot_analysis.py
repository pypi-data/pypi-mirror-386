#!/usr/bin/env python3
"""プロット分析ドメインのユニットテスト

TDD+DDD原則に基づく失敗するテストから開始
実行時間目標: < 0.1秒/テスト


仕様書: SPEC-INTEGRATION
"""

import time

import pytest

from noveler.domain.ai_integration.entities.plot_analysis import PlotAnalysis
from noveler.domain.ai_integration.services.plot_analysis_service import PlotAnalysisService
from noveler.domain.ai_integration.value_objects.analysis_criteria import (
    AnalysisCriteria,
    CriteriaCategory,
    CriteriaWeight,
)
from noveler.domain.ai_integration.value_objects.analysis_result import AnalysisResult, ImprovementPoint, StrengthPoint
from noveler.domain.ai_integration.value_objects.plot_score import PlotScore
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestPlotAnalysisDomain:
    """プロット分析ドメインのテストスイート"""

    # =================================================================
    # RED Phase: 失敗するテストを先に書く
    # =================================================================

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-PLOT_SCORE_SHOULD_VA")
    def test_plot_score_should_validate_range(self) -> None:
        """プロットスコアは0-100の範囲でなければならない"""
        # 無効な値は拒否されるべき
        with pytest.raises(ValueError, match="0以上100以下"):
            PlotScore(-1)

        with pytest.raises(ValueError, match="0以上100以下"):
            PlotScore(101)

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-PLOT_SCORE_CREATION_")
    def test_plot_score_creation_with_valid_value(self) -> None:
        """有効な値でプロットスコアを作成"""
        SAMPLE_SCORE = 85
        score = PlotScore(SAMPLE_SCORE)
        assert score.value == SAMPLE_SCORE
        assert score.grade == "A"  # 80-89はA評価
        assert score.is_high_quality()  # 80以上は高品質

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-PLOT_SCORE_GRADE_CAL")
    def test_plot_score_grade_calculation(self) -> None:
        """スコアに基づくグレード計算"""
        assert PlotScore(95).grade == "S"  # 90-100
        assert PlotScore(85).grade == "A"  # 80-89
        assert PlotScore(75).grade == "B"  # 70-79
        assert PlotScore(65).grade == "C"  # 60-69
        assert PlotScore(55).grade == "D"  # 50-59
        assert PlotScore(45).grade == "E"  # 0-49

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-PLOT_SCORE_IS_ACCEPT")
    def test_plot_score_is_acceptable(self) -> None:
        """許容範囲判定のテスト"""
        # 60点以上は許容範囲
        assert PlotScore(60).is_acceptable()
        assert PlotScore(75).is_acceptable()
        assert PlotScore(90).is_acceptable()

        # 60点未満は許容範囲外
        assert not PlotScore(59).is_acceptable()
        assert not PlotScore(30).is_acceptable()
        assert not PlotScore(0).is_acceptable()

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-PLOT_SCORE_STRING_RE")
    def test_plot_score_string_representation(self) -> None:
        """文字列表現のテスト"""
        score = PlotScore(85)
        assert str(score) == "85/100 (A)"

        score = PlotScore(95)
        assert str(score) == "95/100 (S)"

        score = PlotScore(45)
        assert str(score) == "45/100 (E)"

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-ANALYSIS_CRITERIA_CR")
    def test_analysis_criteria_creation(self) -> None:
        """分析基準の作成"""
        criteria = AnalysisCriteria(
            category=CriteriaCategory.STRUCTURE,
            weight=CriteriaWeight(25),
            factors=["plot_coherence", "pacing", "climax_buildup"],
        )

        assert criteria.category == CriteriaCategory.STRUCTURE
        assert criteria.weight.value == 25
        assert len(criteria.factors) == 3
        assert "pacing" in criteria.factors

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-CRITERIA_WEIGHT_VALI")
    def test_criteria_weight_validation(self) -> None:
        """基準の重みは合計100になるべき"""
        weights = [
            CriteriaWeight(25),  # structure
            CriteriaWeight(25),  # characters
            CriteriaWeight(20),  # themes
            CriteriaWeight(15),  # originality
            CriteriaWeight(15),  # technical
        ]

        total = sum(w.value for w in weights)
        assert total == 100

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-ANALYSIS_RESULT_CREA")
    def test_analysis_result_creation(self) -> None:
        """分析結果の作成"""
        strengths = [
            StrengthPoint("キャラクターの動機が明確", 85),
            StrengthPoint("緊張感の構築が効果的", 82),
        ]

        improvements = [
            ImprovementPoint("中盤のペース配分", 65, "第3-5話で展開が停滞する可能性"),
        ]

        result = AnalysisResult(
            total_score=PlotScore(78),
            strengths=strengths,
            improvements=improvements,
            overall_advice="全体的によく構成されたプロットです。",
        )

        assert result.total_score.value == 78
        assert len(result.strengths) == 2
        assert len(result.improvements) == 1
        assert result.has_high_quality_structure()

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-PLOT_ANALYSIS_ENTITY")
    def test_plot_analysis_entity_creation(self) -> None:
        """プロット分析エンティティの作成"""
        analysis = PlotAnalysis(
            id="analysis_001",
            plot_file_path="20_プロット/章別プロット/chapter01.yaml",
            analyzed_at=project_now().datetime,
        )

        assert analysis.id == "analysis_001"
        assert analysis.plot_file_path.endswith("chapter01.yaml")
        assert analysis.analyzed_at is not None
        assert analysis.result is None  # 結果はまだない

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-PLOT_ANALYSIS_WITH_R")
    def test_plot_analysis_with_result(self) -> None:
        """分析結果を含むプロット分析"""
        analysis = PlotAnalysis(
            id="analysis_002",
            plot_file_path="20_プロット/章別プロット/chapter01.yaml",
            analyzed_at=project_now().datetime,
        )

        result = AnalysisResult(
            total_score=PlotScore(82),
            strengths=[StrengthPoint("構成が優れている", 90)],
            improvements=[],
            overall_advice="素晴らしいプロットです。",
        )

        analysis.set_result(result)
        assert analysis.result == result
        assert analysis.is_analyzed()

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-PLOT_ANALYSIS_SERVIC")
    def test_plot_analysis_service_evaluate_structure(self) -> None:
        """構造評価のテスト"""
        service = PlotAnalysisService()

        plot_data = {
            "setup": {"description": "明確な設定"},
            "development": {"events": ["event1", "event2", "event3"]},
            "climax": {"description": "感動的なクライマックス"},
            "resolution": {"description": "満足のいく結末"},
        }

        score = service.evaluate_structure(plot_data)
        assert isinstance(score, PlotScore)
        assert score.value >= 70  # 良い構造は高スコア

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-PLOT_ANALYSIS_SERVIC")
    def test_plot_analysis_service_evaluate_characters(self) -> None:
        """キャラクター評価のテスト"""
        service = PlotAnalysisService()

        character_data = {
            "protagonist": {"motivation": "明確な動機", "arc": "成長の軌跡", "conflicts": ["内的葛藤", "外的対立"]},
            "antagonist": {"motivation": "信念に基づく行動", "relationship": "主人公との深い因縁"},
        }

        score = service.evaluate_characters(character_data)
        assert isinstance(score, PlotScore)
        assert score.value >= 75

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-PLOT_ANALYSIS_SERVIC")
    def test_plot_analysis_service_full_analysis(self) -> None:
        """完全な分析フローのテスト"""
        service = PlotAnalysisService()

        plot_content = {
            "metadata": {"title": "ch01:始まりの時", "genre": "fantasy", "target_length": 10},
            "structure": {
                "setup": {"description": "主人公の日常"},
                "development": {"events": ["出会い", "試練", "成長"]},
                "climax": {"description": "最大の試練"},
                "resolution": {"description": "新たな旅立ち"},
            },
            "characters": {"main": {"protagonist": {"name": "主人公", "motivation": "世界を救う"}}},
            "themes": {"main_theme": "勇気と友情", "sub_themes": ["成長", "自己犠牲"]},
        }

        result = service.analyze(plot_content)

        assert isinstance(result, AnalysisResult)
        assert result.total_score.value > 0
        assert len(result.strengths) > 0
        assert result.overall_advice != ""

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-IMPROVEMENT_POINT_PR")
    def test_improvement_point_priority(self) -> None:
        """改善点の優先度判定"""
        high_priority = ImprovementPoint(
            "致命的な構造欠陥",
            30,  # 低スコア
            "物語が成立しない",
        )

        medium_priority = ImprovementPoint("ペース配分の問題", 60, "中盤が冗長")

        assert high_priority.is_critical()  # スコア40未満は致命的
        assert not medium_priority.is_critical()
        assert high_priority.priority == "high"
        assert medium_priority.priority == "medium"

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-ANALYSIS_RESULT_SUMM")
    def test_analysis_result_summary(self) -> None:
        """分析結果のサマリー生成"""
        result = AnalysisResult(
            total_score=PlotScore(75),
            strengths=[
                StrengthPoint("魅力的なキャラクター", 85),
                StrengthPoint("独創的な世界観", 80),
            ],
            improvements=[
                ImprovementPoint("構成の改善", 60, "起承転結が不明確"),
            ],
            overall_advice="キャラクターと世界観は素晴らしいです。構成を整えることでさらに良くなります。",
        )

        summary = result.get_summary()
        assert "総合評価: 75/100点" in summary
        assert "強み: 2項目" in summary
        assert "改善点: 1項目" in summary

    # =================================================================
    # Performance tests
    # =================================================================

    @pytest.mark.spec("SPEC-PLOT_ANALYSIS-ANALYSIS_PERFORMANCE")
    def test_analysis_performance(self) -> None:
        """分析のパフォーマンステスト"""

        service = PlotAnalysisService()
        plot_data = {
            "structure": {"setup": {}, "development": {}, "climax": {}, "resolution": {}},
            "characters": {"protagonist": {"motivation": "test"}},
            "themes": {"main_theme": "test"},
        }

        start_time = time.time()

        # 100回分析を実行
        for _ in range(100):
            service.analyze(plot_data)

        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"分析に{elapsed:.3f}秒かかりました(目標: < 1.0秒)"
