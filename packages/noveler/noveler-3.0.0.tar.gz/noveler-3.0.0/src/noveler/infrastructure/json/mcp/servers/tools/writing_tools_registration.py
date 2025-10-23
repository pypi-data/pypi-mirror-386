"""Register writing-related MCP tools (drafting, workflows, Claude integration)."""

from typing import Any

from noveler.infrastructure.json.mcp.servers.tools.tool_registration_system import ToolRegistrationMixin


class WritingToolsRegistration(ToolRegistrationMixin):
    """Register writing-oriented MCP tools."""

    def register_tools(self) -> None:
        """Register the writing tool collections."""
        self._register_write_tools()
        self._register_claude_write_tools()
        self._register_18step_writing_tools()
        self._register_staged_writing_tools()

    def _register_write_tools(self) -> None:
        """Register basic file writing utilities."""

        @self.server.tool("write", "ファイルへの書き込み（プロジェクトルート相対パス）")
        async def write_file(relative_path: str, content: str) -> dict[str, Any]:
            """Write file contents relative to the project root."""
            return await self._handle_write_file(relative_path, content)

    def _register_claude_write_tools(self) -> None:
        """Register Claude-assisted writing tools."""

        @self.server.tool("write_with_claude", "Claude Code実行前提：プロット→原稿変換実行")
        async def write_with_claude(episode_number: int, dry_run: bool = False) -> dict[str, Any]:
            """Create manuscripts via Claude-assisted workflows."""
            return await self._handle_claude_write(episode_number, dry_run)

        @self.server.tool("write_manuscript_draft", "原稿下書き作成（プロット解析付き）")
        async def write_manuscript_draft(
            episode_number: int,
            plot_analysis: dict[str, Any] | None = None,
            writing_settings: dict[str, Any] | None = None
        ) -> dict[str, Any]:
            """Generate manuscript drafts using plot analysis."""
            return await self._handle_manuscript_draft(episode_number, plot_analysis, writing_settings)

    def _register_18step_writing_tools(self) -> None:
        """Register 18-step writing workflow tools."""

        @self.server.tool("get_writing_tasks", "18ステップ執筆システムのタスクリスト取得")
        async def get_writing_tasks(episode_number: int, project_root: str | None = None) -> dict[str, Any]:
            """Return the 18-step writing task list."""
            return await self._handle_get_writing_tasks(episode_number, project_root)

        @self.server.tool("execute_writing_step", "18ステップ執筆システムの特定ステップ実行")
        async def execute_writing_step(
            episode_number: int,
            step_id: float,
            dry_run: bool = False,
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Execute a single step of the 18-step workflow."""
            return await self._handle_execute_writing_step(episode_number, step_id, dry_run, project_root)

        @self.server.tool("get_task_status", "現在の執筆タスクの進捗状況と状態を確認")
        async def get_task_status(episode_number: int, project_root: str | None = None) -> dict[str, Any]:
            """Return the current writing task status."""
            return await self._handle_get_task_status(episode_number, project_root)

        # バッチ処理ツール
        @self.server.tool("create_batch_job", "バッチ処理ジョブ作成")
        async def create_batch_job(
            episode_numbers: list[int],
            step_ranges: list[dict[str, Any]],
            job_name: str = "batch_writing_job"
        ) -> dict[str, Any]:
            """Create a batch writing job."""
            return await self._handle_create_batch_job(episode_numbers, step_ranges, job_name)

        @self.server.tool("execute_batch_job", "バッチ処理ジョブ実行")
        async def execute_batch_job(job_id: str, dry_run: bool = False) -> dict[str, Any]:
            """Execute the specified batch writing job."""
            return await self._handle_execute_batch_job(job_id, dry_run)

        @self.server.tool("get_batch_status", "バッチ処理状態取得")
        async def get_batch_status(job_id: str) -> dict[str, Any]:
            """Return the status of a batch writing job."""
            return await self._handle_get_batch_status(job_id)

    def _register_staged_writing_tools(self) -> None:
        """Register staged writing helper tools."""

        @self.server.tool("analyze_episode_quality", "エピソード品質分析")
        async def analyze_episode_quality(
            episode_number: int,
            analysis_type: str = "comprehensive",
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Analyse episode quality metrics."""
            return await self._handle_analyze_episode_quality(episode_number, analysis_type, project_root)

        @self.server.tool("get_progress_display", "執筆進捗表示取得")
        async def get_progress_display(project_root: str | None = None) -> dict[str, Any]:
            """Return progress display data."""
            return await self._handle_get_progress_display(project_root)

        @self.server.tool("export_ui_reports", "UI向けレポート出力")
        async def export_ui_reports(
            report_types: list[str],
            output_format: str = "json",
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Export UI-friendly reports."""
            return await self._handle_export_ui_reports(report_types, output_format, project_root)

    # 実装メソッド（派生クラスで実装）
    async def _handle_write_file(self, relative_path: str, content: str) -> dict[str, Any]:
        """Handle file writing requests."""
        raise NotImplementedError

    async def _handle_claude_write(self, episode_number: int, dry_run: bool) -> dict[str, Any]:
        """Handle Claude-assisted writing requests."""
        raise NotImplementedError

    async def _handle_manuscript_draft(
        self,
        episode_number: int,
        plot_analysis: dict[str, Any] | None,
        writing_settings: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Handle manuscript draft generation."""
        raise NotImplementedError

    async def _handle_get_writing_tasks(self, episode_number: int, project_root: str | None) -> dict[str, Any]:
        """Handle retrieval of the 18-step task list."""
        raise NotImplementedError

    async def _handle_execute_writing_step(
        self,
        episode_number: int,
        step_id: float,
        dry_run: bool,
        project_root: str | None
    ) -> dict[str, Any]:
        """Handle execution of a single 18-step workflow stage."""
        raise NotImplementedError

    async def _handle_get_task_status(self, episode_number: int, project_root: str | None) -> dict[str, Any]:
        """Handle writing task status queries."""
        raise NotImplementedError

    async def _handle_create_batch_job(
        self,
        episode_numbers: list[int],
        step_ranges: list[dict[str, Any]],
        job_name: str
    ) -> dict[str, Any]:
        """Handle batch job creation."""
        raise NotImplementedError

    async def _handle_execute_batch_job(self, job_id: str, dry_run: bool) -> dict[str, Any]:
        """Handle batch job execution."""
        raise NotImplementedError

    async def _handle_get_batch_status(self, job_id: str) -> dict[str, Any]:
        """Handle batch status queries."""
        raise NotImplementedError

    async def _handle_analyze_episode_quality(
        self,
        episode_number: int,
        analysis_type: str,
        project_root: str | None
    ) -> dict[str, Any]:
        """Handle episode quality analysis requests."""
        raise NotImplementedError

    async def _handle_get_progress_display(self, project_root: str | None) -> dict[str, Any]:
        """Handle progress display retrieval."""
        raise NotImplementedError

    async def _handle_export_ui_reports(
        self,
        report_types: list[str],
        output_format: str,
        project_root: str | None
    ) -> dict[str, Any]:
        """Handle UI report export requests."""
        raise NotImplementedError
