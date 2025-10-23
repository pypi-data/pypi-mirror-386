"""Domain.value_objects.consistency_check_result
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""一貫性チェック結果値オブジェクト

エピソードの一貫性チェック結果を表す値オブジェクト。
"""


from dataclasses import dataclass
from typing import TYPE_CHECKING

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from datetime import datetime

    from noveler.domain.value_objects.consistency_violation import ConsistencyViolation

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass(frozen=True)
class ConsistencyCheckResult:
    """一貫性チェック結果

    特定のエピソードに対する一貫性チェックの結果を保持する。
    """

    episode_number: int
    violations: list[ConsistencyViolation]
    checked_at: datetime = None

    def __post_init__(self) -> None:
        """初期化後の処理"""
        if self.checked_at is None:
            object.__setattr__(self, "checked_at", project_now().datetime)

        # violationsを不変にする
        object.__setattr__(self, "violations", tuple(self.violations))

    @property
    def has_violations(self) -> bool:
        """違反があるかどうか"""
        return len(self.violations) > 0

    @property
    def violation_count(self) -> int:
        """違反数を取得"""
        return len(self.violations)

    def get_violations_by_character(self, character_name: str) -> list[ConsistencyViolation]:
        """特定キャラクターの違反を取得

        Args:
            character_name: キャラクター名

        Returns:
            該当する違反のリスト
        """
        return [v for v in self.violations if v.character_name == character_name]

    def get_violations_by_attribute(self, attribute: str) -> list[ConsistencyViolation]:
        """特定属性の違反を取得

        Args:
            attribute: 属性名

        Returns:
            該当する違反のリスト
        """
        return [v for v in self.violations if v.attribute == attribute]

    def get_violations_by_severity(self, severity: str) -> list[ConsistencyViolation]:
        """特定重要度の違反を取得

        Args:
            severity: 重要度(critical, major, minor)

        Returns:
            該当する違反のリスト
        """
        return [v for v in self.violations if v.severity == severity]

    def to_dict(self) -> dict:
        """辞書形式に変換

        Returns:
            結果の辞書表現
        """
        return {
            "episode_number": self.episode_number,
            "violations": [v.to_dict() for v in self.violations],
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
            "violation_count": self.violation_count,
            "has_violations": self.has_violations,
        }
