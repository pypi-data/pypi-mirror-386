#!/usr/bin/env python3
"""YAMLベースの原稿紐付けリポジトリ実装"""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.plot_version_entities import ManuscriptPlotLink, PlotVersion
from noveler.domain.repositories import ManuscriptPlotLinkRepository
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class YamlManuscriptLinkRepository(ManuscriptPlotLinkRepository):
    """YAMLファイルを使用した原稿紐付けリポジトリ"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_root)
        self.management_dir = path_service.get_management_dir()
        self.episode_file = path_service.get_episode_management_file()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """必要なディレクトリを作成"""
        self.management_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Interface compatibility helpers
    # ------------------------------------------------------------------
    def find_by_manuscript_id(self, manuscript_id: str) -> ManuscriptPlotLink | None:
        """原稿IDはエピソード番号とみなして検索"""

        return self.find_by_episode(str(manuscript_id))

    def find_by_plot_id(self, plot_id: str) -> list[ManuscriptPlotLink]:
        """指定したプロットバージョンに紐付くリンクを返す"""

        return [link for link in self.find_all() if link.plot_version.version_number == plot_id]

    def delete_by_manuscript_id(self, manuscript_id: str) -> None:
        """原稿IDに対応する紐付け情報を削除"""

        data = self._load_data()
        if "episodes" not in data:
            return

        manuscript_key = str(manuscript_id)
        if manuscript_key in data["episodes"]:
            del data["episodes"][manuscript_key]
            self._save_data(data)

    def save(self, link: ManuscriptPlotLink) -> None:
        """紐付け情報を保存"""
        data = self._load_data()

        if "episodes" not in data:
            data["episodes"] = {}

        # エピソード情報を更新
        episode_data: dict[str, Any] = data["episodes"].get(link.episode_number, {})
        episode_data.update(
            {
                "plot_version": link.plot_version.version_number,
                "implementation_date": link.implementation_date.isoformat(),
                "git_commit": link.git_commit,
            },
        )

        if link.plot_snapshot:
            episode_data["plot_snapshot"] = link.plot_snapshot

        data["episodes"][link.episode_number] = episode_data

        self._save_data(data)

    def find_by_episode(self, episode_number: int) -> ManuscriptPlotLink | None:
        """エピソード番号で紐付け情報を検索"""
        data = self._load_data()

        episode_data: dict[str, Any] = data.get("episodes", {}).get(episode_number)
        if not episode_data or "plot_version" not in episode_data:
            return None

        # プロットバージョンを作成(簡易実装)
        plot_version = PlotVersion(
            version_number=episode_data["plot_version"],
            created_at=project_now().datetime,  # 仮の値
            author="",
            major_changes=[],
            affected_chapters=[],
        )

        # 実装日を解析
        impl_date_str = episode_data.get("implementation_date", "")
        impl_date = project_now().datetime
        if impl_date_str:
            try:
                impl_date = datetime.fromisoformat(impl_date_str)
            except ValueError:
                try:
                    impl_date = datetime.strptime(impl_date_str, "%Y-%m-%d").replace(tzinfo=JST)
                except ValueError:
                    impl_date = project_now().datetime

        return ManuscriptPlotLink(
            episode_number=episode_number,
            plot_version=plot_version,
            implementation_date=impl_date,
            git_commit=episode_data.get("git_commit", ""),
            plot_snapshot=episode_data.get("plot_snapshot"),
        )

    def find_all(self) -> list[ManuscriptPlotLink]:
        """全ての紐付け情報を取得"""
        data = self._load_data()
        links = []

        for episode_number in data.get("episodes", {}):
            link = self.find_by_episode(episode_number)
            if link:
                links.append(link)

        return links

    def find_outdated(self, current_version: PlotVersion) -> list[ManuscriptPlotLink]:
        """古いバージョンで実装された原稿を検索"""
        all_links = self.find_all()

        return [link for link in all_links if link.is_outdated_for(current_version)]

    def _load_data(self) -> dict:
        """YAMLファイルからデータを読み込み"""
        if not self.episode_file.exists():
            return {}

        with Path(self.episode_file).open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _save_data(self, data: dict[str, Any]) -> None:
        """データをYAMLファイルに保存"""
        with Path(self.episode_file).open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
