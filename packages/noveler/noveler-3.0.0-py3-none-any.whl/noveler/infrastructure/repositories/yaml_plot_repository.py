#!/usr/bin/env python3
"""YAMLプロットリポジトリ実装

DDD原則に基づくインフラストラクチャ層
プロット情報をYAMLファイルで永続化
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.plot_repository import MasterPlotData, PlotRepository
from noveler.infrastructure.factories.path_service_factory import create_path_service


class YamlPlotRepository(PlotRepository):
    """YAMLベースのプロットリポジトリ実装"""

    def __init__(self, base_path: Path | str, logger_service=None, console_service=None) -> None:
        """Args:
        base_path: プロジェクトのベースパス
        """
        self.base_path = Path(base_path)

        self.logger_service = logger_service
        self.console_service = console_service
    def find_episode_plot(self, project_name: str, episode_number: int) -> dict[str, Any] | None:
        """エピソードのプロット情報を取得"""
        # 章別プロットディレクトリを探索
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        plot_dir = path_service.get_plots_dir() / "章別プロット"

        if not plot_dir.exists():
            return None

        # 各YAMLファイルを検索
        for yaml_file in plot_dir.glob("*.yaml"):
            try:
                with Path(yaml_file).open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if data and "episodes" in data:
                    for episode in data["episodes"]:
                        if episode.get("episode_number") == f"{episode_number:03d}":
                            return episode
            except Exception:
                continue

        return None

    def find_chapter_plot(self, project_name: str, chapter_number: int) -> dict[str, Any] | None:
        """章のプロット情報を取得"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        plot_dir = path_service.get_plots_dir() / "章別プロット"
        primary_file = plot_dir / f"ch{chapter_number:02d}.yaml"
        fallback_files = [
            plot_dir / f"第{chapter_number}章.yaml",
            plot_dir / f"第{chapter_number:02d}章.yaml",
        ]

        if primary_file.exists():
            plot_file = primary_file
        else:
            plot_file = next((fp for fp in fallback_files if fp.exists()), primary_file)

        if not plot_file.exists():
            return None

        try:
            with Path(plot_file).open(encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def save_episode_plot(self, project_name: str, episode_number: int) -> None:
        """エピソードのプロット情報を保存"""
        # 実装は省略(既存のプロット構造を壊さないため)

    def exists(self, project_name: str, episode_number: int) -> bool:
        """話プロットが存在するか確認"""
        return self.find_episode_plot(project_name, episode_number) is not None

    def get_all_episode_plots(self, project_name: str) -> list[dict[str, Any]]:
        """プロジェクトの全話プロットを取得"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        plot_dir = path_service.get_plots_dir() / "章別プロット"
        all_plots = []

        if not plot_dir.exists():
            return all_plots

        # 各YAMLファイルからエピソードを収集
        for yaml_file in sorted(plot_dir.glob("*.yaml")):
            try:
                with Path(yaml_file).open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if data and "episodes" in data:
                    all_plots.extend(data["episodes"])
            except Exception:
                continue

        # エピソード番号でソート
        all_plots.sort(key=lambda x: x.get("episode_number", "999"))

        return all_plots

    def find_all_episodes(self) -> list[Any]:
        """全エピソードのプロット情報を取得"""
        # TODO: 実装
        return []

    def load_master_plot(self, project_root: Path) -> MasterPlotData:
        """全体構成(マスタープロット)を読み込む"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        master_plot_file = path_service.get_plots_dir() / "全体構成.yaml"

        if not master_plot_file.exists():
            msg = f"全体構成.yamlが見つかりません: {master_plot_file}"
            raise FileNotFoundError(msg)

        try:
            with Path(master_plot_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                # MasterPlotData型に合わせて必要なフィールドを確保
                return {
                    "title": data.get("title", ""),
                    "genre": data.get("genre", ""),
                    "concept": data.get("concept", ""),
                    "chapters": data.get("chapters", []),
                }
        except Exception as e:
            msg = f"全体構成.yamlの読み込みに失敗しました: {e}"
            raise OSError(msg) from e

    def get_chapter_plot_files(self, project_root: Path) -> list[Path]:
        """章別プロットファイルのリストを取得"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        chapter_plot_dir = path_service.get_plots_dir() / "章別プロット"

        if not chapter_plot_dir.exists():
            return []

        # 章別プロットファイルを収集(第N章.yaml形式)
        files = list(chapter_plot_dir.glob("ch*.yaml"))
        if not files:
            files = list(chapter_plot_dir.glob("第*章.yaml"))
        return sorted(files)

    def load_chapter_plot(self, chapter_file: str) -> dict[str, str]:
        """章別プロットファイルを読み込む"""
        chapter_file = Path(chapter_file)

        if not chapter_file.exists():
            msg = f"章別プロットファイルが見つかりません: {chapter_file}"
            raise FileNotFoundError(msg)

        try:
            with Path(chapter_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

                # データが辞書でない場合は空の辞書を返す
                if not isinstance(data, dict):
                    self.console_service.print(f"警告: {chapter_file} のデータが辞書形式ではありません")
                    return {}

                # str型の値のみを含むよう変換
                return {k: str(v) for k, v in data.items() if isinstance(v, str | int | float)}
        except Exception as e:
            msg = f"章別プロットファイルの読み込みに失敗しました: {e}"
            raise OSError(msg) from e

    def find_episode_plot_by_number(self, episode_number: int) -> dict[str, Any] | None:
        """エピソード番号でプロット情報を取得(プロジェクト名なし版)

        Args:
            episode_number: エピソード番号

        Returns:
            プロット情報の辞書、見つからない場合はNone
        """
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        plot_dir = path_service.get_plots_dir() / "章別プロット"

        if not plot_dir.exists():
            return None

        # 各YAMLファイルを検索
        for yaml_file in plot_dir.glob("*.yaml"):
            try:
                with Path(yaml_file).open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if data and "episodes" in data:
                    for episode in data["episodes"]:
                        if episode.get("episode_number") == f"{episode_number:03d}":
                            return episode
            except Exception:
                continue

        return None

    async def find_by_episode_number(self, episode_number: int) -> dict[str, Any] | None:
        """エピソード番号でプロット情報を取得（統合ワークフロー用）

        Args:
            episode_number: エピソード番号

        Returns:
            プロット情報の辞書、見つからない場合はNone
        """
        try:
            # B20準拠: パス管理はPathServiceを使用
            path_service = create_path_service()
            plot_dir = path_service.get_plots_dir() / "話別プロット"

            if not plot_dir.exists():
                return None

            # エピソード番号に対応するファイルを検索
            plot_file_patterns = [
                f"第{episode_number:03d}話*.yaml",
                f"第{episode_number:03d}話*.yml",
                f"episode{episode_number:03d}*.yaml",
                f"{episode_number:03d}*.yaml",
            ]

            for pattern in plot_file_patterns:
                matches = list(plot_dir.glob(pattern))
                if matches:
                    # 最初にマッチしたファイルを読み込み
                    with Path(matches[0]).open(encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                        # エピソード情報を返す（title属性を含む）
                        if data and isinstance(data, dict):
                            return data

            return None

        except Exception:
            # エラー時はNoneを返す
            return None
