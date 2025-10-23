"""Domain.services.speech_style_checker
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""話し方チェッカー

話し方(敬語・丁寧語など)の一貫性をチェックする専門クラス。
"""


from typing import TYPE_CHECKING, Protocol

from noveler.domain.services.attribute_checker_base import AttributeChecker

if TYPE_CHECKING:
    from noveler.domain.value_objects.consistency_violation import ConsistencyViolation


class CheckContext(Protocol):
    """チェックコンテキストのプロトコル"""

    expected_value: str

    def is_character_mentioned(self) -> bool:
        """キャラクターが言及されているか確認"""
        ...

    def extract_speech(self) -> str | None:
        """セリフを抽出"""
        ...


class SpeechStyleChecker(AttributeChecker):
    """話し方の一貫性チェッカー"""

    def check(self, context: CheckContext) -> ConsistencyViolation | None:
        """話し方の一貫性をチェック"""
        if not context.is_character_mentioned():
            return None

        return self._check_polite_speech(context)

    def _check_polite_speech(self, context: CheckContext) -> ConsistencyViolation | None:
        """丁寧語の使用をチェック"""
        if context.expected_value != "丁寧語":
            return None

        speech = context.extract_speech()
        if not speech:
            return None

        return self._analyze_speech_style(context, speech)

    def _analyze_speech_style(self, context: CheckContext, speech: str) -> ConsistencyViolation | None:
        """セリフの敬語レベルを分析"""
        polite_markers = ["です", "ます", "ございます"]
        casual_markers = ["!", "だ", "よ"]

        has_polite = any(marker in speech for marker in polite_markers)
        has_casual = any(marker in speech for marker in casual_markers)

        # 丁寧語が期待されているのにカジュアルな表現がある場合
        if not has_polite and has_casual:
            return self._create_violation(context, "speech_style", speech)

        return None
