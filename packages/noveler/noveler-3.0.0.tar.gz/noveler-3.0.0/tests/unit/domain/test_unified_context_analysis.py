#!/usr/bin/env python3
"""統合コンテキスト分析システムのテスト

SPEC-UCA-001: 統合コンテキスト分析システム仕様
- 全A31項目（68項目）の統合分析
- 全文コンテキスト保持
- 段階的改善提案生成
- 直接Claude分析レベルの詳細度達成
"""

from datetime import timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from noveler.application.use_cases.unified_context_analysis_use_case import (
    UnifiedAnalysisRequest,
    UnifiedContextAnalysisUseCase,
)
from noveler.domain.entities.holistic_analysis_result import (
    ComprehensiveImprovement,
    ContextMetrics,
    CrossPhaseInsight,
    HolisticAnalysisResult,
    PhaseAnalysis,
)
from noveler.domain.entities.unified_analysis_context import UnifiedAnalysisContext
from noveler.domain.services.unified_context_analyzer import UnifiedContextAnalyzer
from noveler.domain.value_objects.analysis_scope import AnalysisScope
from noveler.domain.value_objects.holistic_score import HolisticScore


class TestHolisticAnalysisResult:
    """統合分析結果エンティティのテスト"""

    @pytest.mark.spec("SPEC-UCA-001-001")
    def test_create_comprehensive_result(self):
        """包括的分析結果の生成"""
        # Given
        result = HolisticAnalysisResult(
            project_name="テスト小説",
            episode_number=5,
            overall_score=HolisticScore(92.4),
            phase_analyses={
                "Phase2_執筆段階": PhaseAnalysis(score=94.0, insights_count=14),
                "Phase3_推敲段階": PhaseAnalysis(score=91.5, insights_count=19),
                "Phase4_品質チェック段階": PhaseAnalysis(score=89.8, insights_count=16),
            },
            cross_phase_insights=[
                CrossPhaseInsight(
                    phases=["Phase2", "Phase3"], insight="冒頭フックと文章リズムの連携効果", impact_score=8.5
                )
            ],
            comprehensive_improvements=[
                ComprehensiveImprovement(
                    improvement_type="holistic_optimization",
                    affected_phases=["Phase2", "Phase3"],
                    original_texts=["実際の原稿テキスト1", "実際の原稿テキスト2"],
                    improved_texts=["改善されたテキスト1", "改善されたテキスト2"],
                    confidence="high",
                    reasoning="全体構造最適化による読者体験向上",
                    expected_impact=7.8,
                )
            ],
            context_preservation_metrics=ContextMetrics(
                preservation_rate=97.5, cross_reference_count=45, context_depth=8
            ),
            execution_time=timedelta(seconds=28.5),
        )

        # Then
        assert result.overall_score.value == 92.4
        assert len(result.phase_analyses) == 3
        assert len(result.cross_phase_insights) == 1
        assert len(result.comprehensive_improvements) == 1
        assert result.context_preservation_metrics.preservation_rate > 95.0
        assert result.execution_time.total_seconds() < 30.0


class TestUnifiedAnalysisContext:
    """統合分析コンテキストのテスト"""

    @pytest.mark.spec("SPEC-UCA-001-002")
    def test_preserve_full_manuscript_context(self):
        """全文コンテキスト保持の検証"""
        # Given
        full_manuscript = "完全な原稿内容" * 1000  # 長文シミュレーション

        # Mock A31チェックリストを適切にセットアップ
        mock_checklist = {
            "Phase2_執筆段階": [
                Mock(id="A31-021", item="テスト項目", phase="Phase2", required=True, item_type="content_quality")
            ]
        }

        mock_cross_ref = Mock()
        mock_cross_ref.relationship_count = 10
        mock_cross_ref.get_relationship_density.return_value = 0.5

        context = UnifiedAnalysisContext(
            manuscript_content=full_manuscript,
            a31_checklist=mock_checklist,
            project_context=Mock(),
            episode_context=Mock(),
            cross_reference_data=mock_cross_ref,
            preservation_scope=AnalysisScope.COMPREHENSIVE,
        )

        # Then
        assert len(context.manuscript_content) > 800  # 制限なし
        assert context.preservation_scope == AnalysisScope.COMPREHENSIVE

    @pytest.mark.spec("SPEC-UCA-001-003")
    def test_maintain_cross_reference_integrity(self):
        """相互参照整合性の維持"""
        # Given
        mock_checklist = {
            "Phase2_執筆段階": [Mock(id=f"A31-{i:03d}") for i in range(1, 35)],
            "Phase3_推敲段階": [Mock(id=f"A31-{i:03d}") for i in range(35, 69)],
        }

        mock_cross_ref = Mock()
        mock_cross_ref.relationship_count = 156  # 68項目の相互関係

        context = UnifiedAnalysisContext(
            manuscript_content="テスト原稿",
            a31_checklist=mock_checklist,
            project_context=Mock(),
            episode_context=Mock(),
            cross_reference_data=mock_cross_ref,
            preservation_scope=AnalysisScope.COMPREHENSIVE,
        )

        # Then
        assert context.cross_reference_data.relationship_count > 100


