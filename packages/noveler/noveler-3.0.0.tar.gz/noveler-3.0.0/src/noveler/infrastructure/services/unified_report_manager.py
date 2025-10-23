"""Infrastructure.services.unified_report_manager
Where: Infrastructure service managing unified report generation.
What: Collects data from multiple sources and produces consolidated reports.
Why: Provides stakeholders with cohesive reporting across systems.
"""

from noveler.presentation.shared.shared_utilities import console

"統合レポート管理システム\n\n仕様書: SPEC-UNIFIED-REPORT-001\npre-commitとCI/CDレポートの統合管理\n\n設計原則:\n    - レポート形式の標準化\n- 可視化データの統一\n- パフォーマンスメトリクス収集\n"
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger

try:
    from noveler.infrastructure.services.unified_file_storage_service import FileContentType, UnifiedFileStorageService
except ImportError:
    # 開発時のフォールバック
    UnifiedFileStorageService = None
    FileContentType = None


class ViolationSeverity(Enum):
    """違反重要度（循環依存解消）"""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ValidationLevel(Enum):
    """検証レベル（循環依存解消）"""

    STRICT = "STRICT"
    MODERATE = "MODERATE"
    BASIC = "BASIC"


class ImpactLevel(Enum):
    """影響レベル（循環依存解消）"""

    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DDDViolation:
    """DDD違反情報（循環依存解消）"""

    file_path: str
    line_number: int
    violation_type: str
    severity: ViolationSeverity
    description: str
    recommendation: str
    rule_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceReport:
    """DDD準拠性レポート（循環依存解消）"""

    timestamp: datetime
    project_root: str
    validation_level: ValidationLevel
    total_files_analyzed: int
    violations: list[DDDViolation]
    compliance_percentage: float
    layer_compliance: dict[str, float]
    summary: dict[str, Any]


@dataclass
class ChangeImpactAnalysis:
    """変更影響分析（循環依存解消）"""

    changed_files: list[str]
    overall_impact_level: ImpactLevel
    affected_layers: set[str]


@dataclass
class UnifiedQualityMetrics:
    """統合品質メトリクス"""

    timestamp: datetime
    execution_context: str
    project_root: str
    ddd_compliance_percentage: float
    ddd_violations_total: int
    ddd_violations_by_severity: dict[str, int]
    changed_files_count: int
    impact_level: str
    affected_layers: list[str]
    analysis_duration_seconds: float
    cache_hit_rate: float
    files_analyzed: int
    compliance_trend: float | None
    violation_trend: int | None
    git_commit_hash: str | None
    git_branch: str
    execution_id: str


@dataclass
class QualityDashboardData:
    """品質ダッシュボードデータ"""

    current_metrics: UnifiedQualityMetrics
    historical_trends: list[UnifiedQualityMetrics]
    compliance_history: list[dict[str, Any]]
    violation_trends: list[dict[str, Any]]
    performance_metrics: list[dict[str, Any]]
    quality_alerts: list[str]
    improvement_recommendations: list[str]


