#!/usr/bin/env python3

"""Domain.services.project_path_resolver
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""プロジェクトパス解決サービス

A31評価のファイルパス解決専用ドメインサービス
"""

from pathlib import Path

from noveler.domain.interfaces.path_service import IPathService
from noveler.domain.repositories.project_config_repository import ProjectConfigRepository
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.file_path import FilePath

# B20準拠修正: Infrastructure依存をInterface経由に変更
# from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class ProjectPathResolver:
    """プロジェクトファイルパス解決サービス"""

    def __init__(self,project_config_repository: ProjectConfigRepository, path_service: IPathService) -> None:
        """初期化

        Args:
            project_config_repository: プロジェクト設定リポジトリ
        """
        self._path_service = path_service
        self._project_config_repository = project_config_repository

    def resolve_episode_file_path(self, project_name: str, episode_number: int) -> FilePath:
        """エピソードファイルパスの解決

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            FilePath: 解決されたファイルパス

        Raises:
            FileNotFoundError: ファイルが見つからない場合
        """
        # 1) PathServiceで統一パスを優先
        candidate = self._path_service.get_manuscript_path(episode_number)
        if candidate.exists():
            return FilePath(str(candidate))

        # 2) 旧設定に基づく探索をフォールバックで実施
        episode_num = EpisodeNumber(episode_number)
        try:
            config = self._project_config_repository.get_config(project_name)
            project_root, manuscript_dir = self._extract_paths_from_config(config)
        except Exception:
            project_root, manuscript_dir = self._get_fallback_paths(project_name)
        episode_file = self._find_episode_file(Path(project_root) / manuscript_dir, episode_num)
        if episode_file and episode_file.exists():
            return FilePath(str(episode_file))

        # 3) 最終フォールバック: PathServiceの統一名で返却
        return FilePath(str(candidate))

    def resolve_project_paths(self, project_name: str) -> tuple[str, str]:
        """プロジェクトパスの解決

        Args:
            project_name: プロジェクト名

        Returns:
            tuple[str, str]: (プロジェクトルート, 原稿ディレクトリ)
        """
        try:
            config = self._project_config_repository.get_config(project_name)
            return self._extract_paths_from_config(config)
        except Exception:
            return self._get_fallback_paths(project_name)

    def _extract_paths_from_config(self, config: dict) -> tuple[str, str]:
        """設定からパス情報を抽出"""
        project_root = config.get("project_root", ".")
        # ハードコーディング排除: 統合パス管理システム経由で取得
        # B20準拠: Path ServiceはDI注入されたものを使用
        default_manuscript = self._path_service.get_manuscript_dir().name
        manuscript_dir = config.get("directories", {}).get("manuscript", default_manuscript)
        return project_root, manuscript_dir

    def _get_fallback_paths(self, project_name: str) -> tuple[str, str]:
        """フォールバック用のパス取得"""
        # ハードコーディング排除: 統合パス管理システム経由で取得
        # B20準拠: Path ServiceはDI注入されたものを使用
        default_manuscript = self._path_service.get_manuscript_dir().name
        return f"projects/{project_name}", default_manuscript

    def _find_episode_file(self, manuscript_dir: Path, episode_num: EpisodeNumber) -> Path | None:
        """エピソードファイルの検索"""
        if not manuscript_dir.exists():
            return None

        # 標準的なファイル名パターンで検索
        patterns = [
            f"第{episode_num.value:03d}話*.md",
            f"第{episode_num.value}話*.md",
            f"episode_{episode_num.value:03d}*.md",
            f"ep{episode_num.value:03d}*.md",
        ]

        for pattern in patterns:
            matches = list(manuscript_dir.glob(pattern))
            if matches:
                return matches[0]  # 最初のマッチを返す

        return None

    def _generate_fallback_episode_path(self, project_name: str, episode_num: EpisodeNumber) -> FilePath:
        """フォールバック用のエピソードパス生成（PathService準拠）"""
        return FilePath(str(self._path_service.get_manuscript_path(episode_num.value)))
