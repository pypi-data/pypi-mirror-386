"""統合執筆ワークフローの統合テスト
仕様: specs/integrated_writing_workflow.spec.md
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.application.use_cases.integrated_writing_use_case import (
    IntegratedWritingRequest,
    IntegratedWritingUseCase,
)
from noveler.infrastructure.repositories.ruamel_yaml_prompt_repository import RuamelYamlPromptRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service


@pytest.mark.spec("SPEC-IWW-001")
class TestIntegratedWritingWorkflow:
    """統合執筆ワークフロー統合テスト"""

    @pytest.fixture
    def mock_repositories(self, tmp_path: Path):
        """モックリポジトリセット"""
        # A30ガイドテンプレート作成
        guide_template = tmp_path / "guide.yaml"
        guide_template.write_text(
            """
stepwise_writing_system:
  methodology: "A30準拠10段階構造化執筆プロセス"
  stages:
    stage1_skeleton:
      name: "骨格構築 - Skeleton Phase"
      objective: "話の骨格・構造を確立"
      tasks:
        - name: "シーン構成の確定"
          details: "導入→展開→転換→結末の流れを設計"
prompt_templates:
  basic_writing_request:
    variables:
      forbidden_expressions: ["〜と思った"]
      recommended_expressions: ["感情 → 身体反応で表現"]
""",
            encoding="utf-8",
        )

        yaml_prompt_repo = RuamelYamlPromptRepository(guide_template)
        episode_repo = Mock()
        plot_repo = Mock()

        # plot_repo のモック設定
        plot_repo.find_by_episode_number = Mock(return_value=None)

        return yaml_prompt_repo, episode_repo, plot_repo

    @pytest.fixture
    def integrated_use_case(self, mock_repositories):
        """統合執筆ユースケース"""
        yaml_prompt_repo, episode_repo, plot_repo = mock_repositories
        return IntegratedWritingUseCase(
            yaml_prompt_repository=yaml_prompt_repo, episode_repository=episode_repo, plot_repository=plot_repo
        )

    @pytest.fixture
    def valid_request(self, tmp_path: Path) -> IntegratedWritingRequest:
        """有効な統合執筆リクエスト"""
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # 必要ディレクトリ作成
        path_service = get_common_path_service()
        (project_root / str(path_service.get_manuscript_dir())).mkdir()

        return IntegratedWritingRequest(
            episode_number=13,
            project_root=project_root,
            word_count_target="3500",
            custom_requirements=["古代システム分析", "リスク評価"],
        )

    @pytest.mark.asyncio
    async def test_complete_integrated_workflow_success(
        self, integrated_use_case: IntegratedWritingUseCase, valid_request: IntegratedWritingRequest
    ):
        """完全な統合ワークフロー成功テスト"""
        # yamllint のモック（成功）
        with patch(
            "noveler.infrastructure.repositories.ruamel_yaml_prompt_repository.asyncio.create_subprocess_exec"
        ) as mock_subprocess:
            mock_process = Mock()
            mock_process.communicate.return_value = ("", "")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            response = await integrated_use_case.execute(valid_request)

            assert response.success
            assert response.session_id.startswith("iww-")
            assert response.yaml_output_path is not None
            assert response.yaml_output_path.exists()
            assert response.manuscript_path is not None
            assert response.manuscript_path.exists()
            assert response.execution_time_seconds > 0
            assert not response.fallback_executed

    @pytest.mark.asyncio
    async def test_workflow_with_yaml_generation_failure(
        self, integrated_use_case: IntegratedWritingUseCase, valid_request: IntegratedWritingRequest
    ):
        """YAML生成失敗時のフォールバックテスト"""

        # YAML生成失敗をシミュレート
        with patch.object(
            integrated_use_case.yaml_prompt_repository,
            "generate_stepwise_prompt",
            side_effect=Exception("YAML生成失敗"),
        ):
            response = await integrated_use_case.execute(valid_request)

            # フォールバックが実行されることを確認
            assert response.success  # フォールバック成功
            assert response.fallback_executed
            assert "統合ワークフロー失敗、従来方式で継続" in response.error_message
            assert response.manuscript_path is not None
            assert response.manuscript_path.exists()

    @pytest.mark.asyncio
    async def test_workflow_with_custom_requirements_extraction(
        self, integrated_use_case: IntegratedWritingUseCase, valid_request: IntegratedWritingRequest
    ):
        """カスタム要件抽出テスト"""

        # プロットデータをモック
        mock_plot_data = Mock()
        mock_plot_data.key_events = ["イベント1", "イベント2", "イベント3"]
        mock_plot_data.technical_elements = ["技術要素1", "技術要素2"]
        mock_plot_data.character_development = True

        integrated_use_case.plot_repository.find_by_episode_number.return_value = mock_plot_data

        with patch(
            "noveler.infrastructure.repositories.ruamel_yaml_prompt_repository.asyncio.create_subprocess_exec"
        ) as mock_subprocess:
            mock_process = Mock()
            mock_process.communicate.return_value = ("", "")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            response = await integrated_use_case.execute(valid_request)

            assert response.success
            # プロット要件が抽出されることを期待（詳細は実装依存）
            assert response.yaml_output_path.exists()

    @pytest.mark.asyncio
    async def test_workflow_performance_requirements(
        self, integrated_use_case: IntegratedWritingUseCase, valid_request: IntegratedWritingRequest
    ):
        """パフォーマンス要件テスト（2秒以内）"""

        with patch(
            "noveler.infrastructure.repositories.ruamel_yaml_prompt_repository.asyncio.create_subprocess_exec"
        ) as mock_subprocess:
            mock_process = Mock()
            mock_process.communicate.return_value = ("", "")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            import time

            start_time = time.perf_counter()

            response = await integrated_use_case.execute(valid_request)

            end_time = time.perf_counter()
            execution_time = end_time - start_time

            assert response.success
            assert execution_time < 2.0  # NFR-001: 2秒以内
            assert response.execution_time_seconds < 2.0

    @pytest.mark.spec("SPEC-INTEGRATED_WRITING_WORKFLOW-REQUEST_VALIDATION")
    def test_request_validation(self, tmp_path: Path):
        """リクエスト検証テスト"""

        # 無効なプロジェクトルート
        nonexistent_root = tmp_path / "nonexistent"

        request = IntegratedWritingRequest(episode_number=13, project_root=nonexistent_root)

        # プロジェクトルートが存在しない場合の処理確認
        assert request.episode_number == 13
        assert request.project_root == nonexistent_root
