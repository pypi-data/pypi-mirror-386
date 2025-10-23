#!/usr/bin/env python3

"""Domain.services.dropout_analysis_services
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""ドロップアウト分析関連ドメインサービス集

DropoutAnalysisUseCaseから分離された専門ロジックを格納
"""


import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Protocol

from noveler.domain.entities.dropout_analysis_session import (
    AnalysisPeriod,
    DropoutAnalysisSession,
    EpisodeMetrics,
)
from noveler.domain.value_objects.project_time import project_now

if TYPE_CHECKING:

    from pathlib import Path

    from noveler.domain.services.dropout_analysis_service import DataValidationService


class KasasagiClient(Protocol):
    """KASASAGIクライアントのプロトコル"""

    def fetch_analytics_data(self, ncode: str, days: int) -> dict[str, Any]:
        """分析データを取得"""
        ...

    def fetch_episode_access(self, ncode: str) -> list[dict[str, Any]]:
        """エピソード別アクセスデータを取得"""
        ...


class ReportGenerator(Protocol):
    """レポート生成器のプロトコル"""

    def generate_markdown_report(self, session: DropoutAnalysisSession, output_path: Path | None = None) -> Path | None:
        """Markdownレポートを生成"""
        ...

    def save_analysis_yaml(self, session: DropoutAnalysisSession, output_path: Path | None = None) -> Path | None:
        """YAML分析結果を保存"""
        ...


@dataclass(frozen=True)
class DropoutAnalysisRequest:
    """離脱率分析リクエスト"""

    project_id: str
    ncode: str
    days: int = 14
    output_path: Path | None = None
    episodes_only: bool = False
    config: dict[str, Any] | None = None


@dataclass
class DropoutAnalysisResponse:
    """離脱率分析レスポンス"""

    success: bool
    session_id: str | None = None
    average_dropout_rate: float | None = None
    critical_episodes: list[dict[str, Any]] | None = None
    recommendations: list[str] | None = None
    report_path: Path | None = None
    yaml_path: Path | None = None
    error_message: str | None = None


class DropoutDataAcquisitionService:
    """ドロップアウトデータ取得専用サービス"""

    def __init__(self, kasasagi_client: KasasagiClient | None = None) -> None:
        self.kasasagi_client = kasasagi_client

    def acquire_episode_data(self, ncode: str, session: DropoutAnalysisSession) -> dict[str, Any]:
        """KASASAGIからエピソードデータを取得してセッションに追加"""
        try:
            if not self.kasasagi_client:
                return {"success": False, "error": "KASASAGIクライアントが利用できません"}

            episode_data: dict[str, Any] = self.kasasagi_client.fetch_episode_access(ncode)

            # データをドメインオブジェクトに変換
            for ep_data in episode_data:
                metrics = EpisodeMetrics(
                    episode_number=ep_data["episode_number"],
                    episode_title=ep_data["episode_title"],
                    page_views=ep_data["pv"],
                    unique_users=ep_data["ua"],
                    access_date=project_now().datetime.date(),
                )

                session.add_episode_metrics(metrics)

            return {"success": True, "episodes_count": len(episode_data)}

        except Exception as e:
            return {"success": False, "error": f"データ取得エラー: {e}"}


class DropoutSessionManagementService:
    """ドロップアウトセッション管理専用サービス"""

    def __init__(self) -> None:
        self._sessions: dict[str, DropoutAnalysisSession] = {}

    def create_session(self, request: DropoutAnalysisRequest) -> dict[str, Any]:
        """分析セッションを作成"""
        try:
            # 分析期間の設定
            end_date = project_now().datetime.date()
            start_date = end_date - timedelta(days=request.days - 1)
            period = AnalysisPeriod(start_date=start_date, end_date=end_date)

            # セッション作成
            session_id = str(uuid.uuid4())
            session = DropoutAnalysisSession(
                session_id=session_id,
                project_id=request.project_id,
                ncode=request.ncode,
                analysis_period=period,
                config=request.config,
            )

            self._sessions[session_id] = session

            return {
                "success": True,
                "session_id": session_id,
                "session": session,
            }

        except Exception as e:
            return {"success": False, "error": f"セッション作成エラー: {e}"}

    def get_session(self, session_id: str) -> DropoutAnalysisSession | None:
        """セッションを取得"""
        return self._sessions.get(session_id)

    def get_session_summary(self, session_id: str) -> dict[str, Any] | None:
        """セッションサマリーを取得"""
        session = self._sessions.get(session_id)
        if session:
            return session.export_summary()
        return None


