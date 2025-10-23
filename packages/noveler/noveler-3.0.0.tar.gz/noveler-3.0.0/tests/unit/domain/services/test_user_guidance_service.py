"""ユーザーガイダンスサービスのテスト

DDD準拠テスト:
    - ビジネスロジックのテスト
- ガイダンス生成アルゴリズムの検証
- ユーザー体験の最適化確認
"""

from unittest.mock import Mock

import pytest

from noveler.domain.entities.user_guidance import GuidanceStep, GuidanceType, UserGuidance
from noveler.domain.services.user_guidance_service import UserGuidanceService
from noveler.domain.value_objects.progress_status import ProgressStatus
from noveler.domain.value_objects.time_estimation import TimeEstimation
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class TestUserGuidanceService:
    """UserGuidanceServiceのテスト"""

    @pytest.fixture
    def service(self):
        """サービスインスタンス"""
        return UserGuidanceService()

    @pytest.fixture
    def mock_error_context(self):
        """モックエラーコンテキスト"""
        context = Mock()
        context.is_prerequisite_error.return_value = True
        context.missing_files = ["10_企画/企画書.yaml", "30_設定集/キャラクター.yaml"]
        context.affected_stage = WorkflowStageType.MASTER_PLOT
        context.error_type = "missing_prerequisite"
        context.get_user_experience_level.return_value = "beginner"
        context.get_project_type.return_value = "fantasy"
        return context

    @pytest.fixture
    def mock_progress_report(self):
        """モック進捗レポート"""
        report = Mock()
        report.stage_statuses = {
            WorkflowStageType.MASTER_PLOT: ProgressStatus.COMPLETED,
            WorkflowStageType.CHAPTER_PLOT: ProgressStatus.NOT_STARTED,
            WorkflowStageType.EPISODE_PLOT: ProgressStatus.NOT_STARTED,
        }
        return report

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_init(self, service: object) -> None:
        """初期化のテスト"""
        assert hasattr(service, "template_mappings")
        assert hasattr(service, "command_templates")
        assert isinstance(service.template_mappings, dict)
        assert isinstance(service.command_templates, dict)

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_generate_prerequisite_guidance(self, service: object, mock_error_context: object) -> None:
        """前提条件ガイダンス生成テスト"""
        guidance = service.generate_prerequisite_guidance(mock_error_context)

        assert isinstance(guidance, UserGuidance)
        assert guidance.guidance_type == GuidanceType.PREREQUISITE_MISSING
        assert guidance.title == "全体構成作成のための前準備"
        assert guidance.target_stage == WorkflowStageType.MASTER_PLOT
        assert len(guidance.steps) == 2  # 2つの不足ファイル

        # 最初のステップ(企画書)
        first_step = guidance.steps[0]
        assert first_step.step_number == 1
        assert "企画書作成" in first_step.title
        assert "作品のコンセプトと基本設定" in first_step.description
        assert "企画書テンプレート.yaml" in first_step.command
        assert isinstance(first_step.time_estimation, TimeEstimation)

        # 2番目のステップ(キャラクター設定)
        second_step = guidance.steps[1]
        assert second_step.step_number == 2
        assert "キャラクター設定作成" in second_step.title
        assert "キャラクター設定テンプレート.yaml" in second_step.command

        # コンテキスト情報
        assert guidance.context_info["error_type"] == "missing_prerequisite"
        assert guidance.context_info["user_experience"] == "beginner"
        assert guidance.context_info["project_type"] == "fantasy"

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_generate_prerequisite_guidance_invalid_context(self, service: object) -> None:
        """無効なコンテキストでの前提条件ガイダンステスト"""
        invalid_context = Mock()
        invalid_context.is_prerequisite_error.return_value = False

        with pytest.raises(ValueError, match="前提条件エラーではありません"):
            service.generate_prerequisite_guidance(invalid_context)

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_generate_success_guidance(self, service: object) -> None:
        """成功ガイダンス生成テスト"""
        context = {
            "completed_stage": WorkflowStageType.MASTER_PLOT,
            "quality_score": 85.0,
            "completion_time": "2時間",
        }

        guidance = service.generate_success_guidance(context)

        assert isinstance(guidance, UserGuidance)
        assert guidance.guidance_type == GuidanceType.SUCCESS_NEXT_STEPS
        assert guidance.title == "全体構成完了 - 次のステップ"
        assert guidance.target_stage == WorkflowStageType.CHAPTER_PLOT
        assert len(guidance.steps) >= 1

        # 次段階のステップ
        next_step = guidance.steps[0]
        assert next_step.step_number == 1
        assert "章別プロット作成" in next_step.title
        assert "novel plot chapter 1" in next_step.command

        # オプショナルなステップ(品質チェック)
        if len(guidance.steps) > 1:
            optional_step = guidance.steps[1]
            assert optional_step.step_number == 2
            assert "品質チェック" in optional_step.title
            assert "novel check plot" in optional_step.command

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_generate_success_guidance_no_completed_stage(self, service: object) -> None:
        """completed_stageがない場合のテスト"""
        context = {"quality_score": 85.0}

        with pytest.raises(ValueError, match="completed_stageが必要です"):
            service.generate_success_guidance(context)

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_generate_success_guidance_final_stage(self, service: object) -> None:
        """最終段階完了時のガイダンステスト"""
        context = {"completed_stage": WorkflowStageType.EPISODE_PLOT}

        guidance = service.generate_success_guidance(context)

        assert guidance.guidance_type == GuidanceType.SUCCESS_NEXT_STEPS
        assert guidance.title == "話数別プロット完了 - 次のステップ"
        assert guidance.target_stage == WorkflowStageType.EPISODE_PLOT
        # 次の段階がないため、ステップは少ない

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_create_file_creation_step(self, service: object) -> None:
        """ファイル作成ステップ生成テスト"""
        step = service._create_file_creation_step(
            1,
            "10_企画/企画書.yaml",
            WorkflowStageType.MASTER_PLOT,
        )

        assert step.step_number == 1
        assert step.title == "企画書作成"
        assert "作品のコンセプトと基本設定" in step.description
        assert "企画書テンプレート.yaml" in step.command
        assert step.time_estimation.minutes == 45
        assert step.prerequisites == []

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_create_file_creation_step_unknown_file(self, service: object) -> None:
        """未知のファイルの作成ステップテスト"""
        step = service._create_file_creation_step(
            1,
            "unknown/file.yaml",
            WorkflowStageType.MASTER_PLOT,
        )

        assert step.step_number == 1
        assert "fileの作成" in step.title
        assert step.time_estimation.minutes == 30

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_create_next_stage_step(self, service: object) -> None:
        """次段階ステップ生成テスト"""
        step = service._create_next_stage_step(
            WorkflowStageType.MASTER_PLOT,
            WorkflowStageType.CHAPTER_PLOT,
        )

        assert step.step_number == 1
        assert "章別プロット作成" in step.title
        assert "novel plot chapter 1" in step.command
        assert step.time_estimation.minutes == 45

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_create_optional_improvement_step(self, service: object) -> None:
        """オプショナル改善ステップ生成テスト"""
        # マスタープロット段階の場合
        step = service._create_optional_improvement_step(WorkflowStageType.MASTER_PLOT)

        assert step is not None
        assert step.step_number == 2
        assert "品質チェック" in step.title
        assert "novel check plot" in step.command

        # 他の段階の場合
        step_none = service._create_optional_improvement_step(WorkflowStageType.CHAPTER_PLOT)
        assert step_none is None

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_get_file_info(self, service: object) -> None:
        """ファイル情報取得テスト"""
        # 既知のファイル
        info = service._get_file_info("10_企画/企画書.yaml")
        assert info["title"] == "企画書作成"
        assert info["template"] == "企画書テンプレート.yaml"
        assert info["time_minutes"] == 45
        assert info["prerequisites"] == []

        # キャラクター設定(前提条件あり)
        char_info = service._get_file_info("30_設定集/キャラクター.yaml")
        assert char_info["prerequisites"] == ["10_企画/企画書.yaml"]

        # 未知のファイル
        unknown_info = service._get_file_info("unknown/file.yaml")
        assert "fileの作成" in unknown_info["title"]
        assert unknown_info["time_minutes"] == 30

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_get_stage_info(self, service: object) -> None:
        """段階情報取得テスト"""
        info = service._get_stage_info(WorkflowStageType.MASTER_PLOT)
        assert info["title"] == "全体構成プロット作成"
        assert "作品全体の構成" in info["description"]
        assert info["time_minutes"] == 60

        # 未知の段階
        info = service._get_stage_info(WorkflowStageType.MASTER_PLOT)  # 実際は既知だが
        assert "title" in info
        assert "description" in info

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_get_cli_command_for_file(self, service: object) -> None:
        """ファイル用CLIコマンド取得テスト"""
        assert service._get_cli_command_for_file("企画書.yaml", WorkflowStageType.MASTER_PLOT) == "novel init project"
        assert (
            service._get_cli_command_for_file("キャラクター.yaml", WorkflowStageType.MASTER_PLOT)
            == "novel create character"
        )

        assert service._get_cli_command_for_file("世界観.yaml", WorkflowStageType.MASTER_PLOT) == "novel create world"
        assert service._get_cli_command_for_file("全体構成.yaml", WorkflowStageType.MASTER_PLOT) == "novel plot master"

        # 未知のファイル
        cmd = service._get_cli_command_for_file("unknown.yaml", WorkflowStageType.MASTER_PLOT)
        assert "手動で作成" in cmd

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_get_cli_command_for_stage(self, service: object) -> None:
        """段階用CLIコマンド取得テスト"""
        assert service._get_cli_command_for_stage(WorkflowStageType.MASTER_PLOT) == "novel plot master"
        assert service._get_cli_command_for_stage(WorkflowStageType.CHAPTER_PLOT) == "novel plot chapter 1"
        assert service._get_cli_command_for_stage(WorkflowStageType.EPISODE_PLOT) == "novel plot episode 1"

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_get_next_stage(self, service: object) -> None:
        """次段階取得テスト"""
        assert service._get_next_stage(WorkflowStageType.MASTER_PLOT) == WorkflowStageType.CHAPTER_PLOT
        assert service._get_next_stage(WorkflowStageType.CHAPTER_PLOT) == WorkflowStageType.EPISODE_PLOT
        assert service._get_next_stage(WorkflowStageType.EPISODE_PLOT) is None

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_get_stage_japanese_name(self, service: object) -> None:
        """段階日本語名取得テスト"""
        assert service._get_stage_japanese_name(WorkflowStageType.MASTER_PLOT) == "全体構成"
        assert service._get_stage_japanese_name(WorkflowStageType.CHAPTER_PLOT) == "章別プロット"
        assert service._get_stage_japanese_name(WorkflowStageType.EPISODE_PLOT) == "話数別プロット"

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_provide_guidance_for_profile_beginner(self, service: object) -> None:
        """初心者向けプロファイルガイダンステスト"""
        profile = {"experience_level": "beginner", "writing_goal": "hobby"}

        guidance = service.provide_guidance_for_profile(profile)

        assert guidance.guidance_type == GuidanceType.BEGINNER_FRIENDLY
        assert guidance.title == "初心者向けガイダンス"
        assert len(guidance.steps) == 1
        assert "基礎から始めましょう" in guidance.steps[0].title
        assert "novel guide basics" in guidance.steps[0].command
        assert guidance.context_info["message"] == "基礎から丁寧に学んでいきましょう"

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_provide_guidance_for_profile_intermediate(self, service: object) -> None:
        """中級者向けプロファイルガイダンステスト"""
        profile = {"experience_level": "intermediate", "writing_goal": "professional"}

        guidance = service.provide_guidance_for_profile(profile)

        assert guidance.guidance_type == GuidanceType.SUCCESS_NEXT_STEPS
        assert guidance.title == "次のステップ"
        assert len(guidance.steps) == 1
        assert "次のステップを開始" in guidance.steps[0].title
        assert "novel plot master" in guidance.steps[0].command

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_provide_error_guidance(self, service: object) -> None:
        """エラーガイダンス提供テスト"""
        # オブジェクト形式のエラーコンテキスト
        error_context = Mock()
        error_context.error_message = "文章が長すぎます"

        guidance = service.provide_error_guidance(error_context)

        assert guidance.guidance_type == GuidanceType.ERROR_RESOLUTION
        assert guidance.title == "エラー解決ガイダンス"
        assert len(guidance.steps) == 1
        assert "エラーの解決" in guidance.steps[0].title
        assert "novel check --auto-fix" in guidance.steps[0].command
        assert "文章を短く分割してください" in guidance.context_info["improvement_examples"]

        # 辞書形式のエラーコンテキスト
        dict_context = {"error_message": "スペルミスがあります"}
        guidance_dict = service.provide_error_guidance(dict_context)

        assert guidance_dict.guidance_type == GuidanceType.ERROR_RESOLUTION
        assert "スペルミスがあります" in guidance_dict.steps[0].description

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_provide_progress_guidance_next_stage(self, service: object, mock_progress_report: object) -> None:
        """進捗ベースガイダンス提供テスト(次段階あり)"""
        guidance = service.provide_progress_guidance(mock_progress_report)

        assert guidance.guidance_type == GuidanceType.PROGRESS_BASED
        assert guidance.title == "進捗に基づくガイダンス"
        assert guidance.target_stage == WorkflowStageType.CHAPTER_PLOT
        assert len(guidance.steps) == 1
        assert "章別プロットの作成" in guidance.steps[0].title
        assert "novel plot chapter 1" in guidance.steps[0].command

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_provide_progress_guidance_all_completed(self, service: object) -> None:
        """進捗ベースガイダンス提供テスト(全完了)"""
        completed_report = Mock()
        completed_report.stage_statuses = {
            WorkflowStageType.MASTER_PLOT: ProgressStatus.COMPLETED,
            WorkflowStageType.CHAPTER_PLOT: ProgressStatus.COMPLETED,
            WorkflowStageType.EPISODE_PLOT: ProgressStatus.COMPLETED,
        }

        guidance = service.provide_progress_guidance(completed_report)

        assert guidance.guidance_type == GuidanceType.SUCCESS_NEXT_STEPS
        assert guidance.title == "完了"
        assert len(guidance.steps) == 1
        assert "全て完了" in guidance.steps[0].title
        assert guidance.steps[0].is_completed

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_initialize_template_mappings(self, service: object) -> None:
        """テンプレートマッピング初期化テスト"""
        mappings = service.template_mappings

        assert "企画書.yaml" in mappings
        assert mappings["企画書.yaml"] == "企画書テンプレート.yaml"
        assert "キャラクター.yaml" in mappings
        assert mappings["キャラクター.yaml"] == "キャラクター設定テンプレート.yaml"

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_initialize_command_templates(self, service: object) -> None:
        """コマンドテンプレート初期化テスト"""
        commands = service.command_templates

        assert "master_plot" in commands
        assert commands["master_plot"] == "novel plot master"
        assert "chapter_plot" in commands
        assert commands["chapter_plot"] == "novel plot chapter"

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_guidance_step_completion_marking(self) -> None:
        """ガイダンスステップの完了マーキングテスト"""
        step = GuidanceStep(
            step_number=1,
            title="テストステップ",
            description="テスト用のステップです",
            command="test command",
            time_estimation=TimeEstimation.from_minutes(10),
        )

        # 初期状態は未完了
        assert not step.is_completed

        # 完了マーク
        step.mark_as_completed()
        assert step.is_completed

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_complex_error_context_handling(self, service: object) -> None:
        """複雑なエラーコンテキスト処理テスト"""
        # 複数の不足ファイルを持つコンテキスト
        complex_context = Mock()
        complex_context.is_prerequisite_error.return_value = True
        complex_context.missing_files = [
            "10_企画/企画書.yaml",
            "30_設定集/キャラクター.yaml",
            "30_設定集/世界観.yaml",
            "20_プロット/全体構成.yaml",
        ]
        complex_context.affected_stage = WorkflowStageType.CHAPTER_PLOT
        complex_context.error_type = "complex_missing"
        complex_context.get_user_experience_level.return_value = "advanced"
        complex_context.get_project_type.return_value = "sf"

        guidance = service.generate_prerequisite_guidance(complex_context)

        assert len(guidance.steps) == 4
        assert guidance.target_stage == WorkflowStageType.CHAPTER_PLOT
        assert guidance.context_info["user_experience"] == "advanced"

        # ステップ番号が順番になっているか確認
        for i, step in enumerate(guidance.steps, 1):
            assert step.step_number == i

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_time_estimation_consistency(self, service: object) -> None:
        """時間見積もりの一貫性テスト"""
        # 企画書作成ステップ
        step1 = service._create_file_creation_step(1, "10_企画/企画書.yaml", WorkflowStageType.MASTER_PLOT)
        assert step1.time_estimation.minutes == 45

        # キャラクター設定ステップ(より時間がかかる)
        step2 = service._create_file_creation_step(2, "30_設定集/キャラクター.yaml", WorkflowStageType.MASTER_PLOT)
        assert step2.time_estimation.minutes == 60

        # 世界観設定ステップ(最も時間がかかる)
        step3 = service._create_file_creation_step(3, "30_設定集/世界観.yaml", WorkflowStageType.MASTER_PLOT)
        assert step3.time_estimation.minutes == 90

        # 時間の順序が適切か確認
        assert step1.time_estimation.minutes < step2.time_estimation.minutes < step3.time_estimation.minutes

    @pytest.mark.spec("SPEC-WORKFLOW-002")
    def test_edge_case_empty_missing_files(self, service: object) -> None:
        """エッジケース:不足ファイルが空の場合"""
        context = Mock()
        context.is_prerequisite_error.return_value = True
        context.missing_files = []  # 空のリスト
        context.affected_stage = WorkflowStageType.MASTER_PLOT
        context.error_type = "empty_missing"
        context.get_user_experience_level.return_value = "intermediate"
        context.get_project_type.return_value = "mystery"

        guidance = service.generate_prerequisite_guidance(context)

        assert len(guidance.steps) == 0
        assert guidance.guidance_type == GuidanceType.PREREQUISITE_MISSING
        assert guidance.title == "全体構成作成のための前準備"
