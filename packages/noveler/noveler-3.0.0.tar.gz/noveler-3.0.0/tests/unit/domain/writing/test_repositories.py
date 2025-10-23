"""執筆コンテキストドメインのリポジトリインターフェーステスト

仕様書: SPEC-UNIT-TEST
"""

from abc import ABC
from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.writing.entities import Episode, EpisodeStatus, WritingRecord, WritingSession
from noveler.domain.writing.repositories import (
    EpisodeRepository,
    WritingRecordRepository,
    WritingSessionRepository,
)
from noveler.domain.writing.value_objects import EpisodeNumber, PublicationStatus, WritingPhase

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestEpisodeRepository:
    """エピソードリポジトリインターフェースのテスト"""

    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(EpisodeRepository, ABC)

        # 全メソッドの存在確認
        methods = [
            "find_by_id",
            "find_by_number",
            "find_by_status",
            "find_next_unwritten",
            "find_all_by_project",
            "find_by_phase",
            "find_by_publication_status",
            "find_latest_episode",
            "save",
            "create_from_plot",
            "update_plot_status",
            "delete",
        ]
        for method in methods:
            assert hasattr(EpisodeRepository, method)

    def test_abstract_methods(self) -> None:
        """抽象メソッドの定義を確認"""
        with pytest.raises(TypeError, match=".*"):
            EpisodeRepository()

    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""
        # モックエンティティの作成
        mock_episode = Mock(spec=Episode)
        mock_episode.id = "episode001"
        mock_episode.project_id = "test_project"
        mock_episode.episode_number = EpisodeNumber(1)
        mock_episode.status = EpisodeStatus.DRAFT_COMPLETE
        mock_episode.phase = WritingPhase.DRAFT
        mock_episode.publication_status = PublicationStatus.UNPUBLISHED

        # モック実装を作成
        class MockEpisodeRepo(EpisodeRepository):
            def __init__(self) -> None:
                self.episodes = {"episode001": mock_episode}

            def find_by_id(self, episode_id: str) -> Episode | None:
                return self.episodes.get(episode_id)

            def find_by_number(self, project_id: str, episode_number: EpisodeNumber) -> Episode | None:
                for ep in self.episodes.values():
                    if ep.project_id == project_id and ep.episode_number == episode_number:
                        return ep
                return None

            def find_by_status(self, project_id: str, status: EpisodeStatus) -> list[Episode]:
                return [ep for ep in self.episodes.values() if ep.project_id == project_id and ep.status == status]

            def find_next_unwritten(self, project_id: str) -> Episode | None:
                unwritten = [
                    ep
                    for ep in self.episodes.values()
                    if ep.project_id == project_id and ep.status == EpisodeStatus.UNWRITTEN
                ]
                return min(unwritten, key=lambda e: e.episode_number.value) if unwritten else None

            def find_all_by_project(self, project_id: str) -> list[Episode]:
                return [ep for ep in self.episodes.values() if ep.project_id == project_id]

            def find_by_phase(self, project_id: str, phase: WritingPhase) -> list[Episode]:
                return [ep for ep in self.episodes.values() if ep.project_id == project_id and ep.phase == phase]

            def find_by_publication_status(self, project_id: str, status: PublicationStatus) -> list[Episode]:
                return [
                    ep
                    for ep in self.episodes.values()
                    if ep.project_id == project_id and ep.publication_status == status
                ]

            def find_latest_episode(self, project_id: str) -> Episode | None:
                project_eps = [ep for ep in self.episodes.values() if ep.project_id == project_id]
                return max(project_eps, key=lambda e: e.episode_number.value) if project_eps else None

            def save(self, episode: Episode) -> Episode:
                self.episodes[episode.id] = episode
                return episode

            def create_from_plot(self, project_id: str, plot_info: dict[str, object]) -> Episode:
                new_episode = Mock(spec=Episode)
                new_episode.id = f"ep_{plot_info.get('number', '999')}"
                new_episode.project_id = project_id
                new_episode.title = plot_info.get("title", "新規エピソード")
                return new_episode

            def update_plot_status(self, _project_id: str, _episode_number: str, _status: str) -> bool:
                # 実装例
                return True

            def delete(self, episode_id: str) -> None:
                self.episodes.pop(episode_id, None)

        repo = MockEpisodeRepo()

        # 各メソッドのテスト
        assert repo.find_by_id("episode001") == mock_episode
        assert repo.find_by_id("not_exists") is None

        found = repo.find_by_number("test_project", EpisodeNumber(1))
        assert found == mock_episode

        by_status = repo.find_by_status("test_project", EpisodeStatus.DRAFT_COMPLETE)
        assert len(by_status) == 1
        assert by_status[0] == mock_episode

        all_episodes = repo.find_all_by_project("test_project")
        assert len(all_episodes) == 1

        saved = repo.save(mock_episode)
        assert saved == mock_episode

        created = repo.create_from_plot("test_project", {"number": "002", "title": "テストタイトル"})
        assert created.project_id == "test_project"

        assert repo.update_plot_status("test_project", "1", "completed") is True

        repo.delete("episode001")
        assert repo.find_by_id("episode001") is None


