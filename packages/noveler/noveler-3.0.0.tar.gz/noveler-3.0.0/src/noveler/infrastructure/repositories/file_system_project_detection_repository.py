"""ファイルシステムプロジェクト検出リポジトリ実装."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.project_detection_repository import ProjectDetectionRepository


class FileSystemProjectDetectionRepository(ProjectDetectionRepository):
    """ファイルシステムを使用したプロジェクト検出リポジトリ実装."""

    def __init__(self, cache_path: Path | None) -> None:
        """初期化.

        Args:
            cache_path: キャッシュファイルのパス
        """
        self.cache_path = cache_path or Path.cwd() / ".project_cache.json"
        self._project_indicators = {
            "プロジェクト設定.yaml",
            "project_config.yaml",
            "pyproject.toml",
            "package.json",
            ".git",
            "requirements.txt",
            "Pipfile",
            "setup.py",
            "Cargo.toml",
        }

    def detect_project_root(self, start_path: Path) -> Path | None:
        """プロジェクトルートを検出.

        Args:
            start_path: 検出開始パス

        Returns:
            プロジェクトルート、見つからない場合はNone
        """
        current = start_path.resolve()

        # 親ディレクトリを遡って検索
        for parent in [current, *list(current.parents)]:
            if self._is_project_root(parent):
                return parent

        return None

    def get_project_type(self, project_root: Path) -> str:
        """プロジェクトタイプを取得.

        Args:
            project_root: プロジェクトルートパス

        Returns:
            プロジェクトタイプ
        """
        if not project_root.exists():
            return "unknown"

        # 小説プロジェクト
        if (project_root / "プロジェクト設定.yaml").exists():
            return "novel"

        # Python プロジェクト
        if (project_root / "pyproject.toml").exists():
            return "python"

        if (project_root / "setup.py").exists():
            return "python"

        if (project_root / "requirements.txt").exists():
            return "python"

        # Node.js プロジェクト
        if (project_root / "package.json").exists():
            return "nodejs"

        # Rust プロジェクト
        if (project_root / "Cargo.toml").exists():
            return "rust"

        # Git リポジトリ
        if (project_root / ".git").exists():
            return "git"

        return "generic"

    def is_valid_project(self, project_path: Path) -> bool:
        """有効なプロジェクトかどうか判定.

        Args:
            project_path: プロジェクトパス

        Returns:
            有効なプロジェクトの場合True
        """
        if not project_path.exists() or not project_path.is_dir():
            return False

        return self._is_project_root(project_path)

    def list_projects_in_directory(self, directory: Path) -> list[Path]:
        """ディレクトリ内のプロジェクト一覧を取得.

        Args:
            directory: 検索対象ディレクトリ

        Returns:
            プロジェクトパスのリスト
        """
        if not directory.exists() or not directory.is_dir():
            return []

        projects = []

        try:
            # 直下のディレクトリを検索
            projects.extend(item for item in directory.iterdir() if item.is_dir() and self._is_project_root(item))

            # サブディレクトリも1階層だけ検索
            for item in directory.iterdir():
                if item.is_dir() and not self._is_project_root(item):
                    projects.extend(
                        subitem for subitem in item.iterdir() if subitem.is_dir() and self._is_project_root(subitem)
                    )

        except (OSError, PermissionError):
            pass

        return sorted(projects)

    def get_project_metadata(self, project_root: Path) -> dict[str, str]:
        """プロジェクトメタデータを取得.

        Args:
            project_root: プロジェクトルートパス

        Returns:
            メタデータ辞書
        """
        metadata = {
            "path": str(project_root),
            "type": self.get_project_type(project_root),
            "name": project_root.name,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

        # 小説プロジェクトの場合、設定ファイルから情報を取得
        if metadata["type"] == "novel":
            config_path = project_root / "プロジェクト設定.yaml"
            if config_path.exists():
                try:
                    # import yaml # Moved to top-level

                    with config_path.Path(encoding="utf-8").open() as f:
                        config = yaml.safe_load(f) or {}

                    if "プロジェクト" in config:
                        project_info = config["プロジェクト"]
                        metadata["title"] = project_info.get("タイトル", project_root.name)
                        metadata["author"] = project_info.get("作者", "")
                        metadata["genre"] = project_info.get("ジャンル", "")

                except Exception:
                    pass

        return metadata

    def cache_project_info(self, project_root: Path) -> None:
        """プロジェクト情報をキャッシュ.

        Args:
            project_root: プロジェクトルートパス
        """
        cache_data: dict[str, Any] = self._load_cache()

        project_key = str(project_root)
        metadata = self.get_project_metadata(project_root)

        cache_data[project_key] = metadata

        self._save_cache(cache_data)

    def get_cached_projects(self) -> list[dict[str, str]]:
        """キャッシュされたプロジェクト一覧を取得.

        Returns:
            プロジェクト情報のリスト
        """
        cache_data: dict[str, Any] = self._load_cache()
        return list(cache_data.values())

    def clear_cache(self) -> None:
        """キャッシュをクリア."""
        if self.cache_path.exists():
            self.cache_path.unlink()

    def _is_project_root(self, path: Path) -> bool:
        """プロジェクトルートかどうか判定.

        Args:
            path: 判定対象パス

        Returns:
            プロジェクトルートの場合True
        """
        if not path.exists() or not path.is_dir():
            return False

        # 指標ファイル/ディレクトリの存在確認
        return any((path / indicator).exists() for indicator in self._project_indicators)

    def _load_cache(self) -> dict[str, dict[str, str]]:
        """キャッシュを読み込み."""
        if not self.cache_path.exists():
            return {}

        try:
            with self.cache_path.Path(encoding="utf-8").open() as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_cache(self, cache_data: dict[str, dict[str, str]]) -> None:
        """キャッシュを保存."""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.Path("w").open(encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
