# File: src/noveler/domain/initialization/entities.py
# Purpose: Define initialization domain aggregates for Noveler, covering
#          project templates and initialization lifecycle state.
# Context: Used by initialization use cases, repositories, and tests; depends
#          on value objects under noveler.domain.initialization.

"""Domain.initialization.entities
Where: Domain entities modelling initialization state.
What: Store setup progress, configuration, and validation outcomes.
Why: Support reproducible project initialization workflows.
"""

from __future__ import annotations

"""プロジェクト初期化ドメイン - エンティティ"""


from dataclasses import dataclass, field
import importlib
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.domain.initialization.value_objects import Genre, InitializationConfig, WritingStyle
from noveler.domain.interfaces.path_service_protocol import get_path_service_manager
from noveler.domain.value_objects.path_configuration import DEFAULT_PATH_CONFIG


def _get_common_path_service_factory() -> Any | None:
    """Return shared path service factory when presentation helper is available."""

    try:
        module = importlib.import_module("noveler.presentation.shared.shared_utilities")
    except Exception:
        return None

    return getattr(module, "get_common_path_service", None)

# B20準拠修正: Infrastructure依存をInterface経由に変更
# from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class InitializationStatus(Enum):
    """プロジェクト初期化のステータス。

    プロジェクトの初期化処理の各段階を表す列挙型。
    """

    STARTED = "started"
    TEMPLATE_SELECTED = "template_selected"
    CONFIG_VALIDATED = "config_validated"
    FILES_CREATED = "files_created"
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


@dataclass(init=False)
class ProjectTemplate:
    """プロジェクトテンプレートエンティティ

    ビジネスルール:
    - ジャンル適合性検証
    - ファイル構造完整性チェック
    - カスタマイズ適用
    """

    template_id: str
    genre: Genre
    name: str
    description: str
    directory_structure: list[str] = field(default_factory=list)
    customizations: dict[str, Any] = field(default_factory=dict)
    structure: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        template_id: str,
        name: str,
        description: str,
        genre: Genre | None = None,
        directory_structure: list[str] | None = None,
        customizations: dict[str, Any] | None = None,
        structure: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        _genre: Genre | None = None,
        _name: str | None = None,
        _description: str | None = None,
    ) -> None:
        assigned_genre = genre or _genre
        if assigned_genre is None:
            msg = "genre is required"
            raise ValueError(msg)

        self.template_id = template_id
        self.genre = assigned_genre
        # 互換性保持用の隠し属性
        self._genre = assigned_genre

        self.name = _name or name
        self.description = _description or description
        self.directory_structure = list(directory_structure or [])
        self.customizations = dict(customizations or {})
        self.structure = dict(structure or {})
        self.metadata = dict(metadata or {})

    def is_suitable_for_genre(self, target_genre: Genre) -> bool:
        """ジャンル適合性チェック"""
        # 完全一致が最優先
        if self.genre == target_genre:
            return True

        # 汎用テンプレートの場合(basicは汎用ではない)
        return self.template_id.endswith("_universal")

    def set_directory_structure(self, directories: list[str]) -> None:
        """ディレクトリ構造設定"""
        self.directory_structure = directories

    def validate_structure(self) -> bool:
        """ディレクトリ構造の検証"""
        # ハードコーディング排除: 統合パス管理システム経由で取得

        # B20準拠: Path ServiceはDI注入されたものを使用
        # TODO: DI注入された path_service を使用するように修正が必要
        try:
            manager = get_path_service_manager()
            path_service = manager.create_common_path_service()
        except Exception:
            path_service = _FallbackPathService(Path.cwd())

        def _normalise(entry: str) -> str:
            path_entry = Path(entry)
            if path_entry.name:
                return path_entry.name
            parts = [part for part in path_entry.parts if part]
            if parts:
                return parts[-1]
            return entry.strip()

        required_names = {
            _normalise(path_service.get_plots_dir()),
            _normalise(path_service.get_manuscript_dir()),
            _normalise(path_service.get_management_dir()),
        }

        structure_names = {
            _normalise(entry)
            for entry in self.directory_structure
            if entry and entry.strip()
        }

        if required_names.issubset(structure_names):
            return True

        # フォールバック: 既定ディレクトリ名での検証（設定未取得時の互換性）
        fallback_required = {
            DEFAULT_PATH_CONFIG.plots,
            DEFAULT_PATH_CONFIG.manuscripts,
            DEFAULT_PATH_CONFIG.management,
        }
        return fallback_required.issubset(structure_names)

    def apply_customizations(self, custom_settings: dict[str, Any]) -> ProjectTemplate:
        """カスタマイズ適用(新しいインスタンス返却)"""
        new_template = ProjectTemplate(
            template_id=self.template_id,
            genre=self.genre,
            name=self.name,
            description=self.description,
            directory_structure=self.directory_structure.copy(),
            customizations=self.customizations.copy(),
            structure=self.structure.copy(),
            metadata=self.metadata.copy(),
        )

        new_template.customizations.update(custom_settings)
        return new_template

    def get_customization(self, key: str) -> object:
        """カスタマイズ設定取得"""
        return self.customizations.get(key)

    def has_customization(self, key: str) -> bool:
        """カスタマイズ設定存在チェック"""
        return key in self.customizations


