"""設定サービスProtocol定義

循環依存回避のための純粋なProtocol定義。
設定管理に関する依存は最小限に抑制。
"""

from typing import Any, Protocol


class IConfigurationServiceProtocol(Protocol):
    """設定サービスProtocol

    ドメイン層で定義し、インフラ層で実装する。
    これによりアプリケーション層がインフラ層に直接依存することを防ぐ。
    """

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値
        """
        ...

    def set(self, key: str, value: Any) -> None:
        """設定値を設定

        Args:
            key: 設定キー
            value: 設定値
        """
        ...

    def get_project_root(self) -> str:
        """プロジェクトルートパスを取得

        Returns:
            プロジェクトルートパス文字列
        """
        ...

    def get_environment(self) -> str:
        """実行環境を取得

        Returns:
            環境名（development/staging/production）
        """
        ...

    def get_api_config(self, service_name: str) -> dict[str, Any]:
        """APIサービスの設定を取得

        Args:
            service_name: サービス名

        Returns:
            API設定辞書
        """
        ...

    def get_database_config(self) -> dict[str, Any]:
        """データベース設定を取得

        Returns:
            データベース設定辞書
        """
        ...

    def get_logging_config(self) -> dict[str, Any]:
        """ロギング設定を取得

        Returns:
            ロギング設定辞書
        """
        ...

    def get_feature_flags(self) -> dict[str, bool]:
        """機能フラグを取得

        Returns:
            機能フラグ辞書
        """
        ...

    def is_feature_enabled(self, feature_name: str) -> bool:
        """機能が有効かどうかを確認

        Args:
            feature_name: 機能名

        Returns:
            有効な場合True
        """
        ...

    def reload(self) -> None:
        """設定を再読み込み"""
        ...
