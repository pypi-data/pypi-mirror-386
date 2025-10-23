"""原稿とプロットのリンクリポジトリインターフェース

原稿とプロットの紐付けを管理するリポジトリインターフェース
"""

from abc import ABC, abstractmethod

from noveler.domain.entities.manuscript_plot_link import ManuscriptPlotLink


class ManuscriptPlotLinkRepository(ABC):
    """原稿とプロットのリンクリポジトリのインターフェース"""

    @abstractmethod
    def find_by_manuscript_id(self, manuscript_id: str) -> ManuscriptPlotLink | None:
        """原稿IDによるリンクの取得"""

    @abstractmethod
    def find_by_plot_id(self, plot_id: str) -> list[ManuscriptPlotLink]:
        """プロットIDによるリンクリストの取得"""

    @abstractmethod
    def find_by_episode(self, episode: int) -> ManuscriptPlotLink | None:
        """エピソードによるリンクの取得"""

    @abstractmethod
    def save(self, link: ManuscriptPlotLink) -> None:
        """リンクの保存"""

    @abstractmethod
    def delete_by_manuscript_id(self, manuscript_id: str) -> None:
        """原稿IDによるリンクの削除"""
