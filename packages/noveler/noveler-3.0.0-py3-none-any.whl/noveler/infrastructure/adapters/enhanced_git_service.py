#!/usr/bin/env python3
"""拡張Git操作サービス
変更ファイルの検出機能を追加
"""

import subprocess

from noveler.infrastructure.adapters.git_service import GitService
from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class EnhancedGitService(GitService):
    """変更検出機能を追加したGitサービス"""

    def get_changed_files(self, since_commit: str) -> list[str]:
        """指定コミット以降の変更ファイルを取得"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", since_commit],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            return [f for f in result.stdout.strip().split("\n") if f]

        except subprocess.CalledProcessError as e:
            logger.exception("Failed to get changed files: %s", e)
            return []

    def get_uncommitted_changes(self) -> list[str]:
        """未コミットの変更ファイルを取得"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    # git status --porcelain の形式を解析
                    # 例: "M  file.txt", "?? new_file.txt"
                    parts = line[3:]  # 最初の3文字(ステータス)をスキップ
                    files.append(parts)

            return files

        except subprocess.CalledProcessError as e:
            logger.exception("Failed to get uncommitted changes: %s", e)
            return []

    def has_plot_changes_since(self, since_commit: str) -> bool:
        """指定コミット以降にプロット関連の変更があるかチェック"""
        changed_files = self.get_changed_files(since_commit)

        plot_prefixes = [
            "20_プロット/",
            "30_設定集/",
        ]

        return any(any(file.startswith(prefix) for prefix in plot_prefixes) for file in changed_files)
