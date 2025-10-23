"""エピソードとプロジェクトリポジトリインターフェーステスト"""

from abc import ABC
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from noveler.domain.entities.episode import Episode
from noveler.domain.repositories.episode_repository import (
    AdvancedEpisodeRepository,
    EpisodeQuery,
    EpisodeRepository,
)
from noveler.domain.repositories.project_repository import ProjectRepository
from noveler.domain.value_objects.project_time import project_now


class TestEpisodeRepository:
    """エピソードリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(EpisodeRepository, ABC)

        # 全メソッドの存在確認
        methods = [
            "save",
            "find_by_id",
            "find_by_project_and_number",
            "find_all_by_project",
            "find_by_status",
            "find_by_date_range",
            "delete",
            "get_next_episode_number",
            "get_episode_count",
            "get_total_word_count",
            "find_by_tags",
            "find_by_quality_score_range",
            "find_ready_for_publication",
            "get_statistics",
            "bulk_update_status",
            "backup_episode",
            "restore_episode",
        ]
        for method in methods:
            assert hasattr(EpisodeRepository, method)

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_abstract_methods(self) -> None:
        """抽象メソッドの定義を確認"""
        with pytest.raises(TypeError, match=".*"):
            EpisodeRepository()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""
        # from noveler.domain.entities.episode import Episode  # Moved to top-level

        # モックエピソードの作成
        mock_episode = Mock(spec=Episode)
        mock_episode.id = "episode001"
        mock_episode.episode_number = 1
        mock_episode.status = "draft"
        mock_episode.word_count = 3000
        mock_episode.quality_score = 85.0
        mock_episode.tags = ["アクション", "バトル"]

        # モック実装を作成
        class MockEpisodeRepo(EpisodeRepository):
            def __init__(self) -> None:
                self.episodes = {}

            def save(self, episode: Episode, _project_id: str) -> None:
                key = f"{_project_id}:{episode.id}"
                self.episodes[key] = episode

            def find_by_id(self, _episode_id: str, _project_id: str) -> Episode | None:
                key = f"{_project_id}:{_episode_id}"
                return self.episodes.get(key)

            def find_by_project_and_number(self, _project_id: str, episode_number: int) -> Episode | None:
                for key, ep in self.episodes.items():
                    if key.startswith(f"{_project_id}:") and ep.episode_number == episode_number:
                        return ep
                return None

            def find_all_by_project(self, project_id: str) -> list[Episode]:
                return [ep for key, ep in self.episodes.items() if key.startswith(f"{project_id}:")]

            def find_by_status(self, project_id: str, status: str) -> list[Episode]:
                return [
                    ep for key, ep in self.episodes.items() if key.startswith(f"{project_id}:") and ep.status == status
                ]

            def find_by_date_range(self, _project_id: str, _start_date: datetime, _end_date: datetime) -> list[Episode]:
                # 実装例
                return []

            def delete(self, _episode_id: str, _project_id: str) -> bool:
                key = f"{_project_id}:{_episode_id}"
                if key in self.episodes:
                    del self.episodes[key]
                    return True
                return False

            def get_next_episode_number(self, project_id: str) -> int:
                project_episodes = self.find_all_by_project(project_id)
                if not project_episodes:
                    return 1
                return max(ep.episode_number for ep in project_episodes) + 1

            def get_episode_count(self, project_id: str) -> int:
                return len(self.find_all_by_project(project_id))

            def get_total_word_count(self, project_id: str) -> int:
                return sum(ep.word_count for ep in self.find_all_by_project(project_id))

            def find_by_tags(self, project_id: str, tags: list[str]) -> list[Episode]:
                result = []
                for key, ep in self.episodes.items():
                    if key.startswith(f"{project_id}:") and any(tag in ep.tags for tag in tags):
                        result.append(ep)
                return result

            def find_by_quality_score_range(self, project_id: str, min_score: float, max_score: float) -> list[Episode]:
                return [
                    ep
                    for key, ep in self.episodes.items()
                    if key.startswith(f"{project_id}:") and min_score <= ep.quality_score <= max_score
                ]

            def find_ready_for_publication(self, project_id: str) -> list[Episode]:
                return [
                    ep
                    for key, ep in self.episodes.items()
                    if key.startswith(f"{project_id}:") and ep.status == "ready_for_publication"
                ]

            def get_statistics(self, project_id: str) -> dict[str, object]:
                episodes = self.find_all_by_project(project_id)
                return {
                    "total_episodes": len(episodes),
                    "total_word_count": sum(ep.word_count for ep in episodes),
                    "average_quality_score": sum(ep.quality_score for ep in episodes) / len(episodes)
                    if episodes
                    else 0,
                }

            def bulk_update_status(self, project_id: str, episode_ids: list[str], new_status: str) -> int:
                count = 0
                for episode_id in episode_ids:
                    key = f"{project_id}:{episode_id}"
                    if key in self.episodes:
                        self.episodes[key].status = new_status
                        count += 1
                return count

            def backup_episode(self, _episode_id: str, _project_id: str) -> bool:
                return True  # 実装例

            def restore_episode(self, _episode_id: str, _project_id: str, _backup_version: str) -> bool:
                return True  # 実装例

        repo = MockEpisodeRepo()

        # 各メソッドのテスト
        repo.save(mock_episode, "test_project")
        assert repo.find_by_id("episode001", "test_project") == mock_episode
        assert repo.find_by_id("not_exists", "test_project") is None

        found = repo.find_by_project_and_number("test_project", 1)
        assert found == mock_episode

        all_episodes = repo.find_all_by_project("test_project")
        assert len(all_episodes) == 1

        assert repo.get_next_episode_number("test_project") == 2
        assert repo.get_episode_count("test_project") == 1
        assert repo.get_total_word_count("test_project") == 3000

        by_tags = repo.find_by_tags("test_project", ["アクション"])
        assert len(by_tags) == 1

        by_score = repo.find_by_quality_score_range("test_project", 80.0, 90.0)
        assert len(by_score) == 1

        stats = repo.get_statistics("test_project")
        assert stats["total_episodes"] == 1
        assert stats["average_quality_score"] == 85.0

        assert repo.delete("episode001", "test_project") is True
        assert repo.find_by_id("episode001", "test_project") is None


class TestEpisodeQuery:
    """エピソード検索クエリのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_query_builder(self) -> None:
        """クエリビルダーの動作確認"""
        query = EpisodeQuery()

        # メソッドチェーン
        query = (
            query.with_project("test_project")
            .with_episode_numbers([1, 2, 3])
            .with_statuses(["draft", "published"])
            .with_tags(["バトル", "ファンタジー"])
            .with_word_count_range(1000, 5000)
            .with_quality_score_range(70.0, 100.0)
            .order_by_field("created_at", desc=True)
            .with_pagination(limit=10, offset=20)
        )

        assert query.project_id == "test_project"
        assert query.episode_numbers == [1, 2, 3]
        assert query.statuses == ["draft", "published"]
        assert query.tags == ["バトル", "ファンタジー"]
        assert query.min_word_count == 1000
        assert query.max_word_count == 5000
        assert query.min_quality_score == 70.0
        assert query.max_quality_score == 100.0
        assert query.order_by == "created_at"
        assert query.order_desc is True
        assert query.limit == 10
        assert query.offset == 20

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_date_range_query(self) -> None:
        """日付範囲クエリのテスト"""
        query = EpisodeQuery()
        now = project_now().datetime
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        query = query.with_created_date_range(yesterday, tomorrow)
        assert query.created_after == yesterday
        assert query.created_before == tomorrow

        query = query.with_updated_date_range(yesterday, tomorrow)
        assert query.updated_after == yesterday
        assert query.updated_before == tomorrow


