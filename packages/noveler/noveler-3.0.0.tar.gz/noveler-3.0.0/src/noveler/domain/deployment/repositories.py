"""デプロイメントドメインのリポジトリインターフェース

永続化の詳細を隠蔽する抽象インターフェース
"""

from abc import ABC, abstractmethod

from noveler.domain.deployment.entities import Deployment, DeploymentHistory, DeploymentTarget, ScriptVersion
from noveler.domain.deployment.value_objects import CommitHash, ProjectPath


class DeploymentRepository(ABC):
    """デプロイメント情報の永続化リポジトリ"""

    @abstractmethod
    def save(self, deployment: Deployment) -> None:
        """デプロイメント情報を保存"""

    @abstractmethod
    def find_by_id(self, deployment_id: str) -> Deployment | None:
        """IDでデプロイメントを検索"""

    @abstractmethod
    def find_by_project(self, project_path: ProjectPath) -> list[Deployment]:
        """プロジェクトごとのデプロイメントを検索"""

    @abstractmethod
    def get_history(self, project_path: ProjectPath) -> DeploymentHistory:
        """プロジェクトのデプロイメント履歴を取得"""

    @abstractmethod
    def rollback(self, deployment: Deployment) -> None:
        """デプロイメントをロールバック"""


class ProjectRepository(ABC):
    """プロジェクト情報のリポジトリ"""

    @abstractmethod
    def find_all_projects(self) -> list[DeploymentTarget]:
        """すべてのデプロイ可能なプロジェクトを検索"""

    @abstractmethod
    def project_exists(self, project_path: ProjectPath) -> bool:
        """プロジェクトが存在するかチェック"""

    @abstractmethod
    def get_project_info(self, project_path: ProjectPath) -> dict | None:
        """プロジェクト情報を取得"""


class GitRepository(ABC):
    """Git操作のリポジトリ"""

    @abstractmethod
    def has_uncommitted_changes(self) -> bool:
        """未コミットの変更があるかチェック"""

    @abstractmethod
    def get_uncommitted_files(self) -> list[str]:
        """未コミットのファイルリストを取得"""

    @abstractmethod
    def get_current_commit(self) -> CommitHash:
        """現在のコミットハッシュを取得"""

    @abstractmethod
    def get_current_branch(self) -> str:
        """現在のブランチ名を取得"""

    @abstractmethod
    def archive_scripts(self, commit: CommitHash, output_path: str) -> None:
        """指定コミットのスクリプトをアーカイブ"""


class VersionRepository(ABC):
    """バージョン情報のリポジトリ"""

    @abstractmethod
    def save_version(self, project_path: ProjectPath, version: ScriptVersion) -> None:
        """バージョン情報を保存"""

    @abstractmethod
    def get_current_version(self, project_path: ProjectPath) -> ScriptVersion | None:
        """現在のバージョン情報を取得"""

    @abstractmethod
    def get_version_history(self, project_path: ProjectPath) -> list[ScriptVersion]:
        """バージョン履歴を取得"""
