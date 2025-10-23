"""品質チェッカーストラテジーパターンのユニットテスト

TDD原則に基づき、実装前にテストを作成。
"""

import pytest

from noveler.domain.entities.quality_checker_strategy import (
    BasicStyleChecker,
    InvalidKanjiChecker,
    QualityChecker,
    QualityCheckResults,
)
from noveler.domain.value_objects.quality_issue import IssueCategory, IssueSeverity
from noveler.domain.value_objects.quality_issue import QualityIssue as QualityIssueVO


@pytest.mark.spec("SPEC-QUALITY-014")
class TestQualityCheckerStrategy:
    """品質チェッカーストラテジーパターンのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-UNNAMED")
    def test_unnamed(self) -> None:
        """QualityCheckerが抽象基底クラスであることを確認"""
        # Given/When/Then
        with pytest.raises(TypeError, match=".*"):
            # 抽象クラスは直接インスタンス化できない
            QualityChecker()


@pytest.mark.spec("SPEC-QUALITY-014")
class TestBasicStyleChecker:
    """基本スタイルチェッカーのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-UNNAMED")
    def test_basic_functionality(self) -> None:
        """三点リーダーの誤用を検出できることを確認"""
        # Given
        checker = BasicStyleChecker()
        content = "彼は言った。。。「それは違う...」"

        # When
        issues = checker.check(content)

        # Then
        assert len(issues) >= 2
        assert any("。。。" in issue.context for issue in issues)
        assert any("..." in issue.context for issue in issues)

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-DUPLICATE")
    def test_duplicate(self) -> None:
        """文末の重複表現を検出できることを確認"""
        # Given
        checker = BasicStyleChecker()
        content = "これはテストです。です。"

        # When
        issues = checker.check(content)

        # Then
        assert len(issues) >= 1
        assert any("です。です。" in issue.context for issue in issues)

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-UNNAMED")
    def test_edge_cases(self) -> None:
        """全角スペースや連続スペースを検出できることを確認"""
        # Given
        checker = BasicStyleChecker()
        content = "これは 全角スペースです。  連続スペースもあります。"

        # When
        issues = checker.check(content)

        # Then
        assert len(issues) >= 2
        assert any("全角スペース" in issue.message for issue in issues)
        assert any("連続スペース" in issue.message for issue in issues)

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-UNNAMED")
    def test_error_handling(self) -> None:
        """複数行の文章で行番号が正しく記録されることを確認"""
        # Given
        checker = BasicStyleChecker()
        content = """1行目は正常です。
2行目も問題ありません。
3行目です。。。問題があります。
4行目は正常です。"""

        # When
        issues = checker.check(content)

        # Then
        assert len(issues) >= 1
        problem_issue = next(i for i in issues if "。。。" in i.context)
        assert problem_issue.line_number == 3


