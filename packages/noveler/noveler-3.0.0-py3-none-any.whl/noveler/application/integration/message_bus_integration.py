"""Message Bus統合サービス

SPEC-901-DDD-REFACTORING対応:
- 既存ユースケースとMessage Busの統合
- ハンドラー登録とBootstrap処理
- CLI統合のためのファサードパターン実装
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces import IConfigurationService, ILoggerService, IPathService

from noveler.application.handlers.plot_command_handlers import (
    MasterPlotUpdateCommandHandler,
    PlotGenerationCommandHandler,
    PlotSaveCommandHandler,
    PlotValidationCommandHandler,
)
from noveler.application.handlers.plot_event_handlers import PlotEventHandlerAggregate
from noveler.application.message_bus import AsyncMessageBus, MessageBus, create_mcp_message_bus
from noveler.application.unit_of_work import AbstractUnitOfWork
from noveler.infrastructure.repositories.outbox_repository import FileOutboxRepository
from noveler.infrastructure.services.idempotency_store import FileIdempotencyStore

# コマンドとハンドラーのインポート
from noveler.domain.commands.plot_commands import (
    GeneratePlotCommand,
    SavePlotCommand,
    UpdateMasterPlotCommand,
    ValidatePlotCommand,
)


class MessageBusIntegrationService:
    """Message Bus統合サービス

    既存ユースケースとMessage Busの統合を管理
    DDDパターンに準拠したBootstrap処理を提供
    """

    def __init__(
        self,
        logger_service: "ILoggerService",
        unit_of_work: AbstractUnitOfWork,
        config_service: "IConfigurationService",
        path_service: "IPathService"
    ) -> None:
        """統合サービス初期化

        Args:
            logger_service: ロガーサービス
            unit_of_work: Unit of Work実装
            config_service: 設定サービス
            path_service: パスサービス
        """
        self.logger_service = logger_service
        self.unit_of_work = unit_of_work
        self.config_service = config_service
        self.path_service = path_service

        # Message Bus インスタンス
        self._message_bus: MessageBus | None = None
        self._async_message_bus: AsyncMessageBus | None = None
        self._outbox_repository: FileOutboxRepository | None = None
        self._idempotency_store: FileIdempotencyStore | None = None

    def initialize_message_bus(self, async_mode: bool = False) -> MessageBus:
        """Message Bus初期化とハンドラー登録

        Args:
            async_mode: 非同期モード有効化

        Returns:
            MessageBus: 初期化済みMessage Busインスタンス
        """
        self.logger_service.info("Message Bus統合初期化開始")

        try:
            # コマンドハンドラー作成
            command_handlers = self._create_command_handlers()

            # イベントハンドラー作成
            event_handlers = self._create_event_handlers()

            # Message Bus作成
            if async_mode:
                outbox_repo, idem_store = self._ensure_support_components()

                self._async_message_bus = AsyncMessageBus(
                    uow=self.unit_of_work,
                    event_handlers=event_handlers,
                    command_handlers=command_handlers,
                    logger=self.logger_service,
                    max_concurrent_events=5,
                    outbox_repository=outbox_repo,
                    idempotency_store=idem_store,
                )
                message_bus = self._async_message_bus
            else:
                outbox_repo, idem_store = self._ensure_support_components()

                self._message_bus = MessageBus(
                    uow=self.unit_of_work,
                    event_handlers=event_handlers,
                    command_handlers=command_handlers,
                    logger=self.logger_service,
                    enable_async=False,
                    outbox_repository=outbox_repo,
                    idempotency_store=idem_store,
                )
                message_bus = self._message_bus

            self.logger_service.info(
                f"Message Bus初期化完了: async_mode={async_mode}, "
                f"commands={len(command_handlers)}, events={len(event_handlers)}"
            )

            return message_bus

        except Exception as e:
            self.logger_service.exception(f"Message Bus初期化エラー: {e}")
            raise

    def _create_command_handlers(self) -> dict[type, Any]:
        """コマンドハンドラー作成

        Returns:
            Dict[Type, Any]: コマンドハンドラー辞書
        """
        # ハンドラーインスタンス作成
        plot_generation_handler = PlotGenerationCommandHandler(
            logger_service=self.logger_service,
            unit_of_work=self.unit_of_work,
            path_service=self.path_service,
            config_service=self.config_service
        )

        plot_validation_handler = PlotValidationCommandHandler(
            logger_service=self.logger_service,
            unit_of_work=self.unit_of_work
        )

        plot_save_handler = PlotSaveCommandHandler(
            logger_service=self.logger_service,
            unit_of_work=self.unit_of_work
        )

        master_plot_update_handler = MasterPlotUpdateCommandHandler(
            logger_service=self.logger_service,
            unit_of_work=self.unit_of_work
        )

        # コマンドハンドラー辞書作成
        return {
            GeneratePlotCommand: plot_generation_handler.handle,
            ValidatePlotCommand: plot_validation_handler.handle,
            SavePlotCommand: plot_save_handler.handle,
            UpdateMasterPlotCommand: master_plot_update_handler.handle
        }

    def _create_event_handlers(self) -> dict[type, list]:
        """イベントハンドラー作成

        Returns:
            Dict[Type, list]: イベントハンドラー辞書
        """
        # イベントハンドラー統合クラス使用
        event_handler_aggregate = PlotEventHandlerAggregate(
            logger_service=self.logger_service,
            config_service=self.config_service
        )

        return event_handler_aggregate.get_event_handlers()

    def get_message_bus(self, async_mode: bool = False) -> MessageBus:
        """Message Bus取得（遅延初期化）

        Args:
            async_mode: 非同期モード

        Returns:
            MessageBus: Message Busインスタンス
        """
        if async_mode:
            if self._async_message_bus is None:
                return self.initialize_message_bus(async_mode=True)
            return self._async_message_bus
        if self._message_bus is None:
            return self.initialize_message_bus(async_mode=False)
        return self._message_bus

    def create_mcp_integration_bus(self) -> MessageBus:
        """MCPサーバー統合用Message Bus作成

        Returns:
            MessageBus: MCP統合用Message Busインスタンス
        """
        self.logger_service.info("MCP統合Message Bus作成開始")

        # 基本ハンドラー取得
        command_handlers = self._create_command_handlers()
        event_handlers = self._create_event_handlers()

        # MCP統合Message Bus作成
        outbox_repo, idem_store = self._ensure_support_components()
        mcp_bus = create_mcp_message_bus(
            uow=self.unit_of_work,
            event_handlers=event_handlers,
            command_handlers=command_handlers,
            async_mode=True,  # MCPは非同期推奨
            outbox_repository=outbox_repo,
            idempotency_store=idem_store,
        )

        self.logger_service.info("MCP統合Message Bus作成完了")
        return mcp_bus

    def get_performance_metrics(self) -> dict[str, Any]:
        """Message Busパフォーマンスメトリクス取得

        Returns:
            Dict[str, Any]: パフォーマンスメトリクス
        """
        metrics = {}

        if self._message_bus:
            metrics["sync_bus"] = self._message_bus.get_metrics()

        if self._async_message_bus:
            metrics["async_bus"] = self._async_message_bus.get_metrics()

        return metrics

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_support_components(self) -> tuple[FileOutboxRepository, FileIdempotencyStore]:
        """Lazy-create repositories backing outbox and idempotency features."""

        if self._outbox_repository and self._idempotency_store:
            return self._outbox_repository, self._idempotency_store

        project_root = self._resolve_project_root()
        if project_root is None:
            base_dir = Path.cwd() / "temp" / "outbox"
        else:
            base_dir = project_root / "temp" / "outbox"
        base_dir.mkdir(parents=True, exist_ok=True)

        self._outbox_repository = FileOutboxRepository(base_dir)
        self._idempotency_store = FileIdempotencyStore(base_dir / "idempotency.json")
        return self._outbox_repository, self._idempotency_store

    def _resolve_project_root(self) -> Path | None:
        """PathServiceから利用可能なプロジェクトルートを推定"""

        candidates: list[Any] = [getattr(self.path_service, "project_root", None)]

        if hasattr(self.path_service, "get_project_root"):
            try:
                candidates.append(self.path_service.get_project_root())
            except Exception:
                candidates.append(None)

        env_project_root = os.environ.get("PROJECT_ROOT")
        if env_project_root:
            candidates.append(env_project_root)

        for candidate in candidates:
            coerced = self._coerce_to_path(candidate)
            if coerced is not None:
                return coerced
        return None

    @staticmethod
    def _coerce_to_path(candidate: Any) -> Path | None:
        """様々な型の入力をPathへ変換（非対応型はNone）"""

        if isinstance(candidate, Path):
            return candidate
        if isinstance(candidate, str):
            try:
                return Path(candidate)
            except Exception:
                return None
        return None


class LegacyUseCaseAdapterService:
    """既存ユースケース互換アダプター

    既存のユースケースインターフェースを維持しながら
    Message Bus経由での処理に変換するアダプター
    """

    def __init__(self, message_bus_integration: MessageBusIntegrationService) -> None:
        """アダプター初期化

        Args:
            message_bus_integration: Message Bus統合サービス
        """
        self.integration_service = message_bus_integration
        self.logger_service = message_bus_integration.logger_service

    def execute_plot_generation(
        self,
        project_root: str,
        episode_number: int | None = None,
        **kwargs
    ) -> Any:
        """プロット生成実行（レガシー互換インターフェース）

        Args:
            project_root: プロジェクトルートパス
            episode_number: エピソード番号
            **kwargs: 追加パラメータ

        Returns:
            Any: プロット生成結果
        """
        self.logger_service.info(f"レガシープロット生成実行: episode={episode_number}")

        # Message Bus経由でコマンド実行
        command = GeneratePlotCommand(
            project_root=project_root,
            episode_number=episode_number,
            chapter_title=kwargs.get("chapter_title"),
            target_length=kwargs.get("target_length"),
            genre=kwargs.get("genre"),
            use_ai_enhancement=kwargs.get("use_ai_enhancement", True),
            quality_check=kwargs.get("quality_check", True),
            auto_save=kwargs.get("auto_save", True)
        )

        message_bus = self.integration_service.get_message_bus(async_mode=False)
        return message_bus.handle(command)

    async def execute_plot_generation_async(
        self,
        project_root: str,
        episode_number: int | None = None,
        **kwargs
    ) -> Any:
        """非同期プロット生成実行（レガシー互換インターフェース）

        Args:
            project_root: プロジェクトルートパス
            episode_number: エピソード番号
            **kwargs: 追加パラメータ

        Returns:
            Any: プロット生成結果
        """
        command = GeneratePlotCommand(
            project_root=project_root,
            episode_number=episode_number,
            chapter_title=kwargs.get("chapter_title"),
            target_length=kwargs.get("target_length"),
            genre=kwargs.get("genre"),
            use_ai_enhancement=kwargs.get("use_ai_enhancement", True),
            quality_check=kwargs.get("quality_check", True),
            auto_save=kwargs.get("auto_save", True)
        )

        async_message_bus = self.integration_service.get_message_bus(async_mode=True)
        return await async_message_bus.handle_async(command)

    def validate_plot_quality(
        self,
        plot_content: str,
        validation_criteria: dict[str, Any],
        project_root: str
    ) -> dict[str, Any]:
        """プロット品質チェック実行（レガシー互換）

        Args:
            plot_content: プロット内容
            validation_criteria: 品質基準
            project_root: プロジェクトルート

        Returns:
            Dict[str, Any]: 品質チェック結果
        """
        command = ValidatePlotCommand(
            plot_content=plot_content,
            validation_criteria=validation_criteria,
            project_root=project_root
        )

        message_bus = self.integration_service.get_message_bus(async_mode=False)
        return message_bus.handle(command)


# Bootstrapファクトリー関数
def create_message_bus_integration(
    logger_service: "ILoggerService",
    unit_of_work: AbstractUnitOfWork,
    config_service: "IConfigurationService",
    path_service: "IPathService"
) -> MessageBusIntegrationService:
    """Message Bus統合サービス作成ファクトリー

    Args:
        logger_service: ロガーサービス
        unit_of_work: Unit of Work実装
        config_service: 設定サービス
        path_service: パスサービス

    Returns:
        MessageBusIntegrationService: 統合サービスインスタンス
    """
    return MessageBusIntegrationService(
        logger_service=logger_service,
        unit_of_work=unit_of_work,
        config_service=config_service,
        path_service=path_service
    )


def create_legacy_adapter(
    integration_service: MessageBusIntegrationService
) -> LegacyUseCaseAdapterService:
    """レガシーアダプター作成ファクトリー

    Args:
        integration_service: Message Bus統合サービス

    Returns:
        LegacyUseCaseAdapterService: レガシーアダプターインスタンス
    """
    return LegacyUseCaseAdapterService(integration_service)
