"""Tests.tests.unit.domain.services.test_readability_analysis_service
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

from noveler.domain.services.readability_analysis_service import ReadabilityAnalysisService


def test_readability_analysis_detects_long_sentence() -> None:
    service = ReadabilityAnalysisService()
    content = "これは短い文です。" + "長い文" * 30 + "。"

    result = service.analyze(content)

    assert any(f.issue_type == "long_sentence" for f in result.issues)
    assert result.score < 100.0


def test_readability_analysis_respects_aspects() -> None:
    service = ReadabilityAnalysisService()
    content = "煩瑣な語彙があります。"

    result = service.analyze(content, aspects=["sentence_length"])
    assert all(f.issue_type != "complex_vocabulary" for f in result.issues)


def test_readability_analysis_returns_average_sentence_length() -> None:
    service = ReadabilityAnalysisService()
    content = "短文です。" * 5

    result = service.analyze(content)

    assert result.average_sentence_length is not None
