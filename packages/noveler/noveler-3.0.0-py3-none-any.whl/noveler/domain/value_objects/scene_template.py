"""Domain.value_objects.scene_template
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""シーンテンプレート値オブジェクト
シーン生成用のテンプレート定義
"""


from dataclasses import dataclass, field
from typing import Any

from noveler.domain.value_objects.generation_options import GenerationOptions


@dataclass(frozen=True)
class SceneTemplate:
    """シーンテンプレート値オブジェクト"""

    name: str
    category: str
    is_default: bool = False

    # テンプレート構造
    setting_patterns: dict[str, list[str]] = field(default_factory=dict)
    direction_templates: dict[str, str] = field(default_factory=dict)
    character_selection_rules: list[str] = field(default_factory=list)
    key_elements_by_genre: dict[str, list[str]] = field(default_factory=dict)
    writing_notes_templates: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """値オブジェクトの不変条件を検証"""
        self._validate_required_fields()
        self._validate_template_structure()

    def _validate_required_fields(self) -> None:
        """必須フィールドの検証"""
        if not self.name or len(self.name.strip()) == 0:
            msg = "テンプレート名は必須です"
            raise ValueError(msg)

        if not self.category or len(self.category.strip()) == 0:
            msg = "カテゴリは必須です"
            raise ValueError(msg)

    def _validate_template_structure(self) -> None:
        """テンプレート構造の検証"""
        # 最低限の構造要素があることを確認
        required_patterns = ["location", "time", "atmosphere"]
        setting_keys = list(self.setting_patterns.keys())

        if not any(key in setting_keys for key in required_patterns):
            # 警告レベル:必須パターンがない場合でも動作はする
            pass

    def is_valid(self) -> bool:
        """テンプレートの有効性をチェック"""
        try:
            self._validate_required_fields()
            self._validate_template_structure()
            return True
        except ValueError:
            return False

    def apply_to_project(self, project_info: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
        """プロジェクト情報にテンプレートを適用"""

        if not isinstance(options, GenerationOptions):
            msg = "optionsはGenerationOptionsの実例である必要があります"
            raise TypeError(msg)

        # ジャンル特性を取得
        genre_characteristics = project_info.get("genre_characteristics", {})
        genre = project_info.get("_genre", "")

        # 設定生成
        setting = self._generate_setting(genre_characteristics, options.detail_level)

        # 演出指示生成
        direction = self._generate_direction(genre, options.detail_level)

        # キャラクター選択
        characters = self._select_characters(project_info, options.detail_level)

        # 重要要素生成
        key_elements = self._generate_key_elements(genre, options.detail_level)

        # 執筆ノート生成
        writing_notes = self._generate_writing_notes(genre, options.detail_level)

        return {
            "setting": setting,
            "direction": direction,
            "characters": characters,
            "key_elements": key_elements,
            "writing_notes": writing_notes,
        }

    def _generate_setting(self, genre_characteristics: dict, _detail_level: str) -> dict[str, str]:
        """設定情報を生成"""
        setting = {}

        # 場所
        if "location" in self.setting_patterns:
            locations = self.setting_patterns["location"]
            if genre_characteristics.get("typical_locations"):
                # ジャンル特性を優先
                setting["location"] = genre_characteristics["typical_locations"][0]
            elif locations:
                setting["location"] = locations[0]
            else:
                setting["location"] = "重要な場所"

        # 時間
        if "time" in self.setting_patterns:
            times = self.setting_patterns["time"]
            setting["time"] = times[0] if times else "適切な時間"

        # 天候
        if "weather" in self.setting_patterns:
            weather_effects = genre_characteristics.get("weather_effects", [])
            if weather_effects:
                setting["weather"] = weather_effects[0]
            else:
                weathers = self.setting_patterns["weather"]
                setting["weather"] = weathers[0] if weathers else "通常の天候"

        # 雰囲気
        if "atmosphere" in self.setting_patterns:
            atmosphere_patterns = genre_characteristics.get("atmosphere_patterns", [])
            if atmosphere_patterns:
                setting["atmosphere"] = atmosphere_patterns[0]
            else:
                atmospheres = self.setting_patterns["atmosphere"]
                setting["atmosphere"] = atmospheres[0] if atmospheres else "緊張感のある"

        return setting

    def _generate_direction(self, genre: str, _detail_level: str) -> dict[str, str]:
        """演出指示を生成"""
        direction = {}

        # ペース配分
        if "pacing" in self.direction_templates:
            direction["pacing"] = self.direction_templates["pacing"]
        else:
            direction["pacing"] = "前半:準備、中盤:展開、終盤:解決"

        # 緊張カーブ
        if "tension_curve" in self.direction_templates:
            direction["tension_curve"] = self.direction_templates["tension_curve"]
        else:
            direction["tension_curve"] = "段階的上昇→最高潮→解決"

        # 感情の流れ(ジャンル別)
        genre_emotion_map = {
            "ファンタジー": "恐怖→決意→友情→勝利の歓喜",
            "恋愛": "不安→告白→感動→幸福",
            "ミステリー": "混乱→推理→驚愕→解決感",
        }

        genre_lower = genre.lower()
        for key, emotion_flow in genre_emotion_map.items():
            if key.lower() in genre_lower:
                direction["emotional_flow"] = emotion_flow
                break
        else:
            direction["emotional_flow"] = "緊張→転換→解決→余韻"

        return direction

    def _select_characters(self, project_info: dict, detail_level: str) -> list[str]:
        """登場キャラクターを選択"""
        characters = []

        # 主人公は必須
        protagonist_info = project_info.get("protagonist_info")
        if protagonist_info:
            protagonist_name = protagonist_info.get("name", "主人公")
            characters.append(f"{protagonist_name}(主人公)")
        elif project_info.get("protagonist_name"):
            characters.append(f"{project_info['protagonist_name']}(主人公)")

        # カテゴリ別の追加キャラクター
        if self.category == "climax_scenes":
            # クライマックスにはアンタゴニストも登場
            antagonist_info = project_info.get("antagonist_info")
            if antagonist_info:
                antagonist_name = antagonist_info.get("name", "アンタゴニスト")
                characters.append(f"{antagonist_name}(アンタゴニスト)")

            # サポートキャラクター(詳細レベルに応じて)
            if detail_level in ["standard", "full"]:
                supporting_chars = project_info.get("supporting_characters", [])
                for char in supporting_chars[:2]:  # 最大2名
                    char_name = char.get("name", "サポート")
                    char_role = char.get("role", "仲間")
                    characters.append(f"{char_name}({char_role})")

        elif self.category == "romance_scenes":
            # ロマンスシーンには恋愛相手も登場
            supporting_chars = project_info.get("supporting_characters", [])
            for char in supporting_chars:
                if "ヒロイン" in char.get("role", ""):
                    char_name = char.get("name", "ヒロイン")
                    characters.append(f"{char_name}(ヒロイン)")
                    break

        return characters or ["主人公"]

    def _generate_key_elements(self, genre: str, _detail_level: str) -> list[str]:
        """重要要素を生成"""
        # ジャンル別の基本要素
        genre_elements = self.key_elements_by_genre.get(genre, [])

        # カテゴリ別の標準要素
        category_elements = {
            "climax_scenes": ["主人公の成長の集大成", "これまでの伏線の回収", "読者が予想できない展開"],
            "emotional_scenes": ["感情の高まりを示す描写", "キャラクター関係性の変化", "心情の内面描写"],
            "romance_scenes": ["互いの気持ちの確認", "関係性の進展", "将来への希望"],
        }

        elements = []
        elements.extend(genre_elements[:2])  # ジャンル要素を2つまで
        elements.extend(category_elements.get(self.category, [])[:3])  # カテゴリ要素を3つまで

        return elements or ["重要な展開"]

    def _generate_writing_notes(self, _genre: str, _detail_level: str) -> dict[str, list[str]]:
        """執筆ノートを生成"""
        notes = {"must_include": [], "avoid": []}

        # カテゴリ別の必須要素
        category_musts = {
            "climax_scenes": ["これまでの物語要素の集大成", "主人公の変化・成長を明確に示す", "読者の期待を上回る展開"],
            "emotional_scenes": ["キャラクターの内面を丁寧に描写", "感情変化の理由を明確に", "読者の共感を呼ぶ描写"],
        }

        # カテゴリ別の避けるべき要素
        category_avoids = {
            "climax_scenes": ["都合の良すぎる奇跡", "キャラクターの行動原理に反する言動", "過度に長い戦闘描写"],
            "emotional_scenes": ["説明的すぎる心理描写", "唐突な感情変化", "陳腐な表現の多用"],
        }

        notes["must_include"] = category_musts.get(self.category, ["重要な要素を含める"])
        notes["avoid"] = category_avoids.get(self.category, ["不自然な展開"])

        return notes

    @classmethod
    def create_default_template(cls, category: str) -> SceneTemplate:
        """デフォルトテンプレートを作成"""
        templates = {
            "climax_scenes": cls(
                name="default_climax",
                category="climax_scenes",
                is_default=True,
                setting_patterns={
                    "location": ["重要な場所", "象徴的な場所"],
                    "time": ["クライマックスの時間", "決戦の時"],
                },
            ),
            "emotional_scenes": cls(
                name="default_emotional",
                category="emotional_scenes",
                is_default=True,
                setting_patterns={"location": ["静かな場所", "特別な場所"], "time": ["感情的な時間", "内省の時"]},
            ),
            "romance_scenes": cls(
                name="default_romance",
                category="romance_scenes",
                is_default=True,
                setting_patterns={
                    "location": ["思い出の場所", "ロマンチックな場所"],
                    "time": ["ロマンチックな時間", "特別な時"],
                },
            ),
        }

        return templates.get(category, cls(name=f"default_{category}", category=category, is_default=True))
