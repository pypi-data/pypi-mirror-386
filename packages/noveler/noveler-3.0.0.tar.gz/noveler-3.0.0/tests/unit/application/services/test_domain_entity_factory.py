#!/usr/bin/env python3
"""ドメインエンティティファクトリーサービスのテスト

DomainEntityFactoryの動作を検証するユニットテスト
DDD準拠・包括的テストカバレッジ対応版
"""

from unittest.mock import Mock

import pytest
from pytest import mark

from noveler.application.services.domain_entity_factory import DomainEntityFactoryService as DomainEntityFactory


class TestDomainEntityFactory:
    """DomainEntityFactory テストクラス"""

    @pytest.fixture
    def mock_logger(self):
        """ロガーのモック"""
        return Mock()

    @pytest.fixture
    def factory(self, mock_logger):
        """DomainEntityFactory インスタンス"""
        return DomainEntityFactory(logger_service=mock_logger)

    @mark.spec("SPEC-DEF-001")
    def test_initialization(self, factory, mock_logger):
        """初期化テスト"""
        # Assert
        assert factory.logger_service is mock_logger

    @mark.spec("SPEC-DEF-002")
    def test_create_episode_publisher(self, factory):
        """エピソードパブリッシャー作成テスト"""
        # Arrange
        episode_id = "episode_001"

        # Act
        publisher = factory.create_episode_publisher(episode_id)

        # Assert
        assert publisher is not None
        assert publisher.episode_id == episode_id

    @mark.spec("SPEC-DEF-003")
    def test_create_episode_quality(self, factory):
        """エピソード品質作成テスト"""
        # Arrange
        episode_id = "episode_001"

        # Act
        quality = factory.create_episode_quality(episode_id)

        # Assert
        assert quality is not None
        assert quality.episode_id == episode_id

    @mark.spec("SPEC-DEF-004")
    def test_create_episode_metadata(self, factory):
        """エピソードメタデータ作成テスト"""
        # Arrange
        episode_id = "episode_001"

        # Act
        metadata = factory.create_episode_metadata(episode_id)

        # Assert
        assert metadata is not None
        assert metadata.episode_id == episode_id

    @mark.spec("SPEC-DEF-005")
    def test_create_episode(self, factory):
        """エピソード作成テスト"""
        # Arrange
        number = 1
        title = "第1話 始まりの物語"
        target_words = 3000

        # Act
        episode = factory.create_episode(number, title, target_words)

        # Assert
        assert episode is not None
        assert episode.number.value == number
        assert episode.title.value == title
        assert episode.target_words.value == target_words

    @mark.spec("SPEC-DEF-006")
    def test_create_episode_with_default_target_words(self, factory):
        """エピソード作成テスト（デフォルト文字数）"""
        # Arrange
        number = 2
        title = "第2話 展開"

        # Act
        episode = factory.create_episode(number, title)

        # Assert
        assert episode is not None
        assert episode.number.value == number
        assert episode.title.value == title
        assert episode.target_words.value == 3000  # デフォルト値

    @mark.spec("SPEC-DEF-007")
    def test_initialization_with_null_logger(self):
        """Nullロガーでの初期化テスト"""
        # Act
        factory = DomainEntityFactory()

        # Assert
        assert factory.logger_service is not None
        # NullLoggerServiceが設定されていることを確認
        assert hasattr(factory.logger_service, "info")
        assert hasattr(factory.logger_service, "error")
