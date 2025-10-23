"""一貫性違反値オブジェクト

キャラクター描写の一貫性違反を表す値オブジェクト。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConsistencyViolation:
    """一貫性違反

    キャラクター設定と実際の描写の不一致を表す。
    """

    character_name: str
    attribute: str
    expected: str
    actual: str
    line_number: int
    context: str | None = None

    def __post_init__(self) -> None:
        """初期化後の検証"""
        if not self.character_name:
            msg = "character_nameは必須です"
            raise ValueError(msg)
        if not self.attribute:
            msg = "attributeは必須です"
            raise ValueError(msg)
        if self.line_number < 1:
            msg = "line_numberは1以上である必要があります"
            raise ValueError(msg)

    @property
    def severity(self) -> str:
        """違反の重要度を判定

        Returns:
            "critical", "major", "minor"のいずれか
        """
        # 重要な属性の定義
        critical_attributes = ["gender", "age", "name"]
        major_attributes = ["hair_color", "eye_color", "personality", "speech_style"]

        if self.attribute in critical_attributes:
            return "critical"
        if self.attribute in major_attributes:
            return "major"
        return "minor"

    def get_correction_suggestion(self) -> "CorrectionSuggestion":
        """修正提案を生成

        Returns:
            修正提案オブジェクト
        """
        if not self.context:
            explanation = f"キャラクター設定に合わせて「{self.actual}」を「{self.expected}」に修正"
            return CorrectionSuggestion(original="", corrected="", explanation=explanation)

        # コンテキスト内の実際の値を期待値で置換
        corrected = self.context.replace(self.actual, self.expected)
        explanation = f"キャラクター設定に合わせて「{self.actual}」を「{self.expected}」に修正"

        return CorrectionSuggestion(original=self.context, corrected=corrected, explanation=explanation)

    def to_dict(self) -> dict:
        """辞書形式に変換

        Returns:
            違反情報の辞書
        """
        return {
            "character_name": self.character_name,
            "attribute": self.attribute,
            "expected": self.expected,
            "actual": self.actual,
            "line_number": self.line_number,
            "context": self.context,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class CorrectionSuggestion:
    """修正提案

    一貫性違反に対する修正案を表す。
    """

    original: str
    corrected: str
    explanation: str

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {"original": self.original, "corrected": self.corrected, "explanation": self.explanation}
