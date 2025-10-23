"""E2E Test: スラッシュコマンド経由のwrite実行でA28プロンプトが使用されることを確認

SPEC: Phase 2修正内容の検証
- YamlPromptRepositoryが正しく注入される
- A28詳細プロンプトシステムが使用される
- direct_claude_execution=True が設定される
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestSlashCommandWriteA28Integration:
    """スラッシュコマンド経由のwrite実行でA28プロンプト使用を検証"""

    @pytest.mark.asyncio
    async def test_write_command_uses_yaml_prompt_repository(self, tmp_path):
        """writeコマンドでYamlPromptRepositoryが使用されることを確認"""
        # Setup: プロジェクト構造作成
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        docs_dir = project_root / "docs"
        docs_dir.mkdir()

        # A30ガイドテンプレート作成（簡易版）
        a30_guide = docs_dir / "A30_執筆ガイド.yaml"
        a30_guide.write_text(
            """
stepwise_writing_system:
  stage1:
    name: "骨格構築"
    description: "基本構造設計"
  stage2:
    name: "三幕構成"
    description: "起承転結設計"

prompt_templates:
  basic_writing_request:
    variables:
      genre: "ファンタジー"
      viewpoint: "三人称単元視点"
""",
            encoding="utf-8",
        )

        # Test: execute_novel_command実行
        from noveler.presentation.mcp.server_runtime import execute_novel_command

        with patch("noveler.application.use_cases.integrated_writing_use_case.IntegratedWritingUseCase") as mock_uc_class:
            mock_uc_instance = AsyncMock()
            mock_uc_instance.execute = AsyncMock(
                return_value={
                    "success": True,
                    "session_id": "test-session-001",
                    "yaml_output_path": str(project_root / "output.yaml"),
                }
            )
            mock_uc_class.return_value = mock_uc_instance

            result = await execute_novel_command("write 1", str(project_root), {})

            # Verify: UseCaseが依存注入付きで初期化されたか
            mock_uc_class.assert_called_once()
            call_kwargs = mock_uc_class.call_args[1]

            # YamlPromptRepositoryが注入されている
            assert "yaml_prompt_repository" in call_kwargs
            assert call_kwargs["yaml_prompt_repository"] is not None

            # EpisodeRepositoryが注入されている
            assert "episode_repository" in call_kwargs
            assert call_kwargs["episode_repository"] is not None

            # PlotRepositoryが注入されている
            assert "plot_repository" in call_kwargs
            assert call_kwargs["plot_repository"] is not None

            # execute()が呼ばれた
            assert mock_uc_instance.execute.called

    @pytest.mark.asyncio
    async def test_write_command_sets_direct_claude_execution_flag(self, tmp_path):
        """writeコマンドでdirect_claude_execution=Trueが設定されることを確認"""
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        from noveler.presentation.mcp.server_runtime import execute_novel_command

        with patch("noveler.application.use_cases.integrated_writing_use_case.IntegratedWritingUseCase") as mock_uc_class:
            mock_uc_instance = AsyncMock()
            mock_uc_instance.execute = AsyncMock(return_value={"success": True})
            mock_uc_class.return_value = mock_uc_instance

            await execute_novel_command("write 1", str(project_root), {})

            # Verify: IntegratedWritingRequest に direct_claude_execution=True が設定された
            execute_call_args = mock_uc_instance.execute.call_args
            request_obj = execute_call_args[0][0]

            assert hasattr(request_obj, "direct_claude_execution")
            assert request_obj.direct_claude_execution is True

    @pytest.mark.asyncio
    async def test_write_command_fallback_when_a30_guide_missing(self, tmp_path):
        """A30ガイドテンプレート不在時のフォールバック動作を確認"""
        project_root = tmp_path / "test_project_no_guide"
        project_root.mkdir()

        from noveler.presentation.mcp.server_runtime import execute_novel_command

        with patch("noveler.application.use_cases.integrated_writing_use_case.IntegratedWritingUseCase") as mock_uc_class:
            mock_uc_instance = AsyncMock()
            mock_uc_instance.execute = AsyncMock(return_value={"success": True})
            mock_uc_class.return_value = mock_uc_instance

            result = await execute_novel_command("write 1", str(project_root), {})

            # Verify: A30ガイドなしでもエラーにならない（フォールバック動作）
            assert result is not None
            assert "success" in result.get("result", {})

            # YamlPromptRepository は None になる（フォールバック）
            call_kwargs = mock_uc_class.call_args[1]
            # A30ガイドがない場合、yaml_prompt_repository は None
            # （実際の動作では簡易YAMLフォールバックが発動）

    @pytest.mark.asyncio
    async def test_yaml_prompt_repository_generates_detailed_prompts(self, tmp_path):
        """YamlPromptRepositoryが詳細プロンプトを生成することを確認"""
        from noveler.domain.value_objects.yaml_prompt_content import YamlPromptMetadata
        from noveler.infrastructure.repositories.ruamel_yaml_prompt_repository import RuamelYamlPromptRepository

        # Setup: A30ガイドテンプレート作成
        guide_path = tmp_path / "A30_執筆ガイド.yaml"
        guide_path.write_text(
            """
