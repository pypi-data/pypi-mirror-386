"""Domain.value_objects.project_context
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""プロジェクトコンテキスト値オブジェクト
プロジェクト情報を集約した不変オブジェクト
"""


from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProjectContext:
    """プロジェクトコンテキスト値オブジェクト

    プロジェクトの基本情報とシーン生成に必要な情報を集約
    """

    project_name: str
    genre: str
    protagonist_name: str | None = None
    setting_world: str | None = None
    theme: str | None = None
    structure_type: str = "三幕構成"

    # キャラクター情報
    main_characters: list[dict[str, Any]] = field(default_factory=list)
    character_relationships: list[dict[str, Any]] = field(default_factory=list)

    # プロット情報
    total_episodes: int | None = None
    act_structure: dict[str, Any] = field(default_factory=dict)
    turning_points: list[dict[str, Any]] = field(default_factory=list)

    # メタ情報
    quality_threshold: int = 80
    target_audience: str | None = None

    def __post_init__(self) -> None:
        """値オブジェクトの不変条件を検証"""
        self._validate_required_fields()
        self._validate_business_rules()

    def _validate_required_fields(self) -> None:
        """必須フィールドの検証"""
        if not self.project_name or len(self.project_name.strip()) == 0:
            msg = "プロジェクト名は必須です"
            raise ValueError(msg)

        if not self.genre or len(self.genre.strip()) == 0:
            msg = "ジャンルは必須です"
            raise ValueError(msg)

    def _validate_business_rules(self) -> None:
        """ビジネスルールの検証"""
        if self.quality_threshold is not None and not (0 <= self.quality_threshold <= 100):
            msg = "品質閾値は0-100の範囲で指定してください"
            raise ValueError(msg)

        if self.total_episodes is not None and self.total_episodes <= 0:
            msg = "総話数は正の整数で指定してください"
            raise ValueError(msg)

    def is_valid(self) -> bool:
        """コンテキストの有効性をチェック"""
        try:
            self._validate_required_fields()
            self._validate_business_rules()
            return True
        except ValueError:
            return False

    def has_character_info(self) -> bool:
        """キャラクター情報が利用可能かチェック"""
        return len(self.main_characters) > 0

    def has_plot_info(self) -> bool:
        """プロット情報が利用可能かチェック"""
        return bool(self.act_structure) or len(self.turning_points) > 0

    def get_protagonist_info(self) -> dict[str, Any] | None:
        """主人公情報を取得"""
        if self.protagonist_name:
            # 主人公名で検索
            for char in self.main_characters:
                if char.get("name") == self.protagonist_name:
                    return char
                if char.get("role") == "主人公":
                    return char

        # 主人公ロールで検索
        for char in self.main_characters:
            if char.get("role") == "主人公":
                return char

        return None

    def get_antagonist_info(self) -> dict[str, Any] | None:
        """アンタゴニスト情報を取得"""
        antagonist_roles = ["アンタゴニスト", "敵", "ボス", "魔王", "悪役"]

        for char in self.main_characters:
            char_role = char.get("role", "").lower()
            if any(role.lower() in char_role for role in antagonist_roles):
                return char

        return None

    def get_supporting_characters(self) -> list[dict[str, Any]]:
        """サポートキャラクター一覧を取得"""
        supporting_roles = ["ヒロイン", "相棒", "仲間", "メンター", "師匠"]

        supporting_chars = []
        for char in self.main_characters:
            char_role = char.get("role", "").lower()
            if any(role.lower() in char_role for role in supporting_roles):
                supporting_chars.append(char)

        return supporting_chars

    def get_genre_characteristics(self) -> dict[str, Any]:
        """ジャンル特性を取得"""
        genre_lower = self.genre.lower()

        genre_map = {
            "ファンタジー": {
                "typical_locations": ["魔王城", "異次元空間", "聖地", "古代遺跡"],
                "weather_effects": ["嵐", "雷雨", "神々しい光", "霧"],
                "atmosphere_patterns": ["神秘的", "荘厳", "緊迫", "幻想的"],
                "key_themes": ["善vs悪", "成長", "友情", "勇気"],
            },
            "恋愛": {
                "typical_locations": ["学校", "公園", "カフェ", "思い出の場所"],
                "weather_effects": ["夕焼け", "星空", "雪", "春風"],
                "atmosphere_patterns": ["甘い", "切ない", "ドキドキ", "温かい"],
                "key_themes": ["愛", "成長", "理解", "絆"],
            },
            "ミステリー": {
                "typical_locations": ["事件現場", "密室", "捜査本部", "犯人のアジト"],
                "weather_effects": ["霧", "雨", "曇天", "薄暗い"],
                "atmosphere_patterns": ["緊張", "不安", "謎めいた", "重厚"],
                "key_themes": ["真実", "正義", "推理", "暴露"],
            },
        }

        # 部分マッチで検索
        for key, characteristics in genre_map.items():
            if key in genre_lower or genre_lower in key:
                return characteristics

        # デフォルト特性
        return {
            "typical_locations": ["重要な場所"],
            "weather_effects": ["通常の天候"],
            "atmosphere_patterns": ["緊張感"],
            "key_themes": ["テーマ"],
        }

    def get_climax_episode_estimate(self) -> int | None:
        """クライマックス話数の推定"""
        if not self.total_episodes:
            return None

        # 三幕構成の場合、第三幕の終盤(80-90%地点)
        if self.structure_type == "三幕構成":
            return int(self.total_episodes * 0.85)

        # その他の構成でも同様の比率
        return int(self.total_episodes * 0.85)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "project_name": self.project_name,
            "genre": self.genre,
            "protagonist_name": self.protagonist_name,
            "setting_world": self.setting_world,
            "theme": self.theme,
            "structure_type": self.structure_type,
            "main_characters": self.main_characters,
            "character_relationships": self.character_relationships,
            "total_episodes": self.total_episodes,
            "act_structure": self.act_structure,
            "turning_points": self.turning_points,
            "quality_threshold": self.quality_threshold,
            "target_audience": self.target_audience,
            # 派生情報
            "protagonist_info": self.get_protagonist_info(),
            "antagonist_info": self.get_antagonist_info(),
            "supporting_characters": self.get_supporting_characters(),
            "genre_characteristics": self.get_genre_characteristics(),
            "climax_episode_estimate": self.get_climax_episode_estimate(),
        }

    @classmethod
    def from_project_files(cls, project_data: dict[str, Any]) -> ProjectContext:
        """プロジェクトファイルデータから構築"""
        # プロジェクト設定.yaml から基本情報
        project_info = project_data.get("project_settings", {})

        # キャラクター.yaml から
        character_data: dict[str, Any] = project_data.get("character_settings", {})

        # 全体構成.yaml から
        plot_data: dict[str, Any] = project_data.get("plot_settings", {})

        return cls(
            project_name=project_info.get("title", ""),
            genre=project_info.get("genre", ""),
            protagonist_name=project_info.get("protagonist", ""),
            setting_world=plot_data.get("world_setting"),
            theme=plot_data.get("theme"),
            structure_type=plot_data.get("structure_type", "三幕構成"),
            main_characters=character_data.get("main_characters", []),
            character_relationships=character_data.get("relationships", []),
            total_episodes=plot_data.get("total_episodes"),
            act_structure=plot_data.get("act_structure", {}),
            turning_points=plot_data.get("turning_points", []),
            quality_threshold=project_info.get("quality_threshold", 80),
            target_audience=project_info.get("target_audience"),
        )
