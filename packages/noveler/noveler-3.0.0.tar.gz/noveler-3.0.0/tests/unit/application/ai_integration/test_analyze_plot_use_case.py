#!/usr/bin/env python3
"""プロット分析ユースケースのユニットテスト

TDD原則に基づくユースケーステスト


仕様書: SPEC-INTEGRATION
"""

from unittest.mock import Mock

import pytest

from noveler.application.ai_integration.use_cases.analyze_plot_use_case import (
    AnalyzePlotUseCase,
    InvalidPlotFormatError,
    PlotFileNotFoundError,
)
from noveler.domain.ai_integration.entities.plot_analysis import PlotAnalysis
from noveler.domain.ai_integration.value_objects.analysis_result import AnalysisResult, StrengthPoint
from noveler.domain.ai_integration.value_objects.plot_score import PlotScore


class TestAnalyzePlotUseCase:
    """プロット分析ユースケースのテスト"""

    def setup_method(self) -> None:
        """テストのセットアップ"""
        self.plot_repository = Mock()
        self.analysis_repository = Mock()
        self.analysis_service = Mock()

        self.use_case = AnalyzePlotUseCase(
            plot_repository=self.plot_repository,
            analysis_repository=self.analysis_repository,
            analysis_service=self.analysis_service,
        )

    @pytest.mark.spec("SPEC-ANALYZE_PLOT_USE_CASE-ANALYZE_EXISTING_PLO")
    def test_analyze_existing_plot_success(self) -> None:
        """既存プロットの分析成功"""
        # Arrange
        plot_path = "20_プロット/章別プロット/chapter01.yaml"
        plot_content = {
            "metadata": {"title": "ch01"},
            "structure": {"setup": {"description": "設定"}},
            "characters": {"protagonist": {"motivation": "動機"}},
        }

        analysis_result = AnalysisResult(
            total_score=PlotScore(85),
            strengths=[StrengthPoint("構成が優れている", 90)],
            improvements=[],
            overall_advice="素晴らしいプロットです。",
        )

        self.plot_repository.exists.return_value = True
        self.plot_repository.load.return_value = plot_content
        self.analysis_service.analyze.return_value = analysis_result

        # Act
        result = self.use_case.execute(plot_path)

        # Assert
        assert isinstance(result, PlotAnalysis)
        assert result.plot_file_path == plot_path
        assert result.is_analyzed()
        assert result.result == analysis_result

        # Verify interactions
        self.plot_repository.exists.assert_called_once_with(plot_path)
        self.plot_repository.load.assert_called_once_with(plot_path)
        self.analysis_service.analyze.assert_called_once_with(plot_content)
        self.analysis_repository.save.assert_called_once()

    @pytest.mark.spec("SPEC-ANALYZE_PLOT_USE_CASE-ANALYZE_NONEXISTENT_")
    def test_analyze_nonexistent_plot_raises_error(self) -> None:
        """存在しないプロットの分析でエラー"""
        # Arrange
        plot_path = "nonexistent.yaml"
        self.plot_repository.exists.return_value = False

        # Act & Assert
        with pytest.raises(PlotFileNotFoundError) as exc_info:
            self.use_case.execute(plot_path)

        assert plot_path in str(exc_info.value)
        self.plot_repository.exists.assert_called_once_with(plot_path)
        self.plot_repository.load.assert_not_called()

    @pytest.mark.spec("SPEC-ANALYZE_PLOT_USE_CASE-ANALYZE_INVALID_FORM")
    def test_analyze_invalid_format_raises_error(self) -> None:
        """無効なフォーマットのプロットでエラー"""
        # Arrange
        plot_path = "invalid.yaml"
        self.plot_repository.exists.return_value = True
        self.plot_repository.load.side_effect = ValueError("Invalid YAML")

        # Act & Assert
        with pytest.raises(InvalidPlotFormatError) as exc_info:
            self.use_case.execute(plot_path)

        assert "Invalid YAML" in str(exc_info.value)

    @pytest.mark.spec("SPEC-ANALYZE_PLOT_USE_CASE-GET_RECENT_ANALYSES")
    def test_get_recent_analyses(self) -> None:
        """最近の分析結果取得"""
        # Arrange
        recent_analyses = [PlotAnalysis("id1", "plot1.yaml", None), PlotAnalysis("id2", "plot2.yaml", None)]
        self.analysis_repository.get_recent.return_value = recent_analyses

        # Act
        result = self.use_case.get_recent_analyses(limit=2)

        # Assert
        assert result == recent_analyses
        self.analysis_repository.get_recent.assert_called_once_with(limit=2)

    @pytest.mark.spec("SPEC-ANALYZE_PLOT_USE_CASE-GET_ANALYSIS_BY_ID")
    def test_get_analysis_by_id(self) -> None:
        """IDによる分析結果取得"""
        # Arrange
        analysis_id = "analysis_123"
        analysis = PlotAnalysis(analysis_id, "plot.yaml", None)
        self.analysis_repository.get_by_id.return_value = analysis

        # Act
        result = self.use_case.get_analysis_by_id(analysis_id)

        # Assert
        assert result == analysis
        self.analysis_repository.get_by_id.assert_called_once_with(analysis_id)

    @pytest.mark.spec("SPEC-ANALYZE_PLOT_USE_CASE-ANALYZE_WITH_OPTIONS")
    def test_analyze_with_options(self) -> None:
        """オプション付き分析"""
        # Arrange
        plot_path = "plot.yaml"
        plot_content = {"structure": {}}
        analysis_options = {"depth": "full", "focus_areas": ["pacing", "character_relations"]}

        self.plot_repository.exists.return_value = True
        self.plot_repository.load.return_value = plot_content
        self.analysis_service.analyze.return_value = Mock(spec=AnalysisResult)

        # Act
        result = self.use_case.execute(plot_path, _options=analysis_options)

        # Assert
        assert isinstance(result, PlotAnalysis)
        # TODO: オプションがサービスに渡されることを確認

    @pytest.mark.spec("SPEC-ANALYZE_PLOT_USE_CASE-CACHE_ANALYSIS_RESUL")
    def test_cache_analysis_result(self) -> None:
        """分析結果のキャッシュ"""
        # Arrange
        plot_path = "plot.yaml"
        cached_analysis = PlotAnalysis("cached_id", plot_path, None)
        cached_analysis.result = Mock(spec=AnalysisResult)

        self.analysis_repository.get_by_plot_path.return_value = cached_analysis

        # Act
        result = self.use_case.execute(plot_path, use_cache=True)

        # Assert
        assert result == cached_analysis
        self.plot_repository.load.assert_not_called()
        self.analysis_service.analyze.assert_not_called()
