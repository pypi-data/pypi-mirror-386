#!/usr/bin/env python3
"""YAMLプロットリポジトリ実装

YAMLファイルとしてプロットを永続化
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.plot_repository import PlotRepository
from noveler.infrastructure.factories.path_service_factory import create_path_service


class YamlPlotRepository(PlotRepository):
    """YAMLベースのプロットリポジトリ実装"""

    def __init__(self, project_root: Path | str) -> None:
        """Args:
        project_root: プロジェクトのルートディレクトリ
        """
        self.project_root = Path(project_root)

    def exists(self, path: str | Path) -> bool:
        """プロットファイルが存在するか確認"""
        full_path = self.project_root / path
        return full_path.exists() and full_path.is_file()

    def _exists_path(self, path: str | Path) -> bool:
        """内部用: パスの存在確認"""
        full_path = self.project_root / path
        return full_path.exists() and full_path.is_file()

    def load(self, path: str | Path) -> dict[str, Any]:
        """プロットファイルを読み込む"""
        full_path = self.project_root / path

        if not full_path.exists():
            msg = f"プロットファイルが見つかりません: {path}"
            raise FileNotFoundError(msg)

        try:
            with full_path.Path(encoding="utf-8").open() as f:
                content = yaml.safe_load(f)
                if content is None:
                    return {}
                return content
        except yaml.YAMLError as e:
            msg = f"YAMLの解析に失敗しました: {e!s}"
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"ファイルの読み込みに失敗しました: {e!s}"
            raise ValueError(msg) from e

    def save(self, path: str | Path, content: dict[str, Any]) -> None:
        """プロットファイルを保存"""
        full_path = self.project_root / path

        # ディレクトリが存在しない場合は作成
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with full_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump(
                content,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

    def find_episode_plot(self, project_name: str, episode_number: int) -> dict[str, Any] | None:
        """エピソードのプロット情報を取得"""
        path = f"{project_name}/プロット/エピソード/第{episode_number:03d}話.yaml"
        if self._exists_path(path):
            return self.load(path)
        return None

    def find_chapter_plot(self, project_name: str, chapter_number: int) -> dict[str, Any] | None:
        """章のプロット情報を取得"""
        path = f"{project_name}/プロット/章別プロット/第{chapter_number}章.yaml"
        if self._exists_path(path):
            return self.load(path)
        return None

    def save_episode_plot(self, project_name: str, episode_number: int, plot_data: dict[str, Any]) -> None:
        """エピソードのプロット情報を保存"""
        path = f"{project_name}/プロット/エピソード/第{episode_number:03d}話.yaml"
        self.save(path, plot_data)

    def get_all_episode_plots(self, project_name: str) -> list[dict[str, Any]]:
        """プロジェクトの全話プロットを取得"""
        episode_dir = self.project_root / project_name / "プロット" / "エピソード"
        plots = []

        if episode_dir.exists():
            for yaml_file in sorted(episode_dir.glob("第*.yaml")):
                try:
                    plot_data: dict[str, Any] = self.load(str(yaml_file.relative_to(self.project_root)))
                    plots.append(plot_data)
                except Exception:
                    # エラーが発生したファイルはスキップ
                    continue

        return plots

    def find_all_episodes(self) -> list[dict[str, Any]]:
        """全エピソードのプロット情報を取得"""
        all_episodes = []

        # プロジェクトディレクトリを検索
        for project_dir in self.project_root.iterdir():
            if project_dir.is_dir():
                episode_plots = self.get_all_episode_plots(project_dir.name)
                all_episodes.extend(episode_plots)

        return all_episodes

    def find_episode_plot_by_number(self, episode_number: int) -> dict[str, Any] | None:
        """エピソード番号でプロット情報を取得"""
        # プロジェクトディレクトリを検索
        for project_dir in self.project_root.iterdir():
            if project_dir.is_dir():
                episode_plot = self.find_episode_plot(project_dir.name, episode_number)
                if episode_plot:
                    return episode_plot

        return None

    def load_master_plot(self, project_root: Path | str) -> dict[str, Any]:
        """全体構成(マスタープロット)を読み込む"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        master_plot_file = path_service.get_plots_dir() / "全体構成.yaml"

        if not master_plot_file.exists():
            msg = f"全体構成.yamlが見つかりません: {master_plot_file}"
            raise FileNotFoundError(msg)

        try:
            with Path(master_plot_file).open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            msg = f"全体構成.yamlの読み込みに失敗しました: {e}"
            raise OSError(msg) from e

    def get_chapter_plot_files(self, project_root: Path | str) -> list[Path]:
        """章別プロットファイルのリストを取得"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        chapter_plot_dir = path_service.get_plots_dir() / "章別プロット"

        if not chapter_plot_dir.exists():
            return []

        # 章別プロットファイルを収集(第N章.yaml形式)
        return sorted(chapter_plot_dir.glob("第*章.yaml"))

    def load_chapter_plot(self, chapter_file: Path | str) -> dict[str, Any]:
        """章別プロットファイルを読み込む"""
        chapter_file = Path(chapter_file)

        if not chapter_file.exists():
            msg = f"章別プロットファイルが見つかりません: {chapter_file}"
            raise FileNotFoundError(msg)

        try:
            with Path(chapter_file).open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            msg = f"章別プロットファイルの読み込みに失敗しました: {e}"
            raise OSError(msg) from e
