"""YAML プロンプトリポジトリインターフェース
仕様: specs/integrated_writing_workflow.spec.md
"""

from abc import ABC, abstractmethod
from pathlib import Path

from noveler.domain.value_objects.yaml_prompt_content import YamlPromptContent, YamlPromptMetadata


class YamlPromptRepository(ABC):
    """YAML プロンプトリポジトリインターフェース

    Domain層のリポジトリインターフェース
    Infrastructure層で具体実装を提供
    """

    @abstractmethod
    async def generate_stepwise_prompt(
        self, metadata: YamlPromptMetadata, custom_requirements: list[str]
    ) -> YamlPromptContent:
        """段階的執筆プロンプト生成

        Args:
            metadata: YAMLプロンプトメタデータ
            custom_requirements: カスタム要件リスト

        Returns:
            生成されたYAMLプロンプトコンテンツ

        Raises:
            YamlGenerationError: YAML生成失敗時
        """

    @abstractmethod
    async def save_with_validation(self, yaml_content: YamlPromptContent, output_path: Path) -> bool:
        """YAML プロンプト検証付き保存

        Args:
            yaml_content: 保存するYAMLコンテンツ
            output_path: 出力パス

        Returns:
            保存成功可否

        Raises:
            YamlValidationError: YAML検証失敗時
            YamlSaveError: ファイル保存失敗時
        """

    @abstractmethod
    async def validate_yaml_format(self, yaml_content: str) -> dict[str, bool]:
        """YAML 形式検証

        Args:
            yaml_content: 検証するYAML文字列

        Returns:
            検証結果辞書 {syntax_valid: bool, yamllint_passed: bool}
        """

    @abstractmethod
    async def load_guide_template(self) -> dict[str, any]:
        """執筆ガイドテンプレート読み込み

        Returns:
            A30ガイドYAMLデータ

        Raises:
            TemplateLoadError: テンプレート読み込み失敗時
        """


class YamlGenerationError(Exception):
    """YAML生成エラー"""


class YamlValidationError(Exception):
    """YAML検証エラー"""


class YamlSaveError(Exception):
    """YAML保存エラー"""


class TemplateLoadError(Exception):
    """テンプレート読み込みエラー"""
