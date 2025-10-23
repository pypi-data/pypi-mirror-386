"""DDD-compliant TDD Test Suite for Writing System
DDD原則に準拠した執筆システムのTDDテストスイート

既存のTDDテストをDDDアーキテクチャに対応してリファクタリング


仕様書: SPEC-UNIT-TEST
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

# Add parent directory to path
# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()

from noveler.application.use_cases.create_episode_from_plot import CreateEpisodeCommand, CreateEpisodeFromPlotUseCase
from noveler.application.use_cases.track_writing_progress import ProgressQuery, TrackWritingProgressUseCase
from noveler.domain.writing.entities import Episode, EpisodeStatus
from noveler.domain.writing.value_objects import EpisodeNumber, EpisodeTitle, WordCount
from noveler.infrastructure.persistence.ddd_episode_repository import FileEpisodeRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestDomainEntities:
    """ドメインエンティティのテスト(DDDアプローチ)"""

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-EPISODE_SHOULD_START")
    def test_episode_should_start_writing_when_unwritten(self) -> None:
        """未執筆状態のエピソードは執筆開始できるべき"""
        # Arrange
        get_common_path_service()
        episode = Episode(
            id="episode001",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テストエピソード"),
            status=EpisodeStatus.UNWRITTEN,
        )

        # Act
        episode.start_writing()

        # Assert
        assert episode.status == EpisodeStatus.IN_PROGRESS
        assert episode.updated_at is not None

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-EPISODE_SHOULD_NOT_S")
    def test_episode_should_not_start_writing_when_already_in_progress(self) -> None:
        """既に執筆中のエピソードは執筆開始できないべき"""
        # Arrange
        episode = Episode(
            id="episode001",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テストエピソード"),
            status=EpisodeStatus.IN_PROGRESS,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="執筆開始できません"):
            episode.start_writing()

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-EPISODE_SHOULD_COMPL")
    def test_episode_should_complete_draft_when_content_exists(self) -> None:
        """内容があるエピソードは初稿完了できるべき"""
        # Arrange
        episode = Episode(
            id="episode001",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テストエピソード"),
            content="これはテスト内容です。",
            status=EpisodeStatus.IN_PROGRESS,
        )

        # Act
        episode.complete_draft()

        # Assert
        assert episode.status == EpisodeStatus.DRAFT_COMPLETE
        assert episode.word_count.value > 0

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-EPISODE_SHOULD_NOT_C")
    def test_episode_should_not_complete_draft_when_content_empty(self) -> None:
        """内容が空のエピソードは初稿完了できないべき"""
        # Arrange
        episode = Episode(
            id="episode001",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テストエピソード"),
            content="",
            status=EpisodeStatus.IN_PROGRESS,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="内容が空のため初稿完了できません"):
            episode.complete_draft()

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-EPISODE_SHOULD_CALCU")
    def test_episode_should_calculate_completion_rate_correctly(self) -> None:
        """エピソードは完成度を正確に計算すべき"""
        # Arrange
        plot_info = {"word_count_target": 1000}
        episode = Episode(
            id="episode001",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テストエピソード"),
            content="これは500文字のテスト内容です。" * 20,  # 約500文字
            word_count=WordCount(500),
            plot_info=plot_info,
        )

        # Act
        completion_rate = episode.get_completion_rate()

        # Assert
        assert completion_rate == 50.0  # 500/1000 * 100

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-EPISODE_CAN_PUBLISH_")
    def test_episode_can_publish_when_meets_requirements(self) -> None:
        """要件を満たすエピソードは公開可能と判定されるべき"""
        # Arrange
        episode = Episode(
            id="episode001",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テストエピソード"),
            content="これは十分な長さのテスト内容です。" * 100,  # 十分な文字数
            status=EpisodeStatus.REVISED,
            word_count=WordCount(2500),
        )

        # Act & Assert
        assert episode.can_publish() is True

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-EPISODE_CANNOT_PUBLI")
    def test_episode_cannot_publish_when_insufficient_content(self) -> None:
        """内容が不十分なエピソードは公開不可と判定されるべき"""
        # Arrange
        episode = Episode(
            id="episode001",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テストエピソード"),
            content="短い内容",
            status=EpisodeStatus.REVISED,
            word_count=WordCount(10),
        )

        # Act & Assert
        assert episode.can_publish() is False


class TestCreateEpisodeUseCase:
    """エピソード作成ユースケースのテスト(DDDアプローチ)"""

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-SHOULD_CREATE_EPISOD")
    def test_should_create_episode_from_valid_plot_info(self) -> None:
        """有効なプロット情報からエピソードを作成すべき"""
        # Arrange
        mock_episode_repo = Mock()
        mock_writing_record_repo = Mock()

        # 重複チェックでNoneを返す(重複なし)
        mock_episode_repo.find_by_number.return_value = None

        # 保存したエピソードを返す
        created_episode = Episode(
            id="episode001",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テストタイトル"),
        )

        mock_episode_repo.save.return_value = created_episode
        mock_episode_repo.update_plot_status.return_value = True

        use_case = CreateEpisodeFromPlotUseCase(
            mock_episode_repo,
            mock_writing_record_repo,
        )

        command = CreateEpisodeCommand(
            project_id="test_project",
            plot_info={
                "episode_number": "001",
                "title": "第1話 テストタイトル",
                "summary": "テストサマリー",
                "word_count_target": 3000,
            },
        )

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.success is True
        assert result.episode is not None
        assert result.episode.episode_number.value == 1
        mock_episode_repo.save.assert_called_once()
        mock_episode_repo.update_plot_status.assert_called_once_with(
            "test_project",
            "001",
            "執筆中",
        )

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-SHOULD_REJECT_DUPLIC")
    def test_should_reject_duplicate_episode_number(self) -> None:
        """重複する話数のエピソード作成を拒否すべき"""
        # Arrange
        mock_episode_repo = Mock()
        mock_writing_record_repo = Mock()

        # 既存エピソードが存在
        existing_episode = Episode(
            id="existing",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("既存エピソード"),
        )

        mock_episode_repo.find_by_number.return_value = existing_episode

        use_case = CreateEpisodeFromPlotUseCase(
            mock_episode_repo,
            mock_writing_record_repo,
        )

        command = CreateEpisodeCommand(
            project_id="test_project",
            plot_info={
                "episode_number": "001",
                "title": "第1話 重複タイトル",
            },
        )

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.success is False
        assert "既に存在します" in result.error_message
        mock_episode_repo.save.assert_not_called()

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-SHOULD_VALIDATE_REQU")
    def test_should_validate_required_fields(self) -> None:
        """必須フィールドの検証を行うべき"""
        # Arrange
        mock_episode_repo = Mock()
        mock_writing_record_repo = Mock()

        use_case = CreateEpisodeFromPlotUseCase(
            mock_episode_repo,
            mock_writing_record_repo,
        )

        command = CreateEpisodeCommand(
            project_id="test_project",
            plot_info={
                # episode_number が不足
                "title": "第1話 テストタイトル",
            },
        )

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.success is False
        assert "必須フィールド" in result.error_message
        mock_episode_repo.save.assert_not_called()


class TestTrackProgressUseCase:
    """進捗追跡ユースケースのテスト(DDDアプローチ)"""

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-SHOULD_CALCULATE_PRO")
    def test_should_calculate_project_progress_correctly(self) -> None:
        """プロジェクト進捗を正確に計算すべき"""
        # Arrange
        mock_episode_repo = Mock()
        mock_session_repo = Mock()

        episodes = [
            Episode(
                id="episode001",
                episode_number=EpisodeNumber(1),
                title=EpisodeTitle("完了エピソード"),
                status=EpisodeStatus.REVISED,
                word_count=WordCount(3000),
            ),
            Episode(
                id="episode002",
                episode_number=EpisodeNumber(2),
                title=EpisodeTitle("進行中エピソード"),
                status=EpisodeStatus.IN_PROGRESS,
                word_count=WordCount(1500),
            ),
            Episode(
                id="episode003",
                episode_number=EpisodeNumber(3),
                title=EpisodeTitle("未執筆エピソード"),
                status=EpisodeStatus.UNWRITTEN,
                word_count=WordCount(0),
            ),
        ]

        mock_episode_repo.find_all_by_project.return_value = episodes

        use_case = TrackWritingProgressUseCase(
            mock_episode_repo,
            mock_session_repo,
        )

        query = ProgressQuery(project_id="test_project")

        # Act
        progress = use_case.execute(query)

        # Assert
        assert progress.total_episodes == 3
        assert progress.completed_episodes == 1  # REVISEDのみ
        assert progress.in_progress_episodes == 1
        assert abs(progress.completion_rate - 33.33) < 0.1  # 1/3 * 100 (浮動小数点誤差考慮)
        assert progress.total_words == 4500  # 3000 + 1500 + 0
        assert progress.next_episode_to_write == 3  # 未執筆エピソード

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-SHOULD_IDENTIFY_NEXT")
    def test_should_identify_next_episode_to_write(self) -> None:
        """次に執筆すべきエピソードを特定すべき"""
        # Arrange
        mock_episode_repo = Mock()
        mock_session_repo = Mock()

        episodes = [
            Episode(
                id="episode001",
                episode_number=EpisodeNumber(1),
                status=EpisodeStatus.PUBLISHED,
            ),
            Episode(
                id="episode003",
                episode_number=EpisodeNumber(3),
                status=EpisodeStatus.UNWRITTEN,
            ),
            Episode(
                id="episode002",
                episode_number=EpisodeNumber(2),
                status=EpisodeStatus.UNWRITTEN,
            ),
        ]

        mock_episode_repo.find_all_by_project.return_value = episodes

        use_case = TrackWritingProgressUseCase(
            mock_episode_repo,
            mock_session_repo,
        )

        query = ProgressQuery(project_id="test_project")

        # Act
        progress = use_case.execute(query)

        # Assert
        assert progress.next_episode_to_write == 2  # 最も早い未執筆話数


class TestFileEpisodeRepository:
    """ファイルベースエピソードリポジトリのテスト(DDDアプローチ)"""

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-SHOULD_SAVE_AND_RETR")
    def test_should_save_and_retrieve_episode(self) -> None:
        """エピソードを保存して取得できるべき"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            project_root = Path(temp_dir)
            repository = FileEpisodeRepository(project_root)

            episode = Episode(
                id="episode001",
                project_id="test_project",
                episode_number=EpisodeNumber(1),
                title=EpisodeTitle("テストタイトル"),
                content="これはテスト内容です。",
                status=EpisodeStatus.IN_PROGRESS,
            )

            # Act
            saved_episode = repository.save(episode)
            retrieved_episode = repository.find_by_number("test_project", EpisodeNumber(1))

            # Assert
            assert saved_episode.id == episode.id
            assert retrieved_episode is not None
            assert retrieved_episode.episode_number.value == 1
            assert retrieved_episode.title.value == "テストタイトル"

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-SHOULD_FIND_NEXT_UNW")
    def test_should_find_next_unwritten_episode_from_plot(self) -> None:
        """プロットから次の未執筆エピソードを見つけるべき"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            project_root = Path(temp_dir)
            repository = FileEpisodeRepository(project_root)

            # プロットファイル作成
            path_service = get_common_path_service()
            plot_dir = project_root / str(path_service.get_plots_dir()) / "章別プロット"
            plot_dir.mkdir(parents=True, exist_ok=True)

            plot_data = {
                "episodes": [
                    {"episode_number": "001", "title": "第1話 始まり", "status": "未執筆"},
                    {"episode_number": "002", "title": "第2話 展開", "status": "未執筆"},
                ],
            }

            plot_file = plot_dir / "chapter01.yaml"
            with Path(plot_file).open("w", encoding="utf-8") as f:
                yaml.dump(plot_data, f, allow_unicode=True)

            # Act
            next_episode = repository.find_next_unwritten("test_project")

            # Assert
            assert next_episode is not None
            assert next_episode.episode_number.value == 1
            assert next_episode.status == EpisodeStatus.UNWRITTEN


class TestIntegrationDDDWritingWorkflow:
    """DDD統合執筆ワークフローのテスト"""

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-COMPLETE_EPISODE_CRE")
    def test_complete_episode_creation_workflow_with_ddd(self) -> None:
        """DDD構造での完全エピソード作成ワークフロー"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            project_root = Path(temp_dir)

            # プロット設定
            self._setup_plot_data(project_root)

            # DDDコンポーネント初期化
            episode_repo = FileEpisodeRepository(project_root)
            writing_record_repo = Mock()  # 簡略化

            use_case = CreateEpisodeFromPlotUseCase(
                episode_repo,
                writing_record_repo,
            )

            command = CreateEpisodeCommand(
                project_id="test_project",
                plot_info={
                    "episode_number": "001",
                    "title": "第1話 冒険の始まり",
                    "summary": "主人公が旅立つ決意を固める",
                    "word_count_target": 3000,
                },
            )

            # Act
            result = use_case.execute(command)

            # Assert
            assert result.success is True
            assert result.episode is not None
            assert result.episode.episode_number.value == 1
            assert "冒険の始まり" in result.episode.title.value

            # ファイルが作成されているか確認
            path_service = get_common_path_service()
            manuscript_file = project_root / str(path_service.get_manuscript_dir()) / "第001話_冒険の始まり.md"
            assert manuscript_file.exists()

            # 取得テスト
            retrieved = episode_repo.find_by_number("test_project", EpisodeNumber(1))
            assert retrieved is not None
            assert retrieved.episode_number.value == 1

    def _setup_plot_data(self, project_root: Path) -> None:
        """テスト用プロットデータ設定"""
        path_service = get_common_path_service()
        plot_dir = project_root / str(path_service.get_plots_dir()) / "章別プロット"
        plot_dir.mkdir(parents=True)

        plot_data = {
            "chapter_info": {
                "chapter_number": 1,
                "chapter_title": "ch01 序章",
            },
            "episodes": [
                {
                    "episode_number": "001",
                    "title": "第1話 冒険の始まり",
                    "summary": "主人公が旅立つ決意を固める",
                    "word_count_target": 3000,
                    "status": "未執筆",
                },
            ],
        }

        with Path(plot_dir / "chapter01.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(plot_data, f, allow_unicode=True)


# DDD原則遵守確認テスト
class TestDDDComplianceChecks:
    """DDD原則遵守の確認テスト"""

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-DOMAIN_ENTITIES_SHOU")
    def test_domain_entities_should_contain_business_logic(self) -> None:
        """ドメインエンティティにビジネスロジックが含まれるべき"""
        # ビジネスルールのテスト
        episode = Episode(
            id="episode001",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テスト"),
            word_count=WordCount(1500),  # 2000文字未満
            status=EpisodeStatus.REVISED,
        )

        # ビジネスルール:2000文字未満は公開不可
        assert episode.can_publish() is False

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-REPOSITORIES_SHOULD_")
    def test_repositories_should_return_domain_objects(self) -> None:
        """リポジトリはドメインオブジェクトを返すべき"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = FileEpisodeRepository(Path(temp_dir))

            # リポジトリが返すオブジェクトの型確認
            result = repository.find_next_unwritten("test_project")

            # Noneまたは正しいドメインエンティティ
            assert result is None or isinstance(result, Episode)

    @pytest.mark.spec("SPEC-DDD_WRITING_SYSTEM-USE_CASES_SHOULD_ORC")
    def test_use_cases_should_orchestrate_domain_logic(self) -> None:
        """ユースケースはドメインロジックを調整すべき"""
        # モックリポジトリ
        mock_repo = Mock()
        mock_writing_repo = Mock()

        use_case = CreateEpisodeFromPlotUseCase(mock_repo, mock_writing_repo)

        # ユースケースが適切にリポジトリを使用することを確認
        command = CreateEpisodeCommand(
            project_id="test",
            plot_info={"episode_number": "001", "title": "Test"},
        )

        mock_repo.find_by_number.return_value = None
        mock_repo.save.return_value = Episode(
            id="test",
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("Test"),
        )

        mock_repo.update_plot_status.return_value = True

        use_case.execute(command)

        # リポジトリメソッドが適切に呼ばれたか確認
        mock_repo.find_by_number.assert_called()
        mock_repo.save.assert_called()
        mock_repo.update_plot_status.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
