"""Application.use_cases.chapter_consistency_interactive_confirmation
Where: Application use case guiding chapter-level consistency confirmations.
What: Displays impact summaries and collects approvals for chapter update actions.
Why: Keeps chapter adjustments aligned with broader narrative consistency through human confirmation.
"""

from noveler.presentation.shared.shared_utilities import console

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfirmationResult:
    """確認結果"""

    approved: bool
    message: str
    user_comments: str = ""


class ChapterConsistencyInteractiveConfirmation:
    """章別整合性インタラクティブ確認"""

    def confirm_chapter_updates(
        self, chapter_impact: dict[str, Any], input_handler: Callable[[str], str]
    ) -> ConfirmationResult:
        """単一章更新の確認"""
        chapter_name = chapter_impact.get("chapter_name", f"第{chapter_impact['affected_chapter']}章")
        affected_episodes = chapter_impact.get("affected_episodes", 0)
        affected_foreshadowing = chapter_impact.get("affected_foreshadowing", 0)
        console.print(f"\n📊 {chapter_name}の整合性更新")
        console.print(f"   影響話数: {affected_episodes}")
        console.print(f"   影響伏線: {affected_foreshadowing}")
        console.print("\n🔄 実行される更新")
        console.print("   - 話数ステータス")
        console.print("   - 伏線管理")
        response = input_handler(f"\n{chapter_name}の整合性更新を実行しますか? [Y/n]: ")
        if response.lower() in ["y", "yes", ""]:
            comments = input_handler("追加コメント(任意): ")
            return ConfirmationResult(
                approved=True, message=f"{chapter_name}の整合性更新が承認されました", user_comments=comments
            )
        return ConfirmationResult(approved=False, message=f"{chapter_name}の整合性更新がキャンセルされました")

    def confirm_multiple_chapters_updates(
        self, chapters_impact: dict[str, Any], input_handler: Callable[[str], str]
    ) -> ConfirmationResult:
        """複数章更新の確認"""
        affected_chapters = chapters_impact.get("affected_chapters", [])
        total_episodes = chapters_impact.get("total_affected_episodes", 0)
        total_foreshadowing = chapters_impact.get("total_affected_foreshadowing", 0)
        chapter_range = f"第{min(affected_chapters)}-{max(affected_chapters)}章"
        console.print(f"\n📊 {chapter_range}の整合性更新")
        console.print(f"   対象章: {len(affected_chapters)}章 ({', '.join(f'第{ch}章' for ch in affected_chapters)})")
        console.print(f"   影響話数: {total_episodes}")
        console.print(f"   影響伏線: {total_foreshadowing}")
        console.print("\n🔄 実行される更新")
        console.print("   - 各章の話数ステータス")
        console.print("   - 各章の伏線管理")
        response = input_handler("\n複数章の整合性更新を実行しますか? [Y/n]: ")
        if response.lower() in ["y", "yes", ""]:
            comments = input_handler("追加コメント(任意): ")
            return ConfirmationResult(
                approved=True, message=f"{chapter_range}の整合性更新が承認されました", user_comments=comments
            )
        return ConfirmationResult(approved=False, message=f"{chapter_range}の整合性更新がキャンセルされました")

    def confirm_minimal_impact_update(
        self, chapter_impact: dict[str, Any], input_handler: Callable[[str], str]
    ) -> ConfirmationResult:
        """軽微な影響時の簡易確認"""
        chapter_name = chapter_impact.get("chapter_name", f"第{chapter_impact['affected_chapter']}章")
        response = input_handler(f"\n{chapter_name}の軽微な変更を記録しますか? [Y/n]: ")
        if response.lower() in ["y", "yes", ""]:
            return ConfirmationResult(approved=True, message=f"{chapter_name}の変更を記録しました")
        return ConfirmationResult(approved=False, message=f"{chapter_name}の変更記録をスキップしました")
