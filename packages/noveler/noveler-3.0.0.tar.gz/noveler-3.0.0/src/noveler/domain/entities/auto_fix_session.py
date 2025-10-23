#!/usr/bin/env python3
"""自動修正セッションエンティティ

SPEC-QUALITY-001に基づく自動修正セッションの管理。
修正結果の追跡と分析機能を提供。
"""

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.a31_fix_level import FixLevel
from noveler.domain.value_objects.a31_fix_result import FixResult
from noveler.domain.value_objects.a31_session_id import SessionId


@dataclass
class AutoFixSession:
    """自動修正セッションエンティティ

    単一エピソードファイルに対する自動修正処理を管理。
    修正結果の追跡、分析、完了判定を行う。
    """

    session_id: SessionId
    target_file: Path
    fix_level: FixLevel
    items_to_fix: list[str]
    results: list[FixResult] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    completed: bool = False

    def add_result(self, fix_result: FixResult) -> None:
        """修正結果の追加

        Args:
            fix_result: 追加する修正結果
        """
        if fix_result.item_id not in self.items_to_fix:
            msg = f"修正対象外の項目です: {fix_result.item_id}"
            raise ValueError(msg)

        # 既存の結果があれば置き換え
        self.results = [r for r in self.results if r.item_id != fix_result.item_id]
        self.results.append(fix_result)

    def get_successful_fixes(self) -> list[FixResult]:
        """成功した修正の取得

        Returns:
            list[FixResult]: 成功した修正結果のリスト
        """
        return [result for result in self.results if result.fix_applied]

    def get_failed_fixes(self) -> list[FixResult]:
        """失敗した修正の取得

        Returns:
            list[FixResult]: 失敗した修正結果のリスト
        """
        return [result for result in self.results if not result.fix_applied]

    def calculate_overall_improvement(self) -> float:
        """全体的な改善度の計算

        Returns:
            float: 平均改善点数
        """
        if not self.results:
            return 0.0

        improvements = [result.after_score - result.before_score for result in self.results]

        return sum(improvements) / len(improvements)

    def is_completed(self) -> bool:
        """セッション完了判定

        Returns:
            bool: 全ての対象項目に結果が記録されている場合True
        """
        processed_items = {result.item_id for result in self.results}
        target_items = set(self.items_to_fix)
        return processed_items == target_items

    def get_episode_info(self) -> tuple[int, str]:
        """ファイルパスからエピソード情報を抽出

        Returns:
            Tuple[int, str]: (エピソード番号, エピソードタイトル)

        Raises:
            ValueError: ファイル名が期待する形式でない場合
        """
        filename = self.target_file.stem
        # 第001話_タイトル.md の形式を想定
        match = re.match(r"第(\d+)話_(.+)", filename)
        if match:
            episode_number = int(match.group(1))
            episode_title = match.group(2)
            return episode_number, episode_title

        msg = f"Invalid episode filename format: {filename}"
        raise ValueError(msg)

    def get_completion_rate(self) -> float:
        """完了率の計算

        Returns:
            float: 完了率(0.0-1.0)
        """
        if not self.items_to_fix:
            return 1.0

        return len(self.results) / len(self.items_to_fix)

    def get_success_rate(self) -> float:
        """成功率の計算

        Returns:
            float: 成功率(0.0-1.0)
        """
        if not self.results:
            return 0.0

        successful_count = len(self.get_successful_fixes())
        return successful_count / len(self.results)

    def get_items_remaining(self) -> list[str]:
        """未処理項目の取得

        Returns:
            list[str]: 未処理の項目IDリスト
        """
        processed_items = {result.item_id for result in self.results}
        return [item_id for item_id in self.items_to_fix if item_id not in processed_items]

    def complete(self) -> None:
        """セッションを完了としてマーク"""
        self.completed = True
        self.end_time = time.time()

    def get_duration(self) -> float:
        """セッション実行時間を取得

        Returns:
            float: 実行時間(秒)
        """
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    def get_successful_fixes_count(self) -> int:
        """成功した修正の数を取得

        Returns:
            int: 成功した修正の数
        """
        return len(self.get_successful_fixes())

    def get_failed_fixes_count(self) -> int:
        """失敗した修正の数を取得

        Returns:
            int: 失敗した修正の数
        """
        return len(self.get_failed_fixes())

    def get_total_improvement(self) -> float:
        """総改善点数を取得

        Returns:
            float: 総改善点数
        """
        return sum(result.after_score - result.before_score for result in self.results if result.fix_applied)

    def get_summary_stats(self) -> dict[str, Any]:
        """サマリー統計の取得

        Returns:
            Dict[str, Any]: セッション統計情報
        """
        return {
            "session_id": str(self.session_id),
            "target_file": str(self.target_file),
            "fix_level": self.fix_level.value,
            "total_items": len(self.items_to_fix),
            "processed_items": len(self.results),
            "successful_fixes": len(self.get_successful_fixes()),
            "failed_fixes": len(self.get_failed_fixes()),
            "completion_rate": self.get_completion_rate(),
            "success_rate": self.get_success_rate(),
            "overall_improvement": self.calculate_overall_improvement(),
            "is_completed": self.is_completed(),
        }

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換

        Returns:
            Dict[str, Any]: セッションデータの辞書表現
        """
        return {
            "session_id": str(self.session_id),
            "target_file": str(self.target_file),
            "fix_level": self.fix_level.value,
            "items_to_fix": self.items_to_fix.copy(),
            "results": [result.to_dict() for result in self.results],
            "completion_rate": self.get_completion_rate(),
            "success_rate": self.get_success_rate(),
            "overall_improvement": self.calculate_overall_improvement(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AutoFixSession":
        """辞書からの復元

        Args:
            data: セッションデータの辞書

        Returns:
            AutoFixSession: 復元されたセッションインスタンス
        """
        return cls(
            session_id=SessionId.from_string(data["session_id"]),
            target_file=Path(data["target_file"]),
            fix_level=FixLevel(data["fix_level"]),
            items_to_fix=data["items_to_fix"],
            results=[FixResult.from_dict(result_data) for result_data in data["results"]],
        )
