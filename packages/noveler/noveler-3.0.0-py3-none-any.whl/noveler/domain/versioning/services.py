"""Domain.versioning.services
Where: Domain services handling versioning operations.
What: Manage creation, comparison, and maintenance of versioned data.
Why: Provide reusable versioning logic for application workflows.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""自動バージョニングのドメインサービス
複数エンティティの調整を行う
"""


from noveler.domain.versioning.entities import FileChangeAnalyzer, VersionDeterminer, VersionSuggestion


class AutoVersioningService:
    """自動バージョニングサービス(ドメインサービス)"""

    def __init__(self) -> None:
        self.version_determiner = VersionDeterminer()
        self.file_analyzer = FileChangeAnalyzer()

    def suggest_version_update(
        self, current_version: str, changed_files: list[str], description: str | None = None
    ) -> VersionSuggestion | None:
        """バージョン更新の提案を生成"""

        # プロット関連の変更のみを抽出
        plot_changes = self.file_analyzer.extract_plot_changes(changed_files)

        # プロット変更がない場合はNoneを返す
        if not plot_changes:
            return None

        # バージョンタイプを判定(優先順位ルール適用)
        version_type = self.version_determiner.determine_version_type(plot_changes)

        # 適切な提案を作成
        if version_type == "major":
            return VersionSuggestion.create_major_bump(
                current_version,
                plot_changes,
                description,
            )

        if version_type == "minor":
            return VersionSuggestion.create_minor_bump(
                current_version,
                plot_changes,
                description,
            )

        # patch
        return VersionSuggestion.create_patch_bump(
            current_version,
            plot_changes,
            description,
        )
