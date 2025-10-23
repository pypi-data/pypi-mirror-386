"""仕様書管理リポジトリインターフェース"""

from abc import ABC, abstractmethod

from noveler.domain.specification.entities import Specification, SpecificationTest


class SpecificationRepository(ABC):
    """仕様書リポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, spec_id: str) -> Specification | None:
        """IDで仕様書を検索"""

    @abstractmethod
    def find_all(self) -> list[Specification]:
        """すべての仕様書を取得"""

    @abstractmethod
    def find_by_test_file(self, test_file_path: str) -> list[Specification]:
        """テストファイルに関連する仕様書を検索"""

    @abstractmethod
    def save(self, specification: Specification) -> None:
        """仕様書を保存"""

    @abstractmethod
    def save_all(self, specifications: list[Specification]) -> None:
        """複数の仕様書を保存"""

    @abstractmethod
    def delete(self, spec_id: str) -> None:
        """仕様書を削除"""


class SpecificationTestRepository(ABC):
    """テスト仕様リポジトリインターフェース"""

    @abstractmethod
    def find_by_test_reference(self, test_file_path: str, function_name: str) -> SpecificationTest | None:
        """テスト参照でテスト仕様を検索"""

    @abstractmethod
    def find_all(self) -> list[SpecificationTest]:
        """すべてのテスト仕様を取得"""

    @abstractmethod
    def find_by_specification_id(self, spec_id: str) -> list[SpecificationTest]:
        """仕様IDに関連するテスト仕様を検索"""

    @abstractmethod
    def find_orphaned_tests(self) -> list[SpecificationTest]:
        """仕様に紐付いていないテストを検索"""

    @abstractmethod
    def save(self, test_specification: SpecificationTest) -> None:
        """テスト仕様を保存"""

    @abstractmethod
    def save_all(self, test_specifications: list[SpecificationTest]) -> None:
        """複数のテスト仕様を保存"""

    @abstractmethod
    def delete_by_test_reference(self, test_file_path: str, function_name: str) -> None:
        """テスト参照でテスト仕様を削除"""
