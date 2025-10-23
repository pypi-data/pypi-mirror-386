"""品質チェック集約ルートのユニットテスト

TDD原則に基づき、実装前にテストを作成。
"""

from datetime import datetime
from typing import NoReturn

import pytest
pytestmark = pytest.mark.quality_domain


from noveler.domain.entities.quality_checker_strategy import (
    BasicStyleChecker,
    InvalidKanjiChecker,
    QualityCheckAggregate,
)
from noveler.domain.value_objects.quality_issue import IssueCategory
from noveler.domain.value_objects.session_id import SessionId


@pytest.mark.spec("SPEC-QUALITY-014")
class TestQualityCheckAggregate:
    """品質チェック集約ルートのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_AGGREGATE-UNNAMED")
    def test_unnamed(self) -> None:
        """集約ルートを作成できることを確認"""
        # Given
        session_id = SessionId()

        # When
        aggregate = QualityCheckAggregate(session_id=session_id)

        # Then
        assert aggregate.session_id == session_id
        assert aggregate.get_checker_count() == 0
        assert aggregate._completed_at is None

    @pytest.mark.spec("SPEC-QUALITY_CHECK_AGGREGATE-ADD")
    def test_add(self) -> None:
        """チェッカーを追加できることを確認"""
        # Given
        session_id = SessionId()
        aggregate = QualityCheckAggregate(session_id=session_id)
        checker = BasicStyleChecker()

        # When
        aggregate.add_checker(checker)

        # Then
        assert aggregate.get_checker_count() == 1

    @pytest.mark.spec("SPEC-QUALITY_CHECK_AGGREGATE-DUPLICATE_ADD")
    def test_duplicate_add(self) -> None:
        """同じチェッカーインスタンスの重複追加を防止することを確認"""
        # Given
        session_id = SessionId()
        aggregate = QualityCheckAggregate(session_id=session_id)
        checker = BasicStyleChecker()

        # When
        aggregate.add_checker(checker)
        aggregate.add_checker(checker)  # 同じインスタンスを再度追加

        # Then
        assert aggregate.get_checker_count() == 1

    @pytest.mark.spec("SPEC-QUALITY_CHECK_AGGREGATE-EXECUTE")
    def test_execute(self) -> None:
        """全てのチェッカーが実行されることを確認"""
        # Given
        session_id = SessionId()
        aggregate = QualityCheckAggregate(session_id=session_id)
        aggregate.add_checker(BasicStyleChecker())
        aggregate.add_checker(InvalidKanjiChecker())

        content = """これはテストです。。。
        旧字体の壱万円です。"""

        # When
        results = aggregate.run_all_checks(content)

        # Then
        assert results is not None
        assert results.total_issues() >= 2  # 少なくとも2つの問題を検出
        assert aggregate._completed_at is not None
        assert isinstance(aggregate._completed_at, datetime)

    @pytest.mark.spec("SPEC-QUALITY_CHECK_AGGREGATE-ERROR_HANDLING")
    def test_error_handling(self) -> None:
        """チェッカーがエラーを起こしても処理が続行されることを確認"""
        # Given
        session_id = SessionId()
        aggregate = QualityCheckAggregate(session_id=session_id)

        # エラーを起こすモックチェッカー
        class ErrorChecker:
            def check(self, _content: str) -> NoReturn:
                msg = "チェック中にエラー発生"
                raise RuntimeError(msg)

        aggregate.add_checker(ErrorChecker())
        aggregate.add_checker(BasicStyleChecker())

        # When
        results = aggregate.run_all_checks("テストコンテンツ")

        # Then
        assert results is not None
        issues = results.all_issues()

        # エラーがシステムエラーとして記録される
        system_errors = [i for i in issues if i.category == IssueCategory.SYSTEM]
        assert len(system_errors) >= 1
        assert "チェッカーエラー" in system_errors[0].message

    @pytest.mark.spec("SPEC-QUALITY_CHECK_AGGREGATE-EMPTY_LIST_EXECUTE")
    def test_empty_list_execute(self) -> None:
        """チェッカーが登録されていない状態での実行を確認"""
        # Given
        session_id = SessionId()
        aggregate = QualityCheckAggregate(session_id=session_id)

        # When
        results = aggregate.run_all_checks("テストコンテンツ")

        # Then
        assert results is not None
        assert results.total_issues() == 0
        assert aggregate._completed_at is not None

    @pytest.mark.spec("SPEC-QUALITY_CHECK_AGGREGATE-UNNAMED")
    def test_basic_functionality(self) -> None:
        """同じ集約で複数回チェックを実行できることを確認"""
        # Given
        session_id = SessionId()
        aggregate = QualityCheckAggregate(session_id=session_id)
        aggregate.add_checker(BasicStyleChecker())

        # When
        results1 = aggregate.run_all_checks("最初のテキスト。。。")
        results2 = aggregate.run_all_checks("2回目のテキスト...")

        # Then
        assert results1.total_issues() >= 1
        assert results2.total_issues() >= 1
        # 2回目の実行で完了時刻が更新される
        assert aggregate._completed_at is not None

    @pytest.mark.spec("SPEC-QUALITY_CHECK_AGGREGATE-UNNAMED")
    def test_edge_cases(self) -> None:
        """各チェック実行の結果が独立していることを確認"""
        # Given
        session_id = SessionId()
        aggregate = QualityCheckAggregate(session_id=session_id)
        aggregate.add_checker(BasicStyleChecker())

        # When
        results1 = aggregate.run_all_checks("問題のあるテキスト。。。")
        results2 = aggregate.run_all_checks("正常なテキストです。")

        # Then
        assert results1.total_issues() > 0
        assert results2.total_issues() == 0
