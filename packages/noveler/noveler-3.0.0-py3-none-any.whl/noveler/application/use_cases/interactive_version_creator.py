#!/usr/bin/env python3
"""インタラクティブなバージョン作成ユーティリティ"""

from collections.abc import Callable
from typing import Any

from noveler.domain.versioning.value_objects import VersionCalculator


class InteractiveVersionCreator:
    """インタラクティブなバージョン作成器"""

    def __init__(self) -> None:
        self.calculator = VersionCalculator()

    def create_interactively(
        self, suggestion_type: str, current_version: str, user_input_handler: Callable[[str], str] | None = None
    ) -> dict[str, Any]:
        """インタラクティブにバージョン情報を作成"""

        # デフォルトの入力ハンドラー
        if not user_input_handler:
            user_input_handler = input

        # デフォルトの次バージョンを計算
        default_version = self.calculator.calculate_next_version(
            current_version,
            suggestion_type,
        )

        # バージョン番号の確認
        version_prompt = f"バージョン番号 [{default_version}]: "
        version_input = user_input_handler(version_prompt)
        final_version = version_input if version_input else default_version

        # 変更内容の入力
        changes_prompt = "変更内容を入力してください: "
        changes_input = user_input_handler(changes_prompt)
        changes = [changes_input] if changes_input else []

        # 影響章の入力
        chapters_prompt = "影響を受ける章番号をカンマ区切りで入力 (例: 1,2,3): "
        chapters_input = user_input_handler(chapters_prompt)

        affected_chapters = []
        if chapters_input:
            try:
                affected_chapters = [int(x.strip()) for x in chapters_input.split(",") if x.strip()]
            except ValueError:
                affected_chapters = []

        # 変更ファイル一覧(簡易実装)
        changed_files = ["プロットファイル"]  # 実際の実装では Git diff から取得

        return {
            "version": final_version,
            "changes": changes,
            "affected_chapters": affected_chapters,
            "changed_files": changed_files,
        }
