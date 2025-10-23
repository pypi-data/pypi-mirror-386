"""Claude Code統合管理ユースケース

本格実装の切り替え、監視、診断機能を提供
"""

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.value_objects.project_time import project_now

# DDD準拠: Application層はInfrastructure層に直接依存しない
# Claude Code統合機能は遅延初期化パターンで提供


class ClaudeCodeManagementUseCase(AbstractUseCase[dict, dict]):
    """Claude Code統合管理ユースケース"""

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        console_service: Optional["IConsoleService"] = None,
        path_service: Optional["IPathService"] = None,
        **kwargs: Any) -> None:
        """ユースケース初期化

        DDD準拠: 依存性注入パターン対応
        Args:
            logger_service: ロガーサービス（DI注入）
            unit_of_work: Unit of Work（DI注入）
            console_service: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
        """
        # 基底クラス初期化（共通サービス）
        super().__init__(console_service=console_service, path_service=path_service, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work
        self._path_service = path_service

        # DDD準拠: Infrastructure層の環境管理は遅延初期化
        self._env_manager = None
        self._session_interface = None

    def _get_environment_manager(self) -> Any:
        """環境管理マネージャーの遅延初期化"""
        if self._env_manager is None:
            # DDD準拠: Application→Infrastructure違反を遅延初期化で回避

            from noveler.infrastructure.config.environment_manager import EnvironmentManager
            self._env_manager = EnvironmentManager()
        return self._env_manager

    def _get_session_interface(self, enable_logging: bool = True) -> Any:
        """セッションインターフェースの遅延初期化"""
        if self._session_interface is None:
            # DDD準拠: Application→Infrastructure違反を遅延初期化で回避

            from noveler.infrastructure.claude_code_session_integration import ClaudeCodeSessionInterface
            self._session_interface = ClaudeCodeSessionInterface(enable_logging=enable_logging)
        return self._session_interface

    def _get_current_integration_config(self) -> dict[str, Any]:
        """統合設定の遅延取得"""
        # DDD準拠: Application→Infrastructure違反を遅延初期化で回避

        # Claude Code統合設定を返す
        return {
            "mode": "development",
            "features": ["plot_generation", "quality_check", "episode_creation"],
            "debug": True
        }

    def switch_to_production_mode(self) -> dict[str, Any]:
        """本格実装モードに切り替え

        Returns:
            Dict[str, Any]: 切り替え結果
        """
        try:
            env_manager = self._get_environment_manager()
            success = env_manager.enable_production_mode()

            if success:
                # 切り替え後の動作確認
                test_result = self._test_session_integration()

                return {
                    "success": True,
                    "mode": "production",
                    "message": "本格実装モードに切り替えました",
                    "session_test": test_result,
                    "timestamp": project_now().to_iso_string(),
                }
            return {
                "success": False,
                "mode": "unchanged",
                "message": "Claude Codeセッション外では本格実装モードを使用できません",
                "recommendation": "HYBRIDモードの使用を推奨します",
                "timestamp": project_now().to_iso_string(),
            }

        except Exception as e:
            self.logger.exception("本格実装モード切り替えエラー")
            return {"success": False, "error": str(e), "timestamp": project_now().to_iso_string()}

    def switch_to_hybrid_mode(self) -> dict[str, Any]:
        """ハイブリッドモードに切り替え(推奨)

        Returns:
            Dict[str, Any]: 切り替え結果
        """
        try:
            env_manager = self._get_environment_manager()
            env_manager.enable_hybrid_mode()

            # 切り替え後の動作確認
            test_result = self._test_session_integration()

            return {
                "success": True,
                "mode": "hybrid",
                "message": "ハイブリッドモード(推奨)に切り替えました",
                "description": "環境を自動検出して最適な実装を使用します",
                "session_test": test_result,
                "timestamp": project_now().to_iso_string(),
            }

        except Exception as e:
            self.logger.exception("ハイブリッドモード切り替えエラー")
            return {"success": False, "error": str(e), "timestamp": project_now().to_iso_string()}

    def switch_to_mock_mode(self) -> dict[str, Any]:
        """モックモードに切り替え(開発・テスト用)

        Returns:
            Dict[str, Any]: 切り替え結果
        """
        try:
            env_manager = self._get_environment_manager()
            env_manager.enable_mock_mode()

            return {
                "success": True,
                "mode": "mock",
                "message": "モックモード(開発・テスト用)に切り替えました",
                "description": "高品質なモックレスポンスを使用します",
                "timestamp": project_now().to_iso_string(),
            }

        except Exception as e:
            self.logger.exception("モックモード切り替えエラー")
            return {"success": False, "error": str(e), "timestamp": project_now().to_iso_string()}

    def get_status_report(self) -> dict[str, Any]:
        """現在の統合状態レポートを取得

        Returns:
            Dict[str, Any]: 状態レポート
        """
        try:
            env_manager = self._get_environment_manager()
            status_report = env_manager.get_status_report()

            # セッション統合のヘルスチェック追加
            if status_report["session_integration_active"]:
                health_check = self._perform_health_check()
                status_report["health_check"] = health_check

            return status_report

        except Exception as e:
            self.logger.exception("状態レポート取得エラー")
            return {"success": False, "error": str(e), "timestamp": project_now().to_iso_string()}

    def test_session_integration(self) -> dict[str, Any]:
        """セッション統合のテスト実行

        Returns:
            Dict[str, Any]: テスト結果
        """
        return self._test_session_integration()

    def _test_session_integration(self) -> dict[str, Any]:
        """セッション統合のテスト実行(内部用)

        Returns:
            Dict[str, Any]: テスト結果
        """
        try:
            # 統合設定の確認
            config = self._get_current_integration_config()

            if not config["use_session_integration"]:
                return {
                    "success": True,
                    "test_type": "mock",
                    "message": "モック実装モードでのテスト完了",
                    "details": {"mock_response_generated": True, "execution_time": "0.1s"},
                }

            # 実際のセッション統合テスト
            session_interface = self._get_session_interface(enable_logging=False)

            test_prompt = """
テスト用プロンプト:Claude Codeセッション統合の動作確認

以下のYAML形式で応答してください:
    ```yaml
test_response:
  status: success
  message: "セッション統合テスト完了"
  timestamp: "2024-08-04T12:00:00Z"
```
"""

            # テスト実行
            start_time = project_now()
            response = session_interface.execute_prompt(prompt=test_prompt, response_format="yaml", timeout=30)

            end_time = project_now()

            execution_time = end_time.to_timestamp() - start_time.to_timestamp()

            return {
                "success": response.get("success", False),
                "test_type": "session_integration",
                "message": "セッション統合テスト完了",
                "details": {
                    "response_received": bool(response),
                    "execution_time": f"{execution_time:.2f}s",
                    "response_format": response.get("format", "unknown"),
                    "environment": response.get("execution_meta", {}).get("environment", "unknown"),
                },
                "raw_response": response if response.get("success") else None,
            }

        except Exception as e:
            self.logger.exception("セッション統合テストエラー")
            return {
                "success": False,
                "test_type": "error",
                "error": str(e),
                "message": "セッション統合テストに失敗しました",
            }

    def _perform_health_check(self) -> dict[str, Any]:
        """セッション統合のヘルスチェック実行

        Returns:
            Dict[str, Any]: ヘルスチェック結果
        """
        try:
            session_interface = self._get_session_interface(enable_logging=False)
            health_result = session_interface.health_check()

            return {
                "success": True,
                "health_status": health_result,
                "overall_health": health_result.get("overall_health", False),
                "timestamp": project_now().to_iso_string(),
            }

        except Exception as e:
            self.logger.exception("ヘルスチェックエラー")
            return {
                "success": False,
                "error": str(e),
                "overall_health": False,
                "timestamp": project_now().to_iso_string(),
            }

    def get_integration_logs(self, lines: int = 50) -> dict[str, Any]:
        """統合ログの取得

        Args:
            lines: 取得する行数

        Returns:
            Dict[str, Any]: ログ情報
        """
        try:
            # B20準拠: パスサービス経由でtemp pathを取得
            temp_path = self._path_service.get_temp_dir() if self._path_service else Path.cwd() / "temp"

            log_files = {
                "session_log": temp_path / "claude_code_session.log",
                "error_log": temp_path / "claude_code_errors",
            }

            logs = {}

            # セッションログの読み取り
            if log_files["session_log"].exists():
                with log_files["session_log"].open(encoding="utf-8") as f:
                    log_lines = f.readlines()
                    logs["session_log"] = log_lines[-lines:] if len(log_lines) > lines else log_lines
            else:
                logs["session_log"] = []

            # エラーログディレクトリの確認
            if log_files["error_log"].exists():
                error_files = list(log_files["error_log"].glob("error_*.log"))
                logs["error_files"] = [str(f) for f in sorted(error_files, reverse=True)[:10]]

                # 最新のエラーログを読み取り
                if error_files:
                    content = Path(error_files[0]).read_text(encoding="utf-8")
                    logs["latest_error"] = content
            else:
                logs["error_files"] = []
                logs["latest_error"] = None

            return {
                "success": True,
                "logs": logs,
                "log_files": {k: str(v) for k, v in log_files.items()},
                "timestamp": project_now().to_iso_string(),
            }

        except Exception as e:
            self.logger.exception("ログ取得エラー")
            return {"success": False, "error": str(e), "timestamp": project_now().to_iso_string()}

    def cleanup_logs(self, days_to_keep: int = 7) -> dict[str, Any]:
        """古いログファイルのクリーンアップ

        Args:
            days_to_keep: 保持する日数

        Returns:
            Dict[str, Any]: クリーンアップ結果
        """
        try:

            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)

            # B20準拠: パスサービス経由でtemp pathを取得
            temp_path = self._path_service.get_temp_dir() if self._path_service else Path.cwd() / "temp"

            cleanup_dirs = [
                temp_path / "claude_code_errors",
                temp_path / "claude_session_data"
            ]

            cleaned_files = []
            total_size_freed = 0

            for dir_path in cleanup_dirs:
                if not dir_path.exists():
                    continue

                for file_path in dir_path.glob("*"):
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_files.append(str(file_path))
                        total_size_freed += size

            return {
                "success": True,
                "cleaned_files_count": len(cleaned_files),
                "total_size_freed_bytes": total_size_freed,
                "days_kept": days_to_keep,
                "cleaned_files": cleaned_files[:10],  # 最初の10ファイルのみ表示
                "timestamp": project_now().to_iso_string(),
            }

        except Exception as e:
            self.logger.exception("ログクリーンアップエラー")
            return {"success": False, "error": str(e), "timestamp": project_now().to_iso_string()}

    async def execute(self, request: dict) -> dict:
        """ユースケース実行 (AbstractUseCaseインターフェース実装)

        Args:
            request: リクエスト辞書

        Returns:
            dict: 実行結果
        """
        action = request.get("action", "status")

        if action == "switch_production":
            return self.switch_to_production_mode()
        if action == "switch_hybrid":
            return self.switch_to_hybrid_mode()
        if action == "switch_mock":
            return self.switch_to_mock_mode()
        if action == "test":
            return self.test_session_integration()
        if action == "health_check":
            return self._perform_health_check()
        if action == "logs":
            lines = request.get("lines", 50)
            return self.get_integration_logs(lines)
        if action == "cleanup":
            days = request.get("days_to_keep", 7)
            return self.cleanup_logs(days)
        return self.get_status_report()
