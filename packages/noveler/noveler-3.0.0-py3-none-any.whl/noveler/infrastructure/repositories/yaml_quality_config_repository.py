"""YAML品質設定リポジトリ"""

import shutil
from pathlib import Path
from typing import Any

import yaml

from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class YamlQualityConfigRepository:
    """YAML形式の品質設定リポジトリ"""

    CONFIG_FILE_NAME = "品質チェック設定.yaml"
    RECORD_FILE_NAME = "品質記録.yaml"

    def exists(self, project_root: Path) -> bool:
        path_service = create_path_service()
        """品質設定ファイルが存在するか確認"""
        path_service = create_path_service(project_root)
        config_path = path_service.get_management_dir() / self.CONFIG_FILE_NAME
        return config_path.exists()

    def load(self, project_root: Path) -> dict[str, Any]:
        """品質設定を読み込み"""
        path_service = create_path_service(project_root)
        config_path = path_service.get_management_dir() / self.CONFIG_FILE_NAME
        if not config_path.exists():
            msg = f"品質設定ファイルが見つかりません: {config_path}"
            raise FileNotFoundError(msg)

        with config_path.Path(encoding="utf-8").open() as f:
            return yaml.safe_load(f)

    def save(self, project_root: Path, config: dict[str, Any]) -> None:
        """品質設定を保存"""
        path_service = create_path_service()
        config_dir = path_service.get_management_dir()
        config_dir.mkdir(parents=True, exist_ok=True)

        config_path = config_dir / self.CONFIG_FILE_NAME

        # YAMLファイルに保存
        with config_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def backup(self, project_root: Path, suffix: str) -> None:
        """品質設定のバックアップを作成"""
        path_service = create_path_service(project_root)
        config_path = path_service.get_management_dir() / self.CONFIG_FILE_NAME
        if not config_path.exists():
            return

        backup_path = config_path.with_suffix(f".yaml.{suffix}")
        shutil.copy2(config_path, backup_path)

    def get_recent_results(self, project_root: Path, count: int) -> list[dict[str, Any]]:
        """最近の品質チェック結果を取得"""
        path_service = create_path_service()
        record_path = path_service.get_management_dir() / self.RECORD_FILE_NAME
        if not record_path.exists():
            return []

        with record_path.Path(encoding="utf-8").open() as f:
            record_data: dict[str, Any] = yaml.safe_load(f)

        quality_checks = record_data.get("quality_checks", [])
        # 最新のcount件を返す
        return quality_checks[-count:] if len(quality_checks) > count else quality_checks
