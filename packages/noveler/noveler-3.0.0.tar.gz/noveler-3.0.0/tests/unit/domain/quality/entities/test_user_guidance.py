#!/usr/bin/env python3
"""ユーザーガイダンスエンティティのテスト

TDD原則に基づく単体テスト


仕様書: SPEC-DOMAIN-ENTITIES
"""

import pytest
pytestmark = pytest.mark.quality_domain

from noveler.domain.entities.user_guidance import GuidanceStep, GuidanceType, UserGuidance
from noveler.domain.value_objects.time_estimation import TimeEstimation
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class TestGuidanceStep:
    """GuidanceStepのテスト"""

    @pytest.mark.spec("SPEC-USER_GUIDANCE-VALID_GUIDANCE_STEP_")
    def test_valid_guidance_step_creation(self) -> None:
        """有効なガイダンスステップの作成"""
        step = GuidanceStep(
            step_number=1,
            title="プロジェクト設定を作成",
            description="プロジェクトの基本設定ファイルを作成します",
            command="cp template.yaml プロジェクト設定.yaml",
            time_estimation=TimeEstimation.from_minutes(10),
        )

        assert step.step_number == 1
        assert step.title == "プロジェクト設定を作成"
        assert step.description == "プロジェクトの基本設定ファイルを作成します"
        assert step.command == "cp template.yaml プロジェクト設定.yaml"
        assert step.time_estimation.in_minutes() == 10
        assert step.is_completed is False
        assert step.prerequisites == []

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GUIDANCE_STEP_WITH_P")
    def test_guidance_step_with_prerequisites(self) -> None:
        """前提条件付きガイダンスステップ"""
        step = GuidanceStep(
            step_number=2,
            title="キャラクター設定を作成",
            description="主要キャラクターの設定を作成します",
            command="edit 30_設定集/キャラクター.yaml",
            time_estimation=TimeEstimation.from_minutes(30),
            prerequisites=["プロジェクト設定.yaml", "10_企画/企画書.yaml"],
        )

        assert step.prerequisites == ["プロジェクト設定.yaml", "10_企画/企画書.yaml"]

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GUIDANCE_STEP_INVALI")
    def test_guidance_step_invalid_step_number(self) -> None:
        """無効なステップ番号"""
        with pytest.raises(ValueError, match="ステップ番号は1以上である必要があります"):
            GuidanceStep(
                step_number=0,
                title="テストステップ",
                description="テスト説明",
                command="test_command",
                time_estimation=TimeEstimation.from_minutes(5),
            )

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GUIDANCE_STEP_EMPTY_")
    def test_guidance_step_empty_title(self) -> None:
        """空のタイトル"""
        with pytest.raises(ValueError, match="ステップタイトルは必須です"):
            GuidanceStep(
                step_number=1,
                title="",
                description="テスト説明",
                command="test_command",
                time_estimation=TimeEstimation.from_minutes(5),
            )

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GUIDANCE_STEP_WHITES")
    def test_guidance_step_whitespace_title(self) -> None:
        """空白のみのタイトル"""
        with pytest.raises(ValueError, match="ステップタイトルは必須です"):
            GuidanceStep(
                step_number=1,
                title="   ",
                description="テスト説明",
                command="test_command",
                time_estimation=TimeEstimation.from_minutes(5),
            )

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GUIDANCE_STEP_EMPTY_")
    def test_guidance_step_empty_description(self) -> None:
        """空の説明"""
        with pytest.raises(ValueError, match="ステップ説明は必須です"):
            GuidanceStep(
                step_number=1,
                title="テストステップ",
                description="",
                command="test_command",
                time_estimation=TimeEstimation.from_minutes(5),
            )

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GUIDANCE_STEP_EMPTY_")
    def test_guidance_step_empty_command(self) -> None:
        """空のコマンド"""
        with pytest.raises(ValueError, match="実行コマンドは必須です"):
            GuidanceStep(
                step_number=1,
                title="テストステップ",
                description="テスト説明",
                command="",
                time_estimation=TimeEstimation.from_minutes(5),
            )

    @pytest.mark.spec("SPEC-USER_GUIDANCE-MARK_AS_COMPLETED")
    def test_mark_as_completed(self) -> None:
        """完了マーク"""
        step = GuidanceStep(
            step_number=1,
            title="テストステップ",
            description="テスト説明",
            command="test_command",
            time_estimation=TimeEstimation.from_minutes(5),
        )

        assert step.is_completed is False
        step.mark_as_completed()
        assert step.is_completed is True

    @pytest.mark.spec("SPEC-USER_GUIDANCE-CAN_EXECUTE_NO_PRERE")
    def test_can_execute_no_prerequisites(self) -> None:
        """前提条件なしの実行可能性"""
        step = GuidanceStep(
            step_number=1,
            title="テストステップ",
            description="テスト説明",
            command="test_command",
            time_estimation=TimeEstimation.from_minutes(5),
        )

        # 前提条件なしは常に実行可能
        assert step.can_execute([]) is True
        assert step.can_execute(["some_file.txt"]) is True

    @pytest.mark.spec("SPEC-USER_GUIDANCE-CAN_EXECUTE_WITH_PRE")
    def test_can_execute_with_prerequisites_satisfied(self) -> None:
        """前提条件満足時の実行可能性"""
        step = GuidanceStep(
            step_number=1,
            title="テストステップ",
            description="テスト説明",
            command="test_command",
            time_estimation=TimeEstimation.from_minutes(5),
            prerequisites=["file1.txt", "file2.txt"],
        )

        existing_files = ["file1.txt", "file2.txt", "file3.txt"]
        assert step.can_execute(existing_files) is True

    @pytest.mark.spec("SPEC-USER_GUIDANCE-CAN_EXECUTE_WITH_PRE")
    def test_can_execute_with_prerequisites_not_satisfied(self) -> None:
        """前提条件不満足時の実行可能性"""
        step = GuidanceStep(
            step_number=1,
            title="テストステップ",
            description="テスト説明",
            command="test_command",
            time_estimation=TimeEstimation.from_minutes(5),
            prerequisites=["file1.txt", "file2.txt"],
        )

        # file2.txtが存在しない
        existing_files = ["file1.txt", "file3.txt"]
        assert step.can_execute(existing_files) is False

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GENERATE_DISPLAY_INC")
    def test_generate_display_incomplete(self) -> None:
        """未完了ステップの表示生成"""
        step = GuidanceStep(
            step_number=1,
            title="プロジェクト設定作成",
            description="基本設定ファイルを作成します",
            command="cp template.yaml プロジェクト設定.yaml",
            time_estimation=TimeEstimation.from_minutes(15),
        )

        display = step.generate_display()

        assert "📝 1. プロジェクト設定作成" in display
        assert "基本設定ファイルを作成します" in display
        assert "cp template.yaml プロジェクト設定.yaml" in display
        assert "15分" in display

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GENERATE_DISPLAY_COM")
    def test_generate_display_completed(self) -> None:
        """完了ステップの表示生成"""
        step = GuidanceStep(
            step_number=1,
            title="プロジェクト設定作成",
            description="基本設定ファイルを作成します",
            command="cp template.yaml プロジェクト設定.yaml",
            time_estimation=TimeEstimation.from_minutes(15),
        )

        step.mark_as_completed()
        display = step.generate_display()

        assert "✅ 1. プロジェクト設定作成" in display


