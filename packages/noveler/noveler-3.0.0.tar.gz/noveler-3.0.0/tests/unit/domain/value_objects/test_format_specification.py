"""
FormatSpecification値オブジェクトのユニットテスト

SPEC-WORKFLOW-002: レガシーモジュールTDD+DDD移行
"""

import pytest

from noveler.domain.exceptions import ValidationError
from noveler.domain.value_objects.format_specification import FormatSpecification, FormatType, ValidationRule

pytestmark = pytest.mark.vo_smoke



@pytest.mark.spec("SPEC-WORKFLOW-002")
class TestValidationRule:
    """ValidationRuleのテストクラス"""

    def test_valid_validation_rule_creation(self) -> None:
        """有効な検証ルールの作成をテスト"""
        # Arrange & Act
        rule = ValidationRule(
            rule_id="syntax_check", name="構文チェック", description="YAML構文の妥当性を検証", enabled=True
        )

        # Assert
        assert rule.rule_id == "syntax_check"
        assert rule.name == "構文チェック"
        assert rule.description == "YAML構文の妥当性を検証"
        assert rule.enabled is True
        assert rule.is_active() is True

    def test_empty_rule_id_raises_error(self) -> None:
        """空のrule_idで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError, match="ルールIDは必須です"):
            ValidationRule(rule_id="", name="テスト", description="説明")

    def test_empty_name_raises_error(self) -> None:
        """空のnameで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError, match="ルール名は必須です"):
            ValidationRule(rule_id="test", name="", description="説明")

    def test_disabled_rule_is_not_active(self) -> None:
        """無効化されたルールがアクティブでないことをテスト"""
        # Arrange & Act
        rule = ValidationRule(rule_id="test", name="テスト", description="説明", enabled=False)

        # Assert
        assert rule.enabled is False
        assert rule.is_active() is False


