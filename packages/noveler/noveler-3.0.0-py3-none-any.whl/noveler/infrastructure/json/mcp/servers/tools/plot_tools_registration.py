"""Register plotting and planning tools exposed via FastMCP."""

from typing import Any

from noveler.infrastructure.json.mcp.servers.tools.tool_registration_system import ToolRegistrationMixin


class PlotToolsRegistration(ToolRegistrationMixin):
    """Register plotting and planning related MCP tools."""

    def register_tools(self) -> None:
        """Register the plotting and planning tool set."""
        self._register_plot_preparation_tools()
        self._register_creative_design_tools()
        self._register_content_analysis_tools()
        self._register_manuscript_writing_tools()

    def _register_plot_preparation_tools(self) -> None:
        """Register tools that assist with plot preparation."""

        @self.server.tool("get_conversation_context", "会話コンテキスト取得（特定会話IDの全関連情報）")
        async def get_conversation_context(conversation_id: str) -> dict[str, Any]:
            """Return conversation context information."""
            return await self._handle_get_conversation_context(conversation_id)

        @self.server.tool("export_design_data", "設計データエクスポート（エピソードの全設計情報）")
        async def export_design_data(episode_number: int) -> dict[str, Any]:
            """Export design artefacts for the requested episode."""
            return await self._handle_export_design_data(episode_number)

        # ファイル参照・ハッシュベース管理
        @self.server.tool("get_file_by_hash", "FR-002: SHA256ハッシュでファイル検索・内容取得")
        async def get_file_by_hash(hash_value: str) -> dict[str, Any]:
            """Return file contents looked up by SHA256 hash."""
            return await self._handle_get_file_by_hash(hash_value)

        @self.server.tool("check_file_changes", "FR-003: 複数ファイルの変更検知")
        async def check_file_changes(file_paths: list[str]) -> dict[str, Any]:
            """Detect changes for the provided file paths."""
            return await self._handle_check_file_changes(file_paths)

        @self.server.tool("list_files_with_hashes", "ファイル・ハッシュ一覧取得")
        async def list_files_with_hashes() -> dict[str, Any]:
            """List tracked files grouped by their SHA256 digest."""
            return await self._handle_list_files_with_hashes()

    def _register_creative_design_tools(self) -> None:
        """Register creative design helper tools."""

        @self.server.tool("novel", "小説執筆支援コマンド実行")
        async def novel_command(command: str, options: dict[str, Any] | None = None, project_root: str | None = None) -> dict[str, Any]:
            """Forward commands to the Noveler CLI adapter."""
            return await self._handle_novel_command(command, options, project_root)

        @self.server.tool("status", "小説執筆状況確認 - 執筆済み原稿一覧とプロジェクト情報を表示")
        async def status_command(project_root: str | None = None) -> dict[str, Any]:
            """Return the current project writing status information."""
            return await self._handle_status_command(project_root)

        # アーティファクト管理
        @self.server.tool("get_file_reference_info", "ファイル参照情報取得")
        async def get_file_reference_info(file_path: str) -> dict[str, Any]:
            """Return reference metadata for stored files."""
            return await self._handle_get_file_reference_info(file_path)

        @self.server.tool("convert_cli_to_json", "CLI実行結果をJSON形式に変換し、95%トークン削減と参照アーキテクチャを適用")
        async def convert_cli_to_json(cli_result: dict[str, Any]) -> dict[str, Any]:
            """Convert CLI payloads into the JSON response format."""
            return await self._handle_convert_cli_to_json(cli_result)

        @self.server.tool("validate_json_response", "JSON レスポンス形式検証")
        async def validate_json_response(json_data: dict[str, Any]) -> dict[str, Any]:
            """Validate that the JSON payload matches the response schema."""
            return await self._handle_validate_json_response(json_data)

    def _register_content_analysis_tools(self) -> None:
        """Register content analysis helper tools."""

        @self.server.tool("analyze_narrative_depth", "物語の深み分析")
        async def analyze_narrative_depth(
            episode_number: int,
            analysis_aspects: list[str] | None = None,
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Analyse narrative depth for the requested episode."""
            return await self._handle_analyze_narrative_depth(episode_number, analysis_aspects, project_root)

        @self.server.tool("extract_character_development", "キャラクター成長分析")
        async def extract_character_development(
            episode_range: dict[str, int],
            character_names: list[str] | None = None,
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Extract character development metrics across episodes."""
            return await self._handle_extract_character_development(episode_range, character_names, project_root)

        @self.server.tool("analyze_foreshadowing", "伏線分析・管理")
        async def analyze_foreshadowing(
            episode_number: int,
            analysis_mode: str = "comprehensive",
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Analyse and catalogue foreshadowing elements."""
            return await self._handle_analyze_foreshadowing(episode_number, analysis_mode, project_root)

    def _register_manuscript_writing_tools(self) -> None:
        """Register manuscript writing helper tools."""

        @self.server.tool("generate_scene_descriptions", "シーン描写生成")
        async def generate_scene_descriptions(
            scene_requirements: dict[str, Any],
            writing_style: str = "default",
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Generate scene descriptions tailored to the requirements."""
            return await self._handle_generate_scene_descriptions(scene_requirements, writing_style, project_root)

        @self.server.tool("optimize_dialogue_flow", "対話フロー最適化")
        async def optimize_dialogue_flow(
            dialogue_draft: str,
            optimization_goals: list[str] | None = None,
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Optimise dialogue flow based on the provided draft."""
            return await self._handle_optimize_dialogue_flow(dialogue_draft, optimization_goals, project_root)

        @self.server.tool("enhance_emotional_impact", "感情的インパクト強化")
        async def enhance_emotional_impact(
            content_sections: list[str],
            target_emotions: list[str],
            project_root: str | None = None
        ) -> dict[str, Any]:
            """Enhance emotional impact for the specified content sections."""
            return await self._handle_enhance_emotional_impact(content_sections, target_emotions, project_root)

    # 実装メソッド（派生クラスで実装）
    async def _handle_get_conversation_context(self, conversation_id: str) -> dict[str, Any]:
        """Handle conversation context retrieval for subclasses."""
        raise NotImplementedError

    async def _handle_export_design_data(self, episode_number: int) -> dict[str, Any]:
        """Handle design data export for subclasses."""
        raise NotImplementedError

    async def _handle_get_file_by_hash(self, hash_value: str) -> dict[str, Any]:
        """Handle hash-based file retrieval in subclasses."""
        raise NotImplementedError

    async def _handle_check_file_changes(self, file_paths: list[str]) -> dict[str, Any]:
        """Handle file change detection in subclasses."""
        raise NotImplementedError

    async def _handle_list_files_with_hashes(self) -> dict[str, Any]:
        """Handle hash listing in subclasses."""
        raise NotImplementedError

    async def _handle_novel_command(self, command: str, options: dict[str, Any] | None, project_root: str | None) -> dict[str, Any]:
        """Handle legacy Noveler command execution."""
        raise NotImplementedError

    async def _handle_status_command(self, project_root: str | None) -> dict[str, Any]:
        """Handle project status lookups."""
        raise NotImplementedError

    async def _handle_get_file_reference_info(self, file_path: str) -> dict[str, Any]:
        """Handle file reference lookups."""
        raise NotImplementedError

    async def _handle_convert_cli_to_json(self, cli_result: dict[str, Any]) -> dict[str, Any]:
        """Handle CLI to JSON conversion logic."""
        raise NotImplementedError

    async def _handle_validate_json_response(self, json_data: dict[str, Any]) -> dict[str, Any]:
        """Handle JSON response validation."""
        raise NotImplementedError

    async def _handle_analyze_narrative_depth(
        self, episode_number: int, analysis_aspects: list[str] | None, project_root: str | None
    ) -> dict[str, Any]:
        """Handle narrative depth analysis."""
        raise NotImplementedError

    async def _handle_extract_character_development(
        self, episode_range: dict[str, int], character_names: list[str] | None, project_root: str | None
    ) -> dict[str, Any]:
        """Handle character development analysis."""
        raise NotImplementedError

    async def _handle_analyze_foreshadowing(
        self, episode_number: int, analysis_mode: str, project_root: str | None
    ) -> dict[str, Any]:
        """Handle foreshadowing analysis."""
        raise NotImplementedError

    async def _handle_generate_scene_descriptions(
        self, scene_requirements: dict[str, Any], writing_style: str, project_root: str | None
    ) -> dict[str, Any]:
        """Handle scene description generation."""
        raise NotImplementedError

    async def _handle_optimize_dialogue_flow(
        self, dialogue_draft: str, optimization_goals: list[str] | None, project_root: str | None
    ) -> dict[str, Any]:
        """Handle dialogue flow optimisation."""
        raise NotImplementedError

    async def _handle_enhance_emotional_impact(
        self, content_sections: list[str], target_emotions: list[str], project_root: str | None
    ) -> dict[str, Any]:
        """Handle emotional impact enhancement."""
        raise NotImplementedError
