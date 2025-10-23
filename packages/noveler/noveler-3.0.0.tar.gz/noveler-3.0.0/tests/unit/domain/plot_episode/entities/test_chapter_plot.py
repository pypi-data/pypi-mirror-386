"""章別プロットエンティティのテスト

SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

import pytest
pytestmark = pytest.mark.plot_episode

from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.value_objects.chapter_number import ChapterNumber


class TestChapterPlot:
    """章別プロットエンティティのテストクラス"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_plot_creation_success(self) -> None:
        """章別プロット作成成功テスト"""
        # Given: 有効な章別プロット情報
        chapter_number = ChapterNumber(1)
        title = "ch01 出会いと冒険の始まり"
        summary = "主人公が新しい世界に踏み出す章"
        key_events = ["転生", "能力発覚", "仲間との出会い"]
        episodes = [
            {"episode_number": 1, "title": "第1話のタイトル", "summary": "第1話の概要"},
            {"episode_number": 2, "title": "第2話のタイトル", "summary": "第2話の概要"},
        ]
        central_theme = "新しい世界への適応と成長"
        viewpoint_management = {
            "primary_pov_character": "主人公",
            "complexity_level": "低",
            "special_conditions": [],
        }

        # When: 章別プロットを作成
        chapter_plot = ChapterPlot(
            chapter_number=chapter_number,
            title=title,
            summary=summary,
            key_events=key_events,
            episodes=episodes,
            central_theme=central_theme,
            viewpoint_management=viewpoint_management,
        )

        # Then: 正しく作成される
        assert chapter_plot.chapter_number == chapter_number
        assert chapter_plot.title == title
        assert chapter_plot.summary == summary
        assert chapter_plot.key_events == key_events
        assert chapter_plot.episodes == episodes
        assert chapter_plot.central_theme == central_theme
        assert chapter_plot.viewpoint_management == viewpoint_management

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_plot_get_episode_info_success(self) -> None:
        """エピソード情報取得成功テスト"""
        # Given: エピソード情報を含む章別プロット
        chapter_plot = ChapterPlot(
            chapter_number=ChapterNumber(1),
            title="ch01テスト",
            summary="テスト概要",
            key_events=["イベント1"],
            episodes=[
                {"episode_number": 1, "title": "第1話", "summary": "第1話概要"},
                {"episode_number": 2, "title": "第2話", "summary": "第2話概要"},
            ],
            central_theme="テーマ",
            viewpoint_management={},
        )

        # When: 特定のエピソード情報を取得
        episode_info = chapter_plot.get_episode_info(1)

        # Then: 正しいエピソード情報が返される
        assert episode_info is not None
        assert episode_info["episode_number"] == 1
        assert episode_info["title"] == "第1話"
        assert episode_info["summary"] == "第1話概要"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_plot_get_episode_info_not_found(self) -> None:
        """エピソード情報取得失敗テスト(存在しないエピソード)"""
        # Given: エピソード情報を含む章別プロット
        chapter_plot = ChapterPlot(
            chapter_number=ChapterNumber(1),
            title="ch01テスト",
            summary="テスト概要",
            key_events=["イベント1"],
            episodes=[
                {"episode_number": 1, "title": "第1話", "summary": "第1話概要"},
            ],
            central_theme="テーマ",
            viewpoint_management={},
        )

        # When: 存在しないエピソード情報を取得
        episode_info = chapter_plot.get_episode_info(99)

        # Then: Noneが返される
        assert episode_info is None

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_plot_contains_episode_true(self) -> None:
        """エピソード包含チェック成功テスト"""
        # Given: エピソード情報を含む章別プロット
        chapter_plot = ChapterPlot(
            chapter_number=ChapterNumber(1),
            title="ch01テスト",
            summary="テスト概要",
            key_events=["イベント1"],
            episodes=[
                {"episode_number": 1, "title": "第1話", "summary": "第1話概要"},
                {"episode_number": 2, "title": "第2話", "summary": "第2話概要"},
            ],
            central_theme="テーマ",
            viewpoint_management={},
        )

        # When & Then: エピソード包含チェック
        assert chapter_plot.contains_episode(1) is True
        assert chapter_plot.contains_episode(2) is True
        assert chapter_plot.contains_episode(3) is False

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_plot_get_context_for_episode(self) -> None:
        """エピソード用コンテキスト取得テスト"""
        # Given: 章別プロット
        chapter_plot = ChapterPlot(
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

        # When: エピソード1のコンテキストを取得
        context = chapter_plot.get_context_for_episode(1)

        # Then: 適切なコンテキストが返される
        assert context is not None
        assert context["chapter_info"]["title"] == "ch01 出会いと冒険の始まり"
        assert context["chapter_info"]["central_theme"] == "新しい世界への適応と成長"
        assert context["episode_info"]["title"] == "第1話"
        assert context["episode_info"]["summary"] == "転生シーン"
        assert "key_events" in context["chapter_info"]
        assert "viewpoint_management" in context["chapter_info"]
