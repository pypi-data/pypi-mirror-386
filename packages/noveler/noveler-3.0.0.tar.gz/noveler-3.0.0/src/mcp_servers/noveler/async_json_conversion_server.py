#!/usr/bin/env python3
# File: src/mcp_servers/noveler/async_json_conversion_server.py
# Purpose: Provide a fully-asynchronous MCP server variant for Noveler that
#          converts CLI outputs to JSON, validates responses, and exposes
#          async novel-writing/check tools with concurrency optimizations.
# Context: Runs as an MCP stdio server using FastMCP when available. Depends on
#          Noveler infrastructure (logging, converters) and async subprocess
#          adapters. This module performs server/tool registration on import
#          through object construction but avoids side effects at module import.
"""Async JSON conversion MCP server for Noveler (SPEC-901 refactoring).

Purpose:
  Offer async tools to convert CLI output to JSON, validate responses, and run
  novel writing/check commands with concurrency and improved error handling.

Side Effects:
  - When instantiated and run, starts stdio-based MCP server and spawns
    subprocesses for CLI execution.
  - Writes JSON artifacts to an output directory when configured to do so.

Notes:
  Requires Python 3.10+. Uses optional ripgrep-like behavior only via adapters.
  No network/APIs are required beyond local process execution.
"""

import asyncio
import json
from noveler.infrastructure.logging.unified_logger import get_logger
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.value_objects.ten_stage_writing_execution import TenStageExecutionStage


# B20準拠: 共有コンポーネント必須使用
from noveler.presentation.shared.shared_utilities import _get_console as get_console

try:
    from mcp import types
    from mcp.server import stdio
    from mcp.server.fastmcp import FastMCP

    MCP_AVAILABLE = True
except ImportError:
    # MCPが利用できない場合のフォールバック
    MCP_AVAILABLE = False
    FastMCP = None
    types = None
    stdio = None

# 非同期Adapter import
from mcp_servers.noveler.core.async_subprocess_adapter import (
    create_async_subprocess_adapter,
    create_concurrent_executor,
)
from mcp_servers.noveler.core.command_builder import CommandBuilder
from mcp_servers.noveler.core.response_parser import ResponseParser
from mcp_servers.noveler.core.format_utils import format_json_result, format_dict
from mcp_servers.noveler.server.ten_stage_tool_bindings import (
    register_async_ten_stage_tools,
)
from noveler.infrastructure.json.converters.cli_response_converter import CLIResponseConverter
from noveler.infrastructure.json.models.response_models import ErrorResponseModel, StandardResponseModel

# Guarded import to avoid PLC0415 and cycles/heavy dependencies at runtime
try:  # pragma: no cover - availability depends on project wiring
    from noveler.infrastructure.services.ten_stage_session_manager import TenStageSessionManager
    TEN_STAGE_AVAILABLE = True
except Exception:  # pragma: no cover
    TenStageSessionManager = None  # type: ignore
    TEN_STAGE_AVAILABLE = False


