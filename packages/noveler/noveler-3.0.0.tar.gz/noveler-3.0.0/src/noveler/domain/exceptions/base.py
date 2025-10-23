"""ドメイン層の基本例外クラス."""

from typing import Any


class DomainError(Exception):
    """ドメイン層の基本例外クラス."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """初期化.

        Args:
            message: エラーメッセージ
            details: 詳細情報
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(DomainError):
    """バリデーションエラー."""

    def __init__(
        self,
        field: str | None = None,
        message: str | None = None,
        value: object = None,
    ) -> None:
        """初期化.

        Args:
            field: エラーが発生したフィールド名。省略時はメッセージのみを扱う。
            message: エラーメッセージ
            value: エラーとなった値
        """
        if message is None and field is not None:
            # 旧実装との後方互換: ValidationError("message")
            message = field
            field = None

        message = message or ""
        details = {"field": field, "value": value}
        if field:
            base_message = f"Validation error in {field}: {message}"
        else:
            base_message = message

        super().__init__(base_message, details)
        self.field = field
        self.message = message
        self.value = value


class DomainFileNotFoundError(DomainError):
    """ファイルが見つからないエラー."""

    def __init__(self, file_path: str, message: str | None = None) -> None:
        """初期化.

        Args:
            file_path: 見つからなかったファイルパス
            message: 追加のエラーメッセージ
        """
        msg = message or f"File not found: {file_path}"
        super().__init__(msg, {"file_path": file_path})
        self.file_path = file_path


class NoEpisodesFoundError(DomainError):
    """エピソードが見つからないエラー."""

    def __init__(self, project_name: str, message: str | None = None) -> None:
        """初期化.

        Args:
            project_name: プロジェクト名
            message: 追加のエラーメッセージ
        """
        msg = message or f"No episodes found in project: {project_name}"
        super().__init__(msg, {"project_name": project_name})
        self.project_name = project_name


class EpisodeNotFoundError(DomainError):
    """特定のエピソードが見つからないエラー."""

    def __init__(self, episode_number: int, project_name: str | None = None) -> None:
        """初期化.

        Args:
            episode_number: エピソード番号
            project_name: プロジェクト名
        """
        msg = f"Episode {episode_number} not found"
        if project_name:
            msg += f" in project {project_name}"
        super().__init__(msg, {"episode_number": episode_number, "project_name": project_name})
        self.episode_number = episode_number


class ProjectNotFoundError(DomainError):
    """プロジェクトが見つからないエラー."""

    def __init__(self, project_name: str) -> None:
        """初期化.

        Args:
            project_name: プロジェクト名
        """
        super().__init__(f"Project not found: {project_name}", {"project_name": project_name})
        self.project_name = project_name


class InvalidOperationError(DomainError):
    """無効な操作エラー."""

    def __init__(self, operation: str, reason: str) -> None:
        """初期化.

        Args:
            operation: 操作名
            reason: 無効な理由
        """
        super().__init__(f"Invalid operation '{operation}': {reason}", {"operation": operation})
        self.operation = operation
        self.reason = reason


class StateTransitionError(DomainError):
    """状態遷移エラー."""

    def __init__(self, current_state: str, target_state: str, reason: str | None = None) -> None:
        """初期化.

        Args:
            current_state: 現在の状態
            target_state: 遷移先の状態
            reason: エラーの理由
        """
        msg = f"Cannot transition from {current_state} to {target_state}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, {"current_state": current_state, "target_state": target_state})
        self.current_state = current_state
        self.target_state = target_state
        self.reason = reason


class ConfigurationError(DomainError):
    """設定エラー."""

    def __init__(self, config_name: str, message: str) -> None:
        """初期化.

        Args:
            config_name: 設定項目名
            message: エラーメッセージ
        """
        super().__init__(f"Configuration error in {config_name}: {message}", {"config_name": config_name})
        self.config_name = config_name


class QualityCheckError(DomainError):
    """品質チェックエラー."""

    def __init__(self, check_type: str, message: str, details: dict[str, Any] | None = None) -> None:
        """初期化.

        Args:
            check_type: チェックタイプ
            message: エラーメッセージ
            details: 詳細情報
        """
        super().__init__(
            f"Quality check error ({check_type}): {message}", {"check_type": check_type, **(details or {})}
        )

        self.check_type = check_type


class RepositoryError(DomainError):
    """リポジトリエラー."""

    def __init__(self, repository_name: str, operation: str, message: str = "") -> None:
        """初期化.

        Args:
            repository_name: リポジトリ名
            operation: 操作名
            message: エラーメッセージ
        """
        super().__init__(
            f"Repository error in {repository_name}.{operation}: {message}",
            {"repository_name": repository_name, "operation": operation},
        )
        self.repository_name = repository_name
        self.operation = operation


