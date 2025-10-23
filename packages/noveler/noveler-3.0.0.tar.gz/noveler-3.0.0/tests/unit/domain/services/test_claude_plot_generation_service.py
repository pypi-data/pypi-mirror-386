"""Claude プロット生成サービスのテスト

SPEC-PLOT-001: Claude Code連携プロット生成システム
統合サービス対応: 個別機能テストとして維持
"""

from unittest.mock import MagicMock, patch

import pytest

from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.entities.generated_episode_plot import GeneratedEpisodePlot
from noveler.domain.interfaces.claude_session_interface import (
    ClaudeSessionExecutorInterface,
    EnvironmentDetectorInterface,
)
from noveler.domain.services.claude_plot_generation_service import (
    ClaudePlotGenerationService,
    PlotGenerationError,
)
from noveler.domain.value_objects.chapter_number import ChapterNumber


class TestClaudePlotGenerationService:
    """Claude プロット生成サービスのテストクラス"""

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

    @pytest.fixture
    def claude_service(self) -> ClaudePlotGenerationService:
        """Claude プロット生成サービスのフィクスチャ"""
        session_executor = MagicMock(spec=ClaudeSessionExecutorInterface)
        session_executor.is_available.return_value = True
        session_executor.execute_prompt.return_value = {"success": True, "data": "{}"}

        environment_detector = MagicMock(spec=EnvironmentDetectorInterface)
        environment_detector.is_claude_code_environment.return_value = True
        environment_detector.get_current_project_name.return_value = "テストプロジェクト"

        return ClaudePlotGenerationService(session_executor, environment_detector)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_generate_episode_plot_success(
        self,
        claude_service: ClaudePlotGenerationService,
        sample_chapter_plot: ChapterPlot,
    ) -> None:
        """エピソードプロット生成成功テスト(個別機能テスト)"""
        # Given: Claude Code連携のモック
        mock_response = {
            "episode_number": 1,
            "title": "第1話 異世界転生",
            "summary": "主人公が異世界に転生し、新しい力に目覚める",
            "scenes": [
                {"scene_number": 1, "title": "転生の瞬間", "description": "主人公の転生シーン"},
                {"scene_number": 2, "title": "新世界の認識", "description": "異世界の環境を理解"},
            ],
            "key_events": ["転生完了", "能力発覚", "世界理解"],
            "viewpoint": "主人公視点",
            "tone": "驚きと希望",
            "conflict": "新環境への適応",
            "resolution": "基本的な世界理解の獲得",
        }

        with patch.object(claude_service, "_call_claude_code") as mock_claude_call:
            mock_claude_call.return_value = mock_response

            # When: エピソードプロット生成
            result = claude_service.generate_episode_plot(sample_chapter_plot, 1)

            # Then: 正しい生成プロットが返される
            assert isinstance(result, GeneratedEpisodePlot)
            assert result.episode_number == 1
            assert result.title == "第1話 異世界転生"
            assert result.summary == "主人公が異世界に転生し、新しい力に目覚める"
            assert len(result.scenes) == 2
            assert result.scenes[0]["title"] == "転生の瞬間"
            assert result.generation_timestamp is not None
            assert result.source_chapter_number == 1

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_generate_episode_plot_episode_not_in_chapter(
        self,
        claude_service: ClaudePlotGenerationService,
        sample_chapter_plot: ChapterPlot,
    ) -> None:
        """エピソードが章に含まれていない場合のテスト"""
        # Given: 章に含まれていないエピソード番号
        episode_number = 99

        # When & Then: 例外が発生
        with pytest.raises(PlotGenerationError, match="エピソード99はchapter01に含まれていません"):
            claude_service.generate_episode_plot(sample_chapter_plot, episode_number)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_generate_episode_plot_claude_error(
        self,
        claude_service: ClaudePlotGenerationService,
        sample_chapter_plot: ChapterPlot,
    ) -> None:
        """Claude Code呼び出しエラーのテスト"""
        # Given: Claude Code呼び出しでエラーが発生する設定
        with patch.object(claude_service, "_call_claude_code") as mock_claude_call:
            mock_claude_call.side_effect = Exception("Claude Code API Error")

            # When & Then: 例外が発生
            with pytest.raises(PlotGenerationError, match="Claude Codeでのプロット生成に失敗しました"):
                claude_service.generate_episode_plot(sample_chapter_plot, 1)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_build_generation_prompt_success(
        self,
        claude_service: ClaudePlotGenerationService,
        sample_chapter_plot: ChapterPlot,
    ) -> None:
        """プロット生成プロンプト構築成功テスト"""
        # Given: 章別プロットとエピソード番号
        episode_number = 1

        # When: プロンプトを構築
        prompt = claude_service._build_generation_prompt(sample_chapter_plot, episode_number)

        # Then: 適切なプロンプトが構築される
        assert isinstance(prompt, str)
        assert "ch01 出会いと冒険の始まり" in prompt
        assert "第1話" in prompt
        assert "転生シーン" in prompt
        assert "新しい世界への適応と成長" in prompt
        assert "主人公" in prompt
        assert "YAML形式で出力してください" in prompt

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_validate_claude_response_success(
        self,
        claude_service: ClaudePlotGenerationService,
    ) -> None:
        """Claude レスポンス検証成功テスト"""
        # Given: 有効なレスポンス
        valid_response = {
            "episode_number": 1,
            "title": "第1話 テスト",
            "summary": "テスト概要",
            "scenes": [{"scene_title": "シーン1", "description": "説明1"}],
            "key_events": ["イベント1"],
            "viewpoint": "主人公視点",
            "tone": "明るい",
            "conflict": "問題",
            "resolution": "解決",
        }

        # When: レスポンス検証
        result = claude_service._validate_claude_response(valid_response, 1)

        # Then: 検証が成功する
        assert result is True

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_validate_claude_response_missing_fields(
        self,
        claude_service: ClaudePlotGenerationService,
    ) -> None:
        """Claude レスポンス検証失敗テスト(必須フィールド不足)"""
        # Given: 必須フィールドが不足しているレスポンス
        invalid_response = {
            "episode_number": 1,
            "title": "第1話 テスト",
            # summary が不足
            "scenes": [],
        }

        # When & Then: 検証が失敗する
        with pytest.raises(PlotGenerationError, match="必須フィールドが不足しています"):
            claude_service._validate_claude_response(invalid_response, 1)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_validate_claude_response_episode_number_mismatch(
        self,
        claude_service: ClaudePlotGenerationService,
    ) -> None:
        """Claude レスポンス検証失敗テスト(エピソード番号不一致)"""
        # Given: エピソード番号が一致しないレスポンス
        invalid_response = {
            "episode_number": 2,  # 期待値は1
            "title": "第1話 テスト",
            "summary": "テスト概要",
            "scenes": [],
            "key_events": [],
            "viewpoint": "視点",
            "tone": "トーン",
            "conflict": "問題",
            "resolution": "解決",
        }

        # When & Then: 検証が失敗する
        with pytest.raises(PlotGenerationError, match="エピソード番号が一致しません"):
            claude_service._validate_claude_response(invalid_response, 1)