class UnifiedReportManager:
    """統合レポート管理システム

    責務:
        - pre-commitとCI/CDレポートの統合
        - 品質メトリクスの標準化
        - ダッシュボードデータ生成
        - 履歴管理とトレンド分析
    """

    def __init__(self, project_root: Path, reports_dir: Path | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            reports_dir: レポート出力ディレクトリ
        """
        self.project_root = project_root
        self.reports_dir = reports_dir or project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.logger = get_logger(__name__)
        self.metrics_history_file = self.reports_dir / "quality_metrics_history.jsonl"
        self.dashboard_data_file = self.reports_dir / "dashboard_data.json"
        self.summary_report_file = self.reports_dir / "quality_summary.json"

    def create_unified_metrics(
        self,
        compliance_report: ComplianceReport,
        change_analysis: ChangeImpactAnalysis | None = None,
        execution_context: str = "manual",
        analysis_duration: float = 0.0,
        cache_hit_rate: float = 0.0,
    ) -> UnifiedQualityMetrics:
        """統合品質メトリクス生成

        Args:
            compliance_report: DDD準拠性レポート
            change_analysis: 変更影響分析結果
            execution_context: 実行コンテキスト
            analysis_duration: 分析所要時間
            cache_hit_rate: キャッシュヒット率

        Returns:
            統合品質メトリクス
        """
        violations_by_severity = {}
        for violation in compliance_report.violations:
            severity = violation.severity.value
            violations_by_severity[severity] = violations_by_severity.get(severity, 0) + 1
        changed_files_count = len(change_analysis.changed_files) if change_analysis else 0
        impact_level = change_analysis.overall_impact_level.value if change_analysis else "minimal"
        affected_layers = list(change_analysis.affected_layers) if change_analysis else []
        git_info = self._get_git_info()
        execution_id = self._generate_execution_id()
        (compliance_trend, violation_trend) = self._calculate_trends(compliance_report)
        return UnifiedQualityMetrics(
            timestamp=datetime.now(timezone.utc),
            execution_context=execution_context,
            project_root=str(self.project_root),
            ddd_compliance_percentage=compliance_report.compliance_percentage,
            ddd_violations_total=len(compliance_report.violations),
            ddd_violations_by_severity=violations_by_severity,
            changed_files_count=changed_files_count,
            impact_level=impact_level,
            affected_layers=affected_layers,
            analysis_duration_seconds=analysis_duration,
            cache_hit_rate=cache_hit_rate,
            files_analyzed=compliance_report.total_files_analyzed,
            compliance_trend=compliance_trend,
            violation_trend=violation_trend,
            git_commit_hash=git_info.get("commit_hash"),
            git_branch=git_info.get("branch", "unknown"),
            execution_id=execution_id,
        )

    def save_metrics(self, metrics: UnifiedQualityMetrics) -> None:
        """メトリクスの保存

        Args:
            metrics: 統合品質メトリクス
        """
        try:
            with open(self.metrics_history_file, "a", encoding="utf-8") as f:
                metrics_dict = asdict(metrics)
                metrics_dict["timestamp"] = metrics.timestamp.isoformat()
                f.write(json.dumps(metrics_dict, ensure_ascii=False) + "\n")
            console.print(f"品質メトリクス保存完了: {metrics.execution_id}")
        except (OSError, json.JSONEncodeError) as e:
            self.logger.exception("メトリクス保存エラー: %s", e)

    def generate_dashboard_data(
        self, current_metrics: UnifiedQualityMetrics, history_days: int = 30
    ) -> QualityDashboardData:
        """ダッシュボードデータ生成

        Args:
            current_metrics: 現在のメトリクス
            history_days: 履歴取得期間（日数）

        Returns:
            品質ダッシュボードデータ
        """
        historical_metrics = self._load_historical_metrics(history_days)
        compliance_history = self._generate_compliance_history(historical_metrics)
        violation_trends = self._generate_violation_trends(historical_metrics)
        performance_metrics = self._generate_performance_metrics(historical_metrics)
        quality_alerts = self._generate_quality_alerts(current_metrics, historical_metrics)
        improvement_recommendations = self._generate_improvement_recommendations(current_metrics, historical_metrics)
        return QualityDashboardData(
            current_metrics=current_metrics,
            historical_trends=historical_metrics[-10:],
            compliance_history=compliance_history,
            violation_trends=violation_trends,
            performance_metrics=performance_metrics,
            quality_alerts=quality_alerts,
            improvement_recommendations=improvement_recommendations,
        )

    def export_dashboard_data(self, dashboard_data: QualityDashboardData) -> None:
        """ダッシュボードデータのエクスポート

        Args:
            dashboard_data: ダッシュボードデータ
        """
        try:
            dashboard_dict = asdict(dashboard_data)
            dashboard_dict["current_metrics"]["timestamp"] = dashboard_data.current_metrics.timestamp.isoformat()
            for trend in dashboard_dict["historical_trends"]:
                if isinstance(trend["timestamp"], datetime):
                    trend["timestamp"] = trend["timestamp"].isoformat()
            with open(self.dashboard_data_file, "w", encoding="utf-8") as f:
                json.dump(dashboard_dict, f, ensure_ascii=False, indent=2)
            console.print(f"ダッシュボードデータエクスポート完了: {self.dashboard_data_file}")
        except (OSError, json.JSONEncodeError) as e:
            self.logger.exception("ダッシュボードデータエクスポートエラー: %s", e)

    def generate_summary_report(self, metrics: UnifiedQualityMetrics) -> dict[str, Any]:
        """サマリーレポート生成

        Args:
            metrics: 統合品質メトリクス

        Returns:
            サマリーレポートデータ
        """
        return {
            "execution_info": {
                "timestamp": metrics.timestamp.isoformat(),
                "context": metrics.execution_context,
                "execution_id": metrics.execution_id,
                "git_branch": metrics.git_branch,
                "git_commit": metrics.git_commit_hash[:8] if metrics.git_commit_hash else None,
            },
            "quality_overview": {
                "compliance_percentage": round(metrics.ddd_compliance_percentage, 1),
                "total_violations": metrics.ddd_violations_total,
                "quality_grade": self._calculate_quality_grade(metrics),
                "improvement_status": self._determine_improvement_status(metrics),
            },
            "performance_stats": {
                "analysis_duration": round(metrics.analysis_duration_seconds, 2),
                "files_analyzed": metrics.files_analyzed,
                "cache_hit_rate": round(metrics.cache_hit_rate * 100, 1),
                "efficiency_score": self._calculate_efficiency_score(metrics),
            },
            "change_impact": {
                "changed_files": metrics.changed_files_count,
                "impact_level": metrics.impact_level,
                "affected_layers": metrics.affected_layers,
            },
            "trends": {"compliance_trend": metrics.compliance_trend, "violation_trend": metrics.violation_trend},
        }

    def export_summary_report(self, summary: dict[str, Any]) -> None:
        """サマリーレポートのエクスポート

        Args:
            summary: サマリーレポートデータ
        """
        try:
            # UnifiedFileStorageServiceを使用してサマリーレポートを保存
            storage_service = UnifiedFileStorageService()
            storage_service.save(
                file_path=self.summary_report_file,
                content=summary,
                content_type=FileContentType.API_RESPONSE,
                metadata={
                    "report_type": "unified_quality_summary",
                    "execution_id": summary["execution_info"]["execution_id"],
                    "compliance_percentage": summary["quality_overview"]["compliance_percentage"],
                },
            )
            console.print(f"サマリーレポートエクスポート完了: {self.summary_report_file}")
        except (OSError, json.JSONEncodeError) as e:
            self.logger.exception("サマリーレポートエクスポートエラー: %s", e)

    def _get_git_info(self) -> dict[str, str]:
        """Git情報取得"""
        git_info = {}
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], check=False, capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                git_info["commit_hash"] = result.stdout.strip()
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                git_info["branch"] = result.stdout.strip()
        except subprocess.SubprocessError:
            pass
        return git_info

    def _generate_execution_id(self) -> str:
        """実行ID生成"""
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"{timestamp}{self.project_root}".encode()
        return hashlib.sha256(hash_input).hexdigest()[:16]

    def _calculate_trends(self, current_report: ComplianceReport) -> tuple[float | None, int | None]:
        """トレンド計算"""
        try:
            previous_metrics = self._load_historical_metrics(days=1)
            if not previous_metrics:
                return (None, None)
            last_metrics = previous_metrics[-1]
            compliance_trend = current_report.compliance_percentage - last_metrics.ddd_compliance_percentage
            violation_trend = len(current_report.violations) - last_metrics.ddd_violations_total
            return (compliance_trend, violation_trend)
        except (IndexError, KeyError):
            return (None, None)

    def _load_historical_metrics(self, days: int) -> list[UnifiedQualityMetrics]:
        """履歴メトリクス読み込み"""
        if not self.metrics_history_file.exists():
            return []
        cutoff_date = datetime.now(timezone.utc).timestamp() - days * 24 * 60 * 60
        metrics = []
        try:
            with open(self.metrics_history_file, encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(data["timestamp"])
                    if timestamp.timestamp() >= cutoff_date:
                        data["timestamp"] = timestamp
                        metrics.append(UnifiedQualityMetrics(**data))
        except (OSError, json.JSONDecodeError, ValueError) as e:
            console.print(f"履歴メトリクス読み込みエラー: {e}")
        return metrics

    def _generate_compliance_history(self, metrics: list[UnifiedQualityMetrics]) -> list[dict[str, Any]]:
        """準拠率履歴データ生成"""
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "compliance_percentage": m.ddd_compliance_percentage,
                "context": m.execution_context,
            }
            for m in metrics
        ]

    def _generate_violation_trends(self, metrics: list[UnifiedQualityMetrics]) -> list[dict[str, Any]]:
        """違反トレンドデータ生成"""
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "total_violations": m.ddd_violations_total,
                "severity_breakdown": m.ddd_violations_by_severity,
            }
            for m in metrics
        ]

    def _generate_performance_metrics(self, metrics: list[UnifiedQualityMetrics]) -> list[dict[str, Any]]:
        """性能メトリクスデータ生成"""
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "analysis_duration": m.analysis_duration_seconds,
                "cache_hit_rate": m.cache_hit_rate,
                "files_analyzed": m.files_analyzed,
            }
            for m in metrics
        ]

    def _generate_quality_alerts(
        self, current: UnifiedQualityMetrics, historical: list[UnifiedQualityMetrics]
    ) -> list[str]:
        """品質アラート生成"""
        alerts = []
        if current.ddd_compliance_percentage < 70.0:
            alerts.append("🚨 DDD準拠率が70%を下回っています")
        if current.ddd_violations_total > 100:
            alerts.append("⚠️ 違反数が100件を超過しています")
        critical_violations = current.ddd_violations_by_severity.get("CRITICAL", 0)
        if critical_violations > 0:
            alerts.append(f"🔴 クリティカル違反が{critical_violations}件検出されています")
        if current.compliance_trend and current.compliance_trend < -5.0:
            alerts.append("📉 準拠率が大幅に低下しています")
        return alerts

    def _generate_improvement_recommendations(
        self, current: UnifiedQualityMetrics, historical: list[UnifiedQualityMetrics]
    ) -> list[str]:
        """改善推奨事項生成"""
        recommendations = []
        if current.cache_hit_rate < 0.3:
            recommendations.append("💡 キャッシュヒット率向上により分析高速化が可能です")
        if current.ddd_violations_by_severity.get("HIGH", 0) > 10:
            recommendations.append("🎯 高重要度違反の優先的な修正を推奨します")
        if len(current.affected_layers) > 3:
            recommendations.append("🏗️ 複数層にまたがる変更は段階的な修正を検討してください")
        return recommendations

    def _calculate_quality_grade(self, metrics: UnifiedQualityMetrics) -> str:
        """品質グレード算出"""
        compliance = metrics.ddd_compliance_percentage
        if compliance >= 95:
            return "A+"
        if compliance >= 90:
            return "A"
        if compliance >= 80:
            return "B"
        if compliance >= 70:
            return "C"
        return "D"

    def _determine_improvement_status(self, metrics: UnifiedQualityMetrics) -> str:
        """改善状況判定"""
        if metrics.compliance_trend is None:
            return "初回分析"
        if metrics.compliance_trend > 2.0:
            return "大幅改善"
        if metrics.compliance_trend > 0:
            return "改善中"
        if metrics.compliance_trend == 0:
            return "変化なし"
        if metrics.compliance_trend > -2.0:
            return "軽微な低下"
        return "要注意"

    def _calculate_efficiency_score(self, metrics: UnifiedQualityMetrics) -> int:
        """効率スコア算出"""
        time_score = max(0, 100 - metrics.analysis_duration_seconds * 10)
        cache_score = metrics.cache_hit_rate * 100
        file_efficiency = min(100, metrics.files_analyzed / 10)
        return int((time_score + cache_score + file_efficiency) / 3)