@pytest.mark.spec("SPEC-QUALITY-014")
class TestInvalidKanjiChecker:
    """無効漢字チェッカーのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-UNNAMED")
    def test_validation(self) -> None:
        """旧字体の漢字を検出できることを確認"""
        # Given
        checker = InvalidKanjiChecker()
        content = "壱万円の價値がある會社の體制"

        # When
        issues = checker.check(content)

        # Then
        assert len(issues) >= 4
        assert any("壱" in issue.context for issue in issues)
        assert any("價" in issue.context for issue in issues)
        assert any("會" in issue.context for issue in issues)
        assert any("體" in issue.context for issue in issues)

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-UNNAMED")
    def test_integration(self) -> None:
        """環境依存文字を検出できることを確認"""
        # Given
        checker = InvalidKanjiChecker()
        content = "㈱株式会社や①番目の項目"

        # When
        issues = checker.check(content)

        # Then
        assert len(issues) >= 2
        assert any("㈱" in issue.context for issue in issues)
        assert any("①" in issue.context for issue in issues)

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-UNNAMED")
    def test_performance(self) -> None:
        """正常な漢字では問題を検出しないことを確認"""
        # Given
        checker = InvalidKanjiChecker()
        content = "正常な日本語の文章です。漢字も問題ありません。"

        # When
        issues = checker.check(content)

        # Then
        assert len(issues) == 0

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-UNNAMED")
    def test_configuration(self) -> None:
        """複数の問題を同時に検出できることを確認"""
        # Given
        checker = InvalidKanjiChecker()
        content = "會社の體制を變更する"

        # When
        issues = checker.check(content)

        # Then
        assert len(issues) == 3
        # 各旧字体が検出されている(contextは行全体なので重複する)
        assert any("會" in i.message for i in issues)
        assert any("體" in i.message for i in issues)
        assert any("變" in i.message for i in issues)


@pytest.mark.spec("SPEC-QUALITY-014")
class TestQualityCheckResults:
    """品質チェック結果のテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-UNNAMED")
    def test_initialization(self) -> None:
        """チェック結果を正しく集計できることを確認"""
        # Given
        issues = [
            QualityIssueVO(
                category=IssueCategory.STYLE, severity=IssueSeverity.ERROR, message="エラー1", line_number=1
            ),
            QualityIssueVO(
                category=IssueCategory.STYLE, severity=IssueSeverity.WARNING, message="警告1", line_number=2
            ),
            QualityIssueVO(
                category=IssueCategory.KANJI, severity=IssueSeverity.ERROR, message="エラー2", line_number=3
            ),
        ]

        # When
        results = QualityCheckResults(issues)

        # Then
        assert results.total_issues() == 3
        assert results.count_by_severity(IssueSeverity.ERROR) == 2
        assert results.count_by_severity(IssueSeverity.WARNING) == 1
        assert len(results.by_category(IssueCategory.STYLE)) == 2
        assert len(results.by_category(IssueCategory.KANJI)) == 1

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-EMPTY")
    def test_empty(self) -> None:
        """問題がない場合の結果を正しく処理できることを確認"""
        # Given
        issues = []

        # When
        results = QualityCheckResults(issues)

        # Then
        assert results.total_issues() == 0
        assert results.count_by_severity(IssueSeverity.ERROR) == 0
        assert len(results.by_category(IssueCategory.STYLE)) == 0

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-UNNAMED")
    def test_success_case(self) -> None:
        """品質スコアを正しく計算できることを確認"""
        # Given
        issues = [
            QualityIssueVO(
                category=IssueCategory.STYLE,
                severity=IssueSeverity.ERROR,
                message="重大なエラー",
                line_number=1,
                penalty_points=10,
            ),
            QualityIssueVO(
                category=IssueCategory.STYLE,
                severity=IssueSeverity.WARNING,
                message="軽微な警告",
                line_number=2,
                penalty_points=3,
            ),
        ]

        # When
        results = QualityCheckResults(issues)
        score = results.calculate_quality_score(100.0)

        # Then
        # 100点から減点: 100 - 10 - 3 = 87
        assert score == 87.0

    @pytest.mark.spec("SPEC-QUALITY_CHECKER_STRATEGY-GET")
    def test_get(self) -> None:
        """カテゴリ別に問題を取得できることを確認"""
        # Given
        issues = [
            QualityIssueVO(
                category=IssueCategory.STYLE, severity=IssueSeverity.ERROR, message="スタイルエラー", line_number=1
            ),
            QualityIssueVO(
                category=IssueCategory.KANJI, severity=IssueSeverity.WARNING, message="漢字の警告", line_number=2
            ),
            QualityIssueVO(
                category=IssueCategory.GRAMMAR, severity=IssueSeverity.INFO, message="文法の情報", line_number=3
            ),
        ]

        # When
        results = QualityCheckResults(issues)

        # Then
        style_issues = results.by_category(IssueCategory.STYLE)
        assert len(style_issues) == 1
        assert style_issues[0].message == "スタイルエラー"

        kanji_issues = results.by_category(IssueCategory.KANJI)
        assert len(kanji_issues) == 1
        assert kanji_issues[0].message == "漢字の警告"
