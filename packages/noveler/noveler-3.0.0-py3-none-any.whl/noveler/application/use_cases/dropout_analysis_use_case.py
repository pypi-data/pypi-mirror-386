#!/usr/bin/env python3

"""Application.use_cases.dropout_analysis_use_case
Where: Application use case focused on reader dropout analysis.
What: Calls domain services to analyse dropout metrics and generate actionable insights.
Why: Helps teams understand reader engagement trends without manual data plumbing.
"""

from __future__ import annotations



from typing import TYPE_CHECKING, Any

from noveler.domain.services.dropout_analysis_services import (
    DropoutAnalysisExecutionService,
    DropoutAnalysisRequest,
    DropoutAnalysisResponse,
    DropoutBulkAnalysisService,
    DropoutDataAcquisitionService,
    DropoutPeriodComparisonService,
    DropoutReportGenerationService,
    DropoutSessionManagementService,
    KasasagiClient,
    ReportGenerator,
)
from noveler.domain.value_objects.project_time import ProjectTimezone

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone

if TYPE_CHECKING:
    from noveler.domain.services.dropout_analysis_service import DataValidationService, DropoutAnalysisService


# レガシークラス(後方互換性のため残存)
class DropoutReportGenerator:
    """離脱率分析レポート生成クラス(レガシー)"""

    def generate_report(self, analysis_data: dict[str, Any]) -> str:
        """分析データからレポートを生成"""
        lines = [
            "# 離脱率分析レポート",
            f"## 分析期間: {analysis_data.get('period', 'N/A')}",
            f"## 総エピソード数: {analysis_data.get('total_episodes', 0)}",
            f"## 平均離脱率: {analysis_data.get('dropout_rate', 0.0):.2f}%",
            "",
            "### 詳細データ",
        ]

        episodes = analysis_data.get("episodes", [])
        for episode in episodes:
            lines.extend(
                [f"- エピソード{episode.get('number', 'N/A')}: 離脱率 {episode.get('dropout_rate', 0.0):.2f}%"]
            )

        return "\n".join(lines)


class DropoutAnalysisUseCase:
    """離脱率分析ユースケース

    離脱率分析のビジネスフローを管理する。
    DDD準拠のアプリケーション層実装。
    """

    def __init__(
        self,
        dropout_analysis_service: DropoutAnalysisService,
        data_validation_service: DataValidationService,
        kasasagi_client: KasasagiClient,
        report_generator: ReportGenerator,
    ) -> None:
        """初期化

        Args:
            dropout_analysis_service: 離脱率分析サービス
            data_validation_service: データ検証サービス
            kasasagi_client: KASASAGIクライアント
            report_generator: レポート生成器
        """
        self.dropout_analysis_service = dropout_analysis_service
        self.data_validation_service = data_validation_service
        self.kasasagi_client = kasasagi_client
        self.report_generator = report_generator

        # 新しいドメインサービスの初期化
        self._data_acquisition_service = DropoutDataAcquisitionService(kasasagi_client)
        self._session_management_service = DropoutSessionManagementService()
        self._analysis_execution_service = DropoutAnalysisExecutionService(data_validation_service)
        self._report_generation_service = DropoutReportGenerationService(report_generator)
        self._bulk_analysis_service = DropoutBulkAnalysisService(self)
        self._period_comparison_service = DropoutPeriodComparisonService(self)

    def analyze_dropout_rate(self, request: DropoutAnalysisRequest) -> DropoutAnalysisResponse:
        """離脱率を分析

        DDD準拠のビジネスフロー:
        1. セッション作成
        2. データ取得
        3. 分析実行
        4. レポート生成
        5. 結果返却
        """
        try:
            # ステップ1: セッション作成(新しいサービス使用)
            session_result = self._session_management_service.create_session(request)
            if not session_result["success"]:
                return DropoutAnalysisResponse(success=False, error_message=session_result["error"])

            session = session_result["session"]
            session_id = session_result["session_id"]

            # ステップ2: データ取得(新しいサービス使用)
            data_result = self._data_acquisition_service.acquire_episode_data(request.ncode, session)

            if not data_result["success"]:
                return DropoutAnalysisResponse(success=False, error_message=data_result["error"])

            # ステップ3: 分析実行(新しいサービス使用)
            analysis_result = self._analysis_execution_service.execute_analysis(session, request)

            if not analysis_result["success"]:
                return DropoutAnalysisResponse(success=False, error_message=analysis_result["error"])

            # ステップ4: レポート生成(新しいサービス使用)
            report_result = self._report_generation_service.generate_reports(session, request)

            if not report_result["success"]:
                return DropoutAnalysisResponse(success=False, error_message=report_result["error"])

            # ステップ5: セッション完了
            session.complete()

            # ステップ6: レスポンス生成
            return DropoutAnalysisResponse(
                success=True,
                session_id=session_id,
                average_dropout_rate=analysis_result["average_dropout_rate"].value,
                critical_episodes=[
                    {"episode": episode.episode_number, "dropout_rate": episode.dropout_rate.value}
                    for episode in analysis_result["critical_episodes"]
                ],
                recommendations=analysis_result["recommendations"],
                report_path=report_result["report_path"],
                yaml_path=report_result["yaml_path"],
            )

        except Exception as e:
            return DropoutAnalysisResponse(
                success=False,
                error_message=f"分析エラー: {e!s}",
            )

    def get_session_summary(self, session_id: str) -> dict[str, Any] | None:
        """セッションのサマリーを取得(新しいサービス使用)

        Args:
            session_id: セッションID

        Returns:
            セッションサマリー
        """
        return self._session_management_service.get_session_summary(session_id)

    def bulk_analyze(self, project_ids: list[str], ncodes: list[str], days: int = 30) -> list[DropoutAnalysisResponse]:
        """複数プロジェクトの一括分析(新しいサービス使用)

        Args:
            project_ids: プロジェクトIDリスト
            ncodes: 小説コードリスト
            days: 分析日数

        Returns:
            分析結果リスト
        """
        return self._bulk_analysis_service.bulk_analyze(project_ids, ncodes, days)

    def compare_periods(
        self, project_id: str, ncode: str, period1_days: int = 30, period2_days: int = 7
    ) -> dict[str, Any]:
        """期間比較分析(新しいサービス使用)

        Args:
            project_id: プロジェクトID
            ncode: 小説コード
            period1_days: 期間1の日数
            period2_days: 期間2の日数

        Returns:
            比較結果
        """
        comparison_result = self._period_comparison_service.compare_periods(
            project_id, ncode, period1_days, period2_days
        )

        if comparison_result["success"]:
            return comparison_result["comparison"]
        return {"error": comparison_result["error"]}