class EpisodeCompletionError(DomainError):
    """エピソード完了エラー."""

    def __init__(self, episode_number: int, message: str) -> None:
        """初期化.

        Args:
            episode_number: エピソード番号
            message: エラーメッセージ
        """
        super().__init__(
            f"Episode completion error (Episode {episode_number}): {message}", {"episode_number": episode_number}
        )

        self.episode_number = episode_number


class InvalidStatusError(DomainError):
    """無効なステータスエラー."""

    def __init__(self, status: str, message: str | None = None) -> None:
        """初期化.

        Args:
            status: 無効なステータス
            message: 追加のエラーメッセージ
        """
        msg = message or f"Invalid status: {status}"
        super().__init__(msg, {"status": status})
        self.status = status


class QualityRecordError(DomainError):
    """品質記録エラー."""

    def __init__(self, record_id: str | None, message: str) -> None:
        """初期化.

        Args:
            record_id: 記録ID
            message: エラーメッセージ
        """
        super().__init__(f"Quality record error: {message}", {"record_id": record_id})
        self.record_id = record_id


class ProjectConfigNotFoundError(DomainError):
    """プロジェクト設定が見つからないエラー."""

    def __init__(self, project_name: str, config_file: str | None = None) -> None:
        """初期化.

        Args:
            project_name: プロジェクト名
            config_file: 設定ファイルパス
        """
        msg = f"Project configuration not found for project: {project_name}"
        if config_file:
            msg += f" (Expected config file: {config_file})"
        super().__init__(msg, {"project_name": project_name, "config_file": config_file})
        self.project_name = project_name
        self.config_file = config_file


class BusinessRuleViolationError(DomainError):
    """ビジネスルール違反エラー."""

    def __init__(self, rule_name: str, message: str, context: dict[str, Any] | None = None) -> None:
        """初期化.

        Args:
            rule_name: 違反したルール名
            message: エラーメッセージ
            context: 違反コンテキスト
        """
        super().__init__(
            f"Business rule violation ({rule_name}): {message}", {"rule_name": rule_name, **(context or {})}
        )

        self.rule_name = rule_name
        self.context = context or {}


class InsufficientDataError(DomainError):
    """データ不足エラー."""

    def __init__(self, required_data: str, message: str | None = None) -> None:
        """初期化.

        Args:
            required_data: 不足している必要データ
            message: 追加のエラーメッセージ
        """
        msg = message or f"Insufficient data: {required_data} is required"
        super().__init__(msg, {"required_data": required_data})
        self.required_data = required_data


class QualityRecordNotFoundError(DomainError):
    """品質記録が見つからないエラー."""

    def __init__(self, record_id: str, message: str | None = None) -> None:
        """初期化.

        Args:
            record_id: 記録ID
            message: 追加のエラーメッセージ
        """
        msg = message or f"Quality record not found: {record_id}"
        super().__init__(msg, {"record_id": record_id})
        self.record_id = record_id


class InvalidVersionError(DomainError):
    """無効なバージョンエラー."""

    def __init__(self, version: str, message: str | None = None) -> None:
        """初期化.

        Args:
            version: 無効なバージョン
            message: 追加のエラーメッセージ
        """
        msg = message or f"Invalid version: {version}"
        super().__init__(msg, {"version": version})
        self.version = version


class RecordTransactionError(DomainError):
    """記録トランザクションエラー."""

    def __init__(self, operation: str, message: str, context: dict[str, Any] | None = None) -> None:
        """初期化.

        Args:
            operation: 操作名
            message: エラーメッセージ
            context: エラーコンテキスト
        """
        super().__init__(
            f"Record transaction error ({operation}): {message}", {"operation": operation, **(context or {})}
        )

        self.operation = operation
        self.context = context or {}


class PlotNotFoundError(DomainError):
    """プロットが見つからないエラー."""

    def __init__(self, plot_id: str, message: str | None = None) -> None:
        """初期化.

        Args:
            plot_id: プロットID
            message: 追加のエラーメッセージ
        """
        msg = message or f"Plot not found: {plot_id}"
        super().__init__(msg, {"plot_id": plot_id})
        self.plot_id = plot_id


class DomainValidationError(DomainError):
    """ドメイン検証エラー."""

    def __init__(self, entity_name: str, field_name: str, message: str = "", value: object = None) -> None:
        """初期化.

        Args:
            entity_name: エンティティ名
            field_name: フィールド名
            message: エラーメッセージ
            value: エラーとなった値
        """
        msg = f"Domain validation error in {entity_name}.{field_name}: {message}"
        super().__init__(msg, {"entity_name": entity_name, "field_name": field_name, "value": value})
        self.entity_name = entity_name
        self.field_name = field_name
        self.value = value


    # 互換性のためのエイリアス
DomainException = DomainError


class PathResolutionError(DomainError):
    """パス解決に失敗、またはフォールバックを許可しない状況で発生するエラー."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message, context or {})