class TestAdvancedEpisodeRepository:
    """高度なエピソードリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(AdvancedEpisodeRepository, EpisodeRepository)
        assert hasattr(AdvancedEpisodeRepository, "find_by_query")
        assert hasattr(AdvancedEpisodeRepository, "count_by_query")

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_inheritance(self) -> None:
        """継承関係の確認"""
        # AdvancedEpisodeRepositoryはEpisodeRepositoryのすべてのメソッドを持つ
        base_methods = [attr for attr in dir(EpisodeRepository) if not attr.startswith("_")]
        for method in base_methods:
            assert hasattr(AdvancedEpisodeRepository, method)


class TestProjectRepository:
    """プロジェクトリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(ProjectRepository, ABC)

        # 全メソッドの存在確認
        methods = [
            "exists",
            "create",
            "get_project_info",
            "update_project_info",
            "delete",
            "get_all_projects",
            "get_project_settings",
            "update_project_settings",
            "get_project_metadata",
            "set_project_metadata",
            "archive_project",
            "restore_project",
            "get_project_statistics",
            "backup_project",
            "get_project_directory",
            "validate_project_structure",
            "initialize_project_structure",
            "get_project_root",
        ]
        for method in methods:
            assert hasattr(ProjectRepository, method)

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_abstract_methods(self) -> None:
        """抽象メソッドの定義を確認"""
        with pytest.raises(TypeError, match=".*"):
            ProjectRepository()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""

        # モック実装を作成
        class MockProjectRepo(ProjectRepository):
            def __init__(self) -> None:
                self.projects = {}
                self.settings = {}
                self.metadata = {}

            def exists(self, project_id: str) -> bool:
                return project_id in self.projects

            def create(self, project_id: str, project_data: dict[str, object]) -> bool:
                if project_id not in self.projects:
                    self.projects[project_id] = project_data
                    return True
                return False

            def get_project_info(self, project_id: str) -> dict[str, object] | None:
                return self.projects.get(project_id)

            def update_project_info(self, project_id: str, project_data: dict[str, object]) -> bool:
                if project_id in self.projects:
                    self.projects[project_id].update(project_data)
                    return True
                return False

            def delete(self, project_id: str) -> bool:
                if project_id in self.projects:
                    del self.projects[project_id]
                    return True
                return False

            def get_all_projects(self) -> list[dict[str, object]]:
                return list(self.projects.values())

            def get_project_settings(self, project_id: str) -> dict[str, object] | None:
                return self.settings.get(project_id)

            def update_project_settings(self, project_id: str, settings: dict[str, object]) -> bool:
                self.settings[project_id] = settings
                return True

            def get_project_metadata(self, project_id: str) -> dict[str, object] | None:
                return self.metadata.get(project_id)

            def set_project_metadata(self, project_id: str, key: str, value: object) -> bool:
                if project_id not in self.metadata:
                    self.metadata[project_id] = {}
                self.metadata[project_id][key] = value
                return True

            def archive_project(self, project_id: str) -> bool:
                if project_id in self.projects:
                    self.projects[project_id]["archived"] = True
                    return True
                return False

            def restore_project(self, project_id: str) -> bool:
                if project_id in self.projects:
                    self.projects[project_id]["archived"] = False
                    return True
                return False

            def get_project_statistics(self, project_id: str) -> dict[str, object] | None:
                if project_id in self.projects:
                    return {"episode_count": 0, "word_count": 0, "quality_score": 0.0}
                return None

            def backup_project(self, project_id: str) -> bool:
                return project_id in self.projects

            def get_project_directory(self, project_id: str) -> str | None:
                if project_id in self.projects:
                    return f"/projects/{project_id}"
                return None

            def validate_project_structure(self, project_id: str) -> dict[str, object]:
                return {"valid": project_id in self.projects, "errors": [], "warnings": []}

            def initialize_project_structure(self, project_id: str) -> bool:
                return project_id in self.projects

            def get_project_root(self, project_id: str) -> str:
                return f"/root/{project_id}"

        repo = MockProjectRepo()

        # 各メソッドのテスト
        assert repo.exists("test_project") is False

        project_data = {"name": "テストプロジェクト", "author": "作者名"}
        assert repo.create("test_project", project_data) is True
        assert repo.exists("test_project") is True

        info = repo.get_project_info("test_project")
        assert info is not None
        assert info["name"] == "テストプロジェクト"

        assert repo.update_project_info("test_project", {"genre": "ファンタジー"}) is True
        info = repo.get_project_info("test_project")
        assert "genre" in info

        all_projects = repo.get_all_projects()
        assert len(all_projects) == 1

        assert repo.update_project_settings("test_project", {"auto_save": True}) is True
        settings = repo.get_project_settings("test_project")
        assert settings is not None
        assert settings["auto_save"] is True

        assert repo.set_project_metadata("test_project", "version", "1.0.0") is True
        metadata = repo.get_project_metadata("test_project")
        assert metadata is not None
        assert metadata["version"] == "1.0.0"

        assert repo.archive_project("test_project") is True
        assert repo.restore_project("test_project") is True

        stats = repo.get_project_statistics("test_project")
        assert stats is not None
        assert "episode_count" in stats

        assert repo.backup_project("test_project") is True

        directory = repo.get_project_directory("test_project")
        assert directory == "/projects/test_project"

        validation = repo.validate_project_structure("test_project")
        assert validation["valid"] is True

        assert repo.initialize_project_structure("test_project") is True

        root = repo.get_project_root("test_project")
        assert root == "/root/test_project"

        assert repo.delete("test_project") is True
        assert repo.exists("test_project") is False


