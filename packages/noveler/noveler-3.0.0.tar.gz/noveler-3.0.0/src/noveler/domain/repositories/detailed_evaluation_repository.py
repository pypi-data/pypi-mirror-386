#!/usr/bin/env python3
"""詳細評価リポジトリ インターフェース

DetailedEvaluationSessionとDetailedAnalysisResultの永続化を管理する
ドメイン層リポジトリインターフェース。
"""

from abc import ABC, abstractmethod

from noveler.domain.entities.detailed_evaluation_session import DetailedEvaluationSession
from noveler.domain.services.detailed_analysis_engine import DetailedAnalysisResult
from noveler.domain.value_objects.episode_number import EpisodeNumber


class DetailedEvaluationRepository(ABC):
    """詳細評価リポジトリ インターフェース

    DetailedEvaluationSessionとDetailedAnalysisResultの永続化操作を定義。
    インフラ層で具体実装（YAML、JSON、DB等）を提供する。
    """

    @abstractmethod
    def save_evaluation_session(self, session: DetailedEvaluationSession) -> None:
        """評価セッションを保存

        Args:
            session: 保存対象の評価セッション

        Raises:
            RepositoryError: 保存に失敗した場合
        """

    @abstractmethod
    def save_analysis_result(self, result: DetailedAnalysisResult) -> None:
        """分析結果を保存

        Args:
            result: 保存対象の分析結果

        Raises:
            RepositoryError: 保存に失敗した場合
        """

    @abstractmethod
    def get_evaluation_session(
        self, project_name: str, episode_number: EpisodeNumber
    ) -> DetailedEvaluationSession | None:
        """評価セッションを取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            Optional[DetailedEvaluationSession]: 見つかった場合は評価セッション、なければNone
        """

    @abstractmethod
    def get_analysis_result(self, session_id: str) -> DetailedAnalysisResult | None:
        """分析結果を取得

        Args:
            session_id: セッションID

        Returns:
            Optional[DetailedAnalysisResult]: 見つかった場合は分析結果、なければNone
        """

    @abstractmethod
    def list_evaluation_sessions(self, project_name: str) -> list[DetailedEvaluationSession]:
        """プロジェクトの評価セッション一覧を取得

        Args:
            project_name: プロジェクト名

        Returns:
            list[DetailedEvaluationSession]: 評価セッション一覧
        """

    @abstractmethod
    def delete_evaluation_session(self, project_name: str, episode_number: EpisodeNumber) -> bool:
        """評価セッションを削除

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            bool: 削除に成功した場合True
        """

    @abstractmethod
    def exists_evaluation_session(self, project_name: str, episode_number: EpisodeNumber) -> bool:
        """評価セッションの存在確認

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            bool: 存在する場合True
        """


class RepositoryError(Exception):
    """リポジトリエラー

    リポジトリ操作で発生するエラーの基底クラス。
    """


class EvaluationSessionNotFoundError(RepositoryError):
    """評価セッション未発見エラー

    指定された評価セッションが見つからない場合のエラー。
    """


class AnalysisResultNotFoundError(RepositoryError):
    """分析結果未発見エラー

    指定された分析結果が見つからない場合のエラー。
    """
