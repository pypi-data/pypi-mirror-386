"""Tests.tests.unit.domain.services.test_rhythm_analysis_service
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

from noveler.domain.services.rhythm_analysis_service import RhythmAnalysisService
from noveler.domain.value_objects.line_width_policy import LineWidthPolicy


def test_line_width_policy_classification_and_dialogue_skip() -> None:
    svc = RhythmAnalysisService()
    policy = LineWidthPolicy(warn=80, critical=120, skip_dialogue_lines=True)

    lines = [
        "「" + ("あ" * 200) + "」",  # dialogue (skip)
        "い" * 85,  # medium
        "う" * 130,  # high
        "",  # empty
    ]
    res = svc.check_line_width(lines, policy)
    # Should detect only the 2nd and 3rd non-dialogue lines
    assert [r.line_number for r in res] == [2, 3]
    assert res[0].severity == "medium" and res[1].severity == "high"
