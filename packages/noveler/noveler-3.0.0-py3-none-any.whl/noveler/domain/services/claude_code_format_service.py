#!/usr/bin/env python3
"""Claude Code フォーマットサービス

SPEC-CLAUDE-002に基づくドメインサービス
"""

from typing import Any

from noveler.domain.entities.file_quality_check_session import FileQualityCheckSession


class ClaudeCodeFormatService:
    """Claude Code向けフォーマット変換サービス

    品質チェックセッションをClaude向けに変換する責務を持つ
    """

    def format_errors_for_claude(self, sessions: list[FileQualityCheckSession]) -> list[dict[str, Any]]:
        """Claude向けエラーフォーマット変換

        Args:
            sessions: 品質チェックセッション一覧

        Returns:
            Claude向けエラー情報一覧
        """
        if not sessions:
            return []

        formatted_errors = []

        for session in sessions:
            if not session.has_errors():
                continue

            error_details = session.get_error_details()
            for error in error_details:
                formatted_error = {
                    "file_path": str(session.file_path),
                    "line_number": error.get("line_number", 0),
                    "error_type": self._classify_error_type(error.get("code", "")),
                    "error_code": error.get("code", "UNKNOWN"),
                    "message": error.get("message", ""),
                    "priority": self._get_error_priority(error.get("code", "")),
                }
                formatted_errors.append(formatted_error)

        return formatted_errors

    def generate_fix_suggestions(self, sessions: list[FileQualityCheckSession]) -> list[dict[str, Any]]:
        """修正提案生成

        Args:
            sessions: 品質チェックセッション一覧

        Returns:
            修正提案一覧
        """
        suggestions = []

        for session in sessions:
            if not session.has_errors():
                continue

            error_details = session.get_error_details()
            for error in error_details:
                suggestion = {
                    "file_path": str(session.file_path),
                    "error_code": error.get("code", ""),
                    "message": self._generate_suggestion_message(error),
                    "priority": self._get_error_priority(error.get("code", "")),
                }
                suggestions.append(suggestion)

        return suggestions

    def create_priority_ranking(self, sessions: list[FileQualityCheckSession]) -> list[dict[str, Any]]:
        """優先度ランキング作成

        Args:
            sessions: 品質チェックセッション一覧

        Returns:
            優先度順のエラー一覧
        """
        formatted_errors = self.format_errors_for_claude(sessions)

        # 優先度順でソート (high > medium > low)
        priority_order = {"high": 0, "medium": 1, "low": 2}

        return sorted(formatted_errors, key=lambda x: priority_order.get(x["priority"], 3))

    def filter_by_priority(self, sessions: list[FileQualityCheckSession], priority: str) -> list[dict[str, Any]]:
        """優先度でフィルタ

        Args:
            sessions: 品質チェックセッション一覧
            priority: フィルタする優先度

        Returns:
            フィルタされたエラー一覧
        """
        formatted_errors = self.format_errors_for_claude(sessions)

        return [error for error in formatted_errors if error["priority"] == priority]

    def _classify_error_type(self, error_code: str) -> str:
        """エラータイプ分類

        Args:
            error_code: エラーコード

        Returns:
            エラータイプ
        """
        if error_code.startswith(("E9", "F")):
            return "syntax"
        if error_code.startswith("ANN"):
            return "type"
        return "style"

    def _get_error_priority(self, error_code: str) -> str:
        """エラー優先度取得

        Args:
            error_code: エラーコード

        Returns:
            優先度
        """
        if error_code.startswith(("E9", "F")):
            return "high"  # 構文エラーは高優先度
        if error_code.startswith("ANN"):
            return "medium"  # 型エラーは中優先度
        return "low"  # スタイルエラーは低優先度

    def _generate_suggestion_message(self, error: dict[str, Any]) -> str:
        """修正提案メッセージ生成

        Args:
            error: エラー情報

        Returns:
            修正提案メッセージ
        """
        code = error.get("code", "")

        suggestions = {
            "E999": "構文エラー - 括弧、クォート、インデントを確認してください",
            "F401": "未使用インポート - 不要なimport文を削除してください",
            "ANN001": "型注釈不足 - 引数に型注釈を追加してください",
            "ANN201": "戻り値型注釈不足 - 戻り値の型注釈を追加してください",
            "E501": "行長すぎ - 79文字以内に改行してください",
        }

        return suggestions.get(code, f"エラーコード {code} の修正が必要です")