class TestRepositoryIntegration:
    """リポジトリインターフェースの統合テスト"""

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_repositories_follow_ddd_principles(self) -> None:
        """リポジトリがDDD原則に従っていることを確認"""
        repositories = [
            EpisodeRepository,
            AdvancedEpisodeRepository,
            ProjectRepository,
        ]

        for repo in repositories:
            assert issubclass(repo, ABC)

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_repository_method_naming_convention(self) -> None:
        """メソッド命名規則の確認"""
        # 検索メソッドは find_ または get_ で始まる
        # 永続化メソッドは save, create, update
        # 削除メソッドは delete
        # 確認メソッドは exists
        # アクションメソッドは動詞で始まる(archive, restore, backup等)
        episode_methods = dir(EpisodeRepository)
        project_methods = dir(ProjectRepository)

        # 一般的なメソッドパターンの確認
        search_prefixes = ["find_", "get_"]
        action_verbs = [
            "save",
            "create",
            "update",
            "delete",
            "archive",
            "restore",
            "backup",
            "validate",
            "initialize",
            "bulk_",
            "exists",
        ]

        for method in episode_methods + project_methods:
            if method.startswith("_"):
                continue

            # メソッド名が適切なパターンに従っているか確認
            valid_pattern = False
            for prefix in search_prefixes + action_verbs:
                if method.startswith(prefix):
                    valid_pattern = True
                    break

            # 抽象メソッド以外はパターンに従うべき
            if not method.startswith("__") and method not in ["__class__", "__module__"]:
                assert valid_pattern, f"Method '{method}' does not follow naming convention"
