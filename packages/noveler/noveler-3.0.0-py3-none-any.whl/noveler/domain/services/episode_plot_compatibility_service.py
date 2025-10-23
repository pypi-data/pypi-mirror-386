"""Domain.services.episode_plot_compatibility_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""話別プロットファイル互換性サービス

新旧両方の命名規則に対応するための互換性レイヤー
- 新形式: episode001_plot.yaml, episode002_plot.yaml, ...
- 旧形式: 第001話_プロット.yaml, 第002話_プロット.yaml, ...
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from noveler.domain.interfaces.path_service import IPathService



class EpisodePlotCompatibilityService:
    """話別プロットファイルの新旧形式互換性を提供"""

    def __init__(self, path_service: IPathService) -> None:
        """初期化

        Args:
            path_service: パスサービス
        """
        self.path_service = path_service
        plots_dir = self.path_service.get_plot_dir()
        primary = plots_dir / "話別プロット"
        legacy = plots_dir / "話数別プロット"
        self.episode_plot_dir = primary if primary.exists() or not legacy.exists() else legacy

    def get_episode_plot_path(self, episode: int) -> Path:
        """話数番号から実際のプロットファイルパスを取得

        新形式を優先し、存在しない場合は旧形式を試行

        Args:
            episode: 話数番号

        Returns:
            Path: 実際のプロットファイルパス
        """
        # 新形式を優先
        new_format_path = self.episode_plot_dir / f"episode{episode:03d}_plot.yaml"
        if new_format_path.exists():
            return new_format_path

        # 旧形式にフォールバック（タイトル部分は_プロット固定）
        old_format_path = self.episode_plot_dir / f"第{episode:03d}話_プロット.yaml"
        if old_format_path.exists():
            return old_format_path

        # どちらも存在しない場合は新形式のパスを返す（新規作成用）
        return new_format_path

    def list_episode_plot_files(self) -> list[Path]:
        """話別プロットファイルの一覧を取得

        新旧両形式のファイルを統合して返す

        Returns:
            list[Path]: 話別プロットファイルのリスト
        """
        if not self.episode_plot_dir.exists():
            return []

        # 新形式のファイル
        new_format_files = list(self.episode_plot_dir.glob("episode*_plot.yaml"))

        # 旧形式のファイル（_プロット.yamlで終わるもの）
        list(self.episode_plot_dir.glob("第*話_プロット.yaml"))

        # タイトル付き旧形式のファイル（第NNN話_*.yaml形式全般）
        all_old_format_files = list(self.episode_plot_dir.glob("第*話_*.yaml"))

        # 重複を除去（同じ話数番号の新旧両形式がある場合は新形式を優先）
        seen_episodes = set()
        result = []

        # 新形式を先に処理
        for file_path in new_format_files:
            match = re.match(r"episode(\d{3})_plot\.yaml", file_path.name)
            if match:
                episode_num = int(match.group(1))
                seen_episodes.add(episode_num)
                result.append(file_path)

        # 旧形式で新形式にない話数のみ追加
        for file_path in all_old_format_files:
            match = re.match(r"第(\d{3})話_.*\.yaml", file_path.name)
            if match:
                episode_num = int(match.group(1))
                if episode_num not in seen_episodes:
                    result.append(file_path)
                    seen_episodes.add(episode_num)

        # 話数番号順にソート
        return sorted(result, key=self._extract_episode_number)

    def _extract_episode_number(self, file_path: Path) -> int:
        """ファイルパスから話数番号を抽出

        Args:
            file_path: ファイルパス

        Returns:
            int: 話数番号（抽出できない場合は999999）
        """
        # 新形式
        match = re.match(r"episode(\d{3})_plot\.yaml", file_path.name)
        if match:
            return int(match.group(1))

        # 旧形式
        match = re.match(r"第(\d{3})話_.*\.yaml", file_path.name)
        if match:
            return int(match.group(1))

        return 999999

    def migrate_to_new_format(self, episode: int) -> tuple[bool, str]:
        """指定話数のファイルを新形式に移行

        Args:
            episode: 話数番号

        Returns:
            tuple[bool, str]: (成功フラグ, メッセージ)
        """
        # 旧形式のファイルを探す（_プロット.yaml優先）
        old_format_path = self.episode_plot_dir / f"第{episode:03d}話_プロット.yaml"

        # _プロット.yamlが存在しない場合、他のタイトル付きファイルを探す
        if not old_format_path.exists():
            pattern = f"第{episode:03d}話_*.yaml"
            matching_files = list(self.episode_plot_dir.glob(pattern))
            if matching_files:
                old_format_path = matching_files[0]  # 最初に見つかったファイル
            else:
                return False, f"旧形式ファイルが存在しません: 第{episode:03d}話_*.yaml"

        new_format_path = self.episode_plot_dir / f"episode{episode:03d}_plot.yaml"

        if new_format_path.exists():
            return False, f"新形式ファイルが既に存在します: {new_format_path.name}"

        try:
            old_format_path.rename(new_format_path)
            return True, f"移行成功: {old_format_path.name} → {new_format_path.name}"
        except Exception as e:
            return False, f"移行失敗: {e}"

    def migrate_all_to_new_format(self) -> tuple[int, int, list[str]]:
        """全ての話別プロットファイルを新形式に移行

        Returns:
            tuple[int, int, list[str]]: (成功数, 失敗数, エラーメッセージリスト)
        """
        success_count = 0
        failure_count = 0
        error_messages = []

        if not self.episode_plot_dir.exists():
            return 0, 0, ["話数別プロットディレクトリが存在しません"]

        # 旧形式のファイルを全て取得
        old_format_files = list(self.episode_plot_dir.glob("第*話_*.yaml"))

        # 話数番号でグループ化（同じ話数の複数ファイルがある場合の対応）
        episode_files = {}
        for file_path in old_format_files:
            match = re.match(r"第(\d{3})話_.*\.yaml", file_path.name)
            if match:
                episode_num = int(match.group(1))
                if episode_num not in episode_files:
                    episode_files[episode_num] = []
                episode_files[episode_num].append(file_path)

        for episode_num, files in episode_files.items():
            # 複数ファイルがある場合は_プロット.yamlを優先
            target_file = None
            for file_path in files:
                if file_path.name.endswith("_プロット.yaml"):
                    target_file = file_path
                    break

            # _プロット.yamlがない場合は最初のファイル
            if target_file is None and files:
                target_file = files[0]

            if target_file:
                success, message = self.migrate_to_new_format(episode_num)
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                    error_messages.append(message)

        return success_count, failure_count, error_messages

    def get_episode_title_from_filename(self, file_path: Path) -> str | None:
        """旧形式のファイル名からタイトルを抽出

        Args:
            file_path: ファイルパス

        Returns:
            str | None: タイトル（抽出できない場合はNone）
        """
        match = re.match(r"第\d{3}話_(.*)\.yaml", file_path.name)
        if match:
            title = match.group(1)
            # "プロット"で終わる場合はタイトルなし
            if title == "プロット":
                return None
            return title
        return None
