"""Tests for Configuration Manager
設定マネージャーのテスト


仕様書: SPEC-INFRASTRUCTURE
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Add parent directory to path
# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()

from noveler.infrastructure.config.config_manager import (
    AppConfig,
    ConfigManager,
    create_production_config,
    create_test_config,
)


class TestAppConfig:
    """AppConfig データクラスのテスト"""

    def test_default_values(self) -> None:
        """デフォルト値のテスト"""
        config = AppConfig()

        assert config.mode == "production"
        assert config.test_mode is False
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.use_mock_services is False
        assert config.quality_threshold == 80
        assert config.auto_fix is False
        assert config.batch_size == 100
        assert config.timeout_seconds == 30

    def test_custom_values(self) -> None:
        """カスタム値のテスト"""
        config = AppConfig(
            mode="test",
            test_mode=True,
            debug=True,
            log_level="DEBUG",
            quality_threshold=70,
        )

        assert config.mode == "test"
        assert config.test_mode is True
        assert config.debug is True
        assert config.log_level == "DEBUG"
        assert config.quality_threshold == 70


class TestConfigManager:
    """ConfigManager クラスのテスト"""

    def test_config_manager_without_file(self) -> None:
        """設定ファイルなしでの初期化テスト"""
        with (
            patch("common.config_manager.ConfigManager._find_config_file", return_value=None),
            patch("common.config_manager.os.getenv") as mock_getenv,
        ):
            # pytest関連の環境変数検出を無効化
            def mock_getenv_side_effect(key: object, default=None):
                # pytest検出を回避するため、これらの変数はNoneを返す
                if key == "PYTEST_CURRENT_TEST":
                    return None
                if key == "_":
                    return "/usr/bin/python3"  # pytestを含まない値
                # その他の設定関連環境変数もNoneを返す
                if key in [
                    "APP_MODE",
                    "TEST_MODE",
                    "DEBUG",
                    "LOG_LEVEL",
                    "USE_MOCK_SERVICES",
                    "TEST_PROJECT_ROOT",
                    "TEST_DATA_DIR",
                    "QUALITY_THRESHOLD",
                    "AUTO_FIX",
                    "BATCH_SIZE",
                    "TIMEOUT_SECONDS",
                ]:
                    return None
                return default

            mock_getenv.side_effect = mock_getenv_side_effect

            manager = ConfigManager()
            config = manager.get_config()

            # デフォルト値が使用されることを確認
            assert config.mode == "production"
            assert config.test_mode is False

    def test_config_from_file(self) -> None:
        """設定ファイルからの読み込みテスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "mode": "test",
                "test_mode": True,
                "debug": True,
                "quality_threshold": 75,
                "auto_fix": True,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        try:
            manager = ConfigManager(config_path)
            config = manager.get_config()

            assert config.mode == "test"
            assert config.test_mode is True
            assert config.debug is True
            assert config.quality_threshold == 75
            assert config.auto_fix is True
        finally:
            config_path.unlink()

    def test_environment_variable_override(self) -> None:
        """環境変数による設定上書きテスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "mode": "production",
                "test_mode": False,
                "quality_threshold": 80,
            }
            yaml.dump(config_data, f)
            config_path = Path(f.name)

        # 環境変数を設定
        env_vars = {
            "APP_MODE": "test",
            "TEST_MODE": "true",
            "QUALITY_THRESHOLD": "70",
        }

        try:
            with patch.dict(os.environ, env_vars):
                manager = ConfigManager(config_path)
                config = manager.get_config()

                # 環境変数の値が優先されることを確認
                assert config.mode == "test"
                assert config.test_mode is True
                assert config.quality_threshold == 70
        finally:
            config_path.unlink()

    def test_pytest_auto_detection(self) -> None:
        """pytest実行時の自動検出テスト"""
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_something.py::test_method"}):
            manager = ConfigManager(None)
            config = manager.get_config()

            assert config.mode == "test"
            assert config.test_mode is True
            assert config.use_mock_services is True

    def test_mode_detection_methods(self) -> None:
        """モード検出メソッドのテスト"""
        # テストモード
        test_config = AppConfig(mode="test", test_mode=True)
        manager = ConfigManager(None)
        manager.config = test_config

        assert manager.is_test_mode() is True
        assert manager.is_production_mode() is False
        assert manager.should_use_mock_services() is True

        # 本番モード
        prod_config = AppConfig(mode="production", test_mode=False)
        manager.config = prod_config

        assert manager.is_test_mode() is False
        assert manager.is_production_mode() is True
        assert manager.should_use_mock_services() is False

    def test_log_level_adjustment(self) -> None:
        """ログレベル調整のテスト"""
        # テストモード時のログレベル調整
        test_config = AppConfig(mode="test", test_mode=True, log_level="DEBUG")
        manager = ConfigManager(None)
        manager.config = test_config

        assert manager.get_log_level() == "WARNING"  # テスト時は抑制

        # 本番モード時はそのまま
        prod_config = AppConfig(mode="production", test_mode=False, log_level="DEBUG")
        manager.config = prod_config

        assert manager.get_log_level() == "DEBUG"

    def test_save_config(self) -> None:
        """設定保存のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir) / "test_config.yaml"

            manager = ConfigManager(None)
            manager.config = AppConfig(
                mode="test",
                test_mode=True,
                quality_threshold=75,
            )

            manager.save_config(save_path)

            # 保存されたファイルを確認
            assert save_path.exists()

            with Path(save_path).open(encoding="utf-8") as f:
                saved_data = yaml.safe_load(f)

            assert saved_data["mode"] == "test"
            assert saved_data["test_mode"] is True
            assert saved_data["quality_threshold"] == 75


