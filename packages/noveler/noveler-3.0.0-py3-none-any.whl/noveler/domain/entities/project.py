"""Domain.entities.project
Where: Domain entity modelling a project aggregate.
What: Holds project settings, directories, and derived state.
Why: Provides a central abstraction for project-wide operations.
"""

from __future__ import annotations

"""プロジェクトエンティティ

小説プロジェクトを表すドメインエンティティ。
"""


from dataclasses import dataclass
from typing import Any

# プロジェクト設定値の型
SettingValue = str | int | float | bool | list[str] | dict[str, Any] | None


@dataclass
class Project:
    """プロジェクトエンティティ

    小説プロジェクトの基本情報と設定を保持する。
    """

    name: str
    settings: dict[str, SettingValue] | None = None

    def __post_init__(self) -> None:
        """初期化後の検証"""
        if not self.name:
            msg = "プロジェクト名は必須です"
            raise ValueError(msg)

        if self.settings is None:
            self.settings = {}

    def get_setting(self, key: str, default: SettingValue) -> SettingValue:
        """設定値を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値
        """
        return self.settings.get(key, default)

    def has_setting(self, key: str) -> bool:
        """設定が存在するかチェック

        Args:
            key: 設定キー

        Returns:
            設定が存在する場合True
        """
        return key in self.settings
