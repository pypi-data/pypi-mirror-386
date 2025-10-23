"""Domain.services.hair_color_checker
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""髪色チェッカー

髪色の一貫性をチェックする専門クラス。
"""


from typing import TYPE_CHECKING

from noveler.domain.services.attribute_checker_base import AttributeChecker
from noveler.domain.value_objects.check_context import CheckContext

if TYPE_CHECKING:
    from noveler.domain.value_objects.consistency_violation import ConsistencyViolation


class HairColorChecker(AttributeChecker):
    """髪色の一貫性チェッカー"""

    def check(self, context: CheckContext) -> ConsistencyViolation | None:
        """髪色の一貫性をチェック"""
        if not context.contains_keywords(["髪", "ヘア"]):
            return None

        # 代名詞での言及チェック
        violation = self._check_pronoun_reference(context)
        if violation:
            return violation

        # 直接言及チェック
        return self._check_direct_reference(context)

    def _check_pronoun_reference(self, context: CheckContext) -> ConsistencyViolation | None:
        """代名詞での髪色言及をチェック"""
        if not context.contains_keywords(["彼の", "彼女の"]):
            return None

        if not context.is_recent_character_mentioned():
            return None

        return self._detect_hair_color_mismatch(context)

    def _check_direct_reference(self, context: CheckContext) -> ConsistencyViolation | None:
        """直接的な髪色言及をチェック"""
        return self._detect_hair_color_mismatch(context)

    def _detect_hair_color_mismatch(self, context: CheckContext) -> ConsistencyViolation | None:
        """髪色の不一致を検出"""
        color_mappings = {
            "金髪": ["金髪"],
            "茶髪": ["茶髪"],
            "黒髪": ["黒髪"],
        }

        for actual_color, keywords in color_mappings.items():
            if context.contains_keywords(keywords) and actual_color != context.expected_value:
                return self._create_violation(context, "hair_color", actual_color)

        return None
