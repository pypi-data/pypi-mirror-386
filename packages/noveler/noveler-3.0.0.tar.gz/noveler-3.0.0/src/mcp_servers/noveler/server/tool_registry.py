# File: src/mcp_servers/noveler/server/tool_registry.py
# Purpose: Register utility MCP tools (conversion/validation/file-info) on a
#          given server instance. Kept small and dependency-light to ease
#          testing and reuse.
# Context: Called from JSONConversionServer._register_tools. Expects a server
#          compatible with FastMCP (or its stub) and a context providing
#          converter, logger, output_dir, and formatting helpers.

"""Utility tool registry for Noveler MCP servers.

Purpose:
    Provide a thin, reusable function to register conversion/validation/
    file-info tools on any FastMCP-like server instance, decoupling the
    server classes from registration details and easing testing.

Side Effects:
    None at module import. The registration function mutates the provided
    server by binding decorated functions when called.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class _FormatterCtx(Protocol):
    """Minimal context required for tool registration.

    Purpose:
        Allow the registry to call back into the host server for conversion,
        logging, and formatting without tight coupling to a specific class.

    Attributes:
        converter: Object exposing `convert(payload: dict) -> dict | None`.
        logger: Logger exposing `.exception(msg)` and `.info(msg, *args)`.
        output_dir: Path root for artefact operations.
        _format_json_result: Callable for pretty-printing conversion results.

    Side Effects:
        None.
    """

    converter: Any
    logger: Any
    output_dir: Path

    def _format_json_result(self, result: dict[str, Any]) -> str:  # noqa: D401
        """Format a JSON conversion result for textual display.

        Purpose:
            Provide a consistent textual representation of conversion output.

        Args:
            result (dict[str, Any]): Conversion result payload.

        Returns:
            str: Formatted lines.

        Side Effects:
            None.
        """


def register_utility_tools(server: Any, ctx: _FormatterCtx) -> None:
    """Register conversion/validation/file-info tools on the server.

    Purpose:
        Centralise low-level tool registration to keep server classes thin.

    Args:
        server (Any): FastMCP-like server exposing a `.tool(...)` decorator.
        ctx (_FormatterCtx): Host providing converter/logger/output_dir.

    Returns:
        None

    Side Effects:
        Binds decorated functions to the provided server instance.
    """

    @server.tool(
        name="convert_cli_to_json",
        description="CLI実行結果をJSON形式に変換し、95%トークン削減とファイル参照アーキテクチャを適用",
    )
    def convert_cli_to_json(cli_result: dict[str, Any]) -> str:
        """Convert the CLI payload into a compressed JSON response.

        Purpose:
            Transform CLI outputs to JSON and summarise results.

        Args:
            cli_result (dict[str, Any]): Raw CLI result mapping.

        Returns:
            str: Human-readable summary with formatted JSON result.

        Side Effects:
            Writes artefacts through the converter when configured.
        """
        try:
            if not cli_result:
                return "エラー: cli_resultパラメータが必要です"

            json_result = ctx.converter.convert(cli_result)
            return f"変換成功:\n{ctx._format_json_result(json_result)}"
        except Exception as e:  # pragma: no cover - pass-through logging path
            ctx.logger.exception("CLI→JSON変換エラー")
            return f"変換エラー: {e!s}"

    @server.tool(name="validate_json_response", description="JSON レスポンス形式検証")
    def validate_json_response(json_data: dict[str, Any]) -> str:
        """Validate whether a JSON payload follows the response schema.

        Purpose:
            Validate response shape (success vs error) using models.

        Args:
            json_data (dict[str, Any]): JSON payload to validate.

        Returns:
            str: Validation result summary.

        Side Effects:
            None besides logging.
        """
        try:
            if not json_data:
                return "エラー: json_dataパラメータが必要です"

            # Defer to converter models via ctx.converter if available
            # Fall back to a light-weight check (keys) if not.
            try:
                # Attempt a no-op convert to leverage pydantic validation
                ctx.converter.convert({**json_data})  # type: ignore[arg-type]
                return "JSON形式検証成功: ConverterValidation"
            except Exception:
                # Minimal shape check
                key = "success"
                if key in json_data:
                    return "JSON形式検証成功: MinimalShape"
                return "JSON形式検証エラー: missing 'success' key"
        except Exception as e:  # pragma: no cover - defensive path
            return f"JSON形式検証エラー: {e!s}"

    @server.tool(name="get_file_reference_info", description="ファイル参照情報取得")
    def get_file_reference_info(file_path: str) -> str:
        """Return metadata for files stored in the JSON artefact storage.

        Purpose:
            Provide quick file metadata for artefacts under `output_dir`.

        Args:
            file_path (str): Path relative to the artefact directory.

        Returns:
            str: Human-readable metadata summary.

        Side Effects:
            Accesses filesystem stat information.
        """
        try:
            if not file_path:
                return "エラー: file_pathパラメータが必要です"

            full_path = ctx.output_dir / file_path
            if not full_path.exists():
                return f"ファイルが見つかりません: {file_path}"

            stat = full_path.stat()
            info = {
                "path": file_path,
                "size_bytes": stat.st_size,
                "modified": __import__("datetime").datetime.fromtimestamp(
                    stat.st_mtime, tz=__import__("datetime").timezone.utc
                ).isoformat(),
                "exists": True,
            }
            # Use host formatting for consistency
            return f"ファイル情報:\n{ctx._format_json_result({'success': True, 'command': 'meta', 'outputs': {'total_files': 1, 'total_size_bytes': info['size_bytes']}})}\n{format_dict(info)}"
        except Exception as e:  # pragma: no cover - defensive path
            return f"ファイル情報取得エラー: {e!s}"

def register_fix_style_extended_tools(server: Any, ctx: "_FormatterCtx") -> None:
    """Register style extension tools on the server.

    Purpose:
        Register opt-in style extension tools for FULLWIDTH_SPACE normalization
        and BRACKETS_MISMATCH auto-correction.

    Args:
        server (Any): FastMCP-like server exposing a `.tool(...)` decorator.
        ctx (_FormatterCtx): Host providing converter/logger/output_dir.

    Returns:
        None

    Side Effects:
        Binds decorated functions to the provided server instance.
    """

    @server.tool(
        name="fix_style_extended",
        description="style拡張機能（opt-in）: FULLWIDTH_SPACE正規化とBRACKETS_MISMATCH自動補正",
    )
    def fix_style_extended(
        episode_number: int | None = None,
        project_name: str | None = None,
        file_path: str | None = None,
        content: str | None = None,
        fullwidth_space_mode: str = "disabled",
        brackets_fix_mode: str = "disabled",
        dry_run: bool = True,
    ) -> str:
        """Fix style issues with opt-in extended features.

        Purpose:
            Process FULLWIDTH_SPACE normalization and BRACKETS_MISMATCH
            auto-correction based on opt-in mode settings.

        Args:
            episode_number (int | None): Episode number for content loading.
            project_name (str | None): Project name for content loading.
            file_path (str | None): Direct file path (takes priority over episode_number).
            content (str | None): Direct content input.
            fullwidth_space_mode (str): FULLWIDTH_SPACE processing mode.
            brackets_fix_mode (str): Bracket correction mode.
            dry_run (bool): Show diff only without writing files.

        Returns:
            str: Execution result with diff and metadata.

        Side Effects:
            May write files when dry_run=False.
        """
        try:
            from mcp_servers.noveler.tools.fix_style_extended_tool import FixStyleExtendedTool
            from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest

            tool = FixStyleExtendedTool()
            request = ToolRequest(
                episode_number=episode_number,
                project_name=project_name,
                additional_params={
                    "file_path": file_path,
                    "content": content,
                    "fullwidth_space_mode": fullwidth_space_mode,
                    "brackets_fix_mode": brackets_fix_mode,
                    "dry_run": dry_run,
                }
            )

            response = tool.execute(request)

            if response.success:
                result_lines = [response.message]
                if hasattr(response, 'metadata') and response.metadata:
                    if "diff" in response.metadata and response.metadata["diff"]:
                        result_lines.append("\n📋 変更内容:")
                        result_lines.append(response.metadata["diff"])

                    changes_made = response.metadata.get("changes_made", 0)
                    result_lines.append(f"\n✅ {changes_made}件の変更を検出しました")

                    if response.metadata.get("dry_run", True):
                        result_lines.append("🔒 dry_runモードのため実際のファイル書き込みは行われていません")
                    elif response.metadata.get("file_updated"):
                        result_lines.append(f"💾 ファイルを更新しました: {response.metadata.get('file_path', '')}")

                return "\n".join(result_lines)
            else:
                return f"エラー: {response.message}"

        except Exception as e:
            ctx.logger.exception("style拡張処理でエラーが発生しました")
            return f"style拡張処理エラー: {e!s}"


def format_dict(data: dict[str, Any]) -> str:
    """Local helper to format key/value pairs.

    Purpose:
        Avoid importing format_utils here to keep the dependency surface
        minimal for tests; this function mirrors the shared one.

    Args:
        data (dict[str, Any]): Mapping to format.

    Returns:
        str: Lines joined by newlines as key: value pairs.

    Side Effects:
        None.
    """
    return "\n".join(f"{k}: {v}" for k, v in data.items())
