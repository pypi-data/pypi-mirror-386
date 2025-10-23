"""Tools.quality_dashboard_generator
Where: Tool generating quality dashboards.
What: Aggregates quality data and produces visual dashboards for stakeholders.
Why: Provides visibility into quality trends across the project.
"""

from noveler.presentation.shared.shared_utilities import console

"品質ダッシュボード生成システム\n\n仕様書: SPEC-QUALITY-DASHBOARD-001\n統合品質メトリクスの可視化ダッシュボード生成\n\n設計原則:\n    - HTML/CSSベースの軽量ダッシュボード\n- リアルタイム更新対応\n- モバイル対応レスポンシブデザイン\n"
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.services.unified_report_manager import (
    QualityDashboardData,
    UnifiedQualityMetrics,
    UnifiedReportManager,
)


class QualityDashboardGenerator:
    """品質ダッシュボード生成システム

    責務:
        - HTML品質ダッシュボード生成
        - チャート・グラフ統合
        - レスポンシブUI提供
        - リアルタイム更新機能
    """

    def __init__(self, project_root: Path, output_dir: Path | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            output_dir: 出力ディレクトリ
        """
        self.project_root = project_root
        self.output_dir = output_dir or project_root / "reports" / "dashboard"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        self.dashboard_file = self.output_dir / "quality_dashboard.html"
        self.css_file = self.output_dir / "dashboard.css"
        self.js_file = self.output_dir / "dashboard.js"

    def generate_dashboard(self, dashboard_data: QualityDashboardData) -> str:
        """ダッシュボード生成

        Args:
            dashboard_data: ダッシュボードデータ

        Returns:
            生成されたダッシュボードのパス
        """
        self._generate_css()
        self._generate_javascript()
        html_content = self._generate_html(dashboard_data)
        with Path(self.dashboard_file).open("w", encoding="utf-8") as f:
            f.write(html_content)
        console.print(f"品質ダッシュボード生成完了: {self.dashboard_file}")
        return str(self.dashboard_file)

    def _generate_html(self, dashboard_data: QualityDashboardData) -> str:
        """HTMLダッシュボード生成

        Args:
            dashboard_data: ダッシュボードデータ

        Returns:
            HTML文字列
        """
        current_metrics = dashboard_data.current_metrics
        return f"""\n<!DOCTYPE html>\n<html lang="ja">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>DDD品質ダッシュボード - {current_metrics.project_root}</title>\n    <link rel="stylesheet" href="dashboard.css">\n    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n</head>\n<body>\n    <div class="container">\n        <!-- ヘッダー -->\n        <header class="dashboard-header">\n            <h1>🎯 DDD品質ダッシュボード</h1>\n            <div class="header-info">\n                <span class="project-name">📁 {Path(current_metrics.project_root).name}</span>\n                <span class="update-time">⏰ {current_metrics.timestamp.strftime("%Y-%m-%d %H:%M:%S")}</span>\n                <span class="execution-context">{self._get_context_emoji(current_metrics.execution_context)} {current_metrics.execution_context}</span>\n            </div>\n        </header>\n\n        <!-- アラート -->\n        {self._generate_alerts_section(dashboard_data.quality_alerts)}\n\n        <!-- メインメトリクス -->\n        <div class="metrics-grid">\n            {self._generate_main_metrics(current_metrics)}\n        </div>\n\n        <!-- チャートセクション -->\n        <div class="charts-section">\n            <div class="chart-container">\n                <h3>📈 準拠率トレンド</h3>\n                <canvas id="complianceChart"></canvas>\n            </div>\n\n            <div class="chart-container">\n                <h3>🚨 違反トレンド</h3>\n                <canvas id="violationChart"></canvas>\n            </div>\n\n            <div class="chart-container">\n                <h3>⚡ パフォーマンス</h3>\n                <canvas id="performanceChart"></canvas>\n            </div>\n        </div>\n\n        <!-- 詳細情報 -->\n        <div class="details-section">\n            <div class="detail-card">\n                <h3>🏗️ アーキテクチャ影響</h3>\n                {self._generate_architecture_details(current_metrics)}\n            </div>\n\n            <div class="detail-card">\n                <h3>💡 改善推奨事項</h3>\n                {self._generate_recommendations(dashboard_data.improvement_recommendations)}\n            </div>\n\n            <div class="detail-card">\n                <h3>📊 履歴サマリー</h3>\n                {self._generate_history_summary(dashboard_data.historical_trends)}\n            </div>\n        </div>\n\n        <!-- フッター -->\n        <footer class="dashboard-footer">\n            <p>Generated by DDD Quality System | {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}</p>\n            <p>Execution ID: <code>{current_metrics.execution_id}</code></p>\n        </footer>\n    </div>\n\n    <!-- JavaScript -->\n    <script src="dashboard.js"></script>\n    <script>\n        // チャートデータ\n        const dashboardData = {json.dumps(self._prepare_chart_data(dashboard_data), ensure_ascii=False, indent=2)};\n\n        // チャート初期化\n        initializeCharts(dashboardData);\n    </script>\n</body>\n</html>\n"""

    def _generate_css(self) -> None:
        """CSSスタイル生成"""
        css_content = "\n/* Dashboard Base Styles */\n* {\n    margin: 0;\n    padding: 0;\n    box-sizing: border-box;\n}\n\nbody {\n    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;\n    line-height: 1.6;\n    color: #333;\n    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n    min-height: 100vh;\n}\n\n.container {\n    max-width: 1200px;\n    margin: 0 auto;\n    padding: 20px;\n}\n\n/* Header */\n.dashboard-header {\n    background: rgba(255, 255, 255, 0.95);\n    border-radius: 12px;\n    padding: 20px;\n    margin-bottom: 20px;\n    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);\n    backdrop-filter: blur(10px);\n}\n\n.dashboard-header h1 {\n    font-size: 2.5em;\n    font-weight: 700;\n    margin-bottom: 10px;\n    background: linear-gradient(45deg, #667eea, #764ba2);\n    -webkit-background-clip: text;\n    -webkit-text-fill-color: transparent;\n}\n\n.header-info {\n    display: flex;\n    gap: 20px;\n    flex-wrap: wrap;\n}\n\n.header-info span {\n    background: #f8f9fa;\n    padding: 6px 12px;\n    border-radius: 20px;\n    font-size: 0.9em;\n    font-weight: 500;\n}\n\n/* Alerts */\n.alerts-section {\n    margin-bottom: 20px;\n}\n\n.alert {\n    background: rgba(255, 255, 255, 0.95);\n    border: 1px solid #dee2e6;\n    border-radius: 8px;\n    padding: 12px 16px;\n    margin-bottom: 8px;\n    backdrop-filter: blur(10px);\n}\n\n.alert.warning {\n    border-left: 4px solid #ffc107;\n    background: rgba(255, 243, 205, 0.95);\n}\n\n.alert.error {\n    border-left: 4px solid #dc3545;\n    background: rgba(248, 215, 218, 0.95);\n}\n\n/* Metrics Grid */\n.metrics-grid {\n    display: grid;\n    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));\n    gap: 20px;\n    margin-bottom: 30px;\n}\n\n.metric-card {\n    background: rgba(255, 255, 255, 0.95);\n    border-radius: 12px;\n    padding: 20px;\n    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);\n    backdrop-filter: blur(10px);\n    transition: transform 0.3s ease;\n}\n\n.metric-card:hover {\n    transform: translateY(-2px);\n}\n\n.metric-card h3 {\n    font-size: 1.1em;\n    font-weight: 600;\n    margin-bottom: 10px;\n    color: #6c757d;\n}\n\n.metric-value {\n    font-size: 2.2em;\n    font-weight: 700;\n    margin-bottom: 5px;\n}\n\n.metric-trend {\n    font-size: 0.9em;\n    font-weight: 500;\n}\n\n.trend-positive {\n    color: #28a745;\n}\n\n.trend-negative {\n    color: #dc3545;\n}\n\n.trend-neutral {\n    color: #6c757d;\n}\n\n/* Charts Section */\n.charts-section {\n    display: grid;\n    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));\n    gap: 20px;\n    margin-bottom: 30px;\n}\n\n.chart-container {\n    background: rgba(255, 255, 255, 0.95);\n    border-radius: 12px;\n    padding: 20px;\n    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);\n    backdrop-filter: blur(10px);\n}\n\n.chart-container h3 {\n    font-size: 1.2em;\n    font-weight: 600;\n    margin-bottom: 15px;\n    color: #495057;\n}\n\n/* Details Section */\n.details-section {\n    display: grid;\n    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));\n    gap: 20px;\n    margin-bottom: 30px;\n}\n\n.detail-card {\n    background: rgba(255, 255, 255, 0.95);\n    border-radius: 12px;\n    padding: 20px;\n    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);\n    backdrop-filter: blur(10px);\n}\n\n.detail-card h3 {\n    font-size: 1.2em;\n    font-weight: 600;\n    margin-bottom: 15px;\n    color: #495057;\n}\n\n.detail-card ul {\n    list-style: none;\n    padding: 0;\n}\n\n.detail-card li {\n    padding: 8px 0;\n    border-bottom: 1px solid #e9ecef;\n}\n\n.detail-card li:last-child {\n    border-bottom: none;\n}\n\n/* Footer */\n.dashboard-footer {\n    background: rgba(255, 255, 255, 0.95);\n    border-radius: 12px;\n    padding: 15px;\n    text-align: center;\n    color: #6c757d;\n    font-size: 0.9em;\n    backdrop-filter: blur(10px);\n}\n\n.dashboard-footer code {\n    background: #f8f9fa;\n    padding: 2px 6px;\n    border-radius: 4px;\n    font-family: 'Monaco', 'Consolas', monospace;\n}\n\n/* Responsive Design */\n@media (max-width: 768px) {\n    .container {\n        padding: 10px;\n    }\n\n    .dashboard-header h1 {\n        font-size: 2em;\n    }\n\n    .header-info {\n        flex-direction: column;\n        gap: 10px;\n    }\n\n    .metrics-grid {\n        grid-template-columns: 1fr;\n    }\n\n    .charts-section {\n        grid-template-columns: 1fr;\n    }\n\n    .details-section {\n        grid-template-columns: 1fr;\n    }\n}\n\n/* Grade Colors */\n.grade-a { color: #28a745; }\n.grade-b { color: #17a2b8; }\n.grade-c { color: #ffc107; }\n.grade-d { color: #dc3545; }\n\n/* Progress Bars */\n.progress {\n    background-color: #e9ecef;\n    border-radius: 4px;\n    height: 8px;\n    overflow: hidden;\n    margin-top: 5px;\n}\n\n.progress-bar {\n    height: 100%;\n    background: linear-gradient(45deg, #28a745, #20c997);\n    transition: width 0.6s ease;\n}\n"
        with Path(self.css_file).open("w", encoding="utf-8") as f:
            f.write(css_content)

    def _generate_javascript(self) -> None:
        """JavaScript生成"""
        js_content = "\n// Dashboard JavaScript Functions\n\nfunction initializeCharts(data) {\n    initComplianceChart(data.compliance_history);\n    initViolationChart(data.violation_trends);\n    initPerformanceChart(data.performance_metrics);\n}\n\nfunction initComplianceChart(complianceData) {\n    const ctx = document.getElementById('complianceChart').getContext('2d');\n\n    new Chart(ctx, {\n        type: 'line',\n        data: {\n            labels: complianceData.map(d => new Date(d.timestamp).toLocaleDateString()),\n            datasets: [{\n                label: '準拠率 (%)',\n                data: complianceData.map(d => d.compliance_percentage),\n                borderColor: '#667eea',\n                backgroundColor: 'rgba(102, 126, 234, 0.1)',\n                fill: true,\n                tension: 0.4\n            }]\n        },\n        options: {\n            responsive: true,\n            scales: {\n                y: {\n                    beginAtZero: true,\n                    max: 100\n                }\n            },\n            plugins: {\n                legend: {\n                    display: true\n                }\n            }\n        }\n    });\n}\n\nfunction initViolationChart(violationData) {\n    const ctx = document.getElementById('violationChart').getContext('2d');\n\n    new Chart(ctx, {\n        type: 'bar',\n        data: {\n            labels: violationData.map(d => new Date(d.timestamp).toLocaleDateString()),\n            datasets: [{\n                label: '違反数',\n                data: violationData.map(d => d.total_violations),\n                backgroundColor: 'rgba(220, 53, 69, 0.8)',\n                borderColor: '#dc3545',\n                borderWidth: 1\n            }]\n        },\n        options: {\n            responsive: true,\n            scales: {\n                y: {\n                    beginAtZero: true\n                }\n            }\n        }\n    });\n}\n\nfunction initPerformanceChart(performanceData) {\n    const ctx = document.getElementById('performanceChart').getContext('2d');\n\n    new Chart(ctx, {\n        type: 'line',\n        data: {\n            labels: performanceData.map(d => new Date(d.timestamp).toLocaleDateString()),\n            datasets: [\n                {\n                    label: '実行時間 (秒)',\n                    data: performanceData.map(d => d.analysis_duration),\n                    borderColor: '#28a745',\n                    backgroundColor: 'rgba(40, 167, 69, 0.1)',\n                    yAxisID: 'y'\n                },\n                {\n                    label: 'キャッシュヒット率 (%)',\n                    data: performanceData.map(d => d.cache_hit_rate * 100),\n                    borderColor: '#17a2b8',\n                    backgroundColor: 'rgba(23, 162, 184, 0.1)',\n                    yAxisID: 'y1'\n                }\n            ]\n        },\n        options: {\n            responsive: true,\n            scales: {\n                y: {\n                    type: 'linear',\n                    display: true,\n                    position: 'left',\n                    title: {\n                        display: true,\n                        text: '実行時間 (秒)'\n                    }\n                },\n                y1: {\n                    type: 'linear',\n                    display: true,\n                    position: 'right',\n                    max: 100,\n                    title: {\n                        display: true,\n                        text: 'キャッシュヒット率 (%)'\n                    },\n                    grid: {\n                        drawOnChartArea: false,\n                    },\n                }\n            }\n        }\n    });\n}\n\n// Auto refresh (optional)\nfunction enableAutoRefresh(intervalMinutes = 5) {\n    setInterval(() => {\n        location.reload();\n    }, intervalMinutes * 60 * 1000);\n}\n\n// Page load\ndocument.addEventListener('DOMContentLoaded', function() {\n    console.log('DDD Quality Dashboard loaded');\n});\n"
        with Path(self.js_file).open("w", encoding="utf-8") as f:
            f.write(js_content)

    def _generate_alerts_section(self, alerts: list[str]) -> str:
        """アラートセクション生成"""
        if not alerts:
            return ""
        alert_html = '<div class="alerts-section">'
        for alert in alerts:
            alert_class = "error" if "🔴" in alert or "🚨" in alert else "warning"
            alert_html += f'<div class="alert {alert_class}">{alert}</div>'
        alert_html += "</div>"
        return alert_html

    def _generate_main_metrics(self, metrics: UnifiedQualityMetrics) -> str:
        """メインメトリクス生成"""
        grade = self._calculate_quality_grade(metrics.ddd_compliance_percentage)
        grade_class = f"grade-{grade.lower()}"
        compliance_trend = metrics.compliance_trend or 0
        trend_class = (
            "trend-positive" if compliance_trend > 0 else "trend-negative" if compliance_trend < 0 else "trend-neutral"
        )
        trend_icon = "📈" if compliance_trend > 0 else "📉" if compliance_trend < 0 else "➡️"
        return f'\n        <div class="metric-card">\n            <h3>🎯 DDD準拠率</h3>\n            <div class="metric-value {grade_class}">{metrics.ddd_compliance_percentage:.1f}%</div>\n            <div class="metric-trend {trend_class}">{trend_icon} {compliance_trend:+.1f}%</div>\n            <div class="progress">\n                <div class="progress-bar" style="width: {metrics.ddd_compliance_percentage}%"></div>\n            </div>\n        </div>\n\n        <div class="metric-card">\n            <h3>🚨 違反数</h3>\n            <div class="metric-value">{metrics.ddd_violations_total}</div>\n            <div class="metric-trend">\n                重要度別: {metrics.ddd_violations_by_severity}\n            </div>\n        </div>\n\n        <div class="metric-card">\n            <h3>⚡ 実行時間</h3>\n            <div class="metric-value">{metrics.analysis_duration_seconds:.2f}s</div>\n            <div class="metric-trend">\n                📁 分析ファイル数: {metrics.files_analyzed}\n            </div>\n        </div>\n\n        <div class="metric-card">\n            <h3>💾 キャッシュ効率</h3>\n            <div class="metric-value">{metrics.cache_hit_rate * 100:.1f}%</div>\n            <div class="metric-trend">\n                🔄 変更ファイル数: {metrics.changed_files_count}\n            </div>\n        </div>\n        '

    def _generate_architecture_details(self, metrics: UnifiedQualityMetrics) -> str:
        """アーキテクチャ詳細生成"""
        return f"\n        <ul>\n            <li><strong>影響レベル:</strong> {metrics.impact_level}</li>\n            <li><strong>変更ファイル数:</strong> {metrics.changed_files_count}</li>\n            <li><strong>影響を受ける層:</strong> {(', '.join(metrics.affected_layers) if metrics.affected_layers else 'なし')}</li>\n            <li><strong>実行コンテキスト:</strong> {metrics.execution_context}</li>\n            <li><strong>Gitブランチ:</strong> {metrics.git_branch}</li>\n        </ul>\n        "

    def _generate_recommendations(self, recommendations: list[str]) -> str:
        """推奨事項生成"""
        if not recommendations:
            return "<p>🎉 現在特別な推奨事項はありません。品質が維持されています。</p>"
        rec_html = "<ul>"
        for rec in recommendations:
            rec_html += f"<li>{rec}</li>"
        rec_html += "</ul>"
        return rec_html

    def _generate_history_summary(self, historical_trends: list[Any] | None) -> str:
        """履歴サマリー生成"""
        if not historical_trends:
            return "<p>履歴データがありません。</p>"
        recent_count = len(historical_trends)
        avg_compliance = sum(t.ddd_compliance_percentage for t in historical_trends) / recent_count
        return f"\n        <ul>\n            <li><strong>最近の分析回数:</strong> {recent_count}回</li>\n            <li><strong>平均準拠率:</strong> {avg_compliance:.1f}%</li>\n            <li><strong>最新分析:</strong> {historical_trends[-1].timestamp.strftime('%Y-%m-%d %H:%M')}</li>\n        </ul>\n        "

    def _prepare_chart_data(self, dashboard_data: QualityDashboardData) -> dict[str, Any]:
        """チャートデータ準備"""
        return {
            "compliance_history": [
                {"timestamp": item["timestamp"], "compliance_percentage": item["compliance_percentage"]}
                for item in dashboard_data.compliance_history
            ],
            "violation_trends": [
                {"timestamp": item["timestamp"], "total_violations": item["total_violations"]}
                for item in dashboard_data.violation_trends
            ],
            "performance_metrics": [
                {
                    "timestamp": item["timestamp"],
                    "analysis_duration": item["analysis_duration"],
                    "cache_hit_rate": item["cache_hit_rate"],
                }
                for item in dashboard_data.performance_metrics
            ],
        }

    def _get_context_emoji(self, context: str) -> str:
        """実行コンテキストの絵文字取得"""
        context_emojis = {"pre-commit": "🔧", "ci": "🏗️", "manual": "👤", "scheduled": "⏰"}
        return context_emojis.get(context, "📋")

    def _calculate_quality_grade(self, compliance_percentage: float) -> str:
        """品質グレード算出"""
        if compliance_percentage >= 95:
            return "A"
        if compliance_percentage >= 80:
            return "B"
        if compliance_percentage >= 60:
            return "C"
        return "D"

    def generate_quick_dashboard(self, project_root: Path) -> str:
        """クイックダッシュボード生成

        Args:
            project_root: プロジェクトルート

        Returns:
            ダッシュボードファイルパス
        """
        report_manager = UnifiedReportManager(project_root)
        dummy_metrics = UnifiedQualityMetrics(
            timestamp=datetime.now(timezone.utc),
            execution_context="manual",
            project_root=str(project_root),
            ddd_compliance_percentage=85.0,
            ddd_violations_total=15,
            ddd_violations_by_severity={"HIGH": 2, "MEDIUM": 8, "LOW": 5},
            changed_files_count=5,
            impact_level="medium",
            affected_layers=["domain", "application"],
            analysis_duration_seconds=2.5,
            cache_hit_rate=0.75,
            files_analyzed=150,
            compliance_trend=2.3,
            violation_trend=-3,
            git_commit_hash="abc123",
            git_branch="main",
            execution_id="quick-demo-123",
        )
        dashboard_data = report_manager.generate_dashboard_data(dummy_metrics, history_days=7)
        return self.generate_dashboard(dashboard_data)


if __name__ == "__main__":
    import sys

    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path()
    generator = QualityDashboardGenerator(project_root)
    dashboard_path = generator.generate_quick_dashboard(project_root)
    console.print(f"✅ 品質ダッシュボード生成完了: {dashboard_path}")
    console.print(f"🌐 ブラウザで確認: file://{Path(dashboard_path).absolute()}")
