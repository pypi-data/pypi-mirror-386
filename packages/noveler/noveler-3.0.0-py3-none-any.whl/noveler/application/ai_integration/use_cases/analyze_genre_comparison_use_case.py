#!/usr/bin/env python3
"""ジャンル比較分析ユースケース

プロジェクト設定に基づいてジャンル比較分析を実行
"""

from typing import Any

from noveler.domain.ai_integration.entities.published_work import SuccessLevel
from noveler.domain.ai_integration.value_objects.genre_benchmark_result import GenreBenchmarkResult
from noveler.domain.ai_integration.value_objects.genre_configuration import (
    GenreConfiguration,
    MainGenre,
    SubGenre,
    TargetFormat,
)
from noveler.domain.repositories.ai_analysis_repository import AIAnalysisRepository
from noveler.domain.repositories.plot_repository import PlotRepository


class ProjectConfigNotFoundError(Exception):
    """プロジェクト設定が見つからない場合のエラー"""


class PublishedWorkDataNotFoundError(Exception):
    """書籍化作品データが見つからない場合のエラー"""


class InsufficientDataError(Exception):
    """分析に必要なデータが不足している場合のエラー"""


class AnalyzeGenreComparisonUseCase:
    """ジャンル比較分析ユースケース

    プロジェクト設定.yamlからジャンル情報を読み込み、
    書籍化作品との比較分析を実行
    """

    def __init__(self, plot_repository: PlotRepository, analysis_repository: AIAnalysisRepository) -> None:
        """初期化

        Args:
            plot_repository: プロットリポジトリ
            analysis_repository: 分析結果リポジトリ
        """
        self.plot_repository = plot_repository
        self.analysis_repository = analysis_repository

    def execute(self, _plot_path: str, project_config: dict[str, Any]) -> GenreBenchmarkResult:
        """ジャンル比較分析を実行

        Args:
            plot_path: プロットファイルパス
            project_config: プロジェクト設定
            published_works: 書籍化作品リスト
            options: オプション設定
            use_cache: キャッシュを使用するか

        Returns:
            ジャンル比較分析結果

        Raises:
            ProjectConfigNotFoundError: プロジェクト設定が見つからない
            PublishedWorkDataNotFoundError: 書籍化作品データが見つからない
            InsufficientDataError: 分析に必要なデータが不足
        """
        # プロジェクト設定からジャンル情報を抽出
        genre_config: dict[str, Any] = self._extract_genre_configuration(project_config)

        # TODO: 実装が未完成のため、デフォルト結果を返す
        return GenreBenchmarkResult(
            genre_config=genre_config, analysis_scores={}, recommendations=[], comparison_data={}
        )

    def get_genre_statistics(
        self, project_config: dict[str, Any], published_works: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """ジャンル統計情報を取得

        Args:
            project_config: プロジェクト設定
            published_works: 書籍化作品リスト

        Returns:
            ジャンル統計情報
        """
        genre_config: dict[str, Any] = self._extract_genre_configuration(project_config)

        # 基本統計
        basic_stats = self.genre_pattern_matcher.get_genre_statistics(
            genre_config,
            published_works,
        )

        # 競合分析
        competition_analysis = self.genre_pattern_matcher.analyze_competition(
            genre_config,
            published_works,
        )

        return {
            "genre_combination": genre_config.get_genre_combination(),
            "basic_statistics": basic_stats,
            "competition_analysis": competition_analysis,
        }

    def get_recent_analyses(self, project_path: str, limit: int) -> list[GenreBenchmarkResult]:
        """最近の分析結果を取得

        Args:
            project_path: プロジェクトパス
            limit: 取得件数制限

        Returns:
            最近の分析結果リスト
        """
        return self.analysis_repository.get_recent_analyses(project_path, limit)

    def _extract_genre_configuration(self, project_config: dict[str, Any]) -> GenreConfiguration:
        """プロジェクト設定からジャンル設定を抽出"""
        genre_section = project_config.get("ジャンル")
        if not genre_section:
            msg = "プロジェクト設定にジャンル情報が見つかりません"
            raise ProjectConfigNotFoundError(msg)

        try:
            # enum値に変換

            main_genre_str = genre_section.get("メイン", "")
            main_genre = self._find_main_genre(main_genre_str)

            sub_genres_str = genre_section.get("サブ", [])
            sub_genres = [self._find_sub_genre(sg) for sg in sub_genres_str]

            target_format_str = genre_section.get("ターゲット", "")
            target_format = self._find_target_format(target_format_str)

            return GenreConfiguration(
                main_genre=main_genre,
                sub_genres=sub_genres,
                target_format=target_format,
            )

        except Exception as e:
            msg = f"ジャンル設定の解析に失敗しました: {e}"
            raise ProjectConfigNotFoundError(msg) from e

    def _find_main_genre(self, genre_str: str) -> MainGenre:
        """メインジャンル文字列をenumに変換"""
        for genre in MainGenre:
            if genre.value == genre_str:
                return genre

        msg = f"未知のメインジャンル: {genre_str}"
        raise ValueError(msg)

    def _find_sub_genre(self, genre_str: str) -> SubGenre:
        """サブジャンル文字列をenumに変換"""
        for genre in SubGenre:
            if genre.value == genre_str:
                return genre

        msg = f"未知のサブジャンル: {genre_str}"
        raise ValueError(msg)

    def _find_target_format(self, format_str: str) -> TargetFormat:
        """ターゲットフォーマット文字列をenumに変換"""
        for format_type in TargetFormat:
            if format_type.value == format_str:
                return format_type

        msg = f"未知のターゲットフォーマット: {format_str}"
        raise ValueError(msg)

    def _load_plot_data(self, plot_path: str) -> dict[str, Any]:
        """プロットデータを読み込み"""
        if not self.plot_repository.exists(plot_path):
            msg = f"プロットファイルが見つかりません: {plot_path}"
            raise FileNotFoundError(msg)

        return self.plot_repository.load(plot_path)

    def _get_min_success_level(self, options: dict[str, Any]) -> SuccessLevel:
        """オプションから最低成功レベルを取得"""
        level_str = options.get("min_success_level", "C級")

        level_map = {
            "S級": SuccessLevel.S_TIER,
            "A級": SuccessLevel.A_TIER,
            "B級": SuccessLevel.B_TIER,
            "C級": SuccessLevel.C_TIER,
        }

        return level_map.get(level_str, SuccessLevel.C_TIER)
