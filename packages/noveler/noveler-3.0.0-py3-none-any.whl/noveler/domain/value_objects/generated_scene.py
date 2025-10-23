"""Domain.value_objects.generated_scene
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""生成されたシーン値オブジェクト
自動生成されたシーンデータを表現する不変オブジェクト
"""


from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass(frozen=True)
class GeneratedScene:
    """生成されたシーン値オブジェクト"""

    category: str
    scene_id: str
    title: str
    importance_level: str = "A"
    episode_range: str | None = None

    # シーン構造
    setting: dict[str, str] = field(default_factory=dict)
    direction: dict[str, str] = field(default_factory=dict)
    characters: list[str] = field(default_factory=list)
    key_elements: list[str] = field(default_factory=list)
    writing_notes: dict[str, list[str]] = field(default_factory=dict)

    # メタ情報
    auto_generated: bool = True
    generation_source: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """値オブジェクトの不変条件を検証"""
        self._validate_required_fields()
        self._validate_importance_level()

    def _validate_required_fields(self) -> None:
        """必須フィールドの検証"""
        if not self.category or len(self.category.strip()) == 0:
            msg = "カテゴリは必須です"
            raise ValueError(msg)

        if not self.scene_id or len(self.scene_id.strip()) == 0:
            msg = "シーンIDは必須です"
            raise ValueError(msg)

        if not self.title or len(self.title.strip()) == 0:
            msg = "タイトルは必須です"
            raise ValueError(msg)

    def _validate_importance_level(self) -> None:
        """重要度レベルの検証"""
        valid_levels = {"S", "A", "B", "C"}
        if self.importance_level not in valid_levels:
            msg = f"重要度レベルは {valid_levels} のいずれかを指定してください"
            raise ValueError(msg)

    def to_yaml_dict(self) -> dict[str, Any]:
        """YAML出力用の辞書形式に変換"""
        result = {
            "title": self.title,
            "importance_level": self.importance_level,
            "episode_range": self.episode_range or "TBD",
            "completion_score": 0.0,  # 初期状態では未完成
            "is_critical": self.importance_level == "S",
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        # 設定情報
        if self.setting:
            result["setting"] = self.setting

        # 演出指示
        if self.direction:
            result["direction"] = self.direction

        # 登場キャラクター
        if self.characters:
            result["characters"] = self.characters

        # 重要要素
        if self.key_elements:
            result["key_elements"] = self.key_elements

        # 執筆ノート
        if self.writing_notes:
            result["writing_notes"] = self.writing_notes

        # 自動生成情報
        if self.auto_generated:
            result["auto_generated"] = True
            if self.generation_source:
                result["generation_source"] = self.generation_source

        return result

    def get_completion_score(self) -> float:
        """完成度スコアを計算"""
        # 各要素の存在チェック
        score_components = {
            "setting": 20.0,
            "direction": 20.0,
            "characters": 15.0,
            "key_elements": 15.0,
            "writing_notes": 15.0,
            "title": 15.0,
        }

        total_score = 0.0

        # タイトルは必須なので常に加算
        total_score += score_components["title"]

        # 設定情報の完成度
        if self.setting:
            setting_completeness = len(self.setting) / 4.0  # location, time, weather, atmosphere
            total_score += score_components["setting"] * min(setting_completeness, 1.0)

        # 演出指示の完成度
        if self.direction:
            direction_completeness = len(self.direction) / 3.0  # pacing, tension_curve, emotional_flow
            total_score += score_components["direction"] * min(direction_completeness, 1.0)

        # キャラクターの完成度
        if self.characters:
            total_score += score_components["characters"]

        # 重要要素の完成度
        if self.key_elements:
            total_score += score_components["key_elements"]

        # 執筆ノートの完成度
        if self.writing_notes:
            notes_completeness = 0.0
            if self.writing_notes.get("must_include"):
                notes_completeness += 0.6
            if self.writing_notes.get("avoid"):
                notes_completeness += 0.4
            total_score += score_components["writing_notes"] * notes_completeness

        return round(total_score / 100.0, 2)

    def is_complete(self) -> bool:
        """シーンが完成しているかチェック"""
        return self.get_completion_score() >= 0.8  # 80%以上で完成とみなす

    def get_missing_elements(self) -> list[str]:
        """不足している要素のリストを取得"""
        missing = []

        if not self.setting:
            missing.append("シーン設定(場所、時間、雰囲気など)")
        else:
            expected_settings = ["location", "time", "weather", "atmosphere"]
            missing_settings = [s for s in expected_settings if s not in self.setting]
            if missing_settings:
                missing.append(f"設定詳細({', '.join(missing_settings)})")

        if not self.direction:
            missing.append("演出指示(ペース、緊張カーブなど)")

        if not self.characters:
            missing.append("登場キャラクター")

        if not self.key_elements:
            missing.append("重要要素")

        if not self.writing_notes or not self.writing_notes.get("must_include"):
            missing.append("必須要素の執筆ノート")

        return missing

    def enhance_with_manual_edits(self, edits: dict[str, Any]) -> dict[str, Any]:
        """手動編集用のベースデータを提供"""
        base_data: dict[str, Any] = self.to_yaml_dict()

        # 手動編集のガイダンス
        guidance = {
            "_editing_guide": {
                "description": "このシーンは自動生成されました。以下の項目を確認・調整してください。",
                "recommendations": [
                    "setting: 場所・時間・天候・雰囲気が作品世界に合っているか確認",
                    "direction: ペース配分と感情の流れが物語の展開に適しているか確認",
                    "characters: 登場キャラクターが適切か、不足はないか確認",
                    "key_elements: 重要要素が物語のテーマに沿っているか確認",
                    "writing_notes: 執筆時の注意点を追加・調整",
                ],
                "completion_score": f"{self.get_completion_score():.1%}",
                "missing_elements": self.get_missing_elements(),
            }
        }

        # ガイダンスを含めたデータを返す
        result = {**base_data, **guidance}

        # 手動編集があれば適用
        if edits:
            result.update(edits)
            # 自動生成フラグを更新
            result["auto_generated"] = False
            result["manually_edited"] = True
            result["updated_at"] = project_now().datetime.isoformat()

        return result
