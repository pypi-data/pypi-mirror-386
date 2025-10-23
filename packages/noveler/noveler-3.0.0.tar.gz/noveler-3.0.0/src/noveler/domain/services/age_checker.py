"""Domain.services.age_checker
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""年齢チェッカー

年齢の一貫性をチェックする専門クラス。
"""


import re
from typing import TYPE_CHECKING

from noveler.domain.services.attribute_checker_base import AttributeChecker
from noveler.domain.value_objects.check_context import CheckContext

if TYPE_CHECKING:
    from noveler.domain.value_objects.consistency_violation import ConsistencyViolation


class AgeChecker(AttributeChecker):
    """年齢の一貫性チェッカー"""

    def check(self, context: CheckContext) -> ConsistencyViolation | None:
        """年齢の一貫性をチェック"""
        if not (context.contains_keywords(["歳"]) and context.is_character_mentioned()):
            return None

        return self._extract_and_validate_age(context)

    def _extract_and_validate_age(self, context: CheckContext) -> ConsistencyViolation | None:
        """年齢を抽出して検証"""
        age_match = re.search(r"(\\d+)歳", context.line)
        if not age_match:
            return None

        actual_age = age_match.group(1) + "歳"
        if actual_age != context.expected_value:
            return self._create_violation(context, "age", actual_age)

        return None
