"""ConfigurationServiceドメインサービスのテスト"""

from unittest.mock import Mock

import pytest

from noveler.domain.services.configuration_service import ConfigurationService
from noveler.domain.value_objects.configuration_key import ConfigurationKey
from noveler.domain.value_objects.file_path import FilePath


@pytest.mark.spec("SPEC-API-001")
class TestConfigurationService:
    """ConfigurationServiceドメインサービスのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.mock_repository = Mock()
        self.service = ConfigurationService(self.mock_repository)

    @pytest.mark.spec("SPEC-API-001")
    def test_load_configuration_success(self) -> None:
        """設定ファイルの読み込みが成功すること"""
        # Arrange
        file_path = FilePath("config.yaml")
        expected_config = {"database": {"host": "localhost", "port": 5432}, "logging": {"level": "INFO"}}
        self.mock_repository.load.return_value = expected_config

        # Act
        result = self.service.load_configuration(file_path)

        # Assert
        assert result == expected_config
        self.mock_repository.load.assert_called_once_with(file_path)

    @pytest.mark.spec("SPEC-API-001")
    def test_load_configuration_file_not_found(self) -> None:
        """設定ファイルが見つからない場合の処理"""
        # Arrange
        file_path = FilePath("nonexistent.yaml")
        self.mock_repository.load.side_effect = FileNotFoundError("File not found")

        # Act & Assert
        with pytest.raises(FileNotFoundError, match=".*"):
            self.service.load_configuration(file_path)

    @pytest.mark.spec("SPEC-API-001")
    def test_get_value_existing_key(self) -> None:
        """存在するキーの値を取得できること"""
        # Arrange
        config = {"database": {"host": "localhost", "port": 5432}, "logging": {"level": "INFO"}}
        self.service._config = config

        # Act & Assert
        key1 = ConfigurationKey("database.host")
        assert self.service.get_value(key1) == "localhost"

        key2 = ConfigurationKey("database.port")
        assert self.service.get_value(key2) == 5432

        key3 = ConfigurationKey("logging.level")
        assert self.service.get_value(key3) == "INFO"

    @pytest.mark.spec("SPEC-API-001")
    def test_get_value_nonexistent_key_with_default(self) -> None:
        """存在しないキーのデフォルト値を取得できること"""
        # Arrange
        config = {"database": {"host": "localhost"}}
        self.service._config = config

        # Act
        key = ConfigurationKey("database.timeout")
        result = self.service.get_value(key, default=30)

        # Assert
        assert result == 30

    @pytest.mark.spec("SPEC-API-001")
    def test_get_value_nonexistent_key_no_default(self) -> None:
        """存在しないキーでデフォルト値がない場合にNoneを返すこと"""
        # Arrange
        config = {"database": {"host": "localhost"}}
        self.service._config = config

        # Act
        key = ConfigurationKey("nonexistent.key")
        result = self.service.get_value(key)

        # Assert
        assert result is None

    @pytest.mark.spec("SPEC-API-001")
    def test_get_value_nested_key(self) -> None:
        """深い階層のキーの値を取得できること"""
        # Arrange
        config = {"app": {"database": {"connection": {"timeout": 30, "pool_size": 10}}}}
        self.service._config = config

        # Act
        key = ConfigurationKey("app.database.connection.timeout")
        result = self.service.get_value(key)

        # Assert
        assert result == 30

    @pytest.mark.spec("SPEC-API-001")
    def test_validate_configuration_valid(self) -> None:
        """有効な設定の検証が成功すること"""
        # Arrange
        config = {"database": {"host": "localhost", "port": 5432}, "logging": {"level": "INFO"}}

        # Act
        result = self.service.validate_configuration(config)

        # Assert
        assert result is True

    @pytest.mark.spec("SPEC-API-001")
    def test_validate_configuration_empty(self) -> None:
        """空の設定の検証が失敗すること"""
        # Arrange
        config = {}

        # Act
        result = self.service.validate_configuration(config)

        # Assert
        assert result is False

    @pytest.mark.spec("SPEC-API-001")
    def test_validate_configuration_none(self) -> None:
        """None設定の検証が失敗すること"""
        # Arrange
        config = None

        # Act
        result = self.service.validate_configuration(config)

        # Assert
        assert result is False

    @pytest.mark.spec("SPEC-API-001")
    def test_set_value(self) -> None:
        """設定値を更新できること"""
        # Arrange
        config = {"database": {"host": "localhost"}}
        self.service._config = config

        # Act
        key = ConfigurationKey("database.port")
        self.service.set_value(key, 5432)

        # Assert
        assert self.service.get_value(key) == 5432

    @pytest.mark.spec("SPEC-API-001")
    def test_set_value_nested_creation(self) -> None:
        """存在しない階層に値を設定できること"""
        # Arrange
        config = {}
        self.service._config = config

        # Act
        key = ConfigurationKey("app.database.host")
        self.service.set_value(key, "localhost")

        # Assert
        assert self.service.get_value(key) == "localhost"
        assert config["app"]["database"]["host"] == "localhost"

    @pytest.mark.spec("SPEC-API-001")
    def test_has_key(self) -> None:
        """キーの存在確認ができること"""
        # Arrange
        config = {"database": {"host": "localhost"}, "logging": {"level": "INFO"}}
        self.service._config = config

        # Act & Assert
        assert self.service.has_key(ConfigurationKey("database.host")) is True
        assert self.service.has_key(ConfigurationKey("database.port")) is False
        assert self.service.has_key(ConfigurationKey("nonexistent")) is False
