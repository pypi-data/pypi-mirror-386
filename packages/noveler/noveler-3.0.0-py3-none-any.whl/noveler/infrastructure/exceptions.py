"""Custom exceptions for the infrastructure layer."""


class InfrastructureError(Exception):
    """Base exception for infrastructure-related failures."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class ConfigurationError(InfrastructureError):
    """Raised when configuration loading fails."""


class FileSystemError(InfrastructureError):
    """Raised when file system operations fail."""


class YAMLParseError(InfrastructureError):
    """Raised when YAML parsing fails."""


class GitOperationError(InfrastructureError):
    """Raised when Git operations fail."""


class ExternalAPIError(InfrastructureError):
    """Raised when external API calls fail."""


class AdapterError(InfrastructureError):
    """Raised when adapter operations fail."""


# 互換性のためのエイリアス
YAMLParseException = YAMLParseError
FileSystemException = FileSystemError
