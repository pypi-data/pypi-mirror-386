# File: src/noveler/presentation/ui/text_rhythm_renderer.py
# Purpose: Provide Rich-based rendering utilities for text rhythm analysis reports in the presentation layer.
# Context: Consumed by CLI/UI code to display domain TextRhythmReport data without leaking Rich dependencies into Domain.

"""Rich renderer for text rhythm analysis reports."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table

from noveler.presentation.shared.shared_utilities import get_console
from noveler.domain.value_objects.text_rhythm_analysis import (
    RhythmSeverity,
    TextRhythmReport,
)


class TextRhythmRichRenderer:
    """Render :class:`TextRhythmReport` instances using Rich components."""

    def __init__(self, console: Any | None = None) -> None:
        self.console = console or get_console()

    def render(self, report: TextRhythmReport, *, show_sentences: bool = False) -> None:
        """Render the supplied report using Rich panels and tables.

        Args:
            report: Domain report produced by the text rhythm analysis service.
            show_sentences: Whether to print detailed sentence information.
        """
        self.console.print(self._build_overall_panel(report))
        self.console.print(self._build_statistics_table(report))
        self.console.print(self._build_distribution_table(report))

        if report.issues:
            self.console.print(self._build_issues_table(report))
        else:
            self.console.print(Panel.fit("✅ 問題は見つかりませんでした", border_style="green", title="Issues"))

        if show_sentences:
            self.console.print(self._build_sentence_table(report))

    def _build_overall_panel(self, report: TextRhythmReport) -> Panel:
        score = report.overall_score
        grade = report.readability_grade.upper()
        style = self._score_style(score)
        body = f"スコア: {score:.1f}/100\nグレード: {grade}"
        return Panel.fit(body, title="Overall", border_style=style)

    def _build_statistics_table(self, report: TextRhythmReport) -> Table:
        stats = report.statistics
        table = Table(title="Statistics", expand=False)
        table.add_column("指標", style="cyan", no_wrap=True)
        table.add_column("値", justify="right")
        table.add_row("総文数", str(stats.total_sentences))
        table.add_row("平均文字数", f"{stats.average_length:.1f} ({self._avg_length_eval(stats.average_length)})")
        table.add_row("中央値", f"{stats.median_length:.1f}")
        table.add_row("標準偏差", f"{stats.std_deviation:.1f} ({self._std_dev_eval(stats.std_deviation)})")
        table.add_row("最小/最大", f"{stats.min_length} / {stats.max_length}")
        table.add_row("リズムスコア", f"{stats.rhythm_score:.1f} ({self._rhythm_eval(stats.rhythm_score)})")
        return table

    def _build_distribution_table(self, report: TextRhythmReport) -> Table:
        percentages = report.statistics.get_distribution_percentages()
        table = Table(title="文字数分布", expand=False)
        table.add_column("カテゴリ", style="magenta", no_wrap=True)
        table.add_column("割合", justify="right")
        table.add_row("極短文 (≤15)", f"{percentages['very_short']:.1f}%")
        table.add_row("短文 (16-25)", f"{percentages['short']:.1f}%")
        table.add_row("中文 (26-40)", f"{percentages['medium']:.1f}%")
        table.add_row("長文 (41-60)", f"{percentages['long']:.1f}%")
        table.add_row("極長文 (≥61)", f"{percentages['very_long']:.1f}%")
        return table

    def _build_issues_table(self, report: TextRhythmReport) -> Table:
        table = Table(title=f"Issues ({len(report.issues)})", expand=False)
        table.add_column("#", justify="right", style="cyan")
        table.add_column("深刻度", style="bold")
        table.add_column("概要", overflow="fold")
        table.add_column("改善提案", overflow="fold")
        table.add_column("対象文数", justify="right")

        for idx, issue in enumerate(report.get_improvement_priority(), 1):
            severity_style = self._severity_style(issue.severity)
            table.add_row(
                str(idx),
                f"[{severity_style}]{issue.severity.value.upper()}[/]",
                issue.description,
                issue.suggestion,
                str(issue.sentence_count),
            )
        return table

    def _build_sentence_table(self, report: TextRhythmReport, limit: int = 10) -> Table:
        table = Table(title="問題文の詳細", expand=False)
        table.add_column("文番号", style="cyan", justify="right")
        table.add_column("文字数", justify="right")
        table.add_column("内容", overflow="fold")

        problematic_indexes = self._problematic_sentence_indexes(report)
        sentences = [s for s in report.sentences if s.index in problematic_indexes]
        for sentence in sentences[:limit]:
            table.add_row(str(sentence.index + 1), str(sentence.character_count), sentence.content.strip())
        if len(sentences) > limit:
            table.add_row("…", "…", "(追加の文は省略されています)")
        return table

    def _problematic_sentence_indexes(self, report: TextRhythmReport) -> set[int]:
        indexes: set[int] = set()
        for issue in report.issues:
            indexes.update(s.index for s in issue.affected_sentences)
        return indexes

    def _severity_style(self, severity: RhythmSeverity) -> str:
        return {
            RhythmSeverity.CRITICAL: "red",
            RhythmSeverity.HIGH: "yellow",
            RhythmSeverity.MEDIUM: "bright_blue",
            RhythmSeverity.LOW: "green",
        }.get(severity, "white")

    def _score_style(self, score: float) -> str:
        if score >= 80:
            return "green"
        if score >= 60:
            return "yellow"
        return "red"

    def _avg_length_eval(self, avg_length: float) -> str:
        if 25 <= avg_length <= 45:
            return "理想的"
        if 20 <= avg_length < 25 or 45 < avg_length <= 50:
            return "やや長め/短め"
        return "要調整"

    def _std_dev_eval(self, std_dev: float) -> str:
        if 8 <= std_dev <= 20:
            return "良好"
        if std_dev < 8:
            return "単調"
        return "ばらつき大"

    def _rhythm_eval(self, score: float) -> str:
        if score >= 80:
            return "優秀"
        if score >= 60:
            return "良好"
        return "要改善"


def render_text_rhythm_report(
    report: TextRhythmReport,
    *,
    console: Any | None = None,
    show_sentences: bool = False,
) -> None:
    """Convenience function to render a report without instantiating the class."""

    TextRhythmRichRenderer(console=console).render(report, show_sentences=show_sentences)
