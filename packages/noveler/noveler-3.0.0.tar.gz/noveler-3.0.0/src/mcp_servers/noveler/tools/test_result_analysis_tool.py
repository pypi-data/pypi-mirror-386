# File: src/mcp_servers/noveler/tools/test_result_analysis_tool.py
# Purpose: Implement the MCP test_result_analysis tool with enhanced delta
#          analysis, error grouping, and hierarchical context reporting.
# Context: Invoked by Noveler MCP servers to translate pytest-json-report
#          outputs into structured issues and guidance for downstream LLM
#          workflows.

"""test_result_analysis ツールの実装

SPEC-MCP-001: MCP Server Granular Microservice Architecture
B20準拠: FC/IS分離によるテスト結果解析とエラー構造化
"""

from __future__ import annotations

import re
import time
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import MCPToolBase, ToolIssue, ToolRequest, ToolResponse
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.logging.unified_logger import get_logger

from .test_result_analysis_components import (
    DeltaAnalysis,
    ErrorGroup,
    ErrorGrouper,
    HierarchicalContext,
    IncrementalAnalyzer,
    TestError,
    build_test_error,
)


class ResultAnalysisTool(MCPToolBase):
    """テスト結果解析ツール.

    `/noveler test run --output-json` の結果を解析し、エラー情報を構造化する。
    - テスト結果JSONの解析
    - エラー分類と重要度判定
    - LLMに最適化された修正提案生成
    - 差分分析とエラーグルーピングによるトークン効率化
    """

    def __init__(self) -> None:
        super().__init__(
            tool_name="test_result_analysis",
            tool_description="テスト結果解析とエラー構造化（LLM自動修正用データ生成）",
        )
        self._incremental_analyzer = IncrementalAnalyzer()
        self._error_grouper = ErrorGrouper()
        self._context_builder = HierarchicalContext()
        # フォールバックイベントは基底クラスの共通バッファを使用

    def get_input_schema(self) -> dict[str, Any]:
        """入力スキーマを返す."""
        return {
            "type": "object",
            "properties": {
                "test_result_json": {
                    "type": "object",
                    "description": "/noveler test run --output-jsonの出力結果",
                },
                "previous_test_result_json": {
                    "type": "object",
                    "description": "前回のテスト結果JSON（差分分析用）",
                },
                "focus_on_failures": {
                    "type": "boolean",
                    "description": "失敗したテストのみに焦点を当てる（省略時はtrue）",
                },
                "max_issues": {
                    "type": "integer",
                    "description": "最大Issue数（省略時は20）",
                    "minimum": 1,
                    "maximum": 100,
                },
                "include_suggestions": {
                    "type": "boolean",
                    "description": "修正提案を含める（省略時はtrue）",
                },
                "enable_delta_analysis": {
                    "type": "boolean",
                    "description": "差分分析を有効化（前回結果との比較）",
                },
                "enable_error_grouping": {
                    "type": "boolean",
                    "description": "エラーグルーピングを有効化",
                },
                "context_detail_level": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 3,
                    "description": "コンテキスト詳細度（1:要約、2:重要情報、3:全詳細）",
                },
            },
            "required": ["test_result_json"],
        }

    def execute(self, request: ToolRequest) -> ToolResponse:
        """テスト結果解析を実行."""
        logger = get_logger(__name__)

        start_time = time.time()
        logger.info("テスト結果解析開始")

        try:
            params = request.additional_params or {}

            try:
                ps = create_path_service()
                self._ps_collect_fallback(ps)
            except Exception:
                # PathServiceの取得は失敗しても解析処理を継続する
                pass

            if "test_result_json" not in params:
                raise KeyError("test_result_json")

            test_result = params["test_result_json"]
            focus_failures = params.get("focus_on_failures", True)
            max_issues = int(params.get("max_issues", 20) or 20)
            include_suggestions = params.get("include_suggestions", True)
            enable_delta = params.get("enable_delta_analysis", False)
            enable_grouping = params.get("enable_error_grouping", False)
            context_detail_level = self._normalise_context_level(params.get("context_detail_level", 1))
            previous_result = params.get("previous_test_result_json") if enable_delta else None

            logger.debug(
                "解析パラメータ: focus_failures=%s, max_issues=%s, include_suggestions=%s, delta=%s, grouping=%s, level=%s",
                focus_failures,
                max_issues,
                include_suggestions,
                enable_delta,
                enable_grouping,
                context_detail_level,
            )
            logger.debug("テスト結果の概要: %s", test_result.get("summary", {}))

            issues = self._analyze_test_results(test_result, focus_failures, max_issues, include_suggestions)

            delta_analysis: DeltaAnalysis | None = None
            if enable_delta:
                delta_analysis = self._incremental_analyzer.analyze_delta(test_result, previous_result)

            error_groups: list[ErrorGroup] = []
            if enable_grouping:
                error_groups = self._error_grouper.group_similar_errors(self._collect_test_errors(test_result))

            score = self._calculate_analysis_score(test_result, issues)

            logger.info("テスト結果解析完了: スコア=%.1f, Issue数=%d", score, len(issues))
            resp = self._create_response(True, score, issues, start_time)

            if delta_analysis is not None:
                resp.metadata["delta_analysis"] = delta_analysis.to_metadata(
                    compact=context_detail_level == 1,
                )

            if enable_grouping:
                resp.metadata["error_groups"] = [
                    group.to_metadata(example_limit=2 if context_detail_level == 1 else None)
                    for group in error_groups
                ]

            resp.metadata["context"] = self._context_builder.build_context(
                issues,
                detail_level=context_detail_level,
                summary=test_result.get("summary", {}),
                delta=delta_analysis,
                error_groups=error_groups,
            )

            self._apply_fallback_metadata(resp)
            return resp

        except KeyError as error:
            logger.exception("必須パラメータが不足")
            error_issue = ToolIssue(
                type="missing_parameter",
                severity="critical",
                message=f"必須パラメータが不足しています: {error}",
                suggestion="test_result_jsonパラメータを指定してください",
            )
            return self._create_response(False, 0.0, [error_issue], start_time)

        except Exception as error:  # pragma: no cover - 予期しない例外を確実に捕捉
            logger.exception("テスト結果解析エラー")
            error_issue = ToolIssue(
                type="analysis_error",
                severity="critical",
                message=f"解析処理に失敗しました: {error}",
                suggestion="テスト結果JSONの形式を確認してください",
            )
            return self._create_response(False, 0.0, [error_issue], start_time)

    def _normalise_context_level(self, raw_level: Any) -> int:
        try:
            level = int(raw_level)
        except (TypeError, ValueError):
            level = 1
        return max(1, min(3, level))

    def _analyze_test_results(
        self,
        test_result: dict[str, Any],
        focus_failures: bool,
        max_issues: int,
        include_suggestions: bool,
    ) -> list[ToolIssue]:
        """テスト結果を詳細解析してIssueリストを生成."""
        logger = get_logger(__name__)
        issues: list[ToolIssue] = []

        stats_issues = self._analyze_test_statistics(test_result)
        logger.debug("統計解析結果: %d個のIssue", len(stats_issues))
        issues.extend(stats_issues)

        if focus_failures:
            failure_issues = self._analyze_test_failures(test_result, include_suggestions)
            issues.extend(failure_issues)

        error_issues = self._analyze_test_errors(test_result, include_suggestions)
        issues.extend(error_issues)

        runtime_issues = self._analyze_runtime_issues(test_result)
        issues.extend(runtime_issues)

        if len(issues) > max_issues:
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            issues.sort(key=lambda item: severity_order.get(item.severity, 4))
            issues = issues[:max_issues]

        return issues

    def _analyze_test_statistics(self, test_result: dict[str, Any]) -> list[ToolIssue]:
        """テスト統計情報を解析."""
        issues: list[ToolIssue] = []

        summary = test_result.get("summary", {})
        total = summary.get("total", 0)
        collected = summary.get("collected", total)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        error = summary.get("error", 0)
        skipped = summary.get("skipped", 0)

        if total == 0 and collected > 0:
            total = collected

        if total > 0 and passed == 0:
            estimated_passed = total - failed - error - skipped
            if estimated_passed >= 0:
                passed = estimated_passed

        if total > 0:
            success_rate = passed / total
            if success_rate < 0.5:
                issues.append(
                    ToolIssue(
                        type="low_success_rate",
                        severity="critical",
                        message=f"テスト成功率が低すぎます（{success_rate:.1%}）: {passed}/{total}個成功",
                        suggestion="失敗したテストを優先的に修正することを推奨します",
                        details={"success_rate": round(success_rate, 3)},
                    )
                )
            elif success_rate < 0.8:
                issues.append(
                    ToolIssue(
                        type="medium_success_rate",
                        severity="high",
                        message=f"テスト成功率を改善できます（{success_rate:.1%}）: {passed}/{total}個成功",
                        suggestion="失敗テストの原因を調査し、段階的に修正してください",
                        details={"success_rate": round(success_rate, 3)},
                    )
                )
            elif success_rate < 1.0:
                issues.append(
                    ToolIssue(
                        type="some_failures",
                        severity="medium",
                        message=f"一部のテストが失敗しています: {failed}個失敗, {error}個エラー",
                        suggestion="失敗とエラーの詳細を確認して修正してください",
                        details={"failed": failed, "error": error},
                    )
                )

        if failed > 0:
            issues.append(
                ToolIssue(
                    type="test_failures",
                    severity="high",
                    message=f"テスト失敗が発生しています: {failed}個",
                    suggestion="失敗したテストのアサーション内容を確認してください",
                    details={"failed": failed},
                )
            )

        if error > 0:
            issues.append(
                ToolIssue(
                    type="test_errors",
                    severity="critical",
                    message=f"テストエラーが発生しています: {error}個",
                    suggestion="セットアップやインポートエラーを確認してください",
                    details={"error": error},
                )
            )

        if skipped > 5:
            issues.append(
                ToolIssue(
                    type="many_skipped_tests",
                    severity="medium",
                    message=f"多くのテストがスキップされています: {skipped}個",
                    suggestion="スキップ理由を確認し、必要に応じて有効化を検討してください",
                    details={"skipped": skipped},
                )
            )

        return issues

    def _analyze_test_failures(self, test_result: dict[str, Any], include_suggestions: bool) -> list[ToolIssue]:
        """失敗したテストを詳細解析."""
        issues: list[ToolIssue] = []
        tests = test_result.get("tests", [])
        for test in tests:
            if test.get("outcome") == "failed":
                issue = self._create_failure_issue(test, include_suggestions)
                if issue:
                    issues.append(issue)
        return issues

    def _analyze_test_errors(self, test_result: dict[str, Any], include_suggestions: bool) -> list[ToolIssue]:
        """エラーが発生したテストを解析."""
        issues: list[ToolIssue] = []
        tests = test_result.get("tests", [])
        for test in tests:
            if test.get("outcome") == "error":
                issue = self._create_error_issue(test, include_suggestions)
                if issue:
                    issues.append(issue)
        return issues

    def _analyze_runtime_issues(self, test_result: dict[str, Any]) -> list[ToolIssue]:
        """実行時の問題を解析."""
        issues: list[ToolIssue] = []

        duration = test_result.get("duration", 0)
        if duration > 300:
            issues.append(
                ToolIssue(
                    type="slow_test_execution",
                    severity="medium",
                    message=f"テスト実行が遅すぎます（{duration:.1f}秒）",
                    suggestion="並列実行の活用や遅いテストの最適化を検討してください",
                    details={"duration": duration},
                )
            )

        collect_report = test_result.get("collect_report")
        if isinstance(collect_report, dict) and not collect_report.get("passed", True):
            issues.append(
                ToolIssue(
                    type="collection_error",
                    severity="critical",
                    message="テストの収集段階でエラーが発生しました",
                    suggestion="インポートエラーやシンタックスエラーを修正してください",
                )
            )

        return issues

    def _create_failure_issue(self, test: dict[str, Any], include_suggestions: bool) -> ToolIssue | None:
        """失敗テストのIssue作成."""
        test_name = test.get("nodeid", "不明なテスト")
        call_info = test.get("call", {})
        longrepr = call_info.get("longrepr", "詳細不明")

        error_type, severity = self._classify_test_error(longrepr)

        suggestion = ""
        if include_suggestions:
            suggestion = self._generate_fix_suggestion(error_type, longrepr, test_name)

        return ToolIssue(
            type=error_type,
            severity=severity,
            message=f"テスト失敗: {test_name} - {longrepr[:200]}...",
            suggestion=suggestion,
            line_number=self._extract_line_number(longrepr),
            details={"nodeid": test_name, "outcome": "failed"},
        )

    def _create_error_issue(self, test: dict[str, Any], include_suggestions: bool) -> ToolIssue | None:
        """エラーテストのIssue作成."""
        test_name = test.get("nodeid", "不明なテスト")
        setup_info = test.get("setup", {}) or test.get("call", {})
        longrepr = setup_info.get("longrepr", "詳細不明")

        error_type, severity = self._classify_test_error(longrepr)

        suggestion = ""
        if include_suggestions:
            suggestion = self._generate_fix_suggestion(error_type, longrepr, test_name)

        return ToolIssue(
            type=f"{error_type}_error",
            severity="critical",
            message=f"テストエラー: {test_name} - {longrepr[:200]}...",
            suggestion=suggestion,
            line_number=self._extract_line_number(longrepr),
            details={"nodeid": test_name, "outcome": "error"},
        )

    def _collect_test_errors(self, test_result: dict[str, Any]) -> list[TestError]:
        """Collect failure and error tests for grouping."""
        errors: list[TestError] = []
        for entry in test_result.get("tests", []):
            outcome = entry.get("outcome", "").lower()
            if outcome not in {"failed", "error"}:
                continue
            nodeid = entry.get("nodeid", "")
            payload = (entry.get("call") or entry.get("setup") or {})
            longrepr = payload.get("longrepr", "")
            error_type, severity = self._classify_test_error(longrepr)
            if outcome == "error":
                severity = "critical"
            errors.append(build_test_error(nodeid, error_type, severity, longrepr))
        return errors

    def _classify_test_error(self, error_message: str) -> tuple[str, str]:
        """エラーメッセージから種類と重要度を分類."""
        error_message_lower = error_message.lower()

        if "importerror" in error_message_lower or "modulenotfounderror" in error_message_lower:
            return "import_error", "critical"
        if "attributeerror" in error_message_lower:
            return "attribute_error", "high"
        if "assertionerror" in error_message_lower:
            return "assertion_failure", "medium"
        if "typeerror" in error_message_lower:
            return "type_error", "high"
        if "valueerror" in error_message_lower:
            return "value_error", "medium"
        if "filenotfounderror" in error_message_lower:
            return "file_not_found", "high"
        if "keyerror" in error_message_lower:
            return "key_error", "medium"
        if "nameerror" in error_message_lower:
            return "name_error", "high"
        if "timeout" in error_message_lower:
            return "timeout_error", "high"
        if "memoryerror" in error_message_lower:
            return "memory_error", "critical"
        return "unknown_error", "medium"

    def _generate_fix_suggestion(self, error_type: str, _error_message: str, test_name: str) -> str:
        """エラータイプに基づく修正提案生成."""
        suggestions = {
            "import_error": "インポートパスを確認し、必要な依存関係をインストールしてください",
            "attribute_error": "オブジェクトの型や属性名を確認してください",
            "assertion_failure": "期待値と実際の値を比較し、テストの前提条件を確認してください",
            "type_error": "引数の型や戻り値の型を確認してください",
            "value_error": "入力値の妥当性や範囲を確認してください",
            "file_not_found": "ファイルパスの存在を確認し、テストデータを準備してください",
            "key_error": "辞書のキーや設定項目の存在を確認してください",
            "name_error": "変数名や関数名のスペルミスを確認してください",
            "timeout_error": "処理時間の短縮やタイムアウト閾値の調整を検討してください",
            "memory_error": "メモリ使用量を削減するか、チャンク処理などを検討してください",
            "unknown_error": "エラーメッセージの詳細を確認し、該当箇所のコードを調査してください",
        }

        base_suggestion = suggestions.get(error_type, suggestions["unknown_error"])

        lowered_name = test_name.lower()
        if "integration" in lowered_name:
            base_suggestion += "\n統合テストの場合、依存するコンポーネントの初期化を確認してください"
        elif "unit" in lowered_name:
            base_suggestion += "\n単体テストの場合、モックやスタブの設定を確認してください"

        return base_suggestion

    def _extract_line_number(self, error_message: str) -> int | None:
        """エラーメッセージから行番号を抽出."""
        match = re.search(r":(\d+)", error_message)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    def _calculate_analysis_score(self, test_result: dict[str, Any], issues: list[ToolIssue]) -> float:
        """解析スコアを計算（0-100）."""
        summary = test_result.get("summary", {})
        total = summary.get("total", 0)
        passed = summary.get("passed", 0)

        base_score = 100.0 if total == 0 else passed / total * 100.0

        penalty = 0
        for issue in issues:
            if issue.severity == "critical":
                penalty += 15
            elif issue.severity == "high":
                penalty += 10
            elif issue.severity == "medium":
                penalty += 5
            else:
                penalty += 2

        return max(0.0, base_score - penalty)
