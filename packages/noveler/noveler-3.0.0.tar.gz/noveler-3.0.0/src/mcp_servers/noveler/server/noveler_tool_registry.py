# File: src/mcp_servers/noveler/server/noveler_tool_registry.py
# Purpose: Register individual Noveler tools (write/check/plot/complete) on a
#          FastMCP-like server instance, keeping server classes thin.
# Context: Called from JSONConversionServer._register_individual_novel_tools.
#          Expects a context (ctx) that provides `_execute_novel_command` and
#          optionally `_handle_write_via_bus_sync` for message-bus flows.

"""Module: Noveler tool registry (write/check/plot/complete).

Purpose:
    Provide a function that registers the primary Noveler tools on a
    FastMCP-like server while keeping server classes small and testable.

Side Effects:
    None at import; when invoked, binds tool functions to the given server.
"""

from __future__ import annotations

from typing import Any, Protocol


class _NovelerCtx(Protocol):
    """Minimal context required to register Noveler tools.

    Purpose:
        Allow the registry to call back into the host server for command
        execution without a hard dependency on the concrete class.

    Methods:
        _execute_novel_command(command, options, project_root) -> str
        _handle_write_via_bus_sync(episode_number) -> str (optional)

    Side Effects:
        None (delegated to the host methods).
    """

    def _execute_novel_command(self, command: str, options: dict[str, Any], project_root: str | None = None) -> str:  # noqa: D401
        """Execute a Noveler CLI command via the MCP adapter.

        Purpose:
            Bridge tool calls to the host's execution pipeline.

        Args:
            command (str): Command string forwarded to the adapter.
            options (dict[str, Any]): Execution options.
            project_root (str | None): Optional project root override.

        Returns:
            str: Human-readable execution summary.

        Side Effects:
            Depends on host implementation; may spawn subprocesses and write artefacts.
        """

    def _handle_write_via_bus_sync(self, episode_number: int) -> str:  # noqa: D401
        """Optionally execute write via message bus in a sync context.

        Purpose:
            Allow synchronous wrapper around async message bus execution.

        Args:
            episode_number (int): Target episode number.

        Returns:
            str: Human-readable execution summary.

        Side Effects:
            Depends on host implementation; may emit domain events.
        """

    def _handle_check_via_bus_sync(self, episode_number: int, auto_fix: bool = False) -> str:
        """Execute quality check via message bus in a sync context.

        Purpose:
            Allow synchronous wrapper around async message bus execution for quality checks.

        Args:
            episode_number (int): Target episode number.
            auto_fix (bool): Apply automatic fixes where supported.

        Returns:
            str: Human-readable execution summary.

        Side Effects:
            Emits quality check commands and events via MessageBus.
        """
        import asyncio
        from noveler.application.simple_message_bus import MessageBus, BusConfig
        from noveler.application.uow import InMemoryUnitOfWork
        from noveler.application.idempotency import InMemoryIdempotencyStore
        from noveler.application.bus_handlers import register_handlers

        async def _async_check():
            # Create MessageBus with minimal configuration
            config = BusConfig(max_retries=2)
            dummy_repo = None  # 簡易実装用
            uow_factory = lambda: InMemoryUnitOfWork(episode_repo=dummy_repo)
            idempotency_store = InMemoryIdempotencyStore()

            bus = MessageBus(
                config=config,
                uow_factory=uow_factory,
                idempotency_store=idempotency_store,
                dispatch_inline=True  # MCP環境では同期処理
            )

            # Register handlers
            register_handlers(bus)

            try:
                # Execute quality check command
                result = await bus.handle_command("check_quality", {
                    "content": f"Episode {episode_number} content placeholder",
                    "check_types": ["grammar", "readability", "rhythm"],
                    "target_score": 80.0,
                    "episode_number": episode_number,
                    "auto_fix": auto_fix
                })

                if result.get("success"):
                    score = result.get("score", 0)
                    passed = result.get("passed", False)
                    status = "合格" if passed else "要改善"
                    return f"品質チェック完了 - Episode {episode_number}: スコア {score:.1f} ({status})"
                else:
                    error = result.get("error", "不明なエラー")
                    return f"品質チェック失敗 - Episode {episode_number}: {error}"

            except Exception as e:
                return f"MessageBus経由品質チェックエラー: {e}"

        try:
            # Run async function in sync context
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _async_check())
                    return future.result(timeout=30)  # 30秒タイムアウト
            return loop.run_until_complete(_async_check())
        except Exception as e:
            return f"非同期実行エラー: {e}"

    def _handle_status_command(self, project_root: str | None = None) -> str:  # noqa: D401
        """Return the project status summary consumed by the status tool."""


