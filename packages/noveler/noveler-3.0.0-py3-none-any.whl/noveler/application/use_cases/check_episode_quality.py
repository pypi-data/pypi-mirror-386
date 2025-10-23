"""Episode quality check use case."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from noveler.domain.quality.entities import QualityReport

if TYPE_CHECKING:
    from noveler.domain.interfaces.quality_checker import QualityChecker
    from noveler.domain.quality.repositories import QualityReportRepository
    from noveler.domain.quality.services import QualityReportGenerator


@dataclass(frozen=True)
class CheckEpisodeQualityCommand:
    """Command object describing which episode to evaluate."""

    project_id: str
    episode_id: str
    content: str
    auto_fix: bool = False


@dataclass(frozen=True)
class CheckEpisodeQualityResult:
    """Result returned after running a quality check."""

    success: bool
    report: QualityReport | None = None
    fixed_content: str | None = None
    error_message: str | None = None


class CheckEpisodeQualityUseCase:
    """Coordinate episode quality checks using injected services."""

    def __init__(
        self,
        quality_checker: "QualityChecker",
        report_generator: "QualityReportGenerator",
        report_repository: "QualityReportRepository",
    ) -> None:
        """Initialise the use case with the required services.

        Args:
            quality_checker: Text quality checker implementation.
            report_generator: Service that builds quality reports.
            report_repository: Repository used to persist quality reports.
        """
        self.quality_checker = quality_checker
        self.report_generator = report_generator
        self.report_repository = report_repository

    def execute(self, command: CheckEpisodeQualityCommand) -> CheckEpisodeQualityResult:
        """Run the quality check workflow for the requested episode."""
        try:
            # 基本文体チェック
            style_violations = self.quality_checker.check_basic_style(
                command.content,
                command.project_id,
            )

            # 構成チェック
            composition_violations = self.quality_checker.check_composition(
                command.content,
            )

            # 全ての違反をマージ
            all_violations = style_violations + composition_violations

            # レポート生成
            report = self.report_generator.generate_report(
                command.episode_id,
                all_violations,
            )

            # 自動修正が必要な場合
            fixed_content = None
            if command.auto_fix:
                fixed_content = self._apply_auto_fixes(
                    command.content,
                    report.get_auto_fixable_violations(),
                )

                report.auto_fixed_count = len(report.get_auto_fixable_violations())

            # レポートを保存(リポジトリが設定されている場合)
            if self.report_repository:
                self.report_repository.save(report)

            return CheckEpisodeQualityResult(
                success=True,
                report=report,
                fixed_content=fixed_content,
            )

        except Exception as e:
            return CheckEpisodeQualityResult(
                success=False,
                error_message=str(e),
            )

    def _apply_auto_fixes(self, content: str, violations: list) -> str:
        """Apply simple auto-fix suggestions to the manuscript."""
        # 簡易的な実装
        # 実際にはもっと複雑な修正ロジックが必要
        fixed_content = content

        for violation in violations:
            if violation.suggestion:
                # 行番号がある場合は行単位で修正
                if violation.line_number:
                    lines = fixed_content.split("\n")
                    line_idx = violation.line_number.value - 1
                    if 0 <= line_idx < len(lines):
                        # suggestionが完全な行の場合
                        if violation.rule_name == "missing_indentation":
                            lines[line_idx] = violation.suggestion
                        # それ以外は置換
                        else:
                            lines[line_idx] = violation.suggestion
                    fixed_content = "\n".join(lines)
                # 行番号がない場合は全体置換
                else:
                    fixed_content = violation.suggestion

        return fixed_content
