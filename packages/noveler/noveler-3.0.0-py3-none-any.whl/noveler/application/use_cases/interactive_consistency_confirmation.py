#!/usr/bin/env python3
"""インタラクティブ整合性確認
ユーザーに整合性更新の承認を求める
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConsistencyConfirmationResult:
    """整合性確認結果"""

    approved: bool
    update_episode_status: bool = True
    update_foreshadowing_notes: bool = True
    message: str = ""


class InteractiveConsistencyConfirmation:
    """インタラクティブ整合性確認"""

    def confirm_consistency_updates(
        self, impact_summary: dict[str, Any], user_input_handler: Callable[[str], str]
    ) -> ConsistencyConfirmationResult:
        """整合性更新の確認をユーザーに求める"""

        # 影響サマリーを表示
        affected_episodes = impact_summary.get("affected_episodes", 0)
        affected_foreshadowing = impact_summary.get("affected_foreshadowing", 0)

        confirmation_message = f"""
📊 プロットバージョンアップの影響範囲:
   - 影響を受ける話数: {affected_episodes}話
   - 確認が必要な伏線: {affected_foreshadowing}件

🔄 実行される整合性更新:
   - 話数管理: 影響話数を「要リビジョン」に変更
   - 伏線管理: レビュー必要項目をマーク

整合性更新を実行しますか? [Y/n]: """

        response = user_input_handler(confirmation_message)

        if response.lower() in ["n", "no"]:
            return ConsistencyConfirmationResult(
                approved=False,
                message="整合性更新をスキップしました",
            )

        # 個別確認(詳細制御が必要な場合)
        update_episode_status = True
        update_foreshadowing_notes = True

        if affected_episodes > 10:  # 大規模変更の場合は個別確認:
            episode_response = user_input_handler(
                f"話数管理を更新しますか?({affected_episodes}話が影響) [Y/n]: ",
            )

            update_episode_status = episode_response.lower() not in ["n", "no"]

        if affected_foreshadowing > 0:
            foreshadow_response = user_input_handler(
                f"伏線管理レビューを記録しますか?({affected_foreshadowing}件が影響) [Y/n]: ",
            )

            update_foreshadowing_notes = foreshadow_response.lower() not in ["n", "no"]

        return ConsistencyConfirmationResult(
            approved=True,
            update_episode_status=update_episode_status,
            update_foreshadowing_notes=update_foreshadowing_notes,
            message="すべての整合性更新が承認されました",
        )
