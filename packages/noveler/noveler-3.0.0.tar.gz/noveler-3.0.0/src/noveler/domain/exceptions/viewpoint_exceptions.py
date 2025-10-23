"""視点管理システムの例外クラス定義."""


class ViewpointError(Exception):
    """視点管理システムの基底例外クラス."""

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} [{detail_str}]"
        return self.message


class ViewpointFileNotFoundError(ViewpointError):
    """視点管理ファイルが見つからない場合の例外."""

    def __init__(self, file_path: str, project_name: str | None = None) -> None:
        message = f"視点管理ファイルが見つかりません: {file_path}"
        details: dict[str, object] = {"file_path": file_path}
        if project_name:
            details["project_name"] = project_name
            message = f"プロジェクト '{project_name}' の{message}"
        super().__init__(message, details)


class ViewpointYAMLParseError(ViewpointError):
    """YAML構文エラーが発生した場合の例外."""

    def __init__(
        self,
        file_path: str,
        line_number: int | None = None,
        column_number: int | None = None,
        original_error: str | None = None,
    ) -> None:
        message = f"YAMLファイルの解析に失敗しました: {file_path}"
        details: dict[str, object] = {"file_path": file_path}

        if line_number is not None:
            details["line"] = line_number
            message += f" (行: {line_number}"
            if column_number is not None:
                details["column"] = column_number
                message += f", 列: {column_number}"
            message += ")"

        if original_error:
            details["original_error"] = original_error
            message += f"\n詳細: {original_error}"

        super().__init__(message, details)


class ViewpointDataInvalidError(ViewpointError):
    """視点管理データが不正な場合の例外."""

    def __init__(
        self, field_name: str, expected_type: str, actual_value: object | None = None, file_path: str | None = None
    ) -> None:
        message = f"視点管理データが不正です: フィールド '{field_name}' は {expected_type} 型である必要があります"
        details: dict[str, object] = {
            "field_name": field_name,
            "expected_type": expected_type,
        }

        if actual_value is not None:
            details["actual_type"] = type(actual_value).__name__
            details["actual_value"] = str(actual_value)[:100]  # 長い値は切り詰め

        if file_path:
            details["file_path"] = file_path
            message += f" ({file_path})"

        super().__init__(message, details)


class ViewpointRepositoryError(ViewpointError):
    """リポジトリ操作中のエラー."""

    def __init__(self, operation: str, reason: str, **kwargs: object) -> None:
        message = f"視点管理リポジトリ操作 '{operation}' に失敗しました: {reason}"
        details: dict[str, object] = {"operation": operation, "reason": reason}
        details.update(kwargs)
        super().__init__(message, details)


class ViewpointConfigurationError(ViewpointError):
    """視点設定の設定エラー."""

    def __init__(
        self,
        config_key: str,
        config_value: object | None = None,
        valid_options: list[str] | None = None,
        file_path: str | None = None,
    ) -> None:
        message = f"視点設定が不正です: '{config_key}'"
        details: dict[str, object] = {"config_key": config_key}

        if config_value is not None:
            details["config_value"] = str(config_value)
            message += f" = '{config_value}'"

        if valid_options:
            details["valid_options"] = valid_options
            message += f" (有効な値: {', '.join(map(str, valid_options))})"

        if file_path:
            details["file_path"] = file_path
            message += f" (ファイル: {file_path})"

        super().__init__(message, details)


class ViewpointAutoDetectionError(ViewpointError):
    """視点自動検出の失敗."""

    def __init__(
        self, text_excerpt: str | None = None, confidence: float | None = None, candidates: list[str] | None = None
    ) -> None:
        message = "視点の自動検出に失敗しました"
        details: dict[str, object] = {}

        if text_excerpt:
            details["text_excerpt"] = text_excerpt[:200]  # 最初の200文字
            message += f": テキスト抜粋 '{text_excerpt[:50]}...'"

        if confidence is not None:
            details["confidence"] = str(confidence)
            message += f" (信頼度: {confidence})"

        if candidates:
            details["candidates"] = str(candidates)
            message += f" (候補: {', '.join(candidates)})"

        super().__init__(message, details)
