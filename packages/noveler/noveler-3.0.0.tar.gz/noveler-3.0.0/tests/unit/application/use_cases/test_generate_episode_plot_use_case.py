"""エピソードプロット生成ユースケースのテスト

SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.application.use_cases.generate_episode_plot_use_case import (
    GenerateEpisodePlotDependencies,
    GenerateEpisodePlotRequest,
    GenerateEpisodePlotUseCase,
)
from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.entities.generated_episode_plot import GeneratedEpisodePlot
from noveler.domain.value_objects.chapter_number import ChapterNumber


class TestGenerateEpisodePlotUseCase:
    """エピソードプロット生成ユースケースのテストクラス(統合サービス対応版)"""

    @pytest.fixture
    def mock_unified_plot_service(self) -> Mock:
        """統合プロット生成サービスのモック"""
        mock_service = Mock()
        # 統合サービスの成功レスポンスをモック
        mock_plot = GeneratedEpisodePlot(
            episode_number=1,
            title="第1話_テストプロット",
            summary="テスト用のプロット概要",
            scenes=[{"scene_number": 1, "title": "テストシーン", "description": "テスト内容"}],
            key_events=["テストイベント"],
            viewpoint="主人公視点",
            tone="テストトーン",
            conflict="テスト課題",
            resolution="テスト解決",
            generation_timestamp=datetime.now(timezone.utc),
            source_chapter_number=1,
        )

        mock_service.generate_episode_plot_complete.return_value = mock_plot
        return mock_service

    @pytest.fixture
    def mock_chapter_plot_repository(self) -> Mock:
        """モック章別プロットリポジトリのフィクスチャ(統合サービス対応)"""
        return Mock()

    @pytest.fixture
    def mock_claude_service(self) -> Mock:
        """モックClaude生成サービスのフィクスチャ(統合サービス内部利用)"""
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
    def test_generate_episode_plot_success(
        self,
        mock_unified_plot_service: Mock,
        sample_chapter_plot: ChapterPlot,
    ) -> None:
        """エピソードプロット生成成功テスト(統合サービス対応)"""

        # テスト対象のユースケース作成(統合サービス注入をモック)
        # オリジナルのユースケース実装に対応したテスト
        dependencies = GenerateEpisodePlotDependencies(
            chapter_plot_repository=Mock(), claude_plot_generation_service=Mock()
        )

        use_case = GenerateEpisodePlotUseCase(dependencies)

        request = GenerateEpisodePlotRequest(episode_number=1, project_path=Path("/test/project"), force=False)

        # モック設定
        mock_plot = mock_unified_plot_service.generate_episode_plot_complete.return_value
        dependencies.chapter_plot_repository.find_by_episode_number.return_value = sample_chapter_plot
        dependencies.claude_plot_generation_service.generate_episode_plot.return_value = mock_plot

        with patch.object(use_case, "_save_generated_plot", return_value=True):
            # 実行
            response = use_case.execute(request)

        # 検証
        assert response.success
        assert response.generated_plot is not None
        assert response.generated_plot.episode_number == 1
        assert "テストプロット" in response.generated_plot.title

        # リポジトリとサービスの呼び出し確認
        dependencies.chapter_plot_repository.find_by_episode_number.assert_called_once_with(1)
        dependencies.claude_plot_generation_service.generate_episode_plot.assert_called_once_with(
            sample_chapter_plot, 1
        )

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_generate_episode_plot_with_fallback(
        self,
        mock_unified_plot_service: Mock,
        sample_chapter_plot: ChapterPlot,
    ) -> None:
        """統合サービス失敗時のフォールバック動作テスト"""

        # 統合サービスをNoneレスポンスに設定
        mock_unified_plot_service.generate_episode_plot_complete.return_value = None

        # オリジナルのユースケース実装に対応したテスト
        dependencies = GenerateEpisodePlotDependencies(
            chapter_plot_repository=Mock(), claude_plot_generation_service=Mock()
        )

        use_case = GenerateEpisodePlotUseCase(dependencies)

        request = GenerateEpisodePlotRequest(episode_number=1, project_path=Path("/test/project"), force=False)

        # モック設定(Claudeサービスの失敗をシミュレート)
        dependencies.chapter_plot_repository.find_by_episode_number.return_value = sample_chapter_plot
        from noveler.domain.services.claude_plot_generation_service import PlotGenerationError

        dependencies.claude_plot_generation_service.generate_episode_plot.side_effect = PlotGenerationError(
            "Claude生成失敗"
        )

        # 実行(フォールバック動作)
        response = use_case.execute(request)

        # フォールバック時の動作確認
        # Claude生成に失敗した場合のハンドリング
        assert response is not None
        assert response.success is False
        assert "プロット生成エラー" in response.error_message

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_generate_episode_plot_error_handling(
        self,
        mock_unified_plot_service: Mock,
        sample_chapter_plot: ChapterPlot,
    ) -> None:
        """統合サービスエラー時のエラーハンドリングテスト"""

        # 統合サービスで例外発生をシミュレート
        mock_unified_plot_service.generate_episode_plot_complete.side_effect = Exception("統合サービスエラー")

        # オリジナルのユースケース実装に対応したテスト
        dependencies = GenerateEpisodePlotDependencies(
            chapter_plot_repository=Mock(), claude_plot_generation_service=Mock()
        )

        use_case = GenerateEpisodePlotUseCase(dependencies)

        request = GenerateEpisodePlotRequest(episode_number=1, project_path=Path("/test/project"), force=False)

        # モック設定(一般的な例外発生をシミュレート)
        dependencies.chapter_plot_repository.find_by_episode_number.return_value = sample_chapter_plot
        dependencies.claude_plot_generation_service.generate_episode_plot.side_effect = Exception("Claude生成エラー")

        # 実行
        response = use_case.execute(request)

        # エラーハンドリングの確認
        # 例外が発生した場合、適切にエラーレスポンスが返される
        assert response is not None
        assert response.success is False
        assert "予期しないエラーが発生しました" in response.error_message
