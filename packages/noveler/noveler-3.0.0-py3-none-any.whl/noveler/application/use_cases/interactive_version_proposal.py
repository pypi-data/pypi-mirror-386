#!/usr/bin/env python3
"""インタラクティブバージョン提案ユースケース"""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ProposalResult:
    """提案結果"""

    accepted: bool
    version: str = ""
    description: str = ""
    message: str = ""


class InteractiveVersionProposal:
    """インタラクティブバージョン提案処理"""

    def handle_proposal(
        self,
        suggested_version: str,
        change_type: str,
        reason: str = "プロットファイル変更",
        user_input_handler: Callable[[str], str] | None = None,
    ) -> ProposalResult:
        """バージョン提案をインタラクティブに処理"""

        # デフォルトの入力ハンドラー
        if not user_input_handler:
            user_input_handler = input

        # 提案メッセージを作成
        proposal_message = f"""
⚠️  プロットファイルが変更されました
理由: {reason}
{change_type.capitalize()}バージョンアップを提案します ({suggested_version})

バージョンアップを実行しますか? [Y/n]: """

        # ユーザーの応答を取得
        response = user_input_handler(proposal_message)

        if response.lower() in ["n", "no"]:
            return ProposalResult(
                accepted=False,
                message="ユーザーがバージョン提案を拒否。今回はスキップします。",
            )

        # バージョンアップ実行時の詳細入力
        description_prompt = "変更内容を入力してください: "
        description = user_input_handler(description_prompt)

        return ProposalResult(
            accepted=True,
            version=suggested_version,
            description=description,
            message=f"バージョン{suggested_version}の作成を承認しました。",
        )
