#!/usr/bin/env python3

"""Application.use_cases.test_auto_fix_use_case
Where: Application use case exercising auto-fix routines in a testing context.
What: Sets up sample inputs, runs auto-fix pipelines, and reports outcomes for validation.
Why: Provides an application-layer harness to verify auto-fix behaviour without manual scripts.
"""

from __future__ import annotations


import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.test_error_diagnostic_engine import (
    ErrorContext,
    ErrorDiagnosticEngine,
    ErrorDiagnosticResult,
    ErrorSeverityLevel,
)


@dataclass
class AutoFixTestRequest:
    """テスト自動修正リクエスト"""

    project_root: Path
    test_result_json: dict[str, Any]
    focus_on_failures: bool = True
    max_issues: int = 20
    include_suggestions: bool = True
    enable_llm_integration: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.project_root, Path):
            object.__setattr__(self, "project_root", Path(self.project_root))


@dataclass
class AutoFixTestResponse:
    """テスト自動修正レスポンス"""

    success: bool
    project_root: Path
    total_tests: int
    failed_tests: int
    error_tests: int
    diagnostic_results: list[TestErrorDiagnosticResult]
    llm_structured_data: dict[str, Any] | None
    execution_time_ms: float
    error_message: str | None = None

    def get_auto_fixable_count(self) -> int:
        """自動修正可能なエラー数を取得"""
        return sum(1 for result in self.diagnostic_results if result.auto_fixable)

    def get_high_priority_issues(self) -> list[TestErrorDiagnosticResult]:
        """高優先度の問題を取得"""
        return [
            result for result in self.diagnostic_results
            if result.priority_score >= 70
        ]

    def get_critical_errors(self) -> list[TestErrorDiagnosticResult]:
        """クリティカルエラーを取得"""
        return [
            result for result in self.diagnostic_results
            if result.severity == ErrorSeverityLevel.CRITICAL
        ]


