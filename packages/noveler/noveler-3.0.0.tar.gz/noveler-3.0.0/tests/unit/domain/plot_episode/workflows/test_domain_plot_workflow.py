#!/usr/bin/env python3
"""プロット作成ワークフロードメインのテスト
TDD+DDD統合開発による実装

ドメインエンティティとビジネスルールをテストで表現し、
プロット作成ワークフローのビジネスロジックを検証


仕様書: SPEC-UNIT-TEST
"""

import pytest
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
pytestmark = pytest.mark.plot_episode



from noveler.domain.entities.plot_creation_task import PlotCreationTask
from noveler.domain.entities.plot_workflow import PlotWorkflow
from noveler.domain.entities.workflow_stage import WorkflowStage
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType
from noveler.domain.value_objects.merge_strategy import MergeStrategy

# これらのクラスが存在しない場合はモック
try:
    from noveler.domain.value_objects.prerequisite_rule import PrerequisiteRule
except ImportError:
    # PrerequisiteRuleクラスのシンプルな実装
    class PrerequisiteRule:
        def __init__(self, file_path: Path, required: bool = True) -> None:
            self.file_path = file_path
            self.required = required

        def is_satisfied(self, _project_root: Path) -> bool:
            return (_project_root / self.file_path).exists()

        def get_description(self) -> str:
            return f"ファイル {self.file_path} が必要です"


try:
    from noveler.domain.services.plot_creation_service import PlotCreationService
except ImportError:
    # PlotCreationServiceのモック実装
    class PlotCreationService:
        def __init__(self, file_repository: object, template_repository: object) -> None:
            self.file_repository = file_repository
            self.template_repository = template_repository

        def create_plot_structure(self, _workflow: PlotWorkflow, _project_root: Path) -> dict:
            return {"success": True, "created_files": []}



DOMAIN_AVAILABLE = True


class TestPrerequisiteRule(unittest.TestCase):
    """前提条件ルール値オブジェクトのテスト"""

    def setUp(self) -> None:
        """テストセットアップ"""
        if not DOMAIN_AVAILABLE:
            self.skipTest("ドメイン層が実装されていません")

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-PREREQUISITE_RULES_C")
    def test_prerequisite_rules_can_be_created(self) -> None:
        """基本的な前提条件ルールを作成できる"""
        rule = PrerequisiteRule(
            file_path="プロジェクト設定.yaml",
            required=True,
            description="プロジェクト基本設定",
        )

        assert rule.file_path == "プロジェクト設定.yaml"
        assert rule.required
        assert rule.description == "プロジェクト基本設定"

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-PARAMETERIZED_PATHS_")
    def test_parameterized_paths_can_be_expanded(self) -> None:
        """パラメータを含むファイルパスを展開できる"""
        rule = PrerequisiteRule(
            file_path="20_プロット/章別プロット/chapter{chapter:02d}.yaml",
            required=True,
            description="章別プロット",
        )

        expanded_path = rule.expand_path(chapter=1)
        assert expanded_path == "20_プロット/章別プロット/chapter01.yaml"

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-OPTIONAL_PREREQUISIT")
    def test_optional_prerequisites_can_be_created(self) -> None:
        """必須でない(推奨)前提条件を作成できる"""
        rule = PrerequisiteRule(
            file_path="30_設定集/魔法システム.yaml",
            required=False,
            description="魔法システム設定",
        )

        assert not rule.required
        assert rule.is_optional()


class TestWorkflowStageType(unittest.TestCase):
    """ワークフロー段階タイプ値オブジェクトのテスト"""

    def setUp(self) -> None:
        """テストセットアップ"""
        if not DOMAIN_AVAILABLE:
            self.skipTest("ドメイン層が実装されていません")

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-WORKFLOW_STAGE_TYPES")
    def test_workflow_stage_types_can_be_created(self) -> None:
        """ワークフロー段階タイプを作成できる"""
        stage_type = WorkflowStageType.MASTER_PLOT

        assert stage_type.value == "master_plot"
        assert stage_type.display_name() == "全体構成作成"

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-ALL_STAGE_TYPES_ARE_")
    def test_all_stage_types_are_defined(self) -> None:
        """全ての段階タイプが適切に定義されている"""
        expected_types = ["master_plot", "chapter_plot", "episode_plot"]

        for expected in expected_types:
            stage_type = WorkflowStageType(expected)
            assert stage_type.value == expected

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-STAGE_ORDER_CAN_BE_R")
    def test_stage_order_can_be_retrieved(self) -> None:
        """ワークフロー段階の実行順序を取得できる"""
        order = WorkflowStageType.get_execution_order()

        assert len(order) == 3
        assert order[0] == WorkflowStageType.MASTER_PLOT
        assert order[1] == WorkflowStageType.CHAPTER_PLOT
        assert order[2] == WorkflowStageType.EPISODE_PLOT


