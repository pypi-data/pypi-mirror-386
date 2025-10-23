"""アクセスデータリポジトリインターフェース

エピソードのアクセスデータを取得するための抽象インターフェース。
DDD原則に基づき、ドメイン層に配置。
"""

from abc import ABC, abstractmethod

from noveler.domain.value_objects.dropout_metrics import AccessData


class AccessDataRepository(ABC):
    """アクセスデータリポジトリの抽象インターフェース"""

    @abstractmethod
    def get_access_data(self, project_name: str, ncode: str) -> AccessData:
        """アクセスデータを取得

        Args:
            project_name: プロジェクト名
            ncode: 小説コード
            target_date: 対象日付(指定しない場合は最新データ)

        Returns:
            アクセスデータ

        Raises:
            DataNotFoundError: データが見つからない場合
            RepositoryError: リポジトリエラー
        """

    @abstractmethod
    def get_access_data_range(self, project_name: str, ncode: str) -> AccessData:
        """期間指定でアクセスデータを取得

        Args:
            project_name: プロジェクト名
            ncode: 小説コード
            start_date: 開始日
            end_date: 終了日

        Returns:
            期間内のアクセスデータ

        Raises:
            DataNotFoundError: データが見つからない場合
            RepositoryError: リポジトリエラー
        """
