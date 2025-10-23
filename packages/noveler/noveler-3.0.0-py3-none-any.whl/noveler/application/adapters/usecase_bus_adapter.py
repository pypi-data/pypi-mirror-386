# File: src/noveler/application/adapters/usecase_bus_adapter.py
# Purpose: Adapter to integrate existing UseCases with MessageBus pattern
# Context: Bridge between legacy UseCase pattern and new MessageBus DDD architecture

"""UseCase MessageBus統合アダプター

既存のUseCaseパターンをMessageBus経由で実行するためのアダプター

参照: TODO.md SPEC-901残件 - 既存ユースケースへのDI移行
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass

from noveler.application.simple_message_bus import MessageBus
from noveler.application.uow import UnitOfWork

T_Request = TypeVar('T_Request')
T_Response = TypeVar('T_Response')


@dataclass
class UseCaseBusRequest:
    """MessageBus経由でUseCaseを実行するためのリクエスト"""

    usecase_name: str
    request_data: Dict[str, Any]
    project_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


@dataclass
class UseCaseBusResponse:
    """MessageBus経由でUseCaseを実行した結果"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    usecase_name: Optional[str] = None


class UseCaseBusAdapter:
    """UseCase ↔ MessageBus 統合アダプター"""

    def __init__(self, message_bus: MessageBus):
        """Initialize adapter with MessageBus instance.

        Args:
            message_bus: MessageBus instance for command/event handling
        """
        self.message_bus = message_bus
        self._usecase_registry = {}
        self._setup_bus_handlers()

    def register_usecase(self, name: str, usecase_class, **dependencies):
        """Register a UseCase for MessageBus integration.

        Args:
            name: UseCase identifier for command routing
            usecase_class: UseCase class to instantiate
            **dependencies: Dependencies to inject into UseCase constructor
        """
        self._usecase_registry[name] = {
            'class': usecase_class,
            'dependencies': dependencies
        }

    def _setup_bus_handlers(self):
        """Setup MessageBus command handlers for UseCase integration."""
        self.message_bus.command_handlers["execute_usecase"] = self._handle_usecase_command

    async def _handle_usecase_command(self, data: Dict[str, Any], *, uow: UnitOfWork) -> Dict[str, Any]:
        """Handle UseCase execution command through MessageBus.

        Args:
            data: Command data containing UseCase request
            uow: Unit of Work instance

        Returns:
            Dict containing UseCase execution result
        """
        try:
            # Parse request
            usecase_name = data.get("usecase_name")
            request_data = data.get("request_data", {})
            options = data.get("options", {})

            if not usecase_name:
                return {
                    "success": False,
                    "error": "usecase_name is required"
                }

            if usecase_name not in self._usecase_registry:
                return {
                    "success": False,
                    "error": f"Unknown usecase: {usecase_name}"
                }

            # Get UseCase configuration
            usecase_config = self._usecase_registry[usecase_name]
            usecase_class = usecase_config['class']
            dependencies = usecase_config['dependencies'].copy()

            # Inject UnitOfWork and other dependencies
            dependencies['unit_of_work'] = uow

            # Add logger service if available
            if hasattr(self.message_bus, '_logger_service'):
                dependencies['logger_service'] = self.message_bus._logger_service

            # Create and execute UseCase
            usecase_instance = usecase_class(**dependencies)

            # Convert request data to UseCase request object if needed
            request_obj = self._create_usecase_request(usecase_class, request_data)

            # Execute UseCase
            if asyncio.iscoroutinefunction(usecase_instance.execute):
                response = await usecase_instance.execute(request_obj)
            else:
                response = usecase_instance.execute(request_obj)

            # Convert response to dict
            response_data = self._convert_response_to_dict(response)

            # Emit UseCase completion event
            uow.add_event("usecase.executed", {
                "usecase_name": usecase_name,
                "success": response_data.get("success", True),
                "request_data": request_data,
                "response_data": response_data
            })

            return {
                "success": True,
                "usecase_name": usecase_name,
                "response": response_data
            }

        except Exception as e:
            # Emit UseCase failure event
            uow.add_event("usecase.failed", {
                "usecase_name": usecase_name,
                "error": str(e),
                "request_data": request_data
            })

            return {
                "success": False,
                "error": f"UseCase execution failed: {e}",
                "usecase_name": usecase_name
            }

    def _create_usecase_request(self, usecase_class, request_data: Dict[str, Any]):
        """Create UseCase request object from dictionary data.

        Args:
            usecase_class: UseCase class to determine request type
            request_data: Dictionary containing request parameters

        Returns:
            UseCase request object
        """
        # Try to get request class from UseCase type annotations
        if hasattr(usecase_class, '__orig_bases__'):
            for base in usecase_class.__orig_bases__:
                if hasattr(base, '__args__') and len(base.__args__) >= 1:
                    request_class = base.__args__[0]
                    if hasattr(request_class, '__init__'):
                        try:
                            return request_class(**request_data)
                        except Exception:
                            pass

        # Fallback: create simple object with attributes
        class SimpleRequest:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        return SimpleRequest(**request_data)

    def _convert_response_to_dict(self, response) -> Dict[str, Any]:
        """Convert UseCase response to dictionary format.

        Args:
            response: UseCase response object

        Returns:
            Dictionary representation of response
        """
        if isinstance(response, dict):
            return response

        if hasattr(response, '__dict__'):
            return {
                key: value for key, value in response.__dict__.items()
                if not key.startswith('_')
            }

        # Fallback for simple objects
        return {"result": str(response)}

    async def execute_usecase_via_bus(self, usecase_name: str, request_data: Dict[str, Any],
                                    options: Optional[Dict[str, Any]] = None) -> UseCaseBusResponse:
        """Execute UseCase through MessageBus (convenience method).

        Args:
            usecase_name: Name of registered UseCase
            request_data: UseCase request parameters
            options: Optional execution options

        Returns:
            UseCaseBusResponse containing execution result
        """
        command_data = {
            "usecase_name": usecase_name,
            "request_data": request_data,
            "options": options or {}
        }

        result = await self.message_bus.handle_command("execute_usecase", command_data)

        return UseCaseBusResponse(
            success=result.get("success", False),
            data=result.get("response"),
            error_message=result.get("error"),
            usecase_name=usecase_name
        )


