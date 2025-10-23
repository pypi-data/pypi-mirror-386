#!/usr/bin/env python3
"""プロット作成ワークフローエンティティのテスト

TDD原則に基づく単体テスト


仕様書: SPEC-DOMAIN-ENTITIES
"""

import pytest
from unittest.mock import Mock
pytestmark = pytest.mark.plot_episode



from noveler.domain.entities.plot_workflow import PlotWorkflow
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class TestPlotWorkflow:
    """PlotWorkflowエンティティのテスト"""

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-INITIALIZATION")
    def test_initialization(self) -> None:
        """ワークフロー初期化"""
        workflow = PlotWorkflow("/test/project")

        assert workflow.project_root == "/test/project"
        assert len(workflow.stages) == 3

        # 段階の種類確認
        stage_types = [stage.stage_type for stage in workflow.stages]
        assert WorkflowStageType.MASTER_PLOT in stage_types
        assert WorkflowStageType.CHAPTER_PLOT in stage_types
        assert WorkflowStageType.EPISODE_PLOT in stage_types

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-STAGES_INITIALIZATIO")
    def test_stages_initialization_content(self) -> None:
        """段階の内容確認"""
        workflow = PlotWorkflow("/test/project")

        # マスタープロット段階
        master_stage = workflow.get_stage_by_type(WorkflowStageType.MASTER_PLOT)
        assert master_stage.stage_type == WorkflowStageType.MASTER_PLOT
        assert len(master_stage.prerequisites) == 4
        assert master_stage.output_files == ["20_プロット/全体構成.yaml"]

        # 章別プロット段階
        chapter_stage = workflow.get_stage_by_type(WorkflowStageType.CHAPTER_PLOT)
        assert chapter_stage.stage_type == WorkflowStageType.CHAPTER_PLOT
        assert len(chapter_stage.prerequisites) == 3
        assert chapter_stage.output_files == ["20_プロット/章別プロット/chapter{chapter:02d}.yaml"]

        # 話数別プロット段階
        episode_stage = workflow.get_stage_by_type(WorkflowStageType.EPISODE_PLOT)
        assert episode_stage.stage_type == WorkflowStageType.EPISODE_PLOT
        assert len(episode_stage.prerequisites) == 2
        assert episode_stage.output_files == ["20_プロット/話別プロット/episode{episode:03d}.yaml"]

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-CAN_EXECUTE_STAGE_SU")
    def test_can_execute_stage_success(self) -> None:
        """段階実行可能性チェック - 成功"""
        workflow = PlotWorkflow("/test/project")

        # モックファイルチェッカー(全ファイル存在)
        file_checker = Mock()
        file_checker.exists.return_value = True

        # マスタープロット段階の実行可能性チェック
        can_execute, results = workflow.can_execute_stage(WorkflowStageType.MASTER_PLOT, file_checker)

        assert can_execute is True
        assert len(results) == 4  # 4つの前提条件
        assert all(result.satisfied for result in results)

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-CAN_EXECUTE_STAGE_FA")
    def test_can_execute_stage_failure(self) -> None:
        """段階実行可能性チェック - 失敗"""
        workflow = PlotWorkflow("/test/project")

        # モックファイルチェッカー(全ファイル不存在)
        file_checker = Mock()
        file_checker.exists.return_value = False

        # マスタープロット段階の実行可能性チェック
        can_execute, results = workflow.can_execute_stage(WorkflowStageType.MASTER_PLOT, file_checker)

        assert can_execute is False
        assert len(results) == 4
        assert all(not result.satisfied for result in results)

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-CAN_EXECUTE_STAGE_PA")
    def test_can_execute_stage_partial_success(self) -> None:
        """段階実行可能性チェック - 部分的成功"""
        workflow = PlotWorkflow("/test/project")

        # モックファイルチェッカー(一部ファイル存在)
        file_checker = Mock()

        def exists_side_effect(path: str) -> bool:
            # プロジェクト設定と企画書のみ存在
            return bool("プロジェクト設定.yaml" in path or "企画書.yaml" in path)

        file_checker.exists.side_effect = exists_side_effect

        # マスタープロット段階の実行可能性チェック
        can_execute, results = workflow.can_execute_stage(WorkflowStageType.MASTER_PLOT, file_checker)

        assert can_execute is False  # 必須ファイルが不足
        assert len(results) == 4
        assert sum(result.satisfied for result in results) == 2  # 2つのファイルが存在

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-CAN_EXECUTE_STAGE_WI")
    def test_can_execute_stage_with_parameters(self) -> None:
        """段階実行可能性チェック - パラメータ使用"""
        workflow = PlotWorkflow("/test/project")

        # モックファイルチェッカー
        file_checker = Mock()
        file_checker.exists.return_value = True

        # 章別プロット段階の実行可能性チェック(章番号指定)
        can_execute, results = workflow.can_execute_stage(WorkflowStageType.CHAPTER_PLOT, file_checker, chapter=1)

        assert can_execute is True
        assert len(results) == 3

        # パラメータが正しく展開されたかチェック
        # 章別プロットの前提条件は「全体構成.yaml」「キャラクター.yaml」「世界観.yaml」
        # 実際のファイルパスを確認
        file_paths = [r.file_path for r in results]
        assert "20_プロット/全体構成.yaml" in file_paths
        assert "30_設定集/キャラクター.yaml" in file_paths
        assert "30_設定集/世界観.yaml" in file_paths

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-CAN_EXECUTE_STAGE_IN")
    def test_can_execute_stage_invalid_stage_type(self) -> None:
        """段階実行可能性チェック - 無効な段階タイプ"""
        workflow = PlotWorkflow("/test/project")
        file_checker = Mock()

        # 存在しない段階タイプ
        invalid_stage = "INVALID_STAGE"

        with pytest.raises(ValueError, match="不明なワークフロー段階"):
            workflow.can_execute_stage(invalid_stage, file_checker)

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-GET_PROGRESS_ALL_INC")
    def test_get_progress_all_incomplete(self) -> None:
        """進捗取得 - 全て未完了"""
        workflow = PlotWorkflow("/test/project")

        # モックファイルチェッカー(全ファイル不存在)
        file_checker = Mock()
        file_checker.exists.return_value = False

        progress = workflow.get_progress(file_checker)

        assert len(progress) == 3
        assert all(not stage_info["completed"] for stage_info in progress.values())

        # 各段階の情報確認
        master_plot_info = progress["master_plot"]
        assert master_plot_info["stage_name"] == "全体構成作成"
        assert master_plot_info["prerequisites_count"] == 4
        assert master_plot_info["output_files"] == ["20_プロット/全体構成.yaml"]

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-GET_PROGRESS_ALL_COM")
    def test_get_progress_all_complete(self) -> None:
        """進捗取得 - 全て完了"""
        workflow = PlotWorkflow("/test/project")

        # モックファイルチェッカー(全ファイル存在)
        file_checker = Mock()
        file_checker.exists.return_value = True

        progress = workflow.get_progress(file_checker)

        assert len(progress) == 3
        assert all(stage_info["completed"] for stage_info in progress.values())

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-GET_PROGRESS_PARTIAL")
    def test_get_progress_partial_complete(self) -> None:
        """進捗取得 - 部分的完了"""
        workflow = PlotWorkflow("/test/project")

        # モックファイルチェッカー(マスタープロットのみ存在)
        file_checker = Mock()

        def exists_side_effect(path: str) -> bool:
            return "全体構成.yaml" in path

        file_checker.exists.side_effect = exists_side_effect

        progress = workflow.get_progress(file_checker)

        # マスタープロットのみ完了
        assert progress["master_plot"]["completed"] is True
        assert progress["chapter_plot"]["completed"] is False
        assert progress["episode_plot"]["completed"] is False

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-GET_STAGE_BY_TYPE_SU")
    def test_get_stage_by_type_success(self) -> None:
        """段階取得 - 成功"""
        workflow = PlotWorkflow("/test/project")

        # 各段階の取得
        master_stage = workflow.get_stage_by_type(WorkflowStageType.MASTER_PLOT)
        assert master_stage.stage_type == WorkflowStageType.MASTER_PLOT

        chapter_stage = workflow.get_stage_by_type(WorkflowStageType.CHAPTER_PLOT)
        assert chapter_stage.stage_type == WorkflowStageType.CHAPTER_PLOT

        episode_stage = workflow.get_stage_by_type(WorkflowStageType.EPISODE_PLOT)
        assert episode_stage.stage_type == WorkflowStageType.EPISODE_PLOT

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-GET_STAGE_BY_TYPE_FA")
    def test_get_stage_by_type_failure(self) -> None:
        """段階取得 - 失敗"""
        workflow = PlotWorkflow("/test/project")

        # 存在しない段階タイプ
        invalid_stage = "INVALID_STAGE"

        with pytest.raises(ValueError, match="不明なワークフロー段階"):
            workflow.get_stage_by_type(invalid_stage)

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-MASTER_PLOT_PREREQUI")
    def test_master_plot_prerequisites(self) -> None:
        """マスタープロット前提条件の詳細確認"""
        workflow = PlotWorkflow("/test/project")
        master_stage = workflow.get_stage_by_type(WorkflowStageType.MASTER_PLOT)

        # 前提条件パス確認
        prerequisite_paths = [rule.file_path for rule in master_stage.prerequisites]
        expected_paths = [
            "プロジェクト設定.yaml",
            "10_企画/企画書.yaml",
            "30_設定集/キャラクター.yaml",
            "30_設定集/世界観.yaml",
        ]

        assert prerequisite_paths == expected_paths

        # 必須条件確認
        required_rules = [rule.required for rule in master_stage.prerequisites]
        assert all(required_rules)  # 全て必須

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-CHAPTER_PLOT_PREREQU")
    def test_chapter_plot_prerequisites(self) -> None:
        """章別プロット前提条件の詳細確認"""
        workflow = PlotWorkflow("/test/project")
        chapter_stage = workflow.get_stage_by_type(WorkflowStageType.CHAPTER_PLOT)

        # 前提条件パス確認
        prerequisite_paths = [rule.file_path for rule in chapter_stage.prerequisites]
        expected_paths = ["20_プロット/全体構成.yaml", "30_設定集/キャラクター.yaml", "30_設定集/世界観.yaml"]

        assert prerequisite_paths == expected_paths

        # 必須条件確認
        required_rules = [rule.required for rule in chapter_stage.prerequisites]
        assert required_rules == [True, True, False]  # 世界観設定は任意

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-EPISODE_PLOT_PREREQU")
    def test_episode_plot_prerequisites(self) -> None:
        """話数別プロット前提条件の詳細確認"""
        workflow = PlotWorkflow("/test/project")
        episode_stage = workflow.get_stage_by_type(WorkflowStageType.EPISODE_PLOT)

        # 前提条件パス確認
        prerequisite_paths = [rule.file_path for rule in episode_stage.prerequisites]
        expected_paths = ["20_プロット/全体構成.yaml", "20_プロット/章別プロット/chapter{chapter:02d}.yaml"]

        assert prerequisite_paths == expected_paths

        # 必須条件確認
        required_rules = [rule.required for rule in episode_stage.prerequisites]
        assert all(required_rules)  # 全て必須  # 全て必須

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-WORKFLOW_STAGE_ORDER")
    def test_workflow_stage_order(self) -> None:
        """ワークフロー段階の順序確認"""
        workflow = PlotWorkflow("/test/project")

        # 段階の順序確認
        stage_types = [stage.stage_type for stage in workflow.stages]
        expected_order = [WorkflowStageType.MASTER_PLOT, WorkflowStageType.CHAPTER_PLOT, WorkflowStageType.EPISODE_PLOT]

        assert stage_types == expected_order

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-OUTPUT_FILES_FORMAT")
    def test_output_files_format(self) -> None:
        """出力ファイル形式の確認"""
        workflow = PlotWorkflow("/test/project")

        # 各段階の出力ファイル確認
        master_stage = workflow.get_stage_by_type(WorkflowStageType.MASTER_PLOT)
        assert master_stage.output_files == ["20_プロット/全体構成.yaml"]

        chapter_stage = workflow.get_stage_by_type(WorkflowStageType.CHAPTER_PLOT)
        assert chapter_stage.output_files == ["20_プロット/章別プロット/chapter{chapter:02d}.yaml"]

        episode_stage = workflow.get_stage_by_type(WorkflowStageType.EPISODE_PLOT)
        assert episode_stage.output_files == ["20_プロット/話別プロット/episode{episode:03d}.yaml"]

    @pytest.mark.spec("SPEC-PLOT_WORKFLOW-COMPLEX_WORKFLOW_SCE")
    def test_complex_workflow_scenario(self) -> None:
        """複雑なワークフローシナリオテスト"""
        workflow = PlotWorkflow("/test/project")

        # 段階的にファイルが作成されるシナリオ
        file_checker = Mock()

        # 段階1: 基本設定のみ存在
        def stage1_exists(path: str) -> bool:
            return path in ["プロジェクト設定.yaml", "10_企画/企画書.yaml"]

        file_checker.exists.side_effect = stage1_exists

        # マスタープロット段階は実行不可
        can_execute, _ = workflow.can_execute_stage(WorkflowStageType.MASTER_PLOT, file_checker)
        assert can_execute is False

        # 段階2: 全ての前提条件が揃う
        def stage2_exists(path: str) -> bool:
            required_files = [
                "プロジェクト設定.yaml",
                "10_企画/企画書.yaml",
                "30_設定集/キャラクター.yaml",
                "30_設定集/世界観.yaml",
            ]
            return path in required_files

        file_checker.exists.side_effect = stage2_exists

        # マスタープロット段階が実行可能
        can_execute, _ = workflow.can_execute_stage(WorkflowStageType.MASTER_PLOT, file_checker)
        assert can_execute is True

        # 段階3: マスタープロット完了
        def stage3_exists(path: str) -> bool:
            files = [
                "プロジェクト設定.yaml",
                "10_企画/企画書.yaml",
                "30_設定集/キャラクター.yaml",
                "30_設定集/世界観.yaml",
                "20_プロット/全体構成.yaml",
            ]
            return path in files

        file_checker.exists.side_effect = stage3_exists

        # 章別プロット段階が実行可能
        can_execute, _ = workflow.can_execute_stage(WorkflowStageType.CHAPTER_PLOT, file_checker)
        assert can_execute is True

        # 進捗状況確認
        progress = workflow.get_progress(file_checker)
        assert progress["master_plot"]["completed"] is True
        assert progress["chapter_plot"]["completed"] is False
        assert progress["episode_plot"]["completed"] is False
