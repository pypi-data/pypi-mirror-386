"""Domain.services.attribute_checker_base
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""属性チェッカー基底クラス

Strategy パターンの基底クラスを定義し、
各属性チェック処理を統一インターフェースで管理する。
"""


from abc import ABC, abstractmethod

from noveler.domain.services.common_validation_patterns import TextContentValidator
from noveler.domain.value_objects.check_context import CheckContext
from noveler.domain.value_objects.consistency_violation import ConsistencyViolation


class AttributeChecker(ABC):
    """属性チェッカーの基底クラス

    Strategy パターンを使用して各属性の
    チェック処理を独立したクラスに分離する。
    共通のバリデーション機能も提供する。
    """

    def __init__(self) -> None:
        self.validator = TextContentValidator()

    @abstractmethod
    def check(self, context: CheckContext) -> ConsistencyViolation | None:
        """属性の一貫性をチェック

        Args:
            context: チェックコンテキスト

        Returns:
            違反が見つかった場合は ConsistencyViolation、
            問題なければ None
        """

    def _create_violation(
        self, context: CheckContext, attribute: str, actual_value: str | None = None
    ) -> ConsistencyViolation:
        """違反オブジェクトを作成するヘルパーメソッド"""
        return ConsistencyViolation(
            character_name=context.character_name,
            attribute=attribute,
            expected=context.expected_value,
            actual=actual_value,
            line_number=context.line_number,
            context=context.get_stripped_line(),
        )
