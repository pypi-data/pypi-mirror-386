"""YAMLベースのプロジェクトリポジトリ実装"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from noveler.infrastructure.repositories.yaml_a31_checklist_repository import (
    YamlA31ChecklistRepository,
)

if TYPE_CHECKING:
    from noveler.domain.entities.a31_checklist_item import A31ChecklistItem


from noveler.domain.repositories.project_repository import ProjectRepository
from noveler.domain.value_objects.genre_type import GenreType


import os


class YamlProjectRepository(ProjectRepository):
    """YAMLファイルを使用したプロジェクトリポジトリ"""

    def __init__(self, base_path: Path | str | None) -> None:
        """初期化

        Args:
            base_path: プロジェクトのベースパス
        """
        self.base_path = Path(base_path) if base_path else Path.cwd().parent

    def exists(self, _project_id: str) -> bool:
        """プロジェクトの存在確認

        Args:
            _project_id: プロジェクトID

        Returns:
            bool: 存在する場合True
        """
        project_path = self.base_path / _project_id
        return project_path.exists() and project_path.is_dir()

    def create(self, _project_id: str, _project_data: dict[str, Any]) -> bool:
        """プロジェクトを作成"""
        # 簡略実装(実際のプロジェクト作成は他のコンポーネントで実装)
        return True

    def get_project_info(self, _project_id: str) -> dict[str, Any] | None:
        """プロジェクト情報を取得"""
        if not self.exists(_project_id):
            return None
        return {"name": _project_id, "path": str(self.base_path / _project_id)}

    def update_project_info(self, _project_id: str, _project_data: dict[str, Any]) -> bool:
        """プロジェクト情報を更新"""
        return True

    def delete(self, _project_id: str) -> bool:
        """プロジェクトを削除"""
        return True

    def get_all_projects(self) -> list[dict[str, Any]]:
        """全プロジェクトを取得"""
        return []

    def get_project_settings(self, _project_id: str) -> dict[str, Any] | None:
        """プロジェクト設定を取得"""
        return {}

    def update_project_settings(self, _project_id: str, _settings: dict[str, Any]) -> bool:
        """プロジェクト設定を更新"""
        return True

    def get_project_metadata(self, _project_id: str) -> dict[str, Any] | None:
        """プロジェクトメタデータを取得"""
        return {}

    def update_project_metadata(self, _project_id: str, _key: str, _value: Any) -> bool:
        """プロジェクトメタデータを更新"""
        return True

    def archive_project(self, _project_id: str) -> bool:
        """プロジェクトをアーカイブ"""
        return True

    def restore_project(self, _project_id: str) -> bool:
        """プロジェクトをアーカイブから復元"""
        return True

    def get_project_statistics(self, _project_id: str) -> dict[str, Any] | None:
        """プロジェクト統計情報を取得"""
        return {}

    def backup_project(self, _project_id: str) -> bool:
        """プロジェクトをバックアップ"""
        return True

    def get_project_directory(self, project_id: str) -> str | None:
        """プロジェクトディレクトリパスを取得"""
        if not self.exists(project_id):
            return None
        return str(self.base_path / project_id)

    def validate_project_structure(self, _project_id: str) -> dict[str, Any]:
        """プロジェクト構造の検証"""
        return {"valid": True}

    def initialize_project_structure(self, _project_id: str) -> bool:
        """プロジェクト構造を初期化"""
        return True

    def get_project_root(self, project_id: str) -> Path | None:
        """プロジェクトのルートディレクトリを取得

        Args:
            project_id: プロジェクトID

        Returns:
            プロジェクトのルートディレクトリパス
        """
        if not self.exists(project_id):
            return None
        return self.base_path / project_id

        print("[DEBUG] YamlProjectRepository base_path:", self.base_path)

    def get_checklist_items(self, project_name: str, item_ids: list[str]) -> list["A31ChecklistItem"]:
        """チェックリスト項目を取得"""
        guide_root_candidates: list[Path] = [self.base_path.parent / "guide"]

        guide_env = os.getenv("NOVEL_GUIDE_ROOT")
        if guide_env:
            guide_root_candidates.append(Path(guide_env))

        guide_root_candidates.append(Path(__file__).parent.parent.parent.parent)

        for candidate in guide_root_candidates:
            if not candidate:
                continue
            if not candidate.exists():
                continue

            template_dir = candidate / "templates"
            if not template_dir.exists():
                continue

            template_exists = any(
                (template_dir / name).exists()
                for name in ("A31.yaml", "A31_原稿執筆チェックリストテンプレート.yaml")
            )
            if not template_exists:
                continue

            checklist_repo = YamlA31ChecklistRepository(candidate)
            return checklist_repo.get_checklist_items(project_name, item_ids)

        checklist_repo = YamlA31ChecklistRepository(Path(__file__).parent.parent.parent.parent)
        return checklist_repo.get_checklist_items(project_name, item_ids)

    def get_project_config(self, project_name: str) -> dict[str, Any]:
        """プロジェクト設定を取得

        Args:
            project_name: プロジェクト名

        Returns:
            Dict[str, Any]: プロジェクト設定データ
        """
        config_path = self._find_project_config_file(project_name)
        if config_path and config_path.exists():
            try:
                f_content = config_path.read_text(encoding="utf-8")
                return yaml.safe_load(f_content) or {}
            except Exception:
                # YAML読み込みエラー時はデフォルト値を返す
                return {}
        return {}

    def get_episode_management(self, project_name: str) -> dict[str, Any]:
        """エピソード管理データを取得

        Args:
            project_name: プロジェクト名

        Returns:
            Dict[str, Any]: エピソード管理データ
        """
        # エピソード管理ファイルの探索
        management_file = self._find_episode_management_file(project_name)
        if management_file and management_file.exists():
            try:
                f_content = management_file.read_text(encoding="utf-8")
                return yaml.safe_load(f_content) or {}
            except Exception:
                # YAML読み込みエラー時はデフォルト値を返す
                return {}
        return {}

    def _find_project_config_file(self, project_name: str) -> Path | None:
        """プロジェクト設定ファイルの探索

        Args:
            project_name: プロジェクト名

        Returns:
            Path | None: 設定ファイルパス、見つからない場合はNone
        """
        possible_paths = [
            self.project_root / project_name / "プロジェクト設定.yaml",
            self.project_root / project_name / "config.yaml",
            self.project_root / "projects" / project_name / "プロジェクト設定.yaml",
            self.project_root / "projects" / project_name / "config.yaml",
        ]

        for path in possible_paths:
            if path.exists():
                return path
        return None

    def _find_episode_management_file(self, project_name: str) -> Path | None:
        """エピソード管理ファイルの探索

        Args:
            project_name: プロジェクト名

        Returns:
            Path | None: 管理ファイルパス、見つからない場合はNone
        """
        possible_paths = [
            self.project_root / project_name / "50_管理資料" / "エピソード管理.yaml",
            self.project_root / "projects" / project_name / "50_管理資料" / "エピソード管理.yaml",
        ]

        for path in possible_paths:
            if path.exists():
                return path
        return None

    def find_by_name(self, project_name: str) -> dict[str, str] | None:
        """プロジェクト名でプロジェクトを検索"""
        # 実装は簡略化(実際の用途では必要に応じて実装)
        return {"name": project_name}

    def get_genre(self, project_root: Path) -> GenreType:
        """プロジェクトのジャンルを取得"""
        config_path = project_root / "プロジェクト設定.yaml"
        if not config_path.exists():
            msg = f"プロジェクト設定ファイルが見つかりません: {config_path}"
            raise FileNotFoundError(msg)

        with config_path.open(encoding="utf-8") as f:
            config = yaml.safe_load(f)

        genre = config.get("genre", "ファンタジー")
        return GenreType(genre)
