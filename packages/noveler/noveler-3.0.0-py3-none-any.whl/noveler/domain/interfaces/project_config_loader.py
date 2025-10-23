"""プロジェクト設定ローダーのインターフェース"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class IProjectConfigLoader(ABC):
    """プロジェクト設定ローダーのインターフェース"""

    @abstractmethod
    def find_project_config(self, start_path: Path) -> Path | None:
        """プロジェクト設定ファイルを検索"""

    @abstractmethod
    def load_project_config(self, config_path: Path) -> dict[str, Any]:
        """プロジェクト設定を読み込み"""
