#!/usr/bin/env python3
"""ValidationResult値オブジェクトのユニットテスト

仕様書: specs/validation_result.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

import pytest

from noveler.domain.value_objects.validation_result import ValidationIssue, ValidationLevel, ValidationResult

pytestmark = pytest.mark.vo_smoke



class TestValidationLevel:
    """ValidationLevelのテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_all(self) -> None:
        """すべてのレベルが定義されていることを確認"""
        assert ValidationLevel.ERROR.value == "error"
        assert ValidationLevel.WARNING.value == "warning"
        assert ValidationLevel.INFO.value == "info"


class TestValidationIssue:
    """ValidationIssueのテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_init(self) -> None:
        """必須フィールドのみで初期化できることを確認"""
        # Act
        issue = ValidationIssue(level=ValidationLevel.ERROR, message="必須項目が未設定です")

        # Assert
        assert issue.level == ValidationLevel.ERROR
        assert issue.message == "必須項目が未設定です"
        assert issue.field_path == ""
        assert issue.suggestion == ""

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_init_all(self) -> None:
        """全フィールドを指定して初期化できることを確認"""
        # Act
        issue = ValidationIssue(
            level=ValidationLevel.WARNING,
            message="説明が短すぎます",
            field_path="chapters[0].description",
            suggestion="100文字以上の説明を記載することを推奨します",
        )

        # Assert
        assert issue.level == ValidationLevel.WARNING
        assert issue.message == "説明が短すぎます"
        assert issue.field_path == "chapters[0].description"
        assert issue.suggestion == "100文字以上の説明を記載することを推奨します"

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_verification(self) -> None:
        """frozen=Trueにより値の変更ができないことを確認"""
        # Arrange
        issue = ValidationIssue(level=ValidationLevel.INFO, message="テストメッセージ")

        # Act & Assert
        with pytest.raises(AttributeError, match=".*"):
            issue.level = ValidationLevel.ERROR  # type: ignore

        with pytest.raises(AttributeError, match=".*"):
            issue.message = "変更"  # type: ignore


class TestValidationResult:
    """ValidationResultのテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_init_minimal(self) -> None:
        """最小構成で初期化できることを確認"""
        # Act
        result = ValidationResult(is_valid=True)

        # Assert
        assert result.is_valid is True
        assert result.issues == []
        assert result.validated_fields == {}

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_init_all(self) -> None:
        """全フィールドを指定して初期化できることを確認"""
        # Arrange
        issues = [ValidationIssue(ValidationLevel.ERROR, "エラー1"), ValidationIssue(ValidationLevel.WARNING, "警告1")]
        fields = {"title": "テストタイトル", "author": "作者名"}

        # Act
        result = ValidationResult(is_valid=False, issues=issues, validated_fields=fields)

        # Assert
        assert result.is_valid is False
        assert len(result.issues) == 2
        assert result.validated_fields == fields

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_has_errors(self) -> None:
        """has_errorsプロパティが正しく動作することを確認"""
        # エラーあり
        with_error = ValidationResult(
            is_valid=False,
            issues=[ValidationIssue(ValidationLevel.ERROR, "エラー"), ValidationIssue(ValidationLevel.WARNING, "警告")],
        )

        assert with_error.has_errors is True

        # エラーなし(警告のみ)
        no_error = ValidationResult(is_valid=True, issues=[ValidationIssue(ValidationLevel.WARNING, "警告")])
        assert no_error.has_errors is False

        # 問題なし
        no_issues = ValidationResult(is_valid=True)
        assert no_issues.has_errors is False

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_has_warnings(self) -> None:
        """has_warningsプロパティが正しく動作することを確認"""
        # 警告あり
        with_warning = ValidationResult(
            is_valid=True,
            issues=[ValidationIssue(ValidationLevel.WARNING, "警告"), ValidationIssue(ValidationLevel.INFO, "情報")],
        )

        assert with_warning.has_warnings is True

        # 警告なし(エラーのみ)
        no_warning = ValidationResult(is_valid=False, issues=[ValidationIssue(ValidationLevel.ERROR, "エラー")])
        assert no_warning.has_warnings is False

        # 問題なし
        no_issues = ValidationResult(is_valid=True)
        assert no_issues.has_warnings is False

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_error_count(self) -> None:
        """error_countプロパティが正しくカウントすることを確認"""
        # 複数のエラー
        result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(ValidationLevel.ERROR, "エラー1"),
                ValidationIssue(ValidationLevel.ERROR, "エラー2"),
                ValidationIssue(ValidationLevel.WARNING, "警告1"),
                ValidationIssue(ValidationLevel.INFO, "情報1"),
            ],
        )

        assert result.error_count == 2

        # エラーなし
        no_error = ValidationResult(is_valid=True, issues=[ValidationIssue(ValidationLevel.WARNING, "警告")])
        assert no_error.error_count == 0

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_warning_count(self) -> None:
        """warning_countプロパティが正しくカウントすることを確認"""
        # 複数の警告
        result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(ValidationLevel.ERROR, "エラー1"),
                ValidationIssue(ValidationLevel.WARNING, "警告1"),
                ValidationIssue(ValidationLevel.WARNING, "警告2"),
                ValidationIssue(ValidationLevel.WARNING, "警告3"),
                ValidationIssue(ValidationLevel.INFO, "情報1"),
            ],
        )

        assert result.warning_count == 3

        # 警告なし
        no_warning = ValidationResult(is_valid=False, issues=[ValidationIssue(ValidationLevel.ERROR, "エラー")])
        assert no_warning.warning_count == 0

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_get_errors(self) -> None:
        """get_errors()がエラーのみを返すことを確認"""
        # Arrange
        error1 = ValidationIssue(ValidationLevel.ERROR, "エラー1")
        error2 = ValidationIssue(ValidationLevel.ERROR, "エラー2")
        warning = ValidationIssue(ValidationLevel.WARNING, "警告")
        info = ValidationIssue(ValidationLevel.INFO, "情報")

        result = ValidationResult(is_valid=False, issues=[error1, warning, error2, info])

        # Act
        errors = result.get_errors()

        # Assert
        assert len(errors) == 2
        assert error1 in errors
        assert error2 in errors
        assert warning not in errors
        assert info not in errors

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_get_warnings(self) -> None:
        """get_warnings()が警告のみを返すことを確認"""
        # Arrange
        error = ValidationIssue(ValidationLevel.ERROR, "エラー")
        warning1 = ValidationIssue(ValidationLevel.WARNING, "警告1")
        warning2 = ValidationIssue(ValidationLevel.WARNING, "警告2")
        info = ValidationIssue(ValidationLevel.INFO, "情報")

        result = ValidationResult(is_valid=False, issues=[error, warning1, info, warning2])

        # Act
        warnings = result.get_warnings()

        # Assert
        assert len(warnings) == 2
        assert warning1 in warnings
        assert warning2 in warnings
        assert error not in warnings
        assert info not in warnings

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_merge_basic_operation(self) -> None:
        """merge()の基本動作を確認"""
        # Arrange
        result1 = ValidationResult(
            is_valid=True,
            issues=[ValidationIssue(ValidationLevel.WARNING, "警告1")],
            validated_fields={"field1": "value1", "field2": "value2"},
        )

        result2 = ValidationResult(
            is_valid=False,
            issues=[ValidationIssue(ValidationLevel.ERROR, "エラー1")],
            validated_fields={"field2": "new_value2", "field3": "value3"},
        )

        # Act
        merged = result1.merge(result2)

        # Assert
        # is_validは両方がTrueの場合のみTrue
        assert merged.is_valid is False

        # issuesは結合される
        assert len(merged.issues) == 2
        assert merged.issues[0].message == "警告1"
        assert merged.issues[1].message == "エラー1"

        # validated_fieldsは後勝ちでマージ
        assert merged.validated_fields == {
            "field1": "value1",
            "field2": "new_value2",  # result2の値で上書き
            "field3": "value3",
        }

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_merge_valid(self) -> None:
        """両方がvalidの場合のmerge()を確認"""
        # Arrange
        result1 = ValidationResult(is_valid=True)
        result2 = ValidationResult(is_valid=True)

        # Act
        merged = result1.merge(result2)

        # Assert
        assert merged.is_valid is True

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_merge_empty_merge(self) -> None:
        """空の結果とのマージを確認"""
        # Arrange
        result = ValidationResult(
            is_valid=False,
            issues=[ValidationIssue(ValidationLevel.ERROR, "エラー")],
            validated_fields={"field": "value"},
        )

        empty = ValidationResult(is_valid=True)

        # Act
        merged = result.merge(empty)

        # Assert
        assert merged.is_valid is False
        assert len(merged.issues) == 1
        assert merged.validated_fields == {"field": "value"}

    @pytest.mark.spec("SPEC-QUALITY-010")
    def test_verification(self) -> None:
        """frozen=Trueにより値の変更ができないことを確認"""
        # Arrange
        result = ValidationResult(is_valid=True)

        # Act & Assert
        with pytest.raises(AttributeError, match=".*"):
            result.is_valid = False  # type: ignore

        # issuesはリストなので、直接代入はできない
        with pytest.raises(AttributeError, match=".*"):
            result.issues = []  # type: ignore
