# File: src/mcp_servers/noveler/server/ten_stage_tool_bindings.py
# Purpose: Provide reusable registration helpers for the ten-stage writing tools shared by
#          Noveler MCP servers, keeping server classes below the 300-line guideline.
# Context: Imported by JSONConversionServer and AsyncJSONConversionServer to bind
#          ten-stage MCP tools without duplicating logic.

"""Module: Ten-stage MCP tool bindings.

Purpose:
    Offer shared registration functions for the synchronous and asynchronous
    ten-stage writing tool suites so server classes remain focused on
    orchestration logic.

Side Effects:
    None at import time. Calling the registration functions mutates the
    provided server by binding decorated tool callables.
"""

from __future__ import annotations

from typing import Any, Protocol

__all__ = [
    "register_ten_stage_tools",
    "register_async_ten_stage_tools",
]


class _HasLogger(Protocol):
    """Minimal logging interface required by the registration helpers."""

    logger: Any


class _SyncTenStageCtx(_HasLogger, Protocol):
    """Context contract for synchronous ten-stage registration."""

    def _execute_ten_stage_step(
        self,
        stage: "TenStageExecutionStage",
        episode: int,
        session_id: str | None = None,
        project_root: str | None = None,
    ) -> str:
        """Execute a single ten-stage step and return a textual response."""


class _AsyncTenStageCtx(_HasLogger, Protocol):
    """Context contract for asynchronous ten-stage registration."""

    async def _execute_ten_stage_step_async(
        self,
        stage: "TenStageExecutionStage",
        episode: int,
        session_id: str | None = None,
        project_root: str | None = None,
    ) -> str:
        """Execute a single ten-stage step asynchronously and return text."""


def register_ten_stage_tools(server: Any, ctx: _SyncTenStageCtx) -> None:
    """Bind synchronous ten-stage writing tools to the given server.

    Purpose:
        Provide per-step MCP tool bindings that delegate execution to the
        host context while keeping the server class small.

    Args:
        server (Any): FastMCP-compatible server exposing a ``tool`` decorator.
        ctx (_SyncTenStageCtx): Host providing execution and logging helpers.

    Returns:
        None

    Side Effects:
        Registers synchronous ten-stage tools on ``server``.
    """

    def _import_ten_stage_modules() -> tuple[type | None, type | None]:
        """Import TenStage components lazily to avoid heavy startup costs."""

        try:
            from noveler.domain.value_objects.ten_stage_writing_execution import TenStageExecutionStage
            from noveler.infrastructure.services.ten_stage_session_manager import TenStageSessionManager
            return TenStageExecutionStage, TenStageSessionManager
        except ImportError as exc:  # pragma: no cover - defensive
            ctx.logger.warning("10段階システムモジュールのインポート失敗: %s", str(exc))
            return None, None

    TenStageExecutionStage, TenStageSessionManager = _import_ten_stage_modules()

    if not TenStageExecutionStage or not TenStageSessionManager:
        ctx.logger.warning("10段階システム機能は利用できません")
        return

    @server.tool(
        name="write_step_1",
        description="STEP1: プロットデータ準備 - 独立5分タイムアウト実行、セッションID生成",
    )
    def write_step_1(
        episode: int,
        project_root: str | None = None,
    ) -> str:
        """Execute stage 1 of the ten-stage workflow synchronously."""

        return ctx._execute_ten_stage_step(
            TenStageExecutionStage.PLOT_DATA_PREPARATION,
            episode,
            project_root=project_root,
        )

    @server.tool(
        name="write_step_2",
        description="STEP2: プロット分析設計 - 前段階のセッションIDを受け取り継続実行",
    )
    def write_step_2(
        episode: int,
        session_id: str,
        project_root: str | None = None,
    ) -> str:
        """Execute stage 2 of the ten-stage workflow synchronously."""

        return ctx._execute_ten_stage_step(
            TenStageExecutionStage.PLOT_ANALYSIS_DESIGN,
            episode,
            session_id,
            project_root,
        )

    @server.tool(
        name="write_step_3",
        description="STEP3: 感情関係性設計 - 独立タイムアウトでキャラクター感情設計",
    )
    def write_step_3(
        episode: int,
        session_id: str,
        project_root: str | None = None,
    ) -> str:
        """Execute stage 3 of the ten-stage workflow synchronously."""

        return ctx._execute_ten_stage_step(
            TenStageExecutionStage.EMOTIONAL_RELATIONSHIP_DESIGN,
            episode,
            session_id,
            project_root,
        )

    @server.tool(
        name="write_step_4",
        description="STEP4: ユーモア魅力設計 - 独立タイムアウトで魅力要素追加",
    )
    def write_step_4(
        episode: int,
        session_id: str,
        project_root: str | None = None,
    ) -> str:
        """Execute stage 4 of the ten-stage workflow synchronously."""

        return ctx._execute_ten_stage_step(
            TenStageExecutionStage.HUMOR_CHARM_DESIGN,
            episode,
            session_id,
            project_root,
        )

    @server.tool(
        name="write_step_5",
        description="STEP5: キャラ心理対話設計 - 独立タイムアウトで対話品質向上",
    )
    def write_step_5(
        episode: int,
        session_id: str,
        project_root: str | None = None,
    ) -> str:
        """Execute stage 5 of the ten-stage workflow synchronously."""

        return ctx._execute_ten_stage_step(
            TenStageExecutionStage.CHARACTER_PSYCHOLOGY_DIALOGUE_DESIGN,
            episode,
            session_id,
            project_root,
        )

    @server.tool(
        name="write_step_6",
        description="STEP6: 場面演出雰囲気設計 - 独立タイムアウトで演出強化",
    )
    def write_step_6(
        episode: int,
        session_id: str,
        project_root: str | None = None,
    ) -> str:
        """Execute stage 6 of the ten-stage workflow synchronously."""

        return ctx._execute_ten_stage_step(
            TenStageExecutionStage.SCENE_DIRECTION_ATMOSPHERE_DESIGN,
            episode,
            session_id,
            project_root,
        )

    @server.tool(
        name="write_step_7",
        description="STEP7: 論理整合性調整 - 独立タイムアウトで矛盾解消",
    )
    def write_step_7(
        episode: int,
        session_id: str,
        project_root: str | None = None,
    ) -> str:
        """Execute stage 7 of the ten-stage workflow synchronously."""

        return ctx._execute_ten_stage_step(
            TenStageExecutionStage.LOGIC_CONSISTENCY_ADJUSTMENT,
            episode,
            session_id,
            project_root,
        )

    @server.tool(
        name="write_step_8",
        description="STEP8: 原稿執筆 - 独立タイムアウトで初原稿生成",
    )
    def write_step_8(
        episode: int,
        session_id: str,
        project_root: str | None = None,
    ) -> str:
        """Execute stage 8 of the ten-stage workflow synchronously."""

        return ctx._execute_ten_stage_step(
            TenStageExecutionStage.MANUSCRIPT_WRITING,
            episode,
            session_id,
            project_root,
        )

    @server.tool(
        name="write_step_9",
        description="STEP9: 品質仕上げ - 独立タイムアウトで品質改善",
    )
    def write_step_9(
        episode: int,
        session_id: str,
        project_root: str | None = None,
    ) -> str:
        """Execute stage 9 of the ten-stage workflow synchronously."""

        return ctx._execute_ten_stage_step(
            TenStageExecutionStage.QUALITY_REFINEMENT,
            episode,
            session_id,
            project_root,
        )

    @server.tool(
        name="write_step_10",
        description="STEP10: 最終調整 - 独立タイムアウトで最終仕上げ",
    )
    def write_step_10(
        episode: int,
        session_id: str,
        project_root: str | None = None,
    ) -> str:
        """Execute stage 10 of the ten-stage workflow synchronously."""

        return ctx._execute_ten_stage_step(
            TenStageExecutionStage.FINAL_ADJUSTMENT,
            episode,
            session_id,
            project_root,
        )


