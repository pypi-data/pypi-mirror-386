"""Domain.services.personality_checker
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""性格チェッカー

性格の一貫性をチェックする専門クラス。
"""


from typing import TYPE_CHECKING, Protocol

from noveler.domain.services.attribute_checker_base import AttributeChecker

if TYPE_CHECKING:
    from noveler.domain.value_objects.consistency_violation import ConsistencyViolation


class CheckContext(Protocol):
    """チェックコンテキストのプロトコル"""

    expected_value: str

    def contains_keywords(self, keywords: list[str]) -> bool:
        """キーワードを含むか確認"""
        ...


class PersonalityChecker(AttributeChecker):
    """性格の一貫性チェッカー"""

    def check(self, context: CheckContext) -> ConsistencyViolation | None:
        """性格の一貫性をチェック"""
        return self._check_introvert_behavior(context)

    def _check_introvert_behavior(self, context: CheckContext) -> ConsistencyViolation | None:
        """内向的な性格設定との矛盾をチェック"""
        if context.expected_value != "内向的":
            return None

        # 外向的な行動パターンを検出
        extrovert_keywords = ["元気に", "明るく"]
        if context.contains_keywords(extrovert_keywords):
            return self._create_violation(context, "personality", "元気に挨拶")

        return None
