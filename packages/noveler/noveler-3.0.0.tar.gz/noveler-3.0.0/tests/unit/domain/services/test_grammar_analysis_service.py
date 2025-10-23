"""Tests.tests.unit.domain.services.test_grammar_analysis_service
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

from noveler.domain.services.grammar_analysis_service import GrammarAnalysisService


def test_grammar_analysis_detects_typo() -> None:
    service = GrammarAnalysisService()
    result = service.analyze("いいえ、そうではありません。")
    assert any(f.issue_type == "typo" for f in result.issues)


def test_grammar_analysis_filters_types() -> None:
    service = GrammarAnalysisService()
    result = service.analyze("いいえ。", check_types=["punctuation"])
    assert all(f.issue_type == "punctuation" for f in result.issues)


def test_grammar_analysis_score_reduces_with_issues() -> None:
    service = GrammarAnalysisService()
    result = service.analyze("出来る。できる。")
    assert result.score < 100.0