class DropoutAnalysisExecutionService:
    """ドロップアウト分析実行専用サービス"""

    def __init__(self, data_validation_service: DataValidationService | None = None) -> None:
        self.data_validation_service = data_validation_service

    def execute_analysis(self, session: DropoutAnalysisSession, request: DropoutAnalysisRequest) -> dict[str, Any]:
        """分析を実行"""
        try:
            # データ検証とフィルタリング
            if self.data_validation_service:
                # 不完全なデータを除外
                session.filter_incomplete_data()

                # データ鮮度の警告を追加
                warning = self.data_validation_service.get_data_freshness_warning()
                if session.config is None:
                    session.config = {}
                session.config["data_freshness_warning"] = warning

            # 分析実行
            avg_rate = session.calculate_average_dropout_rate()

            # 閾値設定とクリティカルエピソード特定
            threshold = request.config.get("critical_threshold", 25.0) if request.config else 25.0

            critical_episodes = session.identify_critical_episodes(threshold)
            recommendations = session.generate_recommendations()

            return {
                "success": True,
                "average_dropout_rate": avg_rate,
                "critical_episodes": critical_episodes,
                "recommendations": recommendations,
            }

        except Exception as e:
            return {"success": False, "error": f"分析実行エラー: {e}"}


class DropoutReportGenerationService:
    """ドロップアウトレポート生成専用サービス"""

    def __init__(self, report_generator: ReportGenerator | None = None) -> None:
        self.report_generator = report_generator

    def generate_reports(
        self,
        session: DropoutAnalysisSession,
        request: DropoutAnalysisRequest,
    ) -> dict[str, Any]:
        """レポートを生成"""
        try:
            report_path = None
            yaml_path = None

            if not self.report_generator:
                return {
                    "success": True,
                    "report_path": None,
                    "yaml_path": None,
                    "warning": "レポート生成器が利用できません",
                }

            # Markdownレポート生成
            if not request.episodes_only:
                report_path = self.report_generator.generate_markdown_report(session, request.output_path)

            # YAML分析結果保存(常に保存)
            yaml_path = self.report_generator.save_analysis_yaml(session)

            return {
                "success": True,
                "report_path": report_path,
                "yaml_path": yaml_path,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"レポート生成エラー: {e}",
                "report_path": None,
                "yaml_path": None,
            }


class DropoutBulkAnalysisService:
    """ドロップアウト一括分析専用サービス"""

    def __init__(self, use_case_executor) -> None:
        """
        Args:
            use_case_executor: analyze_dropout_rateメソッドを持つオブジェクト
        """
        self.use_case_executor = use_case_executor

    def bulk_analyze(self, project_ids: list[str], ncodes: list[str], days: int = 30) -> list[DropoutAnalysisResponse]:
        """複数プロジェクトの一括分析"""
        results: list[Any] = []

        for project_id, ncode in zip(project_ids, ncodes, strict=False):
            request = DropoutAnalysisRequest(
                project_id=project_id,
                ncode=ncode,
                days=days,
            )

            response = self.use_case_executor.analyze_dropout_rate(request)
            results.append(response)

        return results


class DropoutPeriodComparisonService:
    """ドロップアウト期間比較専用サービス"""

    def __init__(self, use_case_executor) -> None:
        """
        Args:
            use_case_executor: analyze_dropout_rateメソッドを持つオブジェクト
        """
        self.use_case_executor = use_case_executor

    def compare_periods(
        self,
        project_id: str,
        ncode: str,
        period1_days: int = 30,
        period2_days: int = 7,
    ) -> dict[str, Any]:
        """期間比較分析"""
        try:
            # 期間1の分析
            request1 = DropoutAnalysisRequest(
                project_id=project_id,
                ncode=ncode,
                days=period1_days,
            )

            response1 = self.use_case_executor.analyze_dropout_rate(request1)

            # 期間2の分析
            request2 = DropoutAnalysisRequest(
                project_id=project_id,
                ncode=ncode,
                days=period2_days,
            )

            response2 = self.use_case_executor.analyze_dropout_rate(request2)

            # 比較結果生成
            comparison = {
                "period1": {
                    "days": period1_days,
                    "average_dropout_rate": response1.average_dropout_rate,
                    "critical_episodes_count": len(response1.critical_episodes or []),
                },
                "period2": {
                    "days": period2_days,
                    "average_dropout_rate": response2.average_dropout_rate,
                    "critical_episodes_count": len(response2.critical_episodes or []),
                },
                "improvement": None,
            }

            # 改善度計算
            if response1.average_dropout_rate and response2.average_dropout_rate:
                improvement = response1.average_dropout_rate - response2.average_dropout_rate

                comparison["improvement"] = {
                    "rate_change": improvement,
                    "percentage": improvement / response1.average_dropout_rate * 100,
                    "trend": "improved" if improvement > 0 else "worsened",
                }

            return {"success": True, "comparison": comparison}

        except Exception as e:
            return {"success": False, "error": f"期間比較エラー: {e}"}
