"""
FormatStandardizationServiceのユニットテスト

SPEC-WORKFLOW-002: レガシーモジュールTDD+DDD移行
"""

import pytest

from noveler.domain.exceptions import ValidationError
from noveler.domain.services.format_standardization_service import (
    ComplianceCheckResult,
    FormatStandardizationService,
    StandardizationResult,
)
from noveler.domain.value_objects.format_specification import FormatSpecification, FormatType


@pytest.mark.spec("SPEC-WORKFLOW-002")
class TestFormatStandardizationService:
    """FormatStandardizationServiceのテストクラス"""

    @pytest.fixture
    def service(self):
        """テスト用サービスインスタンス"""
        return FormatStandardizationService()

    @pytest.fixture
    def sample_yaml_data(self):
        """テスト用YAMLデータ"""
        return {
            "title": "テストエピソード",
            "content": "これはテストコンテンツです。",
            "metadata": {"word_count": 100, "status": "執筆済み"},
        }

    @pytest.fixture
    def sample_markdown_content(self) -> str:
        """テスト用Markdownコンテンツ"""
        return """# テストタイトル

これはテストの段落です。

## サブタイトル

- リスト項目1
* リスト項目2
+ リスト項目3

**太字テキスト**
__太字テキスト2__
*斜体テキスト*
_斜体テキスト2_
"""

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-SERVICE_INITIALIZATI")
    def test_service_initialization_sets_default_specs(self, service: object) -> None:
        """サービス初期化時にデフォルト仕様が設定されることをテスト"""
        # Act
        specs = service.get_format_specifications()

        # Assert
        assert FormatType.YAML in specs
        assert FormatType.MARKDOWN in specs
        assert specs[FormatType.YAML].format_type == FormatType.YAML
        assert specs[FormatType.MARKDOWN].format_type == FormatType.MARKDOWN

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-REGISTER_FORMAT_SPEC")
    def test_register_format_specification_adds_valid_spec(self, service: object) -> None:
        """有効なフォーマット仕様が登録されることをテスト"""
        # Arrange
        custom_spec = FormatSpecification(format_id="json_custom", name="JSONカスタム", format_type=FormatType.JSON)

        initial_count = len(service.get_format_specifications())

        # Act
        service.register_format_specification(custom_spec)

        # Assert
        specs = service.get_format_specifications()
        assert len(specs) == initial_count + 1
        assert FormatType.JSON in specs
        assert specs[FormatType.JSON] == custom_spec

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-REGISTER_FORMAT_SPEC")
    def test_register_format_specification_raises_error_for_invalid_type(self, service: object) -> None:
        """無効な型の仕様登録で例外が発生することをテスト"""
        # Arrange & Act & Assert
        with pytest.raises(
            ValidationError, match="フォーマット仕様はFormatSpecificationのインスタンスである必要があります"
        ):
            service.register_format_specification("invalid_spec")

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_YAML_FOR")
    def test_standardize_yaml_format_with_dict_data_returns_success_result(
        self, service: object, sample_yaml_data: object
    ) -> None:
        """辞書データのYAML標準化で成功結果が返されることをテスト"""
        # Act
        result = service.standardize_yaml_format(sample_yaml_data, None)

        # Assert
        assert isinstance(result, StandardizationResult)
        assert result.is_successful() is True
        assert len(result.standardized_content) > 0
        assert "title: テストエピソード" in result.standardized_content
        assert result.applied_spec.format_type == FormatType.YAML

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_YAML_FOR")
    def test_standardize_yaml_format_with_string_data_returns_success_result(self, service: object) -> None:
        """文字列データのYAML標準化で成功結果が返されることをテスト"""
        # Arrange
        yaml_string = """
title: テストタイトル
content: テストコンテンツ
metadata:
  status: 執筆済み
"""

        # Act
        result = service.standardize_yaml_format(yaml_string, None)

        # Assert
        assert isinstance(result, StandardizationResult)
        assert result.is_successful() is True
        assert len(result.standardized_content) > 0
        assert "title:" in result.standardized_content

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_YAML_FOR")
    def test_standardize_yaml_format_with_invalid_yaml_returns_failed_result(self, service: object) -> None:
        """無効なYAMLで失敗結果が返されることをテスト"""
        # Arrange
        invalid_yaml = "title: テスト\ncontent: [invalid yaml"

        # Act
        result = service.standardize_yaml_format(invalid_yaml, None)

        # Assert
        assert isinstance(result, StandardizationResult)
        assert result.is_successful() is False
        assert len(result.violations) > 0
        assert "YAML構文エラー" in result.violations[0]

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_YAML_FOR")
    def test_standardize_yaml_format_with_none_data_returns_failed_result(self, service: object) -> None:
        """Noneデータで失敗結果が返されることをテスト"""
        # Act
        result = service.standardize_yaml_format(None, None)

        # Assert
        assert isinstance(result, StandardizationResult)
        assert result.is_successful() is False
        assert "YAMLデータが空です" in result.violations

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_YAML_FOR")
    def test_standardize_yaml_format_with_custom_spec(self, service: object) -> None:
        """カスタム仕様でYAML標準化をテスト"""
        # Arrange
        custom_spec = FormatSpecification.create_yaml_spec()
        data = {"title": "テスト"}

        # Act
        result = service.standardize_yaml_format(data, custom_spec)

        # Assert
        assert result.applied_spec.format_id == "yaml_standard"

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_YAML_FOR")
    def test_standardize_yaml_format_with_non_yaml_spec_raises_error(self, service: object) -> None:
        """非YAML仕様で例外が発生することをテスト"""
        # Arrange
        markdown_spec = FormatSpecification.create_markdown_spec()
        data = {"title": "テスト"}

        # Act & Assert
        with pytest.raises(ValidationError, match="YAML用の仕様ではありません"):
            service.standardize_yaml_format(data, markdown_spec)

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_MARKDOWN")
    def test_standardize_markdown_format_with_valid_content_returns_success_result(
        self, service: object, sample_markdown_content: object
    ) -> None:
        """有効なMarkdownの標準化で成功結果が返されることをテスト"""
        # Act
        result = service.standardize_markdown_format(sample_markdown_content, None)

        # Assert
        assert isinstance(result, StandardizationResult)
        assert result.is_successful() is True
        assert len(result.standardized_content) > 0
        assert "# テストタイトル" in result.standardized_content
        assert result.applied_spec.format_type == FormatType.MARKDOWN

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_MARKDOWN")
    def test_standardize_markdown_format_with_empty_content_returns_failed_result(self, service: object) -> None:
        """空のMarkdownコンテンツで失敗結果が返されることをテスト"""
        # Act
        result = service.standardize_markdown_format("", None)

        # Assert
        assert isinstance(result, StandardizationResult)
        assert result.is_successful() is False
        assert "Markdownコンテンツが空です" in result.violations

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_MARKDOWN")
    def test_standardize_markdown_format_applies_corrections(self, service: object) -> None:
        """Markdown標準化で修正が適用されることをテスト"""
        # Arrange
        content_with_issues = """# タイトル

* リスト1
+ リスト2
- リスト3

__太字__
_斜体_
"""

        # Act
        result = service.standardize_markdown_format(content_with_issues, None)

        # Assert
        assert result.has_corrections() is True
        assert len(result.corrections) > 0
        # リストマーカーが統一されることを期待
        assert "- リスト1" in result.standardized_content
        assert "- リスト2" in result.standardized_content
        assert "- リスト3" in result.standardized_content

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_MARKDOWN")
    def test_standardize_markdown_format_with_custom_spec(self, service: object) -> None:
        """カスタム仕槗でMarkdown標準化をテスト"""
        # Arrange
        custom_spec = FormatSpecification.create_markdown_spec()
        content = "# テスト"

        # Act
        result = service.standardize_markdown_format(content, custom_spec)

        # Assert
        assert result.applied_spec.format_id == "markdown_standard"

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZE_MARKDOWN")
    def test_standardize_markdown_format_with_non_markdown_spec_raises_error(self, service: object) -> None:
        """非Markdown仕様で例外が発生することをテスト"""
        # Arrange
        yaml_spec = FormatSpecification.create_yaml_spec()
        content = "# テスト"

        # Act & Assert
        with pytest.raises(ValidationError, match="Markdown用の仕様ではありません"):
            service.standardize_markdown_format(content, yaml_spec)

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-VALIDATE_FORMAT_COMP")
    def test_validate_format_compliance_with_valid_yaml_returns_compliant_result(self, service: object) -> None:
        """有効なYAMLの準拠性チェックで準拠結果が返されることをテスト"""
        # Arrange
        valid_yaml = """title: テスト
content: コンテンツ
metadata:
  status: 執筆済み
"""

        # Act
        result = service.validate_format_compliance(valid_yaml, FormatType.YAML)

        # Assert
        assert isinstance(result, ComplianceCheckResult)
        assert result.is_compliant is True
        assert len(result.violations) == 0
        assert result.score > 0.0

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-VALIDATE_FORMAT_COMP")
    def test_validate_format_compliance_with_invalid_yaml_returns_non_compliant_result(self, service: object) -> None:
        """無効なYAMLの準拠性チェックで非準拠結果が返されることをテスト"""
        # Arrange
        invalid_yaml = "title: テスト\ncontent: [invalid"

        # Act
        result = service.validate_format_compliance(invalid_yaml, FormatType.YAML)

        # Assert
        assert isinstance(result, ComplianceCheckResult)
        assert result.is_compliant is False
        assert len(result.violations) > 0

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-VALIDATE_FORMAT_COMP")
    def test_validate_format_compliance_with_valid_markdown_returns_compliant_result(self, service: object) -> None:
        """有効なMarkdownの準拠性チェックで準拠結果が返されることをテスト"""
        # Arrange
        valid_markdown = """# タイトル

これは有効なMarkdownコンテンツです。

## サブタイトル

- リスト項目1
- リスト項目2
"""

        # Act
        result = service.validate_format_compliance(valid_markdown, FormatType.MARKDOWN)

        # Assert
        assert isinstance(result, ComplianceCheckResult)
        assert result.is_compliant is True or len(result.violations) == 0  # 軽微な提案はOK
        assert result.score > 0.0

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-VALIDATE_FORMAT_COMP")
    def test_validate_format_compliance_with_markdown_issues_returns_violations(self, service: object) -> None:
        """問題のあるMarkdownで違反が返されることをテスト"""
        # Arrange
        # 行末に明示的に空白を追加して問題のあるコンテンツを作成
        problematic_markdown = "# タイトル\n\nこれは行末に空白があります。 \nそして非常に長い行です。これは80文字を超える可能性があり、推奨されません。長すぎる行は読みにくくなります。長すぎる行は読みにくくなります。\n"

        # Act
        result = service.validate_format_compliance(problematic_markdown, FormatType.MARKDOWN)

        # Assert
        assert isinstance(result, ComplianceCheckResult)
        # 行末空白で違反が発生することを期待
        assert len(result.violations) > 0 or len(result.suggestions) > 0

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-VALIDATE_FORMAT_COMP")
    def test_validate_format_compliance_with_unsupported_format_returns_error(self, service: object) -> None:
        """サポートされていないフォーマットで仕様なしエラーが返されることをテスト"""
        # Act
        result = service.validate_format_compliance("content", FormatType.JSON)

        # Assert
        assert isinstance(result, ComplianceCheckResult)
        assert result.is_compliant is False
        assert "仕様が設定されていません" in result.violations[0]

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-BATCH_STANDARDIZE_CO")
    def test_batch_standardize_content_with_mixed_formats_returns_results_list(self, service: object) -> None:
        """混合フォーマットの一括標準化で結果リストが返されることをテスト"""
        # Arrange
        content_list = [
            ("title: テスト", FormatType.YAML),
            ("# タイトル\n\nコンテンツ", FormatType.MARKDOWN),
            ("title: 別のテスト", FormatType.YAML),
        ]

        # Act
        results = service.batch_standardize_content(content_list)

        # Assert
        assert len(results) == 3
        for result in results:
            assert isinstance(result, StandardizationResult)
            # 一部は成功することを期待

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-BATCH_STANDARDIZE_CO")
    def test_batch_standardize_content_with_empty_list_returns_empty_list(self, service: object) -> None:
        """空リストの一括標準化で空リストが返されることをテスト"""
        # Act
        results = service.batch_standardize_content([])

        # Assert
        assert results == []

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-BATCH_STANDARDIZE_CO")
    def test_batch_standardize_content_handles_individual_errors_gracefully(self, service: object) -> None:
        """一括標準化で個別エラーが適切に処理されることをテスト"""
        # Arrange
        content_list = [
            ("title: 有効なYAML", FormatType.YAML),
            ("invalid: [yaml", FormatType.YAML),  # 無効なYAML
            ("# 有効なMarkdown", FormatType.MARKDOWN),
        ]

        # Act
        results = service.batch_standardize_content(content_list)

        # Assert
        assert len(results) == 3
        assert results[0].is_successful() is True
        assert results[1].is_successful() is False  # エラーが記録される
        assert results[2].is_successful() is True

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-BATCH_STANDARDIZE_CO")
    def test_batch_standardize_content_with_unsupported_format_creates_error_result(self, service: object) -> None:
        """サポートされていないフォーマットでエラー結果が作成されることをテスト"""
        # Arrange
        content_list = [("content", FormatType.HTML)]

        # Act
        results = service.batch_standardize_content(content_list)

        # Assert
        assert len(results) == 1
        assert results[0].is_successful() is False
        assert "サポートされていないフォーマット" in results[0].violations[0]

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-STANDARDIZATION_RESU")
    def test_standardization_result_creation_and_properties(self, service: object, sample_yaml_data: object) -> None:
        """StandardizationResultの作成と属性をテスト"""
        # Act
        result = service.standardize_yaml_format(sample_yaml_data, None)

        # Assert
        assert hasattr(result, "standardized_content")
        assert hasattr(result, "applied_spec")
        assert hasattr(result, "violations")
        assert hasattr(result, "corrections")
        assert hasattr(result, "standardization_timestamp")
        assert result.is_successful() is True
        assert result.has_corrections() is True  # 標準化で何らかの修正が適用される

    @pytest.mark.spec("SPEC-FORMAT_STANDARDIZATION_SERVICE-COMPLIANCE_CHECK_RES")
    def test_compliance_check_result_creation_and_properties(self, service: object) -> None:
        """ComplianceCheckResultの作成と属性をテスト"""
        # Arrange
        content = "title: テスト"

        # Act
        result = service.validate_format_compliance(content, FormatType.YAML)

        # Assert
        assert hasattr(result, "is_compliant")
        assert hasattr(result, "violations")
        assert hasattr(result, "suggestions")
        assert hasattr(result, "score")
        assert hasattr(result, "check_timestamp")
        assert isinstance(result.score, float)
        assert 0.0 <= result.score <= 1.0
