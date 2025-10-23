#!/usr/bin/env python3
"""TDD+DDD準拠性チェックツール

DDDComplianceEngineを使用したpre-commit統合対応チェックツール
B20準拠: Domain層の依存関係厳密管理版
"""
import argparse
import asyncio

# B20準拠：パフォーマンス監視は簡易実装
import contextlib
import sys
import time
from pathlib import Path
from typing import Any

# B20準拠：共有コンソール使用（直接Console()インスタンス化禁止）
from noveler.presentation.cli.shared_utilities import console

# B20準拠：統一コンソールサービス使用
from noveler.infrastructure.services.change_impact_analyzer import ChangeImpactAnalyzer
from noveler.infrastructure.services.ddd_compliance_engine import (
    DDDComplianceEngine,
    ValidationLevel,
    ViolationSeverity,
)
from noveler.infrastructure.services.unified_report_manager import UnifiedReportManager


@contextlib.contextmanager
def monitor_performance(operation_name: str):
    """簡易パフォーマンス監視"""
    start_time = time.time()
    try:
        yield {"operation": operation_name}
    finally:
        duration = time.time() - start_time
        print(f"⏱️  {operation_name}: {duration:.2f}秒")


class DDDComplianceChecker:
    """DDD準拠性チェッカー"""

    def __init__(
        self,
        project_root: Path,
        validation_level: ValidationLevel = ValidationLevel.MODERATE,
        logger_service: Any | None = None,
        console_service: Any | None = None,
    ) -> None:
        self.project_root = project_root
        self.engine = DDDComplianceEngine(project_root, validation_level)
        # B20準拠：共有コンソール使用
        self.console = console if console_service is None else console_service

    async def check_compliance(self, quick_mode: bool = False, verbose: bool = False) -> int:
        """DDD準拠性チェック実行

        Args:
            quick_mode: クイックモード（重要な違反のみチェック）
            verbose: 詳細モード（全違反を表示）

        Returns:
            エラー数（0=成功、>0=違反検出）
        """
        with monitor_performance("ddd_compliance_check") as perf_monitor:
            try:
                change_analyzer = ChangeImpactAnalyzer(self.project_root)
                change_analysis = change_analyzer.analyze_changes()
                if change_analysis.recommended_validation_level != self.engine.validation_level:
                    self.console.print(
                        f"🔄 変更影響分析により検証レベル調整: {change_analysis.recommended_validation_level.value}"
                    )
                    self.engine = DDDComplianceEngine(self.project_root, change_analysis.recommended_validation_level)
                self.console.print("🔍 DDD準拠性分析実行中...")
                if change_analysis.changed_files:
                    self.console.print(
                        f"📊 変更影響分析: {len(change_analysis.changed_files)}ファイル変更、影響レベル={change_analysis.overall_impact_level.value}"
                    )
                report = await self.engine.analyze_project_compliance()
                self.console.print("\n📊 分析結果:")
                self.console.print(f"  - 分析ファイル数: {report.total_files_analyzed}")
                self.console.print(f"  - 全体準拠率: {report.compliance_percentage:.1f}%")
                self.console.print(f"  - 検出違反数: {len(report.violations)}")
                severity_counts = {}
                for violation in report.violations:
                    severity = violation.severity.value
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                if severity_counts:
                    self.console.print("\n🚨 違反内訳:")
                    for severity, count in severity_counts.items():
                        emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
                        self.console.print(f"  - {emoji} {severity}: {count}件")
                if quick_mode:
                    critical_violations = [
                        v
                        for v in report.violations
                        if v.severity in [ViolationSeverity.CRITICAL, ViolationSeverity.HIGH]
                    ]
                    if critical_violations:
                        self.console.print(f"\n🔴 重要な違反 ({len(critical_violations)}件):")
                        display_count = len(critical_violations) if verbose else min(20, len(critical_violations))
                        for violation in critical_violations[:display_count]:
                            self.console.print(f"  - {violation.file_path}:{violation.line_number}")
                            self.console.print(f"    {violation.violation_type}: {violation.description}")
                        if len(critical_violations) > display_count:
                            remaining = len(critical_violations) - display_count
                            self.console.print(f"    ... 他{remaining}件（--verboseで全件表示）")
                    return len(critical_violations)
                if report.violations:
                    self.console.print("\n📝 検出された違反:")
                    sorted_violations = sorted(
                        report.violations, key=lambda v: ["CRITICAL", "HIGH", "MEDIUM", "LOW"].index(v.severity.value)
                    )
                    if verbose:
                        display_count = len(sorted_violations)
                    else:
                        critical_high = [v for v in sorted_violations if v.severity.value in ["CRITICAL", "HIGH"]]
                        others = [v for v in sorted_violations if v.severity.value not in ["CRITICAL", "HIGH"]]
                        critical_display = len(critical_high)
                        others_display = min(15, len(others))
                        display_count = critical_display + others_display
                    displayed = 0
                    for violation in sorted_violations:
                        if displayed >= display_count:
                            break
                        emoji = {
                            ViolationSeverity.CRITICAL: "🔴",
                            ViolationSeverity.HIGH: "🟠",
                            ViolationSeverity.MEDIUM: "🟡",
                            ViolationSeverity.LOW: "🟢",
                        }.get(violation.severity, "⚪")
                        self.console.print(f"  {emoji} {violation.file_path}:{violation.line_number}")
                        self.console.print(f"     {violation.violation_type}: {violation.description}")
                        displayed += 1
                    if len(sorted_violations) > displayed:
                        remaining = len(sorted_violations) - displayed
                        self.console.print(f"     ... 他{remaining}件（--verboseで全件表示）")
                return len(report.violations)
            except Exception as e:
                self.console.print(f"❌ DDD準拠性チェックエラー: {e}")
                return 1
            finally:
                try:
                    end_time = time.time()
                    analysis_duration = getattr(self, "_start_time", end_time) - end_time
                    report_manager = UnifiedReportManager(self.project_root)
                    metrics = report_manager.create_unified_metrics(
                        compliance_report=report if "report" in locals() else None,
                        change_analysis=change_analysis if "change_analysis" in locals() else None,
                        execution_context="pre-commit" if quick_mode else "manual",
                        analysis_duration=abs(analysis_duration),
                        cache_hit_rate=0.0,
                    )
                    report_manager.save_metrics(metrics)
                    summary = report_manager.generate_summary_report(metrics)
                    report_manager.export_summary_report(summary)
                    self.console.print(f"📊 品質メトリクス保存完了: {metrics.execution_id[:8]}")
                except Exception as report_error:
                    self.console.print(f"⚠️ レポート生成エラー: {report_error}")

    async def check_compliance_with_plot_adherence(
        self,
        quick_mode: bool = False,
        verbose: bool = False,
        include_plot_adherence: bool = False,
        episode_number: int | None = None,
        manuscript_file: str | None = None,
    ) -> int:
        """プロット準拠機能統合版DDD準拠性チェック実行

        SPEC-PLOT-ADHERENCE-001統合実装

        Args:
            quick_mode: クイックモード（重要な違反のみチェック）
            verbose: 詳細モード（全違反を表示）
            include_plot_adherence: プロット準拠チェックを含める
            episode_number: エピソード番号（プロット準拠チェック用）
            manuscript_file: 原稿ファイルパス（プロット準拠チェック用）

        Returns:
            エラー数（0=成功、>0=違反検出）
        """
        ddd_violation_count = await self.check_compliance(quick_mode, verbose)
        plot_adherence_violation_count = 0
        if include_plot_adherence and episode_number is not None:
            try:
                plot_adherence_violation_count = await self._execute_plot_adherence_check(
                    episode_number, manuscript_file, verbose
                )
            except Exception as e:
                self.console.print(f"⚠️ プロット準拠チェックエラー（処理続行）: {e}")
                plot_adherence_violation_count = 0
        total_violations = ddd_violation_count + plot_adherence_violation_count
        self.console.print("\n" + "=" * 50)
        self.console.print("📊 統合品質チェック結果サマリー")
        self.console.print("=" * 50)
        self.console.print(f"🏗️ DDD準拠性違反: {ddd_violation_count}件")
        if include_plot_adherence:
            self.console.print(f"📖 プロット準拠違反: {plot_adherence_violation_count}件")
        self.console.print(f"📊 総合違反件数: {total_violations}件")
        if total_violations == 0:
            self.console.print("🎉 全ての品質チェックに合格しました！")
        else:
            self.console.print("⚠️ 品質改善が必要です。上記の違反を修正してください。")
        return total_violations

    async def _execute_plot_adherence_check(
        self, episode_number: int, manuscript_file: str | None = None, verbose: bool = False
    ) -> int:
        """プロット準拠チェック実行

        Args:
            episode_number: エピソード番号
            manuscript_file: 原稿ファイルパス（Noneの場合は自動検索）
            verbose: 詳細モード

        Returns:
            int: プロット準拠違反件数
        """
        self.console.print(f"\n📖 プロット準拠チェック実行中 - 第{episode_number:03d}話")
        try:
            manuscript_content = await self._get_manuscript_content(episode_number, manuscript_file)
            if not manuscript_content:
                self.console.print("⚠️ 原稿ファイルが見つかりません - プロット準拠チェックをスキップ")
                return 0
            from noveler.application.use_cases.validate_plot_adherence_use_case import (
                PlotAdherenceRequest,
                ValidatePlotAdherenceUseCase,
            )

            plot_adherence_use_case = ValidatePlotAdherenceUseCase()
            request = PlotAdherenceRequest(
                episode_number=episode_number,
                manuscript_content=manuscript_content,
                project_root=self.project_root,
                include_suggestions=True,
                minimum_score_threshold=95.0,
            )
            response = await plot_adherence_use_case.execute(request)
            if not response.success:
                self.console.print(f"❌ プロット準拠検証エラー: {response.error_message}")
                return 1
            self.console.print(f"📊 プロット準拠率: {response.adherence_score:.1f}%")
            self.console.print(f"📋 検証要素数: {response.plot_elements_checked}個")
            if response.is_acceptable_quality():
                self.console.print("✅ プロット準拠チェック合格")
                return 0
            self.console.print(f"❌ プロット準拠率が基準未達: {response.get_quality_summary()}")
            if response.missing_elements:
                self.console.print("\n⚠️ 不足要素:")
                for element in response.missing_elements[:5]:
                    self.console.print(f"  - {element}")
                if len(response.missing_elements) > 5:
                    remaining = len(response.missing_elements) - 5
                    self.console.print(f"  ... 他{remaining}件")
            if response.suggestions and verbose:
                self.console.print("\n💡 改善提案:")
                for suggestion in response.suggestions[:3]:
                    self.console.print(f"  - {suggestion}")
            return 1
        except Exception as e:
            self.console.print(f"❌ プロット準拠チェック実行エラー: {e}")
            return 1

    async def _get_manuscript_content(self, episode_number: int, manuscript_file: str | None = None) -> str:
        """原稿内容を取得

        Args:
            episode_number: エピソード番号
            manuscript_file: 原稿ファイルパス（Noneの場合は自動検索）

        Returns:
            str: 原稿内容（見つからない場合は空文字）
        """
        try:
            from pathlib import Path

            if manuscript_file:
                file_path = Path(manuscript_file)
                if not file_path.is_absolute():
                    file_path = self.project_root / file_path
                if file_path.exists():
                    return file_path.read_text(encoding="utf-8")
            search_patterns = [
                f"manuscripts/episode_{episode_number:03d}.md",
                f"manuscripts/第{episode_number:03d}話.md",
                f"episodes/episode_{episode_number:03d}.txt",
                f"drafts/episode_{episode_number:03d}.md",
                f"output/第{episode_number:03d}話.md",
            ]
            for pattern in search_patterns:
                file_path = self.project_root / pattern
                if file_path.exists():
                    return file_path.read_text(encoding="utf-8")
            return ""
        except Exception as e:
            self.console.print(f"⚠️ 原稿ファイル読み取りエラー: {e}")
            return ""