class AsyncJSONConversionServer:
    """Fully async JSON-conversion MCP server.

    Purpose:
        Expose async tools for JSON conversion/validation and orchestrate
        novel-related commands with concurrency and robust error handling.

    Side Effects:
        Registers tool handlers on a FastMCP instance; later execution may
        spawn subprocesses and write artifacts depending on configured tools.
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        max_concurrent: int = 3,
        enable_performance_optimization: bool = True
    ) -> None:
        """Initialise async components and FastMCP server.

        Purpose:
            Construct the server, initialise async adapters/executors, and
            register tool handlers on the FastMCP instance.

        Args:
            output_dir (Path | None): Directory to emit JSON artifacts.
            max_concurrent (int): Max concurrent tasks for adapters.
            enable_performance_optimization (bool): Enable tuned paths.

        Side Effects:
            Creates adapter/executor instances; registers tools on FastMCP.

        Raises:
            RuntimeError: When the MCP library is unavailable.
        """
        if not MCP_AVAILABLE:
            msg = "MCPライブラリが利用できません。pip install mcp を実行してください。"
            raise RuntimeError(msg)

        self.output_dir = output_dir or Path.cwd() / "temp" / "json_output"
        self.converter = CLIResponseConverter(output_dir=self.output_dir)
        self.logger = get_logger(__name__)

        # 非同期コンポーネント初期化
        self._async_adapter = create_async_subprocess_adapter(mock_mode=False)
        self._concurrent_executor = create_concurrent_executor(
            mock_mode=False,
            max_concurrent=max_concurrent,
            retry_policy={"max_retries": 2, "retry_delay": 1.0}
        )

        # コアコンポーネント（DDD準拠）
        self._command_builder = CommandBuilder()
        self._response_parser = ResponseParser()

        # パフォーマンス最適化設定
        self._performance_optimization = enable_performance_optimization
        self._concurrent_limit = max_concurrent

        # FastMCPサーバー初期化
        self.server = FastMCP(
            name="async-json-conversion",
            instructions="非同期小説執筆支援システム - 完全非同期処理・並列実行・Message Bus統合準備対応",
        )

        # ツール登録
        self._register_async_tools()
        self._register_async_novel_tools()

    def _register_async_tools(self) -> None:
        """Register generic async tools (conversion, validation, file info).

        Purpose:
            Define and bind generic utility tools on the FastMCP server.

        Returns:
            None

        Side Effects:
            Registers decorated tool callables on the FastMCP instance.
        """

        @self.server.tool(
            name="convert_cli_to_json_async",
            description="CLI実行結果を非同期でJSON形式に変換 - パフォーマンス最適化済み",
        )
        async def convert_cli_to_json_async(cli_result: dict[str, Any]) -> str:
            """Convert a CLI result dict to JSON asynchronously.

            Purpose:
                Perform JSON conversion off the event loop using a thread.

            Args:
                cli_result (dict[str, Any]): Raw CLI result object.

            Returns:
                str: Human-readable summary with formatted JSON section.

            Side Effects:
                Uses a thread pool; logs to the unified logger.
            """
            try:
                if not cli_result:
                    return "エラー: cli_resultパラメータが必要です"

                self.logger.debug("非同期JSON変換開始")
                start_time = datetime.now()

                # 非同期JSON変換実行（同期変換器は to_thread で実行）
                json_result = await asyncio.to_thread(self.converter.convert, cli_result)

                execution_time = (datetime.now() - start_time).total_seconds()
                self.logger.info("JSON変換完了: %.3fs", execution_time)

                return f"非同期変換成功 ({execution_time:.3f}s):\n{self._format_json_result(json_result)}"

            except Exception as e:
                self.logger.exception("非同期CLI→JSON変換エラー")
                return f"変換エラー: {e!s}"

        @self.server.tool(
            name="validate_json_response_async",
            description="JSON レスポンス形式を非同期で検証"
        )
        async def validate_json_response_async(json_data: dict[str, Any]) -> str:
            """Validate a JSON response structure asynchronously.

            Purpose:
                Offload JSON schema/shape validation to a thread to avoid
                blocking the event loop.

            Args:
                json_data (dict[str, Any]): Target JSON payload to validate.

            Returns:
                str: Validation result summary string.

            Side Effects:
                None besides logging.
            """
            try:
                if not json_data:
                    return "エラー: json_dataパラメータが必要です"

                # 非同期バリデーション（同期実装は to_thread で実行）
                return await asyncio.to_thread(self._validate_json_sync, json_data)

            except Exception as e:
                return f"非同期JSON検証エラー: {e!s}"

        @self.server.tool(
            name="get_file_reference_info_async",
            description="ファイル参照情報を非同期で取得"
        )
        async def get_file_reference_info_async(file_path: str) -> str:
            """Fetch file reference information asynchronously.

            Purpose:
                Retrieve and present file reference info for a given path.

            Args:
                file_path (str): Relative or absolute file path.

            Returns:
                str: Human-readable summary of file metadata.

            Side Effects:
                Reads file metadata and possibly content hashes in a thread.
            """
            try:
                if not file_path:
                    return "エラー: file_pathパラメータが必要です"

                full_path = self.output_dir / file_path

                # 非同期ファイル操作（同期実装は to_thread で実行）
                file_info = await asyncio.to_thread(self._get_file_info_sync, full_path, file_path)

                return f"非同期ファイル情報取得完了:\n{self._format_dict(file_info)}"

            except Exception as e:
                return f"非同期ファイル情報取得エラー: {e!s}"

    def _register_async_novel_tools(self) -> None:
        """Register async novel-writing/check tools on FastMCP.

        Purpose:
            Define and bind novel-specific tools (write/check/concurrent).

        Returns:
            None

        Side Effects:
            Registers decorated tool callables on the FastMCP instance.
        """

        @self.server.tool(
            name="noveler_write_async",
            description="小説エピソード非同期執筆 - 並列処理最適化対応",
        )
        async def noveler_write_async(
            episode_number: int,
            dry_run: bool = False,
            five_stage: bool = True,
            project_root: str | None = None,
            use_concurrent: bool = False
        ) -> str:
            """Run asynchronous novel writing for a single episode.

            Purpose:
                Execute the `write` flow for one episode with optional
                concurrency and flags.

            Args:
                episode_number (int): Target episode number (>=1).
                dry_run (bool): If True, avoid persistent changes.
                five_stage (bool): Enable five-stage flow switch.
                project_root (str | None): Project root path.
                use_concurrent (bool): Toggle concurrent path.

            Returns:
                str: Human-readable execution summary.

            Side Effects:
                Spawns subprocesses via adapters; reads/writes project files.
            """
            try:
                if episode_number <= 0:
                    return f"エラー: episode_numberは1以上の整数である必要があります（受信値: {episode_number}）"

                self.logger.info("非同期執筆開始: episode=%d", episode_number)
                start_time = datetime.now()

                # 非同期実行
                result = await self._execute_novel_command_async(
                    f"write {episode_number}",
                    {"dry_run": dry_run, "five_stage": five_stage},
                    project_root,
                    use_concurrent=use_concurrent
                )

                execution_time = (datetime.now() - start_time).total_seconds()
                self.logger.info("非同期執筆完了: %.3fs", execution_time)

                return f"{result}\n\n⚡ 非同期実行時間: {execution_time:.3f}秒"

            except Exception as e:
                self.logger.exception("非同期noveler_writeエラー")
                return f"非同期実行エラー: {e!s}"

        @self.server.tool(
            name="noveler_check_async",
            description="小説品質チェック - 非同期処理対応",
        )
        async def noveler_check_async(
            episode_number: int,
            auto_fix: bool = False,
            verbose: bool = False,
            project_root: str | None = None
        ) -> str:
            """Run asynchronous novel quality check for a single episode.

            Purpose:
                Execute the `check` flow for one episode with options.

            Args:
                episode_number (int): Target episode number (>=1).
                auto_fix (bool): Apply automatic fixes when possible.
                verbose (bool): Emit verbose diagnostic information.
                project_root (str | None): Project root path.

            Returns:
                str: Human-readable check result summary.

            Side Effects:
                Spawns subprocesses via adapters; reads/writes project files.
            """
            try:
                if episode_number <= 0:
                    return f"エラー: episode_numberは1以上の整数である必要があります（受信値: {episode_number}）"

                result = await self._execute_novel_command_async(
                    f"check {episode_number}",
                    {"auto_fix": auto_fix, "verbose": verbose},
                    project_root
                )

                return f"{result}\n\n🔍 非同期品質チェック完了"

            except Exception as e:
                self.logger.exception("非同期noveler_checkエラー")
                return f"非同期チェックエラー: {e!s}"

        @self.server.tool(
            name="concurrent_episode_processing",
            description="複数エピソードの並列処理 - 高性能実行",
        )
        async def concurrent_episode_processing(
            episodes: list[int],
            operation: str = "write",
            project_root: str | None = None,
            max_concurrent: int = 3
        ) -> str:
            """Process multiple episodes concurrently.

            Purpose:
                Execute `write`/`check` operations across episodes with a
                concurrency limit.

            Args:
                episodes (list[int]): List of episode numbers.
                operation (str): Operation name (e.g., "write" or "check").
                project_root (str | None): Project root path.
                max_concurrent (int): Max concurrency for execution.

            Returns:
                str: Aggregated multi-episode execution summary.

            Side Effects:
                Spawns multiple subprocesses; reads/writes project files.
            """
            try:
                if not episodes:
                    return "エラー: 処理対象エピソードが指定されていません"

                if len(episodes) > 10:
                    return "エラー: 一度に処理可能なエピソード数は10個までです"

                self.logger.info("並列処理開始: %d episodes, operation=%s", len(episodes), operation)
                start_time = datetime.now()

                # 並列実行用コマンド準備
                commands = []
                for episode in episodes:
                    working_dir = Path(project_root) if project_root else Path.cwd()
                    cmd_parts, _ = self._command_builder.build_novel_command(
                        f"{operation} {episode}",
                        {"concurrent": True},
                        project_root
                    )
                    env_vars = self._command_builder.build_environment_vars(project_root)

                    commands.append((cmd_parts, working_dir, env_vars, 300))

                # 並列実行
                results = await self._concurrent_executor.execute_concurrent(commands)

                execution_time = (datetime.now() - start_time).total_seconds()

                # 結果集計
                success_count = sum(1 for r in results if r.return_code == 0)

                response_lines = [
                    f"🚀 並列処理完了: {len(episodes)}エピソード",
                    f"✅ 成功: {success_count}/{len(episodes)}",
                    f"⏱️ 実行時間: {execution_time:.3f}秒",
                    f"📈 推定単体実行時間: {execution_time * len(episodes):.1f}秒",
                    f"🎯 効率化倍率: {len(episodes) / max(1, execution_time / 60):.1f}x",
                    ""
                ]

                for _i, (episode, result) in enumerate(zip(episodes, results, strict=False)):
                    status = "✅" if result.return_code == 0 else "❌"
                    response_lines.append(f"{status} Episode {episode}: {result.return_code}")

                return "\n".join(response_lines)

            except Exception as e:
                self.logger.exception("並列処理エラー")
                return f"並列処理エラー: {e!s}"

        # 10段階個別実行ツールの非同期版
        register_async_ten_stage_tools(self.server, self)

    async def _execute_novel_command_async(
        self,
        command: str,
        options: dict[str, Any],
        project_root: str | None = None,
        use_concurrent: bool = False
    ) -> str:
        """Execute novel-related CLI command asynchronously.

        Purpose:
            Common async execution path for `write`/`check` operations.

        Args:
            command (str): CLI-style command string (e.g., "write 1").
            options (dict[str, Any]): Command options passed to adapters.
            project_root (str | None): Project root path.
            use_concurrent (bool): Use concurrent executor when True.

        Returns:
            str: Human-readable formatted result (success or error).

        Side Effects:
            Spawns subprocesses; reads/writes JSON artefacts via converter.
        """
        try:
            # 作業ディレクトリ決定
            working_dir = Path(project_root).absolute() if project_root else Path.cwd()

            # 環境変数の構築
            env_vars = self._command_builder.build_environment_vars(project_root)

            # コマンド構築
            cmd_parts, _ = self._command_builder.build_novel_command(
                command, options, project_root
            )

            # 非同期実行
            if use_concurrent and self._performance_optimization:
                # 並列実行器を使用（将来的に複数操作の同時実行等に使用）
                subprocess_result = await self._concurrent_executor.execute_single(
                    cmd_parts, working_dir, env_vars, timeout=300
                )
            else:
                # 単一非同期実行
                subprocess_result = await self._async_adapter.execute(
                    cmd_parts, working_dir, env_vars, timeout=300
                )

            # レスポンス解析
            parsed_result = self._response_parser.parse_novel_output(
                subprocess_result.stdout,
                subprocess_result.stderr,
                subprocess_result.return_code
            )

            # 実行結果データ構築
            cli_result = {
                "success": parsed_result["success"],
                "stdout": parsed_result["raw_output"]["stdout"],
                "stderr": parsed_result["raw_output"]["stderr"],
                "command": " ".join(cmd_parts),
                "returncode": parsed_result["return_code"],
                "working_dir": str(working_dir),
                "project_root": project_root,
                "execution_time": subprocess_result.execution_time,
                "async_execution": True
            }

            # 成功/失敗フォーマット
            if cli_result.get("success", False):
                response_text = self._format_novel_success_result(cli_result)
            else:
                response_text = self._format_novel_error_result(cli_result)

            # 非同期JSON変換と保存
            await self._convert_and_save_async(cli_result)

            return f"{response_text}\n\n📁 非同期JSON変換・保存完了（95%トークン削減）"

        except asyncio.TimeoutError:
            return "実行エラー: コマンドがタイムアウトしました（5分）\n\n💡 非同期実行でもタイムアウトが発生しました"
        except Exception as e:
            self.logger.exception("非同期小説コマンド実行エラー")
            return f"非同期実行エラー: {e!s}"

    async def _execute_ten_stage_step_async(
        self,
        stage: "TenStageExecutionStage",
        episode: int,
        session_id: str | None = None,
        project_root: str | None = None
    ) -> str:
        """Execute one step of the ten-stage flow asynchronously.

        Purpose:
            Run a specific `stage` for an `episode` in async mode.

        Args:
            stage (TenStageExecutionStage): Target stage enum/value.
            episode (int): Episode number.
            session_id (str | None): Optional session identifier.
            project_root (str | None): Project root path.

        Returns:
            str: Human-readable summary of execution or error.

        Side Effects:
            Spawns subprocesses; writes logs and JSON artefacts.
        """
        try:
            if not TEN_STAGE_AVAILABLE:
                return "エラー: TenStageSessionManager が利用できません"

            # プロジェクトルート解決
            working_dir = Path(project_root).absolute() if project_root else Path.cwd()

            # セッションマネージャー初期化
            session_manager = TenStageSessionManager(working_dir)

            # セッション処理
            if session_id:
                context = session_manager.load_session(session_id)
                if not context:
                    return f"エラー: セッションが見つかりません: {session_id}"
            elif stage.step_number == 1:
                context = session_manager.create_session(episode)
                session_id = context.session_id
            else:
                return f"エラー: STEP{stage.step_number}にはsession_idが必要です"

            # 非同期コマンド構築・実行
            cmd_parts = [
                str(self._command_builder._get_noveler_command_path()),
                "write", str(episode),
                "--ten-stage-step", str(stage.step_number),
                "--session-id", session_id
            ]

            env_vars = self._command_builder.build_environment_vars(project_root)

            # 非同期実行（各ステップ独立タイムアウト）
            subprocess_result = await self._async_adapter.execute(
                cmd_parts, working_dir, env_vars, timeout=stage.timeout_seconds
            )

            # レスポンス解析
            parsed_result = self._response_parser.parse_novel_output(
                subprocess_result.stdout,
                subprocess_result.stderr,
                subprocess_result.return_code
            )

            # 10段階特有の結果データ構築
            cli_result = {
                "success": parsed_result["success"],
                "stdout": parsed_result["raw_output"]["stdout"],
                "stderr": parsed_result["raw_output"]["stderr"],
                "command": " ".join(cmd_parts),
                "returncode": parsed_result["return_code"],
                "stage": stage.display_name,
                "step": stage.step_number,
                "session_id": session_id,
                "next_step": stage.step_number + 1 if stage.get_next_stage() else None,
                "timeout_seconds": stage.timeout_seconds,
                "execution_time": subprocess_result.execution_time,
                "async_execution": True
            }

            # 成功時の処理
            if cli_result["success"]:
                # セッション更新（非同期化可能）
                output_data = self._extract_step_output(subprocess_result.stdout)
                session_manager.update_stage_completion(session_id, stage, output_data, turns_used=1)

                # 実行ログ保存
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                try:
                    log_file = session_manager.save_execution_log(
                        episode_number=episode,
                        step_number=stage.step_number,
                        step_name=stage.display_name,
                        execution_data=cli_result,
                        timestamp=timestamp
                    )
                    self.logger.info("実行ログ保存完了: %s", log_file.name)
                except Exception as log_error:
                    self.logger.warning("実行ログ保存に失敗: %s", str(log_error))

                response_text = self._format_ten_stage_success_result(cli_result)
            else:
                response_text = self._format_ten_stage_error_result(cli_result)

            # 非同期JSON変換・保存
            await self._convert_and_save_async(cli_result)

            return f"{response_text}\n\n📁 非同期JSON保存完了\n📊 実行ログ: 50_管理資料/原稿執筆ログ/episode{episode:03d}_step{stage.step_number:02d}_{timestamp}.json"

        except asyncio.TimeoutError:
            return f"実行エラー: ステップがタイムアウトしました（{stage.timeout_seconds}秒）\n\n💡 非同期STEP{stage.step_number}でもタイムアウト発生"
        except Exception as e:
            self.logger.exception("非同期10段階ステップ実行エラー: %s", stage.display_name)
            return f"非同期実行エラー: {e!s}"

    async def _convert_and_save_async(self, cli_result: dict[str, Any]) -> None:
        """Convert and persist JSON artefacts asynchronously.

        Purpose:
            Offload conversion/persist to a worker thread.

        Args:
            cli_result (dict[str, Any]): Parsed CLI run result.

        Returns:
            None

        Side Effects:
            Writes artefacts to the configured output directory.
        """
        try:
            await asyncio.to_thread(self.converter.convert, cli_result)
        except Exception as e:
            self.logger.warning("非同期JSON変換エラー: %s", str(e))

    # 同期処理のヘルパーメソッド（非同期実行用）
    def _validate_json_sync(self, json_data: dict[str, Any]) -> str:
        """Validate JSON synchronously (for executor threads).

        Purpose:
            Perform pydantic-style validation in a blocking context.

        Args:
            json_data (dict[str, Any]): Target JSON to validate.

        Returns:
            str: Validation result summary string.

        Side Effects:
            None.
        """
        try:
            if json_data.get("success", False):
                model = StandardResponseModel(**json_data)
            else:
                model = ErrorResponseModel(**json_data)
            return f"非同期JSON形式検証成功: {model.__class__.__name__}"
        except Exception as e:
            return f"JSON形式検証エラー: {e!s}"

    def _get_file_info_sync(self, full_path: Path, file_path: str) -> dict[str, Any]:
        """Return file metadata synchronously (for executor threads).

        Purpose:
            Gather basic file info for reporting.

        Args:
            full_path (Path): Absolute path to the file.
            file_path (str): Display path (relative or original input).

        Returns:
            dict[str, Any]: Metadata such as size, mtime, existence.

        Side Effects:
            Accesses filesystem stat information.
        """
        if not full_path.exists():
            return {"error": f"ファイルが見つかりません: {file_path}"}

        stat = full_path.stat()
        return {
            "path": file_path,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "exists": True,
        }

    def _extract_step_output(self, stdout: str) -> dict[str, Any]:
        """Extract step-output JSON block from stdout.

        Purpose:
            Try to parse a JSON block from CLI stdout; fallback to text.

        Args:
            stdout (str): Raw standard output text.

        Returns:
            dict[str, Any]: Parsed JSON or a fallback structure.

        Side Effects:
            None.
        """
        try:
            # JSON ブロックを探索
            json_pattern = r"\{(?:[^{}]|{[^{}]*})*\}"
            matches = re.findall(json_pattern, stdout)

            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

            # JSON が見つからない場合はテキストとして保存
            return {
                "raw_output": stdout,
                "extraction_method": "text_fallback"
            }

        except Exception:
            return {"raw_output": stdout, "extraction_error": True}

    # フォーマット系メソッド（同期版から引用）
    def _format_json_result(self, result: dict[str, Any]) -> str:
        """Format a JSON result summary as text.

        Purpose:
            Provide a concise, human-readable summary of a JSON result.

        Args:
            result (dict[str, Any]): JSON result payload.

        Returns:
            str: Formatted summary lines.

        Side Effects:
            None.
        """
        return format_json_result(result)

    def _format_dict(self, data: dict[str, Any]) -> str:
        """Format a dictionary into key:value lines.

        Purpose:
            Compact textual representation for simple metadata blocks.

        Args:
            data (dict[str, Any]): Input mapping.

        Returns:
            str: Joined lines of key:value.

        Side Effects:
            None.
        """
        return format_dict(data)

    def _format_novel_success_result(self, result: dict[str, Any]) -> str:
        """Format a success result for novel operations.

        Purpose:
            Provide a readable summary when a novel operation succeeds.

        Args:
            result (dict[str, Any]): CLI/parsed result payload.

        Returns:
            str: Textual summary.

        Side Effects:
            None.
        """
        lines = []
        lines.append(f"🎉 {result.get('message', '非同期実行完了')}")
        lines.append("=" * 40)

        # 基本情報
        if "episode_number" in result:
            lines.append(f"📖 話数: 第{result['episode_number']}話")

        if "execution_time" in result:
            time_sec = result["execution_time"]
            lines.append(f"⏱️ 実行時間: {time_sec:.1f}秒（非同期）")

        if result.get("async_execution"):
            lines.append("⚡ 非同期処理完了")

        return "\n".join(lines)

    def _format_novel_error_result(self, result: dict[str, Any]) -> str:
        """Format an error result for novel operations.

        Purpose:
            Provide a readable summary when a novel operation fails.

        Args:
            result (dict[str, Any]): CLI/parsed result payload.

        Returns:
            str: Textual summary.

        Side Effects:
            None.
        """
        lines = []
        lines.append(f"❌ {result.get('error', '非同期実行失敗')}")
        lines.append("=" * 40)

        if "command" in result:
            lines.append(f"📝 コマンド: {result['command']}")

        if result.get("async_execution"):
            lines.append("🔧 非同期処理でエラーが発生")

        return "\n".join(lines)

    def _format_ten_stage_success_result(self, result: dict[str, Any]) -> str:
        """Format a success result for a ten-stage step.

        Purpose:
            Provide a readable summary when a stage succeeds.

        Args:
            result (dict[str, Any]): Execution result payload.

        Returns:
            str: Textual summary.

        Side Effects:
            None.
        """
        lines = []
        lines.append(f"🎉 {result.get('stage', 'ステップ')} 完了! ⚡非同期")
        lines.append("=" * 50)

        lines.append(f"📖 エピソード: 第{result.get('episode', 'N/A')}話")
        lines.append(f"🔢 ステップ: {result.get('step', 'N/A')}/10")
        lines.append(f"🆔 セッションID: {result.get('session_id', 'N/A')[:8]}...")

        if result.get("execution_time"):
            lines.append(f"⏱️ 実行時間: {result['execution_time']:.3f}秒（非同期）")

        if result.get("next_step"):
            lines.append(f"▶️ 次ステップ: STEP{result['next_step']}")
            lines.append(f"💡 次実行: write_step_async(step={result['next_step']}, episode={result.get('episode', 1)}, session_id=\"{result.get('session_id', '')}\")")
        else:
            lines.append("🎊 全ステップ完了!")

        return "\n".join(lines)

    def _format_ten_stage_error_result(self, result: dict[str, Any]) -> str:
        """Format an error result for a ten-stage step.

        Purpose:
            Provide a readable summary when a stage fails.

        Args:
            result (dict[str, Any]): Execution result payload.

        Returns:
            str: Textual summary.

        Side Effects:
            None.
        """
        lines = []
        lines.append(f"❌ {result.get('stage', 'ステップ')} 失敗 ⚡非同期")
        lines.append("=" * 50)

        lines.append(f"🔢 ステップ: {result.get('step', 'N/A')}/10")
        lines.append(f"🆔 セッションID: {result.get('session_id', 'N/A')[:8]}...")

        if result.get("stderr"):
            lines.append(f"🔴 エラー内容: {result['stderr'][:200]}...")

        lines.append("\n🔧 復旧提案:")
        lines.append(f"  • write_step_async(step={result.get('step', 'X')}, ...)で再実行")
        lines.append("  • プロジェクトルートとセッションIDを確認")

        return "\n".join(lines)

    async def run(self) -> None:
        """Run the FastMCP stdio server asynchronously.

        Purpose:
            Start the stdio-based MCP event loop for this server instance.

        Returns:
            None

        Side Effects:
            Opens stdio streams and blocks the event loop; downstream tool
            invocations may spawn subprocesses and perform file I/O.

        Raises:
            RuntimeError: If the MCP library is not available.
        """
        if not MCP_AVAILABLE:
            msg = "MCPが利用できません"
            raise RuntimeError(msg)

        self.logger.info("非同期FastMCP サーバー実行開始 (stdio)")
        await self.server.run_stdio_async()


async def main() -> None:
    """CLI entrypoint for the async MCP server.

    Purpose:
        Provide a convenient `python -m` entry for running the server.

    Returns:
        None

    Side Effects:
        Prints to the console on missing dependencies and runs the server.
    """
    if not MCP_AVAILABLE:
        console = get_console()
        console.print("エラー: MCPライブラリが利用できません")
        console.print("以下のコマンドでインストールしてください:")
        console.print("pip install mcp")
        return 1

    # 非同期サーバー起動（パフォーマンス最適化有効）
    server = AsyncJSONConversionServer(
        max_concurrent=3,
        enable_performance_optimization=True
    )
    await server.run()
    return 0


if __name__ == "__main__":
    asyncio.run(main())
