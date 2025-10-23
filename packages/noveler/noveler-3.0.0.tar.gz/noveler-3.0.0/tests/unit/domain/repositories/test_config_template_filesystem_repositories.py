"""Tests.tests.unit.domain.repositories.test_config_template_filesystem_repositories
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType

"""設定・テンプレート・ファイルシステムリポジトリインターフェーステスト

仕様書: SPEC-UNIT-TEST
"""

from abc import ABC
from datetime import datetime

import pytest

from noveler.domain.repositories.configuration_repository import (
    ConfigurationRepository,
    EpisodeManagementDataRepository,
    ManuscriptRepository,
)
from noveler.domain.repositories.file_system_repository import FileSystemRepository
from noveler.domain.repositories.template_repository import TemplateRepository


class TestConfigurationRepository:
    """設定管理リポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-INTERFACE_DEFINITION")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(ConfigurationRepository, ABC)

        methods = [
            "load_project_config",
            "save_project_config",
            "load_quality_config",
            "save_quality_config",
            "project_exists",
        ]
        for method in methods:
            assert hasattr(ConfigurationRepository, method)

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-ABSTRACT_METHODS")
    def test_abstract_methods(self) -> None:
        """抽象メソッドの定義を確認"""
        with pytest.raises(TypeError, match=".*"):
            ConfigurationRepository()

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-METHOD_SIGNATURES")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""

        # モック実装を作成
        class MockConfigRepo(ConfigurationRepository):
            def __init__(self) -> None:
                self.project_configs = {}
                self.quality_configs = {}
                self.projects = set()

            def load_project_config(self, project_path: str) -> dict[str, object]:
                if project_path not in self.project_configs:
                    msg = f"設定ファイルが存在しません: {project_path}"
                    raise FileNotFoundError(msg)
                return self.project_configs[project_path]

            def save_project_config(self, project_path: str, config_data: dict[str, object]) -> None:
                self.project_configs[project_path] = config_data
                self.projects.add(project_path)

            def load_quality_config(self, project_path: str) -> dict[str, object]:
                if project_path not in self.quality_configs:
                    return {"default": True}  # デフォルト設定
                return self.quality_configs[project_path]

            def save_quality_config(self, project_path: str, config_data: dict[str, object]) -> None:
                self.quality_configs[project_path] = config_data

            def project_exists(self, project_path: str) -> bool:
                return project_path in self.projects

        repo = MockConfigRepo()

        # プロジェクト設定のテスト
        config_data = {"name": "テストプロジェクト", "author": "作者名"}
        repo.save_project_config("/test/project", config_data)

        assert repo.project_exists("/test/project") is True
        loaded = repo.load_project_config("/test/project")
        assert loaded["name"] == "テストプロジェクト"

        # 存在しない設定の読み込みテスト
        with pytest.raises(FileNotFoundError, match=".*"):
            repo.load_project_config("/not/exists")

        # 品質設定のテスト
        quality_config = {"strict_mode": True, "min_score": 80}
        repo.save_quality_config("/test/project", quality_config)

        loaded_quality = repo.load_quality_config("/test/project")
        assert loaded_quality["strict_mode"] is True

        # デフォルト品質設定のテスト
        default_quality = repo.load_quality_config("/no/quality/config")
        assert "default" in default_quality


