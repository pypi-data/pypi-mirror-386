"""Tests.tests.unit.domain.services.test_sentence_run_analysis_service
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

from noveler.domain.services.sentence_run_analysis_service import SentenceRunAnalysisService


def test_consecutive_runs_long_and_short() -> None:
    svc = SentenceRunAnalysisService()
    sentences = [
        "あいうえお" * 10,  # long (50)
        "かきくけこ" * 10,  # long
        "さしすせそ" * 10,  # long (3連)
        "たちつ",  # short
        "なにぬ",  # short (2連、しきい値未満なら除外)
        "はひふへほま",  # mid（6文字でshort閾値超え）
    ]
    res = svc.find_consecutive_runs(sentences, long_len=45, short_len=5, long_thr=3, short_thr=3)
    kinds = [r.kind for r in res]
    assert kinds == ["long"], f"expected only long run >=3, got {kinds}"
    assert res[0].count == 3 and res[0].start_sentence_index == 0
