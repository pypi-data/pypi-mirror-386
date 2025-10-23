"""Domain.services.attribute_checker_factory
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""属性チェッカーファクトリー

Factory パターンを使用して適切な属性チェッカーを生成する。
"""


from typing import TYPE_CHECKING

from noveler.domain.services.age_checker import AgeChecker
from noveler.domain.services.eye_color_checker import EyeColorChecker
from noveler.domain.services.hair_color_checker import HairColorChecker
from noveler.domain.services.personality_checker import PersonalityChecker
from noveler.domain.services.speech_style_checker import SpeechStyleChecker
from noveler.domain.value_objects.check_context import CheckContext

if TYPE_CHECKING:
    from noveler.domain.services.attribute_checker_base import AttributeChecker


class AttributeCheckerFactory:
    """属性チェッカーのファクトリクラス

    Factory パターンを使用して、属性タイプに応じた
    適切なチェッカーインスタンスを生成する。
    """

    @staticmethod
    def create_checker(attribute_type: str) -> AttributeChecker:
        """属性タイプに応じたチェッカーを生成

        Args:
            attribute_type: 属性タイプ(hair_color, eye_color等)

        Returns:
            適切な属性チェッカーインスタンス

        Raises:
            ValueError: 未知の属性タイプの場合
        """
        checker_mapping = {
            "hair_color": HairColorChecker,
            "eye_color": EyeColorChecker,
            "personality": PersonalityChecker,
            "speech_style": SpeechStyleChecker,
            "age": AgeChecker,
        }

        checker_class = checker_mapping.get(attribute_type)
        if not checker_class:
            # デフォルトチェッカーでフォールバック
            return DefaultAttributeChecker(attribute_type)

        return checker_class()


class DefaultAttributeChecker:
    """デフォルト属性チェッカー

    未定義の属性タイプに対するフォールバック実装。
    基本的なパターンマッチングのみ行う。
    """

    def __init__(self, attribute_type: str) -> None:
        self.attribute_type = attribute_type

    def check(self, _context: CheckContext) -> None:
        """基本チェック(現在は何もしない)

        将来的には設定可能なルールエンジンなどを実装予定。
        """
        # 未実装の属性タイプは現在スキップ
        return
