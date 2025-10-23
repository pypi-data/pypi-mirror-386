"""Domain.writing.value_objects.writing_duration
Where: Domain value object representing writing durations.
What: Stores timing information for sessions and writing activities.
Why: Enables analysis of writing cadence and productivity.
"""

from __future__ import annotations

"""執筆時間を表す値オブジェクト"""


from dataclasses import dataclass

@dataclass(frozen=True)
class WritingDuration:
    """執筆時間を表す値オブジェクト(分単位)."""

    minutes: int

    def __post_init__(self) -> None:
        if not isinstance(self.minutes, int):
            raise TypeError("執筆時間は整数である必要があります")
        if self.minutes < 0:
            raise ValueError("執筆時間は0以上である必要があります")

    def to_hours_and_minutes(self) -> tuple[int, int]:
        """時間と分に変換."""
        hours = self.minutes // 60
        remaining_minutes = self.minutes % 60
        return hours, remaining_minutes

    def __str__(self) -> str:
        hours, minutes = self.to_hours_and_minutes()
        if hours > 0:
            return f"{hours}時間{minutes}分"
        return f"{minutes}分"

    def __add__(self, other: "WritingDuration") -> "WritingDuration":
        """執筆時間を加算."""
        if not isinstance(other, WritingDuration):
            return NotImplemented
        return WritingDuration(self.minutes + other.minutes)
