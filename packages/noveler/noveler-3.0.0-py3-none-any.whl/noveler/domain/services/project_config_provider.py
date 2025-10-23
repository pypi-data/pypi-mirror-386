#!/usr/bin/env python3

"""Domain.services.project_config_provider
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""プロジェクト設定プロバイダサービス

A31評価のプロジェクト設定管理専用ドメインサービス
"""


# Phase 6修正: Service → Repository循環依存解消
from typing import Any, Protocol


class IProjectConfigRepository(Protocol):
    """プロジェクト設定リポジトリインターフェース（循環依存解消）"""

    def get_config(self, key: str) -> Any: ...
    def set_config(self, key: str, value: Any) -> bool: ...
    def load_all_configs(self) -> dict[str, Any]: ...


class ProjectConfigProvider:
    """プロジェクト設定プロバイダサービス"""

    def __init__(self, project_config_repository: IProjectConfigRepository) -> None:
        """初期化

        Args:
            project_config_repository: プロジェクト設定リポジトリ
        """
        self._project_config_repository = project_config_repository

    def get_project_config(self, project_name: str) -> dict[str, Any]:
        """プロジェクト設定を取得

        Args:
            project_name: プロジェクト名

        Returns:
            dict[str, Any]: プロジェクト設定
        """
        try:
            return self._project_config_repository.get_config(project_name)
        except Exception:
            # デフォルト設定を返す
            return {
                "a31_checklist": {
                    "claude_evaluation": True,
                    "show_line_numbers": True,
                    "review_verbosity": "standard",
                }
            }

    def should_run_a31_evaluation(
        self,
        config: dict[str, Any],
        include_a31: bool,
        a31_only: bool,
    ) -> bool:
        """A31評価を実行すべきかを判定

        Args:
            config: プロジェクト設定
            include_a31: A31評価を含めるかのフラグ
            a31_only: A31評価のみ実行するかのフラグ

        Returns:
            bool: 実行すべき場合True
        """
        # a31_onlyが指定された場合は常に実行
        if a31_only:
            return True

        # include_a31が明示的にFalseの場合は実行しない
        if not include_a31:
            return False

        # 設定でClaude評価が無効化されている場合は実行しない
        a31_config: dict[str, Any] = config.get("a31_checklist", {})
        return a31_config.get("claude_evaluation", True)

    def get_review_verbosity(self, config: dict[str, Any], default: str = "standard") -> str:
        """レビュー詳細度を取得

        Args:
            config: プロジェクト設定
            default: デフォルト値

        Returns:
            str: レビュー詳細度
        """
        a31_config: dict[str, Any] = config.get("a31_checklist", {})
        return a31_config.get("review_verbosity", default)

    def should_show_line_numbers(self, config: dict[str, Any]) -> bool:
        """行番号を表示すべきかを判定

        Args:
            config: プロジェクト設定

        Returns:
            bool: 表示すべき場合True
        """
        a31_config: dict[str, Any] = config.get("a31_checklist", {})
        return a31_config.get("show_line_numbers", True)