class TestUserGuidance:
    """UserGuidanceエンティティのテスト"""

    def create_sample_steps(self) -> list[GuidanceStep]:
        """サンプルステップの作成"""
        return [
            GuidanceStep(
                step_number=1,
                title="プロジェクト設定作成",
                description="基本設定ファイルを作成",
                command="cp template.yaml プロジェクト設定.yaml",
                time_estimation=TimeEstimation.from_minutes(10),
            ),
            GuidanceStep(
                step_number=2,
                title="企画書作成",
                description="作品の企画書を作成",
                command="edit 10_企画/企画書.yaml",
                time_estimation=TimeEstimation.from_minutes(30),
            ),
            GuidanceStep(
                step_number=3,
                title="キャラクター設定",
                description="主要キャラクターの設定",
                command="edit 30_設定集/キャラクター.yaml",
                time_estimation=TimeEstimation.from_minutes(45),
            ),
        ]

    @pytest.mark.spec("SPEC-USER_GUIDANCE-VALID_USER_GUIDANCE_")
    def test_valid_user_guidance_creation(self) -> None:
        """有効なユーザーガイダンスの作成"""
        steps = self.create_sample_steps()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        assert guidance.guidance_type == GuidanceType.PREREQUISITE_MISSING
        assert guidance.title == "プロット作成の準備"
        assert len(guidance.steps) == 3
        assert guidance.target_stage == WorkflowStageType.MASTER_PLOT
        assert guidance.created_at is None
        assert guidance.context_info == {}

    @pytest.mark.spec("SPEC-USER_GUIDANCE-USER_GUIDANCE_WITH_C")
    def test_user_guidance_with_context(self) -> None:
        """コンテキスト情報付きユーザーガイダンス"""
        steps = self.create_sample_steps()
        context = {"project_name": "test_project", "missing_files": ["プロジェクト設定.yaml", "企画書.yaml"]}

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
            created_at="2024-07-16T10:00:00",
            context_info=context,
        )

        assert guidance.created_at == "2024-07-16T10:00:00"
        assert guidance.context_info == context

    @pytest.mark.spec("SPEC-USER_GUIDANCE-USER_GUIDANCE_EMPTY_")
    def test_user_guidance_empty_title(self) -> None:
        """空のタイトル"""
        steps = self.create_sample_steps()

        with pytest.raises(ValueError, match="ガイダンスタイトルは必須です"):
            UserGuidance(
                guidance_type=GuidanceType.PREREQUISITE_MISSING,
                title="",
                steps=steps,
                target_stage=WorkflowStageType.MASTER_PLOT,
            )

    @pytest.mark.spec("SPEC-USER_GUIDANCE-USER_GUIDANCE_EMPTY_")
    def test_user_guidance_empty_steps(self) -> None:
        """空のステップリスト"""
        with pytest.raises(ValueError, match="ガイダンスステップは最低1個必要です"):
            UserGuidance(
                guidance_type=GuidanceType.PREREQUISITE_MISSING,
                title="テストガイダンス",
                steps=[],
                target_stage=WorkflowStageType.MASTER_PLOT,
            )

    @pytest.mark.spec("SPEC-USER_GUIDANCE-USER_GUIDANCE_NON_CO")
    def test_user_guidance_non_consecutive_step_numbers(self) -> None:
        """非連続なステップ番号"""
        steps = [
            GuidanceStep(
                step_number=1,
                title="ステップ1",
                description="説明1",
                command="command1",
                time_estimation=TimeEstimation.from_minutes(10),
            ),
            GuidanceStep(
                step_number=3,  # 2がスキップされている
                title="ステップ3",
                description="説明3",
                command="command3",
                time_estimation=TimeEstimation.from_minutes(10),
            ),
        ]

        with pytest.raises(ValueError, match="ステップ番号が連続していません: 期待値2, 実際値3"):
            UserGuidance(
                guidance_type=GuidanceType.PREREQUISITE_MISSING,
                title="テストガイダンス",
                steps=steps,
                target_stage=WorkflowStageType.MASTER_PLOT,
            )

    @pytest.mark.spec("SPEC-USER_GUIDANCE-CALCULATE_TOTAL_TIME")
    def test_calculate_total_time(self) -> None:
        """総所要時間の計算"""
        steps = self.create_sample_steps()  # 10分 + 30分 + 45分 = 85分

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        total_time = guidance.calculate_total_time()
        assert total_time.in_minutes() == 85
        assert total_time.display_text() == "1時間25分"

    @pytest.mark.spec("SPEC-USER_GUIDANCE-CALCULATE_COMPLETION")
    def test_calculate_completion_rate_none_completed(self) -> None:
        """完了率計算 - 未完了"""
        steps = self.create_sample_steps()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        assert guidance.calculate_completion_rate() == 0

    @pytest.mark.spec("SPEC-USER_GUIDANCE-CALCULATE_COMPLETION")
    def test_calculate_completion_rate_partial_completed(self) -> None:
        """完了率計算 - 部分完了"""
        steps = self.create_sample_steps()
        steps[0].mark_as_completed()  # 1つ目のステップを完了

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        assert guidance.calculate_completion_rate() == 33  # 1/3 = 33%

    @pytest.mark.spec("SPEC-USER_GUIDANCE-CALCULATE_COMPLETION")
    def test_calculate_completion_rate_all_completed(self) -> None:
        """完了率計算 - 全完了"""
        steps = self.create_sample_steps()
        for step in steps:
            step.mark_as_completed()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        assert guidance.calculate_completion_rate() == 100

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GET_NEXT_STEP_FIRST_")
    def test_get_next_step_first_step(self) -> None:
        """次のステップ取得 - 最初のステップ"""
        steps = self.create_sample_steps()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        next_step = guidance.get_next_step()
        assert next_step is not None
        assert next_step.step_number == 1
        assert next_step.title == "プロジェクト設定作成"

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GET_NEXT_STEP_MIDDLE")
    def test_get_next_step_middle_step(self) -> None:
        """次のステップ取得 - 中間のステップ"""
        steps = self.create_sample_steps()
        steps[0].mark_as_completed()  # 1つ目完了

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        next_step = guidance.get_next_step()
        assert next_step is not None
        assert next_step.step_number == 2
        assert next_step.title == "企画書作成"

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GET_NEXT_STEP_ALL_CO")
    def test_get_next_step_all_completed(self) -> None:
        """次のステップ取得 - 全完了"""
        steps = self.create_sample_steps()
        for step in steps:
            step.mark_as_completed()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        next_step = guidance.get_next_step()
        assert next_step is None

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GET_CURRENT_STEP_NUM")
    def test_get_current_step_number(self) -> None:
        """現在のステップ番号取得"""
        steps = self.create_sample_steps()
        steps[0].mark_as_completed()  # 1つ目完了

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        assert guidance.get_current_step_number() == 2

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GET_CURRENT_STEP_NUM")
    def test_get_current_step_number_all_completed(self) -> None:
        """現在のステップ番号取得 - 全完了"""
        steps = self.create_sample_steps()
        for step in steps:
            step.mark_as_completed()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        assert guidance.get_current_step_number() == 4  # len(steps) + 1

    @pytest.mark.spec("SPEC-USER_GUIDANCE-IS_COMPLETED_FALSE")
    def test_is_completed_false(self) -> None:
        """完了状態チェック - 未完了"""
        steps = self.create_sample_steps()
        steps[0].mark_as_completed()  # 1つだけ完了

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        assert guidance.is_completed() is False

    @pytest.mark.spec("SPEC-USER_GUIDANCE-IS_COMPLETED_TRUE")
    def test_is_completed_true(self) -> None:
        """完了状態チェック - 完了"""
        steps = self.create_sample_steps()
        for step in steps:
            step.mark_as_completed()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        assert guidance.is_completed() is True

    @pytest.mark.spec("SPEC-USER_GUIDANCE-CAN_START_NEXT_STEP_")
    def test_can_start_next_step_true(self) -> None:
        """次のステップ開始可能性 - 可能"""
        steps = self.create_sample_steps()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        # 前提条件なしのステップは常に開始可能
        assert guidance.can_start_next_step([]) is True

    @pytest.mark.spec("SPEC-USER_GUIDANCE-CAN_START_NEXT_STEP_")
    def test_can_start_next_step_false_no_next_step(self) -> None:
        """次のステップ開始可能性 - 次のステップなし"""
        steps = self.create_sample_steps()
        for step in steps:
            step.mark_as_completed()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        assert guidance.can_start_next_step([]) is False

    @pytest.mark.spec("SPEC-USER_GUIDANCE-CAN_START_NEXT_STEP_")
    def test_can_start_next_step_false_prerequisites_not_met(self) -> None:
        """次のステップ開始可能性 - 前提条件不満足"""
        steps = self.create_sample_steps()
        steps[1].prerequisites = ["required_file.txt"]  # 2つ目のステップに前提条件追加
        steps[0].mark_as_completed()  # 1つ目完了

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        # required_file.txtが存在しない
        assert guidance.can_start_next_step([]) is False

        # required_file.txtが存在する
        assert guidance.can_start_next_step(["required_file.txt"]) is True

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GENERATE_DISPLAY_INC")
    def test_generate_display_incomplete(self) -> None:
        """表示生成 - 未完了"""
        steps = self.create_sample_steps()
        steps[0].mark_as_completed()  # 1つ目完了

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        display = guidance.generate_display()

        # タイトルと進捗情報
        assert "🎯 プロット作成の準備" in display
        assert "📊 進捗: 33% 完了" in display
        assert "⏱️  予想所要時間: 1時間25分" in display

        # ステップ情報
        assert "✅ 1. プロジェクト設定作成" in display
        assert "📝 2. 企画書作成" in display
        assert "📝 3. キャラクター設定" in display

        # 次のステップハイライト
        assert "🔄 次のステップ: 企画書作成" in display

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GENERATE_DISPLAY_COM")
    def test_generate_display_completed(self) -> None:
        """表示生成 - 完了"""
        steps = self.create_sample_steps()
        for step in steps:
            step.mark_as_completed()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="プロット作成の準備",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        display = guidance.generate_display()

        # 完了状態
        assert "📊 進捗: 100% 完了" in display
        assert "✅ 全ステップ完了!" in display
        assert "🔄 次のステップ:" not in display

    @pytest.mark.spec("SPEC-USER_GUIDANCE-GUIDANCE_TYPES_ENUM")
    def test_guidance_types_enum(self) -> None:
        """ガイダンスタイプの列挙値"""
        # 全てのタイプが使用可能
        guidance_types = [
            GuidanceType.PREREQUISITE_MISSING,
            GuidanceType.SUCCESS_NEXT_STEPS,
            GuidanceType.ERROR_RESOLUTION,
            GuidanceType.PROGRESS_UPDATE,
        ]

        for guidance_type in guidance_types:
            steps = self.create_sample_steps()
            guidance = UserGuidance(
                guidance_type=guidance_type,
                title="テストガイダンス",
                steps=steps,
                target_stage=WorkflowStageType.MASTER_PLOT,
            )

            assert guidance.guidance_type == guidance_type

    @pytest.mark.spec("SPEC-USER_GUIDANCE-COMPLEX_WORKFLOW_SCE")
    def test_complex_workflow_scenario(self) -> None:
        """複雑なワークフローシナリオ"""
        # 段階的に前提条件が満たされるシナリオ
        steps = [
            GuidanceStep(
                step_number=1,
                title="基本ファイル作成",
                description="基本的なファイルを作成",
                command="touch basic.txt",
                time_estimation=TimeEstimation.from_minutes(5),
            ),
            GuidanceStep(
                step_number=2,
                title="設定ファイル作成",
                description="設定ファイルを作成",
                command="edit config.yaml",
                time_estimation=TimeEstimation.from_minutes(15),
                prerequisites=["basic.txt"],
            ),
            GuidanceStep(
                step_number=3,
                title="最終確認",
                description="作成されたファイルを確認",
                command="check files",
                time_estimation=TimeEstimation.from_minutes(10),
                prerequisites=["basic.txt", "config.yaml"],
            ),
        ]

        guidance = UserGuidance(
            guidance_type=GuidanceType.SUCCESS_NEXT_STEPS,
            title="段階的セットアップ",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        # 初期状態: 最初のステップは実行可能
        assert guidance.can_start_next_step([]) is True

        # 1つ目完了後: 2つ目のステップは実行不可(前提条件不満足)
        steps[0].mark_as_completed()
        assert guidance.can_start_next_step([]) is False

        # basic.txt作成後: 2つ目のステップは実行可能
        assert guidance.can_start_next_step(["basic.txt"]) is True

        # 2つ目完了後: 3つ目のステップは実行不可(config.yamlが不足)
        steps[1].mark_as_completed()
        assert guidance.can_start_next_step(["basic.txt"]) is False

        # 全ファイル作成後: 3つ目のステップは実行可能
        assert guidance.can_start_next_step(["basic.txt", "config.yaml"]) is True

        # 全完了後: 次のステップなし
        steps[2].mark_as_completed()
        assert guidance.can_start_next_step(["basic.txt", "config.yaml"]) is False
        assert guidance.is_completed() is True
