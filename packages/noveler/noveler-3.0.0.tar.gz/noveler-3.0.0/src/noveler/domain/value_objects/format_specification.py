"""フォーマット仕様値オブジェクト."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from noveler.domain.exceptions import ValidationError


class FormatType(Enum):
    """フォーマットタイプ."""

    MARKDOWN = "markdown"
    HTML = "html"
    PLAIN_TEXT = "plain_text"
    YAML = "yaml"
    JSON = "json"


@dataclass(frozen=True)
class FormatSpecification:
    """フォーマット仕様値オブジェクト."""

    format_id: str
    name: str
    format_type: FormatType
    encoding: str = "utf-8"
    line_ending: str = "\n"
    indent_size: int = 2
    use_tabs: bool = False
    max_line_length: int | None = None
    properties: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """値オブジェクトの不変条件を検証."""
        if self.properties is None:
            object.__setattr__(self, "properties", {})

        self._validate_format_id()
        self._validate_name()
        self._validate_encoding()
        self._validate_indent_size()

    def _validate_format_id(self) -> None:
        """フォーマットIDの妥当性検証."""
        if not self.format_id or not self.format_id.strip():
            msg = "format_id"
            raise ValidationError(msg, "フォーマットIDは必須です")

    def _validate_name(self) -> None:
        """名前の妥当性検証."""
        if not self.name or not self.name.strip():
            msg = "name"
            raise ValidationError(msg, "フォーマット名は必須です")

    def _validate_encoding(self) -> None:
        """エンコーディングの妥当性検証."""
        valid_encodings = ["utf-8", "utf-16", "shift_jis", "euc-jp", "iso-2022-jp"]
        if self.encoding not in valid_encodings:
            msg = "encoding"
            raise ValidationError(msg, f"サポートされていないエンコーディング: {self.encoding}")

    def _validate_indent_size(self) -> None:
        """インデントサイズの妥当性検証."""
        if self.indent_size < 0:
            msg = "indent_size"
            raise ValidationError(msg, "インデントサイズは0以上である必要があります")

    def get_indent_string(self) -> str:
        """インデント文字列を取得."""
        if self.use_tabs:
            return "\t"
        return " " * self.indent_size

    def is_text_format(self) -> bool:
        """テキストフォーマットかどうか判定."""
        return self.format_type in [FormatType.MARKDOWN, FormatType.PLAIN_TEXT, FormatType.YAML]

    def get_file_extension(self) -> str:
        """対応するファイル拡張子を取得."""
        extensions = {
            FormatType.MARKDOWN: ".md",
            FormatType.HTML: ".html",
            FormatType.PLAIN_TEXT: ".txt",
            FormatType.YAML: ".yaml",
            FormatType.JSON: ".json",
        }
        return extensions.get(self.format_type, ".txt")

    @classmethod
    def create_yaml_spec(cls) -> "FormatSpecification":
        """YAMLフォーマット仕様を作成"""
        return cls(
            format_id="yaml_standard",
            name="YAML標準フォーマット",
            format_type=FormatType.YAML,
            encoding="utf-8",
            line_ending="\n",
            indent_size=2,
            use_tabs=False,
            properties={
                "allow_unicode": True,
                "default_flow_style": False,
                "sort_keys": False,
            },
        )

    @classmethod
    def create_markdown_spec(cls) -> "FormatSpecification":
        """Markdownフォーマット仕様を作成"""
        return cls(
            format_id="markdown_standard",
            name="Markdown標準フォーマット",
            format_type=FormatType.MARKDOWN,
            encoding="utf-8",
            line_ending="\n",
            indent_size=2,
            use_tabs=False,
            max_line_length=80,
            properties={
                "heading_style": "atx",
                "bullet_style": "-",
                "emphasis_style": "*",
            },
        )


@dataclass(frozen=True)
class ValidationRule:
    """検証ルール値オブジェクト."""

    rule_id: str
    name: str
    description: str
    enabled: bool = True

    def __post_init__(self) -> None:
        """値オブジェクトの不変条件を検証."""
        self._validate_rule_id()
        self._validate_name()

    def _validate_rule_id(self) -> None:
        """ルールIDの妥当性検証."""
        if not self.rule_id or not self.rule_id.strip():
            msg = "rule_id"
            raise ValidationError(msg, "ルールIDは必須です")

    def _validate_name(self) -> None:
        """名前の妥当性検証."""
        if not self.name or not self.name.strip():
            msg = "name"
            raise ValidationError(msg, "ルール名は必須です")

    def is_active(self) -> bool:
        """ルールが有効かどうか."""
        return self.enabled
