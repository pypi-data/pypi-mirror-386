#!/usr/bin/env python3
"""DDD品質ゲート

仕様書: SPEC-DDD-AUTO-COMPLIANCE-001
CI/CDパイプライン統合用DDD品質ゲート実装
"""

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.i_unified_file_storage import FileContentType
from noveler.domain.services.architecture_dependency_analyzer import ArchitectureDependencyAnalyzer
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.services.ddd_compliance_engine import (
    DDDComplianceEngine,
    ValidationLevel,
    ViolationSeverity,
)
from noveler.infrastructure.storage import UnifiedFileStorageService
from noveler.presentation.shared.shared_utilities import console


class QualityGateMode(Enum):
    """品質ゲートモード"""

    STRICT = "strict"  # 厳格モード（CI/CDでの使用）
    MODERATE = "moderate"  # 中程度モード（開発中の使用）
    REPORT_ONLY = "report"  # レポートのみ（情報収集）
    CI = "ci"  # CI環境専用


class ExitCode(Enum):
    """終了コード"""

    SUCCESS = 0
    WARNINGS = 1
    VIOLATIONS = 2
    ERROR = 3


@dataclass
class QualityGateResult:
    """品質ゲート結果"""

    mode: QualityGateMode
    passed: bool
    exit_code: ExitCode
    compliance_percentage: float
    violations_count: int
    critical_violations: int
    warnings_count: int
    report_path: str | None
    summary: dict[str, Any]