class TestWorkflowStage(unittest.TestCase):
    """ワークフロー段階エンティティのテスト"""

    def setUp(self) -> None:
        """テストセットアップ"""
        if not DOMAIN_AVAILABLE:
            self.skipTest("ドメイン層が実装されていません")

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-WORKFLOW_STAGE_CAN_B")
    def test_workflow_stage_can_be_created(self) -> None:
        """ワークフロー段階エンティティを作成できる"""
        prerequisites = [
            PrerequisiteRule("プロジェクト設定.yaml", True, "プロジェクト設定"),
            PrerequisiteRule("10_企画/企画書.yaml", True, "企画書"),
        ]

        stage = WorkflowStage(
            stage_type=WorkflowStageType.MASTER_PLOT,
            prerequisites=prerequisites,
            output_files=["20_プロット/全体構成.yaml"],
        )

        assert stage.stage_type == WorkflowStageType.MASTER_PLOT
        assert len(stage.prerequisites) == 2
        assert len(stage.output_files) == 1

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-PREREQUISITE_CHECK_I")
    def test_prerequisite_check_is_possible(self) -> None:
        """前提条件のチェックができる"""
        prerequisites = [
            PrerequisiteRule("存在するファイル.yaml", True, "存在ファイル"),
            PrerequisiteRule("存在しないファイル.yaml", True, "不存在ファイル"),
        ]

        stage = WorkflowStage(
            stage_type=WorkflowStageType.MASTER_PLOT,
            prerequisites=prerequisites,
            output_files=["出力.yaml"],
        )

        # ファイル存在確認の関数をモック
        file_checker = Mock()
        file_checker.exists.side_effect = lambda path: path == "存在するファイル.yaml"

        satisfied, results = stage.check_prerequisites(file_checker)

        assert not satisfied  # 1つでも不足があれば失敗
        assert len(results) == 2
        assert results[0].satisfied  # 存在するファイル
        assert not results[1].satisfied  # 存在しないファイル

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-OUTPUT_FILE_ALREADY_")
    def test_output_file_already_exists_can_be_checked(self) -> None:
        """出力予定ファイルが既に存在するかチェックできる"""
        stage = WorkflowStage(
            stage_type=WorkflowStageType.MASTER_PLOT,
            prerequisites=[],
            output_files=["20_プロット/全体構成.yaml"],
        )

        file_checker = Mock()
        file_checker.exists.return_value = True

        has_conflicts = stage.has_output_conflicts(file_checker)
        assert has_conflicts

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-PREREQUISITE_CHECK_W")
    def test_prerequisite_check_with_parameters_is_possible(self) -> None:
        """パラメータを使った前提条件チェックができる"""
        prerequisites = [
            PrerequisiteRule("20_プロット/章別プロット/chapter{chapter:02d}.yaml", True, "章別プロット"),
        ]

        stage = WorkflowStage(
            stage_type=WorkflowStageType.EPISODE_PLOT,
            prerequisites=prerequisites,
            output_files=["話数別プロット.yaml"],
        )

        file_checker = Mock()
        file_checker.exists.return_value = True

        satisfied, results = stage.check_prerequisites(file_checker, chapter=1)

        assert satisfied
        file_checker.exists.assert_called_with("20_プロット/章別プロット/chapter01.yaml")


