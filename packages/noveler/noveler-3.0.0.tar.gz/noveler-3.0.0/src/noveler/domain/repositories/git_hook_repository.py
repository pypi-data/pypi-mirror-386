"""Domain.repositories.git_hook_repository
Where: Domain repository interface for git hook configuration.
What: Declares operations to manage git hook scripts and metadata.
Why: Supports infrastructure integration for project git hooks.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""Gitフックリポジトリインターフェース

DDD原則に基づくドメイン層のリポジトリ抽象化
"""


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class GitHookRepository(ABC):
    """Gitフックリポジトリインターフェース"""

    @abstractmethod
    def install_hooks(self, project_path: Path) -> bool:
        """Gitフックをインストール

        Args:
            project_path: プロジェクトのパス

        Returns:
            インストール成功時True
        """

    @abstractmethod
    def uninstall_hooks(self, project_path: Path) -> bool:
        """Gitフックをアンインストール

        Args:
            project_path: プロジェクトのパス

        Returns:
            アンインストール成功時True
        """

    @abstractmethod
    def is_hooks_installed(self, project_path: Path) -> bool:
        """Gitフックがインストールされているかチェック

        Args:
            project_path: プロジェクトのパス

        Returns:
            インストール済みの場合True
        """

    @abstractmethod
    def get_hook_status(self, project_path: Path) -> dict[str, bool]:
        """各フックの状態を取得

        Args:
            project_path: プロジェクトのパス

        Returns:
            フック名と状態のマッピング
        """

    @abstractmethod
    def update_hooks(self, project_path: Path) -> bool:
        """Gitフックを更新

        Args:
            project_path: プロジェクトのパス

        Returns:
            更新成功時True
        """
