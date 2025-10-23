#!/usr/bin/env python3

"""Application.use_cases.scene_use_case
Where: Application use case orchestrating scene-level operations.
What: Manages scene creation, updates, and validation through domain services.
Why: Centralises scene workflows so callers avoid duplicating orchestration code.
"""

from __future__ import annotations



from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.scene_entity import ImportanceLevel, Scene, SceneCategory
from noveler.domain.value_objects.scene_direction import SceneDirection
from noveler.domain.value_objects.scene_setting import SceneSetting


class SceneUseCase(AbstractUseCase[dict, bool]):
    """シーン管理ユースケース"""

    def __init__(self,
        repository: object = None,
        logger_service: ILoggerService = None,
        unit_of_work: IUnitOfWork = None,
        **kwargs) -> None:
        super().__init__(**kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        # リポジトリ初期化 - 直接渡された場合はそれを使用
        if repository is not None:
            self.repository = repository
        elif hasattr(self, "repository_factory") and hasattr(self.repository_factory, "create_yaml_scene_repository"):
            self.repository = self.repository_factory.create_yaml_scene_repository()
        else:
            self.repository = None
        self._category_mapping = {
            "CLIMAX": SceneCategory.CLIMAX,
            "EMOTIONAL": SceneCategory.EMOTIONAL,
            "ROMANCE": SceneCategory.ROMANCE,
            "ACTION": SceneCategory.ACTION,
            "MYSTERY": SceneCategory.MYSTERY,
            "COMEDY": SceneCategory.COMEDY,
            "DAILY": SceneCategory.DAILY,
        }

    async def execute(self, request: dict) -> bool:
        """シーン管理を実行"""
        action = request.get("action", "create")
        if action == "create":
            return self.create_scene(request)
        if action == "update":
            return self.update_scene(request["scene_id"], request)
        if action == "delete":
            return self.delete_scene(request["scene_id"])
        return False

    def create_scene(self, scene_data: dict[str, Any]) -> bool:
        """新しいシーンを作成"""
        try:
            scene = self._create_base_scene(scene_data)
            self._apply_optional_settings(scene, scene_data)
            return self.repository.save(scene)
        except Exception:
            self.logger.exception("シーンの作成に失敗しました")
            return False

    def _create_base_scene(self, scene_data: dict[str, Any]) -> Scene:
        """基本シーンエンティティを作成"""
        category = self._parse_category(scene_data["category"])
        importance = ImportanceLevel(scene_data["importance_level"])

        return Scene(
            scene_id=scene_data["scene_id"],
            title=scene_data["title"],
            category=category,
            importance_level=importance,
            episode_range=scene_data["episode_range"],
        )

    def _parse_category(self, category_str: str) -> SceneCategory:
        """カテゴリー文字列をSceneCategoryに変換"""
        category_key = self._normalize_category_key(category_str)
        return self._category_mapping.get(category_key, SceneCategory.ACTION)

    def _normalize_category_key(self, category_str: str) -> str:
        """カテゴリー文字列を正規化"""
        if category_str.endswith("_scenes"):
            return category_str[:-7].upper()
        return category_str.upper()

    def _apply_optional_settings(self, scene: Scene, scene_data: dict[str, Any]) -> None:
        """オプション設定を適用"""
        self._apply_setting_if_exists(scene, scene_data)
        self._apply_direction_if_exists(scene, scene_data)
        self._apply_characters_if_exists(scene, scene_data)
        self._apply_key_elements_if_exists(scene, scene_data)
        self._apply_writing_notes_if_exists(scene, scene_data)
        self._apply_quality_checklist_if_exists(scene, scene_data)

    def _apply_setting_if_exists(self, scene: Scene, scene_data: dict[str, Any]) -> None:
        """設定情報を適用"""
        if "setting" not in scene_data:
            return
        setting = SceneSetting(**scene_data["setting"])
        scene.set_setting(setting)

    def _apply_direction_if_exists(self, scene: Scene, scene_data: dict[str, Any]) -> None:
        """演出情報を適用"""
        if "direction" not in scene_data:
            return
        direction = SceneDirection(**scene_data["direction"])
        scene.set_direction(direction)

    def _apply_characters_if_exists(self, scene: Scene, scene_data: dict[str, Any]) -> None:
        """キャラクター情報を適用"""
        if "characters" not in scene_data:
            return
        for character in scene_data["characters"]:
            scene.add_character(character)

    def _apply_key_elements_if_exists(self, scene: Scene, scene_data: dict[str, Any]) -> None:
        """重要要素を適用"""
        if "key_elements" not in scene_data:
            return
        for element in scene_data["key_elements"]:
            scene.add_key_element(element)

    def _apply_writing_notes_if_exists(self, scene: Scene, scene_data: dict[str, Any]) -> None:
        """執筆メモを適用"""
        if "writing_notes" not in scene_data:
            return
        for key, value in scene_data["writing_notes"].items():
            scene.set_writing_note(key, value)

    def _apply_quality_checklist_if_exists(self, scene: Scene, scene_data: dict[str, Any]) -> None:
        """品質チェックリストを適用"""
        if "quality_checklist" not in scene_data:
            return
        for category_name, items in scene_data["quality_checklist"].items():
            for item in items:
                scene.add_quality_check(category_name, item)

    def list_scenes_by_category(self, category_str: str) -> list[dict[str, Any]]:
        """カテゴリ別にシーンを一覧表示"""
        try:
            category = self._parse_category(category_str)
            if not category:
                return []

            scenes = self.repository.find_by_category(category)
            return [self._scene_to_summary_dict(scene) for scene in scenes]
        except Exception:
            self.logger.exception("シーン一覧の取得に失敗しました")
            return []

    def _scene_to_summary_dict(self, scene: Scene) -> dict[str, Any]:
        """シーンを要約辞書に変換"""
        return {
            "scene_id": scene.scene_id,
            "title": scene.title,
            "category": scene.category.value,
            "importance_level": scene.importance_level.value,
            "episode_range": scene.episode_range,
            "completion_score": scene.get_completion_score(),
        }

    def list_all_scenes(self) -> dict[str, list[dict[str, Any]]]:
        """全シーンを一覧表示"""
        try:
            scenes = self.repository.find_all()
            return self._categorize_scenes(scenes)
        except Exception as e:
            if self._logger_service:
                self._logger_service.error(f"全シーン取得エラー: {e}")
            return {}

    def _categorize_scenes(self, scenes: list[Scene]) -> dict[str, list[dict[str, Any]]]:
        """シーンをカテゴリ別に分類"""
        categorized_scenes = {}
        for scene in scenes:
            category = scene.category.value
            if category not in categorized_scenes:
                categorized_scenes[category] = []

            scene_dict = self._scene_to_summary_dict(scene)
            categorized_scenes[category].append(scene_dict)

        return categorized_scenes

    def get_scene_details(self, scene_id: str) -> dict[str, Any] | None:
        """シーンの詳細情報を取得"""
        try:
            scene = self.repository.find_by_id(scene_id)
            if not scene:
                return None

            details: dict[str, Any] = {
                "scene_id": scene.scene_id,
                "title": scene.title,
                "category": scene.category.value,
                "importance_level": scene.importance_level.value,
                "episode_range": scene.episode_range,
                "created_at": scene.created_at.isoformat(),
                "updated_at": scene.updated_at.isoformat(),
                "characters": scene.characters,
                "key_elements": scene.key_elements,
                "writing_notes": scene.writing_notes,
                "quality_checklist": scene.quality_checklist,
                "completion_score": scene.get_completion_score(),
                "is_critical": scene.is_critical(),
            }

            if scene.setting:
                details["setting"] = scene.setting.to_dict()

            if scene.direction:
                details["direction"] = scene.direction.to_dict()

            return details

        except Exception as e:
            if self._logger_service:
                self._logger_service.error(f"シーン詳細取得エラー: {e}")
            return None

    def update_scene(self, scene_id: str, update_data: dict[str, Any]) -> bool:
        """シーンを更新"""
        try:
            scene = self.repository.find_by_id(scene_id)
            if not scene:
                return False

            self._apply_basic_updates(scene, update_data)
            self._apply_complex_updates(scene, update_data)
            return self.repository.save(scene)

        except Exception as e:
            if self._logger_service:
                self._logger_service.error(f"シーン更新エラー: {e}")
            return False

    def _apply_basic_updates(self, scene: Scene, update_data: dict[str, Any]) -> None:
        """基本フィールドの更新を適用"""
        if "title" in update_data:
            scene.title = update_data["title"]

        if "episode_range" in update_data:
            scene.episode_range = update_data["episode_range"]

        if "characters" in update_data:
            scene.characters = update_data["characters"]

        if "key_elements" in update_data:
            scene.key_elements = update_data["key_elements"]

        if "quality_checklist" in update_data:
            scene.quality_checklist = update_data["quality_checklist"]

    def _apply_complex_updates(self, scene: Scene, update_data: dict[str, Any]) -> None:
        """複雑なオブジェクトの更新を適用"""
        if "setting" in update_data:
            setting = SceneSetting(**update_data["setting"])
            scene.set_setting(setting)

        if "direction" in update_data:
            direction = SceneDirection(**update_data["direction"])
            scene.set_direction(direction)

        if "writing_notes" in update_data:
            for key, value in update_data["writing_notes"].items():
                scene.set_writing_note(key, value)

    def delete_scene(self, scene_id: str) -> bool:
        """シーンを削除"""
        try:
            return self.repository.delete(scene_id)

        except Exception as e:
            if self._logger_service:
                self._logger_service.error(f"シーン削除エラー: {e}")
            return False

    def validate_scenes(self) -> dict[str, Any]:
        """全シーンの整合性を検証"""
        try:
            scenes = self.repository.find_all()
            issues = []
            stats = self._calculate_scene_statistics(scenes)

            for scene in scenes:
                scene_issues = self._validate_single_scene(scene)
                issues.extend(scene_issues)

            return {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "stats": stats,
            }

        except Exception as e:
            if self._logger_service:
                self._logger_service.error(f"シーン検証エラー: {e}")
            return {
                "is_valid": False,
                "issues": [f"検証中にエラーが発生: {e}"],
                "stats": {},
            }

    def _calculate_scene_statistics(self, scenes: list[Scene]) -> dict[str, Any]:
        """シーン統計を計算"""
        stats = {
            "total_scenes": len(scenes),
            "critical_scenes": 0,
            "completed_scenes": 0,
            "categories": {},
        }

        for scene in scenes:
            if scene.is_critical():
                stats["critical_scenes"] += 1

            if scene.get_completion_score() >= 0.8:
                stats["completed_scenes"] += 1

            category = scene.category.value
            stats["categories"][category] = stats["categories"].get(category, 0) + 1

        return stats

    def _validate_single_scene(self, scene: Scene) -> list[str]:
        """単一シーンを検証"""
        issues = []
        issues.extend(self._validate_required_fields(scene))
        issues.extend(self._validate_critical_scene_completeness(scene))
        issues.extend(self._validate_setting_completeness(scene))
        return issues

    def _validate_required_fields(self, scene: Scene) -> list[str]:
        """必須フィールドを検証"""
        issues = []

        if not scene.title or not scene.title.strip():
            issues.append(f"{scene.scene_id}: タイトルが空です")

        if not scene.episode_range or not scene.episode_range.strip():
            issues.append(f"{scene.scene_id}: エピソード範囲が空です")

        return issues

    def _validate_critical_scene_completeness(self, scene: Scene) -> list[str]:
        """クリティカルシーンの完成度を検証"""
        if not scene.is_critical():
            return []

        completion_score = scene.get_completion_score()
        if completion_score < 0.6:
            return [f"{scene.scene_id}: クリティカルシーンの設定が不十分(完成度)"]

        return []

    def _validate_setting_completeness(self, scene: Scene) -> list[str]:
        """設定情報の完成度を検証"""
        if not scene.setting:
            return []

        if not scene.setting.location or not scene.setting.atmosphere:
            return [f"{scene.scene_id}: 設定情報が不完全"]

        return []

    def initialize_repository(self) -> bool:
        """リポジトリを初期化"""
        try:
            return self.repository.initialize()

        except Exception as e:
            if self._logger_service:
                self._logger_service.error(f"リポジトリ初期化エラー: {e}")
            return False
