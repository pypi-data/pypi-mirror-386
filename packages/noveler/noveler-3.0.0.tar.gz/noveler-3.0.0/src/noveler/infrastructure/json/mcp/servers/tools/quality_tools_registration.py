"""Register quality analysis and checking tools for FastMCP."""

from typing import Any

from noveler.infrastructure.json.mcp.servers.tools.tool_registration_system import ToolRegistrationMixin


class QualityToolsRegistration(ToolRegistrationMixin):
    """Register quality-related MCP tools."""

    def register_tools(self) -> None:
        """Register the quality checking tool set."""
        self._register_main_check_tools()
        self._register_specialized_check_tools()
        self._register_quality_refinement_tools()

    def _register_main_check_tools(self) -> None:
        """Register the primary quality checking tools."""

        @self.server.tool("get_check_tasks", "品質チェックタスクリスト取得")
        async def get_check_tasks(
            episode_number: int,
            check_type: str = "all",
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Return the quality check task list."""
            return await self._handle_get_check_tasks(episode_number, check_type, project_root)

        @self.server.tool("execute_check_step", "品質チェックの特定ステップ実行")
        async def execute_check_step(
            episode_number: int,
            step_id: float,
            input_data: dict[str, Any],
            dry_run: bool = False,
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Execute an individual quality check step."""
            return await self._handle_execute_check_step(episode_number, step_id, input_data, dry_run, project_root)

        @self.server.tool("get_check_status", "現在の品質チェック進捗状況と状態を確認")
        async def get_check_status(episode_number: int, project_root: str | None = None) -> dict[str, Any]:
            """Return the current quality check status."""
            return await self._handle_get_check_status(episode_number, project_root)

        @self.server.tool("get_check_history", "過去の品質チェック履歴を取得")
        async def get_check_history(
            episode_number: int,
            limit: int = 10,
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Return historical quality check results."""
            return await self._handle_get_check_history(episode_number, limit, project_root)

    def _register_specialized_check_tools(self) -> None:
        """Register specialised quality analysis tools."""

        @self.server.tool("check_readability", "読みやすさチェック（文の長さ、難解語彙）")
        async def check_readability(
            episode_number: int,
            project_name: str | None = None,
            check_aspects: list[str] | None = None
        ) -> dict[str, Any]:
            """Execute the readability checker."""
            return await self._handle_readability_check(episode_number, project_name, check_aspects)

        @self.server.tool("check_grammar", "文法・誤字脱字チェック")
        async def check_grammar(
            episode_number: int,
            project_name: str | None = None,
            check_types: list[str] | None = None
        ) -> dict[str, Any]:
            """Execute the grammar checker."""
            return await self._handle_grammar_check(episode_number, project_name, check_types)

        @self.server.tool("test_result_analysis", "テスト結果解析とエラー構造化（LLM自動修正用データ生成）")
        async def test_result_analysis(
            test_result_json: dict[str, Any],
            focus_on_failures: bool = True,
            include_suggestions: bool = True,
            max_issues: int = 20
        ) -> dict[str, Any]:
            """Analyse test results and produce structured data."""
            return await self._handle_test_result_analysis(
                test_result_json, focus_on_failures, include_suggestions, max_issues
            )

    def _register_quality_refinement_tools(self) -> None:
        """Register quality refinement helper tools."""

        @self.server.tool("backup_management", "ファイル・ディレクトリのバックアップ管理（作成・復元・一覧・削除）")
        async def backup_management(
            episode_number: int,
            action: str,
            backup_id: str | None = None,
            backup_name: str | None = None,
            file_path: str | None = None,
            restore_path: str | None = None,
            filter_pattern: str | None = None,
            project_name: str | None = None
        ) -> dict[str, Any]:
            """Handle backup management operations."""
            return await self._handle_backup_management(
                episode_number, action, backup_id, backup_name,
                file_path, restore_path, filter_pattern, project_name
            )

        @self.server.tool("design_conversations", "STEP7: 会話設計（会話ID体系を使用した対話構造の設計）")
        async def design_conversations(
            episode_number: int,
            scene_number: int,
            dialogues: list[dict[str, Any]]
        ) -> dict[str, Any]:
            """Handle conversation design operations."""
            return await self._handle_design_conversations(episode_number, scene_number, dialogues)

        @self.server.tool("track_emotions", "STEP8: 感情曲線追跡（会話IDベースの感情変化管理）")
        async def track_emotions(emotions: list[dict[str, Any]]) -> dict[str, Any]:
            """Handle emotion tracking operations."""
            return await self._handle_track_emotions(emotions)

        @self.server.tool("design_scenes", "STEP9: 情景設計（会話IDベースの場所・時間管理）")
        async def design_scenes(scenes: list[dict[str, Any]]) -> dict[str, Any]:
            """Handle scene design operations."""
            return await self._handle_design_scenes(scenes)

        @self.server.tool("design_senses", "STEP10: 五感描写設計（会話IDベースの感覚トリガー管理）")
        async def design_senses(triggers: list[dict[str, Any]]) -> dict[str, Any]:
            """Handle sensory design operations."""
            return await self._handle_design_senses(triggers)

        @self.server.tool("manage_props", "STEP11: 小道具・世界観設計（会話IDベースの物品管理）")
        async def manage_props(props: list[dict[str, Any]]) -> dict[str, Any]:
            """Handle prop management operations."""
            return await self._handle_manage_props(props)

    # 実装メソッド（派生クラスで実装）
    async def _handle_get_check_tasks(
        self, episode_number: int, check_type: str, project_root: str | None
    ) -> dict[str, Any]:
        """Handle quality check task list retrieval."""
        raise NotImplementedError

    async def _handle_execute_check_step(
        self,
        episode_number: int,
        step_id: float,
        input_data: dict[str, Any],
        dry_run: bool,
        project_root: str | None
    ) -> dict[str, Any]:
        """Handle generic quality check execution."""
        raise NotImplementedError

    async def _handle_get_check_status(self, episode_number: int, project_root: str | None) -> dict[str, Any]:
        """Handle quality status retrieval."""
        raise NotImplementedError

    async def _handle_get_check_history(
        self, episode_number: int, limit: int, project_root: str | None
    ) -> dict[str, Any]:
        """Handle quality history retrieval."""
        raise NotImplementedError

    async def _handle_readability_check(
        self, episode_number: int, project_name: str | None, check_aspects: list[str] | None
    ) -> dict[str, Any]:
        """Handle readability checks."""
        raise NotImplementedError

    async def _handle_grammar_check(
        self, episode_number: int, project_name: str | None, check_types: list[str] | None
    ) -> dict[str, Any]:
        """Handle grammar checks."""
        raise NotImplementedError

    async def _handle_test_result_analysis(
        self,
        test_result_json: dict[str, Any],
        focus_on_failures: bool,
        include_suggestions: bool,
        max_issues: int
    ) -> dict[str, Any]:
        """Handle test result analysis."""
        raise NotImplementedError

    async def _handle_backup_management(
        self,
        episode_number: int,
        action: str,
        backup_id: str | None,
        backup_name: str | None,
        file_path: str | None,
        restore_path: str | None,
        filter_pattern: str | None,
        project_name: str | None
    ) -> dict[str, Any]:
        """Handle backup management requests."""
        raise NotImplementedError

    async def _handle_design_conversations(
        self, episode_number: int, scene_number: int, dialogues: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Handle conversation design requests."""
        raise NotImplementedError

    async def _handle_track_emotions(self, emotions: list[dict[str, Any]]) -> dict[str, Any]:
        """Handle emotion tracking requests."""
        raise NotImplementedError

    async def _handle_design_scenes(self, scenes: list[dict[str, Any]]) -> dict[str, Any]:
        """Handle scene design requests."""
        raise NotImplementedError

    async def _handle_design_senses(self, triggers: list[dict[str, Any]]) -> dict[str, Any]:
        """Handle sensory design requests."""
        raise NotImplementedError

    async def _handle_manage_props(self, props: list[dict[str, Any]]) -> dict[str, Any]:
        """Handle prop management requests."""
        raise NotImplementedError
