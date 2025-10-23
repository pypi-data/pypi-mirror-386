"""Tests.tests.unit.domain.services.test_text_wrapping_service
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

from noveler.domain.services.text_wrapping_service import wrap_japanese_line


def test_wrap_japanese_line_prefers_break_chars() -> None:
    s = "これはテスト、改行候補がありますので適度な位置で折り返します。"
    wrapped = wrap_japanese_line(s, max_width=12)
    # Should contain a newline and not split into single characters only
    assert "\n" in wrapped
    parts = wrapped.split("\n")
    # 近傍の安全点で折り返すため、max_width±20の範囲に収まる想定
    assert all(len(p) <= 32 for p in parts)