class TestGlobalFunctions:
    """グローバル関数のテスト"""

    def test_create_test_config(self) -> None:
        """テスト用設定作成のテスト"""
        config = create_test_config()

        assert config.mode == "test"
        assert config.test_mode is True
        assert config.use_mock_services is True
        assert config.log_level == "WARNING"
        assert config.batch_size == 10  # テスト用は小さく

    def test_create_production_config(self) -> None:
        """本番用設定作成のテスト"""
        config = create_production_config()

        assert config.mode == "production"
        assert config.test_mode is False
        assert config.use_mock_services is False
        assert config.log_level == "INFO"
        assert config.auto_fix is True
        assert config.batch_size == 100


class TestConfigIntegration:
    """設定の統合テスト"""

    def test_config_file_search(self) -> None:
        """設定ファイル検索のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 設定ファイルを作成
            config_file = temp_path / "app_config.yaml"
            config_data = {"mode": "test", "debug": True}

            with Path(config_file).open("w", encoding="utf-8") as f:
                yaml.dump(config_data, f)

            # 該当ディレクトリから実行
            with patch("pathlib.Path.cwd", return_value=temp_path):
                manager = ConfigManager()
                config = manager.get_config()

                assert config.mode == "test"
                assert config.debug is True

    def test_multiple_config_files(self) -> None:
        """複数の設定ファイル名での検索テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 優先度の低い設定ファイル
            config_file1 = temp_path / "settings.yaml"
            with Path(config_file1).open("w", encoding="utf-8") as f:
                yaml.dump({"mode": "production"}, f)

            # 優先度の高い設定ファイル
            config_file2 = temp_path / "app_config.yaml"
            with Path(config_file2).open("w", encoding="utf-8") as f:
                yaml.dump({"mode": "test"}, f)

            with patch("pathlib.Path.cwd", return_value=temp_path):
                manager = ConfigManager()

                # app_config.yamlが優先されることを確認
                assert manager.config_path == config_file2

    def test_environment_priority(self) -> None:
        """環境変数の優先度テスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            # ファイルでは production
            yaml.dump({"mode": "production", "debug": False}, f)
            config_path = Path(f.name)

        try:
            # 環境変数では test
            with patch.dict(os.environ, {"APP_MODE": "test", "DEBUG": "true"}):
                manager = ConfigManager(config_path)
                config = manager.get_config()

                # 環境変数が優先されることを確認
                assert config.mode == "test"
                assert config.debug is True
        finally:
            config_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
