#!/usr/bin/env python3
"""プロット分析ユースケース

プロット分析のアプリケーションロジックを実装
"""

from typing import Any

from noveler.domain.ai_integration.entities.plot_analysis import PlotAnalysis
from noveler.domain.ai_integration.services.plot_analysis_service import PlotAnalysisService
from noveler.domain.repositories.ai_analysis_repository import AIAnalysisRepository
from noveler.domain.repositories.plot_repository import PlotRepository


class PlotFileNotFoundError(Exception):
    """プロットファイルが見つからない"""


class InvalidPlotFormatError(Exception):
    """プロットフォーマットが無効"""


class AnalyzePlotUseCase:
    """プロット分析ユースケース

    プロットファイルを読み込み、分析し、結果を保存する
    """

    def __init__(
        self,
        plot_repository: PlotRepository,
        analysis_repository: AIAnalysisRepository,
        analysis_service: PlotAnalysisService,
    ) -> None:
        """Args:
        plot_repository: プロットリポジトリ
        analysis_repository: 分析結果リポジトリ
        analysis_service: プロット分析サービス
        """
        self.plot_repository = plot_repository
        self.analysis_repository = analysis_repository
        self.analysis_service = analysis_service

    def execute(self, plot_path: str, _options: dict[str, Any] | None = None, use_cache: bool = False) -> PlotAnalysis:
        """プロット分析を実行

        Args:
            plot_path: 分析対象のプロットファイルパス
            _options: 分析オプション(将来の拡張用)
            use_cache: キャッシュを使用するかどうか

        Returns:
            分析結果を含むPlotAnalysis

        Raises:
            PlotFileNotFoundError: プロットファイルが存在しない
            InvalidPlotFormatError: プロットフォーマットが無効
        """
        if use_cache:
            cached_analysis = self.analysis_repository.get_by_plot_path(plot_path)
            if cached_analysis and cached_analysis.result:
                return cached_analysis
        if not self.plot_repository.exists(plot_path):
            msg = f"プロットファイルが見つかりません: {plot_path}"
            raise PlotFileNotFoundError(msg)

        try:
            plot_content = self.plot_repository.load(plot_path)
        except Exception as e:
            msg = f"プロットファイルの読み込みに失敗しました: {e!s}"
            raise InvalidPlotFormatError(msg) from e

        analysis = PlotAnalysis.create(plot_path)

        result = self.analysis_service.analyze(plot_content)
        analysis.set_result(result)

        self.analysis_repository.save(analysis)

        return analysis

    def get_recent_analyses(self, limit: int) -> list[PlotAnalysis]:
        """最近の分析結果を取得

        Args:
            limit: 取得件数

        Returns:
            最近の分析結果リスト
        """
        return self.analysis_repository.get_recent(limit=limit)

    def get_analysis_by_id(self, analysis_id: str) -> PlotAnalysis | None:
        """IDで分析結果を取得

        Args:
            analysis_id: 分析ID

        Returns:
            分析結果(存在しない場合はNone)
        """
        return self.analysis_repository.get_by_id(analysis_id)
