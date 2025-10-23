"""プロット進捗管理サービスのテスト

DDD準拠テスト:
    - ビジネスロジックのテスト
- リポジトリパターンのモック化
- 進捗分析アルゴリズムの検証
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from noveler.domain.entities.progress_report import ProgressReport
from noveler.domain.services.plot_progress_service import PlotProgressService
from noveler.domain.value_objects.progress_status import ProgressStatus
from noveler.domain.value_objects.time_estimation import TimeEstimation
from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


pytestmark = pytest.mark.plot_episode


class TestPlotProgressService:
    """PlotProgressServiceのテスト"""

    @pytest.fixture
    def mock_repository(self):
        """プロット進捗リポジトリのモック"""
        repo = Mock()
        repo.get_project_root.return_value = Path("/test/project")
        return repo

    @pytest.fixture
    def service(self, mock_repository: object):
        """サービスインスタンス"""
        return PlotProgressService(mock_repository)

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_analyze_project_progress_not_started(self, service: object, mock_repository: object) -> None:
        """未着手プロジェクトの進捗分析テスト"""
        # リポジトリの返り値を設定
        mock_repository.find_master_plot.return_value = None
        mock_repository.find_chapter_plots.return_value = []
        mock_repository.find_episode_plots.return_value = []

        # 実行
        report = service.analyze_project_progress("test_project")

        # 検証
        assert isinstance(report, ProgressReport)
        assert report.overall_completion == 0
        assert report.stage_statuses[WorkflowStageType.MASTER_PLOT] == ProgressStatus.NOT_STARTED
        assert report.stage_statuses[WorkflowStageType.CHAPTER_PLOT] == ProgressStatus.NOT_STARTED
        assert report.stage_statuses[WorkflowStageType.EPISODE_PLOT] == ProgressStatus.NOT_STARTED
        assert len(report.next_actions) > 0
        assert "マスタープロット" in report.next_actions[0].title

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_analyze_project_progress_master_only(self, service: object, mock_repository: object) -> None:
        """マスタープロットのみ完成の進捗分析テスト"""
        # マスタープロット完成
        mock_repository.find_master_plot.return_value = {"title": "テスト小説", "chapters": [1, 2, 3]}
        mock_repository.calculate_file_completion.return_value = 85  # 高完成度
        mock_repository.find_chapter_plots.return_value = []
        mock_repository.find_episode_plots.return_value = []

        # 実行
        report = service.analyze_project_progress("test_project")

        # 検証
        assert report.overall_completion == 30  # マスタープロットの重み30%
        assert report.stage_statuses[WorkflowStageType.MASTER_PLOT] == ProgressStatus.COMPLETED
        assert report.stage_statuses[WorkflowStageType.CHAPTER_PLOT] == ProgressStatus.NOT_STARTED
        assert len(report.next_actions) > 0
        assert "chapter01" in report.next_actions[0].title

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_analyze_project_progress_in_progress(self, service: object, mock_repository: object) -> None:
        """進行中プロジェクトの進捗分析テスト"""
        # マスタープロット完成
        mock_repository.find_master_plot.return_value = {"title": "テスト小説"}

        # 章別プロット進行中
        mock_repository.find_chapter_plots.return_value = [
            {"chapter": 1, "complete": True},
            {"chapter": 2, "complete": False},
        ]

        # 完成度計算のモック(呼び出し順に応じた返り値)
        mock_repository.calculate_file_completion.side_effect = [
            90,  # マスタープロット
            85,  # ch01
            40,  # ch02(未完成)
        ]

        mock_repository.find_episode_plots.return_value = []
        mock_repository.find_incomplete_chapters.return_value = [2]

        # 実行
        report = service.analyze_project_progress("test_project")

        # 検証
        assert report.overall_completion == 50  # 30% + 20%(章別の半分)
        assert report.stage_statuses[WorkflowStageType.MASTER_PLOT] == ProgressStatus.COMPLETED
        assert report.stage_statuses[WorkflowStageType.CHAPTER_PLOT] == ProgressStatus.IN_PROGRESS
        assert "chapter02" in report.next_actions[0].title

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_analyze_project_progress_all_completed(self, service: object, mock_repository: object) -> None:
        """全完成プロジェクトの進捗分析テスト"""
        # 全て完成
        mock_repository.find_master_plot.return_value = {"complete": True}
        mock_repository.find_chapter_plots.return_value = [{"chapter": i} for i in range(1, 4)]
        mock_repository.find_episode_plots.return_value = [{"episode": i} for i in range(1, 31)]
        mock_repository.calculate_file_completion.return_value = 95  # 全て高完成度

        # 実行
        report = service.analyze_project_progress("test_project")

        # 検証
        assert report.overall_completion == 100
        assert all(status == ProgressStatus.COMPLETED for status in report.stage_statuses.values())
        assert "執筆を開始" in report.next_actions[0].title

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_determine_master_status_various_scores(self, service: object, mock_repository: object) -> None:
        """マスタープロットのステータス判定テスト"""
        # 高スコア
        mock_repository.calculate_file_completion.return_value = 85
        status = service._determine_master_status({"data": "test"})
        assert status == ProgressStatus.COMPLETED

        # 中スコア
        mock_repository.calculate_file_completion.return_value = 50
        status = service._determine_master_status({"data": "test"})
        assert status == ProgressStatus.IN_PROGRESS

        # 低スコア
        mock_repository.calculate_file_completion.return_value = 20
        status = service._determine_master_status({"data": "test"})
        assert status == ProgressStatus.NEEDS_REVIEW

        # データなし
        status = service._determine_master_status(None)
        assert status == ProgressStatus.NOT_STARTED

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_determine_chapters_status(self, service: object, mock_repository: object) -> None:
        """章別プロットのステータス判定テスト"""
        # 全章完成
        chapters = [{"chapter": 1}, {"chapter": 2}, {"chapter": 3}]
        mock_repository.calculate_file_completion.side_effect = [90, 85, 95]
        status = service._determine_chapters_status(chapters)
        assert status == ProgressStatus.COMPLETED

        # 一部進行中
        mock_repository.calculate_file_completion.side_effect = [90, 40, 30]
        status = service._determine_chapters_status(chapters)
        assert status == ProgressStatus.IN_PROGRESS

        # 空リスト
        status = service._determine_chapters_status([])
        assert status == ProgressStatus.NOT_STARTED

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_calculate_overall_completion(self, service: object) -> None:
        """全体完了率計算のテスト"""
        # 全て未着手
        statuses = {
            WorkflowStageType.MASTER_PLOT: ProgressStatus.NOT_STARTED,
            WorkflowStageType.CHAPTER_PLOT: ProgressStatus.NOT_STARTED,
            WorkflowStageType.EPISODE_PLOT: ProgressStatus.NOT_STARTED,
        }
        completion = service._calculate_overall_completion(statuses)
        assert completion == 0

        # マスタープロットのみ完成
        statuses[WorkflowStageType.MASTER_PLOT] = ProgressStatus.COMPLETED
        completion = service._calculate_overall_completion(statuses)
        assert completion == 30  # 重み0.3 * 100%

        # 全て進行中
        statuses = {
            WorkflowStageType.MASTER_PLOT: ProgressStatus.IN_PROGRESS,
            WorkflowStageType.CHAPTER_PLOT: ProgressStatus.IN_PROGRESS,
            WorkflowStageType.EPISODE_PLOT: ProgressStatus.IN_PROGRESS,
        }
        completion = service._calculate_overall_completion(statuses)
        assert completion == 50  # 全て50%

        # 全て完成
        statuses = {
            WorkflowStageType.MASTER_PLOT: ProgressStatus.COMPLETED,
            WorkflowStageType.CHAPTER_PLOT: ProgressStatus.COMPLETED,
            WorkflowStageType.EPISODE_PLOT: ProgressStatus.COMPLETED,
        }
        completion = service._calculate_overall_completion(statuses)
        assert completion == 100

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_suggest_next_actions_master_incomplete(self, service: object) -> None:
        """マスタープロット未完成時の次アクション提案テスト"""
        statuses = {
            WorkflowStageType.MASTER_PLOT: ProgressStatus.IN_PROGRESS,
            WorkflowStageType.CHAPTER_PLOT: ProgressStatus.NOT_STARTED,
            WorkflowStageType.EPISODE_PLOT: ProgressStatus.NOT_STARTED,
        }

        actions = service._suggest_next_actions(statuses, "test_project")

        assert len(actions) == 1
        assert actions[0].title == "マスタープロットを完成させましょう"
        assert actions[0].command == "novel plot master"
        assert actions[0].priority == "high"
        assert isinstance(actions[0].time_estimation, TimeEstimation)

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_suggest_next_actions_chapter_in_progress(self, service: object, mock_repository: object) -> None:
        """章別プロット進行中の次アクション提案テスト"""
        statuses = {
            WorkflowStageType.MASTER_PLOT: ProgressStatus.COMPLETED,
            WorkflowStageType.CHAPTER_PLOT: ProgressStatus.IN_PROGRESS,
            WorkflowStageType.EPISODE_PLOT: ProgressStatus.NOT_STARTED,
        }
        mock_repository.find_incomplete_chapters.return_value = [2, 3]

        actions = service._suggest_next_actions(statuses, "test_project")

        assert len(actions) == 1
        assert "chapter02" in actions[0].title
        assert actions[0].command == "novel plot chapter 2"

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_suggest_next_actions_episode_not_started(self, service: object) -> None:
        """話別プロット未着手時の次アクション提案テスト"""
        statuses = {
            WorkflowStageType.MASTER_PLOT: ProgressStatus.COMPLETED,
            WorkflowStageType.CHAPTER_PLOT: ProgressStatus.COMPLETED,
            WorkflowStageType.EPISODE_PLOT: ProgressStatus.NOT_STARTED,
        }

        actions = service._suggest_next_actions(statuses, "test_project")

        assert len(actions) == 1
        assert "episode001" in actions[0].title
        assert actions[0].command == "novel plot episode 1"

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_get_completion_summary(self, service: object, mock_repository: object) -> None:
        """進捗サマリー文字列生成のテスト"""
        # モックの設定
        mock_repository.find_master_plot.return_value = {"complete": True}
        mock_repository.find_chapter_plots.return_value = [{"chapter": 1}]
        mock_repository.find_episode_plots.return_value = []
        mock_repository.calculate_file_completion.return_value = 85

        # 実行
        summary = service.get_completion_summary("test_project")

        # 検証
        assert "📊 プロット作成進捗:" in summary
        assert "📋 段階別状況:" in summary
        assert "✅" in summary  # 完成マーク
        assert "⚪" in summary  # 未着手マーク
        assert "🔄 推奨される次のステップ:" in summary

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_progress_report_metadata(self, service: object, mock_repository: object) -> None:
        """ProgressReportのメタデータテスト"""
        # 最小限のモック設定
        mock_repository.find_master_plot.return_value = None
        mock_repository.find_chapter_plots.return_value = []
        mock_repository.find_episode_plots.return_value = []

        # 実行
        report = service.analyze_project_progress("test_project")

        # メタデータ検証
        assert report.metadata["version"] == "2.0"
        assert report.metadata["ddd_compliant"] is True
        assert report.metadata["analyzer"] == "PlotProgressService"
        assert report.created_at is not None

        # 作成日時の形式確認
        created_dt = datetime.fromisoformat(report.created_at)
        assert isinstance(created_dt, datetime)

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_next_action_properties(self, service: object) -> None:
        """NextActionオブジェクトのプロパティテスト"""
        statuses = {
            WorkflowStageType.MASTER_PLOT: ProgressStatus.NOT_STARTED,
            WorkflowStageType.CHAPTER_PLOT: ProgressStatus.NOT_STARTED,
            WorkflowStageType.EPISODE_PLOT: ProgressStatus.NOT_STARTED,
        }

        actions = service._suggest_next_actions(statuses, "test_project")
        action = actions[0]

        assert hasattr(action, "title")
        assert hasattr(action, "command")
        assert hasattr(action, "time_estimation")
        assert hasattr(action, "priority")
        assert hasattr(action, "description")  # titleの別名
        assert hasattr(action, "estimated_time")  # time_estimationの別名

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_needs_review_status(self, service: object, mock_repository: object) -> None:
        """NEEDS_REVIEWステータスの処理テスト"""
        # 低完成度でNEEDS_REVIEWになるケース
        mock_repository.find_master_plot.return_value = {"title": "低品質"}
        mock_repository.calculate_file_completion.return_value = 25

        report = service.analyze_project_progress("test_project")

        assert report.stage_statuses[WorkflowStageType.MASTER_PLOT] == ProgressStatus.NEEDS_REVIEW
        # NEEDS_REVIEWは30%として計算される
        assert report.overall_completion == 9  # 30% * 0.3

    @pytest.mark.spec("SPEC-PLOT-002")
    def test_empty_project_handling(self, service: object, mock_repository: object) -> None:
        """空プロジェクトの処理テスト"""
        # 全てNoneまたは空
        mock_repository.find_master_plot.return_value = None
        mock_repository.find_chapter_plots.return_value = []
        mock_repository.find_episode_plots.return_value = []
        mock_repository.get_project_root.return_value = None

        report = service.analyze_project_progress("empty_project")

        # プロジェクトルートはIDがそのまま使われる
        assert report.project_root == "empty_project"
        assert report.overall_completion == 0
        assert len(report.next_actions) > 0