async def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="TDD+DDD準拠性チェック")
    parser.add_argument("--quick", action="store_true", help="クイックモード（重要な違反のみ）")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細モード（全違反を表示）")
    parser.add_argument("--level", choices=["basic", "moderate", "strict"], default="moderate", help="検証レベル")
    parser.add_argument("--project-root", type=Path, default=Path(), help="プロジェクトルート")
    parser.add_argument("--include-plot-adherence", action="store_true", help="プロット準拠チェックを含める")
    parser.add_argument("--episode-number", type=int, help="エピソード番号（プロット準拠チェック用）")
    parser.add_argument("--manuscript-file", type=str, help="原稿ファイルパス（プロット準拠チェック用）")
    args = parser.parse_args()
    level_mapping = {
        "basic": ValidationLevel.BASIC,
        "moderate": ValidationLevel.MODERATE,
        "strict": ValidationLevel.STRICT,
    }
    validation_level = level_mapping[args.level]
    checker = DDDComplianceChecker(args.project_root, validation_level)
    if args.include_plot_adherence:
        if args.episode_number is None:
            # B20準拠：共有コンソール使用
            console.print("❌ プロット準拠チェックにはエピソード番号（--episode-number）が必要です")
            sys.exit(1)
        error_count = await checker.check_compliance_with_plot_adherence(
            quick_mode=args.quick,
            verbose=args.verbose,
            include_plot_adherence=True,
            episode_number=args.episode_number,
            manuscript_file=args.manuscript_file,
        )
    else:
        error_count = await checker.check_compliance(args.quick, args.verbose)
    # B20準拠：共有コンソール使用（Console()は作成しない）
    if error_count == 0:
        console.print("✅ 品質チェック: 成功")
        sys.exit(0)
    else:
        console.print(f"❌ 品質チェック: {error_count}件の違反検出")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
