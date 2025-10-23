#!/usr/bin/env python3
"""Service adapter that wraps Git commands at the infrastructure layer."""

import subprocess
from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class GitService:
    """Provide convenience wrappers for Git operations."""

    def __init__(self, project_root: Path | str) -> None:
        self.project_root = project_root
        self.logger_service = logger

    def create_tag(self, tag_name: str, message: str) -> bool:
        """Create an annotated Git tag if it does not already exist."""
        try:
            # タグが既に存在するかチェック
            result = subprocess.run(
                ["git", "tag", "-l", tag_name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.stdout.strip():
                self.logger_service.info("Tag %s already exists", tag_name)
                return True

            # タグを作成
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", message],
                cwd=self.project_root,
                check=True,
            )

            self.logger_service.info("Created git tag: %s", tag_name)
            return True

        except subprocess.CalledProcessError as e:
            logger.exception("Failed to create git tag: %s", e)
            return False

    def get_current_commit(self) -> str:
        """Return the hash of the current HEAD commit."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            return result.stdout.strip()

        except subprocess.CalledProcessError:
            logger.exception("Failed to get current commit")
            return ""

    def get_commit_range(self, from_ref: str, to_ref: str) -> str:
        """Return the range expression used in Git diff commands."""
        return f"{from_ref}..{to_ref}"

    def get_diff(self, from_ref: str, to_ref: str, path_filter: str | None = None) -> dict:
        """Return diff statistics and file list between two references."""
        try:
            # 変更されたファイルのリストを取得
            cmd = ["git", "diff", "--name-only", from_ref, to_ref]
            if path_filter:
                cmd.append(path_filter)

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            files = [f for f in result.stdout.strip().split("\n") if f]

            # 統計情報を取得
            stat_cmd = ["git", "diff", "--stat", from_ref, to_ref]
            if path_filter:
                stat_cmd.append(path_filter)

            stat_result = subprocess.run(
                stat_cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            # 簡易的な統計解析
            additions = 0
            deletions = 0
            for line in stat_result.stdout.split("\n"):
                if "+" in line and "-" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "+" in part:
                            additions += int(part.replace("+", "").strip())
                        elif "-" in part:
                            deletions += int(part.replace("-", "").strip())

            return {
                "files": files,
                "additions": additions,
                "deletions": deletions,
                "stat": stat_result.stdout,
            }

        except subprocess.CalledProcessError as e:
            logger.exception("Failed to get diff: %s", e)
            return {
                "files": [],
                "additions": 0,
                "deletions": 0,
                "stat": "",
            }

    def get_file_at_commit(self, file_path: str, commit: str) -> str | None:
        """Return file contents at a specific commit, or ``None`` on failure."""
        try:
            result = subprocess.run(
                ["git", "show", f"{commit}:{file_path}"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            return result.stdout

        except subprocess.CalledProcessError:
            logger.exception("Failed to get file %s at commit %s", file_path, commit)
            return None

    def get_diff_content(self, from_ref: str, to_ref: str, file_path: str | None = None) -> str | None:
        """Return diff output between two refs, optionally scoped to a file."""
        try:
            cmd = ["git", "diff", from_ref, to_ref]
            if file_path:
                cmd.extend(["--", file_path])
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            return result.stdout

        except subprocess.CalledProcessError:
            logger.exception("Failed to get diff for %s", file_path or "all files")
            return None
