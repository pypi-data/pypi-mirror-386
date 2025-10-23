#!/usr/bin/env python3
"""YAMLベースのプロットバージョンリポジトリ実装
永続化層の実装
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.plot_version_entities import PlotVersion
from noveler.domain.repositories import PlotVersionRepository
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class YamlPlotVersionRepository(PlotVersionRepository):
    """YAMLファイルを使用したプロットバージョンリポジトリ"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        path_service = create_path_service(project_root)
        self.plot_dir = path_service.get_plot_dir()
        self.version_file = self.plot_dir / "プロットバージョン管理.yaml"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """必要なディレクトリを作成"""
        self.plot_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Interface compatibility shims
    # ------------------------------------------------------------------
    def find_by_id(self, version_id: str) -> PlotVersion | None:
        """IDによる検索: YAMLではバージョン番号をIDとして扱う"""

        return self.find_by_version(version_id)

    def find_by_plot_id(self, plot_id: str) -> list[PlotVersion]:
        """プロット単位のバージョン一覧を取得"""

        # YAMLファイルは単一プロットを前提としているため全件を返す
        return self.find_all()

    def get_latest_version(self, plot_id: str) -> PlotVersion | None:
        """最新バージョンを取得"""

        versions = self.find_all()
        return versions[-1] if versions else None

    def save(self, plot_version: PlotVersion) -> None:
        """プロットバージョンを保存"""
        # 既存データを読み込み
        data = self._load_data()

        # バージョン情報を追加
        version_data: dict[str, Any] = {
            "date": plot_version.created_at.strftime("%Y-%m-%d"),
            "author": plot_version.author,
            "major_changes": plot_version.major_changes,
            "affected_chapters": plot_version.affected_chapters,
            "git_tag": plot_version.git_tag,
            "git_commit_range": plot_version.git_commit_range,
        }

        # 前バージョンがある場合
        if plot_version.previous_version:
            version_data["previous_version"] = plot_version.previous_version.version_number

        data["versions"][plot_version.version_number] = version_data

        # メタデータを更新
        data["metadata"]["current_version"] = plot_version.version_number
        data["metadata"]["last_updated"] = project_now().datetime.isoformat()

        # 保存
        self._save_data(data)

    def find_by_version(self, version_number: str) -> PlotVersion | None:
        """バージョン番号でプロットバージョンを検索"""
        data = self._load_data()

        if version_number not in data.get("versions", {}):
            return None

        return self._convert_to_entity(version_number, data)

    def find_all(self) -> list[PlotVersion]:
        """全てのプロットバージョンを取得"""
        data = self._load_data()
        versions = []

        for version_number in data.get("versions", {}):
            entity = self._convert_to_entity(version_number, data)
            if entity:
                versions.append(entity)

        # バージョン番号でソート
        versions.sort(key=lambda v: v.version_number)
        return versions

    def get_current(self) -> PlotVersion | None:
        """現在のプロットバージョンを取得"""
        data = self._load_data()
        current_version = data.get("metadata", {}).get("current_version")

        if not current_version:
            return None

        return self.find_by_version(current_version)

    def _load_data(self) -> dict:
        """YAMLファイルからデータを読み込み"""
        if not self.version_file.exists():
            return {
                "metadata": {
                    "created_at": project_now().datetime.isoformat(),
                    "current_version": None,
                },
                "versions": {},
            }

        with Path(self.version_file).open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _save_data(self, data: dict[str, Any]) -> None:
        """データをYAMLファイルに保存"""
        with Path(self.version_file).open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def _convert_to_entity(self, version_number: str, data: dict[str, Any]) -> PlotVersion | None:
        """YAMLデータをエンティティに変換"""
        version_data: dict[str, Any] = data["versions"].get(version_number)
        if not version_data:
            return None

        # 日付を解析
        date_str = version_data.get("date", "")
        created_at = datetime.strptime(date_str, "%Y-%m-%d") if date_str else project_now().datetime

        # 前バージョンを取得
        previous_version = None
        if "previous_version" in version_data:
            previous_version = self.find_by_version(version_data["previous_version"])

        return PlotVersion(
            version_number=version_number,
            created_at=created_at,
            author=version_data.get("author", ""),
            major_changes=version_data.get("major_changes", []),
            affected_chapters=version_data.get("affected_chapters", []),
            git_tag=version_data.get("git_tag"),
            git_commit_range=version_data.get("git_commit_range"),
            previous_version=previous_version,
        )