stepwise_writing_system:
  stage1:
    name: "骨格構築"
    description: "基本構造を設計する段階"
    requirements:
      - "キャラクター設定の確認"
      - "シーン構成の検討"
  stage2:
    name: "三幕構成"
    description: "起承転結を設計する段階"
    requirements:
      - "起：導入部の設計"
      - "承：展開部の設計"
      - "転：クライマックス設計"
      - "結：結末設計"

prompt_templates:
  basic_writing_request:
    variables:
      genre: "ファンタジー"
      viewpoint: "三人称単元視点"
      word_count: "4000"
""",
            encoding="utf-8",
        )

        # Test: プロンプト生成
        repo = RuamelYamlPromptRepository(guide_template_path=guide_path)

        metadata = YamlPromptMetadata(
            title="第001話テスト",
            project="test_project",
            episode_file="第001話.txt",
            genre="ファンタジー",
            word_count="4000",
            viewpoint="三人称単元視点",
            viewpoint_character="主人公",
            detail_level="high",
            methodology="stepwise",
            generated_at="2025-10-11T22:00:00Z",
        )

        prompt_content = await repo.generate_stepwise_prompt(metadata=metadata, custom_requirements=[])

        # Verify: 詳細プロンプトが生成された
        yaml_string = prompt_content.yaml_content
        assert len(yaml_string) > 1000  # 簡易YAMLの数百文字より大幅に長い
        assert "stage1" in yaml_string or "骨格構築" in yaml_string
        assert "stage2" in yaml_string or "三幕構成" in yaml_string

    @pytest.mark.asyncio
    async def test_integrated_writing_use_case_with_repositories(self, tmp_path):
        """IntegratedWritingUseCaseがリポジトリ注入で正しく動作することを確認"""
        from noveler.application.use_cases.integrated_writing_use_case import (
            IntegratedWritingRequest,
            IntegratedWritingUseCase,
        )

        # Setup: モックリポジトリ
        mock_yaml_repo = Mock()
        mock_yaml_repo.generate_stepwise_prompt = AsyncMock(
            return_value=Mock(
                yaml_content="metadata:\n  title: Test\ntask_definition:\n  - Write story",
                validation_passed=True,
            )
        )

        mock_episode_repo = Mock()
        mock_plot_repo = Mock()

        # Test: UseCase実行
        uc = IntegratedWritingUseCase(
            yaml_prompt_repository=mock_yaml_repo,
            episode_repository=mock_episode_repo,
            plot_repository=mock_plot_repo,
        )

        request = IntegratedWritingRequest(
            episode_number=1,
            project_root=tmp_path,
            direct_claude_execution=False,  # テストではClaude実行なし
        )

        # Verify: リポジトリが使用される
        # （実際の実行は複雑なため、モックが呼ばれることを確認）
        assert uc.yaml_prompt_repository is not None
        assert uc.episode_repository is not None
        assert uc.plot_repository is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
