#!/usr/bin/env python3
"""SceneData Value Object

プロットのシーン情報を構造化して保持するValue Object。
SPEC-PLOT-MANUSCRIPT-001で定義されたシーンデータ表現。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SceneData:
    """シーンデータ Value Object

    プロット内の1シーンを表現する不変オブジェクト。
    原稿生成時の基本単位として使用される。

    Attributes:
        scene_number: シーン番号（1から開始）
        title: シーンタイトル
        description: シーンの説明・あらすじ
        characters: 登場キャラクター一覧
        events: シーン内で発生するイベント一覧
        location: 場所設定（オプション）
        time_setting: 時間設定（オプション）
    """

    scene_number: int
    title: str
    description: str
    characters: list[str]
    events: list[str]
    location: str | None = None
    time_setting: str | None = None

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.scene_number < 1:
            msg = "scene_number must be greater than 0"
            raise ValueError(msg)

        if not self.title.strip():
            msg = "title cannot be empty"
            raise ValueError(msg)

        if not self.description.strip():
            msg = "description cannot be empty"
            raise ValueError(msg)

        if not self.characters:
            msg = "characters list cannot be empty"
            raise ValueError(msg)

        if not self.events:
            msg = "events list cannot be empty"
            raise ValueError(msg)

    @classmethod
    def from_yaml_data(cls, yaml_scene: dict) -> SceneData:
        """YAMLデータからSceneDataを生成

        Args:
            yaml_scene: YAMLから読み込んだシーンデータ辞書

        Returns:
            SceneData: 構築されたシーンデータ

        Raises:
            KeyError: 必須フィールドが不足している場合
            ValueError: データが無効な場合
        """
        return cls(
            scene_number=yaml_scene["scene_number"],
            title=yaml_scene["title"],
            description=yaml_scene["description"],
            characters=yaml_scene.get("characters", []),
            events=yaml_scene.get("events", []),
            location=yaml_scene.get("location"),
            time_setting=yaml_scene.get("time_setting")
        )

    def has_character(self, character_name: str) -> bool:
        """指定キャラクターが登場するかチェック

        Args:
            character_name: チェック対象キャラクター名

        Returns:
            bool: 登場する場合True
        """
        return character_name in self.characters

    def has_event(self, event_name: str) -> bool:
        """指定イベントが発生するかチェック

        Args:
            event_name: チェック対象イベント名

        Returns:
            bool: 発生する場合True
        """
        return event_name in self.events

    def get_character_count(self) -> int:
        """登場キャラクター数を取得

        Returns:
            int: キャラクター数
        """
        return len(self.characters)

    def get_event_count(self) -> int:
        """発生イベント数を取得

        Returns:
            int: イベント数
        """
        return len(self.events)

    def to_dict(self) -> dict:
        """辞書形式に変換

        Returns:
            dict: シーンデータ辞書
        """
        return {
            "scene_number": self.scene_number,
            "title": self.title,
            "description": self.description,
            "characters": self.characters.copy(),
            "events": self.events.copy(),
            "location": self.location,
            "time_setting": self.time_setting
        }

    def __str__(self) -> str:
        """文字列表現"""
        return f"Scene {self.scene_number}: {self.title} (chars: {len(self.characters)}, events: {len(self.events)})"

    def __repr__(self) -> str:
        """デバッグ用文字列表現"""
        return (f"SceneData(scene_number={self.scene_number}, "
                f"title='{self.title}', "
                f"characters={self.characters}, "
                f"events={self.events})")