def register_async_ten_stage_tools(server: Any, ctx: _AsyncTenStageCtx) -> None:
    """Bind asynchronous ten-stage writing tools to the given server.

    Purpose:
        Provide an async ``write_step_async`` entry point shared by both MCP
        server implementations.

    Args:
        server (Any): FastMCP-compatible server exposing a ``tool`` decorator.
        ctx (_AsyncTenStageCtx): Host providing async execution and logging.

    Returns:
        None

    Side Effects:
        Registers the async ten-stage tool on ``server``.
    """

    def _import_ten_stage_modules() -> tuple[type | None, type | None]:
        """Import TenStage components lazily to avoid heavy startup costs."""

        try:
            from noveler.domain.value_objects.ten_stage_writing_execution import TenStageExecutionStage
            from noveler.infrastructure.services.ten_stage_session_manager import TenStageSessionManager
            return TenStageExecutionStage, TenStageSessionManager
        except ImportError as exc:  # pragma: no cover - defensive
            ctx.logger.warning("10段階システムモジュールのインポート失敗: %s", str(exc))
            return None, None

    TenStageExecutionStage, TenStageSessionManager = _import_ten_stage_modules()

    if not TenStageExecutionStage or not TenStageSessionManager:
        ctx.logger.warning("10段階システム機能は利用できません")
        return

    @server.tool(
        name="write_step_async",
        description="10段階執筆ステップ非同期実行 - 任意ステップ番号対応",
    )
    async def write_step_async(
        step: int,
        episode: int,
        session_id: str | None = None,
        project_root: str | None = None,
    ) -> str:
        """Run a single step of the ten-stage flow asynchronously."""

        try:
            if not (1 <= step <= 10):
                return f"エラー: stepは1-10の範囲で指定してください（受信値: {step}）"

            if episode <= 0:
                return f"エラー: episodeは1以上の整数である必要があります（受信値: {episode}）"

            stage = TenStageExecutionStage.from_step_number(step)
            if not stage:
                return f"エラー: 無効なステップ番号: {step}"

            ctx.logger.info("非同期10段階実行開始: STEP%d, episode=%d", step, episode)
            result = await ctx._execute_ten_stage_step_async(
                stage,
                episode,
                session_id,
                project_root,
            )
            return f"{result}\n\n⚡ 非同期STEP{step}実行完了"
        except Exception as exc:  # pragma: no cover - defensive
            ctx.logger.exception("非同期10段階ステップエラー")
            return f"非同期STEP{step}エラー: {exc!s}"
