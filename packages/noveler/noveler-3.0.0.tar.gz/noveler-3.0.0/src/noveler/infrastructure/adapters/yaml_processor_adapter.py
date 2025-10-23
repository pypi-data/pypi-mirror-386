"""
YAML処理統合基盤インフラ層アダプター

SPEC-YAML-001: DDD準拠YAML処理統合基盤仕様書準拠
既存のyaml_utilsをラップしてドメインインターフェースを実装
"""

from typing import Any

import yaml

from noveler.domain.interfaces.yaml_processor import IYamlContentProcessor, IYamlProcessor
from noveler.infrastructure.utils.yaml_utils import YAMLHandler, YAMLMultilineString


class YamlProcessorAdapter(IYamlProcessor):
    """YAML処理統合基盤のインフラ層アダプター実装

    既存のYAMLUtilsをラップしてドメインインターフェースを実装。
    DDD原則に従い、インフラ層の具体実装として動作する。
    """

    def __init__(self) -> None:
        """コンストラクタ"""
        self._yaml_handler = YAMLHandler()

    def create_multiline_string(self, content: str) -> YAMLMultilineString:
        """マルチライン文字列オブジェクト生成

        Args:
            content (str): マルチライン文字列の内容

        Returns:
            YAMLMultilineString: YAML処理用マルチラインオブジェクト

        Raises:
            ValueError: contentが空文字列の場合
        """
        if not content:
            msg = "Content cannot be empty"
            raise ValueError(msg)

        return YAMLMultilineString(content)

    def process_content_to_dict(self, content: dict[str, Any]) -> dict[str, Any]:
        """コンテンツ辞書のYAML処理対応変換

        辞書内の長い文字列値を適切なYAML形式（マルチライン対応）に変換する。

        Args:
            content (Dict[str, Any]): 変換対象の辞書

        Returns:
            Dict[str, Any]: YAML保存用に変換された辞書

        Raises:
            ValueError: contentがNoneまたは無効な形式の場合
        """
        if content is None:
            msg = "Content dictionary cannot be None"
            raise ValueError(msg)

        if not isinstance(content, dict):
            msg = "Content must be a dictionary"
            raise ValueError(msg)

        result = {}

        for key, value in content.items():
            if isinstance(value, str) and ("\\n" in value or len(value) > 100):
                # 長いまたはマルチライン文字列をYAMLMultilineStringに変換
                result[key] = YAMLMultilineString(value)
            elif isinstance(value, dict):
                # ネストした辞書を再帰的に処理
                result[key] = self.process_content_to_dict(value)
            elif isinstance(value, list):
                # リスト内の文字列も処理
                result[key] = self._process_list_content(value)
            else:
                # その他の型はそのまま
                result[key] = value

        return result

    def create_safe_yaml_dict(
        self, base_dict: dict[str, Any], multiline_fields: list[str] | None = None
    ) -> dict[str, Any]:
        """YAML安全辞書生成

        Args:
            base_dict (Dict[str, Any]): ベースとなる辞書
            multiline_fields (Optional[List[str]]): マルチライン変換対象フィールド名リスト

        Returns:
            Dict[str, Any]: YAML保存用安全辞書

        Raises:
            ValueError: base_dictが無効な場合
        """
        if base_dict is None:
            msg = "Base dictionary cannot be None"
            raise ValueError(msg)

        if not isinstance(base_dict, dict):
            msg = "Base dict must be a dictionary"
            raise ValueError(msg)

        multiline_fields = multiline_fields or []
        result = {}

        for key, value in base_dict.items():
            if key in multiline_fields and isinstance(value, str):
                # 指定されたフィールドを強制的にマルチライン対応
                result[key] = YAMLMultilineString(value)
            elif isinstance(value, str) and ("\\n" in value or len(value) > 200):
                # 自動判定によるマルチライン変換
                result[key] = YAMLMultilineString(value)
            elif isinstance(value, dict):
                # ネストした辞書を再帰的に処理
                result[key] = self.create_safe_yaml_dict(value, multiline_fields)
            elif isinstance(value, list):
                # リスト内容を処理
                result[key] = self._process_list_content(value, multiline_fields)
            else:
                result[key] = value

        return result

    def validate_yaml_serializable(self, data: Any) -> bool:
        """YAMLシリアライズ可能性検証

        Args:
            data (Any): 検証対象データ

        Returns:
            bool: シリアライズ可能な場合True
        """
        try:
            # 実際にYAMLシリアライズを試行
            yaml_str = yaml.dump(data, allow_unicode=True, default_style=None)
            return isinstance(yaml_str, str) and len(yaml_str) > 0
        except Exception:
            return False

    def _process_list_content(self, content_list: list[Any], multiline_fields: list[str] | None = None) -> list[Any]:
        """リスト内容のYAML処理

        Args:
            content_list (List[Any]): 処理対象リスト
            multiline_fields (Optional[List[str]]): マルチライン対象フィールド

        Returns:
            List[Any]: 処理済みリスト
        """
        result = []

        for item in content_list:
            if isinstance(item, str) and ("\\n" in item or len(item) > 100):
                result.append(YAMLMultilineString(item))
            elif isinstance(item, dict):
                result.append(self.create_safe_yaml_dict(item, multiline_fields))
            else:
                result.append(item)

        return result


