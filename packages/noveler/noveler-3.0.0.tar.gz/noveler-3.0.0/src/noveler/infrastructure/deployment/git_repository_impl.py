"""Gitリポジトリの実装

コマンドライン経由でGit操作を実行
"""

import subprocess
import tempfile
from pathlib import Path

from noveler.domain.deployment.repositories import GitRepository
from noveler.domain.deployment.value_objects import CommitHash


class GitRepositoryImpl(GitRepository):
    """Git操作の実装"""

    def __init__(self, repo_path: Path | str) -> None:
        self.repo_path = Path(repo_path)

    def has_uncommitted_changes(self) -> bool:
        """未コミットの変更があるかチェック"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def get_uncommitted_files(self) -> list[str]:
        """未コミットのファイルリストを取得"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            # ステータス文字を除いてファイル名のみ取得
            return [line[3:] for line in result.stdout.strip().split("\n") if line]

        except subprocess.CalledProcessError:
            return []

    def get_current_commit(self) -> CommitHash:
        """現在のコミットハッシュを取得"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            return CommitHash(result.stdout.strip())
        except subprocess.CalledProcessError:
            return CommitHash("unknown")

    def get_current_branch(self) -> str:
        """現在のブランチ名を取得"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def archive_scripts(self, commit: CommitHash, output_path: Path) -> None:
        """指定コミットのスクリプトをアーカイブ"""
        try:
            # git archiveとtarをパイプで接続(shell=Trueを避ける)
            # import tempfile # Moved to top-level
            with tempfile.NamedTemporaryFile(suffix=".tar", delete=True) as temp_tar:
                # git archiveでtarファイルを作成
                subprocess.run(
                    ["git", "archive", "--format=tar", "-o", temp_tar.name, f"{commit.value}:scripts"],
                    cwd=self.repo_path,
                    check=True,
                )

                # tarファイルを展開
                subprocess.run(["tar", "-x", "-f", temp_tar.name, "-C", str(output_path)], check=True)

        except subprocess.CalledProcessError as e:
            msg = f"Failed to archive noveler: {e}"
            raise RuntimeError(msg) from e
