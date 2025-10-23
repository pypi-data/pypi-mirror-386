#!/usr/bin/env python3
"""ユーザーガイダンス機能のドメイン層テスト
TDD+DDD統合開発による実装

ビジネスルールをテストコードで表現し、
ユーザビリティ向上のビジネスロジックを検証


仕様書: SPEC-UNIT-TEST
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pytest
import yaml

# スクリプトのルートディレクトリをパスに追加
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from noveler.domain.entities.error_context import ErrorContext, ErrorSeverity
from noveler.domain.entities.progress_report import NextAction, ProgressReport, ProgressStatus
from noveler.domain.entities.user_guidance import GuidanceStep, GuidanceType, UserGuidance
from noveler.domain.repositories.plot_progress_repository import PlotProgressRepository
from noveler.domain.services.plot_progress_service import PlotProgressService
from noveler.domain.services.smart_error_handler_service import SmartErrorHandlerService
from noveler.domain.services.user_guidance_service import UserGuidanceService
from noveler.domain.value_objects.time_estimation import TimeEstimation
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestGuidanceStep(unittest.TestCase):
    """ガイダンスステップのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CREATE_GUIDANCE_STEP")
    def test_create_guidance_step(self) -> None:
        """ガイダンスステップを作成できる"""
        get_common_path_service()
        step = GuidanceStep(
            step_number=1,
            title="企画書作成",
            description="作品のコンセプトを決めましょう",
            command="cp template.yaml project.yaml",
            time_estimation=TimeEstimation.from_minutes(30),
            is_completed=False,
        )

        assert step.step_number == 1
        assert step.title == "企画書作成"
        assert not step.is_completed
        assert step.time_estimation.in_minutes() == 30

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-MARK_STEP_AS_COMPLET")
    def test_mark_step_as_completed(self) -> None:
        """ステップを完了状態にできる"""
        step = GuidanceStep(
            step_number=1,
            title="テスト",
            description="テスト",
            command="test",
            time_estimation=TimeEstimation.from_minutes(10),
        )

        assert not step.is_completed
        step.mark_as_completed()
        assert step.is_completed

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-DETERMINE_STEP_EXECU")
    def test_determine_step_executability(self) -> None:
        """ステップの実行可能性を判定できる"""
        step = GuidanceStep(
            step_number=1,
            title="テスト",
            description="テスト",
            command="test",
            time_estimation=TimeEstimation.from_minutes(10),
            prerequisites=["file1.yaml", "file2.yaml"],
        )

        # 前提条件が満たされていない場合
        assert not step.can_execute(existing_files=[])

        # 前提条件が満たされている場合
        assert step.can_execute(existing_files=["file1.yaml", "file2.yaml"])


