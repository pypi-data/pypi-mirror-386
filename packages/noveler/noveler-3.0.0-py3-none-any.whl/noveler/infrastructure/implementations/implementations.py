"""Infrastructure.implementations.implementations
Where: Infrastructure module registering concrete service implementations.
What: Wires domain interfaces to their infrastructure counterparts via DI.
Why: Ensures implementations are registered centrally for consumption.
"""

"Production implementations of interfaces\n本番環境用のインターフェース実装\n"
import os
from pathlib import Path
from typing import Any

import yaml

from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager
from noveler.infrastructure.interfaces import (
    IEnvironmentManager,
    IFileOperations,
    ILogger,
    IProjectConfigLoader,
    IYamlHandler,
)
from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class ProductionProjectConfigLoader(IProjectConfigLoader):
    """本番環境用プロジェクト設定ローダー"""

    def find_project_config(self, start_path: Path | None) -> Path | None:
        """プロジェクト設定ファイルを検索"""
        if start_path is None:
            start_path = Path.cwd()
        current = start_path.resolve()
        for parent in [current, *list(current.parents)]:
            config_file = parent / "プロジェクト設定.yaml"
            if config_file.exists():
                return config_file
            config_file_en = parent / "project_config.yaml"
            if config_file_en.exists():
                return config_file_en
        return None

    def load_project_config(self, config_path: Path) -> dict[str, Any]:
        """プロジェクト設定を読み込み"""
        try:
            with Path(config_path).open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger_service.warning("Failed to load config %s: %s", config_path, e)
            return {}


class ProductionFileOperations(IFileOperations):
    """本番環境用ファイル操作"""

    def read_file(self, file_path: Path) -> str:
        """ファイルを読み込み"""
        return file_path.read_text(encoding="utf-8")

    def write_file(self, file_path: Path, content: str) -> None:
        """ファイルに書き込み"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def exists(self, file_path: Path) -> bool:
        """ファイルの存在確認"""
        return file_path.exists()

    def list_files(self, directory: Path, pattern: str) -> list[Path]:
        """ディレクトリ内のファイル一覧"""
        if not directory.exists():
            return []
        return list(directory.glob(pattern))


class ProductionYamlHandler(IYamlHandler):
    """本番環境用YAML操作"""

    def load_yaml(self, file_path: Path) -> dict[str, Any]:
        """YAMLファイルを読み込み"""
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            logger.exception("Failed to load YAML %s", file_path)
            return {}

    def save_yaml(self, data: dict[str, Any], file_path: Path) -> None:
        """YAMLファイルに保存"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with Path(file_path).open("w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


class ProductionLogger(ILogger):
    """本番環境用ロガー"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def exception(self, message: str) -> None:
        self.logger.exception(message)


class ProductionEnvironmentManager(IEnvironmentManager):
    """本番環境用環境管理"""

    def get_mode(self) -> str:
        """現在のモードを取得"""
        config_manager = get_configuration_manager()
        return config_manager.get_system_setting("APP_MODE", "production")

    def is_test_mode(self) -> bool:
        """テストモードかどうか"""
        return self.get_mode() == "test"

    def setup_environment(self, project_root: Path) -> None:
        """環境変数を設定（DDD準拠・既存環境変数尊重）"""
        existing_project_root = os.environ.get("PROJECT_ROOT")
        if not existing_project_root:
            os.environ["PROJECT_ROOT"] = str(project_root)
        guide_root = project_root.parent / "00_ガイド"
        if guide_root.exists():
            os.environ["GUIDE_ROOT"] = str(guide_root)
        scripts_root = guide_root / "scripts" if guide_root.exists() else project_root / "scripts"
        if scripts_root.exists():
            os.environ["SCRIPTS_ROOT"] = str(scripts_root)