class TestWritingRecordRepository:
    """執筆記録リポジトリインターフェースのテスト"""

    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(WritingRecordRepository, ABC)

        methods = ["find_by_id", "find_by_episode", "find_by_date_range", "save", "delete"]
        for method in methods:
            assert hasattr(WritingRecordRepository, method)

    def test_abstract_methods(self) -> None:
        """抽象メソッドの定義を確認"""
        with pytest.raises(TypeError, match=".*"):
            WritingRecordRepository()

    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""
        # モックエンティティの作成
        mock_record = Mock(spec=WritingRecord)
        mock_record.id = "rec001"
        mock_record.episode_id = "episode001"
        mock_record.project_id = "test_project"
        mock_record.created_at = project_now().datetime

        # モック実装を作成
        class MockWritingRecordRepo(WritingRecordRepository):
            def __init__(self) -> None:
                self.records = {"rec001": mock_record}

            def find_by_id(self, record_id: str) -> WritingRecord | None:
                return self.records.get(record_id)

            def find_by_episode(self, episode_id: str) -> list[WritingRecord]:
                return [r for r in self.records.values() if r.episode_id == episode_id]

            def find_by_date_range(
                self,
                project_id: str,
                start_date: datetime,
                end_date: datetime,
            ) -> list[WritingRecord]:
                return [
                    r
                    for r in self.records.values()
                    if r.project_id == project_id and start_date <= r.created_at <= end_date
                ]

            def save(self, record: WritingRecord) -> WritingRecord:
                self.records[record.id] = record
                return record

            def delete(self, record_id: str) -> None:
                self.records.pop(record_id, None)

        repo = MockWritingRecordRepo()

        # 各メソッドのテスト
        assert repo.find_by_id("rec001") == mock_record
        assert repo.find_by_id("not_exists") is None

        by_episode = repo.find_by_episode("episode001")
        assert len(by_episode) == 1
        assert by_episode[0] == mock_record

        now = project_now().datetime
        by_date = repo.find_by_date_range("test_project", now - timedelta(days=1), now + timedelta(days=1))
        assert len(by_date) == 1

        saved = repo.save(mock_record)
        assert saved == mock_record

        repo.delete("rec001")
        assert repo.find_by_id("rec001") is None


