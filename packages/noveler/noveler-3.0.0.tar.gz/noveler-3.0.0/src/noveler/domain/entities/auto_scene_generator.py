#!/usr/bin/env python3

"""Domain.entities.auto_scene_generator
Where: Domain entity representing automated scene generation state.
What: Holds prompts, generated scenes, and evaluation metadata.
Why: Keeps auto-generated scenes traceable across workflows.
"""

from __future__ import annotations

"""シーン自動生成エンティティ.

ドメイン駆動設計に基づくシーン自動生成の中核エンティティ。
"""


from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from noveler.domain.exceptions import BusinessRuleViolationError
from noveler.domain.value_objects.generated_scene import GeneratedScene
from noveler.domain.value_objects.generation_options import GenerationOptions
from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.scene_template import SceneTemplate

if TYPE_CHECKING:
    from noveler.domain.value_objects.project_context import ProjectContext


@dataclass
class AutoSceneGenerator:
    """シーン自動生成エンティティ

    ビジネスルール:
    1. プロジェクトコンテキストは必須
    2. 生成オプションに応じてテンプレートを選択
    3. 生成されたシーンは既存構造と整合性を保つ
    4. 自動生成フラグと生成元情報を記録
    """

    id: str = field(default_factory=lambda: project_now().format_timestamp("%Y%m%d_%H%M%S"))
    project_context: ProjectContext | None = None
    available_templates: list[SceneTemplate] = field(default_factory=list)
    generation_history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """エンティティ不変条件の検証"""
        self._validate_entity_state()
        self._add_default_templates()

    def _validate_entity_state(self) -> None:
        """エンティティの状態を検証"""
        # プロジェクトコンテキストが設定された後の検証は generate_scene で実行

    def set_project_context(self, context: ProjectContext) -> None:
        """プロジェクトコンテキストを設定

        Args:
            context: プロジェクト情報コンテキスト

        Raises:
            BusinessRuleViolationError: コンテキストが無効な場合
        """
        context_error = "プロジェクトコンテキストが無効です"
        if not context.is_valid():
            error_code = "invalid_project_context"
            raise BusinessRuleViolationError(error_code, context_error)

        self.project_context = context

    def update_project_context(self, context: ProjectContext) -> None:
        """プロジェクトコンテキストを更新(エイリアス)

        Args:
            context: プロジェクト情報コンテキスト

        Raises:
            BusinessRuleViolationError: コンテキストが無効な場合
        """
        self.set_project_context(context)

    def add_template(self, template: SceneTemplate) -> None:
        """利用可能なテンプレートを追加

        Args:
            template: シーンテンプレート

        Raises:
            BusinessRuleViolationError: テンプレートが無効な場合
        """
        self._add_template_impl(template)

    def add_custom_template(self, template: SceneTemplate) -> None:
        """カスタムテンプレートを追加(エイリアス)

        Args:
            template: シーンテンプレート

        Raises:
            BusinessRuleViolationError: テンプレートが無効な場合
        """
        self._add_template_impl(template)

    def _add_template_impl(self, template: SceneTemplate) -> None:
        """テンプレート追加の内部実装"""
        template_error = "テンプレートが無効です"
        if not template.is_valid():
            error_code = "invalid_template"
            raise BusinessRuleViolationError(error_code, template_error)

        # 同じカテゴリ・名前のテンプレートは上書き
        existing_index = None
        for i, existing in enumerate(self.available_templates):
            if existing.category == template.category and existing.name == template.name:
                existing_index = i
                break

        if existing_index is not None:
            self.available_templates[existing_index] = template
        else:
            self.available_templates.append(template)

    def generate_scene(
        self, scene_category: str, scene_id: str, options: GenerationOptions | None = None
    ) -> GeneratedScene:
        """シーンを自動生成

        Args:
            scene_category: シーンカテゴリ
            scene_id: シーンID
            options: 生成オプション

        Returns:
            GeneratedScene: 生成されたシーン

        Raises:
            BusinessRuleViolationError: 生成条件が満たされない場合
        """
        if options is None:
            options = GenerationOptions()

        # ビジネスルール検証
        self._validate_generation_preconditions(scene_category, scene_id, options)

        # 適用テンプレートを選択
        template = self._select_template(scene_category, options.template_name)

        # シーン生成
        generated_scene = self._execute_generation(scene_category, scene_id, template, options)

        # 生成履歴を記録
        self._record_generation_history(scene_category, scene_id, template, options)

        return generated_scene

    def _validate_generation_preconditions(
        self, scene_category: str, scene_id: str, options: GenerationOptions | None
    ) -> None:
        """生成前提条件を検証"""
        context_missing_error = "プロジェクトコンテキストが設定されていません"
        category_missing_error = "シーンカテゴリは必須です"
        scene_id_missing_error = "シーンIDは必須です"
        options_invalid_error = "生成オプションが無効です"

        if not self.project_context:
            error_code = "context_missing"
            raise BusinessRuleViolationError(error_code, context_missing_error)

        if not scene_category:
            error_code = "category_missing"
            raise BusinessRuleViolationError(error_code, category_missing_error)

        if not scene_id:
            error_code = "scene_id_missing"
            raise BusinessRuleViolationError(error_code, scene_id_missing_error)

        if not options.is_valid():
            error_code = "options_invalid"
            raise BusinessRuleViolationError(error_code, options_invalid_error)

        # 重複IDチェック
        for entry in self.generation_history:
            if entry["scene_id"] == scene_id:
                duplicate_id_error = f"シーンID '{scene_id}' は既に使用されています"
                error_code = "duplicate_scene_id"
                raise BusinessRuleViolationError(error_code, duplicate_id_error)

    def _select_template(self, category: str, template_name: str | None) -> SceneTemplate:
        """適用するテンプレートを選択"""
        # 指定されたテンプレート名がある場合、それを優先
        if template_name:
            for template in self.available_templates:
                if template.category == category and template.name == template_name:
                    return template
            template_not_found_error = f"指定されたテンプレート '{template_name}' が見つかりません"
            error_code = "template_not_found"
            raise BusinessRuleViolationError(error_code, template_not_found_error)

        # カテゴリ別のデフォルトテンプレートを選択
        category_templates = [t for t in self.available_templates if t.category == category]
        if not category_templates:
            category_not_found_error = f"カテゴリ '{category}' のテンプレートが見つかりません"
            error_code = "category_not_found"
            raise BusinessRuleViolationError(error_code, category_not_found_error)

        # デフォルトまたは最初のテンプレートを使用
        default_template = next((t for t in category_templates if t.is_default), None)
        return default_template or category_templates[0]

    def _execute_generation(
        self, scene_category: str, scene_id: str, template: SceneTemplate, options: GenerationOptions | None
    ) -> GeneratedScene:
        """実際の生成処理を実行"""
        # プロジェクトコンテキストからの情報取得
        project_info = self.project_context.to_dict()

        # テンプレートにプロジェクト情報を適用
        scene_data: dict[str, Any] = template.apply_to_project(project_info, options)

        # GeneratedSceneオブジェクトを作成
        return GeneratedScene(
            category=scene_category,
            scene_id=scene_id,
            title=options.title or "新しいシーン",
            importance_level=options.importance_level,
            episode_range=options.episode_range,
            setting=scene_data.get("setting", {}),
            direction=scene_data.get("direction", {}),
            characters=scene_data.get("characters", []),
            key_elements=scene_data.get("key_elements", []),
            writing_notes=scene_data.get("writing_notes", {}),
            auto_generated=True,
            generation_source=[
                f"プロジェクト設定: {self.project_context.project_name}",
                f"テンプレート: {template.name}",
                f"ジャンル設定: {self.project_context.genre}",
            ],
            created_at=project_now().datetime,
            updated_at=project_now().datetime,
        )

    def _record_generation_history(
        self, scene_category: str, scene_id: str, template: SceneTemplate, options: GenerationOptions | None
    ) -> None:
        """生成履歴を記録"""
        history_entry = {
            "timestamp": project_now().datetime.isoformat(),
            "scene_category": scene_category,
            "scene_id": scene_id,
            "template_used": template.name,
            "project_context": self.project_context.project_name,
            "options": options.to_dict(),
        }
        self.generation_history.append(history_entry)

    def can_generate_scene(self, scene_category: str) -> bool:
        """指定カテゴリのシーンを生成可能かチェック"""
        if not self.project_context:
            return False

        # カテゴリ対応のテンプレートが存在するか
        return any(t.category == scene_category for t in self.available_templates)

    def get_available_categories(self) -> list[str]:
        """利用可能なシーンカテゴリ一覧を取得"""
        return list({t.category for t in self.available_templates})

    def get_template(self, template_name: str) -> SceneTemplate | None:
        """テンプレートを名前で取得"""
        for template in self.available_templates:
            if template.name == template_name:
                return template
        return None

    def get_generation_history(self) -> list[dict[str, Any]]:
        """生成履歴を取得"""
        return self.generation_history.copy()

    def get_generation_statistics(self) -> dict[str, Any]:
        """生成統計情報を取得"""
        return self._get_statistics_impl()

    def get_scene_statistics(self) -> dict[str, Any]:
        """シーン統計情報を取得(エイリアス)"""
        return self._get_statistics_impl()

    def _get_statistics_impl(self) -> dict[str, Any]:
        """統計情報取得の内部実装"""
        if not self.generation_history:
            return {
                "total_generations": 0,
                "total_scenes": 0,
                "categories_used": [],
                "templates_used": [],
                "by_category": {},
                "average_per_day": 0.0,
            }

        categories = [entry["scene_category"] for entry in self.generation_history]
        templates = [entry["template_used"] for entry in self.generation_history]

        # カテゴリ別統計
        by_category = {}
        for category in categories:
            by_category[category] = by_category.get(category, 0) + 1

        # 日別の生成数計算(簡易版)
        dates = [entry["timestamp"][:10] for entry in self.generation_history]
        unique_dates = list(set(dates))
        avg_per_day = len(self.generation_history) / max(len(unique_dates), 1)

        return {
            "total_generations": len(self.generation_history),
            "total_scenes": len(self.generation_history),
            "categories_used": list(set(categories)),
            "templates_used": list(set(templates)),
            "by_category": by_category,
            "average_per_day": round(avg_per_day, 1),
        }

    def _add_default_templates(self) -> None:
        """デフォルトテンプレートを追加"""
        default_templates = [
            SceneTemplate(
                name="emotional_default",
                category="emotional_scenes",
                is_default=True,
                setting_patterns={"location": ["emotional_setting"]},
            ),
            SceneTemplate(
                name="climax_default",
                category="climax_scenes",
                is_default=True,
                setting_patterns={"location": ["climax_setting"]},
            ),
            SceneTemplate(
                name="romance_default",
                category="romance_scenes",
                is_default=True,
                setting_patterns={"location": ["romance_setting"]},
            ),
        ]

        for template in default_templates:
            self.available_templates.append(template)

    def clear_generation_history(self) -> None:
        """生成履歴をクリア"""
        self.generation_history.clear()
