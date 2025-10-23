"""品質問題値オブジェクトのユニットテスト

TDD原則に基づき、実装前にテストを作成。
"""

import pytest
pytestmark = pytest.mark.quality_domain


from noveler.domain.value_objects.quality_issue import IssueCategory, IssueSeverity, QualityIssue


@pytest.mark.spec("SPEC-QUALITY-014")
class TestQualityIssue:
    """品質問題値オブジェクトのテスト"""

    def test_unnamed(self) -> None:
        """品質問題を作成できることを確認"""
        # Given/When
        issue = QualityIssue(
            category=IssueCategory.STYLE,
            severity=IssueSeverity.WARNING,
            message="三点リーダーは「…」を使用してください",
            line_number=10,
            position=5,
            context="それは。。。違います",
            suggestion="それは…違います",
            penalty_points=3,
        )

        # Then
        assert issue.category == IssueCategory.STYLE
        assert issue.severity == IssueSeverity.WARNING
        assert issue.message == "三点リーダーは「…」を使用してください"
        assert issue.line_number == 10
        assert issue.position == 5
        assert issue.context == "それは。。。違います"
        assert issue.suggestion == "それは…違います"
        assert issue.penalty_points == 3

    def test_basic_functionality(self) -> None:
        """重要度に応じてデフォルトの減点ポイントが設定されることを確認"""
        # Given/When
        error_issue = QualityIssue(
            category=IssueCategory.STYLE, severity=IssueSeverity.ERROR, message="エラー", line_number=1
        )

        warning_issue = QualityIssue(
            category=IssueCategory.STYLE, severity=IssueSeverity.WARNING, message="警告", line_number=1
        )

        info_issue = QualityIssue(
            category=IssueCategory.STYLE, severity=IssueSeverity.INFO, message="情報", line_number=1
        )

        # Then
        assert error_issue.penalty_points == 5
        assert warning_issue.penalty_points == 3
        assert info_issue.penalty_points == 1

    def test_edge_cases(self) -> None:
        """値オブジェクトが不変であることを確認"""
        # Given
        issue = QualityIssue(
            category=IssueCategory.STYLE, severity=IssueSeverity.WARNING, message="テスト", line_number=1
        )

        # When/Then
        with pytest.raises(AttributeError, match=".*"):
            issue.message = "変更されたメッセージ"

    def test_error_handling(self) -> None:
        """同じ内容の品質問題が等しいと判定されることを確認"""
        # Given
        issue1 = QualityIssue(
            category=IssueCategory.STYLE,
            severity=IssueSeverity.WARNING,
            message="同じメッセージ",
            line_number=10,
            position=5,
        )

        issue2 = QualityIssue(
            category=IssueCategory.STYLE,
            severity=IssueSeverity.WARNING,
            message="同じメッセージ",
            line_number=10,
            position=5,
        )

        issue3 = QualityIssue(
            category=IssueCategory.STYLE,
            severity=IssueSeverity.WARNING,
            message="違うメッセージ",
            line_number=10,
            position=5,
        )

        # Then
        assert issue1 == issue2
        assert issue1 != issue3

    def test_validation(self) -> None:
        """品質問題の文字列表現が適切であることを確認"""
        # Given
        issue = QualityIssue(
            category=IssueCategory.KANJI,
            severity=IssueSeverity.ERROR,
            message="旧字体が使用されています",
            line_number=5,
            context="壱万円",
        )

        # When
        str_repr = str(issue)

        # Then
        assert "5行目" in str_repr
        assert "ERROR" in str_repr
        assert "旧字体が使用されています" in str_repr

    def test_determine(self) -> None:
        """修正提案の有無を判定できることを確認"""
        # Given
        issue_with_suggestion = QualityIssue(
            category=IssueCategory.STYLE,
            severity=IssueSeverity.WARNING,
            message="問題",
            line_number=1,
            suggestion="修正案",
        )

        issue_without_suggestion = QualityIssue(
            category=IssueCategory.STYLE, severity=IssueSeverity.WARNING, message="問題", line_number=1
        )

        # Then
        assert issue_with_suggestion.has_suggestion() is True
        assert issue_without_suggestion.has_suggestion() is False


@pytest.mark.spec("SPEC-QUALITY-014")
class TestIssueSeverity:
    """問題重要度列挙型のテスト"""

    def test_integration(self) -> None:
        """重要度が正しく定義されていることを確認"""
        # Then
        assert IssueSeverity.ERROR.value == "error"
        assert IssueSeverity.WARNING.value == "warning"
        assert IssueSeverity.INFO.value == "info"

    def test_performance(self) -> None:
        """重要度を比較できることを確認"""
        # Then
        assert IssueSeverity.ERROR.weight > IssueSeverity.WARNING.weight
        assert IssueSeverity.WARNING.weight > IssueSeverity.INFO.weight

    def test_convert(self) -> None:
        """重要度を適切な文字列に変換できることを確認"""
        # Then
        assert str(IssueSeverity.ERROR) == "エラー"
        assert str(IssueSeverity.WARNING) == "警告"
        assert str(IssueSeverity.INFO) == "情報"


@pytest.mark.spec("SPEC-QUALITY-014")
class TestIssueCategory:
    """問題カテゴリ列挙型のテスト"""

    def test_configuration(self) -> None:
        """カテゴリが正しく定義されていることを確認"""
        # Then
        assert IssueCategory.STYLE.value == "style"
        assert IssueCategory.GRAMMAR.value == "grammar"
        assert IssueCategory.KANJI.value == "kanji"
        assert IssueCategory.COMPOSITION.value == "composition"
        assert IssueCategory.CHARACTER.value == "character"
        assert IssueCategory.READABILITY.value == "readability"

    def test_initialization(self) -> None:
        """カテゴリを日本語で表示できることを確認"""
        # Then
        assert IssueCategory.STYLE.display_name == "文体・スタイル"
        assert IssueCategory.GRAMMAR.display_name == "文法"
        assert IssueCategory.KANJI.display_name == "漢字・表記"
        assert IssueCategory.COMPOSITION.display_name == "構成"
        assert IssueCategory.CHARACTER.display_name == "キャラクター"
        assert IssueCategory.READABILITY.display_name == "読みやすさ"

    def test_success_case(self) -> None:
        """カテゴリの説明を取得できることを確認"""
        # Then
        assert "三点リーダー" in IssueCategory.STYLE.description
        assert "文法的" in IssueCategory.GRAMMAR.description
        assert "旧字体" in IssueCategory.KANJI.description
