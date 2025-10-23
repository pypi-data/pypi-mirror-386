#!/usr/bin/env python3

"""Domain.entities.novel_project
Where: Domain entity representing a novel project aggregate.
What: Stores project metadata, settings, and state.
Why: Serves as the root aggregate for novel-related workflows.
"""

from __future__ import annotations

"""小説プロジェクトエンティティ

NovelProjectエンティティの動作を実装するドメインエンティティ
DDD準拠・パフォーマンス最適化対応版
"""


from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_info import ProjectInfo


@dataclass
class NovelProject:
    """小説プロジェクトエンティティ

    小説プロジェクトの基本情報と設定を保持する。
    """

    name: str
    project_info: ProjectInfo
    project_path: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """初期化後の検証"""
        if not self.name or not self.name.strip():
            msg = "プロジェクト名が無効です"
            raise ValueError(msg)

        if self.project_path is None:
            msg = "プロジェクトパスが無効です"
            raise ValueError(msg)

        if not isinstance(self.project_path, Path):
            msg = "プロジェクトパスはPathオブジェクトである必要があります"
            raise ValueError(msg)

        if not isinstance(self.project_info, ProjectInfo):
            msg = "project_infoはProjectInfoである必要があります"
            raise TypeError(msg)

        if not self.project_info.title or not self.project_info.title.strip():
            msg = "プロジェクト情報のタイトルが無効です"
            raise ValueError(msg)

        if not self.project_info.author or not self.project_info.author.strip():
            msg = "プロジェクト情報の作者が無効です"
            raise ValueError(msg)

    def set_metadata(self, key: str, value: Any) -> None:
        """メタデータを設定

        Args:
            key: メタデータキー
            value: メタデータ値
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """メタデータを取得

        Args:
            key: メタデータキー
            default: デフォルト値

        Returns:
            メタデータ値
        """
        return self.metadata.get(key, default)

    def update_configuration(self, config_updates: dict[str, Any]) -> None:
        """設定を更新

        Args:
            config_updates: 更新する設定の辞書
        """
        self.configuration.update(config_updates)

    def get_configuration(self) -> dict[str, Any]:
        """現在の設定を取得

        Returns:
            設定の辞書
        """
        return self.configuration.copy()
