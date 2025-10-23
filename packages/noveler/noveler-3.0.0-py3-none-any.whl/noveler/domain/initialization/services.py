# File: src/noveler/domain/initialization/services.py
# Purpose: Implement domain services that orchestrate project initialization
#          behaviours such as template selection and setup automation.
# Context: Used by higher-level application flows and unit tests; depends on
#          initialization value objects for configuration inputs.

"""Domain.initialization.services
Where: Domain services implementing project initialization behaviour.
What: Execute setup routines, validations, and environment configuration.
Why: Centralise initialization logic for reuse by application layers.
"""

from __future__ import annotations

"""プロジェクト初期化ドメイン - ドメインサービス"""


from dataclasses import dataclass
from typing import Any

from noveler.domain.initialization.value_objects import Genre, InitializationConfig, WritingStyle


@dataclass
class TemplateRanking:
    """テンプレートランキング結果"""

    template_id: str
    score: float
    reasoning: str


class TemplateSelectionService:
    """テンプレート選択ドメインサービス

    ビジネスルール:
    - 設定に基づく最適テンプレート選択
    - 適合度スコアリング
    - 選択理由の提供
    """

    def __init__(self) -> None:
        # 簡略化実装用のテンプレートデータ
        self._templates = {
            "fantasy_light": {
                "genre": Genre.FANTASY,
                "style_preferences": [WritingStyle.LIGHT, WritingStyle.COMEDY],
                "features": ["magic_system", "world_building", "character_growth"],
            },
            "fantasy_basic": {
                "genre": Genre.FANTASY,
                "style_preferences": [WritingStyle.SERIOUS, WritingStyle.LIGHT],
                "features": ["basic_fantasy", "standard_structure"],
            },
            "romance_emotional": {
                "genre": Genre.ROMANCE,
                "style_preferences": [WritingStyle.LIGHT, WritingStyle.SERIOUS],
                "features": ["relationship_focus", "emotional_depth"],
            },
            "mystery_logical": {
                "genre": Genre.MYSTERY,
                "style_preferences": [WritingStyle.SERIOUS, WritingStyle.DARK],
                "features": ["investigation_structure", "logical_progression"],
            },
            "sf_hard": {
                "genre": Genre.SCIENCE_FICTION,
                "style_preferences": [WritingStyle.SERIOUS],
                "features": ["scientific_accuracy", "technology_focus"],
            },
            "sf_basic": {
                "genre": Genre.SCIENCE_FICTION,
                "style_preferences": [WritingStyle.LIGHT, WritingStyle.SERIOUS],
                "features": ["basic_sf", "accessible_technology"],
            },
            "universal_basic": {
                "genre": None,  # 汎用
                "style_preferences": list(WritingStyle),
                "features": ["flexible_structure", "genre_agnostic"],
            },
        }

    def select_optimal_template(self, config: InitializationConfig) -> str:
        """設定に基づく最適テンプレート選択"""
        ranked_templates = self.rank_templates(config)

        if not ranked_templates:
            return "universal_basic"  # フォールバック

        return ranked_templates[0].template_id

    def rank_templates(self, config: InitializationConfig) -> list[TemplateRanking]:
        """テンプレート適合度ランキング"""
        rankings = []

        for template_id, template_data in self._templates.items():
            score = self._calculate_compatibility_score(config, template_id, template_data)
            reasoning = self._generate_reasoning(config, template_data, score)

            rankings.append(
                TemplateRanking(
                    template_id=template_id,
                    score=score,
                    reasoning=reasoning,
                ),
            )

        # スコア降順でソート
        rankings.sort(key=lambda x: x.score, reverse=True)
        return rankings

    def _calculate_compatibility_score(
        self,
        config: InitializationConfig,
        template_id: str,
        template_data: dict[str, Any],
    ) -> float:
        """互換性スコア計算"""
        score = 0.0

        template_genre = template_data["genre"]
        genre_matches = template_genre == config.genre
        is_universal = template_genre is None

        # ジャンル適合度 (40%)
        if genre_matches:
            score += 0.4
        elif is_universal:  # 汎用テンプレート
            score += 0.25

        # スタイル適合度 (30%)
        if config.writing_style in template_data["style_preferences"]:
            style_bonus = 0.3
            # 優先度が高いスタイルの場合はボーナス
            if template_data["style_preferences"][0] == config.writing_style:
                style_bonus *= 1.2

            if not genre_matches and not is_universal:
                style_bonus *= 0.5
            score += style_bonus

        # 更新頻度適合度 (20%)
        frequency_compatibility = {
            "daily": {"fantasy_light": 0.8, "romance_emotional": 0.9},
            "weekly": {"fantasy_basic": 0.9, "mystery_logical": 0.8},
            "monthly": {"sf_hard": 0.9},
        }

        template_freq_score = frequency_compatibility.get(
            config.update_frequency.value,
            {},
        ).get(template_id, 0.5)

        if not genre_matches and not is_universal:
            template_freq_score = min(template_freq_score, 0.5)

        score += 0.2 * template_freq_score

        # 特殊ボーナス (10%)
        if self._has_special_compatibility(config, template_id):
            score += 0.1

        return min(score, 1.0)  # 最大1.0

    def _has_special_compatibility(self, config: InitializationConfig, template_id: str) -> bool:
        """特殊互換性チェック"""
        # ライトファンタジーの組み合わせ
        if (
            config.genre == Genre.FANTASY
            and config.writing_style == WritingStyle.LIGHT
            and "fantasy_light" in template_id
        ):
            return True

        # ハードSFの組み合わせ
        return bool(
            config.genre == Genre.SCIENCE_FICTION
            and config.writing_style == WritingStyle.SERIOUS
            and "sf_hard" in template_id
        )

    def _generate_reasoning(
        self, config: InitializationConfig, template_data: dict[str, Any], score: float = 0.0
    ) -> str:
        """選択理由生成"""
        reasons = []

        if template_data["genre"] == config.genre:
            reasons.append(f"{config.genre.value}ジャンルに特化")
        elif template_data["genre"] is None:
            reasons.append("汎用テンプレートで柔軟性が高い")

        if config.writing_style in template_data["style_preferences"]:
            reasons.append(f"{config.writing_style.value}スタイルに適合")

        if score > 0.8:
            reasons.append("高い適合度")
        elif score > 0.6:
            reasons.append("適度な適合度")
        else:
            reasons.append("基本的な適合度")

        return "、".join(reasons)

    def get_selection_reasoning(self, config: InitializationConfig, template_id: str) -> str:
        """選択理由の詳細説明"""
        if template_id not in self._templates:
            return "不明なテンプレートです"

        template_data: dict[str, Any] = self._templates[template_id]
        score = self._calculate_compatibility_score(config, template_id, template_data)

        return self._generate_reasoning(config, template_data, score)


