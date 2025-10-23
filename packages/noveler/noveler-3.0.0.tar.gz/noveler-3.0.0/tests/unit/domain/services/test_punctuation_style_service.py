"""Tests.tests.unit.domain.services.test_punctuation_style_service
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

from noveler.domain.services.punctuation_style_service import PunctuationStyleService


def test_punctuation_style_findings() -> None:
    svc = PunctuationStyleService()
    lines = [
        "これは…奇数…のテスト…",  # odd count of ellipsis (3)
        "これは...",  # ascii dots style
        "ダッシュ—のテスト",  # wrong dash
        "正しい……と――の行",  # correct styles should not report
    ]
    findings = svc.analyze_lines(lines)
    kinds = [f.kind for f in findings]
    assert "ellipsis_odd_count" in kinds
    assert "ellipsis_style" in kinds
    assert "dash_style" in kinds
    # No finding for correct line
    assert all(f.line_index != 4 for f in findings)