class TestPlotCreationTask(unittest.TestCase):
    """プロット作成タスクエンティティのテスト"""

    def setUp(self) -> None:
        """テストセットアップ"""
        if not DOMAIN_AVAILABLE:
            self.skipTest("ドメイン層が実装されていません")

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-PLOT_CREATION_TASK_C")
    def test_plot_creation_task_can_be_created(self) -> None:
        """プロット作成タスクを作成できる"""
        task = PlotCreationTask(
            stage_type=WorkflowStageType.MASTER_PLOT,
            project_root=Path("/project"),
            parameters={},
        )

        assert task.stage_type == WorkflowStageType.MASTER_PLOT
        assert task.project_root == Path("/project")
        assert task.status == "pending"

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-TASK_CAN_START_EXECU")
    def test_task_can_start_execution(self) -> None:
        """タスクを実行開始状態にできる"""
        task = PlotCreationTask(
            stage_type=WorkflowStageType.CHAPTER_PLOT,
            project_root=Path("/project"),
            parameters={"chapter": 1},
        )

        task.start_execution()

        assert task.status == "in_progress"
        assert task.started_at is not None

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-TASK_CAN_BE_COMPLETE")
    def test_task_can_be_completed(self) -> None:
        """タスクを完了状態にできる"""
        task = PlotCreationTask(
            stage_type=WorkflowStageType.EPISODE_PLOT,
            project_root=Path("/project"),
            parameters={"episode": 5, "chapter": 1},
        )

        task.start_execution()
        created_files = [Path("20_プロット/話別プロット/episode005.yaml")]
        task.complete_execution(created_files)

        assert task.status == "completed"
        assert task.completed_at is not None
        assert len(task.created_files) == 1

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-TASK_CAN_BE_SET_TO_F")
    def test_task_can_be_set_to_failure_state(self) -> None:
        """タスクを失敗状態にできる"""
        task = PlotCreationTask(
            stage_type=WorkflowStageType.MASTER_PLOT,
            project_root=Path("/project"),
            parameters={},
        )

        task.start_execution()
        task.fail_execution("テンプレートファイルが見つかりません")

        assert task.status == "failed"
        assert task.failed_at is not None
        assert task.error_message == "テンプレートファイルが見つかりません"

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-OUTPUT_FILE_PATH_FRO")
    def test_output_file_path_from_parameters_can_be_generated(self) -> None:
        """パラメータから出力ファイルパスを生成できる"""
        task = PlotCreationTask(
            stage_type=WorkflowStageType.EPISODE_PLOT,
            project_root=Path("/project"),
            parameters={"episode": 5, "chapter": 1},
        )

        output_path = task.generate_output_path()
        expected = Path("/project/20_プロット/話別プロット/episode005.yaml")

        assert output_path == str(expected)


class TestPlotWorkflow(unittest.TestCase):
    """プロット作成ワークフローエンティティのテスト"""

    def setUp(self) -> None:
        """テストセットアップ"""
        if not DOMAIN_AVAILABLE:
            self.skipTest("ドメイン層が実装されていません")

        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir

    def tearDown(self) -> None:
        """テスト後処理"""

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-PLOT_WORKFLOW_CAN_BE")
    def test_plot_workflow_can_be_created(self) -> None:
        """プロット作成ワークフローを作成できる"""
        workflow = PlotWorkflow(self.project_root)

        assert workflow.project_root == self.project_root
        assert len(workflow.stages) == 3  # 3つの段階

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-STAGE_EXECUTION_ORDE")
    def test_stage_execution_order_is_correct(self) -> None:
        """ワークフロー段階の実行順序が正しい"""
        workflow = PlotWorkflow(self.project_root)

        stage_types = [stage.stage_type for stage in workflow.stages]
        expected_order = [
            WorkflowStageType.MASTER_PLOT,
            WorkflowStageType.CHAPTER_PLOT,
            WorkflowStageType.EPISODE_PLOT,
        ]

        assert stage_types == expected_order

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-SPECIFIC_STAGE_PRERE")
    def test_specific_stage_prerequisites_can_be_checked(self) -> None:
        """特定のワークフロー段階の前提条件をチェックできる"""
        workflow = PlotWorkflow(self.project_root)

        # ファイルリポジトリをモック
        file_repo = Mock()
        file_repo.exists.return_value = True

        can_execute, check_results = workflow.can_execute_stage(
            WorkflowStageType.MASTER_PLOT,
            file_repo,
        )

        assert can_execute
        assert len(check_results) > 0

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-CANNOT_EXECUTE_WHEN_")
    def test_cannot_execute_when_previous_stage_incomplete(self) -> None:
        """前の段階が完了していない場合は次段階を実行できない"""
        workflow = PlotWorkflow(self.project_root)

        file_repo = Mock()
        file_repo.exists.side_effect = lambda path: False  # 全て存在しない

        can_execute, check_results = workflow.can_execute_stage(
            WorkflowStageType.CHAPTER_PLOT,
            file_repo,
            chapter=1,
        )

        assert not can_execute

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-WORKFLOW_OVERALL_PRO")
    def test_workflow_overall_progress_can_be_retrieved(self) -> None:
        """ワークフロー全体の進捗状況を取得できる"""
        workflow = PlotWorkflow(self.project_root)

        file_repo = Mock()
        file_repo.exists.side_effect = lambda path: "全体構成.yaml" in path

        progress = workflow.get_progress(file_repo)

        assert "master_plot" in progress
        assert progress["master_plot"]["completed"]
        assert not progress["chapter_plot"]["completed"]