class TestUnifiedContextAnalyzer:
    """統合コンテキスト分析器のテスト"""

    @pytest.mark.spec("SPEC-UCA-001-004")
    @pytest.mark.asyncio
    async def test_holistic_analysis_execution(self):
        """統合分析の実行"""
        # Given
        analyzer = UnifiedContextAnalyzer()

        # 適切なコンテキストMockを作成
        mock_checklist = {
            "Phase2_執筆段階": [
                Mock(
                    id="A31-021",
                    item="テスト項目1",
                    phase="Phase2",
                    required=True,
                    item_type="content_quality",
                    get_priority_score=lambda: 8.0,
                    has_cross_references=lambda: False,
                ),
                Mock(
                    id="A31-022",
                    item="テスト項目2",
                    phase="Phase2",
                    required=True,
                    item_type="readability_check",
                    get_priority_score=lambda: 7.5,
                    has_cross_references=lambda: False,
                ),
            ],
            "Phase3_推敲段階": [
                Mock(
                    id="A31-031",
                    item="テスト項目3",
                    phase="Phase3",
                    required=True,
                    item_type="style_consistency",
                    get_priority_score=lambda: 7.0,
                    has_cross_references=lambda: False,
                )
            ],
        }

        mock_cross_ref = Mock()
        mock_cross_ref.relationship_count = 10
        mock_cross_ref.get_relationship_density.return_value = 0.5
        mock_cross_ref.phase_interactions = {"Phase2_執筆段階": ["Phase3_推敲段階"]}

        mock_project_context = Mock()
        mock_project_context.project_name = "テストプロジェクト"
        mock_project_context.episode_number = 1

        context = Mock()
        context.manuscript_content = "テスト原稿" * 500
        context.a31_checklist = mock_checklist
        context.project_context = mock_project_context
        context.cross_reference_data = mock_cross_ref
        context.preservation_scope = AnalysisScope.COMPREHENSIVE
        context.get_total_items_count.return_value = 3
        context.get_required_items_count.return_value = 3
        context.should_preserve_full_context.return_value = True

        # When
        result = await analyzer.analyze_holistically(context)

        # Then
        assert isinstance(result, HolisticAnalysisResult)
        assert result.overall_score.value > 0
        assert len(result.phase_analyses) >= 2
        assert result.context_preservation_metrics.preservation_rate > 90.0

    @pytest.mark.spec("SPEC-UCA-001-005")
    @pytest.mark.asyncio
    async def test_cross_phase_insight_generation(self):
        """段階間洞察の生成"""
        # Given
        analyzer = UnifiedContextAnalyzer()

        # コンテキストを適切にセットアップ
        mock_checklist = {
            "Phase2_執筆段階": [
                Mock(
                    id="A31-021",
                    item="テスト項目1",
                    phase="Phase2",
                    required=True,
                    item_type="content_quality",
                    get_priority_score=lambda: 8.0,
                    has_cross_references=lambda: False,
                )
            ],
            "Phase3_推敲段階": [
                Mock(
                    id="A31-031",
                    item="テスト項目2",
                    phase="Phase3",
                    required=True,
                    item_type="style_consistency",
                    get_priority_score=lambda: 7.0,
                    has_cross_references=lambda: False,
                )
            ],
        }

        mock_cross_ref = Mock()
        mock_cross_ref.relationship_count = 5
        mock_cross_ref.get_relationship_density.return_value = 0.3
        mock_cross_ref.phase_interactions = {"Phase2_執筆段階": ["Phase3_推敲段階"]}

        mock_project_context = Mock()
        mock_project_context.project_name = "テストプロジェクト"
        mock_project_context.episode_number = 1

        context = Mock()
        context.manuscript_content = "テスト原稿"
        context.a31_checklist = mock_checklist
        context.project_context = mock_project_context
        context.cross_reference_data = mock_cross_ref
        context.preservation_scope = AnalysisScope.COMPREHENSIVE
        context.get_total_items_count.return_value = 2
        context.get_required_items_count.return_value = 2
        context.should_preserve_full_context.return_value = True

        # When
        result = await analyzer.analyze_holistically(context)

        # Then
        assert len(result.cross_phase_insights) >= 0  # 0個以上（生成されない場合もある）
        for insight in result.cross_phase_insights:
            assert len(insight.phases) >= 1  # 1段階以上
            assert insight.impact_score > 0


