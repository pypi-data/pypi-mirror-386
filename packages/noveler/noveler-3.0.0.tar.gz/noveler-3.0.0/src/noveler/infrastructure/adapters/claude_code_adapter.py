"""Integration helpers for exporting quality reports to Claude Code."""

from noveler.presentation.shared.shared_utilities import console

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from noveler.domain.entities.file_quality_check_session import FileQualityCheckSession
from noveler.domain.value_objects.project_time import project_now


class ClaudeCodeAdapter:
    """Manage exports used by Claude Code quality workflows."""

    def __init__(self, project_root: Path, logger_service=None, console_service=None) -> None:
        """Configure output locations and optional services.

        Args:
            project_root: Root directory used to resolve export destinations.
            logger_service: Optional logger used to record operational events.
            console_service: Optional console abstraction used for user feedback.
        """
        self.project_root = project_root
        self.output_dir = project_root / "temp"
        self.error_file = self.output_dir / "claude_code_errors.json"
        self.suggestion_file = self.output_dir / "claude_code_suggestions.md"
        self.output_dir.mkdir(exist_ok=True)
        self.logger_service = logger_service
        self.console_service = console_service

    def export_errors_for_claude(self, sessions: list[FileQualityCheckSession]) -> None:
        """Export quality check errors into artifacts for Claude Code.

        Args:
            sessions: Completed file quality check sessions to summarize.
        """
        errors: list[Any] = []
        summary = {"total_errors": 0, "syntax_errors": 0, "type_errors": 0, "style_errors": 0}
        for session in sessions:
            if not session.has_errors():
                continue
            session_errors = session.get_error_details()
            for error in session_errors:
                claude_error = {
                    "file_path": str(session.file_path).replace(str(self.project_root), ""),
                    "line_number": error.get("line_number", 0),
                    "error_type": self._classify_error_type(error.get("code", "")),
                    "error_code": error.get("code", "UNKNOWN"),
                    "message": error.get("message", ""),
                    "suggestion": self._generate_suggestion(error),
                }
                errors.append(claude_error)
                error_type = claude_error["error_type"]
                summary["total_errors"] += 1
                if error_type == "syntax":
                    summary["syntax_errors"] += 1
                elif error_type == "type":
                    summary["type_errors"] += 1
                elif error_type == "style":
                    summary["style_errors"] += 1
        output_data: dict[str, Any] = {
            "timestamp": project_now().to_iso_string(),
            "project_root": str(self.project_root),
            "errors": errors,
            "summary": summary,
        }
        with Path(self.error_file).open("w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        self._generate_suggestions_markdown(errors, summary)

    def _classify_error_type(self, error_code: str) -> str:
        """Map a raw linting error code to a broad category.

        Args:
            error_code: Identifier produced by the linting or analysis tool.

        Returns:
            str: Category label such as ``"syntax"``, ``"type"``, or ``"style"``.
        """
        if error_code.startswith(("E9", "F")):
            return "syntax"
        if error_code.startswith("ANN"):
            return "type"
        return "style"

    def _generate_suggestion(self, error: dict[str, Any]) -> str:
        """Generate a human-friendly suggestion for resolving an error.

        Args:
            error: Error payload emitted by the linting tool.

        Returns:
            str: Suggestion text embedded in the Markdown report.
        """
        code = error.get("code", "")
        message = error.get("message", "")
        suggestions = {
            "E999": "Python構文エラー - 括弧、クォート、インデントを確認",
            "F401": "未使用インポート - 不要なimport文を削除",
            "ANN001": "型注釈不足 - 引数に型注釈を追加",
            "ANN201": "戻り値型注釈不足 - 戻り値の型注釈を追加",
        }
        return suggestions.get(code, f"エラーコード {code}: {message}")

    def _generate_suggestions_markdown(self, errors: list[dict], summary: dict) -> None:
        """Render the Markdown document consumed by Claude Code.

        Args:
            errors: Normalized error entries ready for presentation.
            summary: Aggregated counts grouped by error type.
        """
        content = f"# 🔧 リアルタイム監視システム - エラー修正提案\n\n## 📊 エラー概要\n\n- **総エラー数**: {summary['total_errors']}\n- **構文エラー**: {summary['syntax_errors']}\n- **型エラー**: {summary['type_errors']}\n- **スタイルエラー**: {summary['style_errors']}\n\n## 🎯 優先修正項目\n\n### 🚨 高優先度(構文エラー)\n"
        syntax_errors = [e for e in errors if e["error_type"] == "syntax"]
        if syntax_errors:
            for error in syntax_errors[:5]:
                content += f"\n#### {error['file_path']}:{error['line_number']}\n- **エラー**: `{error['error_code']}` - {error['message']}\n- **修正提案**: {error['suggestion']}\n"
        else:
            content += "\n✅ 構文エラーはありません\n"
        content += "\n### 📝 中優先度(型エラー)\n"
        type_errors = [e for e in errors if e["error_type"] == "type"]
        if type_errors:
            for error in type_errors[:5]:
                content += f"\n#### {error['file_path']}:{error['line_number']}\n- **エラー**: `{error['error_code']}` - {error['message']}\n- **修正提案**: {error['suggestion']}\n"
        else:
            content += "\n✅ 型エラーはありません\n"
        content += f"\n\n## 🤖 Claude Code活用提案\n\n### 修正コマンド例\n\n```bash\n# エラーファイル確認\ncat temp/claude_code_errors.json\n\n# 個別ファイル修正\n# (Claude Codeがこのマークダウンを読んで修正提案)\n```\n\n### 一括修正戦略\n\n1. **構文エラー優先**: 致命的エラーから修正\n2. **型注釈追加**: ANN001エラーの系統的修正\n3. **スタイル調整**: 最終的な品質向上\n\n## 🔄 更新日時\n\n{project_now().format_timestamp('%Y年%m月%d日 %H:%M:%S')}\n\n---\n\nこのファイルはリアルタイム監視システムが自動生成しています。\nClaude Codeでの修正作業にご活用ください。\n"
        with Path(self.suggestion_file).open("w", encoding="utf-8") as f:
            f.write(content)

    def get_claude_integration_status(self) -> dict[str, Any]:
        """Describe the on-disk status of Claude Code export artifacts.

        Returns:
            dict[str, Any]: Flags and paths that indicate export availability.
        """
        return {
            "error_file_exists": self.error_file.exists(),
            "suggestion_file_exists": self.suggestion_file.exists(),
            "error_file_path": str(self.error_file),
            "suggestion_file_path": str(self.suggestion_file),
            "last_updated": self._get_last_updated(),
        }

    def _get_last_updated(self) -> str | None:
        """Return the ISO timestamp for the most recent export.

        Returns:
            str | None: Timestamp string when the file exists, otherwise ``None``.
        """
        if self.error_file.exists():
            timestamp = self.error_file.stat().st_mtime
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        return None


async def export_current_errors_for_claude(project_root: Path) -> None:
    """Export current errors into Claude Code artifacts using defaults.

    Args:
        project_root: Root directory that contains the temporary export folder.
    """
    adapter = ClaudeCodeAdapter(project_root)
    from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

    ConsoleServiceAdapter()
    console.print("✅ Claude Code向けエラー情報を出力しました")
    console.print(f"   エラーファイル: {adapter.error_file}")
    console.print(f"   提案書: {adapter.suggestion_file}")
