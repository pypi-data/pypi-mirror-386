"""分析結果リポジトリインターフェース

離脱率分析結果を永続化するための抽象インターフェース。
DDD原則に基づき、ドメイン層に配置。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class AnalysisResultData:
    """分析結果のデータ群"""

    project_name: str
    ncode: str
    analysis_date: date
    average_dropout_rate: float
    episode_dropouts: list[dict]
    critical_episodes: list[dict]
    recommendations: list[str]


class AnalysisResult:
    """分析結果を表すドメインモデル"""

    def __init__(self, analysis_id: str, data: AnalysisResultData) -> None:
        self.analysis_id = analysis_id
        self.project_name = data.project_name
        self.ncode = data.ncode
        self.analysis_date = data.analysis_date
        self.average_dropout_rate = data.average_dropout_rate
        self.episode_dropouts = data.episode_dropouts
        self.critical_episodes = data.critical_episodes
        self.recommendations = data.recommendations


class AnalysisResultRepository(ABC):
    """分析結果リポジトリの抽象インターフェース"""

    @abstractmethod
    def save(self, result: AnalysisResult) -> None:
        """分析結果を保存

        Args:
            result: 分析結果

        Raises:
            RepositoryError: 保存エラー
        """

    @abstractmethod
    def find_by_id(self, analysis_id: str) -> AnalysisResult | None:
        """IDで分析結果を検索

        Args:
            analysis_id: 分析ID

        Returns:
            分析結果(見つからない場合はNone)

        Raises:
            RepositoryError: リポジトリエラー
        """

    @abstractmethod
    def find_latest_by_project(self, project_name: str, ncode: str) -> AnalysisResult | None:
        """プロジェクトの最新分析結果を取得

        Args:
            project_name: プロジェクト名
            ncode: 小説コード

        Returns:
            最新の分析結果(見つからない場合はNone)

        Raises:
            RepositoryError: リポジトリエラー
        """

    @abstractmethod
    def find_by_date_range(self, project_name: str, ncode: str) -> list[AnalysisResult]:
        """期間指定で分析結果を検索

        Args:
            project_name: プロジェクト名
            ncode: 小説コード
            start_date: 開始日
            end_date: 終了日

        Returns:
            期間内の分析結果リスト

        Raises:
            RepositoryError: リポジトリエラー
        """
