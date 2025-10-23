"""Domain.entities.plot_version
Where: Domain entity describing a plot version.
What: Encapsulates version metadata, change sets, and status.
Why: Enables tracking of plot evolution over time.
"""

from __future__ import annotations

"""プロットバージョンエンティティ

プロットのバージョン管理を行うエンティティ
"""


from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from datetime import datetime

# メタデータ値の型
MetadataValue = str | int | float | bool | list[str] | dict[str, Any]

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class PlotVersion:
    """プロットバージョンエンティティ"""

    version_id: str
    plot_id: str
    version_number: int
    content: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    author: str
    description: str = ""
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def update_content(self, new_content: dict[str, Any]) -> None:
        """コンテンツの更新"""
        self.content = new_content
        self.updated_at = project_now().datetime

    def deactivate(self) -> None:
        """非アクティブ化"""
        self.is_active = False
        self.updated_at = project_now().datetime

    def add_metadata(self, key: str, value: MetadataValue) -> None:
        """メタデータの追加"""
        self.metadata[key] = value
        self.updated_at = project_now().datetime
