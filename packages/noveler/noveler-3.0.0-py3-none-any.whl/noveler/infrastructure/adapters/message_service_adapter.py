"""Legacy-compatible adapter that surfaces message service helpers."""

from noveler.application.services.message_service import MessageService, MessageType


class MessageServiceAdapter:
    """Bridge the application message service for legacy callers."""

    def __init__(self) -> None:
        # NullLogger でMessageService を初期化
        class NullLogger:
            def log(self, *args, **kwargs) -> None: pass
            def info(self, *args, **kwargs) -> None: pass
            def error(self, *args, **kwargs) -> None: pass
            def debug(self, *args, **kwargs) -> None: pass

        self.message_service = MessageService(NullLogger())

    def make_friendly(self, message: str, error_type: str) -> dict[str, str | list[str]]:
        """Return a user-friendly representation of the provided message.

        Args:
            message: Raw message text received from the caller.
            error_type: Message type label such as ``"error"`` or ``"warning"``.

        Returns:
            dict[str, str | list[str]]: Legacy formatted friendly message payload.
        """
        # error_typeをMessageTypeに変換
        type_mapping = {
            "error": MessageType.ERROR,
            "warning": MessageType.WARNING,
            "success": MessageType.SUCCESS,
            "info": MessageType.INFO,
        }

        msg_type = type_mapping.get(error_type, MessageType.ERROR)
        user_message = self.message_service.create_user_message(message, msg_type)

        # レガシー形式の辞書を返す
        result = {
            "original": user_message.original,
            "friendly": user_message.friendly,
            "solutions": user_message.solutions,
            "type": error_type,
        }

        if user_message.note:
            result["note"] = user_message.note

        return result

    def format_error_display(self, error_info: dict[str, str | list[str]]) -> str:
        """Format a friendly error payload for terminal output.

        Args:
            error_info: Dictionary produced by ``make_friendly``.

        Returns:
            str: Rendered multi-line error message.
        """
        lines = []
        lines.append("")  # 空行
        lines.append("=" * 60)

        # メインメッセージ
        lines.append(error_info["friendly"])
        lines.append("")

        # 注記がある場合
        if "note" in error_info:
            lines.append(f"📌 {error_info['note']}")
            lines.append("")

        # 解決方法
        if error_info["solutions"]:
            lines.append("💡 解決方法:")
            for solution in error_info["solutions"]:
                if solution.startswith("  "):
                    lines.append(solution)  # インデント済み
                else:
                    lines.append(f"  {solution}")
            lines.append("")

        # 元のエラーメッセージ(参考用)
        if error_info["type"] == "error":
            lines.append("🔍 技術的な詳細:")
            lines.append(f"  {error_info['original']}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("")

        return "\n".join(lines)

    def enhance_success_message(self, message: str) -> str:
        """Enhance a success message for user presentation."""
        return self.message_service.enhance_success_message(message)

    def check_common_issues(self) -> list[str]:
        """Return proactive advice for common issues."""
        return self.message_service.check_common_issues()


# グローバルインスタンス(レガシー互換性)
friendly_msg = MessageServiceAdapter()


def show_friendly_error(error: Exception, context: str) -> None:
    """Display an error using the message service fallbacks.

    Args:
        error: Exception instance to report.
        context: Human readable description of the failing operation.
    """
    try:
        from noveler.infrastructure.di.repository_factory import RepositoryFactory
        repository_factory = RepositoryFactory()
    except Exception:
        print(f"ERROR: {context}: {error}")
        return
    logger_service = repository_factory.get_logger_service()
    message_service = MessageService(logger_service)
    message_service.show_error(error, context)


def show_friendly_warning(message: str) -> None:
    """Display a warning using the message service fallbacks.

    Args:
        message: Warning text to present.
    """
    try:
        from noveler.infrastructure.di.repository_factory import RepositoryFactory
        repository_factory = RepositoryFactory()
    except Exception:
        print(f"WARNING: {message}")
        return
    logger_service = repository_factory.get_logger_service()
    message_service = MessageService(logger_service)
    message_service.show_warning(message)


def show_friendly_success(message: str) -> None:
    """Display a success message using the message service fallbacks.

    Args:
        message: Success text to present.
    """
    try:
        from noveler.infrastructure.di.repository_factory import RepositoryFactory
        repository_factory = RepositoryFactory()
    except Exception:
        print(f"SUCCESS: {message}")
        return
    logger_service = repository_factory.get_logger_service()
    message_service = MessageService(logger_service)
    message_service.show_success(message)


def check_common_issues() -> list:
    """Return proactive advice for common issues using a fresh service instance.

    Returns:
        list: Advice strings produced by the message service.
    """
    message_service = MessageService()
    return message_service.check_common_issues()


# エクスポートする関数
__all__ = [
    "MessageServiceAdapter",
    "check_common_issues",
    "friendly_msg",
    "show_friendly_error",
    "show_friendly_success",
    "show_friendly_warning",
]
