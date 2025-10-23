#!/usr/bin/env python3
"""A31評価結果値オブジェクト

SPEC-QUALITY-001に基づく評価結果の表現。
個別チェックリスト項目の評価情報を保持。
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvaluationResult:
    """評価結果値オブジェクト

    単一チェックリスト項目に対する評価結果を記録。
    スコア、閾値、判定結果、詳細情報を保持。
    """

    item_id: str
    current_score: float
    threshold_value: float
    passed: bool
    details: dict[str, Any]

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self._validate_result()

    def _validate_result(self) -> None:
        """結果の妥当性検証"""
        if not self.item_id:
            msg = "item_idは必須です"
            raise ValueError(msg)

        if self.current_score < 0:
            msg = "current_scoreは0以上である必要があります"
            raise ValueError(msg)

        if not isinstance(self.details, dict):
            msg = "detailsは辞書である必要があります"
            raise TypeError(msg)

    def get_score_gap(self) -> float:
        """閾値との差分を取得

        Returns:
            float: 閾値との差分(正数は閾値超過、負数は不足)
        """
        return self.current_score - self.threshold_value

    def get_pass_margin(self) -> float:
        """合格マージンの取得

        Returns:
            float: 合格マージン(正数は余裕、負数は不足)
        """
        if self.passed:
            return abs(self.get_score_gap())
        return -abs(self.get_score_gap())

    def needs_improvement(self) -> bool:
        """改善が必要かの判定

        Returns:
            bool: 改善が必要な場合True
        """
        return not self.passed

    def is_critical_failure(self, critical_threshold: float = 50.0) -> bool:
        """重大な失敗かの判定

        Args:
            critical_threshold: 重大失敗の閾値

        Returns:
            bool: 重大な失敗の場合True
        """
        return not self.passed and self.current_score < critical_threshold

    def get_improvement_needed(self) -> float:
        """必要な改善量の計算

        Returns:
            float: 閾値到達に必要な改善点数(0以下は改善不要)
        """
        if self.passed:
            return 0.0

        return self.threshold_value - self.current_score

    def get_evaluation_grade(self) -> str:
        """評価グレードの取得

        Returns:
            str: 評価グレード("A", "B", "C", "D", "F")
        """
        if self.current_score >= 90:
            return "A"
        if self.current_score >= 80:
            return "B"
        if self.current_score >= 70:
            return "C"
        if self.current_score >= 60:
            return "D"
        return "F"

    def get_status_summary(self) -> str:
        """状態サマリーの取得

        Returns:
            str: 評価状態の要約文
        """
        status = "合格" if self.passed else "不合格"
        grade = self.get_evaluation_grade()
        gap = self.get_score_gap()

        if self.passed:
            return f"{status} (グレード: {grade}, +{gap:.1f}点)"
        return f"{status} (グレード: {grade}, {gap:.1f}点)"

    def has_error(self) -> bool:
        """評価エラーの有無チェック

        Returns:
            bool: エラーが含まれている場合True
        """
        return "error" in self.details

    def get_error_message(self) -> str:
        """エラーメッセージの取得

        Returns:
            str: エラーメッセージ(エラーがない場合は空文字)
        """
        return self.details.get("error", "")

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換

        Returns:
            Dict[str, Any]: 評価結果データの辞書表現
        """
        return {
            "item_id": self.item_id,
            "current_score": self.current_score,
            "threshold_value": self.threshold_value,
            "passed": self.passed,
            "details": self.details.copy(),
            "score_gap": self.get_score_gap(),
            "evaluation_grade": self.get_evaluation_grade(),
            "needs_improvement": self.needs_improvement(),
            "improvement_needed": self.get_improvement_needed(),
            "status_summary": self.get_status_summary(),
            "has_error": self.has_error(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationResult":
        """辞書からの復元

        Args:
            data: 評価結果データの辞書

        Returns:
            EvaluationResult: 復元された評価結果インスタンス
        """
        return cls(
            item_id=data["item_id"],
            current_score=data["current_score"],
            threshold_value=data["threshold_value"],
            passed=data["passed"],
            details=data["details"],
        )

    @classmethod
    def create_passed_result(
        cls, item_id: str, current_score: float, threshold_value: float, details: dict[str, Any] | None = None
    ) -> "EvaluationResult":
        """合格結果の作成

        Args:
            item_id: 項目ID
            current_score: 現在スコア
            threshold_value: 閾値
            details: 詳細情報

        Returns:
            EvaluationResult: 合格評価結果
        """
        if details is None:
            details: dict[str, Any] = {}

        return cls(
            item_id=item_id, current_score=current_score, threshold_value=threshold_value, passed=True, details=details
        )

    @classmethod
    def create_failed_result(
        cls, item_id: str, current_score: float, threshold_value: float, details: dict[str, Any] | None = None
    ) -> "EvaluationResult":
        """不合格結果の作成

        Args:
            item_id: 項目ID
            current_score: 現在スコア
            threshold_value: 閾値
            details: 詳細情報

        Returns:
            EvaluationResult: 不合格評価結果
        """
        if details is None:
            details: dict[str, Any] = {}

        return cls(
            item_id=item_id, current_score=current_score, threshold_value=threshold_value, passed=False, details=details
        )

    @classmethod
    def create_error_result(cls, item_id: str, error_message: str) -> "EvaluationResult":
        """エラー結果の作成

        Args:
            item_id: 項目ID
            error_message: エラーメッセージ

        Returns:
            EvaluationResult: エラー評価結果
        """
        return cls(
            item_id=item_id, current_score=0.0, threshold_value=0.0, passed=False, details={"error": error_message}
        )
