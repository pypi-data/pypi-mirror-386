"""Facade bridging CLI calls with the Message Bus integration layer."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces import IConfigurationService, IConsoleService, ILoggerService, IPathService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.integration.message_bus_integration import (
    create_legacy_adapter,
    create_message_bus_integration,
)
from noveler.domain.commands.plot_commands import ValidatePlotCommand


class CLIMessageBusFacade:
    """Handle CLI compatibility by delegating to the Message Bus layer."""

    def __init__(
        self,
        logger_service: "ILoggerService",
        console_service: "IConsoleService",
        unit_of_work: "IUnitOfWork",
        config_service: "IConfigurationService",
        path_service: "IPathService"
    ) -> None:
        """Initialise the facade with required infrastructure services."""
        self.logger_service = logger_service
        self.console_service = console_service
        self.unit_of_work = unit_of_work
        self.config_service = config_service
        self.path_service = path_service

        # Message Bus統合サービス初期化
        self.integration_service = create_message_bus_integration(
            logger_service=logger_service,
            unit_of_work=unit_of_work,
            config_service=config_service,
            path_service=path_service
        )

        # レガシーアダプター初期化
        self.legacy_adapter = create_legacy_adapter(self.integration_service)

        # Message Bus初期化（遅延実行）
        self._message_bus_initialized = False

    def _ensure_message_bus_initialized(self) -> None:
        """Ensure the message bus connection is initialised lazily."""
        if not self._message_bus_initialized:
            try:
                self.integration_service.initialize_message_bus(async_mode=False)
                self._message_bus_initialized = True
                self.logger_service.info("CLI Message Bus統合初期化完了")
            except Exception as e:
                self.logger_service.exception(f"Message Bus初期化エラー: {e}")
                raise

    # -----------------------------------
    # プロット関連コマンド（既存インターフェース維持）
    # -----------------------------------

    def generate_plot(
        self,
        project_root: str | None = None,
        episode_number: int | None = None,
        chapter_title: str | None = None,
        use_ai: bool = True,
        **kwargs
    ) -> dict[str, Any]:
        """Generate plot data via the Message Bus while preserving CLI shape."""
        self._ensure_message_bus_initialized()

        # プロジェクトルート解決
        if project_root is None:
            project_root = str(self.path_service.get_project_root())

        self.console_service.info(f"プロット生成開始 (Episode {episode_number or '?'})")

        try:
            # Message Bus経由で実行
            result = self.legacy_adapter.execute_plot_generation(
                project_root=project_root,
                episode_number=episode_number,
                chapter_title=chapter_title,
                use_ai_enhancement=use_ai,
                quality_check=kwargs.get("quality_check", True),
                auto_save=kwargs.get("auto_save", True),
                **kwargs
            )

            self.console_service.success("プロット生成完了")

            # CLI用レスポンス形式
            return {
                "status": "success",
                "result": result,
                "episode_number": episode_number,
                "generated_at": result.metadata.get("generated_at") if hasattr(result, "metadata") else None
            }

        except Exception as e:
            error_msg = f"プロット生成エラー: {e}"
            self.console_service.error(error_msg)
            self.logger_service.exception(error_msg)

            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    def validate_plot(
        self,
        plot_file_path: str,
        quality_criteria: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Validate plot quality via the Message Bus while preserving CLI shape."""
        self._ensure_message_bus_initialized()

        self.console_service.info(f"プロット品質チェック開始: {plot_file_path}")

        try:
            # ファイル読み込み
            plot_path = Path(plot_file_path)
            if not plot_path.exists():
                msg = f"プロットファイルが見つかりません: {plot_file_path}"
                raise FileNotFoundError(msg)

            plot_content = plot_path.read_text(encoding="utf-8")

            # デフォルト品質基準
            if quality_criteria is None:
                quality_criteria = {
                    "min_length": 200,
                    "require_title": True,
                    "require_structure": True,
                    "min_paragraphs": 3
                }

            # Message Bus経由で実行
            result = self.legacy_adapter.validate_plot_quality(
                plot_content=plot_content,
                validation_criteria=quality_criteria,
                project_root=str(self.path_service.get_project_root())
            )

            # 結果表示
            quality_score = result.get("quality_score", 0.0)
            passed = result.get("passed_validation", False)

            if passed:
                self.console_service.success(f"品質チェック合格 (スコア: {quality_score:.2f})")
            else:
                self.console_service.warning(f"品質改善推奨 (スコア: {quality_score:.2f})")

            return {
                "status": "success",
                "quality_score": quality_score,
                "passed_validation": passed,
                "metrics": result.get("metrics", {}),
                "file_path": plot_file_path
            }

        except Exception as e:
            error_msg = f"プロット品質チェックエラー: {e}"
            self.console_service.error(error_msg)
            self.logger_service.exception(error_msg)

            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    # -----------------------------------
    # 非同期実行オプション
    # -----------------------------------

    async def generate_plot_async(
        self,
        project_root: str | None = None,
        episode_number: int | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """Generate plot data asynchronously and return a CLI-shaped payload."""
        # 非同期Message Bus初期化
        self.integration_service.initialize_message_bus(async_mode=True)

        if project_root is None:
            project_root = str(self.path_service.get_project_root())

        self.console_service.info(f"非同期プロット生成開始 (Episode {episode_number or '?'})")

        try:
            result = await self.legacy_adapter.execute_plot_generation_async(
                project_root=project_root,
                episode_number=episode_number,
                **kwargs
            )

            self.console_service.success("非同期プロット生成完了")

            return {
                "status": "success",
                "result": result,
                "episode_number": episode_number,
                "execution_mode": "async"
            }

        except Exception as e:
            error_msg = f"非同期プロット生成エラー: {e}"
            self.console_service.error(error_msg)
            self.logger_service.exception(error_msg)

            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_mode": "async"
            }

    # -----------------------------------
    # 統計・監視機能
    # -----------------------------------

    def get_message_bus_metrics(self) -> dict[str, Any]:
        """Return diagnostics about the Message Bus integration performance."""
        try:
            metrics = self.integration_service.get_performance_metrics()

            self.console_service.info("Message Bus メトリクス:")
            for bus_type, bus_metrics in metrics.items():
                self.console_service.info(f"  {bus_type}:")
                for key, value in bus_metrics.items():
                    self.console_service.info(f"    {key}: {value}")

            return {
                "status": "success",
                "metrics": metrics
            }

        except Exception as e:
            error_msg = f"メトリクス取得エラー: {e}"
            self.console_service.error(error_msg)
            return {
                "status": "error",
                "error": str(e)
            }

    # -----------------------------------
    # CLI互換ヘルパーメソッド
    # -----------------------------------

    def show_integration_status(self) -> None:
        """Return a summary describing the Message Bus integration state."""
        try:
            self._ensure_message_bus_initialized()

            self.console_service.info("=== Message Bus統合状況 ===")
            self.console_service.info("統合サービス: 初期化完了")
            self.console_service.info("レガシーアダプター: 有効")

            # メトリクス表示
            metrics = self.integration_service.get_performance_metrics()
            if metrics:
                self.console_service.info("パフォーマンスメトリクス:")
                for bus_type, bus_metrics in metrics.items():
                    processed = bus_metrics.get("messages_processed", 0)
                    errors = bus_metrics.get("errors", 0)
                    self.console_service.info(f"  {bus_type}: 処理済み={processed}, エラー={errors}")

        except Exception as e:
            self.console_service.error(f"統合状況取得エラー: {e}")

    def test_message_bus_connection(self) -> bool:
        """Test the Message Bus connection and return its status."""
        try:
            self._ensure_message_bus_initialized()

            # 簡単なテストコマンド実行
            test_command = ValidatePlotCommand(
                plot_content="テストコンテンツ",
                validation_criteria={"test": True},
                project_root=str(self.path_service.get_project_root())
            )

            message_bus = self.integration_service.get_message_bus(async_mode=False)
            message_bus.handle(test_command)

            self.console_service.success("Message Bus接続テスト成功")
            return True

        except Exception as e:
            self.console_service.error(f"Message Bus接続テストエラー: {e}")
            self.logger_service.exception(f"Message Bus接続テストエラー: {e}")
            return False


# ファサード作成ファクトリー関数
def create_cli_message_bus_facade(
    logger_service: "ILoggerService",
    console_service: "IConsoleService",
    unit_of_work: "IUnitOfWork",
    config_service: "IConfigurationService",
    path_service: "IPathService"
) -> CLIMessageBusFacade:
    """Factory helper that creates the CLI message bus facade."""
    return CLIMessageBusFacade(
        logger_service=logger_service,
        console_service=console_service,
        unit_of_work=unit_of_work,
        config_service=config_service,
        path_service=path_service
    )