class TestManuscriptRepository:
    """原稿リポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-INTERFACE_DEFINITION")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(ManuscriptRepository, ABC)

        methods = ["load_episode_content", "save_episode_content", "list_episodes"]
        for method in methods:
            assert hasattr(ManuscriptRepository, method)

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-METHOD_SIGNATURES")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""

        # モック実装を作成
        class MockManuscriptRepo(ManuscriptRepository):
            def __init__(self) -> None:
                self.manuscripts = {}

            def load_episode_content(self, project_path: str, episode_number: int) -> str:
                key = f"{project_path}:{episode_number}"
                if key not in self.manunoveler:
                    msg = f"原稿が見つかりません: 第{episode_number}話"
                    raise FileNotFoundError(msg)
                return self.manuscripts[key]

            def save_episode_content(self, project_path: str, episode_number: int, content: str) -> None:
                key = f"{project_path}:{episode_number}"
                self.manuscripts[key] = content

            def list_episodes(self, project_path: str) -> list[int]:
                episodes = []
                for key in self.manunoveler:
                    if key.startswith(f"{project_path}:"):
                        episode_num = int(key.split(":")[1])
                        episodes.append(episode_num)
                return sorted(episodes)

        repo = MockManuscriptRepo()

        # 原稿の保存と読み込み
        content = "# 第1話 タイトル\n\n本文が始まります..."
        repo.save_episode_content("/test/project", 1, content)

        loaded = repo.load_episode_content("/test/project", 1)
        assert loaded == content

        # 複数エピソードの管理
        repo.save_episode_content("/test/project", 2, "第2話の内容")
        repo.save_episode_content("/test/project", 3, "第3話の内容")

        episodes = repo.list_episodes("/test/project")
        assert episodes == [1, 2, 3]

        # 存在しないエピソードの読み込み
        with pytest.raises(FileNotFoundError, match=".*"):
            repo.load_episode_content("/test/project", 999)


class TestEpisodeManagementDataRepository:
    """話数管理データリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-INTERFACE_DEFINITION")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(EpisodeManagementDataRepository, ABC)

        methods = [
            "load_episode_management",
            "save_episode_management",
            "get_episode_metadata",
            "update_episode_metadata",
        ]
        for method in methods:
            assert hasattr(EpisodeManagementDataRepository, method)

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-METHOD_SIGNATURES")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""

        # モック実装を作成
        class MockEpisodeManagementRepo(EpisodeManagementDataRepository):
            def __init__(self) -> None:
                self.management_data = {}

            def load_episode_management(self, project_path: str) -> dict[str, object]:
                if project_path not in self.management_data:
                    return {"episodes": {}}
                return self.management_data[project_path]

            def save_episode_management(self, project_path: str, data: dict[str, object]) -> None:
                self.management_data[project_path] = data

            def get_episode_metadata(self, project_path: str, episode_number: int) -> dict[str, object]:
                data = self.load_episode_management(project_path)
                episodes = data.get("episodes", {})
                return episodes.get(str(episode_number), {})

            def update_episode_metadata(
                self, project_path: str, episode_number: int, metadata: dict[str, object]
            ) -> None:
                data = self.load_episode_management(project_path)
                if "episodes" not in data:
                    data["episodes"] = {}
                data["episodes"][str(episode_number)] = metadata
                self.save_episode_management(project_path, data)

        repo = MockEpisodeManagementRepo()

        # 話数管理データの保存と読み込み
        management_data = {
            "episodes": {"1": {"title": "第1話", "status": "published"}, "2": {"title": "第2話", "status": "draft"}}
        }
        repo.save_episode_management("/test/project", management_data)

        loaded = repo.load_episode_management("/test/project")
        assert "episodes" in loaded
        assert len(loaded["episodes"]) == 2

        # 個別エピソードのメタデータ取得
        metadata = repo.get_episode_metadata("/test/project", 1)
        assert metadata["title"] == "第1話"
        assert metadata["status"] == "published"

        # メタデータの更新
        new_metadata = {"title": "第1話 改訂版", "status": "revised", "word_count": 3000}
        repo.update_episode_metadata("/test/project", 1, new_metadata)

        updated = repo.get_episode_metadata("/test/project", 1)
        assert updated["title"] == "第1話 改訂版"
        assert updated["word_count"] == 3000


