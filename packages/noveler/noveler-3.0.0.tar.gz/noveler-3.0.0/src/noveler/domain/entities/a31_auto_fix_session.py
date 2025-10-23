#!/usr/bin/env python3

"""Domain.entities.a31_auto_fix_session
Where: Domain entity modelling an A31 auto-fix session.
What: Tracks session parameters, progress, and outcomes.
Why: Enables consistent handling of A31 auto-fix processes.
"""

from __future__ import annotations

"""A31自動修正セッション エンティティ(DDD実装)

A31チェックリストの自動修正プロセスを管理するドメインエンティティ。
修正レベル、対象項目、実行結果を統合管理し、ビジネスルールを適用。
"""


import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

from noveler.domain.value_objects.a31_fix_level import FixLevel
from noveler.domain.value_objects.a31_fix_result import FixResult
from noveler.domain.value_objects.a31_session_id import SessionId
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.project_time import project_now


@dataclass
class A31AutoFixSession:
    """A31自動修正セッション

    自動修正プロセスの状態管理と実行結果を保持するエンティティ。
    修正レベルに応じた適用範囲の制御とビジネスルールを実装。
    """

    session_id: SessionId
    project_name: str
    episode_number: EpisodeNumber
    fix_level: FixLevel
    items_to_fix: list[str]
    created_at: datetime = field(default_factory=project_now)
    completed_at: datetime | None = None
    fix_results: list[FixResult] = field(default_factory=list)
    is_completed: bool = False

    @classmethod
    def create(
        cls,
        project_name: str,
        episode_number: int,
        fix_level: FixLevel,
        items_to_fix: list[str] | None = None,
    ) -> A31AutoFixSession:
        """新規セッション作成

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            fix_level: 修正レベル
            items_to_fix: 修正対象項目ID(Noneの場合は修正レベルに応じて決定)

        Returns:
            A31AutoFixSession: 新規作成されたセッション
        """
        session_id = SessionId(str(uuid.uuid4()))
        episode_num = EpisodeNumber(episode_number)

        # 修正対象項目の決定(Noneの場合は修正レベルに応じて自動決定)
        if items_to_fix is None:
            items_to_fix = cls._determine_fixable_items(fix_level)

        return cls(
            session_id=session_id,
            project_name=project_name,
            episode_number=episode_num,
            fix_level=fix_level,
            items_to_fix=items_to_fix,
        )

    def add_fix_result(self, fix_result: FixResult) -> None:
        """修正結果を追加

        Args:
            fix_result: 修正結果
        """
        if self.is_completed:
            msg = "セッション完了後は修正結果を追加できません"
            raise ValueError(msg)

        # 重複チェック
        existing_item_ids = {result.item_id for result in self.fix_results}
        if fix_result.item_id in existing_item_ids:
            msg = f"項目 {fix_result.item_id} の修正結果は既に追加済みです"
            raise ValueError(msg)

        self.fix_results.append(fix_result)

    def complete_session(self) -> None:
        """セッション完了

        セッションを完了状態にマークし、完了時刻を記録。
        """
        if self.is_completed:
            msg = "セッションは既に完了しています"
            raise ValueError(msg)

        self.is_completed = True
        self.completed_at = project_now()

    def get_successful_fixes(self) -> list[FixResult]:
        """成功した修正結果を取得

        Returns:
            list[FixResult]: 成功した修正結果のリスト
        """
        return [result for result in self.fix_results if result.success]

    def get_failed_fixes(self) -> list[FixResult]:
        """失敗した修正結果を取得

        Returns:
            list[FixResult]: 失敗した修正結果のリスト
        """
        return [result for result in self.fix_results if not result.success]

    def get_completion_rate(self) -> float:
        """修正完了率を計算

        Returns:
            float: 修正完了率(0.0~1.0)
        """
        if not self.items_to_fix:
            return 1.0

        successful_count = len(self.get_successful_fixes())
        return successful_count / len(self.items_to_fix)

    def get_session_summary(self) -> dict[str, Any]:
        """セッションサマリーを取得

        Returns:
            dict[str, Any]: セッション情報のサマリー
        """
        successful_fixes = self.get_successful_fixes()
        failed_fixes = self.get_failed_fixes()

        return {
            "session_id": self.session_id.value,
            "project_name": self.project_name,
            "episode_number": self.episode_number.value,
            "fix_level": self.fix_level.value,
            "total_items": len(self.items_to_fix),
            "successful_fixes": len(successful_fixes),
            "failed_fixes": len(failed_fixes),
            "completion_rate": self.get_completion_rate(),
            "is_completed": self.is_completed,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "successful_item_ids": [result.item_id for result in successful_fixes],
            "failed_item_ids": [result.item_id for result in failed_fixes],
        }

    @staticmethod
    def _determine_fixable_items(fix_level: FixLevel) -> list[str]:
        """修正レベルに応じて修正可能項目を決定

        Args:
            fix_level: 修正レベル

        Returns:
            list[str]: 修正対象項目IDのリスト
        """
        # Safe レベル: フォーマット系のみ
        safe_items = [
            "A31-045",  # 段落字下げ
            "A31-035",  # 記号統一
        ]

        # Standard レベル: Safe + 軽微な内容調整
        standard_items = safe_items + [
            "A31-044",  # 用語統一
        ]

        # Interactive レベル: Standard + ユーザー確認必要項目
        interactive_items = standard_items + [
            "A31-033",  # キャラクター口調(部分的)
        ]

        if fix_level == FixLevel.SAFE:
            return safe_items
        if fix_level == FixLevel.STANDARD:
            return standard_items
        if fix_level == FixLevel.INTERACTIVE:
            return interactive_items
        return []
