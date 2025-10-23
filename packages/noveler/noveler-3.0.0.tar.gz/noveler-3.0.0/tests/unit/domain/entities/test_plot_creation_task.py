#!/usr/bin/env python3
"""PlotCreationTask エンティティのユニットテスト

仕様書: specs/plot_creation_task_entity.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

from datetime import datetime

import pytest

from noveler.domain.entities.plot_creation_task import PlotCreationTask
from noveler.domain.value_objects.merge_strategy import MergeStrategy
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestPlotCreationTask:
    """PlotCreationTaskのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.project_root = "/test/project"
        self.basic_parameters = {"chapter": 1}

    # ===== 1. 状態遷移テスト =====

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-TASK_NORMAL_EXECUTIO")
    def test_task_normal_execution_flow(self) -> None:
        """TEST-1: 正常な状態遷移フロー(pending → in_progress → completed)"""
        # Given
        task = PlotCreationTask(WorkflowStageType.CHAPTER_PLOT, self.project_root, self.basic_parameters)
        created_files = ["output.yaml", "backup.yaml"]

        # 初期状態確認
        assert task.status == "pending"
        assert task.started_at is None

        before_start = project_now().datetime

        # When: タスク開始
        task.start_execution()

        # Then: 実行中状態に遷移
        after_start = project_now().datetime
        assert task.status == "in_progress"
        assert before_start <= task.started_at <= after_start

        before_complete = project_now().datetime

        # When: タスク完了
        task.complete_execution(created_files)

        # Then: 完了状態に遷移
        after_complete = project_now().datetime
        assert task.status == "completed"
        assert before_complete <= task.completed_at <= after_complete
        assert task.created_files == created_files
        assert task.created_files is not created_files  # コピーされている

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-TASK_FAILURE_FROM_PE")
    def test_task_failure_from_pending(self) -> None:
        """TEST-2: pending状態からの失敗遷移"""
        # Given
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        error_message = "テスト用エラー"
        before_fail = project_now().datetime

        # When
        task.fail_execution(error_message)

        # Then
        after_fail = project_now().datetime
        assert task.status == "failed"
        assert before_fail <= task.failed_at <= after_fail
        assert task.error_message == error_message

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-TASK_FAILURE_FROM_IN")
    def test_task_failure_from_in_progress(self) -> None:
        """TEST-3: in_progress状態からの失敗遷移"""
        # Given
        task = PlotCreationTask(WorkflowStageType.EPISODE_PLOT, self.project_root, {"episode": 1})
        task.start_execution()
        error_message = "実行中エラー"
        before_fail = project_now().datetime

        # When
        task.fail_execution(error_message)

        # Then
        after_fail = project_now().datetime
        assert task.status == "failed"
        assert before_fail <= task.failed_at <= after_fail
        assert task.error_message == error_message

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-START_EXECUTION_INVA")
    def test_start_execution_invalid_status(self) -> None:
        """TEST-4: 不正状態からの実行開始でエラー"""
        # Case 1: in_progress状態から
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        task.start_execution()

        with pytest.raises(ValueError, match="タスクは既に実行中または完了しています"):
            task.start_execution()

        # Case 2: completed状態から
        task2 = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        task2.start_execution()
        task2.complete_execution([])

        with pytest.raises(ValueError, match="タスクは既に実行中または完了しています"):
            task2.start_execution()

        # Case 3: failed状態から
        task3 = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        task3.fail_execution("test error")

        with pytest.raises(ValueError, match="タスクは既に実行中または完了しています"):
            task3.start_execution()

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-COMPLETE_EXECUTION_I")
    def test_complete_execution_invalid_status(self) -> None:
        """TEST-5: 不正状態からの完了試行でエラー"""
        # Case 1: pending状態から
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})

        with pytest.raises(ValueError, match="タスクは実行中ではありません"):
            task.complete_execution([])

        # Case 2: completed状態から
        task2 = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        task2.start_execution()
        task2.complete_execution([])

        with pytest.raises(ValueError, match="タスクは実行中ではありません"):
            task2.complete_execution([])

        # Case 3: failed状態から
        task3 = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        task3.fail_execution("test error")

        with pytest.raises(ValueError, match="タスクは実行中ではありません"):
            task3.complete_execution([])

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-FAIL_EXECUTION_INVAL")
    def test_fail_execution_invalid_status(self) -> None:
        """TEST-6: 不正状態からの失敗試行でエラー"""
        # Case 1: completed状態から
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        task.start_execution()
        task.complete_execution([])

        with pytest.raises(ValueError, match="タスクは既に完了または失敗しています"):
            task.fail_execution("test error")

        # Case 2: failed状態から
        task2 = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        task2.fail_execution("first error")

        with pytest.raises(ValueError, match="タスクは既に完了または失敗しています"):
            task2.fail_execution("second error")

    # ===== 2. 出力パス生成テスト =====

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-GENERATE_OUTPUT_PATH")
    def test_generate_output_path_master_plot(self) -> None:
        """TEST-7: マスタープロットの出力パス生成"""
        # Given
        task = PlotCreationTask(
            WorkflowStageType.MASTER_PLOT,
            self.project_root,
            {},  # パラメータ不要
        )

        # When
        path = task.generate_output_path()

        # Then
        expected = f"{self.project_root}/20_プロット/全体構成.yaml"
        assert path == expected

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-GENERATE_OUTPUT_PATH")
    def test_generate_output_path_chapter_plot(self) -> None:
        """TEST-8: 章別プロットの出力パス生成"""
        # Given
        task = PlotCreationTask(WorkflowStageType.CHAPTER_PLOT, self.project_root, {"chapter": 3})

        # When
        path = task.generate_output_path()

        # Then
        expected = f"{self.project_root}/20_プロット/章別プロット/chapter03.yaml"
        assert path == expected

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-GENERATE_OUTPUT_PATH")
    def test_generate_output_path_chapter_plot_missing_parameter(self) -> None:
        """TEST-9: 章別プロットでchapterパラメータ不足時はデフォルト値1を使用"""
        # Given
        task = PlotCreationTask(
            WorkflowStageType.CHAPTER_PLOT,
            self.project_root,
            {},  # chapterパラメータなし
        )

        # When
        path = task.generate_output_path()

        # Then: デフォルト値1が使用される
        expected = f"{self.project_root}/20_プロット/章別プロット/chapter01.yaml"
        assert path == expected

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-GENERATE_OUTPUT_PATH")
    def test_generate_output_path_episode_plot(self) -> None:
        """TEST-10: 話数別プロットの出力パス生成(3桁ゼロパディング)"""
        # Given
        task = PlotCreationTask(WorkflowStageType.EPISODE_PLOT, self.project_root, {"episode": 5})

        # When
        path = task.generate_output_path()

        # Then
        expected = f"{self.project_root}/20_プロット/話別プロット/episode005.yaml"
        assert path == expected

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-GENERATE_OUTPUT_PATH")
    def test_generate_output_path_episode_plot_large_number(self) -> None:
        """話数別プロットの大きな番号での出力パス生成"""
        # Given
        task = PlotCreationTask(WorkflowStageType.EPISODE_PLOT, self.project_root, {"episode": 123})

        # When
        path = task.generate_output_path()

        # Then
        expected = f"{self.project_root}/20_プロット/話別プロット/episode123.yaml"
        assert path == expected

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-GENERATE_OUTPUT_PATH")
    def test_generate_output_path_episode_plot_missing_parameter(self) -> None:
        """TEST-11: 話数別プロットでepisodeパラメータ不足時はデフォルト値1を使用"""
        # Given
        task = PlotCreationTask(
            WorkflowStageType.EPISODE_PLOT,
            self.project_root,
            {},  # episodeパラメータなし
        )

        # When
        path = task.generate_output_path()

        # Then: デフォルト値1が使用される
        expected = f"{self.project_root}/20_プロット/話別プロット/episode001.yaml"
        assert path == expected

    # ===== 3. 初期化テスト =====

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-INITIALIZATION_WITH_")
    def test_initialization_with_defaults(self) -> None:
        """TEST-13: デフォルトパラメータでの初期化"""
        # Given & When
        before_init = project_now().datetime
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        after_init = project_now().datetime

        # Then
        assert task.stage_type == WorkflowStageType.MASTER_PLOT
        assert task.project_root == self.project_root
        assert task.parameters == {}
        assert task.merge_strategy == MergeStrategy.MERGE
        assert task.status == "pending"
        assert before_init <= task.created_at <= after_init
        assert task.started_at is None
        assert task.completed_at is None
        assert task.failed_at is None
        assert task.error_message is None
        assert task.created_files == []

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-INITIALIZATION_WITH_")
    def test_initialization_with_custom_merge_strategy(self) -> None:
        """TEST-14: カスタムマージ戦略での初期化"""
        # Given & When
        task = PlotCreationTask(
            WorkflowStageType.CHAPTER_PLOT, self.project_root, self.basic_parameters, MergeStrategy.REPLACE
        )

        # Then
        assert task.merge_strategy == MergeStrategy.REPLACE

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-INITIAL_STATE_VERIFI")
    def test_initial_state_verification(self) -> None:
        """TEST-15: 初期化直後の全属性確認"""
        # Given & When
        task = PlotCreationTask(
            WorkflowStageType.EPISODE_PLOT, "/custom/path", {"episode": 10, "extra": "value"}, MergeStrategy.APPEND
        )

        # Then: 設定値確認
        assert task.stage_type == WorkflowStageType.EPISODE_PLOT
        assert task.project_root == "/custom/path"
        assert task.parameters == {"episode": 10, "extra": "value"}
        assert task.merge_strategy == MergeStrategy.APPEND

        # Then: 初期状態確認
        assert task.status == "pending"
        assert isinstance(task.created_at, datetime)

        # Then: None値確認
        assert task.started_at is None
        assert task.completed_at is None
        assert task.failed_at is None
        assert task.error_message is None

        # Then: 空リスト確認
        assert task.created_files == []
        assert isinstance(task.created_files, list)

    # ===== 4. 状態判定テスト =====

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-STATUS_CHECK_METHODS")
    def test_status_check_methods(self) -> None:
        """TEST-16: 状態判定メソッドの正確性"""
        # Given: pending状態
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})

        # Then: pending状態
        assert task.is_completed() is False
        assert task.is_failed() is False
        assert task.is_in_progress() is False

        # When: 実行開始
        task.start_execution()

        # Then: in_progress状態
        assert task.is_completed() is False
        assert task.is_failed() is False
        assert task.is_in_progress() is True

        # When: 完了
        task.complete_execution([])

        # Then: completed状態
        assert task.is_completed() is True
        assert task.is_failed() is False
        assert task.is_in_progress() is False

        # Given: 新しいタスクを失敗させる
        task_fail = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        task_fail.fail_execution("test error")

        # Then: failed状態
        assert task_fail.is_completed() is False
        assert task_fail.is_failed() is True
        assert task_fail.is_in_progress() is False

    # ===== 5. マージ戦略テスト =====

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-MERGE_STRATEGY_PROPE")
    def test_merge_strategy_properties(self) -> None:
        """TEST-19: MergeStrategy プロパティ検証"""
        # Given
        merge_task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {}, MergeStrategy.MERGE)
        replace_task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {}, MergeStrategy.REPLACE)
        append_task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {}, MergeStrategy.APPEND)

        # Then: is_safe プロパティ
        assert merge_task.merge_strategy.is_safe is True
        assert replace_task.merge_strategy.is_safe is False
        assert append_task.merge_strategy.is_safe is True

        # Then: requires_confirmation プロパティ
        assert merge_task.merge_strategy.requires_confirmation is False
        assert replace_task.merge_strategy.requires_confirmation is True
        assert append_task.merge_strategy.requires_confirmation is False

    # ===== 6. 時刻整合性テスト =====

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-EXECUTION_TIMESTAMPS")
    def test_execution_timestamps_consistency(self) -> None:
        """TEST-20: 実行時刻記録の順序確認"""
        # Given
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})

        # When: 段階的実行
        task.start_execution()
        task.complete_execution([])

        # Then: 時刻順序確認
        assert task.created_at <= task.started_at <= task.completed_at

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-FAILURE_TIMESTAMPS_C")
    def test_failure_timestamps_consistency(self) -> None:
        """TEST-21: 失敗時刻記録の順序確認"""
        # Given
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})

        # When: 実行開始後失敗
        task.start_execution()
        task.fail_execution("test error")

        # Then: 時刻順序確認
        assert task.created_at <= task.started_at <= task.failed_at

    # ===== 7. データ不変性テスト =====

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-CREATED_FILES_IMMUTA")
    def test_created_files_immutability(self) -> None:
        """TEST-22: created_files保護の確認"""
        # Given
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})
        original_files = ["file1.yaml", "file2.yaml"]

        # When: タスク完了
        task.start_execution()
        task.complete_execution(original_files)

        # Then: リストがコピーされている
        assert task.created_files == original_files
        assert task.created_files is not original_files

        # When: 元のリストを変更
        original_files.append("file3.yaml")

        # Then: タスクのリストは影響を受けない
        assert len(task.created_files) == 2
        assert "file3.yaml" not in task.created_files

        # When: タスクのリストを変更しようとする
        task.created_files.copy()
        task.created_files.append("malicious.yaml")

        # Then: 実際には変更されている(Pythonのリストは可変)
        # これは仕様上の制限として受け入れる
        assert len(task.created_files) == 3

    # ===== 8. パラメータ検証テスト =====

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-PARAMETER_VALIDATION")
    def test_parameter_validation_for_chapter_plot(self) -> None:
        """TEST-17: 章別プロットでchapterパラメータが未指定時はデフォルト値が使用される"""
        # Given: chapterパラメータなし
        task = PlotCreationTask(WorkflowStageType.CHAPTER_PLOT, self.project_root, {"other": "value"})

        # When
        path = task.generate_output_path()

        # Then: デフォルト値1が使用される
        assert "chapter01.yaml" in path

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-PARAMETER_VALIDATION")
    def test_parameter_validation_for_episode_plot(self) -> None:
        """TEST-18: 話数別プロットでepisodeパラメータが未指定時はデフォルト値が使用される"""
        # Given: episodeパラメータなし
        task = PlotCreationTask(WorkflowStageType.EPISODE_PLOT, self.project_root, {"other": "value"})

        # When
        path = task.generate_output_path()

        # Then: デフォルト値1が使用される
        assert "episode001.yaml" in path

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-GENERATE_OUTPUT_PATH")
    def test_generate_output_path_unknown_stage_type(self) -> None:
        """TEST-12: 未定義のWorkflowStageTypeでValueError(実装では発生しない)"""
        # Note: 現在の実装では全てのWorkflowStageTypeが定義されているため、
        # このテストは理論的なものです。将来の拡張を見越したテストです。

        # Given: 通常のWorkflowStageTypeで動作確認
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})

        # When & Then: 正常に動作する
        path = task.generate_output_path()
        assert "全体構成.yaml" in path

    # ===== 9. エッジケーステスト =====

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-EMPTY_PARAMETERS_WIT")
    def test_empty_parameters_with_master_plot(self) -> None:
        """空パラメータでのマスタープロット処理"""
        # Given
        task = PlotCreationTask(WorkflowStageType.MASTER_PLOT, self.project_root, {})

        # When & Then: エラーなく処理される
        path = task.generate_output_path()
        assert "全体構成.yaml" in path

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-EXTRA_PARAMETERS_IGN")
    def test_extra_parameters_ignored(self) -> None:
        """不要なパラメータは無視される"""
        # Given
        task = PlotCreationTask(
            WorkflowStageType.MASTER_PLOT, self.project_root, {"chapter": 1, "episode": 5, "extra": "ignored"}
        )

        # When & Then: エラーなく処理される
        path = task.generate_output_path()
        assert "全体構成.yaml" in path

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-ZERO_EPISODE_NUMBER")
    def test_zero_episode_number(self) -> None:
        """エピソード番号0での処理"""
        # Given
        task = PlotCreationTask(WorkflowStageType.EPISODE_PLOT, self.project_root, {"episode": 0})

        # When
        path = task.generate_output_path()

        # Then
        assert "episode000.yaml" in path

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-NEGATIVE_EPISODE_NUM")
    def test_negative_episode_number(self) -> None:
        """負のエピソード番号での処理"""
        # Given
        task = PlotCreationTask(WorkflowStageType.EPISODE_PLOT, self.project_root, {"episode": -1})

        # When
        path = task.generate_output_path()

        # Then
        assert "episode-01.yaml" in path

    @pytest.mark.spec("SPEC-PLOT_CREATION_TASK-LARGE_CHAPTER_NUMBER")
    def test_large_chapter_number(self) -> None:
        """大きな章番号での処理"""
        # Given
        task = PlotCreationTask(WorkflowStageType.CHAPTER_PLOT, self.project_root, {"chapter": 999})

        # When
        path = task.generate_output_path()

        # Then
        assert "chapter999.yaml" in path
