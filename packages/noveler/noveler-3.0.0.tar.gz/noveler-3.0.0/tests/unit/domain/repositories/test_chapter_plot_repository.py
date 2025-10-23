"""章別プロットリポジトリのテスト

from noveler.domain.exceptions.chapter_plot_exceptions import ChapterPlotNotFoundError
SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

import pytest

from unittest.mock import Mock


from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.value_objects.chapter_number import ChapterNumber


class TestChapterPlotRepository:
    """章別プロットリポジトリのテストクラス"""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """モックリポジトリのフィクスチャ"""
        return Mock()

    @pytest.fixture
    def sample_chapter_plot(self) -> ChapterPlot:
        """サンプル章別プロットのフィクスチャ"""
        return ChapterPlot(
            chapter_number=ChapterNumber(1),
            title="ch01 出会いと冒険の始まり",
            summary="主人公が新しい世界に踏み出す章",
            key_events=["転生", "能力発覚", "仲間との出会い"],
            episodes=[
                {"episode_number": 1, "title": "第1話", "summary": "転生シーン"},
                {"episode_number": 2, "title": "第2話", "summary": "能力発覚"},
            ],
            central_theme="新しい世界への適応と成長",
            viewpoint_management={
                "primary_pov_character": "主人公",
                "complexity_level": "低",
            },
        )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_find_by_chapter_number_success(
        self,
        mock_repository: Mock,
        sample_chapter_plot: ChapterPlot,
    ) -> None:
        """章番号による章別プロット取得成功テスト"""
        # Given: モックリポジトリの設定
        chapter_number = ChapterNumber(1)
        mock_repository.find_by_chapter_number.return_value = sample_chapter_plot

        # When: 章別プロットを取得
        result = mock_repository.find_by_chapter_number(chapter_number)

        # Then: 正しい章別プロットが返される
        assert result == sample_chapter_plot
        mock_repository.find_by_chapter_number.assert_called_once_with(chapter_number)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_find_by_chapter_number_not_found(self, mock_repository: Mock) -> None:
        """章番号による章別プロット取得失敗テスト"""
        # Given: 存在しない章番号でモックを設定
        chapter_number = ChapterNumber(99)
        mock_repository.find_by_chapter_number.side_effect = ChapterPlotNotFoundError(
            f"章別プロットが見つかりません: {chapter_number}"
        )

        # When & Then: 例外が発生
        with pytest.raises(ChapterPlotNotFoundError):
            mock_repository.find_by_chapter_number(chapter_number)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_find_by_episode_number_success(
        self,
        mock_repository: Mock,
        sample_chapter_plot: ChapterPlot,
    ) -> None:
        """エピソード番号による章別プロット取得成功テスト"""
        # Given: モックリポジトリの設定
        episode_number = 1
        mock_repository.find_by_episode_number.return_value = sample_chapter_plot

        # When: エピソード番号で章別プロットを取得
        result = mock_repository.find_by_episode_number(episode_number)

        # Then: 正しい章別プロットが返される
        assert result == sample_chapter_plot
        mock_repository.find_by_episode_number.assert_called_once_with(episode_number)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_find_by_episode_number_not_found(self, mock_repository: Mock) -> None:
        """エピソード番号による章別プロット取得失敗テスト"""
        # Given: 存在しないエピソード番号でモックを設定
        episode_number = 99
        mock_repository.find_by_episode_number.side_effect = ChapterPlotNotFoundError(
            f"エピソード{episode_number}を含む章別プロットが見つかりません"
        )

        # When & Then: 例外が発生
        with pytest.raises(ChapterPlotNotFoundError):
            mock_repository.find_by_episode_number(episode_number)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_exists_success(self, mock_repository: Mock) -> None:
        """章別プロット存在確認成功テスト"""
        # Given: 存在確認のモック設定
        chapter_number = ChapterNumber(1)
        mock_repository.exists.return_value = True

        # When: 存在確認
        result = mock_repository.exists(chapter_number)

        # Then: Trueが返される
        assert result is True
        mock_repository.exists.assert_called_once_with(chapter_number)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_exists_failure(self, mock_repository: Mock) -> None:
        """章別プロット存在確認失敗テスト"""
        # Given: 存在しない章番号でモック設定
        chapter_number = ChapterNumber(99)
        mock_repository.exists.return_value = False

        # When: 存在確認
        result = mock_repository.exists(chapter_number)

        # Then: Falseが返される
        assert result is False
        mock_repository.exists.assert_called_once_with(chapter_number)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_list_all_success(self, mock_repository: Mock, sample_chapter_plot: ChapterPlot) -> None:
        """全章別プロット一覧取得成功テスト"""
        # Given: 複数の章別プロットでモック設定
        chapter_plots = [sample_chapter_plot]
        mock_repository.list_all.return_value = chapter_plots

        # When: 全章別プロット取得
        result = mock_repository.list_all()

        # Then: 正しいリストが返される
        assert result == chapter_plots
        mock_repository.list_all.assert_called_once()

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_list_all_empty(self, mock_repository: Mock) -> None:
        """全章別プロット一覧取得(空)テスト"""
        # Given: 空のリストでモック設定
        mock_repository.list_all.return_value = []

        # When: 全章別プロット取得
        result = mock_repository.list_all()

        # Then: 空のリストが返される
        assert result == []
        mock_repository.list_all.assert_called_once()
