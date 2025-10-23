"""エラー出力フォーマット

SPEC-CLAUDE-001に基づくエラー情報の出力形式を定義する値オブジェクト
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ExportFormatType(Enum):
    """出力フォーマット種別"""

    JSON = "json"
    MARKDOWN = "markdown"
    PLAIN = "plain"


@dataclass(frozen=True)
class ErrorExportFormat:
    """エラー出力フォーマット

    Claude Code向けエラー情報の出力形式を定義する値オブジェクト
    """

    format_type: ExportFormatType
    structure_version: str
    include_suggestions: bool = True
    max_errors_per_file: int = 10
    priority_filter: Literal["all", "high", "medium", "low"] = "all"

    def __post_init__(self) -> None:
        """値の検証"""
        if not isinstance(self.format_type, ExportFormatType):
            msg = "format_typeはExportFormatTypeである必要があります"
            raise TypeError(msg)

        if not self.structure_version:
            msg = "structure_versionは空にできません"
            raise ValueError(msg)

        if not isinstance(self.structure_version, str):
            msg = "structure_versionは文字列である必要があります"
            raise TypeError(msg)

        if self.max_errors_per_file <= 0:
            msg = "max_errors_per_fileは正の整数である必要があります"
            raise ValueError(msg)

        if self.max_errors_per_file > 100:
            msg = "max_errors_per_fileは100以下である必要があります"
            raise ValueError(msg)

        valid_priorities = {"all", "high", "medium", "low"}
        if self.priority_filter not in valid_priorities:
            msg = f"priority_filterは{valid_priorities}のいずれかである必要があります"
            raise ValueError(msg)

    @classmethod
    def json_format(cls, version: str = "1.0") -> "ErrorExportFormat":
        """JSON形式フォーマット作成

        Args:
            version: 構造バージョン

        Returns:
            JSON形式のErrorExportFormat
        """
        return cls(
            format_type=ExportFormatType.JSON,
            structure_version=version,
            include_suggestions=True,
            max_errors_per_file=20,
        )

    @classmethod
    def markdown_format(cls, version: str = "1.0") -> "ErrorExportFormat":
        """Markdown形式フォーマット作成

        Args:
            version: 構造バージョン

        Returns:
            Markdown形式のErrorExportFormat
        """
        return cls(
            format_type=ExportFormatType.MARKDOWN,
            structure_version=version,
            include_suggestions=True,
            max_errors_per_file=10,
        )

    @classmethod
    def plain_format(cls, version: str = "1.0") -> "ErrorExportFormat":
        """プレーンテキスト形式フォーマット作成

        Args:
            version: 構造バージョン

        Returns:
            プレーンテキスト形式のErrorExportFormat
        """
        return cls(
            format_type=ExportFormatType.PLAIN,
            structure_version=version,
            include_suggestions=False,
            max_errors_per_file=5,
        )

    def get_file_extension(self) -> str:
        """ファイル拡張子取得

        Returns:
            フォーマットに対応するファイル拡張子
        """
        extensions = {ExportFormatType.JSON: ".json", ExportFormatType.MARKDOWN: ".md", ExportFormatType.PLAIN: ".txt"}
        return extensions[self.format_type]

    def get_mime_type(self) -> str:
        """MIMEタイプ取得

        Returns:
            フォーマットに対応するMIMEタイプ
        """
        mime_types = {
            ExportFormatType.JSON: "application/json",
            ExportFormatType.MARKDOWN: "text/markdown",
            ExportFormatType.PLAIN: "text/plain",
        }
        return mime_types[self.format_type]

    def is_structured_format(self) -> bool:
        """構造化フォーマット判定

        Returns:
            構造化フォーマットかどうか
        """
        return self.format_type in {ExportFormatType.JSON}

    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.format_type.value} v{self.structure_version}"
