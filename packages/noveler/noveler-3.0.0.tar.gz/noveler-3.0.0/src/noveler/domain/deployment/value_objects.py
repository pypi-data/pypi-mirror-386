"""Domain.deployment.value_objects
Where: Domain value objects describing deployment data.
What: Provides typed objects for deployment configuration and status.
Why: Keeps deployment-related data consistent across domain services.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

"""デプロイメントドメインの値オブジェクト

不変で同一性を持たない値を表現
"""


import re
from dataclasses import dataclass

@dataclass(frozen=True)
class ProjectPath:
    """プロジェクトパス値オブジェクト"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            msg = "Project path cannot be empty"
            raise ValueError(msg)

        # パスの正規化はインフラ層で行う
        # ドメイン層では文字列のまま保持

    # existsメソッドはインフラ層で実装すべき
    # ドメイン層ではファイルシステムに依存しない

    # is_valid_projectメソッドはインフラ層で実装すべき
    # ドメイン層ではファイルシステムに依存しない

    # pathプロパティは削除
    # ドメイン層ではPathオブジェクトを使用しない

    def __str__(self) -> str:
        return self.value

    @property
    def path(self):
        """Return a pathlib.Path representation for compatibility."""
        return Path(self.value)


@dataclass(frozen=True)
class CommitHash:
    """Gitコミットハッシュ値オブジェクト"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            msg = "Commit hash cannot be empty"
            raise ValueError(msg)

        # Check if valid hash (simple version)
        if not re.match(r"^[a-fA-F0-9]+$", self.value):
            msg = f"Invalid commit hash: {self.value}"
            raise ValueError(msg)

    @property
    def short(self) -> str:
        """短縮版のハッシュを返す"""
        return self.value[:7]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DeploymentConfig:
    """デプロイメント設定値オブジェクト"""

    scripts_directory_name: str = ".novel-scripts"
    create_backup: bool = True
    backup_retention_days: int = 7
    verify_after_deploy: bool = True
    parallel_deploy: bool = False
    max_parallel_deployments: int = 3

    def validate(self) -> list[str]:
        """設定の検証"""
        errors: list[Any] = []

        # ディレクトリ名の検証
        if "/" in self.scripts_directory_name or "\\" in self.scripts_directory_name:
            errors.append("Scripts directory name cannot contain path separators")

        if not self.scripts_directory_name:
            errors.append("Scripts directory name cannot be empty")

        # バックアップ保持期間の検証
        if self.backup_retention_days < 0:
            errors.append("Backup retention days must be non-negative")

        # 並列デプロイメント数の検証
        if self.max_parallel_deployments < 1:
            errors.append("Max parallel deployments must be at least 1")

        return errors


@dataclass
class DeploymentResult:
    """デプロイメント結果値オブジェクト"""

    success: bool
    message: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    deployed_files_count: int = 0
    backup_created: bool = False
    backup_path: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "success": self.success,
            "message": self.message,
            "deployed_files_count": self.deployed_files_count,
            "backup_created": self.backup_created,
            "backup_path": self.backup_path,
            "error_message": self.error_message,
        }
