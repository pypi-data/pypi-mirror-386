"""原稿とプロットのリンクエンティティ

原稿とプロットの紐付けを管理するエンティティ
"""

from dataclasses import dataclass
from datetime import datetime

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class ManuscriptPlotLink:
    """原稿とプロットのリンクエンティティ"""

    manuscript_id: str
    plot_id: str
    plot_version_id: str
    linked_at: datetime
    linked_by: str
    link_type: str = "main"  # main, reference, etc.
    notes: str = ""

    def update_version(self, new_version_id: str) -> None:
        """バージョンの更新"""
        self.plot_version_id = new_version_id
        self.linked_at = project_now().datetime

    def add_notes(self, notes: str) -> None:
        """ノートの追加"""
        self.notes = notes