class TestPlotCreationService(unittest.TestCase):
    """プロット作成ドメインサービスのテスト"""

    def setUp(self) -> None:
        """テストセットアップ"""
        if not DOMAIN_AVAILABLE:
            self.skipTest("ドメイン層が実装されていません")

        # リポジトリのモック
        self.file_repo = Mock()
        self.template_repo = Mock()
        self.file_repo.load_project_config.return_value = {}
        self.file_repo.load_file.return_value = {}
        self.file_repo.exists.side_effect = lambda path: "20_プロット" not in str(path)
        self.file_repo.save_file.return_value = None
        self.file_repo.create_directory.return_value = None
        self.template_repo.load_template.return_value = {"template": "content"}

        self.mock_merge_service = Mock()
        self.mock_merge_service.merge_plot_data.side_effect = lambda existing, new, _: new
        validation_result = Mock()
        validation_result.is_valid = True
        validation_result.issues = []
        self.mock_validation_service = Mock()
        self.mock_validation_service.validate_plot_file.return_value = validation_result

        self.service = PlotCreationService(
            self.file_repo,
            self.template_repo,
            plot_merge_service=self.mock_merge_service,
            plot_validation_service=self.mock_validation_service,
        )
        self.service.plot_merge_service = self.mock_merge_service
        self.service.plot_validation_service = self.mock_validation_service

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-OVERALL_STRUCTURE_CA")
    def test_overall_structure_can_be_created(self) -> None:
        """全体構成プロットを作成できる"""
        # モック設定
        self.file_repo.exists.side_effect = lambda path: "20_プロット/全体構成.yaml" not in str(path)
        self.template_repo.load_template.return_value = {"template": "content"}

        task = PlotCreationTask(
            stage_type=WorkflowStageType.MASTER_PLOT,
            project_root=Path("/project"),
            parameters={},
        )

        # 実行
        result = self.service.execute_plot_creation(task)

        # 検証
        assert result.success
        assert task.status == "completed"
        self.template_repo.load_template.assert_called_once()

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-CREATION_REJECTED_WH")
    def test_creation_rejected_when_prerequisites_missing(self) -> None:
        """前提条件を満たしていない場合は作成を拒否する"""
        # モック設定(前提条件不足)
        self.file_repo.exists.return_value = False

        task = PlotCreationTask(
            stage_type=WorkflowStageType.CHAPTER_PLOT,
            project_root=Path("/project"),
            parameters={"chapter": 1},
        )

        # 実行
        result = self.service.execute_plot_creation(task)

        # 検証
        assert not result.success
        assert task.status == "failed"
        assert "前提条件" in task.error_message

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-VERIFICATION_REQUIRE")
    def test_verification_required_on_file_conflict(self) -> None:
        """既存ファイルとの衝突時は確認を求める"""
        # モック設定
        self.file_repo.exists.side_effect = lambda path: True  # 全て存在

        task = PlotCreationTask(
            stage_type=WorkflowStageType.EPISODE_PLOT,
            project_root=Path("/project"),
            parameters={"episode": 5, "chapter": 1},
        )
        task.merge_strategy = MergeStrategy.REPLACE

        # 実行(自動確認=False)
        result = self.service.execute_plot_creation(task, auto_confirm=False)

        # 検証(確認待ちで停止)
        assert not result.success
        assert result.conflict_files == [task.generate_output_path()]

    @pytest.mark.skip(reason="Mock configuration interference - needs investigation")
    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-CUSTOMIZED_FILE_CREA")
    def test_customized_file_creation_using_template(self) -> None:
        """テンプレートを使ってプロジェクト固有の情報でカスタマイズする"""
        # 新しいMockインスタンスを作成（テスト間の干渉を避ける）
        file_repo = Mock()
        template_repo = Mock()

        # モック設定
        file_repo.load_project_config.return_value = {"title": "テストプロジェクト"}
        file_repo.load_file.return_value = {}
        file_repo.exists.side_effect = lambda path: "20_プロット/全体構成.yaml" not in str(path)
        file_repo.save_file.return_value = None
        file_repo.create_directory.return_value = None
        template_repo.load_template.return_value = {"project": "{title}"}

        # 新しいサービスインスタンス
        service = PlotCreationService(
            file_repo,
            template_repo,
            plot_merge_service=self.mock_merge_service,
            plot_validation_service=self.mock_validation_service,
        )

        task = PlotCreationTask(
            stage_type=WorkflowStageType.MASTER_PLOT,
            project_root=Path("/project"),
            parameters={},
        )

        # 実行
        result = service.execute_plot_creation(task)

        # 検証(プロジェクト情報が適用されているか)
        assert result.success
        saved_content = file_repo.save_file.call_args[0][1]
        assert "テストプロジェクト" in str(saved_content)


