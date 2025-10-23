"""プロット作成サービスのテスト

DDD準拠テスト:
    - ビジネスロジックのテスト
- リポジトリパターンのモック化
- ワークフロー実行の検証


仕様書: SPEC-DOMAIN-SERVICES
"""

from unittest.mock import Mock, patch

import pytest

from noveler.domain.entities.plot_creation_task import PlotCreationTask
from noveler.domain.services.plot_creation_service import PlotCreationResult, PlotCreationService
from noveler.domain.value_objects.merge_strategy import MergeStrategy
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class TestPlotCreationResult:
    """PlotCreationResultのテスト"""

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-RESULT_CREATION_SUCC")
    def test_result_creation_success(self) -> None:
        """成功結果の作成"""
        result = PlotCreationResult(success=True, created_files=["chapter1.yaml", "chapter2.yaml"], error_message="")

        assert result.success is True
        assert len(result.created_files) == 2
        assert result.error_message == ""
        assert result.conflict_files == []
        assert result.messages == []

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-RESULT_CREATION_FAIL")
    def test_result_creation_failure(self) -> None:
        """失敗結果の作成"""
        result = PlotCreationResult(
            success=False,
            created_files=[],
            error_message="Template not found",
            conflict_files=["existing.yaml"],
        )

        assert result.success is False
        assert len(result.created_files) == 0
        assert result.error_message == "Template not found"
        assert len(result.conflict_files) == 1

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-RESULT_DEFAULT_CONFL")
    def test_result_default_conflict_files(self) -> None:
        """conflict_filesのデフォルト値"""
        result = PlotCreationResult(success=True, created_files=["test.yaml"])

        assert result.conflict_files == []
        assert result.messages == []


