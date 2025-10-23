#!/usr/bin/env python3
"""エピソード管理統合ユースケースのテスト(TDD RED段階)

レガシーEpisodeManagerをDDDアーキテクチャに統合するためのテスト。
ビジネスロジックの分離とドメイン知識の統合を検証。
"""

from unittest.mock import Mock, create_autospec

import pytest

# 実装前なのでImportError が発生する(これが期待される動作)
try:
    from noveler.application.use_cases.episode_management_integration_use_case import (
        CreateEpisodeFromPlotRequest,
        CreateEpisodeFromPlotResponse,
        EpisodeManagementIntegrationUseCase,
        FindNextUnwrittenEpisodeRequest,
        FindNextUnwrittenEpisodeResponse,
    )
    from noveler.domain.entities.episode import Episode, EpisodeStatus
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.plot_repository import PlotRepository
    from noveler.domain.value_objects.episode_number import EpisodeNumber
    from noveler.domain.value_objects.episode_title import EpisodeTitle
    from noveler.domain.value_objects.word_count import WordCount
except ImportError as e:
    # TDD RED段階では実装が存在しないため、仮の定義を作成
    print(f"実装クラスが存在しません(TDD RED段階の期待動作): {e}")

    class EpisodeManagementIntegrationUseCase:
        pass

    class FindNextUnwrittenEpisodeRequest:
        pass

    class FindNextUnwrittenEpisodeResponse:
        pass

    class CreateEpisodeFromPlotRequest:
        pass

    class CreateEpisodeFromPlotResponse:
        pass

    class Episode:
        pass

    class EpisodeStatus:
        UNWRITTEN = "unwritten"
        DRAFT = "draft"

    class EpisodeRepository:
        pass

    class PlotRepository:
        pass

    class EpisodeNumber:
        pass

    class EpisodeTitle:
        pass

    class WordCount:
        pass