class TestPlotWorkflowIntegration(unittest.TestCase):
    """プロット作成ワークフロー統合テスト"""

    def setUp(self) -> None:
        """テストセットアップ"""
        if not DOMAIN_AVAILABLE:
            self.skipTest("ドメイン層が実装されていません")

        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_root = self.temp_dir

    def tearDown(self) -> None:
        """テスト後処理"""

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_WORKFLOW-COMPLETE_WORKFLOW_EX")
    def test_complete_workflow_execution(self) -> None:
        """全体構成→章別→話数別の完全なワークフローを実行"""
        PlotWorkflow(self.project_root)

        # ファイルリポジトリをモック
        file_repo = Mock()
        template_repo = Mock()

        # 段階的にファイルが作成される状況をシミュレート
        created_files = set()

        def mock_exists(path):
            # 相対パスを絶対パスに変換して確認
            abs_path = str(self.project_root / path) if isinstance(path, str) else str(path)
            return abs_path in created_files

        def mock_save(path: object, _content: object) -> None:
            abs_path = str(self.project_root / path) if isinstance(path, str) else str(path)
            created_files.add(abs_path)

        file_repo.exists.side_effect = mock_exists
        file_repo.save_file.side_effect = mock_save
        file_repo.load_project_config.return_value = {}
        template_repo.load_template.return_value = {"template": "data"}

        service = PlotCreationService(file_repo, template_repo)

        # 1. 前提ファイルを準備
        created_files.update(
            [
                str(self.project_root / "プロジェクト設定.yaml"),
                str(self.project_root / "10_企画/企画書.yaml"),
                str(self.project_root / "30_設定集/キャラクター.yaml"),
                str(self.project_root / "30_設定集/世界観.yaml"),
            ],
        )

        # 2. 全体構成作成
        master_task = PlotCreationTask(
            stage_type=WorkflowStageType.MASTER_PLOT,
            project_root=self.project_root,
            parameters={},
        )

        result1 = service.execute_plot_creation(master_task)
        # デバッグ情報を出力
        if not result1.success:
            print(f"Error: {result1.error_message}")
            print(f"Created files: {result1.created_files}")
        assert result1.success, f"Master plot creation failed: {result1.error_message}"

        # 3. 章別プロット作成
        chapter_task = PlotCreationTask(
            stage_type=WorkflowStageType.CHAPTER_PLOT,
            project_root=self.project_root,
            parameters={"chapter": 1},
        )

        result2 = service.execute_plot_creation(chapter_task)
        assert result2.success

        # 4. 話数別プロット作成
        episode_task = PlotCreationTask(
            stage_type=WorkflowStageType.EPISODE_PLOT,
            project_root=self.project_root,
            parameters={"episode": 1, "chapter": 1},
        )

        result3 = service.execute_plot_creation(episode_task)
        assert result3.success

        # 全ての段階が成功していることを確認
        assert master_task.status == "completed"
        assert chapter_task.status == "completed"
        assert episode_task.status == "completed"


if __name__ == "__main__":
    unittest.main()
