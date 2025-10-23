#!/usr/bin/env python3
"""YAMLシーンリポジトリ実装

DDD原則に基づくインフラストラクチャ層
重要シーン情報をYAMLファイルで永続化
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.scene_repository import SceneRepository


class YamlSceneRepository(SceneRepository):
    """YAMLベースのシーンリポジトリ実装"""

    def __init__(self, base_path: str | Path) -> None:
        """Args:
        base_path: プロジェクトのベースパス
        """
        self.base_path = Path(base_path) if isinstance(base_path, str) else base_path

    def find_by_episode(self, project_name: str, episode_number: int) -> list[dict[str, Any]]:
        """エピソードに関連するシーン情報を取得"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        project_path = self.base_path / project_name
        path_service = create_path_service(project_path)
        scene_file = path_service.get_scene_file(episode_number)

        if not scene_file.exists():
            return []

        scenes = []
        episode_str = f"第{episode_number:03d}話"

        try:
            with Path(scene_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return scenes

            # 各カテゴリを検索
            for category, category_scenes in data.items():
                if isinstance(category_scenes, dict):
                    for scene_id, scene_data in category_scenes.items():
                        # エピソード番号が含まれるシーンIDを探す
                        if episode_str in scene_id:
                            scene_info = {"scene_id": scene_id, "category": category, **scene_data}
                            scenes.append(scene_info)
        except Exception:
            return scenes

        return scenes

    def find_by_id(self, project_name: str, scene_id: str) -> dict[str, Any] | None:
        """シーンIDでシーン情報を取得"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        project_path = self.base_path / project_name
        path_service = create_path_service(project_path)
        scene_file = path_service.get_scene_file(1)  # デフォルトエピソードの汎用シーンファイル

        if not scene_file.exists():
            return None

        try:
            with Path(scene_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return None

            # 各カテゴリを検索
            for category, category_scenes in data.items():
                if isinstance(category_scenes, dict) and scene_id in category_scenes:
                    return {"scene_id": scene_id, "category": category, **category_scenes[scene_id]}
        except Exception:
            return None

        return None

    def save_scene(self, project_name: str, scene_data: dict[str, Any]) -> None:
        """シーン情報を保存"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        project_path = self.base_path / project_name
        path_service = create_path_service(project_path)
        scene_file = path_service.get_scene_file(1)  # デフォルトエピソードの汎用シーンファイル

        # ディレクトリ作成
        scene_file.parent.mkdir(parents=True, exist_ok=True)

        # 既存データ読み込み
        existing_data: dict[str, Any] = {}
        if scene_file.exists():
            try:
                with Path(scene_file).open(encoding="utf-8") as f:
                    existing_data: dict[str, Any] = yaml.safe_load(f) or {}
            except Exception:
                existing_data: dict[str, Any] = {}

        # カテゴリとシーンIDを取得
        category = scene_data.get("category", "general_scenes")
        scene_id = scene_data.get("scene_id")

        if not scene_id:
            msg = "scene_id is required"
            raise ValueError(msg)

        # カテゴリが存在しない場合は作成
        if category not in existing_data:
            existing_data[category] = {}

        # シーンデータから不要なフィールドを除去
        scene_info = {k: v for k, v in scene_data.items() if k not in ["category", "scene_id"]}

        # データ更新
        existing_data[category][scene_id] = scene_info

        # ファイルに書き込み
        with Path(scene_file).open("w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, allow_unicode=True, default_flow_style=False)

    def find_by_category(self, project_name: str, category: str) -> list[dict[str, Any]]:
        """カテゴリ別にシーンを取得"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        project_path = self.base_path / project_name
        path_service = create_path_service(project_path)
        scene_file = path_service.get_scene_file(1)  # デフォルトエピソードの汎用シーンファイル

        if not scene_file.exists():
            return []

        scenes = []

        try:
            with Path(scene_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or category not in data:
                return scenes

            category_scenes = data.get(category, {})
            if isinstance(category_scenes, dict):
                for scene_id, scene_data in category_scenes.items():
                    scene_info = {"scene_id": scene_id, "category": category, **scene_data}
                    scenes.append(scene_info)
        except Exception:
            return scenes

        return scenes

    def find_by_importance(self, project_name: str, importance_level: str) -> list[dict[str, Any]]:
        """重要度別にシーンを取得"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        project_path = self.base_path / project_name
        path_service = create_path_service(project_path)
        scene_file = path_service.get_scene_file(1)  # デフォルトエピソードの汎用シーンファイル

        if not scene_file.exists():
            return []

        scenes = []

        try:
            with Path(scene_file).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return scenes

            # 全カテゴリを検索
            for category, category_scenes in data.items():
                if isinstance(category_scenes, dict):
                    for scene_id, scene_data in category_scenes.items():
                        if scene_data.get("importance_level") == importance_level:
                            scene_info = {"scene_id": scene_id, "category": category, **scene_data}
                            scenes.append(scene_info)
        except Exception:
            return scenes

        return scenes

    def exists(self, project_name: str, scene_id: str) -> bool:
        """シーンが存在するか確認"""
        return self.find_by_id(project_name, scene_id) is not None