class DDDQualityGate:
    """DDD品質ゲート

    責務:
        - CI/CDパイプライン統合
        - 品質基準による合否判定
        - 詳細レポート生成
        - 段階的品質評価
        - Git Hooks統合

    設計原則:
        - 高速実行（CI環境での制約）
        - 明確な合否基準
        - 詳細なフィードバック
    """

    def __init__(self, project_root: Path, mode: QualityGateMode = QualityGateMode.MODERATE) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            mode: 品質ゲートモード
        """
        self.project_root = project_root
        self.mode = mode
        self.logger = get_logger(__name__)

        # 品質基準設定
        self._initialize_quality_standards()

        # コンポーネント初期化
        self.compliance_engine = DDDComplianceEngine(project_root, self._get_validation_level())

        self.dependency_analyzer = ArchitectureDependencyAnalyzer(project_root)

        # CI環境検出
        self.is_ci_environment = self._detect_ci_environment()

    def _initialize_quality_standards(self) -> None:
        """品質基準の初期化"""
        self.quality_standards = {
            QualityGateMode.STRICT: {
                "min_compliance_percentage": 95.0,
                "max_critical_violations": 0,
                "max_high_violations": 2,
                "max_total_violations": 10,
                "require_architecture_health": 0.9,
            },
            QualityGateMode.MODERATE: {
                "min_compliance_percentage": 85.0,
                "max_critical_violations": 2,
                "max_high_violations": 5,
                "max_total_violations": 20,
                "require_architecture_health": 0.7,
            },
            QualityGateMode.REPORT_ONLY: {
                "min_compliance_percentage": 0.0,
                "max_critical_violations": float("inf"),
                "max_high_violations": float("inf"),
                "max_total_violations": float("inf"),
                "require_architecture_health": 0.0,
            },
            QualityGateMode.CI: {
                "min_compliance_percentage": 90.0,
                "max_critical_violations": 1,
                "max_high_violations": 3,
                "max_total_violations": 15,
                "require_architecture_health": 0.8,
            },
        }

    def _get_validation_level(self) -> ValidationLevel:
        """検証レベル取得"""
        mapping = {
            QualityGateMode.STRICT: ValidationLevel.STRICT,
            QualityGateMode.CI: ValidationLevel.STRICT,
            QualityGateMode.MODERATE: ValidationLevel.MODERATE,
            QualityGateMode.REPORT_ONLY: ValidationLevel.BASIC,
        }
        return mapping.get(self.mode, ValidationLevel.MODERATE)

    def _detect_ci_environment(self) -> bool:
        """CI環境検出"""
        ci_indicators = [
            "CI",
            "CONTINUOUS_INTEGRATION",
            "GITHUB_ACTIONS",
            "GITLAB_CI",
            "JENKINS_URL",
            "TRAVIS",
            "CIRCLECI",
            "AZURE_DEVOPS",
        ]

        return any(os.getenv(indicator) for indicator in ci_indicators)

    async def run_quality_gate(self) -> QualityGateResult:
        """品質ゲート実行

        Returns:
            QualityGateResult: 品質ゲート結果
        """
        self.logger.info("DDD品質ゲート実行開始 - モード: %s", self.mode.value)

        try:
            # 1. DDD準拠性分析
            compliance_report = await self.compliance_engine.analyze_project_compliance()

            # 2. アーキテクチャ依存関係分析
            architecture_result = await self.dependency_analyzer.analyze_project_architecture()

            # 3. 品質評価
            quality_result = self._evaluate_quality(compliance_report, architecture_result)

            # 4. レポート生成
            report_path = await self._generate_quality_report(compliance_report, architecture_result, quality_result)

            # 5. 結果サマリー生成
            summary = self._generate_result_summary(compliance_report, architecture_result, quality_result)

            result = QualityGateResult(
                mode=self.mode,
                passed=quality_result["passed"],
                exit_code=quality_result["exit_code"],
                compliance_percentage=compliance_report.compliance_percentage,
                violations_count=len(compliance_report.violations),
                critical_violations=quality_result["critical_violations"],
                warnings_count=quality_result["warnings_count"],
                report_path=str(report_path) if report_path else None,
                summary=summary,
            )

            # 6. 結果出力
            await self._output_results(result)

            return result

        except Exception as e:
            self.logger.exception("品質ゲート実行エラー")
            return QualityGateResult(
                mode=self.mode,
                passed=False,
                exit_code=ExitCode.ERROR,
                compliance_percentage=0.0,
                violations_count=0,
                critical_violations=0,
                warnings_count=0,
                report_path=None,
                summary={"error": str(e)},
            )

    def _evaluate_quality(self, compliance_report: object, architecture_result: object) -> dict[str, Any]:
        """品質評価

        Args:
            compliance_report: 準拠性レポート
            architecture_result: アーキテクチャ分析結果

        Returns:
            品質評価結果
        """
        standards = self.quality_standards[self.mode]

        # 違反数集計
        critical_violations = sum(1 for v in compliance_report.violations if v.severity == ViolationSeverity.CRITICAL)

        high_violations = sum(1 for v in compliance_report.violations if v.severity == ViolationSeverity.HIGH)

        total_violations = len(compliance_report.violations)

        # 品質基準チェック
        checks = {
            "compliance_percentage": compliance_report.compliance_percentage >= standards["min_compliance_percentage"],
            "critical_violations": critical_violations <= standards["max_critical_violations"],
            "high_violations": high_violations <= standards["max_high_violations"],
            "total_violations": total_violations <= standards["max_total_violations"],
            "architecture_health": architecture_result.architecture_health_score
            >= standards["require_architecture_health"],
        }

        # 全体合否判定
        passed = all(checks.values()) if self.mode != QualityGateMode.REPORT_ONLY else True

        # 終了コード決定
        if not passed:
            exit_code = ExitCode.VIOLATIONS if critical_violations > 0 else ExitCode.WARNINGS
        else:
            exit_code = ExitCode.SUCCESS

        # 警告数計算
        warnings_count = sum(
            1 for v in compliance_report.violations if v.severity in [ViolationSeverity.MEDIUM, ViolationSeverity.LOW]
        )

        return {
            "passed": passed,
            "exit_code": exit_code,
            "checks": checks,
            "critical_violations": critical_violations,
            "high_violations": high_violations,
            "total_violations": total_violations,
            "warnings_count": warnings_count,
            "standards": standards,
        }

    async def _generate_quality_report(self, compliance_report: object, architecture_result: object, quality_result: object) -> Path | None:
        """品質レポート生成

        Args:
            compliance_report: 準拠性レポート
            architecture_result: アーキテクチャ分析結果
            quality_result: 品質評価結果

        Returns:
            レポートファイルパス
        """
        # レポート出力ディレクトリ
        reports_dir = self.project_root / "reports" / "ddd_quality"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # CI環境では詳細レポートを生成
        if self.is_ci_environment or self.mode == QualityGateMode.CI:
            report_path = reports_dir / f"ddd_quality_gate_{self.mode.value}.json"

            report_data: dict[str, Any] = {
                "timestamp": compliance_report.timestamp.isoformat(),
                "mode": self.mode.value,
                "project_root": str(self.project_root),
                "quality_gate": {
                    "passed": quality_result["passed"],
                    "exit_code": quality_result["exit_code"].value,
                    "standards": quality_result["standards"],
                    "checks": quality_result["checks"],
                },
                "compliance": {
                    "percentage": compliance_report.compliance_percentage,
                    "total_files": compliance_report.total_files_analyzed,
                    "violations": [
                        {
                            "file_path": v.file_path,
                            "line_number": v.line_number,
                            "type": v.violation_type,
                            "severity": v.severity.value,
                            "description": v.description,
                            "recommendation": v.recommendation,
                        }
                        for v in compliance_report.violations
                    ],
                    "layer_compliance": compliance_report.layer_compliance,
                },
                "architecture": {
                    "health_score": architecture_result.architecture_health_score,
                    "violations": [
                        {
                            "source_layer": v.source_layer,
                            "target_layer": v.target_layer,
                            "type": v.violation_type.value,
                            "severity": v.severity,
                            "count": v.count,
                            "recommendation": v.recommendation,
                        }
                        for v in architecture_result.layer_violations
                    ],
                    "circular_dependencies": architecture_result.circular_dependencies,
                    "layer_metrics": architecture_result.layer_metrics,
                },
            }

            # UnifiedFileStorageServiceを使用してレポートを保存
            storage_service = UnifiedFileStorageService()
            storage_service.save(
                file_path=report_path,
                content=report_data,
                content_type=FileContentType.API_RESPONSE,
                metadata={
                    "report_type": "ddd_quality_gate",
                    "mode": self.mode.value,
                    "passed": quality_result["passed"],
                    "compliance_percentage": compliance_report.compliance_percentage,
                },
            )

            return report_path

        return None

    def _generate_result_summary(self, compliance_report: object, architecture_result: object, quality_result: object) -> dict[str, Any]:
        """結果サマリー生成

        Args:
            compliance_report: 準拠性レポート
            architecture_result: アーキテクチャ分析結果
            quality_result: 品質評価結果

        Returns:
            結果サマリー
        """
        return {
            "quality_gate_passed": quality_result["passed"],
            "compliance_percentage": compliance_report.compliance_percentage,
            "architecture_health_score": architecture_result.architecture_health_score,
            "total_violations": quality_result["total_violations"],
            "critical_violations": quality_result["critical_violations"],
            "high_violations": quality_result["high_violations"],
            "warnings": quality_result["warnings_count"],
            "circular_dependencies": len(architecture_result.circular_dependencies),
            "standards_met": quality_result["checks"],
            "recommendations": compliance_report.summary.get("recommendations", []),
        }

    async def _output_results(self, result: QualityGateResult) -> None:
        """結果出力

        Args:
            result: 品質ゲート結果
        """
        # コンソール出力（CI環境では簡潔に）
        if self.is_ci_environment:
            await self._output_ci_results(result)
        else:
            await self._output_interactive_results(result)

        # ログ出力
        if result.passed:
            self.logger.info(f"DDD品質ゲート合格 - 準拠率: {result.compliance_percentage:.1f}%")
        else:
            self.logger.warning(
                f"DDD品質ゲート不合格 - 準拠率: {result.compliance_percentage:.1f}%, "
                f"クリティカル違反: {result.critical_violations}件"
            )

    async def _output_ci_results(self, result: QualityGateResult) -> None:
        """CI環境用結果出力"""
        status = "✅ PASSED" if result.passed else "❌ FAILED"

        self.console_service.print(f"DDD Quality Gate: {status}")
        self.console_service.print(f"Compliance: {result.compliance_percentage:.1f}%")
        self.console_service.print(f"Violations: {result.violations_count} (Critical: {result.critical_violations})")
        self.console_service.print(f"Architecture Health: {result.summary.get('architecture_health_score', 0):.2f}")

        if result.report_path:
            self.console_service.print(f"Report: {result.report_path}")

        if not result.passed:
            self.console_service.print("\nFailing Checks:")
            for check, passed in result.summary.get("standards_met", {}).items():
                if not passed:
                    self.console_service.print(f"  ❌ {check}")

    async def _output_interactive_results(self, result: QualityGateResult) -> None:
        """インタラクティブ環境用結果出力"""
        # Rich ConsoleでカラフルなLive表示
        # DDD準拠: Infrastructure→Presentation依存を除去
        # from noveler.presentation.shared.shared_utilities import console

        status_color = "green" if result.passed else "red"
        status_text = "合格" if result.passed else "不合格"

        console.print(f"\n[{status_color}]🎯 DDD品質ゲート結果: {status_text}[/{status_color}]")
        console.print(f"📊 DDD準拠率: {result.compliance_percentage:.1f}%")
        console.print(
            f"🏗️  アーキテクチャ健全性: {result.summary.get('architecture_health_score', 0):.2f}"
        )

        # 違反統計
        if result.violations_count > 0:
            console.print("\n📋 違反統計:")
            console.print(f"  🔴 クリティカル: {result.critical_violations}件")
            console.print(f"  🟠 高重要度: {result.summary.get('high_violations', 0)}件")
            console.print(f"  🟡 警告: {result.warnings_count}件")
            console.print(f"  📊 合計: {result.violations_count}件")

        # 循環依存
        circular_deps = result.summary.get("circular_dependencies", 0)
        if circular_deps > 0:
            console.print(f"🔄 循環依存: {circular_deps}件")

        # 品質基準チェック結果
        console.print("\n🎚️  品質基準:")
        for check, passed in result.summary.get("standards_met", {}).items():
            status_icon = "✅" if passed else "❌"
            console.print(f"  {status_icon} {check}")

        # 推奨事項
        recommendations = result.summary.get("recommendations", [])
        if recommendations:
            console.print("\n💡 推奨事項:")
            for i, rec in enumerate(recommendations[:5], 1):
                console.print(f"  {i}. {rec}")

        if result.report_path:
            console.print(f"\n📄 詳細レポート: {result.report_path}")


async def main() -> None:
    """メイン関数（CLI実行用）"""
    parser = argparse.ArgumentParser(description="DDD品質ゲート")

    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in QualityGateMode],
        default=QualityGateMode.MODERATE.value,
        help="品質ゲートモード",
    )

    parser.add_argument(
        "--check",
        choices=["all", "compliance", "dependencies", "violations"],
        default="all",
        help="実行するチェック種類",
    )

    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="プロジェクトルートパス")

    parser.add_argument("--report", action="store_true", help="詳細レポート出力")

    parser.add_argument("--output", type=Path, help="出力ファイルパス")

    args = parser.parse_args()

    # モード設定
    mode = QualityGateMode(args.mode)

    # 品質ゲート実行
    quality_gate = DDDQualityGate(args.project_root, mode)
    result = await quality_gate.run_quality_gate()

    # 追加レポート出力
    if args.report and args.output:
        report_data: dict[str, Any] = {
            "timestamp": result.summary.get("timestamp", ""),
            "mode": result.mode.value,
            "passed": result.passed,
            "summary": result.summary,
        }

        # UnifiedFileStorageServiceを使用して追加レポートを保存
        storage_service = UnifiedFileStorageService()
        storage_service.save(
            file_path=args.output,
            content=report_data,
            content_type=FileContentType.API_RESPONSE,
            metadata={"report_type": "ddd_quality_gate_additional", "mode": result.mode.value, "passed": result.passed},
        )

    # 終了コード設定
    sys.exit(result.exit_code.value)


if __name__ == "__main__":
    asyncio.run(main())