class TestUserGuidance(unittest.TestCase):
    """ユーザーガイダンスエンティティのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CREATE_USER_GUIDANCE")
    def test_create_user_guidance(self) -> None:
        """ユーザーガイダンスを作成できる"""
        steps = [
            GuidanceStep(1, "ステップ1", "説明1", "cmd1", TimeEstimation.from_minutes(10)),
            GuidanceStep(2, "ステップ2", "説明2", "cmd2", TimeEstimation.from_minutes(20)),
        ]

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="前提条件不足のガイダンス",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        assert guidance.guidance_type == GuidanceType.PREREQUISITE_MISSING
        assert len(guidance.steps) == 2
        assert guidance.target_stage == WorkflowStageType.MASTER_PLOT

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CALCULATE_TOTAL_DURA")
    def test_calculate_total_duration(self) -> None:
        """全体の所要時間を計算できる"""
        steps = [
            GuidanceStep(1, "ステップ1", "説明1", "cmd1", TimeEstimation.from_minutes(15)),
            GuidanceStep(2, "ステップ2", "説明2", "cmd2", TimeEstimation.from_minutes(25)),
        ]

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="テストガイダンス",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        total_time = guidance.calculate_total_time()
        assert total_time.in_minutes() == 40

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CALCULATE_COMPLETION")
    def test_calculate_completion_rate(self) -> None:
        """完了率を計算できる"""
        steps = [
            GuidanceStep(1, "ステップ1", "説明1", "cmd1", TimeEstimation.from_minutes(10)),
            GuidanceStep(2, "ステップ2", "説明2", "cmd2", TimeEstimation.from_minutes(20)),
        ]
        steps[0].mark_as_completed()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="テストガイダンス",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        completion_rate = guidance.calculate_completion_rate()
        assert completion_rate == 50  # 1/2 = 50%

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-GET_NEXT_STEP")
    def test_get_next_step(self) -> None:
        """次のステップを取得できる"""
        steps = [
            GuidanceStep(1, "ステップ1", "説明1", "cmd1", TimeEstimation.from_minutes(10)),
            GuidanceStep(2, "ステップ2", "説明2", "cmd2", TimeEstimation.from_minutes(20)),
        ]
        steps[0].mark_as_completed()

        guidance = UserGuidance(
            guidance_type=GuidanceType.PREREQUISITE_MISSING,
            title="テストガイダンス",
            steps=steps,
            target_stage=WorkflowStageType.MASTER_PLOT,
        )

        next_step = guidance.get_next_step()
        assert next_step.step_number == 2
        assert next_step.title == "ステップ2"


class TestErrorContext(unittest.TestCase):
    """エラーコンテキストのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CREATE_ERROR_CONTEXT")
    def test_create_error_context(self) -> None:
        """エラーコンテキストを作成できる"""
        context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=WorkflowStageType.MASTER_PLOT,
            missing_files=["file1.yaml", "file2.yaml"],
            user_context={"project_type": "fantasy", "experience_level": "beginner"},
        )

        assert context.error_type == "PREREQUISITE_MISSING"
        assert context.severity == ErrorSeverity.WARNING
        assert len(context.missing_files) == 2
        assert context.user_context["experience_level"] == "beginner"

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-DETERMINE_ERROR_SEVE")
    def test_determine_error_severity(self) -> None:
        """エラーの深刻度を判定できる"""
        warning_context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=WorkflowStageType.MASTER_PLOT,
            missing_files=["file1.yaml"],
        )

        error_context = ErrorContext(
            error_type="SYSTEM_FAILURE",
            severity=ErrorSeverity.ERROR,
            affected_stage=WorkflowStageType.MASTER_PLOT,
            missing_files=[],
        )

        assert not warning_context.is_critical()
        assert error_context.is_critical()

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-GENERATE_USER_MESSAG")
    def test_generate_user_message(self) -> None:
        """ユーザー向けメッセージを生成できる"""
        context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=WorkflowStageType.MASTER_PLOT,
            missing_files=["企画書.yaml"],
            user_context={"experience_level": "beginner"},
        )

        message = context.generate_user_message()
        assert "企画書.yaml" in message
        assert "全体構成" in message
        assert len(message) > 50  # 十分な説明があること