class TestEpisodeManagementIntegrationUseCase:
    """エピソード管理統合ユースケースのテスト

    ビジネスルール:
    1. プロットから未執筆エピソードを特定できる
    2. プロット情報からエピソードを自動作成できる
    3. レガシー機能をDDDアーキテクチャで統合する
    4. 適切なエラーハンドリングを行う
    """

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_unnamed(self) -> None:
        """プロットから未執筆エピソードを正常に検索できることを確認"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        plot_repo = create_autospec(PlotRepository)

        # 既存エピソードのモック
        episode_repo.find_all_by_project.return_value = [
            Mock(number=EpisodeNumber(1), status=EpisodeStatus.DRAFT),
            Mock(number=EpisodeNumber(2), status=EpisodeStatus.DRAFT),
        ]

        # プロット情報のモック
        plot_repo.find_all_episodes.return_value = [
            Mock(episode_number=1, title="第1話", status="執筆済み"),
            Mock(episode_number=2, title="第2話", status="執筆済み"),
            Mock(episode_number=3, title="第3話", status="未執筆"),
            Mock(episode_number=4, title="第4話", status="未執筆"),
        ]

        use_case = EpisodeManagementIntegrationUseCase(
            episode_repository=episode_repo,
            plot_repository=plot_repo,
        )

        request = FindNextUnwrittenEpisodeRequest(project_id="project_001")

        # Act
        response = use_case.find_next_unwritten_episode(request)

        # Assert
        assert response.success is True
        assert response.episode_number == 3
        assert response.episode_title == "第3話"
        assert response.plot_available is True

        # リポジトリ呼び出しの確認
        episode_repo.find_all_by_project.assert_called_once_with("project_001")
        plot_repo.find_all_episodes.assert_called_once()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_all(self) -> None:
        """全てのエピソードが執筆済みの場合の処理"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        plot_repo = create_autospec(PlotRepository)

        # 全エピソードが既に存在
        episode_repo.find_all_by_project.return_value = [
            Mock(number=EpisodeNumber(1)),
            Mock(number=EpisodeNumber(2)),
            Mock(number=EpisodeNumber(3)),
        ]

        # プロット情報も全て執筆済み
        plot_repo.find_all_episodes.return_value = [
            Mock(episode_number=1, status="執筆済み"),
            Mock(episode_number=2, status="執筆済み"),
            Mock(episode_number=3, status="執筆済み"),
        ]

        use_case = EpisodeManagementIntegrationUseCase(
            episode_repository=episode_repo,
            plot_repository=plot_repo,
        )

        request = FindNextUnwrittenEpisodeRequest(project_id="project_001")

        # Act
        response = use_case.find_next_unwritten_episode(request)

        # Assert
        assert response.success is True
        assert response.episode_number is None
        assert response.message == "全てのエピソードが執筆済みです"

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_from_creation(self) -> None:
        """プロット情報からエピソードを正常に作成できることを確認"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        plot_repo = create_autospec(PlotRepository)

        # プロット情報のモック
        plot_info = Mock(
            episode_number=3,
            title="第3話:新たな出会い",
            summary="主人公が新たな仲間と出会う重要な話",
            target_words=3000,
            keywords=["出会い", "仲間", "冒険"],
        )

        plot_repo.find_episode_plot.return_value = plot_info

        # エピソードが存在しないことを確認
        episode_repo.find_by_project_and_number.return_value = None

        use_case = EpisodeManagementIntegrationUseCase(
            episode_repository=episode_repo,
            plot_repository=plot_repo,
        )

        request = CreateEpisodeFromPlotRequest(
            project_id="project_001",
            episode_number=3,
            generate_initial_content=True,
        )

        # Act
        response = use_case.create_episode_from_plot(request)

        # Assert
        assert response.success is True
        assert response.episode_number == 3
        assert response.episode_title == "第3話:新たな出会い"
        assert response.created_file_path is not None
        assert response.initial_content_generated is True

        # エピソード保存の確認
        episode_repo.save.assert_called_once()
        saved_episode = episode_repo.save.call_args[0][0]
        assert saved_episode.number.value == 3
        assert saved_episode.title.value == "第3話:新たな出会い"
        assert saved_episode.status == EpisodeStatus.DRAFT

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_duplicatecheck(self) -> None:
        """既に存在するエピソードの重複作成を防止"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        plot_repo = create_autospec(PlotRepository)

        # 既存エピソードのモック
        existing_episode = Mock(
            number=EpisodeNumber(3),
            title=EpisodeTitle("既存の第3話"),
        )

        episode_repo.find_by_project_and_number.return_value = existing_episode

        use_case = EpisodeManagementIntegrationUseCase(
            episode_repository=episode_repo,
            plot_repository=plot_repo,
        )

        request = CreateEpisodeFromPlotRequest(
            project_id="project_001",
            episode_number=3,
        )

        # Act
        response = use_case.create_episode_from_plot(request)

        # Assert
        assert response.success is False
        assert "既に存在します" in response.error_message
        assert response.existing_episode_title == "既存の第3話"

        # 保存が呼ばれないことを確認
        episode_repo.save.assert_not_called()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_error(self) -> None:
        """プロット情報が不足している場合のエラー処理"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        plot_repo = create_autospec(PlotRepository)

        # プロット情報が見つからない
        plot_repo.find_episode_plot.return_value = None
        episode_repo.find_by_project_and_number.return_value = None

        use_case = EpisodeManagementIntegrationUseCase(
            episode_repository=episode_repo,
            plot_repository=plot_repo,
        )

        request = CreateEpisodeFromPlotRequest(
            project_id="project_001",
            episode_number=99,
        )

        # Act
        response = use_case.create_episode_from_plot(request)

        # Assert
        assert response.success is False
        assert "プロット情報が見つかりません" in response.error_message
        assert response.episode_number == 99

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_feature(self) -> None:
        """プロットタイトルの正規化機能をテスト"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        plot_repo = create_autospec(PlotRepository)

        # 特殊文字を含むプロット情報
        plot_info = Mock(
            episode_number=5,
            title="第5話:「魔法の<試練>」~冒険の始まり~",
            summary="特殊文字を含むタイトルのテスト",
            target_words=2500,
        )

        plot_repo.find_episode_plot.return_value = plot_info
        episode_repo.find_by_project_and_number.return_value = None

        use_case = EpisodeManagementIntegrationUseCase(
            episode_repository=episode_repo,
            plot_repository=plot_repo,
        )

        request = CreateEpisodeFromPlotRequest(
            project_id="project_001",
            episode_number=5,
        )

        # Act
        response = use_case.create_episode_from_plot(request)

        # Assert
        assert response.success is True
        # タイトルが適切に正規化されていることを確認
        assert "「」<>" not in response.episode_title
        assert "魔法の試練" in response.episode_title

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_initgenerationfeature(self) -> None:
        """プロット情報から初期コンテンツを生成する機能"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        plot_repo = create_autospec(PlotRepository)

        plot_info = Mock(
            episode_number=1,
            title="第1話:物語の始まり",
            summary="主人公の日常から冒険への転機を描く",
            target_words=3000,
            keywords=["日常", "転機", "冒険"],
            character_focus=["主人公"],
            scene_setting="平和な村",
        )

        plot_repo.find_episode_plot.return_value = plot_info
        episode_repo.find_by_project_and_number.return_value = None

        use_case = EpisodeManagementIntegrationUseCase(
            episode_repository=episode_repo,
            plot_repository=plot_repo,
        )

        request = CreateEpisodeFromPlotRequest(
            project_id="project_001",
            episode_number=1,
            generate_initial_content=True,
        )

        # Act
        response = use_case.create_episode_from_plot(request)

        # Assert
        assert response.success is True
        assert response.initial_content_generated is True

        # 保存されたエピソードの内容を確認
        saved_episode = episode_repo.save.call_args[0][0]
        assert len(saved_episode.content) > 0
        assert "物語の始まり" in saved_episode.content or "主人公" in saved_episode.content

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_new(self) -> None:
        """エピソード作成時の統計情報更新をテスト"""
        # Arrange
        episode_repo = create_autospec(EpisodeRepository)
        plot_repo = create_autospec(PlotRepository)

        plot_info = Mock(
            episode_number=10,
            title="第10話:中間地点",
            summary="物語の中間地点となる重要な話",
            target_words=3500,
        )

        plot_repo.find_episode_plot.return_value = plot_info
        episode_repo.find_by_project_and_number.return_value = None

        # 既存エピソード統計のモック(エピソード作成後の更新済み統計)
        episode_repo.get_statistics.return_value = {
            "total_episodes": 10,
            "total_words": 30500,
            "average_words": 3050,
        }

        use_case = EpisodeManagementIntegrationUseCase(
            episode_repository=episode_repo,
            plot_repository=plot_repo,
        )

        request = CreateEpisodeFromPlotRequest(
            project_id="project_001",
            episode_number=10,
        )

        # Act
        response = use_case.create_episode_from_plot(request)

        # Assert
        assert response.success is True
        assert response.project_statistics is not None
        assert response.project_statistics["total_episodes"] == 10


class TestFindNextUnwrittenEpisodeRequest:
    """未執筆エピソード検索要求のテスト"""

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_creation(self) -> None:
        """要求オブジェクトを正常に作成できることを確認"""
        # Act
        request = FindNextUnwrittenEpisodeRequest(
            project_id="project_001",
            include_plot_info=True,
        )

        # Assert
        assert request.project_id == "project_001"
        assert request.include_plot_info is True


class TestCreateEpisodeFromPlotRequest:
    """プロットからエピソード作成要求のテスト"""

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_creation(self) -> None:
        """要求オブジェクトを正常に作成できることを確認"""
        # Act
        request = CreateEpisodeFromPlotRequest(
            project_id="project_001",
            episode_number=5,
            generate_initial_content=True,
            override_existing=False,
        )

        # Assert
        assert request.project_id == "project_001"
        assert request.episode_number == 5
        assert request.generate_initial_content is True
        assert request.override_existing is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