class ProjectSetupService:
    """プロジェクトセットアップドメインサービス

    ビジネスルール:
    - ディレクトリ構造生成
    - 初期ファイル作成
    - 設定ファイル生成
    """

    def generate_directory_structure(self, config: InitializationConfig, _template: dict[str, Any]) -> list[str]:
        """ディレクトリ構造生成"""
        base_structure = [
            f"{config.project_name}/",
            f"{config.project_name}/10_企画/",
            f"{config.project_name}/20_プロット/",
            f"{config.project_name}/20_プロット/章別プロット/",
            f"{config.project_name}/30_設定集/",
            f"{config.project_name}/40_原稿/",
            f"{config.project_name}/50_管理資料/",
            f"{config.project_name}/90_アーカイブ/",
        ]

        # ジャンル固有ディレクトリ追加
        if config.genre == Genre.FANTASY:
            base_structure.extend(
                [
                    f"{config.project_name}/30_設定集/魔法システム/",
                    f"{config.project_name}/30_設定集/種族設定/",
                ],
            )

        elif config.genre == Genre.SCIENCE_FICTION:
            base_structure.extend(
                [
                    f"{config.project_name}/30_設定集/技術仕様/",
                    f"{config.project_name}/30_設定集/世界年表/",
                ],
            )

        return base_structure

    def generate_initial_files(self, config: InitializationConfig) -> dict[str, str]:
        """初期ファイル生成"""
        files = {}

        # プロジェクト設定.yaml
        files[f"{config.project_name}/プロジェクト設定.yaml"] = self._generate_project_config(config)

        # 企画書.yaml
        files[f"{config.project_name}/10_企画/企画書.yaml"] = self._generate_project_plan(config)

        # 全体構成.yaml
        files[f"{config.project_name}/20_プロット/全体構成.yaml"] = self._generate_master_plot(config)

        # キャラクター.yaml
        files[f"{config.project_name}/30_設定集/キャラクター.yaml"] = self._generate_character_settings(config)

        return files

    def _generate_project_config(self, config: InitializationConfig) -> str:
        """プロジェクト設定YAML生成"""
        return f"""# プロジェクト設定
project_name: "{config.project_name}"
author: "{config.author_name}"
genre: "{config.genre.value}"
writing_style: "{config.writing_style.value}"
update_frequency: "{config.update_frequency.value}"

# 品質基準
quality_standards:
  readability_target: 0.8
  dialogue_ratio_target: 0.35

# 執筆設定
writing_settings:
  target_episode_length: 3000
  chapters_per_arc: 10
"""

    def _generate_project_plan(self, config: InitializationConfig) -> str:
        """企画書YAML生成"""
        return f"""# 企画書
title: "{config.project_name}"
author: "{config.author_name}"
genre: "{config.genre.value}"

# コンセプト
concept:
  theme: ""
  target_audience: ""
  unique_selling_point: ""

# あらすじ
synopsis:
  one_line: ""
  short: ""
  detailed: ""
"""

    def _generate_master_plot(self, config: InitializationConfig) -> str:
        """全体構成YAML生成"""
        return f"""# 全体構成
title: "{config.project_name}"

# 構成
structure:
  total_chapters: 0
  current_chapter: 0
  estimated_episodes: 0

# 三幕構成
acts:
  act1:
    description: "導入部"
    chapters: []
  act2:
    description: "展開部"
    chapters: []
  act3:
    description: "結末部"
    chapters: []
"""

    def _generate_character_settings(self, _config: InitializationConfig) -> str:
        """キャラクター設定YAML生成"""
        return """# キャラクター設定
characters:
  main:
    protagonist:
      name: ""
      age: 0
      personality: ""
      background: ""

  supporting: []

  antagonist:
    name: ""
    motivation: ""
"""


