#!/usr/bin/env python3
"""事前執筆チェックユースケースのテスト

TDD+DDD原則に従い、アプリケーション層のユースケーステスト


仕様書: SPEC-APPLICATION-USE-CASES
"""

import pytest

from unittest.mock import Mock


from noveler.application.use_cases.pre_writing_check_use_case import (
    CheckItemInput,
    PreWritingCheckRequest,
    PreWritingCheckUseCase,
)
from noveler.domain.entities.pre_writing_check import CheckItemType
from noveler.domain.exceptions import DomainException


class TestPreWritingCheckUseCase:
    """事前執筆チェックユースケースのテスト"""

    @pytest.fixture
    def mock_episode_repository(self):
        """モックエピソードリポジトリ"""
        return Mock()

    @pytest.fixture
    def mock_project_repository(self):
        """モックプロジェクトリポジトリ"""
        return Mock()

    @pytest.fixture
    def mock_plot_repository(self):
        """モックプロットリポジトリ"""
        return Mock()

    @pytest.fixture
    def mock_scene_repository(self):
        """モックシーンリポジトリ"""
        return Mock()

    @pytest.fixture
    def use_case(
        self,
        mock_episode_repository: object,
        mock_project_repository: object,
        mock_plot_repository: object,
        mock_scene_repository: object,
    ):
        """ユースケースインスタンス"""
        return PreWritingCheckUseCase(
            episode_repository=mock_episode_repository,
            project_repository=mock_project_repository,
            plot_repository=mock_plot_repository,
            scene_repository=mock_scene_repository,
        )

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK_USE_CASE-NEW_CHECK_CREATION")
    def test_new_check_creation(self, use_case: object, mock_project_repository: object) -> None:
        """新規チェックリストが作成できること"""
        # 準備
        mock_project_repository.exists.return_value = True

        input_data = PreWritingCheckRequest(episode_number=5, project_name="テストプロジェクト")

        # 実行
        output = use_case.create_check_list(input_data)

        # 検証
        assert output.success is True
        assert output.episode_number == 5
        assert output.project_name == "テストプロジェクト"
        assert len(output.check_items) == 5
        assert output.completion_rate == 0.0

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK_USE_CASE-UNNAMED")
    def test_unnamed(self, use_case: object, mock_project_repository: object) -> None:
        """存在しないプロジェクトの場合は例外が発生すること"""
        # 準備
        mock_project_repository.exists.return_value = False

        input_data = PreWritingCheckRequest(episode_number=5, project_name="存在しないプロジェクト")

        # 実行・検証
        with pytest.raises(DomainException, match="プロジェクトが存在しません"):
            use_case.create_check_list(input_data)

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK_USE_CASE-EPISODES_FROM_VERIFI")
    def test_episodes_from_verification(self, use_case: object, mock_episode_repository: object) -> None:
        """前話の情報を取得して確認できること"""
        # 準備
        mock_episode = Mock()
        mock_episode.title.value = "前話のタイトル"
        mock_episode.content = "前話の内容..."
        mock_episode.get_metadata.return_value = "前話のクライマックスシーン"

        mock_episode_repository.find_by_number.return_value = mock_episode

        # 実行
        result = use_case.check_previous_flow(project_name="テストプロジェクト", current_episode_number=5)

        # 検証
        assert result["has_previous"] is True
        assert result["previous_title"] == "前話のタイトル"
        assert result["previous_ending"] == "前話のクライマックスシーン"
        assert "suggestions" in result

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK_USE_CASE-1EPISODES_EPISODESCH")
    def test_1episodes_episodescheck(self, use_case: object) -> None:
        """第1話の場合は前話チェックが不要であること"""
        # 実行
        result = use_case.check_previous_flow(project_name="テストプロジェクト", current_episode_number=1)

        # 検証
        assert result["has_previous"] is False
        assert result["skip_reason"] == "第1話のため前話確認は不要"

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK_USE_CASE-ANALYSIS")
    def test_analysis(self, use_case: object, mock_plot_repository: object) -> None:
        """プロット情報から離脱リスクを分析できること"""
        # 準備
        mock_plot = {
            "episode_number": "005",
            "development_pattern": "daily_life",  # 日常回
            "detailed_plot": {
                "opening": {"scene": "朝の平和な風景から始まる"},
                "middle": {"scene": "延々と続く説明シーン"},
            },
        }
        mock_plot_repository.find_episode_plot.return_value = mock_plot

        # 実行
        risks = use_case.analyze_dropout_risks(project_name="テストプロジェクト", episode_number=5)

        # 検証
        assert len(risks) > 0
        assert any("日常回" in risk for risk in risks)
        assert any("説明" in risk for risk in risks)

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK_USE_CASE-GET")
    def test_get(self, use_case: object, mock_scene_repository: object) -> None:
        """重要シーン情報を取得できること"""
        # 準備
        mock_scenes = [
            {
                "scene_id": "climax_001",
                "title": "主人公覚醒シーン",
                "importance_level": "S",
                "sensory_details": {"visual": "光が溢れる演出"},
            },
            {
                "scene_id": "emotional_001",
                "title": "別れのシーン",
                "importance_level": "A",
                "sensory_details": {"auditory": "静寂の中の足音"},
            },
        ]
        mock_scene_repository.find_by_episode.return_value = mock_scenes

        # 実行
        scenes = use_case.get_important_scenes(project_name="テストプロジェクト", episode_number=5)

        # 検証
        assert len(scenes) == 2
        assert scenes[0]["title"] == "主人公覚醒シーン"
        assert scenes[0]["importance_level"] == "S"

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK_USE_CASE-CHECK")
    def test_check(self, use_case: object, mock_project_repository: object) -> None:
        """チェック項目を完了できること"""
        # 準備
        mock_project_repository.exists.return_value = True

        # チェックリスト作成
        create_input = PreWritingCheckRequest(episode_number=5, project_name="テストプロジェクト")
        check_output = use_case.create_check_list(create_input)
        check_id = check_output.check_id

        # チェック項目完了
        complete_input = CheckItemInput(
            check_id=check_id, item_type=CheckItemType.PREVIOUS_FLOW, notes="前話のクライマックスから自然に繋がっている"
        )

        # 実行
        output = use_case.complete_check_item(complete_input)

        # 検証
        assert output.success is True
        assert output.completion_rate == 20.0  # 5項目中1項目完了

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK_USE_CASE-ALL_CHECK_DETERMINE")
    def test_all_check_determine(self, use_case: object, mock_project_repository: object) -> None:
        """全チェック完了後に執筆開始可能と判定されること"""
        # 準備
        mock_project_repository.exists.return_value = True

        # チェックリスト作成
        create_input = PreWritingCheckRequest(episode_number=5, project_name="テストプロジェクト")
        check_output = use_case.create_check_list(create_input)
        check_id = check_output.check_id

        # 全項目を完了
        for item_type in [
            CheckItemType.EPISODE_INFO,
            CheckItemType.PREVIOUS_FLOW,
            CheckItemType.EPISODE_PURPOSE,
            CheckItemType.DROPOUT_RISK,
            CheckItemType.IMPORTANT_SCENE,
        ]:
            complete_input = CheckItemInput(
                check_id=check_id, item_type=item_type, notes=f"{item_type.value}を確認済み"
            )

            use_case.complete_check_item(complete_input)

        # 実行
        result = use_case.validate_for_writing(check_id)

        # 検証
        assert result["can_start_writing"] is True
        assert len(result["issues"]) == 0
        assert result["completion_rate"] == 100.0

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK_USE_CASE-COMPLETE")
    def test_complete(self, use_case: object, mock_project_repository: object) -> None:
        """未完了項目がある場合に警告が出ること"""
        # 準備
        mock_project_repository.exists.return_value = True

        # チェックリスト作成(未完了のまま)
        create_input = PreWritingCheckRequest(episode_number=5, project_name="テストプロジェクト")
        check_output = use_case.create_check_list(create_input)
        check_id = check_output.check_id

        # 実行
        result = use_case.validate_for_writing(check_id)

        # 検証
        assert result["can_start_writing"] is False
        assert len(result["issues"]) > 0
        assert result["completion_rate"] == 0.0

    @pytest.mark.spec("SPEC-PRE_WRITING_CHECK_USE_CASE-CHECK_SAVE")
    def test_check_save(self, use_case: object, mock_project_repository: object) -> None:
        """チェック履歴が保存されること"""
        # 準備
        mock_project_repository.exists.return_value = True

        # チェックリスト作成
        create_input = PreWritingCheckRequest(episode_number=5, project_name="テストプロジェクト")
        use_case.create_check_list(create_input)

        # 実行
        history = use_case.get_check_history(project_name="テストプロジェクト", episode_number=5)

        # 検証
        assert len(history) > 0
        assert history[0]["episode_number"] == 5
        assert history[0]["completion_rate"] == 0.0
