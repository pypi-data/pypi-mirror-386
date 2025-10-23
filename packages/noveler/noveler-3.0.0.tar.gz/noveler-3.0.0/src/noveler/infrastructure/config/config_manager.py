"""Configuration Manager for Test/Production Mode Switching

テスト/本番モード切り替え用設定管理
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

try:
    from noveler.presentation.shared.shared_utilities import get_common_path_service
except ImportError:  # pragma: no cover - optional dependency for production runtime
    get_common_path_service = None


@dataclass
class AppConfig:
    """アプリケーション設定"""

    mode: str = "production"
    test_mode: bool = False
    debug: bool = False
    log_level: str = "INFO"
    use_mock_services: bool = False

    # テスト専用設定
    test_project_root: str | None = None
    test_data_dir: str | None = None

    # 品質チェック設定
    quality_threshold: int = 80
    auto_fix: bool = False

    # パフォーマンス設定
    batch_size: int = 100
    timeout_seconds: int = 30


class ConfigManager:
    """設定管理クラス"""

    def __init__(
        self,
        config_path: Path | None = None,
        *,
        path_service: Any | None = None,
        logger_service: Any | None = None,
        console_service: Any | None = None,
    ) -> None:
        self.logger_service = logger_service
        self.console_service = console_service
        self.path_service = path_service or self._create_default_path_service()

        self.config_path = self._resolve_initial_config_path(config_path)
        self.config = self._load_config()

    def _create_default_path_service(self) -> Any | None:
        """Create a default path service when available."""
        if get_common_path_service is None:
            return None

        try:
            return get_common_path_service()
        except Exception:  # pragma: no cover - fallback when service is unavailable
            return None

    def _resolve_initial_config_path(self, explicit_path: Path | None) -> Path | None:
        """Resolve configuration path using explicit path or path service."""
        if explicit_path:
            return Path(explicit_path)

        if self.path_service is not None:
            try:
                service_path = self.path_service.get_config_path()
            except AttributeError:
                service_path = None

            if service_path:
                return Path(service_path)

        return self._find_config_file()

    def _log_warning(self, message: str) -> None:
        """Log a warning message when services are available."""
        if self.logger_service and hasattr(self.logger_service, "warning"):
            self.logger_service.warning(message)
        elif self.console_service and hasattr(self.console_service, "print"):
            self.console_service.print(message)

    def _ensure_config_path(self) -> Path | None:
        """Ensure that the configuration path is resolved."""
        if self.config_path is None:
            self.config_path = self._resolve_initial_config_path(None)
        return self.config_path

    def _find_config_file(self) -> Path | None:
        """設定ファイルを検索"""
        # 環境変数から取得
        env_config: dict[str, Any] = os.getenv("APP_CONFIG_PATH")
        if env_config:
            return Path(env_config)

        # カレントディレクトリから検索
        current_dir = Path.cwd()

        # よく使われる設定ファイル名
        config_names = [
            "app_config.yaml",
            "config.yaml",
            "settings.yaml",
            "app_settings.yaml",
        ]

        # カレントディレクトリとその親ディレクトリを検索
        for directory in [current_dir, *list(current_dir.parents)]:
            for config_name in config_names:
                config_file = directory / config_name
                if config_file.exists():
                    return config_file

            # configディレクトリも検索
            config_dir = directory / "config"
            if config_dir.exists():
                for config_name in config_names:
                    config_file = config_dir / config_name
                    if config_file.exists():
                        return config_file

        return None

    def _load_config_from_file(self, config_path: Path | None) -> dict[str, Any]:
        """設定ファイルから辞書を読み込む"""
        if not config_path:
            return {}

        try:
            path_obj = Path(config_path)
            if not path_obj.exists():
                return {}

            content = path_obj.read_text(encoding="utf-8")
        except Exception as exc:
            self._log_warning(f"Warning: 設定ファイルの読み込みに失敗しました: {exc}")
            return {}

        try:
            loaded = yaml.safe_load(content) or {}
        except Exception as exc:
            self._log_warning(f"Warning: 設定ファイルの解析に失敗しました: {exc}")
            return {}

        if not isinstance(loaded, dict):
            self._log_warning("Warning: 設定ファイルの形式が不正です。辞書を期待します。")
            return {}

        return loaded

    def _load_config(self) -> AppConfig:
        """設定を読み込み"""
        config_dict = self._load_config_from_file(self._ensure_config_path())

        # 環境変数から設定を読み込み(優先度高)
        env_config: dict[str, Any] = self._load_from_environment()
        config_dict.update(env_config)

        # AppConfigオブジェクトを作成
        return AppConfig(**{k: v for k, v in config_dict.items() if hasattr(AppConfig, k)})

    def _load_from_environment(self) -> dict[str, Any]:
        """環境変数から設定を読み込み"""
        env_mappings = {
            "APP_MODE": "mode",
            "TEST_MODE": "test_mode",
            "DEBUG": "debug",
            "LOG_LEVEL": "log_level",
            "USE_MOCK_SERVICES": "use_mock_services",
            "TEST_PROJECT_ROOT": "test_project_root",
            "TEST_DATA_DIR": "test_data_dir",
            "QUALITY_THRESHOLD": "quality_threshold",
            "AUTO_FIX": "auto_fix",
            "BATCH_SIZE": "batch_size",
            "TIMEOUT_SECONDS": "timeout_seconds",
        }

        config: dict[str, Any] = {}
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # 型変換
                if config_key in ["test_mode", "debug", "use_mock_services", "auto_fix"]:
                    config[config_key] = value.lower() in ("true", "1", "yes", "on")
                elif config_key in ["quality_threshold", "batch_size", "timeout_seconds"]:
                    try:
                        config[config_key] = int(value)
                    except ValueError:
                        self._log_warning(
                            f"Warning: Invalid integer value for {config_key}: {value}"
                        )
                else:
                    config[config_key] = value

        # テストモードの自動検出
        if os.getenv("PYTEST_CURRENT_TEST") or "pytest" in os.getenv("_", ""):
            config["mode"] = "test"
            config["test_mode"] = True
            config["use_mock_services"] = True

        return config

    def load_config(self) -> dict[str, Any]:
        """設定ファイルを読み込み辞書として返す"""
        config_path = self._ensure_config_path()
        file_config = self._load_config_from_file(config_path)

        env_config = self._load_from_environment()
        merged = {**file_config, **env_config}
        self.config = AppConfig(**{k: v for k, v in merged.items() if hasattr(AppConfig, k)})

        return file_config

    def reload_config(self) -> None:
        """設定を再読み込み"""
        self.config = self._load_config()

    def save_config(self, config_data: dict[str, Any] | Path | str | None = None, config_path: Path | None = None) -> bool:
        """設定をファイルに保存"""
        if config_data is None or isinstance(config_data, (str, Path)):
            if isinstance(config_data, (str, Path)):
                config_path = Path(config_data)
            data_payload = vars(self.config).copy() if self.config is not None else {}
        else:
            data_payload = dict(config_data)

        save_path = config_path or self._ensure_config_path()

        if save_path is None and self.path_service is not None:
            try:
                config_dir = self.path_service.get_config_dir()
            except AttributeError:
                config_dir = None

            if config_dir:
                save_path = Path(config_dir) / "settings.yaml"

        if save_path is None:
            save_path = Path.cwd() / "app_config.yaml"

        save_path = Path(save_path)

        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            yaml_content = yaml.dump(
                data_payload,
                default_flow_style=False,
            )
            save_path.write_text(yaml_content, encoding="utf-8")
        except Exception as exc:
            self._log_warning(f"Failed to save config to {save_path}: {exc}")
            return False

        if self.config is not None:
            updated = vars(self.config).copy()
        else:
            updated = {}

        for key, value in data_payload.items():
            if hasattr(AppConfig, key):
                updated[key] = value

        if updated:
            self.config = AppConfig(**updated)

        self.config_path = save_path
        return True

    def get_config(self) -> AppConfig:
        """設定を取得"""
        return self.config

    def is_test_mode(self) -> bool:
        """テストモードかどうか"""
        return self.config.test_mode or self.config.mode == "test"

    def is_production_mode(self) -> bool:
        """本番モードかどうか"""
        return self.config.mode == "production" and not self.config.test_mode

    def should_use_mock_services(self) -> bool:
        """モックサービスを使用するかどうか"""
        return self.config.use_mock_services or self.is_test_mode()

    def get_log_level(self) -> str:
        """ログレベルを取得"""
        if self.is_test_mode():
            return "WARNING"  # テスト時はログを抑制
        return self.config.log_level

    def get_claude_timeout(self) -> int:
        """Claude APIタイムアウト時間を取得"""
        return getattr(self.config, "claude_timeout", 60)

    def get_claude_max_retries(self) -> int:
        """Claude API最大リトライ回数を取得"""
        return getattr(self.config, "claude_max_retries", 3)

    def get_claude_retry_delay(self) -> float:
        """Claude APIリトライ間隔を取得"""
        return getattr(self.config, "claude_retry_delay", 1.0)

    def get_max_file_size_mb(self) -> int:
        """最大ファイルサイズ（MB）を取得"""
        return getattr(self.config, "max_file_size_mb", 10)

    def get_encoding(self) -> str:
        """デフォルト文字エンコーディングを取得"""
        return getattr(self.config, "encoding", "utf-8")

    def get_min_quality_score(self) -> int:
        """最低品質スコアを取得"""
        return getattr(self.config, "min_quality_score", 70)

    def get_confidence_threshold(self) -> float:
        """信頼度閾値を取得"""
        return getattr(self.config, "confidence_threshold", 0.8)

    def get_analysis_depth(self) -> str:
        """分析の深さを取得"""
        return getattr(self.config, "analysis_depth", "detailed")

    def get_default_path(self, path_type: str) -> str:
        """デフォルトパスを取得"""
        default_paths = getattr(self.config, "default_paths", {})
        return default_paths.get(
            path_type,
            {
                "manuscript": "40_原稿",
                "plot": "20_プロット",
                "settings": "30_設定集",
                "management": "50_管理資料",
                "planning": "10_企画",
            }.get(path_type, ""),
        )


# グローバル設定マネージャー
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """グローバル設定マネージャーを取得"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_app_config() -> AppConfig:
    """アプリケーション設定を取得"""
    return get_config_manager().get_config()


def is_test_mode() -> bool:
    """テストモードかどうか"""
    return get_config_manager().is_test_mode()


def should_use_mock_services() -> bool:
    """モックサービスを使用するかどうか"""
    return get_config_manager().should_use_mock_services()


def create_test_config() -> AppConfig:
    """テスト用設定を作成"""
    return AppConfig(
        mode="test",
        test_mode=True,
        debug=True,
        log_level="WARNING",
        use_mock_services=True,
        quality_threshold=70,  # テスト時は少し緩く
        auto_fix=False,
        batch_size=10,  # テスト時は小さく
        timeout_seconds=5,
    )


def create_production_config() -> AppConfig:
    """本番用設定を作成"""
    return AppConfig(
        mode="production",
        test_mode=False,
        debug=False,
        log_level="INFO",
        use_mock_services=False,
        quality_threshold=80,
        auto_fix=True,
        batch_size=100,
        timeout_seconds=30,
    )
