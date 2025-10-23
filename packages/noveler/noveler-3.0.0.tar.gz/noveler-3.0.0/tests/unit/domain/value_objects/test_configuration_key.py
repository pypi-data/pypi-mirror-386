"""ConfigurationKey値オブジェクトのテスト"""

import pytest

from noveler.domain.value_objects.configuration_key import ConfigurationKey


pytestmark = pytest.mark.vo_smoke


@pytest.mark.spec("SPEC-API-001")
class TestConfigurationKey:
    """ConfigurationKey値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-API-001")
    def test_valid_key_creation(self) -> None:
        """有効なキーで作成できること"""
        # 単一キー
        key1 = ConfigurationKey("database")
        assert str(key1) == "database"

        # ドット区切りキー
        key2 = ConfigurationKey("database.host")
        assert str(key2) == "database.host"

        # 深い階層のキー
        key3 = ConfigurationKey("app.config.database.connection.timeout")
        assert str(key3) == "app.config.database.connection.timeout"

    @pytest.mark.spec("SPEC-API-001")
    def test_invalid_key_rejection(self) -> None:
        """無効なキーを拒否すること"""
        # 空文字列
        with pytest.raises(ValueError, match="Configuration key cannot be empty"):
            ConfigurationKey("")

        # None
        with pytest.raises(TypeError, match=".*"):
            ConfigurationKey(None)

        # 空白のみ
        with pytest.raises(ValueError, match="Configuration key cannot be empty"):
            ConfigurationKey("   ")

        # 先頭/末尾のドット
        with pytest.raises(ValueError, match="Configuration key cannot start or end with a dot"):
            ConfigurationKey(".database")

        with pytest.raises(ValueError, match="Configuration key cannot start or end with a dot"):
            ConfigurationKey("database.")

        # 連続したドット
        with pytest.raises(ValueError, match="Configuration key cannot contain consecutive dots"):
            ConfigurationKey("database..host")

    @pytest.mark.spec("SPEC-API-001")
    def test_path_segments_conversion(self) -> None:
        """パスセグメントへの変換が正しく行われること"""
        # 単一セグメント
        key1 = ConfigurationKey("database")
        assert key1.as_path_segments() == ["database"]

        # 複数セグメント
        key2 = ConfigurationKey("database.host.port")
        assert key2.as_path_segments() == ["database", "host", "port"]

        # 深い階層
        key3 = ConfigurationKey("app.config.database.connection.timeout")
        assert key3.as_path_segments() == ["app", "config", "database", "connection", "timeout"]

    @pytest.mark.spec("SPEC-API-001")
    def test_equality(self) -> None:
        """等価性の判定が正しく行われること"""
        key1 = ConfigurationKey("database.host")
        key2 = ConfigurationKey("database.host")
        key3 = ConfigurationKey("database.port")

        assert key1 == key2
        assert key1 != key3
        assert key1 != "database.host"  # 文字列との比較

    @pytest.mark.spec("SPEC-API-001")
    def test_hash(self) -> None:
        """ハッシュ値が正しく生成されること"""
        key1 = ConfigurationKey("database.host")
        key2 = ConfigurationKey("database.host")
        key3 = ConfigurationKey("database.port")

        # 同じキーは同じハッシュ値
        assert hash(key1) == hash(key2)
        # 異なるキーは異なるハッシュ値(高確率で)
        assert hash(key1) != hash(key3)

        # 辞書のキーとして使用可能
        config_dict = {key1: "localhost"}
        assert config_dict[key2] == "localhost"

    @pytest.mark.spec("SPEC-API-001")
    def test_immutability(self) -> None:
        """値オブジェクトが不変であること"""
        key = ConfigurationKey("database.host")

        # 属性の変更を試みる
        with pytest.raises(AttributeError, match=".*"):
            key.key = "new.key"

        # 元の値が変わっていないことを確認
        assert str(key) == "database.host"
