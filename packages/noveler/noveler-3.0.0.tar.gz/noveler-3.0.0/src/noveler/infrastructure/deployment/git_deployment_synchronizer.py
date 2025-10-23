"""Git デプロイメント同期器

$GUIDE_ROOTのコミット済みスクリプトを$PROJECT_ROOTに同期
"""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from noveler.domain.deployment.value_objects import CommitHash
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class GitDeploymentSynchronizer:
    """Git を使ったデプロイメント同期"""

    def __init__(self, guide_root: Path) -> None:
        self.guide_root = Path(guide_root)
        self._logger = logger

    def get_latest_commit(self) -> CommitHash:
        """最新のコミットハッシュを取得"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.guide_root,
                capture_output=True,
                text=True,
                check=True,
            )

            return CommitHash(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            msg = "Failed to get latest commit"
            raise RuntimeError(msg) from e

    def get_deployed_commit(self, project_path: object) -> CommitHash | None:
        """デプロイ済みのコミットハッシュを取得"""
        version_file = Path(project_path.value) / ".novel-scripts" / "VERSION"

        if not version_file.exists():
            return None

        try:
            content = version_file.read_text(encoding="utf-8")
            # "Git Commit: abc123def" の形式から抽出
            match = re.search(r"Git Commit:\s*([0-9a-fA-F]{7,40})", content)
            if match:
                return CommitHash(match.group(1))
        except Exception as e:
            self._logger.debug("コミット情報の解析に失敗しました: %s", e)

        return None

    def sync_to_latest(self, project_path: object) -> bool:
        """最新のコミットに同期"""
        try:
            scripts_dir = Path(project_path.value) / ".novel-scripts"

            # 既存のスクリプトディレクトリを削除
            if scripts_dir.exists():
                shutil.rmtree(scripts_dir)

            # 新しいディレクトリを作成
            scripts_dir.mkdir(parents=True, exist_ok=True)

            # Git archive を使ってスクリプトをチェックアウト
            self._archive_scripts_to_directory(scripts_dir)

            # VERSION ファイルを作成
            self._create_version_file(scripts_dir)

            return True

        except Exception as e:
            # 失敗した場合はクリーンアップ
            if scripts_dir.exists():
                shutil.rmtree(scripts_dir, ignore_errors=True)
            msg = f"Failed to sync noveler: {e}"
            raise RuntimeError(msg) from e

    def create_backup(self, project_path: object) -> str | None:
        """既存スクリプトのバックアップを作成"""
        scripts_dir = Path(project_path.value) / ".novel-scripts"

        if not scripts_dir.exists():
            return None

        # バックアップディレクトリ名を生成
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        backup_name = f".noveler.backup.{timestamp}"
        backup_path = Path(project_path.value) / backup_name

        try:
            shutil.copytree(scripts_dir, backup_path)
            return backup_name
        except Exception:
            return None

    def _archive_scripts_to_directory(self, target_dir: Path) -> None:
        """Git archive を使ってスクリプトを展開"""
        try:
            # Git archive コマンドでスクリプトディレクトリをアーカイブして展開
            # git archiveとtarをパイプで接続(shell=Trueを避ける)
            # import tempfile # Moved to top-level
            with tempfile.NamedTemporaryFile(suffix=".tar", delete=True) as temp_tar:
                # git archiveでtarファイルを作成
                subprocess.run(
                    ["git", "archive", "--format=tar", "-o", temp_tar.name, "HEAD:scripts"],
                    cwd=self.guide_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # tarファイルを展開
                subprocess.run(
                    ["tar", "-x", "-f", temp_tar.name, "-C", str(target_dir)],
                    check=True,
                    capture_output=True,
                    text=True,
                )

        except subprocess.CalledProcessError as e:
            msg = f"Git archive failed: {e.stderr}"
            raise RuntimeError(msg) from e

    def _create_version_file(self, scripts_dir: Path) -> None:
        """VERSION ファイルを作成"""
        try:
            # 現在のコミット情報を取得
            commit_hash = self.get_latest_commit()

            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.guide_root,
                capture_output=True,
                text=True,
                check=True,
            )

            branch = branch_result.stdout.strip()

            # VERSION ファイルの内容を作成
            version_content = f"""Deployed: {project_now().datetime.strftime("%Y-%m-%d %H:%M:%S")}
Mode: PRODUCTION
Git Commit: {commit_hash.value}
Git Branch: {branch}
Deployed By: auto-sync
Deployment Method: git-archive
"""

            version_file = scripts_dir / "VERSION"
            version_file.write_text(version_content, encoding="utf-8")

        except Exception as e:
            # VERSION ファイル作成に失敗してもデプロイは続行
            self._logger.warning("VERSION ファイル作成に失敗しました: %s", e)

    def verify_deployment(self, project_path: object) -> bool:
        """デプロイメントの検証"""
        scripts_dir = project_path.path / ".novel-scripts"

        # 基本的なファイルの存在確認
        required_files = [
            "main/novel.py",
            "domain",
            "application",
            "infrastructure",
        ]

        return all((scripts_dir / required).exists() for required in required_files)
