#!/usr/bin/env python3

"""Domain.services.evaluation_result_formatter
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""評価結果フォーマットサービス

A31評価結果の出力フォーマット専用ドメインサービス
"""


from noveler.domain.value_objects.a31_evaluation_result import EvaluationResult


class EvaluationResultFormatter:
    """評価結果フォーマットサービス"""

    def generate_review_output(
        self,
        evaluation_results: dict[str, EvaluationResult],
        verbosity: str,
    ) -> str:
        """レビュー出力を生成

        Args:
            evaluation_results: 評価結果
            verbosity: 詳細度(none/basic/standard/verbose)

        Returns:
            str: レビュー出力
        """
        if verbosity == "none":
            return ""

        lines = ["Claude Code評価結果:"]

        for item_id, result in evaluation_results.items():
            # 基本ステータス表示
            lines.extend(self._format_basic_status(item_id, result))

            # 詳細情報表示
            if verbosity in ["standard", "verbose"]:
                lines.extend(self._format_detailed_feedback(result))

            # 追加情報表示
            if verbosity == "verbose":
                lines.extend(self._format_verbose_info(result))

        return "\n".join(lines)

    def _format_basic_status(self, item_id: str, result: EvaluationResult) -> list[str]:
        """基本ステータスをフォーマット

        Args:
            item_id: 項目ID
            result: 評価結果

        Returns:
            list[str]: フォーマット済み行リスト
        """
        status_icon = "✓" if result.passed else "✗"
        status_text = "PASS" if result.passed else "FAIL"
        return [f"  {item_id} [{status_text}] {status_icon}"]

    def _format_detailed_feedback(self, result: EvaluationResult) -> list[str]:
        """詳細フィードバックをフォーマット

        Args:
            result: 評価結果

        Returns:
            list[str]: フォーマット済み行リスト
        """
        lines = []
        claude_eval = result.details.get("claude_evaluation", {})

        # 良い点の表示
        evidence_points = claude_eval.get("evidence_points", [])
        for evidence in evidence_points:
            line_info = self._format_line_range(evidence.get("line_range", ["?", "?"]))
            content = evidence.get("content", "")
            lines.append(f"    ✓ 良い点: {content} {line_info}")

        # 改善提案の表示
        improvements = claude_eval.get("improvement_suggestions", [])
        for improvement in improvements:
            line_info = self._format_line_range(improvement.get("line_range", ["?", "?"]))
            content = improvement.get("content", "")
            lines.append(f"    ⚠ 改善案: {content} {line_info}")

        # 問題点の表示
        issues = claude_eval.get("issues_found", [])
        for issue in issues:
            line_number = issue.get("line_number", "?")
            content = issue.get("content", "")
            lines.append(f"    ✗ 問題: {content} (行{line_number})")

        return lines

    def _format_verbose_info(self, result: EvaluationResult) -> list[str]:
        """詳細情報をフォーマット

        Args:
            result: 評価結果

        Returns:
            list[str]: フォーマット済み行リスト
        """
        confidence = result.details.get("confidence", 0.0)
        return [f"    信頼度: {confidence:.1%}"]

    def _format_line_range(self, line_range: list[str | int]) -> str:
        """行範囲をフォーマット

        Args:
            line_range: 行範囲リスト

        Returns:
            str: フォーマット済み行範囲文字列
        """
        if len(line_range) >= 2:
            return f"(行{line_range[0]}-{line_range[1]})"
        return "(行?)"
