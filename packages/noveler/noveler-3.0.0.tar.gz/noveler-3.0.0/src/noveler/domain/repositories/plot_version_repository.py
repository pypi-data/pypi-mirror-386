"""プロットバージョンリポジトリインターフェース

プロットのバージョン管理に関するリポジトリインターフェース
"""

from abc import ABC, abstractmethod

from noveler.domain.entities.plot_version import PlotVersion


class PlotVersionRepository(ABC):
    """プロットバージョンリポジトリのインターフェース"""

    @abstractmethod
    def find_by_id(self, version_id: str) -> PlotVersion | None:
        """IDによるプロットバージョンの取得"""

    @abstractmethod
    def find_by_plot_id(self, plot_id: str) -> list[PlotVersion]:
        """プロットIDによるバージョンリストの取得"""

    @abstractmethod
    def save(self, plot_version: PlotVersion) -> None:
        """プロットバージョンの保存"""

    @abstractmethod
    def get_latest_version(self, plot_id: str) -> PlotVersion | None:
        """最新バージョンの取得"""

    @abstractmethod
    def get_current(self) -> PlotVersion | None:
        """現在のプロットバージョンの取得"""

    @abstractmethod
    def find_by_version(self, version: str) -> PlotVersion | None:
        """バージョン番号によるプロットバージョンの取得"""

    @abstractmethod
    def find_all(self) -> list[PlotVersion]:
        """全プロットバージョンの取得"""
