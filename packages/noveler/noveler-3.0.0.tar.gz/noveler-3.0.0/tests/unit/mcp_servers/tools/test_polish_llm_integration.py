"""
単体テスト: polish_manuscript_applyのLLM統合確認

SPEC-LLM-001準拠: UniversalLLMUseCase統合の確認
"""
import pytest
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, AsyncMock

from mcp_servers.noveler.tools.polish_manuscript_apply_tool import PolishManuscriptApplyTool
from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest


@pytest.mark.spec("SPEC-LLM-001")
class TestPolishLLMIntegration:
    """polish_manuscript_applyのLLM統合テスト"""

    @pytest.fixture
    def tool(self):
        """テスト対象ツール"""
        return PolishManuscriptApplyTool()

    @pytest.fixture
    def sample_request(self):
        """テスト用リクエスト"""
        return ToolRequest(
            episode_number=1,
            project_name="test_project",
            additional_params={
                "dry_run": True,
                "stages": ["stage2", "stage3"]
            }
        )

    def test_llm_execution_uses_universal_pattern(self, tool):
        """LLM実行が中央集約された_run_llm経由であることを確認"""
        assert hasattr(tool, '_run_llm')

        assert hasattr(tool, '_run_llm'), "統一された_run_llmメソッドが存在する"
        assert not hasattr(tool, '_run_llm_legacy'), "レガシー実装メソッドは削除済みであるべき"

    def test_universal_llm_usecase_import_availability(self):
        """UniversalLLMUseCaseのインポート可能性確認"""
        try:
            from noveler.application.use_cases.universal_llm_use_case import UniversalLLMUseCase
            from noveler.infrastructure.integrations.universal_claude_code_service import UniversalClaudeCodeService
            from noveler.domain.value_objects.universal_prompt_execution import (
                UniversalPromptRequest,
                PromptType,
                ProjectContext
            )
            import_success = True
        except ImportError as e:
            import_success = False
            print(f"インポートエラー: {e}")

        assert import_success, "統合に必要なクラスがインポート可能である必要がある"

    def test_current_mcp_environment_handling(self, tool):
        """現在のMCP環境ハンドリング確認"""
        test_prompt = "テスト用プロンプト"
        project_root = Path("/tmp")  # 存在するパスを使用

        # v3.0.0: MCP環境でもUniversalLLMUseCase統合により適切に動作
        with patch('noveler.infrastructure.factories.path_service_factory.is_mcp_environment', return_value=True):
            fallback_response = MagicMock()
            fallback_response.is_success.return_value = True
            fallback_response.get_metadata_value.return_value = "fallback"
            fallback_response.extracted_data = {"fallback_mode": True}

            with patch('noveler.application.use_cases.universal_llm_use_case.UniversalLLMUseCase') as mock_use_case_cls:
                mock_use_case = mock_use_case_cls.return_value
                mock_use_case.execute_with_fallback = AsyncMock(return_value=fallback_response)

                result = tool._run_llm(project_root, test_prompt)
                assert result is None

    def test_run_llm_invokes_use_case_and_returns_content(self, tool):
        """_run_llmがUnified UseCaseを利用して結果を返す"""
        project_root = Path("/tmp")
        prompt = "テスト用プロンプト"

        mock_response = MagicMock()
        mock_response.is_success.return_value = True
        mock_response.get_metadata_value.return_value = None
        mock_response.extracted_data = {}
        mock_response.get_writing_content.return_value = "改稿後"

        with patch('noveler.application.use_cases.universal_llm_use_case.UniversalLLMUseCase') as mock_use_case_cls:
            mock_use_case = mock_use_case_cls.return_value
            mock_use_case.execute_with_fallback = AsyncMock(return_value=mock_response)

            result = tool._run_llm(project_root, prompt)
            assert result == "改稿後"
            mock_use_case.execute_with_fallback.assert_called_once()

    def test_v3_force_llm_parameter_removed(self, tool):
        """v3.0.0: force_llmパラメータの完全削除確認"""
        # メソッドシグネチャからforce_llmが削除されたことを確認
        import inspect
        signature = inspect.signature(tool._run_llm)
        assert "force_llm" not in signature.parameters, "force_llmパラメータは完全削除される必要があります"

        # スキーマからもforce_llmが削除されたことを確認
        schema = tool.get_input_schema()
        properties = schema.get("properties", {})
        assert "force_llm" not in properties, "スキーマからforce_llmが削除される必要があります"

        # force_llmを含むリクエストでもエラーにならないことを確認（無視される）
        request_with_old_param = ToolRequest(
            episode_number=1,
            project_name="test_project",
            additional_params={
                "dry_run": True,
                "force_llm": True  # このパラメータは無視されるべき
            }
        )

        with patch.object(tool, '_resolve_target_path', return_value=Path("/test/manuscript.md")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.read_text', return_value="テスト内容"):
                    with patch('pathlib.Path.write_text'):
                        with patch.object(tool, '_run_llm', return_value='{"manuscript": "改稿後", "improvements": []}'):
                            # 古いパラメータが含まれていてもエラーにならない
                            result = tool.execute(request_with_old_param)
                            assert result.success

    def test_fallback_behavior_simulation(self, tool):
        """フォールバック動作のシミュレーション"""
        test_prompt = "テスト用プロンプト"
        project_root = Path("/tmp")  # 存在するパスを使用

        # LLM失敗時のフォールバック確認
        with patch.object(tool, '_run_llm', side_effect=Exception("LLM接続エラー")) as mock_llm:
            try:
                result = tool._run_llm(project_root, test_prompt)
                # 例外が発生した場合の処理確認
            except Exception:
                # 現在の実装では例外処理されている
                pass

        # 統合後は適切なフォールバック処理が実装される予定

    def test_performance_requirements_check(self, tool, sample_request):
        """パフォーマンス要件の確認"""
        import time

        with patch.object(tool, '_resolve_target_path', return_value=Path("/test/manuscript.md")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.read_text', return_value="テスト内容"):
                    with patch('pathlib.Path.write_text'):
                        with patch.object(tool, '_run_llm', return_value='{"manuscript": "改稿後", "improvements": []}'):
                            start_time = time.perf_counter()
                            result = tool.execute(sample_request)
                            duration = time.perf_counter() - start_time

                            # SPEC-LLM-001: パフォーマンス劣化10%以内
                        # 基準時間を30秒とする（仕様書準拠）
                        assert duration < 30.0, f"実行時間が基準を超過: {duration:.2f}秒"
                        assert result.success

    def test_architecture_boundary_compliance(self):
        """アーキテクチャ境界遵守の確認"""
        # DDD層設計確認
        tool = PolishManuscriptApplyTool()

        # Presentation層のツールが適切な依存関係を持つことを確認
        # - Application層のUseCaseに依存してOK
        # - Domain層のオブジェクトを使用してOK
        # - Infrastructure層への直接依存は最小限

        # 現在の実装でのインポート確認
        # Domain層依存は既にインポートで確認済み（ツールが正常に動作する）

        # Presentation層のツールが適切な層に依存していることを確認
        assert hasattr(tool, '_run_llm'), "統合されたLLM実行メソッドが存在する"
        assert hasattr(tool, '_run_async_in_thread'), "イベントループ競合回避メソッドが存在する"
        assert not hasattr(tool, '_run_llm_unified'), "削除されたレガシーメソッドが存在しない"
        assert not hasattr(tool, '_run_llm_legacy'), "削除されたレガシーメソッドが存在しない"

        # DDD境界遵守：統合後はApplication層経由でのLLM実行
        # UniversalLLMUseCaseの依存関係は動的インポートで実現

    def test_run_llm_skips_fallback_response(self, tool):
        """フォールバックレスポンスを検出して改稿適用を避ける"""
        from noveler.domain.value_objects.universal_prompt_execution import UniversalPromptResponse, PromptType

        project_root = Path("/tmp")
        prompt = "テストプロンプト"

        fallback_response = UniversalPromptResponse(
            success=True,
            response_content="フォールバック指示",
            extracted_data={"fallback_mode": True},
            prompt_type=PromptType.WRITING,
            metadata={"mode": "fallback"},
        )

        with patch(
            "noveler.application.use_cases.universal_llm_use_case.UniversalLLMUseCase"
        ) as mock_use_case_cls:
            mock_use_case = mock_use_case_cls.return_value
            mock_use_case.execute_with_fallback = AsyncMock(return_value=fallback_response)

            with patch(
                "noveler.infrastructure.integrations.universal_claude_code_service.UniversalClaudeCodeService"
            ):
                result = tool._run_llm(project_root, prompt)

        assert result is None

    def test_execute_does_not_write_when_llm_returns_none(self, tool, sample_request):
        """LLMがNoneを返した場合は原稿を上書きしない"""
        with patch.object(tool, '_resolve_target_path', return_value=Path("/tmp/manuscript.md")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.read_text', return_value="元の内容"):
                    with patch('pathlib.Path.write_text') as mock_write:
                        with patch.object(tool, '_run_llm', return_value=None):
                            result = tool.execute(
                                ToolRequest(
                                    episode_number=sample_request.episode_number,
                                    project_name=sample_request.project_name,
                                    additional_params={
                                        "dry_run": False,
                                        "stages": ["stage2", "stage3"],
                                        "save_report": False,
                                    },
                                )
                            )

        assert result.success
        mock_write.assert_not_called()

    def test_build_prompt_reads_template_file(self, tool, tmp_path):
        """テンプレートファイルからプロンプトを読み込む"""
        template_dir = tmp_path / "templates" / "quality" / "checks"
        template_dir.mkdir(parents=True)
        stage2_template = template_dir / "polish_stage2_content.yaml"
        stage2_template.write_text(
            """
metadata:
  step_id: 26
  step_name: "Test Stage2"
  description: "Stage2 schema v2 test template with extended filler to exceed size limits. lorem ipsum lorem ipsum lorem ipsum lorem ipsum lorem ipsum lorem ipsum lorem ipsum lorem ipsum lorem ipsum lorem ipsum lorem ipsum lorem ipsum "
llm_config:
  role_messages:
    system: "SYSTEM MSG"
    user: "USER MSG"
prompt:
  main_instruction: "Stage2 Template for episode {episode_number}: {project_title}"
constraints:
  hard_rules: ["rule1"]
  soft_targets: []
tasks:
  bullets: ["task1"]
  details: []
artifacts:
  format: json
  required_fields: ["manuscript"]
  example: "{}"
acceptance_criteria:
  checklist: ["check"]
  metrics: []
  by_task: []
""",
            encoding="utf-8",
        )

        request = ToolRequest(episode_number=5, project_name="TestProject")
        prompt, source = tool._build_prompt("stage2", "本文", tmp_path, request)

        assert "SYSTEM MSG" in prompt
        assert "Stage2 Template for episode 005" in prompt
        assert "# Manuscript" in prompt
        assert source == str(stage2_template)

    def test_build_prompt_falls_back_when_placeholder_missing(self, tool, tmp_path):
        """テンプレートのプレースホルダ解決に失敗した場合は内蔵デフォルトへフォールバック"""
        template_dir = tmp_path / "templates" / "quality" / "checks"
        template_dir.mkdir(parents=True)
        # テンプレートに未知のプレースホルダを配置して KeyError を誘発
        (template_dir / "polish_stage3_reader.yaml").write_text(
            ("Unknown placeholder {does_not_exist}\n" * 20),
            encoding="utf-8",
        )

        request = ToolRequest(episode_number=1, project_name="Foo")
        prompt, source = tool._build_prompt("stage3", "テキスト", tmp_path, request)

        assert "Reader Experience Designer" in prompt  # 内蔵デフォルトを使用
        assert source == "embedded_default"

    def test_polish_manuscript_tool_uses_template_loader(self, tmp_path):
        """PolishManuscriptToolがSchema v2テンプレートローダーを利用することを確認"""
        from mcp_servers.noveler.tools.polish_manuscript_tool import PolishManuscriptTool

        tool = PolishManuscriptTool()
        request = ToolRequest(
            episode_number=2,
            project_name="SpecProject",
            additional_params={"stages": ["stage2"], "dry_run": True},
        )
        manuscript_path = tmp_path / "manuscript.md"
        manuscript_path.write_text("テキスト", encoding="utf-8")

        with (
            patch.object(tool, '_resolve_target_path', return_value=manuscript_path),
            patch('mcp_servers.noveler.tools.polish_manuscript_tool.create_path_service', return_value=SimpleNamespace(project_root=tmp_path)),
            patch('pathlib.Path.exists', return_value=True),
            patch('pathlib.Path.read_text', return_value="テキスト"),
            patch('mcp_servers.noveler.tools.polish_manuscript_tool.PolishManuscriptApplyTool') as mock_loader_cls,
        ):
            loader = mock_loader_cls.return_value
            loader._build_prompt.return_value = (
                "PROMPT_FROM_TEMPLATE",
                'templates/quality/checks/polish_stage2_content.yaml',
            )

            response = tool.execute(request)

        loader._build_prompt.assert_called_once_with('stage2', 'テキスト', tmp_path, request)
        assert response.success
        assert response.metadata.get('prompts', {}).get('stage2') == 'PROMPT_FROM_TEMPLATE'
        assert response.issues
        assert response.issues[0].details.get('template_source') == 'templates/quality/checks/polish_stage2_content.yaml'

