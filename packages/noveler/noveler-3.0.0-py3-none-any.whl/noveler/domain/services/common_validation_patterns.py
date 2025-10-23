"""Domain.services.common_validation_patterns
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""共通バリデーションパターン

重複するバリデーションロジックを統一し、
DRY原則に従ってコードの重複を削減する。
"""


from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


class TextContentValidator:
    """テキストコンテンツのバリデーター

    各種チェック処理で共通して使用される
    テキスト内容の検証ロジックを統一管理する。
    """

    @staticmethod
    def contains_keywords(text: str, keywords: list[str]) -> bool:
        """指定されたキーワードがテキストに含まれているかチェック"""
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def contains_character_mention(text: str, character_name: str) -> bool:
        """キャラクター名がテキストに含まれているかチェック"""
        return character_name in text

    @staticmethod
    def contains_dialogue(text: str) -> bool:
        """会話(セリフ)が含まれているかチェック"""
        return "「" in text and "」" in text

    @staticmethod
    def extract_dialogue(text: str) -> str | None:
        """セリフ部分を抽出"""
        if not TextContentValidator.contains_dialogue(text):
            return None
        return text[text.index("「") + 1 : text.index("」")]

    @staticmethod
    def contains_action_indicators(text: str) -> bool:
        """アクション要素が含まれているかチェック"""
        action_keywords = ["走る", "歩く", "振り向く", "立ち上がる", "座る", "動く"]
        return TextContentValidator.contains_keywords(text, action_keywords)

    @staticmethod
    def contains_emotion_indicators(text: str) -> bool:
        """感情表現が含まれているかチェック"""
        emotion_keywords = ["嬉しい", "悲しい", "怒る", "驚く", "喜ぶ", "泣く", "笑う"]
        return TextContentValidator.contains_keywords(text, emotion_keywords)


class ConditionalChecker:
    """条件チェッカー

    複数の条件を組み合わせた判定処理を統一管理し、
    複雑な条件式の可読性を向上させる。
    """

    @staticmethod
    def all_conditions(conditions: list[Callable[[], bool]]) -> bool:
        """すべての条件が真であるかチェック"""
        return all(condition() for condition in conditions)

    @staticmethod
    def any_conditions(conditions: list[Callable[[], bool]]) -> bool:
        """いずれかの条件が真であるかチェック"""
        return any(condition() for condition in conditions)

    @staticmethod
    def conditional_increment(condition: bool, current_value: int | float, increment: int | float = 1) -> int | float:
        """条件が真の場合にのみ値を増加"""
        return current_value + increment if condition else current_value


class ScoreCalculationHelper:
    """スコア計算ヘルパー

    各種品質チェックで共通して使用される
    スコア計算ロジックを統一管理する。
    """

    @staticmethod
    def calculate_ratio_score(actual: float, target: float, tolerance: float = 0.1) -> float:
        """比率ベースのスコアを計算

        Args:
            actual: 実際の値
            target: 目標値
            tolerance: 許容誤差(比率)

        Returns:
            0.0-1.0のスコア
        """
        if target == 0:
            return 1.0 if actual == 0 else 0.0

        ratio = actual / target

        # 完全一致時
        if ratio == 1.0:
            return 1.0

        # 許容範囲内
        if 1.0 - tolerance <= ratio <= 1.0 + tolerance:
            # 線形減衰
            deviation = abs(ratio - 1.0)
            return 1.0 - (deviation / tolerance) * 0.2

        # 許容範囲外
        return max(0.0, 1.0 - abs(ratio - 1.0))

    @staticmethod
    def calculate_weighted_average(scores: list[float], weights: list[float]) -> float:
        """重み付き平均を計算

        Args:
            scores: 各項目のスコア
            weights: 各項目の重み

        Returns:
            重み付き平均スコア
        """
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(scores.get(key, 0.0) * weight for key, weight in weights.items())

        return weighted_sum / total_weight

    @staticmethod
    def normalize_score(score: float, min_score: float = 0.0, max_score: float = 1.0) -> float:
        """スコアを指定範囲に正規化"""
        return max(min_score, min(max_score, score))


class ValidationResult:
    """バリデーション結果

    バリデーション処理の結果を統一的に管理する。
    """

    def __init__(self, is_valid: bool, message: str, details: dict[str, Any] | None = None) -> None:
        self.is_valid = is_valid
        self.message = message
        self.details = details or {}

    def __bool__(self) -> bool:
        """真偽値として評価"""
        return self.is_valid

    def add_detail(self, key: str, value: object) -> None:
        """詳細情報を追加"""
        self.details[key] = value

    @classmethod
    def success(cls, message: str) -> ValidationResult:
        """成功結果を作成"""
        return cls(True, message)

    @classmethod
    def failure(cls, message: str, details: dict[str, Any]) -> ValidationResult:
        """失敗結果を作成"""
        return cls(False, message, details)
