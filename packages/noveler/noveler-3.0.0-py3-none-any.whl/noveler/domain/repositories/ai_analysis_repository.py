#!/usr/bin/env python3
"""AI分析リポジトリインターフェース

AI分析結果の永続化を抽象化
"""

from abc import ABC, abstractmethod

from noveler.domain.ai_integration.entities.plot_analysis import PlotAnalysis


class AIAnalysisRepository(ABC):
    """AI分析リポジトリの抽象インターフェース"""

    @abstractmethod
    def save(self, analysis: PlotAnalysis) -> None:
        """分析結果を保存

        Args:
            analysis: プロット分析結果
        """

    @abstractmethod
    def get_by_id(self, analysis_id: str) -> PlotAnalysis | None:
        """IDで分析結果を取得

        Args:
            analysis_id: 分析ID

        Returns:
            分析結果(存在しない場合はNone)
        """

    @abstractmethod
    def get_by_plot_path(self, plot_path: str) -> PlotAnalysis | None:
        """プロットパスで最新の分析結果を取得

        Args:
            plot_path: プロットファイルパス

        Returns:
            最新の分析結果(存在しない場合はNone)
        """

    @abstractmethod
    def get_recent(self, limit: int) -> list[PlotAnalysis]:
        """最近の分析結果を取得

        Args:
            limit: 取得件数

        Returns:
            分析結果のリスト(新しい順)
        """

    @abstractmethod
    def delete(self, analysis_id: str) -> bool:
        """分析結果を削除

        Args:
            analysis_id: 分析ID

        Returns:
            削除成功の場合True
        """
