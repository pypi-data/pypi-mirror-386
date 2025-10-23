#!/usr/bin/env python3
"""YamlEpisodeRepositoryのユニットテスト

仕様書に基づくテスト実装
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from noveler.domain.entities.episode import Episode, EpisodeStatus
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.quality_score import QualityScore
from noveler.domain.value_objects.word_count import WordCount
from noveler.infrastructure.repositories.yaml_episode_repository import YamlEpisodeRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestYamlEpisodeRepository:
    """YamlEpisodeRepositoryのテストクラス"""

    def setup_method(self) -> None:
        """テストメソッドごとの初期設定"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

        # パスサービスを作成
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service
        self.path_service = create_path_service(self.project_root)

        # リポジトリインスタンス作成（新しいコンストラクタシグネチャ対応）
        self.repository = YamlEpisodeRepository(self.project_root, self.path_service)

    def teardown_method(self) -> None:
        """テストメソッドごとの後処理"""
        self.temp_dir.cleanup()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_ensure_directories_creates_required_folders(self) -> None:
        """必要なディレクトリが作成されることを確認"""
        # Assert: ディレクトリが作成されている（テスト用のpath_serviceを使用）
        assert self.path_service.get_manuscript_dir().exists()
        assert self.path_service.get_management_dir().exists()

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_save_new_episode(self) -> None:
        """新規エピソードの保存テスト"""
        # Given: 新しいエピソード
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("始まりの朝"),
            content="これは第1話の内容です。",
            target_words=WordCount(3000),
        )

        # When: エピソードを保存
        self.repository.save(episode, "test-project")

        # Then: 原稿ファイルが作成される
        manuscript_path = self.path_service.get_manuscript_dir() / "第001話_始まりの朝.md"
        assert manuscript_path.exists()
        assert manuscript_path.read_text(encoding="utf-8") == "これは第1話の内容です。"

        # Then: 話数管理YAMLが作成される
        management_path = self.path_service.get_management_dir() / "話数管理.yaml"
        assert management_path.exists()

        # Then: YAMLの内容を確認
        with Path(management_path).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert len(data["episodes"]) == 1
        episode_data = data["episodes"][0]
        assert episode_data["number"] == 1
        assert episode_data["title"] == "始まりの朝"
        assert episode_data["status"] == "DRAFT"
        assert episode_data["word_count"] == 12  # "これは第1話の内容です。" の文字数
        assert episode_data["target_words"] == 3000
        assert episode_data["version"] == 1

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_save_existing_episode_update(self) -> None:
        """既存エピソードの更新テスト"""
        # Given: 既存のエピソードを保存
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("始まりの朝"),
            content="初版の内容",
            target_words=WordCount(3000),
        )

        self.repository.save(episode, "test-project")

        # When: 同じ番号のエピソードを更新
        episode.update_content("更新された内容")
        episode.version = 2
        self.repository.save(episode, "test-project")

        # Then: 原稿ファイルが更新される
        manuscript_path = self.path_service.get_manuscript_dir() / "第001話_始まりの朝.md"
        assert manuscript_path.read_text(encoding="utf-8") == "更新された内容"

        # Then: 話数管理YAMLが更新される
        management_path = self.path_service.get_management_dir() / "話数管理.yaml"
        with Path(management_path).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert len(data["episodes"]) == 1  # 重複なし
        assert data["episodes"][0]["version"] == 2
        assert data["episodes"][0]["word_count"] == 7

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_find_by_number_existing(self) -> None:
        """存在するエピソードの番号検索テスト"""
        # Given: エピソードを保存
        original_episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("始まりの朝"),
            content="これは第1話の内容です。",
            target_words=WordCount(3000),
        )

        original_episode.complete()  # ステータスをCOMPLETEDに
        original_episode.set_quality_score(QualityScore(85))
        self.repository.save(original_episode, "test-project")

        # When: 番号で検索
        found_episode = self.repository.find_by_number("test-project", EpisodeNumber(1))

        # Then: エピソードが見つかる
        assert found_episode is not None
        assert found_episode.number.value == 1
        assert found_episode.title.value == "始まりの朝"
        assert found_episode.content == "これは第1話の内容です。"
        assert found_episode.status == EpisodeStatus.COMPLETED
        assert found_episode.quality_score.value == 85

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_find_by_number_not_existing(self) -> None:
        """存在しないエピソードの番号検索テスト"""
        # When: 存在しない番号で検索
        found_episode = self.repository.find_by_number("test-project", EpisodeNumber(999))

        # Then: Noneが返される
        assert found_episode is None

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_find_all_episodes(self) -> None:
        """全エピソード取得テスト"""
        # Given: 複数のエピソードを保存
        episodes = [
            Episode(
                number=EpisodeNumber(1), title=EpisodeTitle("第1話"), content="内容1", target_words=WordCount(3000)
            ),
            Episode(
                number=EpisodeNumber(2), title=EpisodeTitle("第2話"), content="内容2", target_words=WordCount(3000)
            ),
            Episode(
                number=EpisodeNumber(3), title=EpisodeTitle("第3話"), content="内容3", target_words=WordCount(3000)
            ),
        ]

        for episode in episodes:
            self.repository.save(episode, "test-project")

        # When: 全エピソードを取得
        all_episodes = self.repository.find_all("test-project")

        # Then: 3つのエピソードが取得される
        assert len(all_episodes) == 3
        assert all_episodes[0].number.value == 1
        assert all_episodes[1].number.value == 2
        assert all_episodes[2].number.value == 3

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_exists_check(self) -> None:
        """エピソード存在確認テスト"""
        # Given: エピソードを保存
        episode = Episode(
            number=EpisodeNumber(1), title=EpisodeTitle("テスト"), content="内容", target_words=WordCount(3000)
        )

        self.repository.save(episode, "test-project")

        # When/Then: 存在確認
        assert self.repository.exists("test-project", EpisodeNumber(1)) is True
        assert self.repository.exists("test-project", EpisodeNumber(2)) is False

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_delete_episode(self) -> None:
        """エピソード削除テスト"""
        # Given: エピソードを保存
        episode = Episode(
            number=EpisodeNumber(1),
            title=EpisodeTitle("削除テスト"),
            content="削除される内容",
            target_words=WordCount(3000),
        )

        self.repository.save(episode, "test-project")

        # 存在確認
        assert self.repository.exists("test-project", EpisodeNumber(1)) is True
        manuscript_path = self.path_service.get_manuscript_dir() / "第001話_削除テスト.md"
        assert manuscript_path.exists()

        # When: エピソードを削除
        self.repository.delete_by_number("test-project", EpisodeNumber(1))

        # Then: エピソードが削除される
        assert self.repository.exists("test-project", EpisodeNumber(1)) is False
        assert not manuscript_path.exists()

        # Then: 話数管理からも削除される
        management_path = self.path_service.get_management_dir() / "話数管理.yaml"
        with Path(management_path).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert len(data["episodes"]) == 0

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_get_next_episode_number(self) -> None:
        """次のエピソード番号取得テスト"""
        # Case 1: エピソードがない場合
        next_number = self.repository.get_next_episode_number("test-project")
        assert next_number == 1

        # Case 2: エピソードがある場合
        for i in [1, 3, 5]:  # 飛び番号で保存
            episode = Episode(
                number=EpisodeNumber(i),
                title=EpisodeTitle(f"第{i}話"),
                content=f"内容{i}",
                target_words=WordCount(3000),
            )

            self.repository.save(episode, "test-project")

        next_number = self.repository.get_next_episode_number("test-project")
        assert next_number == 6  # 最大値5の次

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_to_dict_conversion(self) -> None:
        """エピソードから辞書への変換テスト"""
        # Given: 完全なエピソード
        episode = Episode(
            number=EpisodeNumber(1), title=EpisodeTitle("テスト"), content="内容", target_words=WordCount(3000)
        )

        episode.status = EpisodeStatus.COMPLETED
        episode.quality_score = QualityScore(85)
        episode.version = 3
        episode.created_at = datetime(2025, 7, 21, 10, 0, 0, tzinfo=timezone.utc)
        episode.completed_at = datetime(2025, 7, 21, 15, 30, 0, tzinfo=timezone.utc)

        # When: 辞書に変換
        result = self.repository._episode_to_dict(episode)

        # Then: 正しく変換される
        assert result["number"] == 1
        assert result["title"] == "テスト"
        assert result["status"] == "COMPLETED"
        assert result["word_count"] == 2
        assert result["target_words"] == 3000
        assert result["version"] == 3
        assert result["quality_score"] == 85
        assert result["created_at"] == "2025-07-21T10:00:00"
        assert result["completed_at"] == "2025-07-21T15:30:00"
        assert "updated_at" in result

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_yaml_file_not_exists_handling(self) -> None:
        """話数管理YAMLが存在しない場合の処理"""
        # When: YAMLファイルが存在しない状態で読み込み
        data = self.repository._load_episode_management()

        # Then: 空のデータが返される
        assert data == {"episodes": []}

    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_multiple_episodes_sorting(self) -> None:
        """複数エピソードのソート確認"""
        # Given: 順不同でエピソードを保存
        for i in [3, 1, 2]:
            episode = Episode(
                number=EpisodeNumber(i),
                title=EpisodeTitle(f"第{i}話"),
                content=f"内容{i}",
                target_words=WordCount(3000),
            )

            self.repository.save(episode, "test-project")

        # When: 話数管理を読み込み
        data = self.repository._load_episode_management()

        # Then: 番号順にソートされている
        numbers = [ep["number"] for ep in data["episodes"]]
        assert numbers == [1, 2, 3]

    @pytest.mark.spec("SPEC-EPISODE-005")
    @patch("noveler.infrastructure.utils.yaml_utils.YAMLHandler")
    def test_yaml_formatter_fallback(self, mock_yaml_handler: object) -> None:
        """YAMLフォーマッターのフォールバック処理テスト"""
        # Given: YAMLHandlerがImportErrorを発生させる
        mock_yaml_handler.save_yaml.side_effect = ImportError()

        # Given: エピソード
        episode = Episode(
            number=EpisodeNumber(1), title=EpisodeTitle("テスト"), content="内容", target_words=WordCount(3000)
        )

        # When: 保存(エラーは発生しない)
        self.repository.save(episode, "test-project")

        # Then: ファイルは正常に保存される
        management_path = self.path_service.get_management_dir() / "話数管理.yaml"
        assert management_path.exists()
