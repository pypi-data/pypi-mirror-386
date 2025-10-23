#!/usr/bin/env python3
"""プロット分析の統合テスト

実際のファイルI/Oとドメインロジックの統合をテスト


仕様書: SPEC-INTEGRATION
"""

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from noveler.application.ai_integration.use_cases.analyze_plot_use_case import (
    AnalyzePlotUseCase,
    InvalidPlotFormatError,
    PlotFileNotFoundError,
)
from noveler.domain.ai_integration.services.plot_analysis_service import PlotAnalysisService
from noveler.infrastructure.ai_integration.repositories.json_analysis_repository import JsonAnalysisRepository
from noveler.infrastructure.ai_integration.repositories.yaml_plot_repository import YamlPlotRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestPlotAnalysisIntegration:
    """プロット分析の統合テスト"""

    def setup_method(self) -> None:
        """テスト環境のセットアップ"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # プロットディレクトリを作成
        path_service = get_common_path_service()
        self.plot_dir = self.project_root / str(path_service.get_plots_dir()) / "章別プロット"
        self.plot_dir.mkdir(parents=True, exist_ok=True)

        # 分析結果ディレクトリを作成
        self.analysis_dir = self.project_root / "logs" / "ai_analysis"
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

        # リポジトリとサービスを初期化
        self.plot_repository = YamlPlotRepository(str(self.project_root))
        self.analysis_repository = JsonAnalysisRepository(str(self.analysis_dir))
        self.analysis_service = PlotAnalysisService()

        # ユースケースを初期化
        self.use_case = AnalyzePlotUseCase(
            plot_repository=self.plot_repository,
            analysis_repository=self.analysis_repository,
            analysis_service=self.analysis_service,
        )

    def teardown_method(self) -> None:
        """テスト環境のクリーンアップ"""
        shutil.rmtree(self.temp_dir)

    def test_full_analysis_workflow(self) -> None:
        """完全な分析ワークフローのテスト"""
        # Arrange: プロットファイルを作成
        plot_data = {
            "metadata": {"title": "ch01:始まりの時", "genre": "fantasy", "target_length": 10},
            "structure": {
                "setup": {"description": "平穏な日常の描写", "pages": "1-2"},
                "development": {"events": ["謎の訪問者", "運命の出会い", "最初の試練"]},
                "climax": {"description": "真実の発覚と決断", "emotional_peak": "驚きと決意"},
                "resolution": {"description": "新たな旅立ち", "next_chapter_hook": "未知の世界へ"},
            },
            "characters": {
                "protagonist": {
                    "name": "アレックス",
                    "motivation": "失われた記憶を取り戻す",
                    "arc": "無知から覚醒へ",
                    "conflicts": ["自己認識", "運命との対峙"],
                },
                "mentor": {"name": "賢者エルダー", "role": "導き手", "secret": "主人公の過去を知っている"},
            },
            "themes": {"main_theme": "自己発見の旅", "sub_themes": ["成長", "信頼", "犠牲"]},
        }

        plot_file = self.plot_dir / "chapter01.yaml"
        with Path(plot_file).open("w", encoding="utf-8") as f:
            yaml.dump(plot_data, f, allow_unicode=True)

        plot_path = "20_プロット/章別プロット/chapter01.yaml"

        # Act: 分析を実行
        analysis = self.use_case.execute(plot_path)

        # Assert: 分析結果の検証
        assert analysis is not None
        assert analysis.plot_file_path == plot_path
        assert analysis.is_analyzed()
        assert analysis.result is not None

        result = analysis.result
        assert result.total_score.value >= 70  # 良いプロットなので高スコア
        assert len(result.strengths) > 0
        assert result.overall_advice != ""

        # 分析結果がファイルに保存されていることを確認
        analysis_files = list(self.analysis_dir.glob("*.json"))
        assert len(analysis_files) == 1

    def test_analyze_nonexistent_file(self) -> None:
        """存在しないファイルの分析"""
        # Act & Assert
        with pytest.raises(PlotFileNotFoundError, match=".*"):
            self.use_case.execute("nonexistent.yaml")

    def test_analyze_minimal_plot(self) -> None:
        """最小限のプロット分析"""
        # Arrange
        minimal_plot = {"structure": {"setup": {}, "development": {}, "climax": {}, "resolution": {}}}

        plot_file = self.plot_dir / "minimal.yaml"
        with Path(plot_file).open("w", encoding="utf-8") as f:
            yaml.dump(minimal_plot, f, allow_unicode=True)

        # Act
        analysis = self.use_case.execute("20_プロット/章別プロット/minimal.yaml")

        # Assert
        assert analysis.is_analyzed()
        assert analysis.result.total_score.value < 70  # 最小限なので低スコア
        assert len(analysis.result.improvements) > 0

    def test_cache_functionality(self) -> None:
        """キャッシュ機能のテスト"""
        # Arrange: プロットファイルを作成
        plot_data = {"structure": {"setup": {"description": "test"}}}
        plot_file = self.plot_dir / "cache_test.yaml"
        with Path(plot_file).open("w", encoding="utf-8") as f:
            yaml.dump(plot_data, f, allow_unicode=True)

        plot_path = "20_プロット/章別プロット/cache_test.yaml"

        # Act: 初回分析
        analysis1 = self.use_case.execute(plot_path)

        # プロットファイルを変更
        plot_data["structure"]["setup"]["description"] = "changed"
        with Path(plot_file).open("w", encoding="utf-8") as f:
            yaml.dump(plot_data, f, allow_unicode=True)

        # キャッシュを使用して分析
        analysis2 = self.use_case.execute(plot_path, use_cache=True)

        # Assert: 同じ分析結果が返される
        assert analysis1.id == analysis2.id
        assert analysis1.result.total_score.value == analysis2.result.total_score.value

    def test_recent_analyses_retrieval(self) -> None:
        """最近の分析結果取得テスト"""
        # Arrange: 複数のプロットを分析
        for i in range(3):
            plot_data = {"structure": {"setup": {"description": f"test{i}"}}}
            plot_file = self.plot_dir / f"test{i}.yaml"
            with Path(plot_file).open("w", encoding="utf-8") as f:
                yaml.dump(plot_data, f, allow_unicode=True)

            self.use_case.execute(f"20_プロット/章別プロット/test{i}.yaml")

        # Act: 最近の分析を取得
        recent = self.use_case.get_recent_analyses(limit=2)

        # Assert
        assert len(recent) == 2
        # 新しい順に返される
        assert recent[0].analyzed_at >= recent[1].analyzed_at

    def test_invalid_yaml_handling(self) -> None:
        """無効なYAMLファイルの処理"""
        # Arrange: 無効なYAMLを作成
        invalid_file = self.plot_dir / "invalid.yaml"
        with Path(invalid_file).open("w", encoding="utf-8") as f:
            f.write("{ invalid yaml content :")

        # Act & Assert

        with pytest.raises(InvalidPlotFormatError, match=".*"):
            self.use_case.execute("20_プロット/章別プロット/invalid.yaml")

    def test_japanese_content_handling(self) -> None:
        """日本語コンテンツの処理"""
        # Arrange
        japanese_plot = {
            "metadata": {"title": "ch01:始まりの朝", "genre": "ファンタジー"},
            "structure": {
                "setup": {"description": "平和な村の日常"},
                "development": {"events": ["謎の旅人", "古い予言", "運命の出会い"]},
                "climax": {"description": "村を襲う危機"},
                "resolution": {"description": "主人公の決意"},
            },
            "characters": {"protagonist": {"name": "太郎", "motivation": "村を守りたい"}},
            "themes": {"main_theme": "勇気と成長", "sub_themes": ["友情", "家族愛"]},
        }

        plot_file = self.plot_dir / "chapter01.yaml"
        with Path(plot_file).open("w", encoding="utf-8") as f:
            yaml.dump(japanese_plot, f, allow_unicode=True)

        # Act
        analysis = self.use_case.execute("20_プロット/章別プロット/chapter01.yaml")

        # Assert
        assert analysis.is_analyzed()
        assert analysis.result.total_score.value > 0