class TestProgressReport(unittest.TestCase):
    """進捗レポートのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_CREATE_PROGRESS_")
    def test_can_create_progress_report(self) -> None:
        """進捗レポートを作成できる"""
        report = ProgressReport(
            project_root=str(Path("/test/project")),
            overall_completion=75,
            stage_statuses={
                WorkflowStageType.MASTER_PLOT: ProgressStatus.COMPLETED,
                WorkflowStageType.CHAPTER_PLOT: ProgressStatus.IN_PROGRESS,
            },
            next_actions=[
                NextAction(
                    title="ch02プロット完成",
                    command="novel plot chapter 2",
                    time_estimation=TimeEstimation.from_minutes(30),
                ),
            ],
        )

        assert report.overall_completion == 75
        assert len(report.stage_statuses) == 2
        assert len(report.next_actions) == 1

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_RECOMMEND_NEXT_A")
    def test_can_recommend_next_action(self) -> None:
        """次のアクションを推奨できる"""
        report = ProgressReport(
            project_root=str(Path("/test/project")),
            overall_completion=50,
            stage_statuses={
                WorkflowStageType.MASTER_PLOT: ProgressStatus.COMPLETED,
            },
            next_actions=[],
        )

        # ビジネスルール: マスタープロット完了後は章別プロットを推奨
        recommended_action = report.recommend_next_action()
        assert recommended_action is not None
        assert "chapter" in recommended_action.command

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_GENERATE_PROGRES")
    def test_can_generate_progress_report_display(self) -> None:
        """進捗レポートの表示を生成できる"""
        report = ProgressReport(
            project_root=str(Path("/test/project")),
            overall_completion=60,
            stage_statuses={
                WorkflowStageType.MASTER_PLOT: ProgressStatus.COMPLETED,
                WorkflowStageType.CHAPTER_PLOT: ProgressStatus.IN_PROGRESS,
            },
            next_actions=[
                NextAction(
                    title="ch01完成",
                    command="novel plot chapter 1",
                    time_estimation=TimeEstimation.from_minutes(20),
                ),
            ],
        )

        display = report.generate_display()
        assert "60%" in display
        assert "完了" in display
        assert "進行中" in display
        assert "novel plot chapter 1" in display


class TestUserGuidanceService(unittest.TestCase):
    """ユーザーガイダンスサービスのテスト"""

    def setUp(self) -> None:
        """テスト前準備"""
        self.service = UserGuidanceService()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        """テスト後クリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_GENERATE_GUIDANC")
    def test_can_generate_guidance_for_insufficient_prerequisites(self) -> None:
        """前提条件不足時のガイダンスを生成できる"""
        error_context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=WorkflowStageType.MASTER_PLOT,
            missing_files=["10_企画/企画書.yaml", "30_設定集/キャラクター.yaml"],
            user_context={"experience_level": "beginner"},
        )

        guidance = self.service.generate_next_steps_guidance(error_context)

        assert guidance.guidance_type == GuidanceType.PREREQUISITE_MISSING
        assert guidance.target_stage == WorkflowStageType.MASTER_PLOT
        assert len(guidance.steps) >= 2  # 不足ファイル分のステップ

        # 各ステップに実行可能なコマンドが含まれていること
        for step in guidance.steps:
            assert len(step.command) > 0
            assert isinstance(step.time_estimation, TimeEstimation)

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_GENERATE_SUCCESS")
    def test_can_generate_success_guidance(self) -> None:
        """成功時のガイダンスを生成できる"""
        context = {
            "completed_stage": WorkflowStageType.MASTER_PLOT,
            "created_files": [Path("/test/全体構成.yaml")],
            "project_characteristics": {"genre": "fantasy", "target_length": 50},
        }

        guidance = self.service.generate_next_steps_guidance(context)

        assert guidance.guidance_type == GuidanceType.SUCCESS_NEXT_STEPS
        assert len(guidance.steps) > 0

        # 次のステップが適切に提案されていること
        first_step = guidance.steps[0]
        assert "chapter" in first_step.command.lower()

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_GENERATE_APPROPR")
    def test_can_generate_appropriate_guidance_by_stage(self) -> None:
        """段階別に適切なガイダンスを生成できる"""
        # マスタープロット段階
        master_context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=WorkflowStageType.MASTER_PLOT,
            missing_files=["10_企画/企画書.yaml"],
        )

        master_guidance = self.service.generate_next_steps_guidance(master_context)
        assert "企画書" in master_guidance.steps[0].title

        # 章別プロット段階
        chapter_context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=WorkflowStageType.CHAPTER_PLOT,
            missing_files=["20_プロット/全体構成.yaml"],
        )

        chapter_guidance = self.service.generate_next_steps_guidance(chapter_context)
        assert "全体構成" in chapter_guidance.steps[0].title


