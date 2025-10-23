"""デプロイメントドメインのリポジトリインターフェーステスト

TDD準拠テスト:
    - DeploymentRepository (ABC)
- ProjectRepository (ABC)
- GitRepository (ABC)
- VersionRepository (ABC)


仕様書: SPEC-UNIT-TEST
"""

from abc import ABC
from unittest.mock import Mock

import pytest

from noveler.domain.deployment.entities import (
    Deployment,
    DeploymentHistory,
    DeploymentMode,
    DeploymentStatus,
    DeploymentTarget,
    ScriptVersion,
)
from noveler.domain.deployment.repositories import (
    DeploymentRepository,
    GitRepository,
    ProjectRepository,
    VersionRepository,
)
from noveler.domain.deployment.value_objects import CommitHash, ProjectPath
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestDeploymentRepository:
    """DeploymentRepository抽象インターフェーステスト"""

    @pytest.mark.spec("SPEC-REPOSITORIES-DEPLOYMENT_REPOSITOR")
    def test_deployment_repository_is_abstract(self) -> None:
        """DeploymentRepositoryが抽象クラスであることを確認"""
        assert issubclass(DeploymentRepository, ABC)

    @pytest.mark.spec("SPEC-REPOSITORIES-DEPLOYMENT_REPOSITOR")
    def test_deployment_repository_abstract_methods(self) -> None:
        """DeploymentRepositoryの抽象メソッド確認"""
        abstract_methods = DeploymentRepository.__abstractmethods__
        expected_methods = {
            "save",
            "find_by_id",
            "find_by_project",
            "get_history",
            "rollback",
        }
        assert abstract_methods == expected_methods

    @pytest.mark.spec("SPEC-REPOSITORIES-DEPLOYMENT_REPOSITOR")
    def test_deployment_repository_save_signature(self) -> None:
        """saveメソッドのシグネチャ確認"""

        # モック実装を作成してインターフェースを検証
        class MockDeploymentRepo(DeploymentRepository):
            def save(self, deployment: Deployment) -> None:
                pass

            def find_by_id(self, _deployment_id: str) -> Deployment | None:
                return None

            def find_by_project(self, _project_path: ProjectPath) -> list[Deployment]:
                return []

            def get_history(self, _project_path: ProjectPath) -> DeploymentHistory:
                return DeploymentHistory(project_path=_project_path, deployments=[])

            def rollback(self, deployment: Deployment) -> None:
                pass

        repo = MockDeploymentRepo()
        deployment = Mock(spec=Deployment)

        # 例外が発生しないことを確認
        repo.save(deployment)

    @pytest.mark.spec("SPEC-REPOSITORIES-DEPLOYMENT_REPOSITOR")
    def test_deployment_repository_find_by_id_signature(self) -> None:
        """find_by_idメソッドのシグネチャ確認"""

        class MockDeploymentRepo(DeploymentRepository):
            def save(self, deployment: Deployment) -> None:
                pass

            def find_by_id(self, _deployment_id: str) -> Deployment | None:
                return None

            def find_by_project(self, _project_path: ProjectPath) -> list[Deployment]:
                return []

            def get_history(self, _project_path: ProjectPath) -> DeploymentHistory:
                return DeploymentHistory(project_path=_project_path, deployments=[])

            def rollback(self, deployment: Deployment) -> None:
                pass

        repo = MockDeploymentRepo()
        result = repo.find_by_id("test-id")

        assert result is None

    @pytest.mark.spec("SPEC-REPOSITORIES-DEPLOYMENT_REPOSITOR")
    def test_deployment_repository_find_by_project_signature(self) -> None:
        """find_by_projectメソッドのシグネチャ確認"""

        class MockDeploymentRepo(DeploymentRepository):
            def save(self, deployment: Deployment) -> None:
                pass

            def find_by_id(self, _deployment_id: str) -> Deployment | None:
                return None

            def find_by_project(self, _project_path: ProjectPath) -> list[Deployment]:
                return []

            def get_history(self, _project_path: ProjectPath) -> DeploymentHistory:
                return DeploymentHistory(project_path=_project_path, deployments=[])

            def rollback(self, deployment: Deployment) -> None:
                pass

        repo = MockDeploymentRepo()
        _project_path = ProjectPath("/test/project")
        result = repo.find_by_project(_project_path)

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.spec("SPEC-REPOSITORIES-DEPLOYMENT_REPOSITOR")
    def test_deployment_repository_get_history_signature(self) -> None:
        """get_historyメソッドのシグネチャ確認"""

        class MockDeploymentRepo(DeploymentRepository):
            def save(self, deployment: Deployment) -> None:
                pass

            def find_by_id(self, _deployment_id: str) -> Deployment | None:
                return None

            def find_by_project(self, _project_path: ProjectPath) -> list[Deployment]:
                return []

            def get_history(self, _project_path: ProjectPath) -> DeploymentHistory:
                return DeploymentHistory(project_path=_project_path, deployments=[])

            def rollback(self, deployment: Deployment) -> None:
                pass

        repo = MockDeploymentRepo()
        _project_path = ProjectPath("/test/project")
        result = repo.get_history(_project_path)

        assert isinstance(result, DeploymentHistory)
        assert result._project_path == _project_path

    @pytest.mark.spec("SPEC-REPOSITORIES-DEPLOYMENT_REPOSITOR")
    def test_deployment_repository_rollback_signature(self) -> None:
        """rollbackメソッドのシグネチャ確認"""

        class MockDeploymentRepo(DeploymentRepository):
            def save(self, deployment: Deployment) -> None:
                pass

            def find_by_id(self, _deployment_id: str) -> Deployment | None:
                return None

            def find_by_project(self, _project_path: ProjectPath) -> list[Deployment]:
                return []

            def get_history(self, _project_path: ProjectPath) -> DeploymentHistory:
                return DeploymentHistory(project_path=_project_path, deployments=[])

            def rollback(self, deployment: Deployment) -> None:
                pass

        repo = MockDeploymentRepo()
        deployment = Mock(spec=Deployment)

        # 例外が発生しないことを確認
        repo.rollback(deployment)


