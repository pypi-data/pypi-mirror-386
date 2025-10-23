#!/usr/bin/env python3
"""A31修正結果値オブジェクト

SPEC-QUALITY-001に基づく修正結果の表現。
修正の詳細情報と成果を記録。
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FixResult:
    """修正結果値オブジェクト

    単一チェックリスト項目に対する修正結果を記録。
    修正内容、スコア変化、適用状況を保持。
    """

    item_id: str
    fix_applied: bool
    fix_type: str
    changes_made: list[str]
    before_score: float
    after_score: float

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self._validate_result()

    def _validate_result(self) -> None:
        """結果の妥当性検証"""
        if not self.item_id:
            msg = "item_idは必須です"
            raise ValueError(msg)

        if self.before_score < 0 or self.after_score < 0:
            msg = "スコアは0以上である必要があります"
            raise ValueError(msg)

        if self.fix_applied and not self.changes_made:
            msg = "修正が適用された場合、changes_madeは空であってはいけません"
            raise ValueError(msg)

        if not self.fix_applied and self.changes_made:
            msg = "修正が適用されていない場合、changes_madeは空である必要があります"
            raise ValueError(msg)

    def get_score_improvement(self) -> float:
        """スコア改善値の取得

        Returns:
            float: 改善スコア(正数は改善、負数は悪化)
        """
        return self.after_score - self.before_score

    def get_improvement_percentage(self) -> float:
        """改善率の計算

        Returns:
            float: 改善率(%)、0除算の場合は0.0
        """
        if self.before_score == 0:
            return 0.0 if self.after_score == 0 else 100.0

        return ((self.after_score - self.before_score) / self.before_score) * 100

    def is_significant_improvement(self, threshold: float = 5.0) -> bool:
        """有意な改善かの判定

        Args:
            threshold: 有意な改善の閾値(デフォルト5点)

        Returns:
            bool: 有意な改善の場合True
        """
        return self.get_score_improvement() >= threshold

    def get_changes_count(self) -> int:
        """変更箇所数の取得

        Returns:
            int: 実施された変更の数
        """
        return len(self.changes_made)

    def get_fix_category(self) -> str:
        """修正カテゴリの取得

        Returns:
            str: 修正タイプから推定されるカテゴリ
        """
        category_map = {
            "format_indentation": "フォーマット",
            "symbol_unification": "記号統一",
            "spelling_correction": "誤字修正",
            "dialogue_balance": "会話バランス",
            "character_consistency": "キャラクター整合性",
            "terminology_check": "用語統一",
            "quality_improvement": "品質向上",
        }
        return category_map.get(self.fix_type, "その他")

    def get_summary(self) -> str:
        """修正結果のサマリー取得

        Returns:
            str: 修正結果の要約文
        """
        if not self.fix_applied:
            return f"{self.item_id}: 修正適用なし"

        improvement = self.get_score_improvement()
        changes_count = self.get_changes_count()

        return (
            f"{self.item_id}: {self.get_fix_category()} "
            f"{changes_count}箇所修正 "
            f"({self.before_score:.1f}→{self.after_score:.1f}, "
            f"+{improvement:.1f}点)"
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換

        Returns:
            Dict[str, Any]: 修正結果データの辞書表現
        """
        return {
            "item_id": self.item_id,
            "fix_applied": self.fix_applied,
            "fix_type": self.fix_type,
            "changes_made": self.changes_made.copy(),
            "before_score": self.before_score,
            "after_score": self.after_score,
            "score_improvement": self.get_score_improvement(),
            "improvement_percentage": self.get_improvement_percentage(),
            "changes_count": self.get_changes_count(),
            "fix_category": self.get_fix_category(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FixResult":
        """辞書からの復元

        Args:
            data: 修正結果データの辞書

        Returns:
            FixResult: 復元された修正結果インスタンス
        """
        return cls(
            item_id=data["item_id"],
            fix_applied=data["fix_applied"],
            fix_type=data["fix_type"],
            changes_made=data["changes_made"],
            before_score=data["before_score"],
            after_score=data["after_score"],
        )

    @classmethod
    def create_successful_fix(
        cls, item_id: str, fix_type: str, changes_made: list[str], before_score: float, after_score: float
    ) -> "FixResult":
        """成功した修正結果の作成

        Args:
            item_id: 項目ID
            fix_type: 修正タイプ
            changes_made: 実施した変更のリスト
            before_score: 修正前スコア
            after_score: 修正後スコア

        Returns:
            FixResult: 成功した修正結果
        """
        return cls(
            item_id=item_id,
            fix_applied=True,
            fix_type=fix_type,
            changes_made=changes_made,
            before_score=before_score,
            after_score=after_score,
        )

    @classmethod
    def create_failed_fix(cls, item_id: str, fix_type: str, current_score: float) -> "FixResult":
        """失敗した修正結果の作成

        Args:
            item_id: 項目ID
            fix_type: 修正タイプ
            current_score: 現在のスコア

        Returns:
            FixResult: 失敗した修正結果
        """
        return cls(
            item_id=item_id,
            fix_applied=False,
            fix_type=fix_type,
            changes_made=[],
            before_score=current_score,
            after_score=current_score,
        )
