"""完成ステータス値オブジェクトのユニットテスト

TDD原則に基づき、実装前にテストを作成。
"""

import pytest

from noveler.domain.value_objects.completion_status import CompletionStatusType, QualityCheckResult, WritingPhase
from noveler.domain.value_objects.quality_score import QualityScore

pytestmark = pytest.mark.vo_smoke



@pytest.mark.spec("SPEC-QUALITY-014")
class TestWritingPhase:
    """執筆フェーズのテスト"""

    @pytest.mark.spec("SPEC-COMPLETION_STATUS-UNNAMED")
    def test_unnamed(self) -> None:
        """各執筆フェーズが定義されていることを確認"""
        assert WritingPhase.DRAFT.value == "draft"
        assert WritingPhase.REVIEW.value == "review"
        assert WritingPhase.FINAL_CHECK.value == "final_check"
        assert WritingPhase.PUBLISHED.value == "published"

    @pytest.mark.spec("SPEC-COMPLETION_STATUS-DETERMINE")
    def test_determine(self) -> None:
        """公開可能かどうかの判定を確認"""
        assert WritingPhase.DRAFT.is_publishable() is False
        assert WritingPhase.REVIEW.is_publishable() is False
        assert WritingPhase.FINAL_CHECK.is_publishable() is False
        assert WritingPhase.PUBLISHED.is_publishable() is True

    @pytest.mark.spec("SPEC-COMPLETION_STATUS-UNNAMED")
    def test_basic_functionality(self) -> None:
        """フェーズの日本語表記を確認"""
        assert WritingPhase.DRAFT.to_japanese() == "下書き"
        assert WritingPhase.REVIEW.to_japanese() == "推敲"
        assert WritingPhase.FINAL_CHECK.to_japanese() == "最終チェック"
        assert WritingPhase.PUBLISHED.to_japanese() == "公開済み"


@pytest.mark.spec("SPEC-QUALITY-014")
class TestCompletionStatusType:
    """完成ステータスタイプのテスト"""

    @pytest.mark.spec("SPEC-COMPLETION_STATUS-STATUS")
    def test_status(self) -> None:
        """各ステータスが定義されていることを確認"""
        assert CompletionStatusType.INITIALIZED == "initialized"
        assert CompletionStatusType.IN_PROGRESS == "in_progress"
        assert CompletionStatusType.COMPLETED == "completed"
        assert CompletionStatusType.FAILED == "failed"


@pytest.mark.spec("SPEC-QUALITY-014")
class TestQualityCheckResult:
    """品質チェック結果のテスト"""

    @pytest.mark.spec("SPEC-COMPLETION_STATUS-UNNAMED")
    def test_edge_cases(self) -> None:
        """成功した品質チェック結果の作成を確認"""
        # When
        result = QualityCheckResult(score=QualityScore(85), passed=True, issues=[])

        # Then
        assert result.score.value == 85
        assert result.passed is True
        assert len(result.issues) == 0

    @pytest.mark.spec("SPEC-COMPLETION_STATUS-UNNAMED")
    def test_error_handling(self) -> None:
        """失敗した品質チェック結果の作成を確認"""
        # When
        issues = ["文章が冗長です", "誤字があります"]
        result = QualityCheckResult(score=QualityScore(60), passed=False, issues=issues)

        # Then
        assert result.score.value == 60
        assert result.passed is False
        assert len(result.issues) == 2
        assert "文章が冗長です" in result.issues

    @pytest.mark.spec("SPEC-COMPLETION_STATUS-DETERMINE")
    def test_determine(self) -> None:
        """品質スコアによる合格判定を確認"""
        # 70点以上で合格
        result1 = QualityCheckResult.from_score(QualityScore(70), threshold=70.0)
        assert result1.passed is True

        # 70点未満で不合格
        result2 = QualityCheckResult.from_score(QualityScore(69), threshold=70.0)
        assert result2.passed is False

        # 90点以上は優秀
        result3 = QualityCheckResult.from_score(QualityScore(90), threshold=70.0)
        assert result3.passed is True
        assert result3.is_excellent() is True

    @pytest.mark.spec("SPEC-COMPLETION_STATUS-UNNAMED")
    def test_validation(self) -> None:
        """品質に応じたメッセージ生成を確認"""
        # 優秀な品質
        result1 = QualityCheckResult(score=QualityScore(95), passed=True, issues=[])
        message = result1.get_summary_message()
        assert "優秀な品質" in message

        # 改善が必要
        result2 = QualityCheckResult(score=QualityScore(60), passed=False, issues=["誤字", "文法エラー"])
        message = result2.get_summary_message()
        assert "改善が必要" in message
        assert "2件の問題" in message