class TestProjectRepository:
    """ProjectRepository抽象インターフェーステスト"""

    @pytest.mark.spec("SPEC-REPOSITORIES-PROJECT_REPOSITORY_I")
    def test_project_repository_is_abstract(self) -> None:
        """ProjectRepositoryが抽象クラスであることを確認"""
        assert issubclass(ProjectRepository, ABC)

    @pytest.mark.spec("SPEC-REPOSITORIES-PROJECT_REPOSITORY_A")
    def test_project_repository_abstract_methods(self) -> None:
        """ProjectRepositoryの抽象メソッド確認"""
        abstract_methods = ProjectRepository.__abstractmethods__
        expected_methods = {
            "find_all_projects",
            "project_exists",
            "get_project_info",
        }
        assert abstract_methods == expected_methods

    @pytest.mark.spec("SPEC-REPOSITORIES-PROJECT_REPOSITORY_F")
    def test_project_repository_find_all_projects_signature(self) -> None:
        """find_all_projectsメソッドのシグネチャ確認"""

        class MockProjectRepo(ProjectRepository):
            def find_all_projects(self) -> list[DeploymentTarget]:
                return []

            def project_exists(self, _project_path: ProjectPath) -> bool:
                return False

            def get_project_info(self, _project_path: ProjectPath) -> dict | None:
                return None

        repo = MockProjectRepo()
        result = repo.find_all_projects()

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.spec("SPEC-REPOSITORIES-PROJECT_REPOSITORY_P")
    def test_project_repository_project_exists_signature(self) -> None:
        """project_existsメソッドのシグネチャ確認"""

        class MockProjectRepo(ProjectRepository):
            def find_all_projects(self) -> list[DeploymentTarget]:
                return []

            def project_exists(self, _project_path: ProjectPath) -> bool:
                return True

            def get_project_info(self, _project_path: ProjectPath) -> dict | None:
                return None

        repo = MockProjectRepo()
        project_path = ProjectPath("/test/project")
        result = repo.project_exists(project_path)

        assert isinstance(result, bool)
        assert result is True

    @pytest.mark.spec("SPEC-REPOSITORIES-PROJECT_REPOSITORY_G")
    def test_project_repository_get_project_info_signature(self) -> None:
        """get_project_infoメソッドのシグネチャ確認"""

        class MockProjectRepo(ProjectRepository):
            def find_all_projects(self) -> list[DeploymentTarget]:
                return []

            def project_exists(self, _project_path: ProjectPath) -> bool:
                return False

            def get_project_info(self, _project_path: ProjectPath) -> dict | None:
                return {"name": "Test Project", "version": "1.0.0"}

        repo = MockProjectRepo()
        project_path = ProjectPath("/test/project")
        result = repo.get_project_info(project_path)

        assert isinstance(result, dict)
        assert result["name"] == "Test Project"


