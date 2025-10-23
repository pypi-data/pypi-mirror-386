"""Domain.repositories.specification_repository
Where: Domain repository interface for system specifications.
What: Provides access to specification documents and versioning information.
Why: Ensures specification data can be managed consistently across services.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""仕様書リポジトリインターフェース

DDD原則に基づくドメイン層のリポジトリ抽象化
"""


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class SpecificationRepository(ABC):
    """仕様書リポジトリインターフェース"""

    @abstractmethod
    def save_specification(self, spec_id: str, content: str, file_path: Path) -> bool:
        """仕様書を保存

        Args:
            spec_id: 仕様書ID
            content: 仕様書の内容
            file_path: 保存先パス

        Returns:
            保存成功時True
        """

    @abstractmethod
    def load_specification(self, spec_id: str) -> str | None:
        """仕様書を読み込み

        Args:
            spec_id: 仕様書ID

        Returns:
            仕様書の内容、存在しない場合None
        """

    @abstractmethod
    def exists(self, spec_id: str) -> bool:
        """仕様書が存在するかチェック

        Args:
            spec_id: 仕様書ID

        Returns:
            存在する場合True
        """

    @abstractmethod
    def list_specifications(self) -> list[str]:
        """全仕様書IDのリストを取得

        Returns:
            仕様書IDのリスト
        """

    @abstractmethod
    def delete_specification(self, spec_id: str) -> bool:
        """仕様書を削除

        Args:
            spec_id: 仕様書ID

        Returns:
            削除成功時True
        """

    @abstractmethod
    def get_specification_path(self, spec_id: str) -> Path | None:
        """仕様書のファイルパスを取得

        Args:
            spec_id: 仕様書ID

        Returns:
            ファイルパス、存在しない場合None
        """
