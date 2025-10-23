"""Infrastructure.claude_code_environment_manager
Where: Infrastructure module managing Claude Code environment setup.
What: Provides helpers to configure environment variables and runtime settings for Claude Code integration.
Why: Ensures Claude Code workflows run with consistent environment preparation.
"""

from noveler.presentation.shared.shared_utilities import console

"Claude Code環境管理モジュール\n\n本格実装と開発実装の段階的切り替えを管理\n環境変数による制御と設定ファイルベースの管理を提供\n"
import json
import os
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.logging.unified_logger import get_logger


class ClaudeCodeMode(Enum):
    """Claude Code統合モード"""

    MOCK = "mock"
    HYBRID = "hybrid"
    PRODUCTION = "production"
    FORCE_SESSION = "force_session"


class ClaudeCodeEnvironmentManager:
    """Claude Code環境管理クラス

    実装の段階的切り替えと環境検出を統合管理
    """

    def __init__(self) -> None:
        """環境管理クラス初期化"""
        self.logger = get_logger(__name__)
        self.config_file = Path("temp/claude_code_config.json")
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_configuration()

    def _load_configuration(self) -> None:
        """設定ファイルから環境設定を読み込み"""
        default_config: dict[str, Any] = {
            "mode": ClaudeCodeMode.HYBRID.value,
            "enable_logging": True,
            "fallback_to_mock": True,
            "session_timeout": 120,
            "auto_detect_environment": True,
            "last_updated": project_now().to_iso_string(),
        }
        try:
            if self.config_file.exists():
                with self.config_file.open(encoding="utf-8") as f:
                    loaded_config: dict[str, Any] = json.load(f)
                    self.config = {**default_config, **loaded_config}
            else:
                self.config = default_config
                self._save_configuration()
        except Exception as e:
            console.print(f"設定ファイル読み込みエラー、デフォルト設定を使用: {e}")
            self.config = default_config

    def _save_configuration(self) -> None:
        """現在の設定をファイルに保存"""
        try:
            self.config["last_updated"] = project_now().to_iso_string()
            with self.config_file.open("w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.exception("設定ファイル保存エラー: %s", e)

    def get_current_mode(self) -> ClaudeCodeMode:
        """現在の動作モードを取得

        Returns:
            ClaudeCodeMode: 現在の動作モード
        """
        env_mode = os.environ.get("CLAUDE_CODE_MODE")
        if env_mode:
            try:
                return ClaudeCodeMode(env_mode.lower())
            except ValueError:
                console.print(f"無効なCLAUDE_CODE_MODE値: {env_mode}")
        config_mode = self.config.get("mode", ClaudeCodeMode.HYBRID.value)
        try:
            return ClaudeCodeMode(config_mode)
        except ValueError:
            console.print(f"無効な設定モード: {config_mode}, HYBRIDに設定")
            return ClaudeCodeMode.HYBRID

    def should_use_session_integration(self) -> bool:
        """セッション統合を使用すべきかを判定

        Returns:
            bool: セッション統合を使用する場合True
        """
        mode = self.get_current_mode()
        if mode == ClaudeCodeMode.MOCK:
            return False
        if mode == ClaudeCodeMode.FORCE_SESSION:
            return True
        if mode == ClaudeCodeMode.PRODUCTION:
            return self._is_claude_code_session()
        if mode == ClaudeCodeMode.HYBRID:
            return self._is_claude_code_session() and self.config.get("auto_detect_environment", True)
        return False

    def _is_claude_code_session(self) -> bool:
        """Claude Codeセッション内での実行かを判定"""
        from noveler.infrastructure.claude_code_session_integration import ClaudeCodeEnvironmentDetector

        return ClaudeCodeEnvironmentDetector.is_claude_code_environment()

    def get_integration_config(self) -> dict[str, Any]:
        """統合設定を取得

        Returns:
            Dict[str, Any]: 統合設定辞書
        """
        return {
            "mode": self.get_current_mode().value,
            "use_session_integration": self.should_use_session_integration(),
            "enable_logging": self.config.get("enable_logging", True),
            "fallback_to_mock": self.config.get("fallback_to_mock", True),
            "session_timeout": self.config.get("session_timeout", 120),
            "is_claude_code_session": self._is_claude_code_session(),
            "environment_auto_detected": self.config.get("auto_detect_environment", True),
        }

    def set_mode(self, mode: ClaudeCodeMode, save_to_file: bool = True) -> None:
        """動作モードを設定

        Args:
            mode: 設定する動作モード
            save_to_file: ファイルに保存するか
        """
        self.config["mode"] = mode.value
        if save_to_file:
            self._save_configuration()
        console.print(f"Claude Code動作モードを{mode.value}に設定しました")

    def enable_production_mode(self) -> bool:
        """本格実装モードを有効化

        Returns:
            bool: 有効化に成功した場合True
        """
        if not self._is_claude_code_session():
            console.print("Claude Codeセッション外では本格実装モードを使用できません")
            return False
        self.set_mode(ClaudeCodeMode.PRODUCTION)
        console.print("本格実装モードを有効化しました")
        return True

    def enable_hybrid_mode(self) -> None:
        """ハイブリッドモードを有効化(推奨設定)"""
        self.set_mode(ClaudeCodeMode.HYBRID)
        console.print("ハイブリッドモード(推奨)を有効化しました")

    def enable_mock_mode(self) -> None:
        """モックモードを有効化(開発・テスト用)"""
        self.set_mode(ClaudeCodeMode.MOCK)
        console.print("モックモード(開発・テスト用)を有効化しました")

    def get_status_report(self) -> dict[str, Any]:
        """現在の状態レポートを取得

        Returns:
            Dict[str, Any]: 状態レポート
        """
        config = self.get_integration_config()
        return {
            "current_mode": config["mode"],
            "session_integration_active": config["use_session_integration"],
            "claude_code_session_detected": config["is_claude_code_session"],
            "configuration": {
                "fallback_enabled": config["fallback_to_mock"],
                "logging_enabled": config["enable_logging"],
                "auto_detection_enabled": config["environment_auto_detected"],
                "session_timeout": config["session_timeout"],
            },
            "file_paths": {"config_file": str(self.config_file), "config_exists": self.config_file.exists()},
            "environment_variables": {
                "CLAUDE_CODE_MODE": os.environ.get("CLAUDE_CODE_MODE"),
                "CLAUDE_CODE_SESSION": os.environ.get("CLAUDE_CODE_SESSION"),
                "ANTHROPIC_CLAUDE_CODE": os.environ.get("ANTHROPIC_CLAUDE_CODE"),
            },
            "recommendations": self._get_recommendations(config),
            "generated_at": project_now().to_iso_string(),
        }

    def _get_recommendations(self, config: dict[str, Any]) -> list[str]:
        """現在の設定に基づく推奨事項を生成

        Args:
            config: 現在の統合設定

        Returns:
            list[str]: 推奨事項のリスト
        """
        recommendations = []
        if config["mode"] == ClaudeCodeMode.MOCK.value:
            recommendations.append(
                "開発・テスト用モックモードです。本格実装をテストする場合はHYBRIDモードに切り替えてください"
            )
        if config["mode"] == ClaudeCodeMode.PRODUCTION.value and (not config["is_claude_code_session"]):
            recommendations.append("本格実装モードですがClaude Codeセッション外です。HYBRIDモードの使用を推奨します")
        if not config["fallback_to_mock"]:
            recommendations.append("フォールバック機能が無効です。エラー時の安全性のため有効化を推奨します")
        if config["is_claude_code_session"] and config["mode"] == ClaudeCodeMode.MOCK.value:
            recommendations.append(
                "Claude Codeセッション内でモックモードです。本格実装を試すためHYBRIDまたはPRODUCTIONモードを検討してください"
            )
        return recommendations


_environment_manager: ClaudeCodeEnvironmentManager | None = None


def get_environment_manager() -> ClaudeCodeEnvironmentManager:
    """環境管理クラスのグローバルインスタンスを取得

    Returns:
        ClaudeCodeEnvironmentManager: 環境管理インスタンス
    """
    global _environment_manager
    if _environment_manager is None:
        _environment_manager = ClaudeCodeEnvironmentManager()
    return _environment_manager


def get_current_integration_config() -> dict[str, Any]:
    """現在の統合設定を取得(便利関数)

    Returns:
        Dict[str, Any]: 統合設定
    """
    return get_environment_manager().get_integration_config()


def should_use_session_integration() -> bool:
    """セッション統合を使用すべきかを判定(便利関数)

    Returns:
        bool: セッション統合を使用する場合True
    """
    return get_environment_manager().should_use_session_integration()