class QualityStandardConfigService:
    """品質基準設定ドメインサービス

    ビジネスルール:
    - ジャンル・スタイル別基準設定
    - 動的基準調整
    - 基準妥当性検証
    """

    def generate_quality_standards(self, config: InitializationConfig) -> dict[str, Any]:
        """品質基準生成"""
        # ベース基準
        standards = {
            "readability": {
                "target_score": 80,
                "weight": 1.0,
                "min_threshold": 70,
            },
            "dialogue_ratio": {
                "target_ratio": 0.35,
                "weight": 1.0,
                "acceptable_range": [0.2, 0.6],
            },
            "sentence_variety": {
                "target_score": 70,
                "weight": 1.0,
                "min_threshold": 60,
            },
        }

        # ジャンル別調整
        if config.genre == Genre.MYSTERY:
            standards["logical_consistency"] = {
                "target_score": 85,
                "weight": 1.2,
                "min_threshold": 75,
            }
            standards["dialogue_ratio"]["target_ratio"] = 0.4

        elif config.genre == Genre.ROMANCE:
            standards["emotional_depth"] = {
                "target_score": 80,
                "weight": 1.3,
                "min_threshold": 70,
            }
            standards["dialogue_ratio"]["target_ratio"] = 0.45

        elif config.genre == Genre.FANTASY:
            standards["world_building"] = {
                "target_score": 75,
                "weight": 1.1,
                "min_threshold": 65,
            }

        # スタイル別調整
        if config.writing_style == WritingStyle.LIGHT:
            standards["readability"]["target_score"] = 85
            standards["readability"]["weight"] = 1.2

        elif config.writing_style == WritingStyle.SERIOUS:
            standards["narrative_depth"] = {
                "target_score": 80,
                "weight": 1.2,
                "min_threshold": 70,
            }

        return standards