class MockPlotProgressRepository(PlotProgressRepository):
    """テスト用モックリポジトリ"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def read_file_content(self, file_path: Path) -> str:
        if Path(file_path).exists():
            return Path(file_path).read_text(encoding="utf-8")
        return ""

    def parse_yaml_content(self, content: str) -> dict:
        if not content.strip():
            return {}
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError:
            return {}

    def file_exists(self, file_path: Path) -> bool:
        return Path(file_path).exists()

    def list_files(self, directory: Path, pattern: str) -> list[Path]:
        return list(Path(directory).glob(pattern))

    def find_master_plot(self, _project_id: str) -> dict | None:
        path_service = get_common_path_service()
        master_plot_file = self.project_root / str(path_service.get_plots_dir()) / "全体構成.yaml"
        if master_plot_file.exists():
            try:
                with Path(master_plot_file).open(encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception:
                return {"project_info": {"title": "テストプロジェクト"}}
        return None

    def find_chapter_plots(self, _project_id: str) -> list[dict]:
        path_service = get_common_path_service()
        chapter_dir = self.project_root / str(path_service.get_plots_dir()) / "章別プロット"
        chapters = []
        if chapter_dir.exists():
            for yaml_file in sorted(chapter_dir.glob("第*.yaml")):
                try:
                    with Path(yaml_file).open(encoding="utf-8") as f:
                        chapters.append(yaml.safe_load(f))
                except Exception:
                    chapters.append({"chapter_info": {"number": 1, "title": "ch01"}})
        return chapters

    def find_episode_plots(self, _project_id: str) -> list[dict]:
        return []

    def calculate_file_completion(self, data: dict) -> float:
        # 簡易的な完成度計算
        if "project_info" in data:
            # 詳細なコンテンツがある場合は高スコア
            if "genre" in data.get("project_info", {}):
                return 85.0
            return 50.0
        if "chapter_info" in data:
            return 50.0
        return 0.0

    def find_incomplete_chapters(self, _project_id: str) -> list[int]:
        # ch01が未完成と仮定
        return [1]

    def get_project_root(self, _project_id: str) -> str:
        return str(self.project_root)


class TestPlotProgressService(unittest.TestCase):
    """プロット進捗サービスのテスト"""

    def setUp(self) -> None:
        """テスト前準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repository = MockPlotProgressRepository(self.temp_dir)
        self.service = PlotProgressService(self.repository)

        # テスト用ディレクトリ構造を作成
        path_service = get_common_path_service()
        (self.temp_dir / str(path_service.get_plots_dir())).mkdir(parents=True)
        (self.temp_dir / str(path_service.get_plots_dir()) / "章別プロット").mkdir(parents=True)

    def tearDown(self) -> None:
        """テスト後クリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_ANALYZE_PROJECT_")
    def test_can_analyze_project_progress(self) -> None:
        """プロジェクト進捗を分析できる"""
        # マスタープロットファイルを作成
        path_service = get_common_path_service()
        master_plot_file = self.temp_dir / str(path_service.get_plots_dir()) / "全体構成.yaml"
        master_plot_file.write_text("project_info:\n  title: テストプロジェクト\n")

        report = self.service.analyze_project_progress(str(self.temp_dir))

        assert report.project_root == str(self.temp_dir)
        assert report.overall_completion > 0
        assert WorkflowStageType.MASTER_PLOT in report.stage_statuses

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_SUGGEST_NEXT_ACT")
    def test_can_suggest_next_action(self) -> None:
        """次のアクションを提案できる"""
        # マスタープロット完了状態を作成
        path_service = get_common_path_service()
        master_plot_file = self.temp_dir / str(path_service.get_plots_dir()) / "全体構成.yaml"
        detailed_content = """project_info:
  title: テストプロジェクト
  genre: ファンタジー
  target_episodes: 50
  target_audience: 青年層
  completion_date: 2024年末
story_structure:
  theme: 成長と友情の物語
  hook: 異世界に召喚された主人公
  conflict: 魔王軍との戦い
  resolution: 仲間との絆で勝利
character_arcs:
  protagonist:
    name: 田中太郎
    growth: 臆病者から勇者へ
  companion:
    name: エルフのリナ
    role: 魔法使いサポート
plot_progression:
  act1: 異世界召喚と基本設定
  act2: 仲間集めと能力開発
  act3: 最終決戦と成長の証明
world_building:
  setting: 中世ファンタジー世界
  magic_system: 属性魔法
  geography: 大陸と島々