class TestGitRepository:
    """GitRepository抽象インターフェーステスト"""

    @pytest.mark.spec("SPEC-REPOSITORIES-GIT_REPOSITORY_IS_AB")
    def test_git_repository_is_abstract(self) -> None:
        """GitRepositoryが抽象クラスであることを確認"""
        assert issubclass(GitRepository, ABC)

    @pytest.mark.spec("SPEC-REPOSITORIES-GIT_REPOSITORY_ABSTR")
    def test_git_repository_abstract_methods(self) -> None:
        """GitRepositoryの抽象メソッド確認"""
        abstract_methods = GitRepository.__abstractmethods__
        expected_methods = {
            "has_uncommitted_changes",
            "get_uncommitted_files",
            "get_current_commit",
            "get_current_branch",
            "archive_scripts",
        }
        assert abstract_methods == expected_methods

    @pytest.mark.spec("SPEC-REPOSITORIES-GIT_REPOSITORY_HAS_U")
    def test_git_repository_has_uncommitted_changes_signature(self) -> None:
        """has_uncommitted_changesメソッドのシグネチャ確認"""

        class MockGitRepo(GitRepository):
            def has_uncommitted_changes(self) -> bool:
                return False

            def get_uncommitted_files(self) -> list[str]:
                return []

            def get_current_commit(self) -> CommitHash:
                return CommitHash("abc123")

            def get_current_branch(self) -> str:
                return "main"

            def archive_scripts(self, commit: CommitHash, output_path: str) -> None:
                pass

        repo = MockGitRepo()
        result = repo.has_uncommitted_changes()

        assert isinstance(result, bool)
        assert result is False

    @pytest.mark.spec("SPEC-REPOSITORIES-GIT_REPOSITORY_GET_U")
    def test_git_repository_get_uncommitted_files_signature(self) -> None:
        """get_uncommitted_filesメソッドのシグネチャ確認"""

        class MockGitRepo(GitRepository):
            def has_uncommitted_changes(self) -> bool:
                return True

            def get_uncommitted_files(self) -> list[str]:
                return ["file1.py", "file2.py"]

            def get_current_commit(self) -> CommitHash:
                return CommitHash("abc123")

            def get_current_branch(self) -> str:
                return "main"

            def archive_scripts(self, commit: CommitHash, output_path: str) -> None:
                pass

        repo = MockGitRepo()
        result = repo.get_uncommitted_files()

        assert isinstance(result, list)
        assert len(result) == 2
        assert "file1.py" in result

    @pytest.mark.spec("SPEC-REPOSITORIES-GIT_REPOSITORY_GET_C")
    def test_git_repository_get_current_commit_signature(self) -> None:
        """get_current_commitメソッドのシグネチャ確認"""

        class MockGitRepo(GitRepository):
            def has_uncommitted_changes(self) -> bool:
                return False

            def get_uncommitted_files(self) -> list[str]:
                return []

            def get_current_commit(self) -> CommitHash:
                return CommitHash("def456")

            def get_current_branch(self) -> str:
                return "main"

            def archive_scripts(self, commit: CommitHash, output_path: str) -> None:
                pass

        repo = MockGitRepo()
        result = repo.get_current_commit()

        assert isinstance(result, CommitHash)
        assert result.value == "def456"

    @pytest.mark.spec("SPEC-REPOSITORIES-GIT_REPOSITORY_GET_C")
    def test_git_repository_get_current_branch_signature(self) -> None:
        """get_current_branchメソッドのシグネチャ確認"""

        class MockGitRepo(GitRepository):
            def has_uncommitted_changes(self) -> bool:
                return False

            def get_uncommitted_files(self) -> list[str]:
                return []

            def get_current_commit(self) -> CommitHash:
                return CommitHash("abc123")

            def get_current_branch(self) -> str:
                return "feature/test"

            def archive_scripts(self, commit: CommitHash, output_path: str) -> None:
                pass

        repo = MockGitRepo()
        result = repo.get_current_branch()

        assert isinstance(result, str)
        assert result == "feature/test"

    @pytest.mark.spec("SPEC-REPOSITORIES-GIT_REPOSITORY_ARCHI")
    def test_git_repository_archive_scripts_signature(self) -> None:
        """archive_scriptsメソッドのシグネチャ確認"""

        class MockGitRepo(GitRepository):
            def has_uncommitted_changes(self) -> bool:
                return False

            def get_uncommitted_files(self) -> list[str]:
                return []

            def get_current_commit(self) -> CommitHash:
                return CommitHash("abc123")

            def get_current_branch(self) -> str:
                return "main"

            def archive_scripts(self, commit: CommitHash, output_path: str) -> None:
                pass

        repo = MockGitRepo()
        commit = CommitHash("abc123")

        # 例外が発生しないことを確認
        repo.archive_scripts(commit, "/output/path")


