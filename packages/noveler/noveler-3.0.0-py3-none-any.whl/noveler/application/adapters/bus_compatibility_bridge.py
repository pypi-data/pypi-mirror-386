# File: src/noveler/application/adapters/bus_compatibility_bridge.py
# Purpose: Compatibility bridge between TypedBus (legacy) and SimpleBus (new implementation)
# Context: Provides seamless migration path from typed command/event to string-based bus

"""Bus互換層ブリッジ

TypedBus（レガシー）とSimpleBus（新実装）の互換性を提供

参照: TODO.md SPEC-901残件 - 互換層（既存型ベースBus ↔ SimpleBus）のブリッジ方針決定と移行計画
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass

from noveler.application.simple_message_bus import MessageBus as SimpleBus
from noveler.application.message_bus import MessageBus as TypedBus


@dataclass
class BusCompatibilityConfig:
    """互換層の設定"""

    enable_command_translation: bool = True
    enable_event_translation: bool = True
    default_bus_type: str = "simple"  # "simple" or "typed"
    translation_logging: bool = False


class CommandTranslator:
    """コマンド変換器"""

    @staticmethod
    def typed_to_simple(command) -> tuple[str, Dict[str, Any]]:
        """型付きコマンドを文字列名+辞書に変換

        Args:
            command: 型付きコマンドオブジェクト

        Returns:
            tuple[str, Dict[str, Any]]: (command_name, command_data)
        """
        command_name = command.__class__.__name__.lower()

        # Remove "command" suffix if present
        if command_name.endswith("command"):
            command_name = command_name[:-7]

        # Convert command object to dictionary
        if hasattr(command, 'to_dict'):
            command_data = command.to_dict()
        elif hasattr(command, '__dict__'):
            command_data = {k: v for k, v in command.__dict__.items() if not k.startswith('_')}
        else:
            command_data = {"data": str(command)}

        return command_name, command_data

    @staticmethod
    def simple_to_typed(command_name: str, command_data: Dict[str, Any]):
        """文字列名+辞書を型付きコマンドに変換

        Args:
            command_name: コマンド名
            command_data: コマンドデータ

        Returns:
            型付きコマンドオブジェクト（簡易版）
        """
        # Create a simple command object
        class GenericCommand:
            def __init__(self, name: str, **kwargs):
                self.command_name = name
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def to_dict(self):
                return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

        return GenericCommand(command_name, **command_data)


class EventTranslator:
    """イベント変換器"""

    @staticmethod
    def typed_to_simple(event) -> tuple[str, Dict[str, Any]]:
        """型付きイベントを文字列名+辞書に変換

        Args:
            event: 型付きイベントオブジェクト

        Returns:
            tuple[str, Dict[str, Any]]: (event_name, event_payload)
        """
        event_name = event.__class__.__name__.lower()

        # Remove "event" suffix if present
        if event_name.endswith("event"):
            event_name = event_name[:-5]

        # Add namespace if not present
        if "." not in event_name:
            # Try to infer namespace from event name
            if any(x in event_name for x in ["episode", "chapter"]):
                event_name = f"episode.{event_name}"
            elif any(x in event_name for x in ["quality", "check"]):
                event_name = f"quality.{event_name}"
            elif any(x in event_name for x in ["plot", "story"]):
                event_name = f"plot.{event_name}"

        # Convert event object to dictionary
        if hasattr(event, 'to_dict'):
            event_payload = event.to_dict()
        elif hasattr(event, '__dict__'):
            event_payload = {k: v for k, v in event.__dict__.items() if not k.startswith('_')}
        else:
            event_payload = {"data": str(event)}

        return event_name, event_payload

    @staticmethod
    def simple_to_typed(event_name: str, event_payload: Dict[str, Any]):
        """文字列名+辞書を型付きイベントに変換

        Args:
            event_name: イベント名
            event_payload: イベントペイロード

        Returns:
            型付きイベントオブジェクト（簡易版）
        """
        from noveler.application.simple_message_bus import GenericEvent

        # Use existing GenericEvent for simple representation
        return GenericEvent(
            event_id=event_payload.get("event_id", f"{event_name}_{id(event_payload)}"),
            event_name=event_name,
            payload=event_payload
        )


class BusCompatibilityBridge:
    """MessageBus互換層ブリッジ"""

    def __init__(self, simple_bus: SimpleBus, typed_bus: Optional[TypedBus] = None,
                 config: Optional[BusCompatibilityConfig] = None):
        """初期化

        Args:
            simple_bus: SimpleBus instance
            typed_bus: TypedBus instance (optional)
            config: 互換層設定
        """
        self.simple_bus = simple_bus
        self.typed_bus = typed_bus
        self.config = config or BusCompatibilityConfig()
        self.command_translator = CommandTranslator()
        self.event_translator = EventTranslator()

        if self.config.translation_logging:
            self._setup_logging()

    def _setup_logging(self):
        """変換ログの設定"""
        from noveler.presentation.cli.shared_utilities.logger import get_logger
        self.logger = get_logger(__name__)

    async def handle_command_unified(self, command_or_name: Union[str, Any],
                                   data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """統一コマンドハンドリング

        Args:
            command_or_name: コマンドオブジェクトまたは文字列名
            data: コマンドデータ（文字列名の場合）

        Returns:
            コマンド実行結果
        """
        if isinstance(command_or_name, str):
            # String-based command -> use SimpleBus
            return await self.simple_bus.handle_command(command_or_name, data or {})
        else:
            # Typed command -> convert and use SimpleBus (or delegate to TypedBus)
            if self.config.default_bus_type == "simple" or not self.typed_bus:
                command_name, command_data = self.command_translator.typed_to_simple(command_or_name)

                if self.config.translation_logging and hasattr(self, 'logger'):
                    self.logger.info(f"Translating typed command {command_or_name.__class__.__name__} "
                                   f"to simple command '{command_name}'")

                return await self.simple_bus.handle_command(command_name, command_data)
            else:
                # Use TypedBus
                return await self.typed_bus.handle_command(command_or_name)

    async def emit_event_unified(self, event_or_name: Union[str, Any],
                               payload: Optional[Dict[str, Any]] = None) -> None:
        """統一イベント発行

        Args:
            event_or_name: イベントオブジェクトまたは文字列名
            payload: イベントペイロード（文字列名の場合）
        """
        if isinstance(event_or_name, str):
            # String-based event -> use SimpleBus
            await self.simple_bus.emit(event_or_name, payload or {})
        else:
            # Typed event -> convert and use SimpleBus (or delegate to TypedBus)
            if self.config.default_bus_type == "simple" or not self.typed_bus:
                event_name, event_payload = self.event_translator.typed_to_simple(event_or_name)

                if self.config.translation_logging and hasattr(self, 'logger'):
                    self.logger.info(f"Translating typed event {event_or_name.__class__.__name__} "
                                   f"to simple event '{event_name}'")

                await self.simple_bus.emit(event_name, event_payload)
            else:
                # Use TypedBus
                await self.typed_bus.emit_event(event_or_name)

    def register_typed_command_handler(self, command_class, handler):
        """型付きコマンドハンドラーの登録

        Args:
            command_class: コマンドクラス
            handler: ハンドラー関数
        """
        command_name = command_class.__name__.lower()
        if command_name.endswith("command"):
            command_name = command_name[:-7]

        async def wrapper(data: Dict[str, Any], **kwargs):
            # Convert simple command data to typed command
            typed_command = self.command_translator.simple_to_typed(command_name, data)
            return await handler(typed_command, **kwargs)

        self.simple_bus.command_handlers[command_name] = wrapper

    def register_typed_event_handler(self, event_class, handler):
        """型付きイベントハンドラーの登録

        Args:
            event_class: イベントクラス
            handler: ハンドラー関数
        """
        event_name = event_class.__name__.lower()
        if event_name.endswith("event"):
            event_name = event_name[:-5]

        # Add namespace inference
        if "." not in event_name:
            if any(x in event_name for x in ["episode", "chapter"]):
                event_name = f"episode.{event_name}"
            elif any(x in event_name for x in ["quality", "check"]):
                event_name = f"quality.{event_name}"
            elif any(x in event_name for x in ["plot", "story"]):
                event_name = f"plot.{event_name}"

        async def wrapper(event):
            # Convert simple event to typed event
            typed_event = self.event_translator.simple_to_typed(event.event_name, event.payload)
            return await handler(typed_event)

        if event_name not in self.simple_bus.event_handlers:
            self.simple_bus.event_handlers[event_name] = []
        self.simple_bus.event_handlers[event_name].append(wrapper)

    async def flush_outbox(self) -> int:
        """Outboxフラッシュ（SimpleBus経由）"""
        return await self.simple_bus.flush_outbox()

    def get_metrics(self) -> Dict[str, Any]:
        """メトリクス取得（SimpleBus経由）"""
        return self.simple_bus.get_metrics_summary()

    def get_health_status(self) -> Dict[str, Any]:
        """ヘルス状態取得（SimpleBus経由）"""
        return self.simple_bus.get_health_status()

    def migrate_to_simple_bus(self) -> None:
        """SimpleBusへの完全移行

        この操作後はTypedBusは使用されなくなります
        """
        self.config.default_bus_type = "simple"
        self.typed_bus = None

        if self.config.translation_logging and hasattr(self, 'logger'):
            self.logger.info("Migrated to SimpleBus completely. TypedBus disabled.")

    def enable_dual_mode(self, typed_bus: TypedBus) -> None:
        """デュアルモード有効化

        Args:
            typed_bus: TypedBus instance
        """
        self.typed_bus = typed_bus
        self.config.default_bus_type = "simple"  # SimpleBusを優先

        if self.config.translation_logging and hasattr(self, 'logger'):
            self.logger.info("Enabled dual mode. SimpleBus is primary, TypedBus is secondary.")


def create_compatibility_bridge(simple_bus: SimpleBus, typed_bus: Optional[TypedBus] = None,
                              enable_logging: bool = False) -> BusCompatibilityBridge:
    """互換層ブリッジのファクトリー関数

    Args:
        simple_bus: SimpleBus instance
        typed_bus: TypedBus instance (optional)
        enable_logging: 変換ログを有効にするか

    Returns:
        設定済みBusCompatibilityBridge
    """
    config = BusCompatibilityConfig(
        translation_logging=enable_logging,
        default_bus_type="simple"
    )

    return BusCompatibilityBridge(simple_bus, typed_bus, config)


# Convenience functions for common migration patterns

async def migrate_typed_command_to_simple(bridge: BusCompatibilityBridge, command) -> Dict[str, Any]:
    """型付きコマンドをSimpleBus経由で実行

    Args:
        bridge: 互換層ブリッジ
        command: 型付きコマンド

    Returns:
        実行結果
    """
    command_name, command_data = bridge.command_translator.typed_to_simple(command)
    return await bridge.simple_bus.handle_command(command_name, command_data)


async def migrate_typed_event_to_simple(bridge: BusCompatibilityBridge, event) -> None:
    """型付きイベントをSimpleBus経由で発行

    Args:
        bridge: 互換層ブリッジ
        event: 型付きイベント
    """
    event_name, event_payload = bridge.event_translator.typed_to_simple(event)
    await bridge.simple_bus.emit(event_name, event_payload)