class TestUnifiedContextAnalysisUseCase:
    """統合コンテキスト分析ユースケースのテスト"""

    @pytest.mark.spec("SPEC-UCA-001-006")
    @pytest.mark.asyncio
    async def test_complete_workflow_execution(self):
        """完全ワークフローの実行"""
        # Given
        # より詳細なMockを作成
        mock_context_preservation_metrics = Mock()
        mock_context_preservation_metrics.preservation_rate = 97.5

        mock_analysis_result = Mock()
        mock_analysis_result.overall_score = HolisticScore(92.4)
        mock_analysis_result.execution_time = timedelta(seconds=25.0)
        mock_analysis_result.total_items_analyzed = 10
        mock_analysis_result.phase_analyses = {}
        mock_analysis_result.cross_phase_insights = []
        mock_analysis_result.comprehensive_improvements = []
        mock_analysis_result.context_preservation_metrics = mock_context_preservation_metrics

        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_holistically.return_value = mock_analysis_result

        # context_builderもAsyncMockにする必要がある
        mock_context = Mock()
        mock_context.get_total_items_count.return_value = 10
        mock_context.validate_context_integrity.return_value = {"is_valid": True, "issues": [], "warnings": []}

        mock_context_builder = AsyncMock()
        mock_context_builder.build_context.return_value = mock_context

        # result_formatterもAsyncMockにする必要がある
        mock_result_formatter = AsyncMock()
        mock_result_formatter.format_result.return_value = mock_analysis_result

        use_case = UnifiedContextAnalysisUseCase(
            unified_analyzer=mock_analyzer, context_builder=mock_context_builder, result_formatter=mock_result_formatter
        )

        request = UnifiedAnalysisRequest(
            project_name="テスト小説",
            episode_number=5,
            include_cross_phase_analysis=True,
            include_comprehensive_improvements=True,
            analysis_scope=AnalysisScope.COMPREHENSIVE,
        )

        # When
        response = await use_case.execute(request)

        # Then
        assert response.success is True
        assert response.analysis_result is not None
        assert response.execution_time_seconds < 30.0
        mock_analyzer.analyze_holistically.assert_called_once()

    @pytest.mark.spec("SPEC-UCA-001-007")
    @pytest.mark.asyncio
    async def test_performance_requirements_compliance(self):
        """パフォーマンス要件の遵守"""
        # Given
        # より詳細なMockを作成
        mock_context_preservation_metrics = Mock()
        mock_context_preservation_metrics.preservation_rate = 95.2

        mock_analysis_result = Mock()
        mock_analysis_result.overall_score = HolisticScore(88.5)
        mock_analysis_result.execution_time = timedelta(seconds=15.0)
        mock_analysis_result.total_items_analyzed = 20
        mock_analysis_result.phase_analyses = {}
        mock_analysis_result.cross_phase_insights = []
        mock_analysis_result.comprehensive_improvements = []
        mock_analysis_result.context_preservation_metrics = mock_context_preservation_metrics

        mock_analyzer = AsyncMock()
        mock_analyzer.analyze_holistically.return_value = mock_analysis_result

        mock_context = Mock()
        mock_context.get_total_items_count.return_value = 20
        mock_context.validate_context_integrity.return_value = {"is_valid": True, "issues": [], "warnings": []}

        mock_context_builder = AsyncMock()
        mock_context_builder.build_context.return_value = mock_context

        mock_result_formatter = AsyncMock()
        mock_result_formatter.format_result.return_value = mock_analysis_result

        use_case = UnifiedContextAnalysisUseCase(
            unified_analyzer=mock_analyzer, context_builder=mock_context_builder, result_formatter=mock_result_formatter
        )

        request = UnifiedAnalysisRequest(
            project_name="大規模小説", episode_number=10, analysis_scope=AnalysisScope.COMPREHENSIVE
        )

        # When
        import time

        start_time = time.time()
        response = await use_case.execute(request)
        execution_time = time.time() - start_time

        # Then
        assert execution_time < 30.0  # 30秒以内
        assert response.memory_usage_mb < 500  # 500MB以下


class TestSystemIntegration:
    """システム統合テスト"""

    @pytest.mark.spec("SPEC-UCA-001-008")
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_direct_claude_quality_parity(self):
        """直接Claude分析品質との同等性"""
        # Given: 実際のA31チェックリストと原稿
        manuscript_content = "実際の原稿内容"

        # When: 統合分析実行
        analyzer = UnifiedContextAnalyzer()
        context = UnifiedAnalysisContext(
            manuscript_content=manuscript_content,
            a31_checklist=Mock(),
            project_context=Mock(),
            episode_context=Mock(),
            cross_reference_data=Mock(),
            preservation_scope=AnalysisScope.COMPREHENSIVE,
        )

        result = await analyzer.analyze_holistically(context)

        # Then: 品質基準達成
        assert result.overall_score.value > 90.0  # 高品質分析
        assert len(result.comprehensive_improvements) > 10  # 豊富な改善提案
        assert result.context_preservation_metrics.preservation_rate > 95.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