class YamlContentProcessorAdapter(IYamlContentProcessor):
    """YAMLコンテンツ処理専用アダプター実装

    エンティティ向けのYAMLコンテンツ処理に特化したアダプター。
    YamlProcessorAdapterと協調して動作する。
    """

    def __init__(self, yaml_processor: IYamlProcessor | None = None) -> None:
        """コンストラクタ

        Args:
            yaml_processor (Optional[IYamlProcessor]): YAML処理実装（デフォルトでアダプター使用）
        """
        self._yaml_processor = yaml_processor or YamlProcessorAdapter()

    def process_episode_content(self, content: str) -> dict[str, Any]:
        """エピソードコンテンツのYAML処理

        Args:
            content (str): エピソードコンテンツ

        Returns:
            Dict[str, Any]: YAML保存用処理済み辞書

        Raises:
            ValueError: contentが無効な場合
        """
        if not content or not content.strip():
            msg = "Episode content cannot be empty"
            raise ValueError(msg)

        # マルチライン文字列として処理
        multiline_content = self._yaml_processor.create_multiline_string(content)

        # エピソード用基本構造
        episode_dict = {
            "content": multiline_content,
            "content_metadata": {
                "character_count": len(content),
                "line_count": content.count("\\n") + 1,
                "paragraph_count": len([p for p in content.split("\\n\\n") if p.strip()]),
                "estimated_reading_time_minutes": max(1, len(content) // 400),  # 400文字/分想定
            },
        }

        return self._yaml_processor.process_content_to_dict(episode_dict)

    def create_episode_yaml_structure(
        self, episode_number: int, title: str, content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """エピソード用YAML構造生成

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
        # パラメータ検証
        if episode_number <= 0:
            msg = "Episode number must be positive"
            raise ValueError(msg)

        if not title or not title.strip():
            msg = "Episode title cannot be empty"
            raise ValueError(msg)

        if not content or not content.strip():
            msg = "Episode content cannot be empty"
            raise ValueError(msg)

        # コンテンツ処理
        processed_content = self.process_episode_content(content)

        # 基本構造作成
        episode_structure = {
            "episode_info": {"number": episode_number, "title": title, "content_type": "episode_prompt"},
            "content": processed_content["content"],
            "content_analysis": processed_content["content_metadata"],
        }

        # 追加メタデータのマージ
        if metadata:
            episode_structure["additional_metadata"] = self._yaml_processor.create_safe_yaml_dict(metadata)

        # 全体をYAML safe形式に変換
        multiline_fields = ["content", "description", "summary", "notes"]
        return self._yaml_processor.create_safe_yaml_dict(episode_structure, multiline_fields)


class YamlUtilsWrapper:
    """既存YAMLUtils機能のラッパー

    既存のYAMLHandlerやYAMLMultilineStringへの互換性レイヤー。
    段階的マイグレーション期間中の互換性維持に使用。
    """

    @staticmethod
    def create_yaml_processor() -> YamlProcessorAdapter:
        """標準YAML処理アダプター生成

        Returns:
            YamlProcessorAdapter: YAML処理アダプター
        """
        return YamlProcessorAdapter()

    @staticmethod
    def create_content_processor() -> YamlContentProcessorAdapter:
        """YAMLコンテンツ処理アダプター生成

        Returns:
            YamlContentProcessorAdapter: YAMLコンテンツ処理アダプター
        """
        return YamlContentProcessorAdapter()

    @staticmethod
    def create_unified_processor() -> dict[str, Any]:
        """統合プロセッサーセット生成

        Returns:
            Dict[str, Any]: 全プロセッサーセット
        """
        yaml_processor = YamlProcessorAdapter()
        content_processor = YamlContentProcessorAdapter(yaml_processor)

        return {
            "yaml_processor": yaml_processor,
            "content_processor": content_processor,
            "yaml_handler": YAMLHandler(),  # 既存コンポーネント互換性
            "multiline_string_creator": yaml_processor.create_multiline_string,
        }


# 便利関数（段階的マイグレーション用）
def get_ddd_yaml_processor() -> YamlProcessorAdapter:
    """DDD準拠YAML処理実装取得

    Returns:
        YamlProcessorAdapter: DDD準拠YAML処理実装
    """
    return YamlProcessorAdapter()


def get_ddd_content_processor() -> YamlContentProcessorAdapter:
    """DDD準拠コンテンツ処理実装取得

    Returns:
        YamlContentProcessorAdapter: DDD準拠コンテンツ処理実装
    """
    return YamlContentProcessorAdapter()


# 後方互換性サポート
def create_legacy_compatible_multiline_string(content: str) -> YAMLMultilineString:
    """レガシー互換マルチライン文字列生成

    Args:
        content (str): 文字列内容

    Returns:
        YAMLMultilineString: マルチライン文字列オブジェクト
    """
    processor = YamlProcessorAdapter()
    return processor.create_multiline_string(content)
