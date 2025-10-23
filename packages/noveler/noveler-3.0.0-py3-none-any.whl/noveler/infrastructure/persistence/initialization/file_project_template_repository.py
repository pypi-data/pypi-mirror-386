"""ファイルベースプロジェクトテンプレートリポジトリ実装

インフラ層:ドメインリポジトリインターフェースの具体実装
"""

import json
from pathlib import Path
from typing import Any

from noveler.domain.initialization.entities import ProjectTemplate
from noveler.domain.initialization.repositories import ProjectTemplateRepository
from noveler.domain.initialization.value_objects import Genre


class FileProjectTemplateRepository(ProjectTemplateRepository):
    """ファイルベースプロジェクトテンプレートリポジトリ

    JSONファイルでテンプレート情報を管理
    """

    def __init__(self, templates_directory: str) -> None:
        self.templates_directory = Path(templates_directory)
        self.templates_directory.mkdir(parents=True, exist_ok=True)
        self._ensure_default_templates()

    def find_by_id(self, template_id: str) -> ProjectTemplate | None:
        """テンプレートIDで検索"""
        template_file = self.templates_directory / f"{template_id}.json"

        if not template_file.exists():
            return None

        try:
            with Path(template_file).open(encoding="utf-8") as f:
                data = json.load(f)

            return self._deserialize_template(data)
        except Exception:
            return None

    def find_by_genre(self, genre: str) -> list[ProjectTemplate]:
        """ジャンルでテンプレート検索"""
        templates = []

        for template_file in self.templates_directory.glob("*.json"):
            try:
                with Path(template_file).open(encoding="utf-8") as f:
                    data = json.load(f)

                template = self._deserialize_template(data)
                if template and template.genre == genre:
                    templates.append(template)
            except Exception:
                continue

        return templates

    def find_all(self) -> list[ProjectTemplate]:
        """全テンプレート取得"""
        templates = []

        for template_file in self.templates_directory.glob("*.json"):
            try:
                with Path(template_file).open(encoding="utf-8") as f:
                    data = json.load(f)

                template = self._deserialize_template(data)
                if template:
                    templates.append(template)
            except Exception:
                continue

        return templates

    def save(self, template: ProjectTemplate) -> None:
        """テンプレート保存"""
        template_file = self.templates_directory / f"{template.template_id}.json"

        data = self._serialize_template(template)

        with Path(template_file).open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def delete(self, template_id: str) -> None:
        """テンプレート削除"""
        template_file = self.templates_directory / f"{template_id}.json"

        if template_file.exists():
            template_file.unlink()

    def _serialize_template(self, template: ProjectTemplate) -> dict[str, Any]:
        """テンプレートをJSONデータに変換"""
        return {
            "template_id": template.template_id,
            "genre": template.genre.value,
            "name": template.name,
            "description": template.description,
            "directory_structure": template.directory_structure,
            "customizations": template.customizations,
        }

    def _deserialize_template(self, data: dict[str, Any]) -> ProjectTemplate | None:
        """JSONデータからテンプレートを復元"""
        try:
            genre = Genre(data["genre"])

            template = ProjectTemplate(
                template_id=data["template_id"],
                genre=genre,
                name=data["name"],
                description=data["description"],
            )

            template.directory_structure = data.get("directory_structure", [])
            template.customizations = data.get("customizations", {})

            return template
        except (KeyError, ValueError):
            return None

    def _ensure_default_templates(self) -> None:
        """デフォルトテンプレートの確保"""
        # 共通基盤からディレクトリ構造を取得
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service()
        basic_structure = path_service.get_required_directories()
        path_service.get_all_directories()

        default_templates = [
            {
                "template_id": "fantasy_light",
                "genre": Genre.FANTASY,
                "name": "ライトファンタジーテンプレート",
                "description": "読みやすいライトファンタジー向けテンプレート",
                "directory_structure": [*basic_structure, "30_設定集/魔法システム", "30_設定集/種族設定"],
                "customizations": {
                    "magic_system": "エレメンタル魔法",
                    "tone": "light",
                    "target_audience": "young_adult",
                },
            },
            {
                "template_id": "fantasy_basic",
                "genre": Genre.FANTASY,
                "name": "基本ファンタジーテンプレート",
                "description": "王道ファンタジー向けテンプレート",
                "directory_structure": basic_structure,
                "customizations": {},
            },
            {
                "template_id": "romance_basic",
                "genre": Genre.ROMANCE,
                "name": "基本ロマンステンプレート",
                "description": "恋愛小説向けテンプレート",
                "directory_structure": basic_structure,
                "customizations": {
                    "relationship_focus": True,
                    "emotional_depth": "high",
                },
            },
            {
                "template_id": "mystery_basic",
                "genre": Genre.MYSTERY,
                "name": "基本ミステリーテンプレート",
                "description": "推理小説向けテンプレート",
                "directory_structure": [*basic_structure, "30_設定集/事件設定", "30_設定集/証拠管理"],
                "customizations": {
                    "investigation_structure": True,
                    "logical_progression": "strict",
                },
            },
            {
                "template_id": "sf_basic",
                "genre": Genre.SCIENCE_FICTION,
                "name": "基本SFテンプレート",
                "description": "SF小説向けテンプレート",
                "directory_structure": [*basic_structure, "30_設定集/技術仕様", "30_設定集/世界年表"],
                "customizations": {
                    "technology_level": "near_future",
                    "scientific_accuracy": "medium",
                },
            },
            {
                "template_id": "universal_basic",
                "genre": Genre.SLICE_OF_LIFE,  # 汎用として日常系を使用
                "name": "汎用テンプレート",
                "description": "あらゆるジャンルに対応する基本テンプレート",
                "directory_structure": basic_structure,
                "customizations": {
                    "flexible_structure": True,
                    "genre_agnostic": True,
                },
            },
        ]

        for template_data in default_templates:
            template_file = self.templates_directory / f"{template_data['template_id']}.json"
            if not template_file.exists():
                # テンプレートオブジェクト作成
                template = ProjectTemplate(
                    template_id=template_data["template_id"],
                    genre=template_data["genre"],
                    name=template_data["name"],
                    description=template_data["description"],
                )

                template.directory_structure = template_data["directory_structure"]
                template.customizations = template_data["customizations"]

                # 保存
                self.save(template)
