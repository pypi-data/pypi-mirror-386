#!/usr/bin/env python3

"""Domain.services.smart_template_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""スマートテンプレートサービス

プロジェクトの特性に応じて動的にテンプレートを
カスタマイズする高度なテンプレート生成機能
"""


from dataclasses import dataclass
from enum import Enum
from typing import Any

from noveler.domain.value_objects.workflow_stage_type import WorkflowStageType


class GenreType(Enum):
    """ジャンル分類"""

    FANTASY = "ファンタジー"
    SF = "SF"
    ROMANCE = "恋愛"
    MYSTERY = "ミステリー"
    SCHOOL = "学園"
    ISEKAI = "異世界"
    SLICE_OF_LIFE = "日常系"
    ACTION = "アクション"


@dataclass
class ProjectCharacteristics:
    """プロジェクト特性"""

    genre: GenreType
    target_length: int  # 予定話数
    target_audience: str  # ターゲット読者
    serialization_pace: str  # 連載ペース
    complexity_level: str  # 複雑度レベル


class SmartTemplateService:
    """スマートテンプレートサービス"""

    def __init__(self) -> None:
        self.genre_templates = self._initialize_genre_templates()
        self.length_adjustments = self._initialize_length_adjustments()

    def generate_optimized_template(
        self,
        stage_type: WorkflowStageType,
        project_characteristics: ProjectCharacteristics,
        project_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """プロジェクト特性に最適化されたテンプレートを生成

        Args:
            stage_type: ワークフロー段階タイプ
            project_characteristics: プロジェクト特性
            project_context: プロジェクトコンテキスト

        Returns:
            Dict[str, Any]: 最適化されたテンプレート
        """
        # ベーステンプレートの取得
        base_template = self._get_base_template(stage_type)

        # ジャンル別カスタマイズ
        genre_customized = self._apply_genre_customization(
            base_template,
            project_characteristics.genre,
            stage_type,
        )

        # 長さ別調整
        length_adjusted = self._apply_length_adjustments(
            genre_customized,
            project_characteristics.target_length,
            stage_type,
        )

        # プロジェクト固有情報の適用
        context_applied = self._apply_project_context(
            length_adjusted,
            project_context,
        )

        # 最終調整
        return self._apply_final_optimizations(
            context_applied,
            project_characteristics,
        )

    def _get_base_template(self, stage_type: WorkflowStageType) -> dict[str, Any]:
        """ベーステンプレートの取得"""
        if stage_type == WorkflowStageType.MASTER_PLOT:
            return {
                "project_info": {
                    "title": "[プロジェクトタイトル]",
                    "genre": "[ジャンル]",
                    "target_episodes": "[予定話数]",
                    "target_audience": "[ターゲット読者]",
                    "completion_date": "[完結予定]",
                },
                "story_structure": {
                    "theme": "[メインテーマ]",
                    "hook": "[読者を引き込む要素]",
                    "conflict": "[主要な対立構造]",
                    "resolution": "[解決方法]",
                },
                "character_arcs": {},
                "plot_progression": {},
                "world_building": {},
                "themes_and_messages": {},
            }
        if stage_type == WorkflowStageType.CHAPTER_PLOT:
            return {
                "chapter_info": {
                    "number": "[章番号]",
                    "title": "[章タイトル]",
                    "purpose": "[この章の役割]",
                    "episodes_count": "[含まれる話数]",
                },
                "chapter_arc": {
                    "opening": "[章の導入]",
                    "development": "[展開部分]",
                    "climax": "[章のクライマックス]",
                    "resolution": "[章の解決/次章への橋渡し]",
                },
                "character_focus": {},
                "plot_threads": {},
                "foreshadowing": {},
            }
        # EPISODE_PLOT
        return {
            "episode_info": {
                "number": "[話数]",
                "title": "[話タイトル]",
                "word_count_target": 3000,
                "estimated_reading_time": "10-12分",
            },
            "episode_structure": {
                "hook": "[冒頭の引き]",
                "development": "[本編の展開]",
                "climax": "[話のクライマックス]",
                "conclusion": "[結末/次話への引き]",
            },
            "scenes": {},
            "character_interactions": {},
            "advancement": {},
        }

    def _apply_genre_customization(
        self, template: dict[str, Any], genre: GenreType, stage_type: WorkflowStageType
    ) -> dict[str, Any]:
        """ジャンル別カスタマイズの適用"""
        customized = template.copy()

        if genre == GenreType.FANTASY:
            if stage_type == WorkflowStageType.MASTER_PLOT:
                customized["magic_system"] = {
                    "type": "[魔法の種類]",
                    "rules": "[魔法のルール]",
                    "limitations": "[制約条件]",
                    "cost": "[使用コスト]",
                }
                customized["world_building"]["fantasy_elements"] = {
                    "races": "[種族設定]",
                    "geography": "[地理・地名]",
                    "history": "[世界の歴史]",
                    "culture": "[文化・習慣]",
                }

        elif genre == GenreType.SF:
            if stage_type == WorkflowStageType.MASTER_PLOT:
                customized["technology_system"] = {
                    "tech_level": "[技術レベル]",
                    "key_technologies": "[重要技術]",
                    "scientific_basis": "[科学的根拠]",
                    "social_impact": "[社会への影響]",
                }

        elif genre == GenreType.MYSTERY:
            if stage_type == WorkflowStageType.MASTER_PLOT:
                customized["mystery_structure"] = {
                    "crime": "[事件内容]",
                    "clues": "[手がかり配置]",
                    "red_herrings": "[ミスリード要素]",
                    "revelation": "[真相解明]",
                }

        elif genre == GenreType.ROMANCE and stage_type == WorkflowStageType.MASTER_PLOT:
            customized["relationship_development"] = {
                "meeting": "[出会い]",
                "attraction": "[惹かれる要因]",
                "obstacles": "[恋愛の障害]",
                "resolution": "[関係の発展]",
            }

        return customized

    def _apply_length_adjustments(
        self, template: dict[str, Any], target_length: int, stage_type: WorkflowStageType
    ) -> dict[str, Any]:
        """長さに応じた調整"""
        adjusted = template.copy()

        if stage_type == WorkflowStageType.MASTER_PLOT:
            if target_length <= 20:  # 短編:
                adjusted["pacing"] = {
                    "type": "compressed",
                    "focus": "核心的な要素に集中",
                    "development_speed": "fast",
                }
            elif target_length <= 100:  # 中編
                adjusted["pacing"] = {
                    "type": "balanced",
                    "focus": "バランス良く展開",
                    "development_speed": "medium",
                }
            else:  # 長編
                adjusted["pacing"] = {
                    "type": "extended",
                    "focus": "詳細な世界構築と人物描写",
                    "development_speed": "slow",
                }

        return adjusted

    def _apply_project_context(self, template: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
        """プロジェクト固有情報の適用"""
        contextualized = template.copy()

        if context:
            project_context_block = contextualized.setdefault("project_context", {})

            if "title" in context:
                self._replace_placeholder(contextualized, "[プロジェクトタイトル]", context["title"])
                project_context_block["title"] = context["title"]

            if "genre" in context:
                self._replace_placeholder(contextualized, "[ジャンル]", context["genre"])
                project_context_block["genre"] = context["genre"]

            if "target_audience" in context:
                self._replace_placeholder(contextualized, "[ターゲット読者]", context["target_audience"])
                project_context_block["target_audience"] = context["target_audience"]

        return contextualized

    def _replace_placeholder(self, obj: object, placeholder: str, value: str) -> None:
        """プレースホルダーの再帰的置換"""
        if isinstance(obj, dict):
            for key, val in obj.items():
                if isinstance(val, str) and placeholder in val:
                    obj[key] = val.replace(placeholder, value)
                else:
                    self._replace_placeholder(val, placeholder, value)
        elif isinstance(obj, list):
            for i, val in enumerate(obj):
                if isinstance(val, str) and placeholder in val:
                    obj[i] = val.replace(placeholder, value)
                else:
                    self._replace_placeholder(val, placeholder, value)

    def _apply_final_optimizations(
        self, template: dict[str, Any], characteristics: ProjectCharacteristics
    ) -> dict[str, Any]:
        """最終最適化の適用"""
        optimized = template.copy()

        # メタデータの追加
        optimized["template_metadata"] = {
            "generated_for_genre": characteristics.genre.value,
            "target_length": characteristics.target_length,
            "optimization_level": "smart_template_v1.0",
            "generation_timestamp": "auto_generated",
        }

        # 品質保証コメントの追加
        optimized["usage_notes"] = {
            "customization": f"このテンプレートは{characteristics.genre.value}ジャンル用に最適化されています",
            "modification": "必要に応じてプロジェクトに合わせて調整してください",
            "reference": "詳細は A_執筆ガイド/A20_プロット作成ガイド.md を参照",
        }

        return optimized

    def _initialize_genre_templates(self) -> dict[GenreType, dict[str, Any]]:
        """ジャンル別テンプレートの初期化"""
        return {
            GenreType.FANTASY: {
                "required_elements": ["magic_system", "world_building"],
                "optional_elements": ["races", "mythology"],
                "common_themes": ["成長", "善悪の対立", "運命"],
            },
            GenreType.SF: {
                "required_elements": ["technology_system", "scientific_basis"],
                "optional_elements": ["space_setting", "time_travel"],
                "common_themes": ["進歩", "人間性", "未来への警鐘"],
            },
            # 他のジャンルも同様に定義
        }

    def _initialize_length_adjustments(self) -> dict[str, dict[str, Any]]:
        """長さ別調整の初期化"""
        return {
            "short": {"chapters": "1-3", "episodes_per_chapter": "5-10"},
            "medium": {"chapters": "3-10", "episodes_per_chapter": "8-15"},
            "long": {"chapters": "10+", "episodes_per_chapter": "10-20"},
        }
