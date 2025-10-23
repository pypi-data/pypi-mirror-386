"""生成エピソードプロットエンティティのテスト

SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

from datetime import datetime
from typing import Any

import pytest

from noveler.domain.entities.generated_episode_plot import GeneratedEpisodePlot
from noveler.domain.value_objects.project_time import project_now


class TestGeneratedEpisodePlot:
    """生成エピソードプロットエンティティのテストクラス"""

    @pytest.fixture
    def sample_claude_response(self) -> dict[str, Any]:
        """サンプルClaude Codeレスポンスのフィクスチャ"""
        return {
            "title": "第001話 異世界転生",
            "summary": "主人公が異世界に転生し、新しい力に目覚める",
            "scenes": [
                {"scene_title": "転生の瞬間", "description": "主人公の転生シーン"},
                {"scene_title": "新世界の認識", "description": "異世界の環境を理解"},
            ],
            "key_events": ["転生完了", "能力発覚", "世界理解"],
            "viewpoint": "主人公視点",
            "tone": "驚きと希望",
            "conflict": "新環境への適応",
            "resolution": "基本的な世界理解の獲得",
        }

    @pytest.fixture
    def sample_generated_plot(self) -> GeneratedEpisodePlot:
        """サンプル生成エピソードプロットのフィクスチャ"""
        return GeneratedEpisodePlot(
            episode_number=1,
            title="第001話 異世界転生",
            summary="主人公が異世界に転生し、新しい力に目覚める",
            scenes=[
                {"scene_title": "転生の瞬間", "description": "主人公の転生シーン"},
                {"scene_title": "新世界の認識", "description": "異世界の環境を理解"},
            ],
            key_events=["転生完了", "能力発覚", "世界理解"],
            viewpoint="主人公視点",
            tone="驚きと希望",
            conflict="新環境への適応",
            resolution="基本的な世界理解の獲得",
            generation_timestamp=project_now().datetime,
            source_chapter_number=1,
        )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_generated_episode_plot_creation_success(self, sample_generated_plot: GeneratedEpisodePlot) -> None:
        """生成エピソードプロット作成成功テスト"""
        # Given & When: サンプル生成プロット
        plot = sample_generated_plot

        # Then: 正しく作成される
        assert plot.episode_number == 1
        assert plot.title == "第001話 異世界転生"
        assert plot.summary == "主人公が異世界に転生し、新しい力に目覚める"
        assert len(plot.scenes) == 2
        assert plot.scenes[0]["scene_title"] == "転生の瞬間"
        assert plot.key_events == ["転生完了", "能力発覚", "世界理解"]
        assert plot.viewpoint == "主人公視点"
        assert plot.tone == "驚きと希望"
        assert plot.conflict == "新環境への適応"
        assert plot.resolution == "基本的な世界理解の獲得"
        assert plot.source_chapter_number == 1
        assert isinstance(plot.generation_timestamp, datetime)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_generated_episode_plot_creation_failure_invalid_episode_number(self) -> None:
        """生成エピソードプロット作成失敗テスト(無効なエピソード番号)"""
        # Given & When & Then: 無効なエピソード番号でエラー
        with pytest.raises(ValueError, match="エピソード番号は1以上である必要があります"):
            GeneratedEpisodePlot(
                episode_number=0,  # 無効
                title="テスト",
                summary="テスト概要",
                scenes=[],
                key_events=[],
                viewpoint="視点",
                tone="トーン",
                conflict="問題",
                resolution="解決",
                generation_timestamp=project_now().datetime,
                source_chapter_number=1,
            )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_generated_episode_plot_creation_failure_empty_title(self) -> None:
        """生成エピソードプロット作成失敗テスト(空のタイトル)"""
        # Given & When & Then: 空のタイトルでエラー
        with pytest.raises(ValueError, match="タイトルは空であってはいけません"):
            GeneratedEpisodePlot(
                episode_number=1,
                title="",  # 空
                summary="テスト概要",
                scenes=[],
                key_events=[],
                viewpoint="視点",
                tone="トーン",
                conflict="問題",
                resolution="解決",
                generation_timestamp=project_now().datetime,
                source_chapter_number=1,
            )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_generated_episode_plot_creation_failure_empty_summary(self) -> None:
        """生成エピソードプロット作成失敗テスト(空の概要)"""
        # Given & When & Then: 空の概要でエラー
        with pytest.raises(ValueError, match="概要は空であってはいけません"):
            GeneratedEpisodePlot(
                episode_number=1,
                title="テスト",
                summary="",  # 空
                scenes=[],
                key_events=[],
                viewpoint="視点",
                tone="トーン",
                conflict="問題",
                resolution="解決",
                generation_timestamp=project_now().datetime,
                source_chapter_number=1,
            )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_from_claude_response_success(self, sample_claude_response: dict[str, Any]) -> None:
        """Claude Codeレスポンスからの作成成功テスト"""
        # Given: サンプルClaude Codeレスポンス
        episode_number = 1
        source_chapter_number = 1

        # When: Claude Codeレスポンスから作成
        plot = GeneratedEpisodePlot.from_claude_response(episode_number, source_chapter_number, sample_claude_response)

        # Then: 正しく作成される
        assert plot.episode_number == episode_number
        assert plot.source_chapter_number == source_chapter_number
        assert plot.title == sample_claude_response["title"]
        assert plot.summary == sample_claude_response["summary"]
        assert plot.scenes == sample_claude_response["scenes"]
        assert plot.key_events == sample_claude_response["key_events"]
        assert plot.viewpoint == sample_claude_response["viewpoint"]
        assert plot.tone == sample_claude_response["tone"]
        assert plot.conflict == sample_claude_response["conflict"]
        assert plot.resolution == sample_claude_response["resolution"]

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_from_claude_response_failure_missing_field(self) -> None:
        """Claude Codeレスポンスからの作成失敗テスト(必須フィールド不足)"""
        # Given: 必須フィールドが不足したレスポンス
        incomplete_response = {
            "title": "テスト",
            "summary": "概要",
            # scenes が不足
            "key_events": [],
            "viewpoint": "視点",
            "tone": "トーン",
            "conflict": "問題",
            "resolution": "解決",
        }

        # When & Then: 例外が発生
        with pytest.raises(ValueError, match="必須フィールドが不足しています: scenes"):
            GeneratedEpisodePlot.from_claude_response(1, 1, incomplete_response)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_to_yaml_dict_success(self, sample_generated_plot: GeneratedEpisodePlot) -> None:
        """YAML辞書変換成功テスト"""
        yaml_dict = sample_generated_plot.to_yaml_dict()

        # Then: 正しい構造で変換される
        episode_info = yaml_dict["episode_info"]
        assert episode_info["episode_number"] == 1
        assert episode_info["title"] == "第001話 異世界転生"
        assert episode_info["chapter_number"] == 1

        # 概要と主要イベントの確認
        assert yaml_dict["synopsis"] == "主人公が異世界に転生し、新しい力に目覚める"
        assert yaml_dict["key_events"][0]["event"] == sample_generated_plot.key_events[0]

        # メタデータの確認
        metadata = yaml_dict["metadata"]
        assert metadata["source"] == "Claude Code Generated"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_get_scene_count(self, sample_generated_plot: GeneratedEpisodePlot) -> None:
        """シーン数取得テスト"""
        # When: シーン数を取得
        scene_count = sample_generated_plot.get_scene_count()

        # Then: 正しいシーン数が返される
        assert scene_count == 2

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_get_key_event_count(self, sample_generated_plot: GeneratedEpisodePlot) -> None:
        """キーイベント数取得テスト"""
        # When: キーイベント数を取得
        key_event_count = sample_generated_plot.get_key_event_count()

        # Then: 正しいキーイベント数が返される
        assert key_event_count == 3

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_has_conflict_resolution_true(self, sample_generated_plot: GeneratedEpisodePlot) -> None:
        """コンフリクト・解決策存在確認テスト(True)"""
        # When: コンフリクト・解決策の存在確認
        has_conflict_resolution = sample_generated_plot.has_conflict_resolution()

        # Then: Trueが返される
        assert has_conflict_resolution is True

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_has_conflict_resolution_false(self) -> None:
        """コンフリクト・解決策存在確認テスト(False)"""
        # Given: コンフリクトまたは解決策が空のプロット
        plot = GeneratedEpisodePlot(
            episode_number=1,
            title="テスト",
            summary="概要",
            scenes=[],
            key_events=[],
            viewpoint="視点",
            tone="トーン",
            conflict="",  # 空
            resolution="解決",
            generation_timestamp=project_now().datetime,
            source_chapter_number=1,
        )

        # When: コンフリクト・解決策の存在確認
        has_conflict_resolution = plot.has_conflict_resolution()

        # Then: Falseが返される
        assert has_conflict_resolution is False

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_get_plot_structure_summary(self, sample_generated_plot: GeneratedEpisodePlot) -> None:
        """プロット構造要約取得テスト"""
        # When: プロット構造要約を取得
        summary = sample_generated_plot.get_plot_structure_summary()

        # Then: 正しい要約が返される
        assert summary["episode_number"] == 1
        assert summary["title"] == "第001話 異世界転生"
        assert summary["scene_count"] == 2
        assert summary["key_event_count"] == 3
        assert summary["viewpoint"] == "主人公視点"
        assert summary["tone"] == "驚きと希望"
        assert summary["has_conflict_resolution"] is True
        assert summary["generation_source"] == "chapter01"
