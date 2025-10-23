#!/usr/bin/env python3
"""依存関係分析ユースケース(リファクタリング版)

DDD準拠 + Command Pattern適用による複雑度削減
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.services.dependency_analysis import (
    CircularDependencyAnalysisCommand,
    DependencyAnalysisService,
    ExternalDependencyAnalysisCommand,
    LayerViolationAnalysisCommand,
)


@dataclass
class DependencyAnalysisRequest:
    """依存関係分析リクエスト"""

    project_root: Path
    output_format: str = "json"  # "json", "text", "mermaid", "graphviz"
    output_file: str | None = None
    include_layer_analysis: bool = True
    include_circular_analysis: bool = True
    include_external_analysis: bool = True
    quiet: bool = False


@dataclass
class DependencyAnalysisResponse:
    """依存関係分析レスポンス"""

    success: bool
    total_violations: int = 0
    results: dict[str, Any] = None
    metrics: dict[str, Any] = None
    report_content: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.results is None:
            self.results = {}
        if self.metrics is None:
            self.metrics = {}

    @classmethod
    def success_response(
        cls, total_violations: int, results: dict, metrics: dict, report_content: str | None = None
    ) -> "DependencyAnalysisResponse":
        """成功レスポンス作成"""
        return cls(
            success=True,
            total_violations=total_violations,
            results=results,
            metrics=metrics,
            report_content=report_content,
        )

    @classmethod
    def error_response(cls, error_message: str) -> "DependencyAnalysisResponse":
        """エラーレスポンス作成"""
        return cls(success=False, error_message=error_message)


class DependencyAnalysisUseCase(AbstractUseCase[DependencyAnalysisRequest, DependencyAnalysisResponse]):
    """依存関係分析ユースケース(リファクタリング版)

    Command Patternを使用して複雑度を削減
    """

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        console_service: Optional["IConsoleService"] = None,
        path_service: Optional["IPathService"] = None,
        **kwargs) -> None:
        """初期化

        DDD準拠: 依存性注入パターン対応
        Args:
            console_service: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
        """
        # 基底クラス初期化（共通サービス）
        super().__init__(console_service=console_service, path_service=path_service, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work


    def execute(self, request: DependencyAnalysisRequest) -> DependencyAnalysisResponse:
        """依存関係分析を実行

        Command Patternによって複雑度を大幅に削減
        """
        try:
            if not request.quiet and hasattr(self, "_get_console"):
                console = self._get_console()
                console.print("[cyan]🔍 依存関係分析を開始します...[/cyan]\n")

            # プロジェクトルートの検証
            if not request.project_root.exists():
                return DependencyAnalysisResponse.error_response(
                    f"プロジェクトルートが見つかりません: {request.project_root}"
                )

            # 分析サービスを構築(Command Pattern)
            analysis_service = self._build_analysis_service(request)

            # 分析実行
            analysis_results = analysis_service.execute_all(request.project_root)

            # 結果を変換
            results: Any = self._convert_results(analysis_results)
            metrics = analysis_service.get_summary_metrics(analysis_results)
            total_violations = metrics.get("total_violations", 0)

            # レポート生成
            report_content = None
            if request.output_format == "text" or not request.quiet:
                report_content = self._generate_text_report(results, metrics)

            # ファイル出力
            if request.output_file:
                self._save_results_to_file(request, results, metrics)

            if not request.quiet and hasattr(self, "_get_console"):
                console = self._get_console()
                console.print(f"[green]✅ 分析完了: {total_violations}件の違反が検出されました[/green]")

            return DependencyAnalysisResponse.success_response(
                total_violations=total_violations,
                results=results,
                metrics=metrics,
                report_content=report_content,
            )

        except Exception as e:
            return DependencyAnalysisResponse.error_response(f"依存関係分析中にエラーが発生しました: {e}")

    def _build_analysis_service(self, request: DependencyAnalysisRequest) -> DependencyAnalysisService:
        """分析サービスを構築(Command Patternの組み立て)"""
        service = DependencyAnalysisService()

        if request.include_layer_analysis:
            if not request.quiet and hasattr(self, "_get_console"):
                console = self._get_console()
                console.print("[blue]📋 レイヤー違反分析...[/blue]")
            service.add_command(LayerViolationAnalysisCommand())

        if request.include_circular_analysis:
            if not request.quiet and hasattr(self, "_get_console"):
                console = self._get_console()
                console.print("[blue]🔄 循環依存分析...[/blue]")
            service.add_command(CircularDependencyAnalysisCommand())

        if request.include_external_analysis:
            if not request.quiet and hasattr(self, "_get_console"):
                console = self._get_console()
                console.print("[blue]📦 外部依存分析...[/blue]")
            service.add_command(ExternalDependencyAnalysisCommand())

        return service

    def _convert_results(self, analysis_results: dict) -> dict:
        """分析結果を変換"""
        results: dict[str, Any] = {}

        for name, result in analysis_results.items():
            results[name] = {
                "violations": [
                    {
                        "message": v.message,
                        "type": v.violation_type.value,
                        "severity": v.severity,
                    }
                    for v in result.violations
                ],
                "metrics": result.metrics,
                "graph_data": result.graph_data,
            }

        return results

    def _generate_text_report(self, results: dict, metrics: dict) -> str:
        """テキスト形式のレポートを生成"""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("📊 依存関係分析レポート")
        report_lines.append("=" * 60)

        # サマリー
        total_violations = metrics.get("total_violations", 0)
        report_lines.append(f"\n総違反数: {total_violations}件")

        for analysis_type in metrics.get("analysis_types", []):
            violation_count = metrics.get(f"{analysis_type}_violations", 0)
            report_lines.append(f"  {analysis_type}: {violation_count}件")

        # 詳細違反
        for name, result in results.items():
            violations: Any = result["violations"]
            if violations:
                report_lines.append(f"\n🔍 {name} ({len(violations)}件):")
                for violation in violations:
                    severity_emoji = "❌" if violation["severity"] == "error" else "⚠️"
                    report_lines.append(f"  {severity_emoji} {violation['message']}")

        # 推奨アクション
        report_lines.append("\n📝 推奨アクション:")
        if total_violations > 0:
            report_lines.append("  1. レイヤー違反を修正してください(必須)")
            report_lines.append("  2. 循環依存を解決してください(必須)")
            report_lines.append("  3. ドメイン層の外部依存を削減してください(推奨)")
        else:
            report_lines.append("  🎉 依存関係の問題は検出されませんでした!")

        report_lines.append("\n" + "=" * 60)
        return "\n".join(report_lines)

    def _save_results_to_file(self, request: DependencyAnalysisRequest, results: dict, metrics: dict) -> None:
        """結果をファイルに保存"""
        output_path = Path(request.output_file)

        if request.output_format == "json":
            data = {
                "analysis_results": results,
                "summary_metrics": metrics,
                "timestamp": "2025-01-18T12:00:00",  # 実際は現在時刻
            }
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        elif request.output_format == "text":
            report_content = self._generate_text_report(results, metrics)
            # バッチ書き込みを使用
            with output_path.open("w", encoding="utf-8") as f:
                f.write("依存関係分析レポート\n")
                f.write("=" * 60 + "\n")
                f.write(report_content)

        elif request.output_format == "mermaid":
            # Mermaid形式(簡易版)
            # バッチ書き込みを使用
            with output_path.open("w", encoding="utf-8") as f:
                f.write("graph TD\n")
                f.write("    A[Domain Layer] --> B[Application Layer]\n")
                f.write("    B --> C[Infrastructure Layer]\n")
                f.write("    B --> D[Presentation Layer]\n")

        elif request.output_format == "graphviz":
            # Graphviz形式(簡易版)
            # バッチ書き込みを使用
            with output_path.open("w", encoding="utf-8") as f:
                f.write("digraph dependencies {\n")
                f.write("    rankdir=TB;\n")
                f.write("    Domain -> Application;\n")
                f.write("    Application -> Infrastructure;\n")
                f.write("    Application -> Presentation;\n")
                f.write("}\n")

        if hasattr(self, "_get_console"):
            console = self._get_console()
            console.print(f"\n[green]結果を保存しました: {output_path}[/green]")
        elif self._logger_service:
            self._logger_service.info(f"結果を保存しました: {output_path}")


# 使用例
if __name__ == "__main__":
    logger_service = get_logger(__name__)

    use_case = DependencyAnalysisUseCase(logger_service=logger_service)

    # テスト用の例 - 実際の使用時はパスサービスを使用すること
    request = DependencyAnalysisRequest(project_root=Path.cwd() / "scripts", output_format="text", quiet=False)

    response = use_case.execute(request)

    if response.success:
        if response.report_content:
            logger_service.info(response.report_content)
    else:
        logger_service.error(f"依存関係分析でエラーが発生: {response.error_message}")
