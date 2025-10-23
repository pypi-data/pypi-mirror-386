"""
エピソードプロンプトエンティティ

SPEC-PROMPT-SAVE-001: プロンプト保存機能仕様書準拠
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.prompt_file_name import PromptFileName


@dataclass
class EpisodePrompt:
    """エピソードプロンプトを表すドメインエンティティ

    プロンプト生成・保存・管理の中心的な業務オブジェクト
    """

    # 識別子
    episode_number: int
    title: str

    # プロンプト内容
    prompt_content: str

    # メタデータ
    generation_timestamp: datetime = field(default_factory=lambda: project_now().datetime)
    template_version: str = "1.0"
    content_sections: dict[str, Any] = field(default_factory=dict)

    # 生成設定
    generation_mode: str = "enhanced"
    quality_level: str = "detailed"

    def __post_init__(self) -> None:
        """エンティティ初期化後の検証"""
        self._validate_business_rules()

    def _validate_business_rules(self) -> None:
        """ビジネスルール検証"""
        if self.episode_number <= 0:
            msg = "Episode number must be positive"
            raise ValueError(msg)

        if not self.title.strip():
            msg = "Episode title cannot be empty"
            raise ValueError(msg)

        if not self.prompt_content.strip():
            msg = "Prompt content cannot be empty"
            raise ValueError(msg)

        if len(self.prompt_content) < 80:
            msg = "Prompt content too short (minimum 80 characters)"
            raise ValueError(msg)

    def get_file_name(self) -> PromptFileName:
        """ファイル名バリューオブジェクト取得

        Returns:
            PromptFileName: ファイル名生成用バリューオブジェクト
        """
        return PromptFileName(episode_number=self.episode_number, title=self.title)

    def get_yaml_content(self) -> dict[str, Any]:
        """YAML保存用辞書生成

        Returns:
            Dict[str, Any]: YAML形式保存用データ
        """
        # 🔧 DDD準拠: インフラ層への直接依存を排除
        # YAML処理はアプリケーション層で処理されるため、ここではプレーン辞書を返す
        return {
            "metadata": {
                "spec_id": "SPEC-PROMPT-SAVE-001",
                "episode_number": self.episode_number,
                "title": self.title,
                "generation_timestamp": self.generation_timestamp.isoformat(),
                "template_version": self.template_version,
                "generation_mode": self.generation_mode,
                "quality_level": self.quality_level,
            },
            "prompt_content": self.prompt_content,  # プレーン文字列として返す
            "content_sections": self.content_sections,
            "validation": {
                "content_length": len(self.prompt_content),
                "sections_count": len(self.content_sections),
                "quality_validated": True,
            },
        }

    @classmethod
    def from_yaml_data(cls, yaml_data: dict[str, Any]) -> "EpisodePrompt":
        """YAMLデータからエンティティ復元

        Args:
            yaml_data: YAML形式のデータ辞書

        Returns:
            EpisodePrompt: 復元されたエンティティ
        """
        metadata = yaml_data.get("metadata", {})

        return cls(
            episode_number=metadata["episode_number"],
            title=metadata["title"],
            prompt_content=yaml_data["prompt_content"],
            generation_timestamp=datetime.fromisoformat(metadata["generation_timestamp"]),
            template_version=metadata.get("template_version", "1.0"),
            content_sections=yaml_data.get("content_sections", {}),
            generation_mode=metadata.get("generation_mode", "enhanced"),
            quality_level=metadata.get("quality_level", "detailed"),
        )

    def update_content(self, new_content: str) -> None:
        """プロンプト内容更新

        Args:
            new_content: 新しいプロンプト内容
        """
        if not new_content.strip():
            msg = "New content cannot be empty"
            raise ValueError(msg)

        if len(new_content) < 80:
            msg = "New content too short (minimum 80 characters)"
            raise ValueError(msg)

        self.prompt_content = new_content
        self.generation_timestamp = project_now().datetime

    def add_content_section(self, section_name: str, section_data: Any) -> None:
        """コンテンツセクション追加

        Args:
            section_name: セクション名
            section_data: セクションデータ
        """
        if not section_name.strip():
            msg = "Section name cannot be empty"
            raise ValueError(msg)

        self.content_sections[section_name] = section_data

    def get_content_quality_score(self) -> float:
        """コンテンツ品質スコア計算

        Returns:
            float: 0.0-1.0の品質スコア
        """
        # 基本品質指標（閾値を現実的に調整）
        # 300文字程度でも一定の品質を評価できるよう目標値を調整
        length_score = min(len(self.prompt_content) / 1000, 1.0)  # 1000文字を満点
        sections_score = min(len(self.content_sections) / 6, 1.0)  # 6セクションを満点

        # タイトル品質
        title_score = 1.0 if len(self.title) >= 3 else 0.5

        return (length_score + sections_score + title_score) / 3

    def is_high_quality(self) -> bool:
        """高品質判定

        Returns:
            bool: 品質スコア0.8以上でTrue
        """
        return self.get_content_quality_score() >= 0.8
