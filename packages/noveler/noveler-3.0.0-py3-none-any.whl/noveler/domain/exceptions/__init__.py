"""ドメイン例外パッケージ."""

from noveler.domain.exceptions.base import (
    BusinessRuleViolationError,
    ConfigurationError,
    DomainException,
    DomainValidationError,
    EpisodeCompletionError,
    EpisodeNotFoundError,
    InsufficientDataError,
    InvalidOperationError,
    InvalidStatusError,
    InvalidVersionError,
    NoEpisodesFoundError,
    PathResolutionError,
    PlotNotFoundError,
    ProjectConfigNotFoundError,
    ProjectNotFoundError,
    QualityCheckError,
    QualityRecordError,
    QualityRecordNotFoundError,
    RecordTransactionError,
    RepositoryError,
    StateTransitionError,
    ValidationError,
)
from noveler.domain.exceptions.viewpoint_exceptions import (
    ViewpointDataInvalidError,
    ViewpointError,
    ViewpointFileNotFoundError,
    ViewpointRepositoryError,
    ViewpointYAMLParseError,
)
from noveler.domain.exceptions.chapter_plot_exceptions import ChapterPlotNotFoundError


class MissingProjectRootError(PathResolutionError):
    """Project root を特定できない場合の例外."""

    def __init__(self, hint: str | None = None) -> None:
        message = "Project root could not be determined"
        context: dict[str, str] | None = None
        if hint:
            message = f"{message}: {hint}"
            context = {"hint": hint}
        super().__init__(message, context)


class MissingConfigurationError(ConfigurationError):
    """必須設定が不足している場合の例外."""

    def __init__(self, config_name: str, message: str | None = None) -> None:
        detail_msg = message or f"Required configuration '{config_name}' is missing"
        super().__init__(detail_msg)
        self.config_name = config_name


class RepositoryDataError(RepositoryError):
    """リポジトリ内のデータ異常を表す例外."""

    def __init__(self, repository: str, message: str) -> None:
        super().__init__(f"[{repository}] {message}")
        self.repository = repository


class RepositoryFallbackError(RepositoryError):
    """リポジトリのフォールバック処理に失敗した場合の例外."""

    def __init__(self, repository: str, attempted_fallback: str, message: str | None = None) -> None:
        detail_msg = message or "Repository fallback resolution failed"
        super().__init__(f"[{repository}] {detail_msg}")
        self.repository = repository
        self.attempted_fallback = attempted_fallback

__all__ = [
    "BusinessRuleViolationError",
    "ConfigurationError",
    # Base exceptions
    "DomainException",
    "DomainValidationError",
    "PathResolutionError",
    "MissingProjectRootError",
    "EpisodeCompletionError",
    "EpisodeNotFoundError",
    "InsufficientDataError",
    "InvalidOperationError",
    "InvalidStatusError",
    "InvalidVersionError",
    "NoEpisodesFoundError",
    "PlotNotFoundError",
    "ProjectConfigNotFoundError",
    "ProjectNotFoundError",
    "QualityCheckError",
    "QualityRecordError",
    "QualityRecordNotFoundError",
    "RecordTransactionError",
    "RepositoryError",
    "RepositoryDataError",
    "RepositoryFallbackError",
    "StateTransitionError",
    "ValidationError",
    "MissingConfigurationError",
    "ViewpointDataInvalidError",
    # Viewpoint exceptions
    "ViewpointError",
    "ViewpointFileNotFoundError",
    "ViewpointRepositoryError",
    "ViewpointYAMLParseError",
]
