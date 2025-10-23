"""Application.use_cases.bidirectional_interactive_confirmation
Where: Application use case handling bidirectional foreshadowing confirmations.
What: Presents impact summaries to the user and gathers approval for forward and reverse checks.
Why: Ensures foreshadowing updates remain consistent through interactive human confirmation.
"""

from noveler.presentation.shared.shared_utilities import console

from contextlib import suppress
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BidirectionalConfirmationResult:
    """双方向確認結果"""

    approved: bool
    include_reverse_check: bool
    message: str
    user_comments: str = ""


class BidirectionalInteractiveConfirmation:
    """双方向伏線インタラクティブ確認

    B20準拠: console_service依存注入対応
    """

    def __init__(self, console_service=None, logger_service=None) -> None:
        """初期化

        Args:
            console_service: コンソールサービス（B20準拠・DI対応）
            logger_service: ロガーサービス（B20準拠・DI対応）
        """
        self._console_service = console_service
        self._logger_service = logger_service

    def _print_to_console(self, message: str) -> None:
        """コンソール出力をDI対応で安全に実行"""

        target_console = self._console_service or console
        with suppress(Exception):
            target_console.print(message)

    def confirm_bidirectional_updates(
        self, impact_data: dict[str, Any], input_handler: Callable[[str], str]
    ) -> BidirectionalConfirmationResult:
        """双方向更新の確認"""
        affected_chapter = impact_data.get("affected_chapter")
        setup_count = impact_data.get("setup_modified_count", 0)
        resolution_count = impact_data.get("resolution_modified_count", 0)
        reverse_check_chapters = impact_data.get("reverse_check_chapters", [])
        impact_summary = impact_data.get("impact_summary", "")
        self._print_to_console("\n🔄 双方向伏線影響分析結果")
        self._print_to_console(f"   {impact_summary}")
        if setup_count > 0:
            self._print_to_console("\n📌 仕込み変更の影響")
            self._print_to_console(f"   - 第{affected_chapter}章で仕込まれた伏線")
            self._print_to_console("   - 影響する回収章の確認が必要")
        if resolution_count > 0:
            self._print_to_console("\n🎯 回収変更の影響")
            self._print_to_console(f"   - 第{affected_chapter}章で回収される伏線")
            self._print_to_console("   - 仕込み章との整合性確認が必要")
        include_reverse = False
        if reverse_check_chapters:
            chapters_str = ", ".join(f"第{ch}章" for ch in sorted(reverse_check_chapters))
            self._print_to_console(f"\n💡 推奨: {chapters_str}の逆方向チェック")
            self._print_to_console("   理由: 影響範囲の整合性確認")
            response = input_handler("\n逆方向チェックも実行しますか? [Y/n]: ")
            include_reverse = response.lower() in ["y", "yes", ""]
        response = input_handler("\n伏線ステータスの更新を実行しますか? [Y/n]: ")
        if response.lower() in ["y", "yes", ""]:
            comments = input_handler("追加コメント(任意): ")
            message_parts = [f"第{affected_chapter}章の伏線ステータスを更新"]
            if include_reverse and reverse_check_chapters:
                chapters_str = ", ".join(f"第{ch}章" for ch in sorted(reverse_check_chapters))
                message_parts.append(f"{chapters_str}の確認を推奨")
            return BidirectionalConfirmationResult(
                approved=True,
                include_reverse_check=include_reverse,
                message=" - ".join(message_parts),
                user_comments=comments,
            )
        return BidirectionalConfirmationResult(
            approved=False, include_reverse_check=False, message=f"第{affected_chapter}章の伏線更新をキャンセルしました"
        )

    def confirm_reverse_check_execution(
        self, chapters: list[int], input_handler: Callable[[str], str]
    ) -> BidirectionalConfirmationResult:
        """逆方向チェックの実行確認"""
        chapters_str = ", ".join(f"第{ch}章" for ch in sorted(chapters))
        console.print("\n🔍 逆方向チェック対象")
        console.print(f"   {chapters_str}")
        console.print("   - これらの章の伏線整合性を確認します")
        console.print("   - 必要に応じて話数ステータスも更新されます")
        response = input_handler("\n逆方向チェックを実行しますか? [Y/n]: ")
        if response.lower() in ["y", "yes", ""]:
            return BidirectionalConfirmationResult(
                approved=True, include_reverse_check=True, message=f"{chapters_str}の逆方向チェックを実行"
            )
        return BidirectionalConfirmationResult(
            approved=False, include_reverse_check=False, message="逆方向チェックをスキップしました"
        )