class _FallbackPathService:
    """Minimal path service used when the factory is unavailable during validation."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    def get_plots_dir(self) -> Path:
        return get_default_plot_dir(self._project_root)

    def get_manuscript_dir(self) -> Path:
        return get_default_manuscript_dir(self._project_root)

    def get_management_dir(self) -> Path:
        return get_default_management_dir(self._project_root)


@dataclass(init=False)
class ProjectInitialization:
    """プロジェクト初期化集約ルート

    ビジネスルール:
    - 初期化プロセスのライフサイクル管理
    - テンプレート・ジャンル適合性検証
    - 品質基準自動設定
    """

    initialization_id: str
    config: InitializationConfig
    status: InitializationStatus = InitializationStatus.STARTED
    selected_template_id: str | None = None
    created_files: list[str] = field(default_factory=list)
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completion_rate: float = 0.0

    def __init__(
        self,
        config: InitializationConfig | str | None = None,
        initialization_id: str | InitializationConfig | None = None,
        status: InitializationStatus = InitializationStatus.STARTED,
        selected_template_id: str | None = None,
        created_files: list[str] | None = None,
        error_message: str | None = None,
        created_at: datetime | None = None,
        *,
        _initialization_id: str | None = None,
    ) -> None:
        """Create a project initialization aggregate with legacy argument support.

        Purpose:
            Accept both the modern signature ``(config=..., initialization_id=...)`` and
            the historical positional order ``(initialization_id, config)``.

        Args:
            config: Initialization settings or, for legacy positional calls, the initialization id.
            initialization_id: Initialization identifier or legacy position for the config object.
            status: Current initialization status.
            selected_template_id: Previously selected template identifier.
            created_files: Files produced during initialization.
            error_message: Last error message, if any.
            created_at: Timestamp for initialization creation.
            _initialization_id: Hydration hook used by repositories.

        Raises:
            ValueError: When the initialization id or configuration cannot be resolved.
        """
        assigned_id: str | None = None
        resolved_config: InitializationConfig | None = None

        if isinstance(config, InitializationConfig):
            resolved_config = config
        elif isinstance(config, str) and config:
            assigned_id = config

        if isinstance(initialization_id, InitializationConfig):
            resolved_config = initialization_id
        elif isinstance(initialization_id, str) and initialization_id:
            assigned_id = assigned_id or initialization_id

        if _initialization_id and not assigned_id:
            assigned_id = _initialization_id

        if not assigned_id:
            msg = "initialization_id is required"
            raise ValueError(msg)
        if resolved_config is None:
            msg = "config is required"
            raise ValueError(msg)

        self.initialization_id = assigned_id
        self._initialization_id = assigned_id
        self.config = resolved_config
        self._resolved_config = resolved_config
        self.status = status
        self.selected_template_id = selected_template_id
        self.created_files = list(created_files or [])
        self.error_message = error_message
        self.created_at = created_at or datetime.now(timezone.utc)
        self.completion_rate = 0.0

    def select_template(self, template_id: str) -> None:
        """テンプレート選択"""
        if self.status != InitializationStatus.STARTED:
            msg = "テンプレート選択は初期状態でのみ可能です"
            raise ValueError(msg)

        # ビジネスルール: テンプレートのジャンル適合性チェック
        # 簡略化実装(実際はリポジトリからテンプレート取得が必要)
        if not self._is_template_compatible(template_id):
            msg = "テンプレートがジャンルに適合していません"
            raise ValueError(msg)

        self.selected_template_id = template_id
        self.status = InitializationStatus.TEMPLATE_SELECTED

    def _is_template_compatible(self, template_id: str) -> bool:
        """テンプレート互換性チェック(簡略化)"""
        genre_mappings = {
            "fantasy_basic": [Genre.FANTASY],
            "fantasy_light": [Genre.FANTASY],
            "romance_basic": [Genre.ROMANCE],
            "romance_emotional": [Genre.ROMANCE],  # TDD: TemplateSelectionServiceで使用される実際のID
            "mystery_basic": [Genre.MYSTERY],
            "mystery_logical": [Genre.MYSTERY],  # TDD: TemplateSelectionServiceで使用される実際のID
            "sf_basic": [Genre.SCIENCE_FICTION],
            "sf_hard": [Genre.SCIENCE_FICTION],  # TDD: TemplateSelectionServiceで使用される実際のID
            "universal_basic": list(Genre),  # 汎用テンプレート
        }

        compatible_genres = genre_mappings.get(template_id, [])
        config_obj = getattr(self, "_resolved_config", self.config)
        # Enum値ベースで比較
        compatible_genre_values = [g.value for g in compatible_genres]
        genre_attr = getattr(config_obj, "genre", None)
        genre_value = getattr(genre_attr, "value", None) if genre_attr is not None else None
        return genre_value in compatible_genre_values

    def validate_configuration(self) -> None:
        """設定検証"""
        if self.status != InitializationStatus.TEMPLATE_SELECTED:
            msg = "テンプレート選択後にのみ設定検証可能です"
            raise ValueError(msg)

        if not self.config.is_valid():
            self.fail_with_error("設定に不備があります")
            return

        self.status = InitializationStatus.CONFIG_VALIDATED

    def create_project_files(self) -> None:
        """プロジェクトファイル作成"""
        if self.status != InitializationStatus.CONFIG_VALIDATED:
            msg = "設定検証後にのみファイル作成可能です"
            raise ValueError(msg)

        # 簡略化実装(実際はファイルシステム操作が必要)
        base_files = [
            f"{self.config.project_name}/プロジェクト設定.yaml",
            f"{self.config.project_name}/10_企画/企画書.yaml",
            f"{self.config.project_name}/20_プロット/全体構成.yaml",
            f"{self.config.project_name}/30_設定集/キャラクター.yaml",
            f"{self.config.project_name}/50_管理資料/品質チェック設定.yaml",
        ]

        self.created_files = base_files
        self.status = InitializationStatus.FILES_CREATED

    def complete_initialization(self) -> None:
        """初期化完了"""
        if self.status != InitializationStatus.FILES_CREATED:
            msg = "ファイル作成後にのみ完了可能です"
            raise ValueError(msg)

        self.status = InitializationStatus.COMPLETED

    def fail_with_error(self, error_message: str) -> None:
        """エラーによる初期化失敗"""
        self.error_message = error_message
        self.status = InitializationStatus.FAILED

    def is_completed(self) -> bool:
        """完了状態チェック"""
        return self.status == InitializationStatus.COMPLETED

    def template_applied(self, template: ProjectTemplate) -> None:
        """テンプレート適用後の状態更新"""
        self.selected_template_id = template.template_id
        if isinstance(getattr(self.config, "additional_settings", None), dict):
            self.config.additional_settings.setdefault("based_on_template", template.template_id)
            if template.structure:
                self.config.additional_settings.setdefault("template_structure", template.structure)
        self.status = InitializationStatus.TEMPLATE_SELECTED

    def start(self) -> None:
        """初期化処理を開始"""
        if self.status not in {InitializationStatus.TEMPLATE_SELECTED, InitializationStatus.CONFIG_VALIDATED}:
            msg = "テンプレート適用後にのみ開始可能です"
            raise ValueError(msg)
        self.status = InitializationStatus.IN_PROGRESS

    def complete(self) -> None:
        """初期化処理を完了"""
        self.status = InitializationStatus.COMPLETED
        self.completion_rate = 100.0

    def generate_quality_standards(self) -> dict[str, float]:
        """プロジェクト固有品質基準生成"""
        standards = {
            "readability_target": 0.8,
            "dialogue_ratio_target": 0.35,
            "sentence_variety_target": 0.7,
            "narrative_depth_target": 0.75,
        }

        # ジャンル別調整
        if self.config.genre == Genre.MYSTERY:
            standards["logical_consistency"] = 0.8
            standards["plot_tension"] = 0.7
            standards["dialogue_ratio_target"] = 0.4  # ミステリーは会話やや多め
        elif self.config.genre == Genre.ROMANCE:
            standards["emotional_depth"] = 0.8
            standards["character_interaction"] = 0.75
            standards["dialogue_ratio_target"] = 0.45  # ロマンスは会話重視
        elif self.config.genre == Genre.FANTASY:
            standards["world_building_consistency"] = 0.8
            standards["descriptive_richness"] = 0.7

        # スタイル別調整
        if self.config.writing_style == WritingStyle.SERIOUS:
            if abs(standards["dialogue_ratio_target"] - 0.35) < 1e-9:
                standards["dialogue_ratio_target"] = round(max(0.2, standards["dialogue_ratio_target"] - 0.05), 3)
            standards["narrative_depth_target"] = round(min(1.0, standards["narrative_depth_target"] + 0.05), 3)
            standards["readability_target"] = round(max(0.5, standards["readability_target"] - 0.05), 3)

        return standards