class TestVersionRepository:
    """VersionRepository抽象インターフェーステスト"""

    @pytest.mark.spec("SPEC-REPOSITORIES-VERSION_REPOSITORY_I")
    def test_version_repository_is_abstract(self) -> None:
        """VersionRepositoryが抽象クラスであることを確認"""
        assert issubclass(VersionRepository, ABC)

    @pytest.mark.spec("SPEC-REPOSITORIES-VERSION_REPOSITORY_A")
    def test_version_repository_abstract_methods(self) -> None:
        """VersionRepositoryの抽象メソッド確認"""
        abstract_methods = VersionRepository.__abstractmethods__
        expected_methods = {
            "save_version",
            "get_current_version",
            "get_version_history",
        }
        assert abstract_methods == expected_methods

    @pytest.mark.spec("SPEC-REPOSITORIES-VERSION_REPOSITORY_S")
    def test_version_repository_save_version_signature(self) -> None:
        """save_versionメソッドのシグネチャ確認"""

        class MockVersionRepo(VersionRepository):
            def save_version(self, project_path: ProjectPath, version: ScriptVersion) -> None:
                pass

            def get_current_version(self, _project_path: ProjectPath) -> ScriptVersion | None:
                return None

            def get_version_history(self, _project_path: ProjectPath) -> list[ScriptVersion]:
                return []

        repo = MockVersionRepo()
        project_path = ProjectPath("/test/project")
        version = ScriptVersion(
            commit_hash=CommitHash("abc123"), timestamp=project_now().datetime, deployed_by="test-user"
        )

        # 例外が発生しないことを確認
        repo.save_version(project_path, version)

    @pytest.mark.spec("SPEC-REPOSITORIES-VERSION_REPOSITORY_G")
    def test_version_repository_get_current_version_signature(self) -> None:
        """get_current_versionメソッドのシグネチャ確認"""

        class MockVersionRepo(VersionRepository):
            def save_version(self, project_path: ProjectPath, version: ScriptVersion) -> None:
                pass

            def get_current_version(self, _project_path: ProjectPath) -> ScriptVersion | None:
                return ScriptVersion(
                    commit_hash=CommitHash("abc123"), timestamp=project_now().datetime, deployed_by="test-user"
                )

            def get_version_history(self, _project_path: ProjectPath) -> list[ScriptVersion]:
                return []

        repo = MockVersionRepo()
        project_path = ProjectPath("/test/project")
        result = repo.get_current_version(project_path)

        assert isinstance(result, ScriptVersion)
        assert result.commit_hash.value == "abc123"

    @pytest.mark.spec("SPEC-REPOSITORIES-VERSION_REPOSITORY_G")
    def test_version_repository_get_version_history_signature(self) -> None:
        """get_version_historyメソッドのシグネチャ確認"""

        class MockVersionRepo(VersionRepository):
            def save_version(self, project_path: ProjectPath, version: ScriptVersion) -> None:
                pass

            def get_current_version(self, _project_path: ProjectPath) -> ScriptVersion | None:
                return None

            def get_version_history(self, _project_path: ProjectPath) -> list[ScriptVersion]:
                return [
                    ScriptVersion(
                        commit_hash=CommitHash("abc123"), timestamp=project_now().datetime, deployed_by="test-user"
                    ),
                    ScriptVersion(
                        commit_hash=CommitHash("def456"), timestamp=project_now().datetime, deployed_by="test-user"
                    ),
                ]

        repo = MockVersionRepo()
        project_path = ProjectPath("/test/project")
        result = repo.get_version_history(project_path)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(v, ScriptVersion) for v in result)