def register_individual_noveler_tools(server: Any, ctx: _NovelerCtx) -> None:
    """Register individual Noveler tools on the given server.

    Purpose:
        Define and bind the primary tools: noveler_write/check/plot/complete.

    Args:
        server (Any): FastMCP-like server exposing a `.tool(...)` decorator.
        ctx (_NovelerCtx): Host providing execution helpers.

    Returns:
        None

    Side Effects:
        Binds decorated functions to `server`.
    """

    @server.tool(
        name="status",
        description="プロジェクト状況確認 - 執筆済み原稿一覧と進捗情報を表示",
    )
    def status(project_root: str | None = None) -> str:
        """Expose the project status summary via the MCP registry."""
        try:
            return ctx._handle_status_command(project_root)
        except Exception as exc:  # pragma: no cover - defensive path
            return f"状況確認エラー: {exc!s}"

    @server.tool(
        name="noveler_write",
        description="小説エピソード執筆 - 指定話数の原稿を生成",
    )
    def noveler_write(
        episode_number: int,
        dry_run: bool = False,
        five_stage: bool = True,
        project_root: str | None = None
    ) -> str:
        """Invoke the ``noveler write`` flow and return the textual reply.

        Purpose:
            High-level tool wrapper for the writer flow.

        Args:
            episode_number (int): Episode number that should be generated.
            dry_run (bool): When ``True`` skip writing files.
            five_stage (bool): Whether to enable the five stage shortcut.
            project_root (str | None): Optional project root override.

        Returns:
            str: Formatted textual response describing the execution outcome.

        Side Effects:
            Delegated to ctx._execute_novel_command or ctx._handle_write_via_bus_sync.
        """
        try:
            if episode_number <= 0:
                return "エラー: episode_numberは1以上の整数である必要があります"
            command = f"write {episode_number}"
            options = {"dry_run": dry_run, "five_stage": five_stage}
            if hasattr(ctx, "_use_message_bus") and getattr(ctx, "_use_message_bus", False):  # type: ignore[attr-defined]
                # type: ignore[call-arg] – optional on protocol
                return ctx._handle_write_via_bus_sync(episode_number)  # type: ignore[attr-defined]
            return ctx._execute_novel_command(command, options, project_root)
        except Exception as e:  # pragma: no cover - defensive path
            return f"実行エラー: {e!s}"

    @server.tool(
        name="noveler_check",
        description="小説品質チェック - 指定話数の品質検証と修正提案",
    )
    def noveler_check(
        episode_number: int,
        auto_fix: bool = False,
        verbose: bool = False,
        project_root: str | None = None
    ) -> str:
        """Run the ``noveler check`` workflow and return the outcome text.

        Purpose:
            High-level tool wrapper for the quality check flow.

        Args:
            episode_number (int): Episode number to analyse.
            auto_fix (bool): Apply automatic fixes where supported.
            verbose (bool): Emit verbose diagnostics when True.
            project_root (str | None): Optional project root.

        Returns:
            str: Human-readable execution summary.

        Side Effects:
            Delegated to ctx._execute_novel_command.
        """
        try:
            if episode_number <= 0:
                return "エラー: episode_numberは1以上の整数である必要があります"

            # Check for MessageBus routing option
            if hasattr(ctx, "_use_message_bus") and getattr(ctx, "_use_message_bus", False):  # type: ignore[attr-defined]
                # Use MessageBus for quality check
                return ctx._handle_check_via_bus_sync(episode_number, auto_fix)  # type: ignore[attr-defined]

            # Default CLI command execution
            command = f"check {episode_number}"
            options = {"auto_fix": auto_fix, "verbose": verbose}
            return ctx._execute_novel_command(command, options, project_root)
        except Exception as e:  # pragma: no cover
            return f"実行エラー: {e!s}"

    @server.tool(
        name="noveler_plot",
        description="小説プロット生成 - 指定話数のプロット作成",
    )
    def noveler_plot(
        episode_number: int,
        regenerate: bool = False,
        project_root: str | None = None
    ) -> str:
        """Execute the ``noveler plot`` command and return its response.

        Purpose:
            High-level tool wrapper for the plot generation flow.

        Args:
            episode_number (int): Episode number to generate plot for.
            regenerate (bool): Force regeneration when True.
            project_root (str | None): Optional project root.

        Returns:
            str: Human-readable execution summary.

        Side Effects:
            Delegated to ctx._execute_novel_command.
        """
        try:
            if episode_number <= 0:
                return "エラー: episode_numberは1以上の整数である必要があります"
            command = f"plot {episode_number}"
            options = {"regenerate": regenerate}
            return ctx._execute_novel_command(command, options, project_root)
        except Exception as e:  # pragma: no cover
            return f"実行エラー: {e!s}"

    @server.tool(
        name="noveler_complete",
        description="小説完成処理 - 指定話数の最終化と投稿準備",
    )
    def noveler_complete(
        episode_number: int,
        auto_publish: bool = False,
        project_root: str | None = None
    ) -> str:
        """Execute the ``noveler complete`` workflow and return the output.

        Purpose:
            High-level tool wrapper for the completion/publish flow.

        Args:
            episode_number (int): Episode number to finalise.
            auto_publish (bool): Trigger auto-publish flow when True.
            project_root (str | None): Optional project root.

        Returns:
            str: Human-readable execution summary.

        Side Effects:
            Delegated to ctx._execute_novel_command.
        """
        try:
            if episode_number <= 0:
                return "エラー: episode_numberは1以上の整数である必要があります"
            command = f"complete {episode_number}"
            options = {"auto_publish": auto_publish}
            return ctx._execute_novel_command(command, options, project_root)
        except Exception as e:  # pragma: no cover
            return f"実行エラー: {e!s}"
