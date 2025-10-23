"""
YAML処理統合基盤インターフェース

SPEC-YAML-001: DDD準拠YAML処理統合基盤仕様書準拠
Domain層でのYAML処理操作の抽象化インターフェース
"""

from abc import ABC, abstractmethod
from typing import Any


class IYamlProcessor(ABC):
    """YAML処理統合基盤の抽象インターフェース

    ドメイン層でYAML処理機能を抽象化し、インフラ層への直接依存を排除する。
    DDD原則に従い、ドメイン層→アプリケーション層→インフラ層の依存方向を厳守。
    """

    @abstractmethod
    def create_multiline_string(self, content: str) -> Any:
        """マルチライン文字列オブジェクト生成

        YAML出力時に適切なフォーマット（リテラルブロック形式）で
        保存されるマルチライン文字列オブジェクトを生成する。

        Args:
            content (str): マルチライン文字列の内容

        Returns:
            Any: YAML処理用マルチラインオブジェクト

        Raises:
            ValueError: contentが空文字列の場合
        """

    @abstractmethod
    def process_content_to_dict(self, content: dict[str, Any]) -> dict[str, Any]:
        """コンテンツ辞書のYAML処理対応変換

        辞書内の文字列値を適切なYAML形式（マルチライン対応）に変換し、
        YAML保存時に正しくフォーマットされるよう処理する。

        Args:
            content (Dict[str, Any]): 変換対象の辞書

        Returns:
            Dict[str, Any]: YAML保存用に変換された辞書

        Raises:
            ValueError: contentがNoneまたは無効な形式の場合
        """

    @abstractmethod
    def create_safe_yaml_dict(self, base_dict: dict[str, Any], multiline_fields: list | None = None) -> dict[str, Any]:
        """YAML安全辞書生成

        指定されたフィールドをマルチライン対応に変換し、
        その他のフィールドは適切な型を維持したYAML辞書を生成する。

        Args:
            base_dict (Dict[str, Any]): ベースとなる辞書
            multiline_fields (Optional[list]): マルチライン変換対象フィールド名リスト

        Returns:
            Dict[str, Any]: YAML保存用安全辞書

        Raises:
            ValueError: base_dictが無効な場合
        """

    @abstractmethod
    def validate_yaml_serializable(self, data: Any) -> bool:
        """YAMLシリアライズ可能性検証

        データがYAMLとして正しくシリアライズ可能かを検証する。

        Args:
            data (Any): 検証対象データ

        Returns:
            bool: シリアライズ可能な場合True
        """


class IYamlContentProcessor(ABC):
    """YAML コンテンツ処理専用インターフェース

    エンティティ向けのYAMLコンテンツ処理に特化した抽象インターフェース。
    エピソードプロンプトなどのエンティティで使用される。
    """

    @abstractmethod
    def process_episode_content(self, content: str) -> dict[str, Any]:
        """エピソードコンテンツのYAML処理

        エピソードの内容をYAML保存用形式に変換する。

        Args:
            content (str): エピソードコンテンツ

        Returns:
            Dict[str, Any]: YAML保存用処理済み辞書

        Raises:
            ValueError: contentが無効な場合
        """

    @abstractmethod
    def create_episode_yaml_structure(
        self, episode_number: int, title: str, content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """エピソード用YAML構造生成

        エピソード情報から標準的なYAML構造を生成する。

        Args:
            episode_number (int): エピソード番号
            title (str): エピソードタイトル
            content (str): エピソード内容
            metadata (Optional[Dict[str, Any]]): 追加メタデータ

        Returns:
            Dict[str, Any]: エピソード用YAML構造

        Raises:
            ValueError: 必須パラメータが無効な場合
        """


# ドメイン層で使用するファクトリーインターフェース
class IYamlProcessorFactory(ABC):
    """YAML処理統合基盤ファクトリーインターフェース

    適切なYAML処理実装を生成するファクトリーの抽象インターフェース。
    依存性注入コンテナとの統合に使用される。
    """

    @abstractmethod
    def create_yaml_processor(self) -> IYamlProcessor:
        """YAML処理インスタンス生成

        Returns:
            IYamlProcessor: YAML処理実装インスタンス
        """

    @abstractmethod
    def create_content_processor(self) -> IYamlContentProcessor:
        """YAMLコンテンツ処理インスタンス生成

        Returns:
            IYamlContentProcessor: YAMLコンテンツ処理実装インスタンス
        """