class QualityCheckBusAdapter:
    """QualityCheckUseCase専用のMessageBus統合アダプター"""

    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self._setup_quality_check_handlers()

    def _setup_quality_check_handlers(self):
        """品質チェック専用のコマンドハンドラーを設定"""
        self.message_bus.command_handlers["quality_check_via_usecase"] = self._handle_quality_check_command

    async def _handle_quality_check_command(self, data: Dict[str, Any], *, uow: UnitOfWork) -> Dict[str, Any]:
        """品質チェックUseCaseをMessageBus経由で実行"""
        from noveler.application.use_cases.quality_check_use_case import QualityCheckUseCase, QualityCheckRequest
        from noveler.presentation.cli.shared_utilities.console import get_console
        from noveler.presentation.cli.shared_utilities.logger import get_logger

        try:
            # Extract parameters
            episode_id = data.get("episode_id")
            project_id = data.get("project_id", "default")
            check_options = data.get("check_options", {})

            if not episode_id:
                return {
                    "success": False,
                    "error": "episode_id is required"
                }

            # Setup UseCase dependencies
            logger_service = get_logger(__name__)

            # Create UseCase request
            request = QualityCheckRequest(
                episode_id=episode_id,
                project_id=project_id,
                check_options=check_options
            )

            # Initialize UseCase with dependencies from UoW
            quality_usecase = QualityCheckUseCase(
                episode_repository=getattr(uow, 'episode_repo', None),
                quality_check_repository=None,  # Will use default
                logger_service=logger_service,
                unit_of_work=uow
            )

            # Execute UseCase
            response = await quality_usecase.execute(request)

            # Convert response to dict format
            result_data = {
                "success": response.success,
                "check_id": getattr(response, 'check_id', None),
                "episode_id": response.episode_id,
                "total_score": getattr(response, 'total_score', 0.0),
                "is_passed": getattr(response, 'is_passed', False),
                "violations_count": len(getattr(response, 'violations', [])),
                "auto_fix_applied": getattr(response, 'auto_fix_applied', False),
                "error_message": getattr(response, 'error_message', None)
            }

            # Emit quality check event
            uow.add_event("quality.checked_via_usecase", {
                "episode_id": episode_id,
                "check_id": result_data.get("check_id"),
                "score": result_data.get("total_score"),
                "passed": result_data.get("is_passed"),
                "via_usecase": True
            })

            return result_data

        except Exception as e:
            uow.add_event("quality.check_failed", {
                "episode_id": data.get("episode_id"),
                "error": str(e),
                "via_usecase": True
            })

            return {
                "success": False,
                "error": f"QualityCheck UseCase execution failed: {e}"
            }


def create_usecase_bus_adapter(message_bus: MessageBus) -> UseCaseBusAdapter:
    """Factory function to create configured UseCaseBusAdapter.

    Args:
        message_bus: MessageBus instance

    Returns:
        Configured UseCaseBusAdapter
    """
    adapter = UseCaseBusAdapter(message_bus)

    # Register commonly used UseCases
    # (This could be moved to a configuration file)

    return adapter


def create_quality_check_bus_adapter(message_bus: MessageBus) -> QualityCheckBusAdapter:
    """Factory function to create QualityCheckBusAdapter.

    Args:
        message_bus: MessageBus instance

    Returns:
        Configured QualityCheckBusAdapter
    """
    return QualityCheckBusAdapter(message_bus)