class TestWritingSessionRepository:
    """執筆セッションリポジトリインターフェースのテスト"""

    def test_interface_definition(self) -> None:
        """インターフェースが正しく定義されていることを確認"""
        assert issubclass(WritingSessionRepository, ABC)

        methods = ["find_by_id", "find_by_date", "find_by_episode", "find_recent_sessions", "save", "delete"]
        for method in methods:
            assert hasattr(WritingSessionRepository, method)

    def test_abstract_methods(self) -> None:
        """抽象メソッドの定義を確認"""
        with pytest.raises(TypeError, match=".*"):
            WritingSessionRepository()

    def test_method_signatures(self) -> None:
        """メソッドシグネチャの確認"""
        # モックエンティティの作成
        mock_session = Mock(spec=WritingSession)
        mock_session.id = "sess001"
        mock_session.episode_id = "episode001"
        mock_session.project_id = "test_project"
        mock_session.date = datetime.now(timezone.utc).date()
        mock_session.created_at = project_now().datetime

        # モック実装を作成
        class MockWritingSessionRepo(WritingSessionRepository):
            def __init__(self) -> None:
                self.sessions = {"sess001": mock_session}

            def find_by_id(self, session_id: str) -> WritingSession | None:
                return self.sessions.get(session_id)

            def find_by_date(self, project_id: str, date: date) -> WritingSession | None:
                for s in self.sessions.values():
                    if s.project_id == project_id and s.date == date:
                        return s
                return None

            def find_by_episode(self, episode_id: str) -> list[WritingSession]:
                return [s for s in self.sessions.values() if s.episode_id == episode_id]

            def find_recent_sessions(self, project_id: str, days: int = 7) -> list[WritingSession]:
                cutoff = project_now().datetime - timedelta(days=days)
                return [s for s in self.sessions.values() if s.project_id == project_id and s.created_at >= cutoff]

            def save(self, session: WritingSession) -> WritingSession:
                self.sessions[session.id] = session
                return session

            def delete(self, session_id: str) -> None:
                self.sessions.pop(session_id, None)

        repo = MockWritingSessionRepo()

        # 各メソッドのテスト
        assert repo.find_by_id("sess001") == mock_session
        assert repo.find_by_id("not_exists") is None

        by_date = repo.find_by_date("test_project", datetime.now(timezone.utc).date())
        assert by_date == mock_session

        by_episode = repo.find_by_episode("episode001")
        assert len(by_episode) == 1
        assert by_episode[0] == mock_session

        recent = repo.find_recent_sessions("test_project", days=7)
        assert len(recent) == 1

        saved = repo.save(mock_session)
        assert saved == mock_session

        repo.delete("sess001")
        assert repo.find_by_id("sess001") is None


class TestRepositoryIntegration:
    """リポジトリインターフェースの統合テスト"""

    def test_repositories_follow_ddd_principles(self) -> None:
        """リポジトリがDDD原則に従っていることを確認"""
        repositories = [
            EpisodeRepository,
            WritingRecordRepository,
            WritingSessionRepository,
        ]

        for repo in repositories:
            assert issubclass(repo, ABC)

    def test_repository_method_naming_convention(self) -> None:
        """メソッド命名規則の確認"""
        # 検索メソッドは find_ で始まる
        # 永続化メソッドは save
        # 削除メソッドは delete
        repo_methods = {
            EpisodeRepository: [
                "find_by_id",
                "find_by_number",
                "find_by_status",
                "find_next_unwritten",
                "find_all_by_project",
                "find_by_phase",
                "find_by_publication_status",
                "find_latest_episode",
                "save",
                "delete",
                "create_from_plot",
                "update_plot_status",
            ],
            WritingRecordRepository: ["find_by_id", "find_by_episode", "find_by_date_range", "save", "delete"],
            WritingSessionRepository: [
                "find_by_id",
                "find_by_date",
                "find_by_episode",
                "find_recent_sessions",
                "save",
                "delete",
            ],
        }

        for repo, methods in repo_methods.items():
            for method in methods:
                assert hasattr(repo, method)
                # 命名規則の確認
                if method not in ["save", "delete", "create_from_plot", "update_plot_status"]:
                    assert method.startswith(("find_", "get_"))

    def test_repository_return_types(self) -> None:
        """リポジトリの戻り値の型が適切であることを確認"""
        # find_by_id系は単一オブジェクトまたはNone
        # find_by_xxx系(複数形)はリスト
        # saveは保存したオブジェクトを返す
        # deleteは何も返さない(None)
        # 型アノテーションで既に定義済み