class TestTemplateRepository:
    """テンプレートリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-INTERFACE_DEFINITION")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(TemplateRepository, ABC)

        methods = ["load_template", "get_template_path"]
        for method in methods:
            assert hasattr(TemplateRepository, method)

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-METHOD_SIGNATURES")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""

        # モック実装を作成
        class MockTemplateRepo(TemplateRepository):
            def __init__(self) -> None:
                self.templates = {
                    WorkflowStageType.MASTER_PLOT: {"template": "全体構成テンプレート"},
                    WorkflowStageType.CHAPTER_PLOT: {"template": "章別プロットテンプレート"},
                    WorkflowStageType.EPISODE_PLOT: {"template": "話数別プロットテンプレート"},
                }

            def load_template(self, stage_type: WorkflowStageType) -> dict[str, object]:
                if stage_type not in self.templates:
                    msg = f"テンプレートが見つかりません: {stage_type.value}"
                    raise FileNotFoundError(msg)
                return self.templates[stage_type]

            def get_template_path(self, stage_type: WorkflowStageType) -> str:
                paths = {
                    WorkflowStageType.MASTER_PLOT: "/templates/master_plot.yaml",
                    WorkflowStageType.CHAPTER_PLOT: "/templates/chapter_plot.yaml",
                    WorkflowStageType.EPISODE_PLOT: "/templates/episode_plot.yaml",
                }
                return paths.get(stage_type, "/templates/unknown.yaml")

        repo = MockTemplateRepo()

        # テンプレートの読み込み
        master_template = repo.load_template(WorkflowStageType.MASTER_PLOT)
        assert "template" in master_template

        chapter_template = repo.load_template(WorkflowStageType.CHAPTER_PLOT)
        assert chapter_template["template"] == "章別プロットテンプレート"

        # テンプレートパスの取得
        path = repo.get_template_path(WorkflowStageType.EPISODE_PLOT)
        assert path == "/templates/episode_plot.yaml"


class TestFileSystemRepository:
    """ファイルシステムリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-INTERFACE_DEFINITION")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(FileSystemRepository, ABC)

        methods = [
            "exists",
            "is_directory",
            "list_files",
            "get_file_info",
            "calculate_hash",
            "get_modification_time",
            "read_yaml",
            "write_yaml",
        ]
        for method in methods:
            assert hasattr(FileSystemRepository, method)

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-METHOD_SIGNATURES")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""

        # モック実装を作成
        class MockFileSystemRepo(FileSystemRepository):
            def __init__(self) -> None:
                self.files = {}
                self.directories = set()
                self.yaml_data = {}

            def exists(self, path: str) -> bool:
                return path in self.files or path in self.directories

            def is_directory(self, path: str) -> bool:
                return path in self.directories

            def list_files(self, directory: str, extensions: set[str] | None = None) -> list[str]:
                files = []
                for file_path in self.files:
                    if file_path.startswith(directory + "/"):
                        if extensions:
                            if any(file_path.endswith(ext) for ext in extensions):
                                files.append(file_path)
                        else:
                            files.append(file_path)
                return files

            def get_file_info(self, file_path: str) -> dict[str, object] | None:
                if file_path not in self.files:
                    return None
                return {
                    "mtime": 1234567890.0,
                    "size": len(self.files[file_path]),
                    "hash": f"hash_{file_path}",
                    "path": file_path,
                }

            def calculate_hash(self, file_path: str) -> str | None:
                if file_path not in self.files:
                    return None
                return f"sha256_{file_path}"

            def get_modification_time(self, file_path: str) -> datetime | None:
                if file_path not in self.files:
                    return None
                return datetime.fromtimestamp(1234567890.0)

            def read_yaml(self, file_path: str) -> dict[str, object] | None:
                return self.yaml_data.get(file_path)

            def write_yaml(self, file_path: str, data: dict[str, object]) -> bool:
                self.yaml_data[file_path] = data
                self.files[file_path] = "yaml_content"
                return True

        repo = MockFileSystemRepo()

        # ファイルとディレクトリの管理
        repo.directories.add("/test/project")
        repo.files["/test/project/file1.yaml"] = "content1"
        repo.files["/test/project/file2.txt"] = "content2"

        assert repo.exists("/test/project") is True
        assert repo.is_directory("/test/project") is True
        assert repo.exists("/test/project/file1.yaml") is True
        assert repo.is_directory("/test/project/file1.yaml") is False

        # ファイルリスト
        all_files = repo.list_files("/test/project")
        assert len(all_files) == 2

        yaml_files = repo.list_files("/test/project", extensions={".yaml", ".yml"})
        assert len(yaml_files) == 1
        assert yaml_files[0].endswith(".yaml")

        # ファイル情報
        info = repo.get_file_info("/test/project/file1.yaml")
        assert info is not None
        assert info["size"] == 8  # len("content1")
        assert "hash" in info

        # ハッシュ計算
        hash_value = repo.calculate_hash("/test/project/file1.yaml")
        assert hash_value is not None
        assert hash_value.startswith("sha256_")

        # YAMLファイル操作
        yaml_data = {"test": "data", "number": 123}
        assert repo.write_yaml("/test/project/config.yaml", yaml_data) is True

        loaded = repo.read_yaml("/test/project/config.yaml")
        assert loaded is not None
        assert loaded["test"] == "data"
        assert loaded["number"] == 123


class TestRepositoryIntegration:
    """リポジトリインターフェースの統合テスト"""

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-REPOSITORIES_FOLLOW_")
    def test_repositories_follow_ddd_principles(self) -> None:
        """リポジトリがDDD原則に従っていることを確認"""
        repositories = [
            ConfigurationRepository,
            ManuscriptRepository,
            EpisodeManagementDataRepository,
            TemplateRepository,
            FileSystemRepository,
        ]

        for repo in repositories:
            assert issubclass(repo, ABC)

    @pytest.mark.spec("SPEC-CONFIG_TEMPLATE_FILESYSTEM_REPOSITORIES-REPOSITORY_SEPARATIO")
    def test_repository_separation_of_concerns(self) -> None:
        """リポジトリが適切に関心事を分離していることを確認"""
        # ConfigurationRepository: 設定ファイルの管理
        # ManuscriptRepository: 原稿ファイルの管理
        # EpisodeManagementDataRepository: 話数管理データの管理
        # TemplateRepository: テンプレートファイルの管理
        # FileSystemRepository: 汎用的なファイルシステム操作

        # 各リポジトリが独自の責務を持つことを確認
        config_methods = set(dir(ConfigurationRepository))
        manuscript_methods = set(dir(ManuscriptRepository))
        episode_mgmt_methods = set(dir(EpisodeManagementDataRepository))

        # 重複するメソッド名が少ないことを確認(抽象メソッド以外)
        common_methods = config_methods & manuscript_methods & episode_mgmt_methods
        abstract_methods = {"__abstractmethods__", "__class__", "__module__", "__dict__", "__weakref__"}

        # 共通メソッドは抽象メソッド関連のみであるべき
        non_abstract_common = common_methods - abstract_methods
        assert len(non_abstract_common) < 5  # 許容範囲内の共通メソッド数
