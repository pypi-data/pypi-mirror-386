"""Dropout rate analysis use case.

Analyzes episode access data to detect high dropout rates and flag episodes needing improvements.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from noveler.domain.entities.dropout_analysis_session import DropoutAnalysisSession, EpisodeMetrics
from noveler.domain.repositories.access_data_repository import AccessDataRepository
from noveler.domain.repositories.analysis_result_repository import AnalysisResult, AnalysisResultData
from noveler.domain.value_objects.analysis_id import AnalysisId
from noveler.domain.value_objects.dropout_metrics import AccessData


@dataclass
class DropoutAnalysisRequest:
    """Input payload for dropout rate analysis.

    Attributes:
        project_name: Name of the project to analyze.
        ncode: External identifier for the project.
        target_date: Optional date restricting the analysis window.
        critical_threshold: Dropout rate threshold considered critical.
        save_result: Whether analysis results should be persisted.
        generate_recommendations: Toggle to compute improvement suggestions.
    """

    project_name: str
    ncode: str
    target_date: date | None = None
    critical_threshold: float = 20.0
    save_result: bool = False
    generate_recommendations: bool = False


@dataclass
class DropoutAnalysisResponse:
    """Result payload produced by the dropout rate analysis.

    Attributes:
        success: Indicates whether the analysis completed successfully.
        average_dropout_rate: Average dropout rate across episodes.
        episode_dropouts: Per-episode dropout information.
        critical_episodes: Episodes exceeding the critical threshold.
        recommendations: Optional list of improvement suggestions.
        analysis_id: Identifier of the stored analysis result.
        error_message: Error detail when the analysis fails.
    """

    success: bool
    average_dropout_rate: float = 0.0
    episode_dropouts: list[dict[str, Any]] = field(default_factory=list)
    critical_episodes: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    analysis_id: str | None = None
    error_message: str | None = None


class AnalyzeDropoutRateUseCase:
    """Coordinate dropout rate analysis using domain services."""

    def __init__(
        self, access_data_repository: AccessDataRepository, analysis_result_repository: AnalysisResult
    ) -> None:
        """Initialise the use case with repositories.

        Args:
            access_data_repository: Repository that provides access data.
            analysis_result_repository: Repository used to persist analysis results.
        """
        self.access_data_repository = access_data_repository
        self.analysis_result_repository = analysis_result_repository

    def execute(self, request: DropoutAnalysisRequest) -> DropoutAnalysisResponse:
        """Execute the dropout rate analysis workflow.

        Args:
            request: Dropout rate analysis request.

        Returns:
            DropoutAnalysisResponse: Analysis response describing findings.
        """
        try:
            # Fetch access data and populate the analysis session
            access_data = self._get_access_data(request)

            # 分析セッションを作成
            analysis_id = AnalysisId(value=None)  # None指定で自動生成
            session = DropoutAnalysisSession(
                session_id=str(analysis_id), project_id=request.project_name, ncode=request.ncode
            )

            # アクセスデータをセッションに反映
            self._populate_session_metrics(session, access_data)

            # 離脱率を分析
            session.filter_incomplete_data()
            dropout_rates = session.calculate_dropout_rates()

            # レスポンスを作成
            response = self._create_response(session, dropout_rates, request, analysis_id)

            # 結果を保存(必要な場合)
            if request.save_result:
                self._save_result(response, request)

            return response

        except Exception as e:
            return DropoutAnalysisResponse(success=False, error_message=str(e))

    def _get_access_data(self, request: DropoutAnalysisRequest) -> AccessData:
        """Fetch access data for the given analysis request.

        Args:
            request: Dropout analysis request.

        Returns:
            AccessData: Access metrics to analyze.
        """
        return self.access_data_repository.get_access_data(
            project_name=request.project_name, ncode=request.ncode, target_date=request.target_date
        )

    def _populate_session_metrics(self, session: DropoutAnalysisSession, access_data: AccessData) -> None:
        """Convert access data into session metrics used by the domain."""

        sorted_accesses = access_data.sorted_by_episode().accesses

        for access in sorted_accesses:
            metrics = EpisodeMetrics(
                episode_number=access.episode_number,
                episode_title=f"第{access.episode_number}話",
                page_views=access.page_views,
                unique_users=max(access.page_views, 1),
                access_date=access.date,
            )
            session.add_episode_metrics(metrics)

    def _create_response(
        self,
        session: DropoutAnalysisSession,
        dropout_rates: list[Any],
        request: DropoutAnalysisRequest,
        analysis_id: AnalysisId,
    ) -> DropoutAnalysisResponse:
        """Build a response object from the analysis results."""

        episode_dropouts = [
            {
                "episode_number": dropout.episode_number,
                "dropout_rate": dropout.dropout_rate.value,
                "page_views": dropout.current_pv,
                "previous_page_views": dropout.previous_pv,
            }
            for dropout in dropout_rates
        ]

        critical_instances = session.identify_critical_episodes(request.critical_threshold)
        critical_episodes = [
            {
                "episode_number": critical.episode_number,
                "dropout_rate": critical.dropout_rate.value,
                "priority": critical.priority,
            }
            for critical in critical_instances
        ]

        recommendations: list[str] = []
        if request.generate_recommendations:
            recommendations = session.generate_recommendations()

        average_rate = session.calculate_average_dropout_rate().value

        return DropoutAnalysisResponse(
            success=True,
            average_dropout_rate=average_rate,
            episode_dropouts=episode_dropouts,
            critical_episodes=critical_episodes,
            recommendations=recommendations,
            analysis_id=str(analysis_id),
        )

    def _generate_recommendations(self, result: Any, critical_episodes: list[Any]) -> list[str]:
        """Generate improvement suggestions based on analysis results.

        Args:
            result: Analysis result payload.
            critical_episodes: Episodes flagged as critical.

        Returns:
            list[str]: Recommendations for improving engagement.
        """
        recommendations = []

        # 平均離脱率に基づく提案
        if result.average_dropout_rate > 25.0:
            recommendations.append(
                f"平均離脱率が{result.average_dropout_rate:.1f}%と高いです。全体的な構成の見直しを検討してください。"
            )

        # 個別エピソードの提案
        recommendations.extend(
            [
                f"第{dropout.episode_number}話の離脱率が{dropout.dropout_rate.value:.1f}%と高いです。内容の見直しが必要です。"
                for dropout in critical_episodes
            ]
        )

        # 一般的な改善提案
        if critical_episodes:
            recommendations.extend(
                [
                    "各話の締めに次話への強い引きを追加することを検討してください",
                    "読者コメントから具体的な問題点を抽出し、改善に活用してください",
                    "情報過多による読者の混乱がないか確認してください",
                ]
            )

        return recommendations

    def _save_result(self, response: DropoutAnalysisResponse, request: DropoutAnalysisRequest) -> None:
        """Persist analysis results when requested.

        Args:
            response: Analysis response payload.
            request: Original analysis request.
        """
        if response.analysis_id:
            data = AnalysisResultData(
                project_name=request.project_name,
                ncode=request.ncode,
                analysis_date=request.target_date or datetime.now(timezone.utc).date(),
                average_dropout_rate=response.average_dropout_rate,
                episode_dropouts=response.episode_dropouts,
                critical_episodes=response.critical_episodes,
                recommendations=response.recommendations,
            )

            result = AnalysisResult(response.analysis_id, data)
            self.analysis_result_repository.save(result)
