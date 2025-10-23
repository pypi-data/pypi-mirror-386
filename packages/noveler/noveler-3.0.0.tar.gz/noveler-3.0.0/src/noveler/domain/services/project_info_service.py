#!/usr/bin/env python3

"""Domain.services.project_info_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""プロジェクト情報サービス
プロジェクトファイルからの情報取得を統括するドメインサービス
"""


from typing import TYPE_CHECKING, Any

from noveler.domain.exceptions import BusinessRuleViolationError
from noveler.domain.value_objects.project_context import ProjectContext

if TYPE_CHECKING:
    from noveler.domain.repositories.project_info_repository import ProjectInfoRepository


class ProjectInfoService:
    """プロジェクト情報ドメインサービス

    複数のプロジェクトファイルから情報を収集し、
    ProjectContextオブジェクトを構築する責務を持つ
    """

    def __init__(self, repository: ProjectInfoRepository) -> None:
        self._repository = repository

    def load_project_context(self, project_root: str | None = None) -> ProjectContext:
        """プロジェクトコンテキストを読み込み

        Args:
            project_root: プロジェクトルートパス(省略時は現在位置から検索)

        Returns:
            ProjectContext: 構築されたプロジェクトコンテキスト

        Raises:
            BusinessRuleViolationError: 必須ファイルが不足している場合
        """
        # プロジェクトファイルを読み込み
        resolved_root = self._resolve_project_root(project_root)
        project_files = self._repository.load_project_files(resolved_root)

        # 必須ファイルの存在確認
        self._validate_required_files(project_files)

        # ProjectContextを構築
        return ProjectContext.from_project_files(project_files)

    def _validate_required_files(self, project_files: dict[str, Any]) -> None:
        """必須ファイルの存在確認"""
        required_files = ["project_settings"]

        missing_files = []
        missing_files.extend(
            self._get_file_display_name(file_key)
            for file_key in required_files
            if file_key not in project_files or not project_files[file_key]
        )

        if missing_files:
            msg = f"以下の必須ファイルが見つかりません: {', '.join(missing_files)}"
            raise BusinessRuleViolationError(
                "PROJECT_REQUIRED_FILES",
                msg,
                {"missing_files": missing_files},
            )

    def _get_file_display_name(self, file_key: str) -> str:
        """ファイルキーから表示名を取得"""
        display_names = {
            "project_settings": "プロジェクト設定.yaml",
            "character_settings": "30_設定集/キャラクター.yaml",
            "plot_settings": "20_プロット/全体構成.yaml",
            "episode_management": "50_管理資料/話数管理.yaml",
        }
        return display_names.get(file_key, file_key)

    def get_available_project_info(self, project_root: str | None = None) -> dict[str, bool]:
        """利用可能なプロジェクト情報の確認

        Args:
            project_root: プロジェクトルートパス

        Returns:
            dict: 各ファイルの利用可能性
        """
        try:
            resolved_root = self._resolve_project_root(project_root)
            project_files = self._repository.load_project_files(resolved_root)

            return {
                "project_settings": bool(project_files.get("project_settings")),
                "character_settings": bool(project_files.get("character_settings")),
                "plot_settings": bool(project_files.get("plot_settings")),
                "episode_management": bool(project_files.get("episode_management")),
            }
        except Exception:
            return {
                "project_settings": False,
                "character_settings": False,
                "plot_settings": False,
                "episode_management": False,
            }

    def validate_project_structure(self, project_root: str | None = None) -> dict[str, Any]:
        """プロジェクト構造の検証

        Args:
            project_root: プロジェクトルートパス

        Returns:
            dict: 検証結果
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "available_files": self.get_available_project_info(project_root),
        }

        try:
            # プロジェクトコンテキストの構築を試行
            context = self.load_project_context(project_root)

            # コンテキストの妥当性確認
            if not context.is_valid():
                validation_result["is_valid"] = False
                validation_result["errors"].append("プロジェクトコンテキストが無効です")

            # 警告レベルのチェック
            available_files = validation_result["available_files"]

            if not available_files["character_settings"]:
                validation_result["warnings"].append(
                    "キャラクター設定ファイルがありません。シーン生成の精度が下がる可能性があります。"
                )

            if not available_files["plot_settings"]:
                validation_result["warnings"].append(
                    "プロット設定ファイルがありません。物語構造を考慮したシーン生成ができません。"
                )

        except BusinessRuleViolationError as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(str(e))
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"予期しないエラー: {e}")

        return validation_result

    def get_project_summary(self, project_root: str | None = None) -> dict[str, Any]:
        """プロジェクト情報のサマリーを取得

        Args:
            project_root: プロジェクトルートパス

        Returns:
            dict: プロジェクトサマリー
        """
        try:
            context = self.load_project_context(project_root)

            return {
                "project_name": context.project_name,
                "genre": context.genre,
                "protagonist": context.protagonist_name,
                "total_episodes": context.total_episodes,
                "structure_type": context.structure_type,
                "has_character_info": context.has_character_info(),
                "has_plot_info": context.has_plot_info(),
                "character_count": len(context.main_characters),
                "quality_threshold": context.quality_threshold,
            }
        except Exception as e:
            return {
                "error": str(e),
                "project_name": None,
                "genre": None,
            }

    def _resolve_project_root(self, project_root: str | None) -> str:
        """プロジェクトルートを決定"""

        if project_root:
            return project_root

        resolver = getattr(self._repository, "get_project_root", None)
        if callable(resolver):
            try:
                resolved = resolver(".")
                if resolved:
                    return resolved
            except Exception:
                return "."

        return "."
