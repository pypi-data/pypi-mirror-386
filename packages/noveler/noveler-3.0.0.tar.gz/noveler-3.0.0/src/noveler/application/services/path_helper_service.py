#!/usr/bin/env python3
"""Helper service that consolidates common path manipulation patterns."""

from pathlib import Path
from typing import Any


class PathHelperService:
    """Expose shared path validation and normalization utilities."""

    def __init__(self, logger=None) -> None:
        """Initialize the helper with an optional logger dependency."""
        # DDD準拠: Infrastructure層への直接依存を回避（遅延初期化）
        self._logger = logger

    def _get_default_logger(self) -> Any:
        """Return the configured logger or lazily acquire the unified logger."""
        if self._logger is None:
            # 遅延初期化: Infrastructure層インポートを実行時まで遅延
            from noveler.infrastructure.logging.unified_logger import get_logger

            self._logger = get_logger(__name__)
        return self._logger

    @staticmethod
    def ensure_path(path_input: str | Path) -> Path:
        """Normalize the input into a ``Path`` instance."""
        return Path(path_input) if isinstance(path_input, str) else path_input

    @staticmethod
    def get_project_directory_path(project_directory: str) -> Path:
        """Return the project directory as a ``Path`` instance."""
        return Path(project_directory)

    def validate_path_exists(self, path: Path, path_type: str = "パス") -> bool:
        """Raise ``FileNotFoundError`` if the provided path does not exist."""
        if not path.exists():
            error_message = f"{path_type} '{path}' が見つかりません"
            # DDD準拠: 遅延初期化されたロガーを使用
            logger = self._get_default_logger()
            logger.error(error_message)
            raise FileNotFoundError(error_message)
        return True
