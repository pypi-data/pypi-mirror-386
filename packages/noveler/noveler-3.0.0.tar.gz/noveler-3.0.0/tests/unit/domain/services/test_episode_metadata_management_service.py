"""
SPEC-EPISODE-004: エピソードメタデータ管理システムのテスト

エピソードメタデータの統合管理、検索・フィルタリング、統計・分析機能のテスト。
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from noveler.domain.repositories.episode_metadata_repository import EpisodeMetadataRepository
from noveler.domain.services.episode_metadata_management_service import EpisodeMetadataManagementService
from noveler.domain.services.metadata_value_objects import (
    BasicMetadata,
    EpisodeMetadata,
    MetadataSearchCriteria,
    MetadataStatistics,
    QualityMetadata,
    TechnicalMetadata,
    WritingMetadata,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.quality_score import QualityScore
from noveler.domain.value_objects.word_count import WordCount


@pytest.mark.spec("SPEC-EPISODE-004")
class TestEpisodeMetadataManagementService:
    """エピソードメタデータ管理サービスのテスト"""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """モックリポジトリ"""
        return Mock()

    @pytest.fixture
    def service(self, mock_repository: Mock) -> EpisodeMetadataManagementService:
        """テスト対象サービス"""
        return EpisodeMetadataManagementService(mock_repository)

    @pytest.fixture
    def sample_metadata(self) -> EpisodeMetadata:
        """サンプルメタデータ"""
        return EpisodeMetadata(
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テストエピソード"),
            basic_info=BasicMetadata(
                author="test_author", genre="fantasy", tags=["冒険", "魔法"], description="テスト用エピソード"
            ),
            writing_info=WritingMetadata(
                word_count=WordCount(1500), writing_duration=timedelta(hours=2), status="draft", completion_rate=0.8
            ),
            quality_info=QualityMetadata(
                overall_score=QualityScore(85),
                category_scores={"structure": QualityScore(80), "style": QualityScore(90)},
                last_check_date=datetime.now(timezone.utc),
                improvement_suggestions=["より具体的な描写を追加"],
            ),
            technical_info=TechnicalMetadata(
                file_path="/path/to/episode001.md",
                file_hash="abc123def456",
                version="1.0.0",
                backup_paths=["/backup/episode001_v1.md"],
            ),
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
            updated_at=datetime.now(timezone.utc),
        )

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-CREATE_METADATA_SUCC")
    def test_create_metadata_success(self, service: EpisodeMetadataManagementService, mock_repository: Mock) -> None:
        """メタデータ作成成功テスト"""
        # Given
        episode_number = EpisodeNumber(1)
        title = EpisodeTitle("新しいエピソード")
        mock_repository.exists.return_value = False  # 存在しない設定

        # When
        result = service.create_metadata(episode_number, title)

        # Then
        assert result.episode_number == episode_number
        assert result.title == title
        assert result.basic_info.author == "default_author"
        assert result.basic_info.genre == "fantasy"
        mock_repository.save.assert_called_once()

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-UPDATE_METADATA_SUCC")
    def test_update_metadata_success(
        self, service: EpisodeMetadataManagementService, sample_metadata: EpisodeMetadata, mock_repository: Mock
    ) -> None:
        """メタデータ更新成功テスト"""
        # Given
        mock_repository.find_by_episode_number.return_value = sample_metadata
        updated_title = EpisodeTitle("更新されたタイトル")

        # When
        result = service.update_metadata(sample_metadata.episode_number, title=updated_title)

        # Then
        assert result.title == updated_title
        assert result.episode_number == sample_metadata.episode_number
        mock_repository.save.assert_called_once()

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-MERGE_METADATA_FROM_")
    def test_merge_metadata_from_multiple_sources(
        self, service: EpisodeMetadataManagementService, mock_repository: Mock, sample_metadata: EpisodeMetadata
    ) -> None:
        """複数ソースからのメタデータ統合テスト"""
        # Given
        episode_number = EpisodeNumber(1)
        mock_repository.find_by_episode_number.return_value = sample_metadata

        # When
        result = service.merge_metadata(episode_number, ["source1", "source2"])

        # Then
        assert result == sample_metadata  # 現在の実装では既存データを返す

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-VALIDATE_CONSISTENCY")
    def test_validate_consistency_success(
        self, service: EpisodeMetadataManagementService, sample_metadata: EpisodeMetadata
    ) -> None:
        """整合性検証成功テスト"""
        # When
        result = service.validate_consistency(sample_metadata)

        # Then
        assert "is_consistent" in result
        assert "issues" in result
        assert "severity" in result
        assert isinstance(result["is_consistent"], bool)

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-SEARCH_METADATA_BY_C")
    def test_search_metadata_by_criteria(
        self, service: EpisodeMetadataManagementService, mock_repository: Mock, sample_metadata: EpisodeMetadata
    ) -> None:
        """検索条件によるメタデータ検索テスト"""
        # Given
        criteria = MetadataSearchCriteria(
            date_range=(datetime.now(timezone.utc) - timedelta(days=7), datetime.now(timezone.utc)),
            quality_score_range=(70.0, 100.0),
            status_filter=["draft", "completed"],
        )

        mock_repository.search_by_criteria.return_value = [sample_metadata]

        # When
        results = service.search_by_criteria(criteria)

        # Then
        assert len(results) == 1
        assert results[0] == sample_metadata
        mock_repository.search_by_criteria.assert_called_once_with(criteria)

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-GET_STATISTICS")
    def test_get_statistics(self, service: EpisodeMetadataManagementService, mock_repository: Mock) -> None:
        """統計情報取得テスト"""
        # Given
        period = timedelta(days=30)
        mock_stats = MetadataStatistics(
            total_episodes=5,
            average_quality_score=85.0,
            average_completion_rate=0.8,
            average_word_count=1500.0,
            total_writing_time=timedelta(hours=10),
        )

        mock_repository.get_statistics.return_value = mock_stats

        # When
        stats = service.get_statistics(period)

        # Then
        assert stats == mock_stats
        mock_repository.get_statistics.assert_called_once_with(period)

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-INVALID_EPISODE_NUMB")
    def test_invalid_episode_number_raises_error(
        self, service: EpisodeMetadataManagementService, mock_repository: Mock
    ) -> None:
        """無効なエピソード番号でエラーが発生することを確認"""
        # Given - EpisodeNumberの値オブジェクト自体で検証済みのため、
        # ここではリポジトリでの既存チェックをテスト
        episode_number = EpisodeNumber(1)
        title = EpisodeTitle("テストタイトル")
        mock_repository.exists.return_value = True  # 既に存在

        # When/Then
        with pytest.raises(ValueError, match="既に存在します"):
            service.create_metadata(episode_number, title)

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-METADATA_NOT_FOUND_R")
    def test_metadata_not_found_returns_none(
        self, service: EpisodeMetadataManagementService, mock_repository: Mock
    ) -> None:
        """存在しないメタデータの検索でNoneが返されることを確認"""
        # Given
        mock_repository.find_by_episode_number.return_value = None
        episode_number = EpisodeNumber(999)

        # When
        result = service.get_metadata(episode_number)

        # Then
        assert result is None
        mock_repository.find_by_episode_number.assert_called_once_with(episode_number)


@pytest.mark.spec("SPEC-EPISODE-004")
class TestEpisodeMetadataValueObjects:
    """エピソードメタデータ値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-EPISODE_METADATA_IMM")
    def test_episode_metadata_immutability(self) -> None:
        """EpisodeMetadataの不変性テスト"""
        # Given
        # from datetime import timedelta  # Moved to top-level

        # メタデータ型はトップレベルでインポート済み
        # BasicMetadata, EpisodeMetadata, QualityMetadata, TechnicalMetadata, WritingMetadata
        # from noveler.domain.value_objects.quality_score import QualityScore  # Moved to top-level
        # from noveler.domain.value_objects.word_count import WordCount  # Moved to top-level

        metadata = EpisodeMetadata(
            episode_number=EpisodeNumber(1),
            title=EpisodeTitle("テスト"),
            basic_info=BasicMetadata("author", "genre", [], "desc"),
            writing_info=WritingMetadata(WordCount(100), timedelta(hours=1), "draft", 0.5),
            quality_info=QualityMetadata(QualityScore(85), {}, datetime.now(timezone.utc), []),
            technical_info=TechnicalMetadata("path", "hash", "1.0", []),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # When/Then - 不変オブジェクトなので属性変更は不可
        with pytest.raises(AttributeError, match=".*"):
            metadata.title = EpisodeTitle("変更後")

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-BASIC_METADATA_VALID")
    def test_basic_metadata_validation(self) -> None:
        """BasicMetadataのバリデーションテスト"""
        # from noveler.domain.services.metadata_value_objects import BasicMetadata  # Moved to top-level

        # When/Then - 無効なデータでエラーが発生することを期待
        with pytest.raises(ValueError, match="著者名は必須です"):
            BasicMetadata(
                author="",  # 空文字は無効
                genre="fantasy",
                tags=[],
                description="",
            )

        with pytest.raises(ValueError, match="ジャンルは必須です"):
            BasicMetadata(
                author="author",
                genre="",  # 空文字は無効
                tags=[],
                description="",
            )

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-METADATA_SEARCH_CRIT")
    def test_metadata_search_criteria_validation(self) -> None:
        """MetadataSearchCriteriaのバリデーションテスト"""
        # from noveler.domain.services.metadata_value_objects import MetadataSearchCriteria  # Moved to top-level

        # When/Then - 無効な日付範囲でエラーが発生することを期待
        with pytest.raises(ValueError, match="開始日は終了日より前である必要があります"):
            MetadataSearchCriteria(
                date_range=(
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc) - timedelta(days=1),
                )  # 終了日が開始日より前
            )

        with pytest.raises(ValueError, match="最小スコアは最大スコアより小さい必要があります"):
            MetadataSearchCriteria(
                quality_score_range=(100.0, 0.0)  # 最大値が最小値より小さい
            )


@pytest.mark.spec("SPEC-EPISODE-004")
class TestEpisodeMetadataRepository:
    """エピソードメタデータリポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-EPISODE_METADATA_MANAGEMENT_SERVICE-REPOSITORY_INTERFACE")
    def test_repository_interface_definition(self) -> None:
        """リポジトリインターフェースの定義テスト"""
        # from noveler.domain.repositories.episode_metadata_repository import EpisodeMetadataRepository  # Moved to top-level

        # When/Then - インターフェースが正しく定義されていることを確認
        # ABCクラスは直接インスタンス化できないが、メソッドの存在は確認可能
        assert hasattr(EpisodeMetadataRepository, "find_by_episode_number")
        assert hasattr(EpisodeMetadataRepository, "search_by_criteria")
        assert hasattr(EpisodeMetadataRepository, "save")
        assert hasattr(EpisodeMetadataRepository, "get_statistics")

        # ABCクラスの直接インスタンス化はエラーになる
        with pytest.raises(TypeError, match=".*"):
            EpisodeMetadataRepository()