themes_and_messages:
  main_theme: 困難を通じた成長
  sub_theme: 異文化理解と協力"""
        master_plot_file.write_text(detailed_content)

        report = self.service.analyze_project_progress(str(self.temp_dir))
        next_actions = report.next_actions

        assert len(next_actions) > 0
        # マスタープロット完了後は章別プロットを提案
        assert "chapter" in next_actions[0].command

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_CALCULATE_COMPLE")
    def test_can_calculate_completion_rate_accurately(self) -> None:
        """完了率を正確に計算できる"""
        # 部分的に完了した状態を作成
        path_service = get_common_path_service()
        master_plot_file = self.temp_dir / str(path_service.get_plots_dir()) / "全体構成.yaml"
        master_plot_file.write_text("project_info:\n  title: テストプロジェクト\n")

        chapter1_file = self.temp_dir / str(path_service.get_plots_dir()) / "章別プロット" / "chapter01.yaml"
        chapter1_file.write_text("chapter_info:\n  number: 1\n  title: ch01\n")

        report = self.service.analyze_project_progress(str(self.temp_dir))

        assert report.overall_completion > 30  # 何らかの進捗がある
        assert report.overall_completion < 100  # 完了していない


class TestSmartErrorHandlerService(unittest.TestCase):
    """スマートエラーハンドラーサービスのテスト"""

    def setUp(self) -> None:
        """テスト前準備"""
        self.service = SmartErrorHandlerService()

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_GENERATE_CONTEXT")
    def test_can_generate_contextual_error_messages(self) -> None:
        """文脈に応じたエラーメッセージを生成できる"""
        error_context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=WorkflowStageType.MASTER_PLOT,
            missing_files=["10_企画/企画書.yaml"],
            user_context={"experience_level": "beginner", "project_type": "fantasy"},
        )

        message = self.service.generate_smart_error_message(error_context)

        # 技術的詳細ではなく、ユーザーフレンドリーな説明であること
        assert "FileNotFoundError" not in message
        assert "exception" not in message.lower()

        # 具体的な解決策が含まれていること
        assert "企画書" in message
        assert "コマンド" in message
        assert "分" in message  # 所要時間の目安

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_ADJUST_EXPLANATI")
    def test_can_adjust_explanations_for_beginners_and_experts(self) -> None:
        """初心者向けと熟練者向けで説明を調整できる"""
        base_context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=WorkflowStageType.MASTER_PLOT,
            missing_files=["10_企画/企画書.yaml"],
        )

        # 初心者向け
        beginner_context = base_context
        beginner_context.user_context = {"experience_level": "beginner"}
        beginner_message = self.service.generate_smart_error_message(beginner_context)

        # 熟練者向け
        expert_context = base_context
        expert_context.user_context = {"experience_level": "expert"}
        expert_message = self.service.generate_smart_error_message(expert_context)

        # 初心者向けの方が詳細な説明がある
        assert len(beginner_message) > len(expert_message)
        assert "詳細" in beginner_message

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-CAN_PROVIDE_GENRE_OP")
    def test_can_provide_genre_optimized_advice(self) -> None:
        """ジャンル別の最適化されたアドバイスを提供できる"""
        fantasy_context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=WorkflowStageType.MASTER_PLOT,
            missing_files=["30_設定集/世界観.yaml"],
            user_context={"project_type": "fantasy"},
        )

        message = self.service.generate_smart_error_message(fantasy_context)

        # ファンタジー特有のアドバイスが含まれている
        assert "魔法" in message
        assert "世界観" in message


class TestIntegratedUserGuidanceWorkflow(unittest.TestCase):
    """統合ユーザーガイダンスワークフローのテスト"""

    def setUp(self) -> None:
        """テスト前準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.guidance_service = UserGuidanceService()
        self.repository = MockPlotProgressRepository(self.temp_dir)
        self.progress_service = PlotProgressService(self.repository)
        self.error_handler = SmartErrorHandlerService()

    def tearDown(self) -> None:
        """テスト後クリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.spec("SPEC-DOMAIN_USER_GUIDANCE-COMPLETE_GUIDANCE_WO")
    def test_complete_guidance_workflow_operates(self) -> None:
        """完全なガイダンスワークフローが動作する"""
        # 1. エラー発生
        error_context = ErrorContext(
            error_type="PREREQUISITE_MISSING",
            severity=ErrorSeverity.WARNING,
            affected_stage=WorkflowStageType.MASTER_PLOT,
            missing_files=["10_企画/企画書.yaml"],
            user_context={"experience_level": "beginner", "project_type": "fantasy"},
        )

        # 2. スマートエラーメッセージ生成
        error_message = self.error_handler.generate_smart_error_message(error_context)
        assert isinstance(error_message, str)
        assert len(error_message) > 100

        # 3. ガイダンス生成
        guidance = self.guidance_service.generate_next_steps_guidance(error_context)
        assert guidance.target_stage == WorkflowStageType.MASTER_PLOT
        assert len(guidance.steps) > 0

        # 4. 進捗分析
        progress_report = self.progress_service.analyze_project_progress(str(self.temp_dir))
        assert progress_report.project_root == str(self.temp_dir)

        # 5. 統合レポート生成
        integrated_report = self._generate_integrated_report(error_message, guidance, progress_report)
        assert "企画書" in integrated_report
        assert "コマンド" in integrated_report
        assert "%" in integrated_report  # 進捗率

    def _generate_integrated_report(
        self,
        error_message: str,
        guidance: "UserGuidance",
        progress: "ProgressReport",
    ) -> str:
        """統合レポートの生成(テスト用ヘルパー)"""
        return f"""
{error_message}

{guidance.generate_display()}

{progress.generate_display()}
"""


if __name__ == "__main__":
    unittest.main()