class AutoFixTestUseCase(AbstractUseCase[AutoFixTestRequest, AutoFixTestResponse]):
    """テスト自動修正ユースケース - B20準拠

    B20準拠DIパターン:
    - logger_service, unit_of_work 注入
    - テスト結果の解析と診断
    - LLM向け構造化データ生成
    """

    def __init__(
        self,
        logger_service,
        unit_of_work,
        **kwargs,
    ) -> None:
        """テスト自動修正ユースケースの初期化 - B20準拠

        Args:
            logger_service: ロガーサービス
            unit_of_work: Unit of Work
            **kwargs: AbstractUseCaseの引数
        """
        # 基底クラス初期化
        super().__init__(**kwargs)

        self._logger_service = logger_service
        self._unit_of_work = unit_of_work
        self._diagnostic_engine = ErrorDiagnosticEngine()

    async def execute(self, request: AutoFixTestRequest) -> AutoFixTestResponse:
        """テスト自動修正の実行

        Args:
            request: テスト自動修正リクエスト

        Returns:
            TestAutoFixResponse: 自動修正結果
        """
        start_time = time.time()

        try:
            self._logger_service.info("テスト自動修正開始")

            # 1. テスト結果の基本情報抽出
            test_summary = self._extract_test_summary(request.test_result_json)

            # 2. エラーコンテキストの作成
            error_contexts = self._create_error_contexts(
                request.test_result_json,
                request.focus_on_failures
            )

            # 3. 診断エンジンによる詳細解析
            diagnostic_results = self._diagnose_errors(error_contexts)

            # 4. 優先度によるフィルタリング
            filtered_results = self._filter_by_priority(diagnostic_results, request.max_issues)

            # 5. LLM向け構造化データ生成
            llm_data = None
            if request.enable_llm_integration:
                llm_data = self._generate_llm_structured_data(
                    filtered_results,
                    test_summary,
                    request.include_suggestions
                )

            execution_time = (time.time() - start_time) * 1000

            self._logger_service.info(
                f"テスト自動修正完了: 診断結果{len(filtered_results)}件、"
                f"自動修正可能{sum(1 for r in filtered_results if r.auto_fixable)}件"
            )

            return AutoFixTestResponse(
                success=True,
                project_root=request.project_root,
                total_tests=test_summary["total"],
                failed_tests=test_summary["failed"],
                error_tests=test_summary["error"],
                diagnostic_results=filtered_results,
                llm_structured_data=llm_data,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._logger_service.error(f"テスト自動修正でエラー発生: {e}")

            return AutoFixTestResponse(
                success=False,
                project_root=request.project_root,
                total_tests=0,
                failed_tests=0,
                error_tests=0,
                diagnostic_results=[],
                llm_structured_data=None,
                execution_time_ms=execution_time,
                error_message=f"テスト自動修正でエラーが発生しました: {e!s}",
            )

    def _extract_test_summary(self, test_result_json: dict[str, Any]) -> dict[str, int]:
        """テスト結果の基本統計情報を抽出"""
        summary = test_result_json.get("summary", {})
        return {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "error": summary.get("error", 0),
            "skipped": summary.get("skipped", 0),
        }

    def _create_error_contexts(
        self,
        test_result_json: dict[str, Any],
        focus_on_failures: bool
    ) -> list[ErrorContext]:
        """エラーコンテキストのリストを作成"""
        contexts = []

        # 1. 通常のテスト失敗を処理
        tests = test_result_json.get("tests", [])
        for test in tests:
            outcome = test.get("outcome", "")

            # フォーカス設定に基づく抽出
            if focus_on_failures and outcome not in ["failed", "error"]:
                continue

            if outcome in ["failed", "error"]:
                context = self._create_single_error_context(test, outcome)
                if context:
                    contexts.append(context)

        # 2. collectorsセクションのエラーを処理（ImportError等）
        collectors = test_result_json.get("collectors", [])
        for collector in collectors:
            outcome = collector.get("outcome", "")

            if outcome == "failed":
                # collectorsエラーからコンテキストを作成
                context = self._create_collector_error_context(collector)
                if context:
                    contexts.append(context)

        return contexts

    def _create_single_error_context(
        self,
        test: dict[str, Any],
        outcome: str
    ) -> ErrorContext | None:
        """単一テストのエラーコンテキストを作成"""
        try:
            test_name = test.get("nodeid", "")

            # テストファイルの抽出
            test_file = test_name.split("::")[0] if "::" in test_name else ""

            # エラー情報の抽出
            if outcome == "failed":
                call_info = test.get("call", {})
                error_message = call_info.get("longrepr", "")
                stack_trace = str(call_info.get("traceback", ""))
                line_number = self._extract_line_number_from_call(call_info)
            else:  # error
                setup_info = test.get("setup", {}) or test.get("call", {})
                error_message = setup_info.get("longrepr", "")
                stack_trace = str(setup_info.get("traceback", ""))
                line_number = self._extract_line_number_from_call(setup_info)

            # テストタイプの推定
            test_type = self._infer_test_type(test_name)

            # テストマーカーの抽出
            test_markers = test.get("markers", [])

            # 実行時間の取得
            execution_time = test.get("duration", 0.0)

            return ErrorContext(
                test_name=test_name,
                test_file=test_file,
                error_message=error_message,
                stack_trace=stack_trace,
                line_number=line_number,
                test_type=test_type,
                test_markers=test_markers,
                execution_time=execution_time
            )

        except Exception as e:
            self._logger_service.warning(f"エラーコンテキスト作成失敗: {test.get('nodeid', '不明')}: {e}")
            return None

    def _create_collector_error_context(self, collector: dict[str, Any]) -> ErrorContext | None:
        """collectorsセクションのエラーからコンテキストを作成"""
        try:
            nodeid = collector.get("nodeid", "unknown_collector")
            longrepr = collector.get("longrepr", "")

            # longreprからエラーメッセージとトレースバックを抽出
            if isinstance(longrepr, str):
                error_message = longrepr
                stack_trace = longrepr
            else:
                error_message = f"Collection failed: {nodeid}"
                stack_trace = str(longrepr)

            # ファイルパスの抽出（nodeIDからパスを推定）
            test_file = nodeid.replace("::", "/") if "::" in nodeid else nodeid

            return ErrorContext(
                test_name=f"collector:{nodeid}",
                test_file=test_file,
                error_message=error_message,
                stack_trace=stack_trace,
                line_number=None,
                test_type="collection",
                test_markers=["collection_error"],
                execution_time=0.0,
            )

        except Exception as e:
            self._logger_service.warning(f"collectorsエラーコンテキスト作成失敗: {e}")
            return None

    def _extract_line_number_from_call(self, call_info: dict[str, Any]) -> int | None:
        """呼び出し情報から行番号を抽出"""
        # traceback情報から行番号を抽出
        traceback = call_info.get("traceback", [])
        if traceback and isinstance(traceback, list):
            for entry in traceback:
                if isinstance(entry, dict) and "lineno" in entry:
                    return entry["lineno"]

        # longrepr文字列から行番号を抽出
        longrepr = call_info.get("longrepr", "")
        if longrepr:
            match = re.search(r":(\d+)", str(longrepr))
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass

        return None

    def _infer_test_type(self, test_name: str) -> str | None:
        """テスト名からテストタイプを推定"""
        test_name_lower = test_name.lower()

        if "integration" in test_name_lower:
            return "integration"
        if "unit" in test_name_lower:
            return "unit"
        if "e2e" in test_name_lower or "end_to_end" in test_name_lower:
            return "e2e"
        if "test_" in test_name_lower:
            return "unit"  # デフォルトで単体テスト扱い

        return None

    def _diagnose_errors(self, contexts: list[ErrorContext]) -> list[TestErrorDiagnosticResult]:
        """診断エンジンによるエラー診断"""
        results = []

        for context in contexts:
            try:
                result = self._diagnostic_engine.diagnose_error(context)
                results.append(result)
            except Exception as e:
                self._logger_service.warning(
                    f"エラー診断失敗: {context.test_name}: {e}"
                )

        return results

    def _filter_by_priority(
        self,
        results: list[TestErrorDiagnosticResult],
        max_issues: int
    ) -> list[TestErrorDiagnosticResult]:
        """優先度によるフィルタリング"""
        # 優先度スコアの降順でソート
        sorted_results = sorted(results, key=lambda x: x.priority_score, reverse=True)

        # 最大Issue数で制限
        return sorted_results[:max_issues]

    def _generate_llm_structured_data(
        self,
        diagnostic_results: list[TestErrorDiagnosticResult],
        test_summary: dict[str, int],
        include_suggestions: bool
    ) -> dict[str, Any]:
        """LLM向け構造化データ生成"""
        # 基本統計
        basic_stats = {
            "test_summary": test_summary,
            "success_rate": test_summary["passed"] / max(test_summary["total"], 1),
            "total_issues": len(diagnostic_results),
            "auto_fixable_issues": sum(1 for r in diagnostic_results if r.auto_fixable),
            "critical_issues": sum(
                1 for r in diagnostic_results
                if r.severity.value == "critical"
            )
        }

        # エラータイプ別統計
        error_type_stats = {}
        for result in diagnostic_results:
            error_type = result.error_type.value
            if error_type not in error_type_stats:
                error_type_stats[error_type] = {
                    "count": 0,
                    "auto_fixable": 0,
                    "avg_priority": 0.0
                }

            error_type_stats[error_type]["count"] += 1
            if result.auto_fixable:
                error_type_stats[error_type]["auto_fixable"] += 1
            error_type_stats[error_type]["avg_priority"] += result.priority_score

        # 平均優先度の計算
        for stats in error_type_stats.values():
            if stats["count"] > 0:
                stats["avg_priority"] /= stats["count"]

        # 詳細診断結果
        detailed_issues = []
        for result in diagnostic_results:
            issue_data = {
                "error_type": result.error_type.value,
                "severity": result.severity.value,
                "priority_score": result.priority_score,
                "confidence": result.confidence,
                "auto_fixable": result.auto_fixable,
                "affected_files": result.affected_files,
                "error_pattern": result.error_pattern,
                "root_cause": result.root_cause_summary,
            }

            if include_suggestions:
                issue_data["fix_suggestions"] = result.fix_suggestions
                issue_data["related_errors"] = result.related_errors

            detailed_issues.append(issue_data)

        # 修正推奨順序
        recommended_fix_order = self._generate_fix_order(diagnostic_results)

        return {
            "analysis_metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "analysis_type": "test_auto_fix",
                "focus_on_failures": True,
                "max_issues": len(diagnostic_results)
            },
            "basic_statistics": basic_stats,
            "error_type_statistics": error_type_stats,
            "detailed_issues": detailed_issues,
            "recommended_fix_order": recommended_fix_order,
            "llm_integration_hints": {
                "primary_focus": "自動修正可能なエラーから優先的に対処してください",
                "secondary_focus": "クリティカルエラーの手動修正を検討してください",
                "suggested_approach": "Import/Syntax エラー → Type/Attribute エラー → Assertion エラーの順で修正"
            }
        }

    def _generate_fix_order(self, results: list[TestErrorDiagnosticResult]) -> list[dict[str, Any]]:
        """修正推奨順序の生成"""
        # 自動修正可能かつ高優先度のものを最優先
        auto_fixable_high_priority = [
            r for r in results
            if r.auto_fixable and r.priority_score >= 70
        ]

        # クリティカルエラー（手動修正必要）
        critical_manual = [
            r for r in results
            if r.severity.value == "critical" and not r.auto_fixable
        ]

        # その他の自動修正可能
        other_auto_fixable = [
            r for r in results
            if r.auto_fixable and r.priority_score < 70
        ]

        order = []

        # 最優先：自動修正可能な高優先度
        for result in auto_fixable_high_priority:
            order.append({
                "priority": "highest",
                "error_type": result.error_type.value,
                "auto_fixable": True,
                "reason": "自動修正可能かつ高優先度",
                "affected_files": result.affected_files[:3]  # 最大3ファイル
            })

        # 次優先：クリティカルエラー（手動）
        for result in critical_manual:
            order.append({
                "priority": "high",
                "error_type": result.error_type.value,
                "auto_fixable": False,
                "reason": "クリティカルエラー（手動修正必要）",
                "affected_files": result.affected_files[:3]
            })

        # 低優先：その他の自動修正可能
        for result in other_auto_fixable:
            order.append({
                "priority": "medium",
                "error_type": result.error_type.value,
                "auto_fixable": True,
                "reason": "自動修正可能",
                "affected_files": result.affected_files[:3]
            })

        return order[:10]  # 最大10件に制限

    def get_structured_summary(self, response: TestAutoFixResponse) -> dict[str, Any]:
        """構造化サマリーを生成

        Args:
            response: テスト自動修正結果

        Returns:
            dict[str, Any]: サマリー情報
        """
        if not response.success:
            return {"success": False, "error": response.error_message}

        return {
            "success": True,
            "project_root": str(response.project_root),
            "test_summary": {
                "total_tests": response.total_tests,
                "failed_tests": response.failed_tests,
                "error_tests": response.error_tests,
                "success_rate": (
                    (response.total_tests - response.failed_tests - response.error_tests)
                    / max(response.total_tests, 1)
                )
            },
            "diagnostic_summary": {
                "total_issues": len(response.diagnostic_results),
                "auto_fixable_count": response.get_auto_fixable_count(),
                "high_priority_count": len(response.get_high_priority_issues()),
                "critical_error_count": len(response.get_critical_errors())
            },
            "execution_time_ms": response.execution_time_ms,
            "llm_integration_ready": response.llm_structured_data is not None,
        }
