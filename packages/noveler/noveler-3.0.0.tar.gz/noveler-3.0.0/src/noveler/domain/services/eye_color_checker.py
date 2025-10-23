"""Domain.services.eye_color_checker
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""瞳の色チェッカー

瞳の色の一貫性をチェックする専門クラス。
"""


from typing import TYPE_CHECKING

from noveler.domain.services.attribute_checker_base import AttributeChecker
from noveler.domain.value_objects.check_context import CheckContext

if TYPE_CHECKING:
    from noveler.domain.value_objects.consistency_violation import ConsistencyViolation


class EyeColorChecker(AttributeChecker):
    """瞳の色の一貫性チェッカー"""

    def check(self, context: CheckContext) -> ConsistencyViolation | None:
        """瞳の色の一貫性をチェック"""
        if not context.contains_keywords(["瞳", "目"]):
            return None

        return self._detect_eye_color_mismatch(context)

    def _detect_eye_color_mismatch(self, context: CheckContext) -> ConsistencyViolation | None:
        """瞳の色の不一致を検出"""
        # 茶色の瞳のチェック
        if context.contains_keywords(["茶色い"]) and context.expected_value == "黒":
            return self._create_violation(context, "eye_color", "茶色い")

        # 青い瞳のチェック
        if context.contains_keywords(["青い"]) and context.expected_value in ["黒", "茶色"]:
            return self._create_violation(context, "eye_color", "青い")

        return None