class TestPlotCreationService:
    """PlotCreationServiceのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.project_file_repo = Mock()
        self.template_repo = Mock()
        self.service = PlotCreationService(self.project_file_repo, self.template_repo)

    def create_sample_task(self, stage_type: WorkflowStageType = WorkflowStageType.CHAPTER_PLOT) -> PlotCreationTask:
        """サンプルタスクを作成"""
        return PlotCreationTask(
            project_root="/test/project",
            stage_type=stage_type,
            parameters={"chapter_number": 1, "chapter_title": "始まりの章"},
        )

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-EXECUTE_PLOT_CREATIO")
    def test_execute_plot_creation_success(self) -> None:
        """プロット作成の成功パターン"""
        # Arrange
        task = self.create_sample_task()

        # Mock workflow
        with patch("noveler.domain.services.plot_creation_service.PlotWorkflow") as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            # 前提条件チェック成功
            mock_workflow.can_execute_stage.return_value = (True, [])

            # 出力衝突なし
            mock_stage = Mock()
            mock_stage.has_output_conflicts.return_value = False
            mock_workflow.get_stage_by_type.return_value = mock_stage

            # テンプレート読み込み成功
            template_content = {"template": "chapter_plot", "title": "{chapter_title}"}
            self.template_repo.load_template.return_value = template_content

            # プロジェクト設定
            self.project_file_repo.load_project_config.return_value = {"project_name": "テストプロジェクト"}

            # ファイル保存成功
            self.project_file_repo.save_file.return_value = True

            # バリデーション結果を成功としてモック
            validation_mock = Mock()
            validation_mock.is_valid = True
            validation_mock.issues = []
            self.service.plot_validation_service.validate_plot_file = Mock(return_value=validation_mock)

            # Mock task methods
            task.start_execution = Mock()
            task.complete_execution = Mock()
            task.generate_output_path = Mock(return_value="/test/project/chapter1.yaml")

            # Act
            result = self.service.execute_plot_creation(task)

            # Assert
            assert result.success is True
            assert len(result.created_files) == 1
            assert result.created_files[0] == "/test/project/chapter1.yaml"
            assert result.error_message == ""
            assert result.messages == []

            task.start_execution.assert_called_once()
            task.complete_execution.assert_called_once_with(["/test/project/chapter1.yaml"])
            self.project_file_repo.create_directory.assert_called_once()
            self.project_file_repo.save_file.assert_called_once()

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-EXECUTE_PLOT_CREATIO")
    def test_execute_plot_creation_prerequisites_not_met(self) -> None:
        """前提条件が満たされていない場合"""
        # Arrange
        task = self.create_sample_task()

        # Mock workflow
        with patch("noveler.domain.services.plot_creation_service.PlotWorkflow") as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            # 前提条件チェック失敗
            mock_result = Mock()
            mock_result.rule.required = True
            mock_result.rule.description = "プロジェクト設定ファイル"
            mock_result.satisfied = False
            mock_result.file_path = "/test/project/プロジェクト設定.yaml"

            mock_workflow.can_execute_stage.return_value = (False, [mock_result])

            # Mock task methods
            task.start_execution = Mock()
            task.fail_execution = Mock()

            # Act
            result = self.service.execute_plot_creation(task)

            # Assert
            assert result.success is False
            assert len(result.created_files) == 0
            assert "不足ファイル" in result.error_message
            assert "プロジェクト設定ファイル" in result.error_message
            assert result.messages
            assert result.messages[0].level == "error"

            task.start_execution.assert_called_once()
            task.fail_execution.assert_called_once()

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-EXECUTE_PLOT_CREATIO")
    def test_execute_plot_creation_file_conflict_no_auto_confirm(self) -> None:
        """ファイル衝突時(自動確認なし)"""
        # Arrange
        task = self.create_sample_task()

        # Mock workflow
        with patch("noveler.domain.services.plot_creation_service.PlotWorkflow") as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            # 前提条件チェック成功
            mock_workflow.can_execute_stage.return_value = (True, [])

            # 出力衝突あり
            mock_stage = Mock()
            mock_stage.has_output_conflicts.return_value = True
            mock_workflow.get_stage_by_type.return_value = mock_stage

            # Mock task methods and attributes
            task.start_execution = Mock()
            task.fail_execution = Mock()
            task.generate_output_path = Mock(return_value="/test/project/chapter1.yaml")
            task.merge_strategy = MergeStrategy.REPLACE

            # Act
            result = self.service.execute_plot_creation(task, auto_confirm=False)

            # Assert
            assert result.success is False
            assert len(result.created_files) == 0
            assert "ファイル衝突により停止(上書き確認が必要)" in result.error_message
            assert len(result.conflict_files) == 1
            assert result.conflict_files[0] == "/test/project/chapter1.yaml"
            assert result.messages
            assert result.messages[0].level == "warning"

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-EXECUTE_PLOT_CREATIO")
    def test_execute_plot_creation_template_error(self) -> None:
        """テンプレート読み込みエラー"""
        # Arrange
        task = self.create_sample_task()

        # Mock workflow
        with patch("noveler.domain.services.plot_creation_service.PlotWorkflow") as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            # 前提条件チェック成功
            mock_workflow.can_execute_stage.return_value = (True, [])

            # 出力衝突なし
            mock_stage = Mock()
            mock_stage.has_output_conflicts.return_value = False
            mock_workflow.get_stage_by_type.return_value = mock_stage

            # テンプレート読み込み失敗
            self.template_repo.load_template.side_effect = Exception("Template not found")

            # Mock task methods
            task.start_execution = Mock()
            task.fail_execution = Mock()

            # Act
            result = self.service.execute_plot_creation(task)

            # Assert
            assert result.success is False
            assert len(result.created_files) == 0
            assert "プロット作成中にエラーが発生" in result.error_message
            assert "Template not found" in result.error_message

            task.fail_execution.assert_called_once()

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-EXECUTE_PLOT_CREATIO")
    def test_execute_plot_creation_file_save_error(self) -> None:
        """ファイル保存エラー"""
        # Arrange
        task = self.create_sample_task()

        # Mock workflow
        with patch("noveler.domain.services.plot_creation_service.PlotWorkflow") as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            # 前提条件チェック成功
            mock_workflow.can_execute_stage.return_value = (True, [])

            # 出力衝突なし
            mock_stage = Mock()
            mock_stage.has_output_conflicts.return_value = False
            mock_workflow.get_stage_by_type.return_value = mock_stage

            # テンプレート読み込み成功
            template_content = {"template": "chapter_plot"}
            self.template_repo.load_template.return_value = template_content

            # プロジェクト設定
            self.project_file_repo.load_project_config.return_value = {}

            # ファイル保存失敗
            self.project_file_repo.save_file.side_effect = Exception("Permission denied")

            # Mock task methods
            task.start_execution = Mock()
            task.fail_execution = Mock()
            task.generate_output_path = Mock(return_value="/test/project/chapter1.yaml")

            # Act
            result = self.service.execute_plot_creation(task)

            # Assert
            assert result.success is False
            assert len(result.created_files) == 0
            assert "Permission denied" in result.error_message

            task.fail_execution.assert_called_once()

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-BUILD_PREREQUISITES_")
    def test_build_prerequisites_error_message(self) -> None:
        """前提条件エラーメッセージ構築"""
        # Arrange
        mock_result1 = Mock()
        mock_result1.rule.required = True
        mock_result1.rule.description = "プロジェクト設定"
        mock_result1.satisfied = False
        mock_result1.file_path = "/test/project/プロジェクト設定.yaml"

        mock_result2 = Mock()
        mock_result2.rule.required = True
        mock_result2.rule.description = "全体構成"
        mock_result2.satisfied = False
        mock_result2.file_path = "/test/project/全体構成.yaml"

        # Act
        error_msg = self.service._build_prerequisites_error_message([mock_result1, mock_result2])

        # Assert
        assert "不足ファイル:" in error_msg
        assert "プロジェクト設定" in error_msg
        assert "全体構成" in error_msg

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-CUSTOMIZE_TEMPLATE_B")
    def test_customize_template_basic(self) -> None:
        """テンプレートカスタマイズ(基本)"""
        # Arrange
        task = self.create_sample_task()
        template_content = {"title": "{chapter_title}", "number": "{chapter_number}", "template": "chapter_plot"}

        self.project_file_repo.load_project_config.return_value = {"project_name": "テストプロジェクト"}

        # Act
        result = self.service._customize_template(template_content, task)

        # Assert
        assert result["title"] == "{chapter_title}"
        assert result["number"] == "{chapter_number}"
        assert result["template"] == "chapter_plot"
        assert result["stage_type"] == WorkflowStageType.CHAPTER_PLOT.value
        assert "creation_date" in result
        assert "last_updated" in result

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-CUSTOMIZE_TEMPLATE_W")
    def test_customize_template_with_project_format(self) -> None:
        """プロジェクト情報を使ったテンプレートカスタマイズ"""
        # Arrange
        task = self.create_sample_task()
        template_content = {"project": "プロジェクト名: {project_name}", "author": "{author}"}

        self.project_file_repo.load_project_config.return_value = {
            "project_name": "テストプロジェクト",
            "author": "テスト作者",
        }

        # Act
        result = self.service._customize_template(template_content, task)

        # Assert
        assert result["project"] == "プロジェクト名: テストプロジェクト"
        assert result["author"] == "{author}"

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-CUSTOMIZE_TEMPLATE_F")
    def test_customize_template_format_error(self) -> None:
        """テンプレートフォーマットエラー時の処理"""
        # Arrange
        task = self.create_sample_task()
        template_content = {"project": "プロジェクト名: {undefined_key}"}

        self.project_file_repo.load_project_config.return_value = {"project_name": "テストプロジェクト"}

        # Act
        result = self.service._customize_template(template_content, task)

        # Assert
        # フォーマットエラーは無視され、元の値が保持される
        assert result["project"] == "プロジェクト名: {undefined_key}"

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-COMPLEX_WORKFLOW_SCE")
    def test_complex_workflow_scenario(self) -> None:
        """複雑なワークフローシナリオ"""
        # Arrange
        task = self.create_sample_task(WorkflowStageType.MASTER_PLOT)

        # Mock workflow with multiple stages
        with patch("noveler.domain.services.plot_creation_service.PlotWorkflow") as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            # 前提条件チェック成功
            mock_workflow.can_execute_stage.return_value = (True, [])

            # 出力衝突なし
            mock_stage = Mock()
            mock_stage.has_output_conflicts.return_value = False
            mock_workflow.get_stage_by_type.return_value = mock_stage

            # 複雑なテンプレート
            template_content = {
                "structure": {"total_chapters": 10, "estimated_episodes": 50},
                "project": "プロジェクト: {project_name}",
                "metadata": {"genre": "{genre}", "target_audience": "{target_audience}"},
            }
            self.template_repo.load_template.return_value = template_content

            # プロジェクト設定
            self.project_file_repo.load_project_config.return_value = {
                "project_name": "複雑なプロジェクト",
                "genre": "ファンタジー",
                "target_audience": "ティーン",
            }

            # Mock task methods
            task.start_execution = Mock()
            task.complete_execution = Mock()
            task.generate_output_path = Mock(return_value="/test/project/全体構成.yaml")

            # Act
            result = self.service.execute_plot_creation(task)

            # Assert
            assert result.success is True
            assert len(result.created_files) == 1

            # カスタマイズされたテンプレートが保存されることを確認
            save_call = self.project_file_repo.save_file.call_args
            saved_content = save_call[0][1]
            assert saved_content["project"] == "プロジェクト: 複雑なプロジェクト"
            assert saved_content["stage_type"] == WorkflowStageType.MASTER_PLOT.value

    @pytest.mark.spec("SPEC-PLOT_CREATION_SERVICE-DIRECTORY_CREATION_F")
    def test_directory_creation_for_nested_output(self) -> None:
        """ネストされた出力パスのディレクトリ作成"""
        # Arrange
        task = self.create_sample_task()

        # Mock workflow
        with patch("noveler.domain.services.plot_creation_service.PlotWorkflow") as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow_class.return_value = mock_workflow

            # 前提条件チェック成功
            mock_workflow.can_execute_stage.return_value = (True, [])

            # 出力衝突なし
            mock_stage = Mock()
            mock_stage.has_output_conflicts.return_value = False
            mock_workflow.get_stage_by_type.return_value = mock_stage

            # テンプレート読み込み成功
            template_content = {"template": "chapter_plot"}
            self.template_repo.load_template.return_value = template_content

            # プロジェクト設定
            self.project_file_repo.load_project_config.return_value = {}

            # ネストされた出力パス
            nested_path = "/test/project/20_プロット/章別プロット/chapter01.yaml"

            # Mock task methods
            task.start_execution = Mock()
            task.complete_execution = Mock()
            task.generate_output_path = Mock(return_value=nested_path)

            # Act
            result = self.service.execute_plot_creation(task)

            # Assert
            assert result.success is True

            # 親ディレクトリが作成されることを確認
            expected_parent = "/test/project/20_プロット/章別プロット"
            self.project_file_repo.create_directory.assert_called_once_with(expected_parent)

            # ファイルが正しいパスに保存されることを確認
            save_call = self.project_file_repo.save_file.call_args
            assert save_call[0][0] == nested_path
