#!/usr/bin/env python3

"""Application.visualizers.content_validation_report_generator
Where: Application visualiser that renders content validation reports.
What: Formats validation outcomes into human-readable summaries.
Why: Makes validation results easy to review and share.
"""

from __future__ import annotations

"""伏線・重要シーン検証結果レポート生成機能

検証結果を視覚的にわかりやすいレポートとして生成し、
執筆者が改善点を把握しやすくする機能を提供。

DDD準拠設計:
- Application層のVisualizerとして実装
- Domain層のValidatorの結果を利用
- Rich形式およびテキスト形式でのレポート生成
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from noveler.application.validators.foreshadowing_content_validator import (
    ForeshadowingValidationResult,
)
from noveler.application.validators.important_scene_validator import SceneValidationResult
from noveler.domain.value_objects.project_time import project_now
from noveler.presentation.shared.shared_utilities import console

# B20準拠: 共有コンソール使用

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class ContentValidationReport:
    """伏線・重要シーン検証の統合レポート"""
    episode_number: int
    foreshadowing_result: ForeshadowingValidationResult
    scene_result: SceneValidationResult
    overall_score: float
    total_issues: int
    critical_issues: int
    generated_at: datetime
    project_name: str = ""

    def has_critical_issues(self) -> bool:
        """致命的な問題があるか"""
        return self.critical_issues > 0

    def get_grade(self) -> str:
        """総合評価グレード"""
        if self.overall_score >= 90:
            return "S"
        if self.overall_score >= 80:
            return "A"
        if self.overall_score >= 70:
            return "B"
        if self.overall_score >= 60:
            return "C"
        return "D"


class ContentValidationReportGenerator:
    """伏線・重要シーン検証レポート生成クラス

    SPEC-CONTENT-VALIDATION-REPORT-001: 検証結果可視化システム
    """

    def __init__(self, console_service=None) -> None:
        """初期化

        Args:
            console_service: コンソールサービス（依存性注入）
        """
        # B20準拠: 共有コンソール使用
        if console_service:
            self.console = console_service
        else:
            self.console = console

    def generate_report(self, foreshadowing_result: ForeshadowingValidationResult,
                       scene_result: SceneValidationResult,
                       project_name: str = "") -> ContentValidationReport:
        """統合レポートを生成

        Args:
            foreshadowing_result: 伏線検証結果
            scene_result: 重要シーン検証結果
            project_name: プロジェクト名

        Returns:
            ContentValidationReport: 統合レポート
        """
        # 総合スコア計算
        overall_score = (foreshadowing_result.score + scene_result.score) / 2

        # 問題集計
        all_issues = foreshadowing_result.issues + scene_result.issues
        total_issues = len(all_issues)

        critical_issues = sum(1 for issue in all_issues
                            if self._is_critical_issue(issue))

        return ContentValidationReport(
            episode_number=foreshadowing_result.episode_number,
            foreshadowing_result=foreshadowing_result,
            scene_result=scene_result,
            overall_score=overall_score,
            total_issues=total_issues,
            critical_issues=critical_issues,
            generated_at=project_now().datetime,
            project_name=project_name
        )

    def display_rich_report(self, report: ContentValidationReport) -> None:
        """Richコンソールでレポートを表示"""

        # ヘッダー
        title = f"📝 第{report.episode_number}話 伏線・重要シーン検証レポート"
        if report.project_name:
            title += f" ({report.project_name})"

        self.console.print(Panel(title, style="bold magenta"))

        # 総合サマリー
        self._display_summary_panel(report)

        # 詳細結果
        self._display_detailed_results(report)

        # 改善提案
        if report.total_issues > 0:
            self._display_improvement_suggestions(report)

        # フッター
        self.console.print(f"[dim]生成日時: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

    def _display_summary_panel(self, report: ContentValidationReport) -> None:
        """総合サマリーパネルを表示"""
        grade = report.get_grade()
        grade_color = self._get_grade_color(grade)

        summary_table = Table.grid(padding=1)
        summary_table.add_column(style="cyan")
        summary_table.add_column(style="white")

        summary_table.add_row("📊 総合スコア:", f"[bold {grade_color}]{report.overall_score:.1f}/100 ({grade})[/bold {grade_color}]")
        summary_table.add_row("🎭 伏線スコア:", f"[bold]{report.foreshadowing_result.score:.1f}/100[/bold]")
        summary_table.add_row("🎬 シーンスコア:", f"[bold]{report.scene_result.score:.1f}/100[/bold]")
        summary_table.add_row("⚠️  総問題数:", f"[bold]{report.total_issues}件[/bold]")

        if report.critical_issues > 0:
            summary_table.add_row("🚨 重要問題:", f"[bold red]{report.critical_issues}件[/bold red]")

        self.console.print(Panel(summary_table, title="📋 検証サマリー", border_style="blue"))

    def _display_detailed_results(self, report: ContentValidationReport) -> None:
        """詳細結果を表示"""
        # 伏線詳細
        self.console.print("\n[bold blue]🎭 伏線検証詳細[/bold blue]")

        foreshadowing_table = Table()
        foreshadowing_table.add_column("項目", style="cyan")
        foreshadowing_table.add_column("結果", justify="right")

        foreshadowing_table.add_row("検証対象", f"{report.foreshadowing_result.total_foreshadowing_checked}件")
        foreshadowing_table.add_row("仕込み済み", f"[green]{report.foreshadowing_result.planted_count}件[/green]")
        foreshadowing_table.add_row("回収済み", f"[green]{report.foreshadowing_result.resolved_count}件[/green]")
        foreshadowing_table.add_row("未仕込み", f"[yellow]{len(report.foreshadowing_result.missing_plantings)}件[/yellow]")
        foreshadowing_table.add_row("未回収", f"[yellow]{len(report.foreshadowing_result.missing_resolutions)}件[/yellow]")

        self.console.print(foreshadowing_table)

        # 重要シーン詳細
        self.console.print("\n[bold blue]🎬 重要シーン検証詳細[/bold blue]")

        scene_table = Table()
        scene_table.add_column("項目", style="cyan")
        scene_table.add_column("結果", justify="right")

        scene_table.add_row("検証対象", f"{report.scene_result.total_scenes_checked}件")
        scene_table.add_row("実装済み", f"[green]{report.scene_result.scenes_implemented}件[/green]")
        scene_table.add_row("未実装", f"[yellow]{len(report.scene_result.missing_scenes)}件[/yellow]")
        scene_table.add_row("不完全", f"[yellow]{len(report.scene_result.incomplete_scenes)}件[/yellow]")

        self.console.print(scene_table)

    def _display_improvement_suggestions(self, report: ContentValidationReport) -> None:
        """改善提案を表示"""
        self.console.print("\n[bold yellow]💡 改善提案[/bold yellow]")

        all_issues = report.foreshadowing_result.issues + report.scene_result.issues

        # 重要度別に問題を分類
        critical_issues = []
        high_issues = []
        other_issues = []

        for issue in all_issues:
            if self._is_critical_issue(issue):
                critical_issues.append(issue)
            elif self._is_high_issue(issue):
                high_issues.append(issue)
            else:
                other_issues.append(issue)

        # 致命的問題
        if critical_issues:
            self.console.print("[bold red]🚨 緊急対応が必要[/bold red]")
            for issue in critical_issues[:5]:  # 最初の5件
                self._get_issue_title(issue)
                self.console.print(f"  • {escape(issue.message)}")
                if issue.suggestion:
                    self.console.print(f"    [dim]→ {escape(issue.suggestion)}[/dim]")

        # 高重要度問題
        if high_issues:
            self.console.print("\n[bold yellow]⚠️  改善推奨[/bold yellow]")
            for issue in high_issues[:3]:  # 最初の3件
                self._get_issue_title(issue)
                self.console.print(f"  • {escape(issue.message)}")
                if issue.suggestion:
                    self.console.print(f"    [dim]→ {escape(issue.suggestion)}[/dim]")

        # その他の問題サマリー
        if other_issues:
            self.console.print(f"\n[dim]その他の改善点: {len(other_issues)}件[/dim]")

    def save_text_report(self, report: ContentValidationReport, output_path: Path) -> None:
        """テキスト形式でレポートを保存"""
        content = self._generate_text_report(report)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        # バッチ書き込みを使用
        Path(output_path).write_text(content, encoding="utf-8")

    def _generate_text_report(self, report: ContentValidationReport) -> str:
        """テキスト形式のレポート内容を生成"""
        lines = []

        # ヘッダー
        lines.append(f"第{report.episode_number}話 伏線・重要シーン検証レポート")
        if report.project_name:
            lines.append(f"プロジェクト: {report.project_name}")
        lines.append(f"生成日時: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)

        # 総合サマリー
        lines.append("\n■ 検証サマリー")
        lines.append(f"総合スコア: {report.overall_score:.1f}/100 ({report.get_grade()})")
        lines.append(f"伏線スコア: {report.foreshadowing_result.score:.1f}/100")
        lines.append(f"シーンスコア: {report.scene_result.score:.1f}/100")
        lines.append(f"総問題数: {report.total_issues}件")

        if report.critical_issues > 0:
            lines.append(f"重要問題: {report.critical_issues}件")

        # 伏線詳細
        lines.append("\n■ 伏線検証詳細")
        lines.append(f"検証対象: {report.foreshadowing_result.total_foreshadowing_checked}件")
        lines.append(f"仕込み済み: {report.foreshadowing_result.planted_count}件")
        lines.append(f"回収済み: {report.foreshadowing_result.resolved_count}件")
        lines.append(f"未仕込み: {len(report.foreshadowing_result.missing_plantings)}件")
        lines.append(f"未回収: {len(report.foreshadowing_result.missing_resolutions)}件")

        # 重要シーン詳細
        lines.append("\n■ 重要シーン検証詳細")
        lines.append(f"検証対象: {report.scene_result.total_scenes_checked}件")
        lines.append(f"実装済み: {report.scene_result.scenes_implemented}件")
        lines.append(f"未実装: {len(report.scene_result.missing_scenes)}件")
        lines.append(f"不完全: {len(report.scene_result.incomplete_scenes)}件")

        # 問題詳細
        if report.total_issues > 0:
            lines.append("\n■ 発見された問題")
            all_issues = report.foreshadowing_result.issues + report.scene_result.issues

            for i, issue in enumerate(all_issues, 1):
                title = self._get_issue_title(issue)
                severity = self._get_severity_text(issue)
                lines.append(f"\n{i}. [{severity}] {title}")
                lines.append(f"   問題: {issue.message}")
                if issue.suggestion:
                    lines.append(f"   提案: {issue.suggestion}")

        return "\n".join(lines)

    def _is_critical_issue(self, issue) -> bool:
        """問題が致命的かどうか判定"""
        if hasattr(issue.severity, "value"):
            return issue.severity.value == "critical"
        return str(issue.severity).lower() == "critical"

    def _is_high_issue(self, issue) -> bool:
        """問題が高重要度かどうか判定"""
        if hasattr(issue.severity, "value"):
            return issue.severity.value == "high"
        return str(issue.severity).lower() == "high"

    def _get_issue_title(self, issue) -> str:
        """問題のタイトルを取得"""
        if hasattr(issue, "scene_title"):
            return issue.scene_title
        if hasattr(issue, "foreshadowing_id"):
            return issue.foreshadowing_id
        return "不明"

    def _get_severity_text(self, issue) -> str:
        """重要度のテキスト表現を取得"""
        severity_value = issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity).lower()

        severity_map = {
            "critical": "緊急",
            "high": "重要",
            "medium": "中",
            "low": "軽微"
        }

        return severity_map.get(severity_value, severity_value)

    def _get_grade_color(self, grade: str) -> str:
        """グレードに対応する色を返す"""
        grade_colors = {
            "S": "bright_green",
            "A": "green",
            "B": "yellow",
            "C": "orange",
            "D": "red"
        }
        return grade_colors.get(grade, "white")