class TestRepositoryIntegration:
    """リポジトリ間の統合テスト"""

    @pytest.mark.spec("SPEC-REPOSITORIES-DEPLOYMENT_AND_PROJE")
    def test_deployment_and_project_repository_integration(self) -> None:
        """DeploymentRepositoryとProjectRepositoryの連携確認"""

        class MockDeploymentRepo(DeploymentRepository):
            def __init__(self) -> None:
                self.deployments: list[Deployment] = []

            def save(self, deployment: Deployment) -> None:
                self.deployments.append(deployment)

            def find_by_id(self, deployment_id: str) -> Deployment | None:
                for d in self.deployments:
                    if d.deployment_id == deployment_id:
                        return d
                return None

            def find_by_project(self, project_path: ProjectPath) -> list[Deployment]:
                return [d for d in self.deployments if d.target.project_path == project_path]

            def get_history(self, project_path: ProjectPath) -> DeploymentHistory:
                project_deployments = self.find_by_project(project_path)
                successful = [d for d in project_deployments if d.status == DeploymentStatus.COMPLETED]
                return DeploymentHistory(
                    project_path=project_path,
                    deployments=project_deployments,
                    last_successful_deployment=successful[-1] if successful else None,
                )

            def rollback(self, deployment: Deployment) -> None:
                deployment.status = DeploymentStatus.ROLLED_BACK

        class MockProjectRepo(ProjectRepository):
            def __init__(self) -> None:
                self.projects = {
                    "/test/project1": {"name": "Project 1", "version": "1.0.0"},
                    "/test/project2": {"name": "Project 2", "version": "2.0.0"},
                }

            def find_all_projects(self) -> list[DeploymentTarget]:
                targets = []
                for path, info in self.projects.items():
                    targets.append(DeploymentTarget(project_path=ProjectPath(path), project_name=info["name"]))

                return targets

            def project_exists(self, project_path: ProjectPath) -> bool:
                return project_path.value in self.projects

            def get_project_info(self, project_path: ProjectPath) -> dict | None:
                return self.projects.get(project_path.value)

        # リポジトリの作成
        deployment_repo = MockDeploymentRepo()
        project_repo = MockProjectRepo()

        # プロジェクトからデプロイメントターゲットを取得
        targets = project_repo.find_all_projects()
        assert len(targets) == 2

        # 最初のプロジェクトにデプロイメントを作成
        target = targets[0]
        deployment = Deployment(target=target, mode=DeploymentMode.DEVELOPMENT, source_commit=CommitHash("abc123"))
        deployment_repo.save(deployment)

        # プロジェクトのデプロイメントを検索
        project_deployments = deployment_repo.find_by_project(target.project_path)
        assert len(project_deployments) == 1
        assert project_deployments[0].target.project_name == "Project 1"

    @pytest.mark.spec("SPEC-REPOSITORIES-GIT_AND_VERSION_REPO")
    def test_git_and_version_repository_integration(self) -> None:
        """GitRepositoryとVersionRepositoryの連携確認"""

        class MockGitRepo(GitRepository):
            def __init__(self) -> None:
                self.current_commit = CommitHash("abc123")
                self.current_branch = "main"
                self.uncommitted_files = []

            def has_uncommitted_changes(self) -> bool:
                return len(self.uncommitted_files) > 0

            def get_uncommitted_files(self) -> list[str]:
                return self.uncommitted_files

            def get_current_commit(self) -> CommitHash:
                return self.current_commit

            def get_current_branch(self) -> str:
                return self.current_branch

            def archive_scripts(self, commit: CommitHash, output_path: str) -> None:
                # アーカイブ処理のモック
                pass

        class MockVersionRepo(VersionRepository):
            def __init__(self) -> None:
                self.versions: dict[str, list[ScriptVersion]] = {}

            def save_version(self, project_path: ProjectPath, version: ScriptVersion) -> None:
                path = project_path.value
                if path not in self.versions:
                    self.versions[path] = []
                self.versions[path].append(version)

            def get_current_version(self, project_path: ProjectPath) -> ScriptVersion | None:
                path = project_path.value
                if self.versions.get(path):
                    return self.versions[path][-1]
                return None

            def get_version_history(self, project_path: ProjectPath) -> list[ScriptVersion]:
                return self.versions.get(project_path.value, [])

        # リポジトリの作成
        git_repo = MockGitRepo()
        version_repo = MockVersionRepo()

        # 現在のコミットでバージョンを作成
        project_path = ProjectPath("/test/project")
        current_commit = git_repo.get_current_commit()

        version = ScriptVersion(commit_hash=current_commit, timestamp=project_now().datetime, deployed_by="test-user")

        version_repo.save_version(project_path, version)

        # バージョン履歴の確認
        history = version_repo.get_version_history(project_path)
        assert len(history) == 1
        assert history[0].commit_hash == current_commit
        assert history[0].deployed_by == "test-user"

    @pytest.mark.spec("SPEC-REPOSITORIES-FULL_DEPLOYMENT_WORK")
    def test_full_deployment_workflow_with_repositories(self) -> None:
        """全リポジトリを使用したデプロイメントワークフローテスト"""

        # 全てのモックリポジトリを実装
        class MockDeploymentRepo(DeploymentRepository):
            def __init__(self) -> None:
                self.deployments: list[Deployment] = []

            def save(self, deployment: Deployment) -> None:
                self.deployments.append(deployment)

            def find_by_id(self, deployment_id: str) -> Deployment | None:
                for d in self.deployments:
                    if d.deployment_id == deployment_id:
                        return d
                return None

            def find_by_project(self, project_path: ProjectPath) -> list[Deployment]:
                return [d for d in self.deployments if d.target.project_path == project_path]

            def get_history(self, project_path: ProjectPath) -> DeploymentHistory:
                project_deployments = self.find_by_project(project_path)
                successful = [d for d in project_deployments if d.status == DeploymentStatus.COMPLETED]
                return DeploymentHistory(
                    project_path=project_path,
                    deployments=project_deployments,
                    last_successful_deployment=successful[-1] if successful else None,
                )

            def rollback(self, deployment: Deployment) -> None:
                deployment.status = DeploymentStatus.ROLLED_BACK

        class MockProjectRepo(ProjectRepository):
            def find_all_projects(self) -> list[DeploymentTarget]:
                return [DeploymentTarget(project_path=ProjectPath("/test/project"), project_name="Test Project")]

            def project_exists(self, project_path: ProjectPath) -> bool:
                return project_path.value == "/test/project"

            def get_project_info(self, project_path: ProjectPath) -> dict | None:
                if self.project_exists(project_path):
                    return {"name": "Test Project", "version": "1.0.0"}
                return None

        class MockGitRepo(GitRepository):
            def has_uncommitted_changes(self) -> bool:
                return False

            def get_uncommitted_files(self) -> list[str]:
                return []

            def get_current_commit(self) -> CommitHash:
                return CommitHash("abc123")

            def get_current_branch(self) -> str:
                return "main"

            def archive_scripts(self, commit: CommitHash, output_path: str) -> None:
                pass

        class MockVersionRepo(VersionRepository):
            def __init__(self) -> None:
                self.versions: list[ScriptVersion] = []

            def save_version(self, _project_path: ProjectPath, version: ScriptVersion) -> None:
                self.versions.append(version)

            def get_current_version(self, _project_path: ProjectPath) -> ScriptVersion | None:
                return self.versions[-1] if self.versions else None

            def get_version_history(self, _project_path: ProjectPath) -> list[ScriptVersion]:
                return self.versions

        # ワークフローの実行
        deployment_repo = MockDeploymentRepo()
        project_repo = MockProjectRepo()
        git_repo = MockGitRepo()
        version_repo = MockVersionRepo()

        # 1. プロジェクトの確認
        projects = project_repo.find_all_projects()
        assert len(projects) == 1
        target = projects[0]

        # 2. Gitの状態確認
        assert not git_repo.has_uncommitted_changes()
        commit = git_repo.get_current_commit()

        # 3. デプロイメントの作成
        deployment = Deployment(target=target, mode=DeploymentMode.PRODUCTION, source_commit=commit)
        deployment_repo.save(deployment)

        # 4. バージョンの保存
        version = ScriptVersion(
            commit_hash=CommitHash("abc123"),
            timestamp=project_now().datetime,
            deployed_by="test-user",
            changes=["Deployment from " + git_repo.get_current_branch()],
        )

        version_repo.save_version(target.project_path, version)

        # 5. デプロイメント完了
        deployment.status = DeploymentStatus.COMPLETED
        deployment_repo.save(deployment)

        # 6. 履歴の確認
        history = deployment_repo.get_history(target.project_path)
        assert len(history.deployments) == 2  # 初回保存と完了時の2回
        assert history.last_successful_deployment is not None

        version_history = version_repo.get_version_history(target.project_path)
        assert len(version_history) == 1
        assert version_history[0].version == "1.0.0"
