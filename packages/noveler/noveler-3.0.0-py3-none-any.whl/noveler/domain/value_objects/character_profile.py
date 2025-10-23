"""Domain.value_objects.character_profile
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""キャラクタープロファイル値オブジェクト

キャラクターの設定情報を保持する不変の値オブジェクト。
"""


from copy import deepcopy
from dataclasses import dataclass
from typing import Any

# キャラクター属性値の型
AttributeValue = str | int | float | bool | list[str] | dict[str, Any]


@dataclass(frozen=True)
class CharacterProfile:
    """キャラクタープロファイル

    キャラクターの名前と各種属性(外見、性格、話し方など)を
    保持する不変の値オブジェクト。
    """

    name: str
    attributes: dict[str, AttributeValue]

    def __post_init__(self) -> None:
        """初期化後の検証"""
        if not self.name or not isinstance(self.name, str):
            msg = "nameは必須です"
            raise TypeError(msg)

        # attributesを不変にするため、深いコピーを作成
        object.__setattr__(self, "attributes", deepcopy(self.attributes))

    def get_attribute(self, key: str, default: AttributeValue | None = None) -> AttributeValue:
        """属性を取得

        Args:
            key: 属性キー
            default: デフォルト値

        Returns:
            属性値
        """
        return self.attributes.get(key, default)

    def has_attribute(self, key: str) -> bool:
        """属性を持っているかチェック

        Args:
            key: 属性キー

        Returns:
            属性が存在する場合True
        """
        return key in self.attributes

    def get_appearance_attributes(self) -> dict[str, Any]:
        """外見に関する属性を取得

        Returns:
            外見属性の辞書
        """
        appearance_keys = [
            "hair_color",
            "eye_color",
            "height",
            "build",
            "skin_color",
            "facial_features",
            "clothing_style",
        ]
        return {key: value for key, value in self.attributes.items() if key in appearance_keys}

    def get_personality_attributes(self) -> dict[str, Any]:
        """性格に関する属性を取得

        Returns:
            性格属性の辞書
        """
        personality_keys = ["personality", "traits", "temperament", "likes", "dislikes", "fears", "goals"]
        return {key: value for key, value in self.attributes.items() if key in personality_keys}

    def get_speech_attributes(self) -> dict[str, AttributeValue]:
        """話し方に関する属性を取得

        Returns:
            話し方属性の辞書
        """
        speech_keys = ["speech_style", "dialect", "catchphrase", "verbal_tics", "formality_level"]
        return {key: value for key, value in self.attributes.items() if key in speech_keys}

    def with_updated_attribute(self, key: str, value: AttributeValue) -> CharacterProfile:
        """属性を更新した新しいインスタンスを作成

        Args:
            key: 更新する属性キー
            value: 新しい値

        Returns:
            更新された新しいCharacterProfile
        """
        new_attributes = deepcopy(self.attributes)
        new_attributes[key] = value
        return CharacterProfile(self.name, new_attributes)

    def merge_with(self, other: CharacterProfile) -> CharacterProfile:
        """他のプロファイルとマージした新しいインスタンスを作成

        Args:
            other: マージするプロファイル

        Returns:
            マージされた新しいCharacterProfile

        Raises:
            ValueError: 名前が異なる場合
        """
        if self.name != other.name:
            msg = f"異なるキャラクターのプロファイルはマージできません: {self.name} != {other.name}"
            raise ValueError(msg)

        merged_attributes = deepcopy(self.attributes)
        merged_attributes.update(other.attributes)

        return CharacterProfile(self.name, merged_attributes)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換

        Returns:
            プロファイルの辞書表現
        """
        return {"name": self.name, "attributes": deepcopy(self.attributes)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CharacterProfile:
        """辞書からインスタンスを作成

        Args:
            data: プロファイルデータ

        Returns:
            CharacterProfileインスタンス
        """
        return cls(name=data["name"], attributes=data.get("attributes", {}))

    # ------------------------------------------------------------------
    # A24 new schema helpers
    # ------------------------------------------------------------------

    def has_new_schema_data(self) -> bool:
        """A24新スキーマデータを保持しているか判定する。"""
        return isinstance(self.attributes.get("_raw_layers"), dict)

    def get_layer(self, layer_name: str) -> dict[str, Any]:
        """指定レイヤーの内容を返す（存在しなければ空辞書）。"""
        layers = self.attributes.get("_raw_layers", {})
        layer = layers.get(layer_name, {}) if isinstance(layers, dict) else {}
        return deepcopy(layer)

    def get_llm_prompt_profile(self) -> dict[str, Any]:
        """LLM プロンプト用プロファイルを返す。"""
        profile = self.attributes.get("_raw_llm_prompt_profile", {})
        return deepcopy(profile) if isinstance(profile, dict) else {}

    def get_narrative_notes(self) -> dict[str, Any]:
        """物語ノート（伏線・未解決課題など）を返す。"""
        notes = self.attributes.get("_raw_narrative_notes", {})
        return deepcopy(notes) if isinstance(notes, dict) else {}

    def get_psychological_summary(self) -> list[str]:
        """心理モデルのサマリ bullet を取得する。"""
        if not self.has_new_schema_data():
            return []

        layers = self.attributes.get("_raw_layers", {})
        if isinstance(layers, dict):
            for layer in layers.values():
                if not isinstance(layer, dict):
                    continue
                models = layer.get("psychological_models", {})
                if isinstance(models, dict) and "summary_bullets" in models:
                    bullets = models.get("summary_bullets", [])
                    return list(bullets) if isinstance(bullets, list) else []
        return []

    def get_decision_flow(self) -> dict[str, Any]:
        """心理モデルの意思決定フローを取得する。"""
        if not self.has_new_schema_data():
            return {}

        layers = self.attributes.get("_raw_layers", {})
        if isinstance(layers, dict):
            for layer in layers.values():
                if not isinstance(layer, dict):
                    continue
                models = layer.get("psychological_models", {})
                if isinstance(models, dict) and "decision_flow" in models:
                    flow = models.get("decision_flow", {})
                    return deepcopy(flow) if isinstance(flow, dict) else {}
        return {}

    def get_status(self) -> dict[str, Any]:
        """ライフサイクルなどのステータス情報を返す。"""
        status = self.attributes.get("_raw_status", {})
        return deepcopy(status) if isinstance(status, dict) else {}

    def get_logging_settings(self) -> dict[str, Any]:
        """ログ出力設定を返す。"""
        logging_settings = self.attributes.get("_raw_logging", {})
        return deepcopy(logging_settings) if isinstance(logging_settings, dict) else {}

    def get_lite_profile_hint(self) -> dict[str, Any]:
        """ライトプロフィール利用ヒントを返す。"""
        hint = self.attributes.get("_raw_lite_profile_hint", {})
        return deepcopy(hint) if isinstance(hint, dict) else {}

    def get_episode_snapshots(self) -> list[dict[str, Any]]:
        """エピソード別スナップショット一覧を返す。"""
        snapshots = self.attributes.get("_raw_episode_snapshots", [])
        return deepcopy(snapshots) if isinstance(snapshots, list) else []

    def get_character_goals(self) -> dict[str, Any]:
        """キャラクターの内外的ゴール情報を取得する。"""
        if not self.has_new_schema_data():
            return {}

        layers = self.attributes.get("_raw_layers", {})
        if isinstance(layers, dict):
            for layer in layers.values():
                if isinstance(layer, dict) and "character_goals" in layer:
                    goals = layer.get("character_goals", {})
                    return deepcopy(goals) if isinstance(goals, dict) else {}
        return {}