@pytest.mark.spec("SPEC-WORKFLOW-002")
class TestFormatSpecification:
    """FormatSpecification値オブジェクトのテストクラス"""

    def test_valid_format_specification_creation(self) -> None:
        """有効なフォーマット仕様の作成をテスト"""
        # Act
        spec = FormatSpecification(
            format_id="yaml_test",
            name="YAMLテスト仕様",
            format_type=FormatType.YAML,
            encoding="utf-8",
            line_ending="\n",
            indent_size=2,
            use_tabs=False,
        )

        # Assert
        assert spec.format_id == "yaml_test"
        assert spec.name == "YAMLテスト仕様"
        assert spec.format_type == FormatType.YAML
        assert spec.encoding == "utf-8"
        assert spec.line_ending == "\n"
        assert spec.indent_size == 2
        assert spec.use_tabs is False

    def test_empty_format_id_raises_error(self) -> None:
        """空のformat_idで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError, match="フォーマットIDは必須です"):
            FormatSpecification(format_id="", name="テスト", format_type=FormatType.YAML)

    def test_empty_name_raises_error(self) -> None:
        """空のnameで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError, match="フォーマット名は必須です"):
            FormatSpecification(format_id="test", name="", format_type=FormatType.YAML)

    def test_invalid_encoding_raises_error(self) -> None:
        """無効なエンコーディングで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError, match="サポートされていないエンコーディング"):
            FormatSpecification(
                format_id="test", name="テスト", format_type=FormatType.YAML, encoding="invalid-encoding"
            )

    def test_negative_indent_size_raises_error(self) -> None:
        """負のインデントサイズで例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError, match="インデントサイズは0以上である必要があります"):
            FormatSpecification(format_id="test", name="テスト", format_type=FormatType.YAML, indent_size=-1)

    def test_get_indent_string_returns_spaces(self) -> None:
        """スペースのインデント文字列が返されることをテスト"""
        # Arrange
        spec = FormatSpecification(
            format_id="test", name="テスト", format_type=FormatType.YAML, indent_size=4, use_tabs=False
        )

        # Act & Assert
        assert spec.get_indent_string() == "    "

    def test_get_indent_string_returns_tab(self) -> None:
        """タブのインデント文字列が返されることをテスト"""
        # Arrange
        spec = FormatSpecification(format_id="test", name="テスト", format_type=FormatType.YAML, use_tabs=True)

        # Act & Assert
        assert spec.get_indent_string() == "\t"

    def test_is_text_format_returns_true_for_text_formats(self) -> None:
        """テキストフォーマットでTrueが返されることをテスト"""
        # Arrange
        yaml_spec = FormatSpecification(format_id="test1", name="YAML", format_type=FormatType.YAML)

        md_spec = FormatSpecification(format_id="test2", name="Markdown", format_type=FormatType.MARKDOWN)

        txt_spec = FormatSpecification(format_id="test3", name="PlainText", format_type=FormatType.PLAIN_TEXT)

        # Act & Assert
        assert yaml_spec.is_text_format() is True
        assert md_spec.is_text_format() is True
        assert txt_spec.is_text_format() is True

    def test_is_text_format_returns_false_for_non_text_formats(self) -> None:
        """非テキストフォーマットでFalseが返されることをテスト"""
        # Arrange
        html_spec = FormatSpecification(format_id="test", name="HTML", format_type=FormatType.HTML)

        # Act & Assert
        assert html_spec.is_text_format() is False

    def test_get_file_extension(self) -> None:
        """正しいファイル拡張子が返されることをテスト"""
        # Arrange
        specs = [
            (FormatType.MARKDOWN, ".md"),
            (FormatType.HTML, ".html"),
            (FormatType.PLAIN_TEXT, ".txt"),
            (FormatType.YAML, ".yaml"),
            (FormatType.JSON, ".json"),
        ]

        # Act & Assert
        for format_type, expected_ext in specs:
            spec = FormatSpecification(format_id="test", name="Test", format_type=format_type)

            assert spec.get_file_extension() == expected_ext

    def test_create_yaml_spec_returns_valid_yaml_spec(self) -> None:
        """必須: YAML仕様が正しく作成されることをテスト"""
        # Act
        spec = FormatSpecification.create_yaml_spec()

        # Assert
        assert spec.format_id == "yaml_standard"
        assert spec.name == "YAML標準フォーマット"
        assert spec.format_type == FormatType.YAML
        assert spec.encoding == "utf-8"
        assert spec.line_ending == "\n"
        assert spec.indent_size == 2
        assert spec.use_tabs is False
        assert spec.properties["allow_unicode"] is True
        assert spec.properties["default_flow_style"] is False
        assert spec.properties["sort_keys"] is False

    def test_create_markdown_spec_returns_valid_markdown_spec(self) -> None:
        """必須: Markdown仕様が正しく作成されることをテスト"""
        # Act
        spec = FormatSpecification.create_markdown_spec()

        # Assert
        assert spec.format_id == "markdown_standard"
        assert spec.name == "Markdown標準フォーマット"
        assert spec.format_type == FormatType.MARKDOWN
        assert spec.encoding == "utf-8"
        assert spec.line_ending == "\n"
        assert spec.indent_size == 2
        assert spec.use_tabs is False
        assert spec.max_line_length == 80
        assert spec.properties["heading_style"] == "atx"
        assert spec.properties["bullet_style"] == "-"
        assert spec.properties["emphasis_style"] == "*"

    def test_immutability_of_format_specification(self) -> None:
        """必須: FormatSpecificationの不変性をテスト"""
        # Arrange
        spec = FormatSpecification(format_id="test", name="Test", format_type=FormatType.YAML)

        # Act & Assert
        with pytest.raises(AttributeError, match=".*"):
            spec.format_type = FormatType.MARKDOWN  # frozen=Trueなので変更不可

    def test_equality_of_format_specifications(self) -> None:
        """必須: FormatSpecificationの等価性をテスト"""
        # Arrange
        spec1 = FormatSpecification(format_id="test1", name="Test1", format_type=FormatType.YAML)

        spec2 = FormatSpecification(format_id="test1", name="Test1", format_type=FormatType.YAML)

        spec3 = FormatSpecification(format_id="test2", name="Test2", format_type=FormatType.MARKDOWN)

        # Act & Assert
        assert spec1 == spec2
        assert spec1 != spec3

    def test_format_specification_with_properties(self) -> None:
        """propertiesを含むフォーマット仕様のテスト"""
        # Arrange
        properties = {"allow_unicode": True, "default_flow_style": False, "sort_keys": False}

        # Act
        spec = FormatSpecification(format_id="test", name="Test", format_type=FormatType.YAML, properties=properties)

        # Assert
        assert spec.properties == properties

    def test_format_specification_default_properties(self) -> None:
        """デフォルトpropertiesのテスト"""
        # Act
        spec = FormatSpecification(format_id="test", name="Test", format_type=FormatType.YAML)

        # Assert
        assert spec.properties == {}

    def test_format_specification_with_max_line_length(self) -> None:
        """max_line_lengthを含むフォーマット仕様のテスト"""
        # Act
        spec = FormatSpecification(format_id="test", name="Test", format_type=FormatType.MARKDOWN, max_line_length=100)

        # Assert
        assert spec.max_line_length == 100

    def test_format_specification_without_max_line_length(self) -> None:
        """max_line_lengthがNoneのフォーマット仕様のテスト"""
        # Act
        spec = FormatSpecification(format_id="test", name="Test", format_type=FormatType.YAML)

        # Assert
        assert spec.max_line_length is None
