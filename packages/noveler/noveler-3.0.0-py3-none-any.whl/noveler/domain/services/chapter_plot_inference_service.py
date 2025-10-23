"""章プロット推論サービス

エピソード番号から章プロット情報を推論するサービス
"""
from typing import TYPE_CHECKING, Any

import yaml

from noveler.domain.interfaces.path_service import IPathService

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.i_path_service import IPathService


class ChapterPlotInferenceService:
    """章プロット推論サービス"""

    def __init__(self, console: "IConsoleService", path_service: "IPathService") -> None:
        """初期化

        Args:
            console: コンソールサービス（DI注入）
            path_service: パスサービス（DI注入）
        """
        self._console = console
        self._path_service = path_service

    def infer_chapter_plot_for_episode(self, episode_number: int) -> dict[str, Any] | None:
        """エピソード番号から章プロット情報を推論

        Args:
            episode_number: エピソード番号

        Returns:
            章プロット情報の辞書、または None

        Note:
            B20準拠: プロジェクトルートパスは注入されたPath Serviceから取得
        """
        try:
            # B20準拠: Path ServiceのInterface経由で安全にパス取得
            chapter_plot_dir = self._path_service.get_plot_dir() / "章別プロット"
            self._console.print_info(f"章別プロットディレクトリを検索: {chapter_plot_dir}")
            if not chapter_plot_dir.exists():
                self._console.print_warning(f"章別プロットディレクトリが見つかりません: {chapter_plot_dir}")
                return None
            chapter_number = self._infer_chapter_from_episode(episode_number)
            self._console.print_info(f"第{episode_number}話 → 第{chapter_number}章 と推論")
            chapter_files = list(chapter_plot_dir.glob(f"ch{chapter_number:02d}*.yaml"))
            if not chapter_files:
                chapter_files = list(chapter_plot_dir.glob(f"第{chapter_number}章*.yaml"))
            if not chapter_files:
                self._console.print_warning(f"第{chapter_number}章のファイルが見つからないため、全ファイルを検索...")
                chapter_files = list(chapter_plot_dir.glob("*.yaml"))
                if chapter_files:
                    chapter_file = chapter_files[0]
                    self._console.print_info(f"代替ファイルを使用: {chapter_file.name}")
                else:
                    self._console.print_error("章プロットファイルが見つかりません")
                    return None
            else:
                chapter_file = chapter_files[0]
                self._console.print_success(f"章プロットファイル発見: {chapter_file.name}")
            chapter_plot_data: dict[str, Any] = yaml.safe_load(chapter_file.read_text(encoding="utf-8"))
            episode_info = self._extract_episode_info(episode_number, chapter_plot_data)
            return {
                "chapter_number": chapter_number,
                "chapter_data": chapter_plot_data,
                "episode_info": episode_info,
                "source_file": str(chapter_file),
            }
        except Exception as e:
            self._console.print_error(f"章プロット推論エラー: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _infer_chapter_from_episode(self, episode_number: int) -> int:
        """エピソード番号から章番号を推論

        Args:
            episode_number: エピソード番号

        Returns:
            推論された章番号
        """
        if episode_number <= 30:
            return 1
        if episode_number <= 70:
            return 2
        return 3

    def _extract_episode_info(self, episode_number: int, chapter_data: dict[str, Any]) -> dict[str, Any]:
        """章データからエピソード関連情報を抽出

        Args:
            episode_number: エピソード番号
            chapter_data: 章プロットデータ

        Returns:
            エピソード関連情報
        """
        try:
            episodes = chapter_data.get("episodes", [])
            for episode in episodes:
                if episode.get("episode_number") == episode_number:
                    return episode
            return {
                "episode_number": episode_number,
                "title": f"第{episode_number}話",
                "summary": "自動推論による基本情報",
                "inferred": True,
            }
        except Exception as e:
            self._console.print_error(f"エピソード情報抽出エラー: {e}")
            return {
                "episode_number": episode_number,
                "title": f"第{episode_number}話",
                "summary": "推論失敗",
                "error": str(e),
            }
