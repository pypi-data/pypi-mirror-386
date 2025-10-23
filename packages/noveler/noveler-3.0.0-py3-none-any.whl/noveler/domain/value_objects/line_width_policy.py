"""Domain.value_objects.line_width_policy
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LineWidthPolicy:
    """行幅検出のポリシー（DDD: 値オブジェクト）

    - warn: 注意喚起のしきい値
    - critical: 強い警告のしきい値
    - skip_dialogue_lines: 会話行（「…」/『…』）を検出対象外にする
    """

    warn: int
    critical: int
    skip_dialogue_lines: bool = True

    def classify_length(self, length: int) -> str | None:
        """長さから深刻度を分類。しきい値未満はNone。"""
        if length <= self.warn:
            return None
        return "high" if length > self.critical else "medium"

    def is_dialogue_line(self, line: str) -> bool:
        if not self.skip_dialogue_lines:
            return False
        try:
            line = line or ""
            # 開閉が同一行に含まれているケースを会話行とみなす
            if ("「" in line and "」" in line) or ("『" in line and "』" in line):
                return True
        except Exception:  # 保守的に検出対象とする
            return False
        return False
