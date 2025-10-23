"""プロット検証データ用リポジトリインターフェース."""

from abc import ABC, abstractmethod

from noveler.domain.value_objects.validation_result import ValidationResult


class PlotValidationDataRepository(ABC):
    """プロット検証データの永続化を担当するリポジトリインターフェース."""

    @abstractmethod
    def get_validation_data(self, plot_id: str) -> dict | None:
        """指定されたプロットの検証データを取得.

        Args:
            plot_id: プロットID

        Returns:
            検証データ、存在しない場合はNone
        """

    @abstractmethod
    def save_validation_data(self, plot_id: str, validation_data: dict) -> None:
        """プロット検証データを保存.

        Args:
            plot_id: プロットID
            validation_data: 検証データ
        """

    @abstractmethod
    def get_validation_history(self, plot_id: str) -> list[dict]:
        """プロットの検証履歴を取得.

        Args:
            plot_id: プロットID

        Returns:
            検証履歴のリスト
        """

    @abstractmethod
    def save_validation_result(self, plot_id: str, result: dict) -> str:
        """検証結果を保存.

        Args:
            plot_id: プロットID
            result: 検証結果

        Returns:
            保存された検証結果のID
        """

    @abstractmethod
    def get_validation_result(self, validation_id: str) -> ValidationResult | None:
        """検証結果を取得.

        Args:
            validation_id: 検証結果ID

        Returns:
            検証結果、存在しない場合はNone
        """

    @abstractmethod
    def get_latest_validation(self, plot_id: str) -> ValidationResult | None:
        """最新の検証結果を取得.

        Args:
            plot_id: プロットID

        Returns:
            最新の検証結果、存在しない場合はNone
        """

    @abstractmethod
    def delete_validation_data(self, plot_id: str) -> bool:
        """検証データを削除.

        Args:
            plot_id: プロットID

        Returns:
            削除成功時True
        """

    @abstractmethod
    def list_validated_plots(self) -> list[str]:
        """検証データが存在するプロットIDのリストを取得.

        Returns:
            プロットIDのリスト
        """
