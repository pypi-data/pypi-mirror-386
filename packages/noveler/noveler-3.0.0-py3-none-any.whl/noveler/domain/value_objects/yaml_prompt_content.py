"""YAML プロンプトコンテンツ値オブジェクト
仕様: specs/integrated_writing_workflow.spec.md
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class YamlPromptMetadata:
    """YAMLプロンプトメタデータ"""

    title: str
    project: str
    episode_file: str
    genre: str
    word_count: str
    viewpoint: str
    viewpoint_character: str
    detail_level: str
    methodology: str
    generated_at: str

    def __post_init__(self) -> None:
        """値オブジェクト不変条件検証"""
        if not self.title:
            msg = "titleは必須です"
            raise ValueError(msg)
        if not self.episode_file:
            msg = "episode_fileは必須です"
            raise ValueError(msg)
        if not self.word_count.isdigit():
            msg = f"word_countは数値文字列である必要があります: {self.word_count}"
            raise ValueError(msg)


@dataclass(frozen=True)
class YamlPromptContent:
    """YAML プロンプトコンテンツ値オブジェクト

    ruamel.yaml準拠の構造化プロンプトデータを表現する不変オブジェクト
    """

    metadata: YamlPromptMetadata
    raw_yaml_content: str
    custom_requirements: list[str]
    validation_passed: bool
    file_size_bytes: int

    def __post_init__(self) -> None:
        """値オブジェクト不変条件検証"""
        if not self.raw_yaml_content:
            msg = "raw_yaml_contentは必須です"
            raise ValueError(msg)

        if self.file_size_bytes < 0:
            msg = "file_size_bytesは0以上である必要があります"
            raise ValueError(msg)

        # YAMLコンテンツの基本検証
        yaml_content_stripped = self.raw_yaml_content.strip()
        if not yaml_content_stripped:
            msg = "YAMLコンテンツが空です"
            raise ValueError(msg)

        # 基本的なYAML構造の確認（Claude品質チェックプロンプト用）
        valid_starts = (
            "metadata:",
            "---",
            "task_definition:",
            "evaluation_criteria:",
            "analysis_instructions:",
            "manuscript_analysis:",
            "quality_assessment:",
        )

        if not yaml_content_stripped.startswith(valid_starts):
            # YAML形式であることの簡単な確認（コロンを含む）
            if ":" not in yaml_content_stripped[:100]:
                actual_start = (
                    yaml_content_stripped[:50] + "..." if len(yaml_content_stripped) > 50 else yaml_content_stripped
                )
                msg = f"YAML形式ではない可能性があります。実際の開始: '{actual_start}'"
                raise ValueError(msg)

    @classmethod
    def create_from_yaml_string(
        cls,
        yaml_content: str,
        metadata: YamlPromptMetadata,
        custom_requirements: list[str],
        validation_passed: bool = True,
    ) -> "YamlPromptContent":
        """YAML文字列からインスタンス作成

        Args:
            yaml_content: 生のYAMLコンテンツ
            metadata: YAMLプロンプトメタデータ
            custom_requirements: カスタム要件リスト
            validation_passed: 検証通過フラグ

        Returns:
            YamlPromptContent: 作成されたインスタンス
        """
        try:
            return cls(
                metadata=metadata,
                raw_yaml_content=yaml_content,
                custom_requirements=custom_requirements.copy(),  # 防御的コピー
                validation_passed=validation_passed,
                file_size_bytes=len(yaml_content.encode("utf-8")),
            )

        except ValueError as e:
            # バリデーションエラーの詳細情報を追加
            yaml_preview = yaml_content[:200] + "..." if len(yaml_content) > 200 else yaml_content
            msg = f"YamlPromptContent作成エラー: {e!s}\nYAMLコンテンツプレビュー:\n{yaml_preview}"
            raise ValueError(msg) from e

    def get_word_count_target(self) -> int:
        """目標文字数を整数で取得"""
        try:
            return int(self.metadata.word_count)
        except ValueError:
            return 4000  # デフォルト値

    def has_custom_requirements(self) -> bool:
        """カスタム要件存在判定"""
        return len(self.custom_requirements) > 0

    def get_file_size_kb(self) -> float:
        """ファイルサイズ（KB）"""
        return self.file_size_bytes / 1024.0

    def is_validated(self) -> bool:
        """YAML検証通過判定"""
        return self.validation_passed

    def contains_requirement(self, requirement: str) -> bool:
        """特定要件含有判定"""
        return requirement in self.custom_requirements

    def get_summary(self) -> str:
        """プロンプト概要文字列"""
        return (
            f"{self.metadata.title} "
            f"({self.metadata.word_count}字, "
            f"{len(self.custom_requirements)}要件, "
            f"{self.get_file_size_kb():.1f}KB)"
        )
